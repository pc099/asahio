"""Intervention engine — 5-level intervention ladder governed by mode.

Levels:
  0 LOG     — record only
  1 FLAG    — add warning metadata
  2 AUGMENT — append verification instruction to prompt
  3 REROUTE — switch to a stronger model
  4 BLOCK   — reject the request entirely

Mode gates:
  OBSERVE   → Level 0 only
  ASSISTED  → Levels 0-3
  AUTONOMOUS → Levels 0-4

All methods are synchronous and target <0.5ms.
"""

import enum
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# Model catalog used for rerouting — loaded dynamically from routing module.

# ── Augmentation text ──────────────────────────────────────────────────

_AUGMENT_SUFFIX = (
    "\n\n[System: This response will be verified for accuracy. "
    "Please ensure all claims are factual and well-supported. "
    "If uncertain, clearly state your uncertainty level.]"
)


class InterventionLevel(int, enum.Enum):
    """Risk-based intervention levels."""

    LOG = 0
    FLAG = 1
    AUGMENT = 2
    REROUTE = 3
    BLOCK = 4


@dataclass
class InterventionThresholds:
    """Risk score thresholds for each intervention level."""

    flag: float = 0.3
    augment: float = 0.5
    reroute: float = 0.7
    block: float = 0.9


# Domain-specific threshold profiles: some agent types are stricter
DOMAIN_PROFILES: dict[str, InterventionThresholds] = {
    "RAG": InterventionThresholds(flag=0.25, augment=0.40, reroute=0.60, block=0.85),
    "AUTONOMOUS": InterventionThresholds(flag=0.20, augment=0.35, reroute=0.55, block=0.80),
    "CODING": InterventionThresholds(flag=0.30, augment=0.50, reroute=0.70, block=0.90),
    "WORKFLOW": InterventionThresholds(flag=0.30, augment=0.50, reroute=0.70, block=0.90),
    "CHATBOT": InterventionThresholds(flag=0.35, augment=0.55, reroute=0.75, block=0.92),
}

# Mode → maximum intervention level allowed
_MODE_CAPS: dict[str, InterventionLevel] = {
    "OBSERVE": InterventionLevel.LOG,
    "ASSISTED": InterventionLevel.REROUTE,
    "AUTONOMOUS": InterventionLevel.BLOCK,
}


@dataclass
class InterventionDecision:
    """Result of intervention evaluation."""

    level: InterventionLevel
    action: str  # "log", "flag", "augment", "reroute", "block"
    reason: str
    risk_score: float
    rerouted_model: Optional[str] = None
    augmented_prompt: Optional[str] = None
    should_block: bool = False


class InterventionEngine:
    """Evaluates risk scores against thresholds and applies mode gates."""

    def __init__(
        self,
        default_thresholds: Optional[InterventionThresholds] = None,
    ) -> None:
        self._default_thresholds = default_thresholds or InterventionThresholds()

    def evaluate(
        self,
        risk_score: float,
        intervention_mode: str,
        prompt: str,
        current_model: Optional[str] = None,
        agent_type: Optional[str] = None,
        threshold_overrides: Optional[dict] = None,
    ) -> InterventionDecision:
        """Determine intervention action based on risk score and mode.

        Args:
            risk_score: Composite risk score 0.0-1.0.
            intervention_mode: OBSERVE, ASSISTED, or AUTONOMOUS.
            prompt: The original prompt (for augmentation).
            current_model: The model currently selected (for rerouting).
            agent_type: Agent type classification (for domain profiles).
            threshold_overrides: Per-agent threshold overrides from JSONB.

        Returns:
            InterventionDecision with action and metadata.
        """
        mode = intervention_mode.upper()
        mode_cap = _MODE_CAPS.get(mode, InterventionLevel.LOG)

        # Resolve thresholds: per-agent overrides > domain profile > defaults
        thresholds = self._resolve_thresholds(agent_type, threshold_overrides)

        # Determine raw intervention level from risk score
        raw_level = self._score_to_level(risk_score, thresholds)

        # Apply mode cap
        effective_level = InterventionLevel(min(raw_level.value, mode_cap.value))

        # Build decision
        return self._build_decision(
            effective_level, risk_score, prompt, current_model, mode, raw_level,
        )

    def _resolve_thresholds(
        self,
        agent_type: Optional[str],
        overrides: Optional[dict],
    ) -> InterventionThresholds:
        """Resolve threshold cascade: overrides > domain > defaults."""
        # Start with defaults
        thresholds = self._default_thresholds

        # Apply domain profile if agent type is known
        if agent_type:
            domain = DOMAIN_PROFILES.get(agent_type.upper())
            if domain:
                thresholds = domain

        # Apply per-agent overrides
        if overrides:
            thresholds = InterventionThresholds(
                flag=overrides.get("flag", thresholds.flag),
                augment=overrides.get("augment", thresholds.augment),
                reroute=overrides.get("reroute", thresholds.reroute),
                block=overrides.get("block", thresholds.block),
            )

        return thresholds

    @staticmethod
    def _score_to_level(
        risk_score: float,
        thresholds: InterventionThresholds,
    ) -> InterventionLevel:
        """Map a risk score to an intervention level via thresholds."""
        if risk_score >= thresholds.block:
            return InterventionLevel.BLOCK
        if risk_score >= thresholds.reroute:
            return InterventionLevel.REROUTE
        if risk_score >= thresholds.augment:
            return InterventionLevel.AUGMENT
        if risk_score >= thresholds.flag:
            return InterventionLevel.FLAG
        return InterventionLevel.LOG

    @staticmethod
    def _build_decision(
        level: InterventionLevel,
        risk_score: float,
        prompt: str,
        current_model: Optional[str],
        mode: str,
        raw_level: InterventionLevel,
    ) -> InterventionDecision:
        """Build InterventionDecision from resolved level."""
        capped = raw_level.value > level.value
        cap_note = f" (capped from {raw_level.name} by {mode} mode)" if capped else ""

        if level == InterventionLevel.BLOCK:
            return InterventionDecision(
                level=level,
                action="block",
                reason=f"Risk score {risk_score:.4f} exceeds block threshold{cap_note}",
                risk_score=risk_score,
                should_block=True,
            )

        if level == InterventionLevel.REROUTE:
            rerouted = _select_stronger_model(current_model)
            return InterventionDecision(
                level=level,
                action="reroute",
                reason=f"Risk score {risk_score:.4f} triggered reroute{cap_note}",
                risk_score=risk_score,
                rerouted_model=rerouted,
            )

        if level == InterventionLevel.AUGMENT:
            return InterventionDecision(
                level=level,
                action="augment",
                reason=f"Risk score {risk_score:.4f} triggered prompt augmentation{cap_note}",
                risk_score=risk_score,
                augmented_prompt=prompt + _AUGMENT_SUFFIX,
            )

        if level == InterventionLevel.FLAG:
            return InterventionDecision(
                level=level,
                action="flag",
                reason=f"Risk score {risk_score:.4f} flagged for review{cap_note}",
                risk_score=risk_score,
            )

        # LOG
        return InterventionDecision(
            level=level,
            action="log",
            reason=f"Risk score {risk_score:.4f} within normal range{cap_note}",
            risk_score=risk_score,
        )


def _select_stronger_model(current_model: Optional[str]) -> str:
    """Select the highest-quality model that isn't the current one."""
    from app.services.routing import get_model_catalog

    catalog = get_model_catalog()
    ranked = sorted(catalog.items(), key=lambda x: x[1].get("quality_score", 0), reverse=True)
    for model_id, _ in ranked:
        if model_id != current_model:
            return model_id
    return ranked[0][0] if ranked else "claude-opus-4-6"
