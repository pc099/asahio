"""Risk scoring engine — composite 0.0-1.0 risk score from 5 factors.

Two computation modes:
- fast_estimate(): sync, <2ms, skips Model C (for gateway critical path)
- full_computation(): async, includes Model C + hallucination check (for background)

Reuses existing services: StructuralExtractor, DependencyClassifier, HallucinationDetector.
"""

import logging
import math
import time
from dataclasses import dataclass, field
from typing import Optional

from app.services.dependency_classifier import DependencyClassifier, DependencyLevel
from app.services.hallucination_detector import HallucinationDetector
from app.services.structural_extractor import StructuralExtractor

logger = logging.getLogger(__name__)

# Default model risk rates when no fingerprint exists
_MODEL_DEFAULT_RISK: dict[str, float] = {
    "gpt-4o": 0.08,
    "gpt-4-turbo": 0.10,
    "gpt-4o-mini": 0.15,
    "gpt-3.5-turbo": 0.22,
    "claude-opus-4": 0.06,
    "claude-sonnet-4": 0.09,
    "claude-3-5-sonnet": 0.09,
    "claude-3-haiku": 0.18,
    "claude-haiku-4": 0.18,
}
_DEFAULT_MODEL_RISK = 0.12


@dataclass
class RiskScoringConfig:
    """Weights for the 5 risk factors. Must sum to 1.0."""

    sequence_position_weight: float = 0.15
    model_specific_weight: float = 0.25
    propagation_weight: float = 0.20
    complexity_weight: float = 0.20
    global_pattern_weight: float = 0.20


@dataclass
class RiskBreakdown:
    """Full risk score breakdown."""

    composite_score: float
    sequence_position_risk: float
    model_specific_risk: float
    propagation_amplifier: float
    complexity_risk: float
    global_pattern_risk: float
    is_fast_estimate: bool
    computation_time_ms: float
    factors: dict = field(default_factory=dict)


def _sigmoid(x: float) -> float:
    """Sigmoid function clamped to avoid overflow."""
    x = max(-10.0, min(10.0, x))
    return 1.0 / (1.0 + math.exp(-x))


def _sequence_position_risk(session_step: Optional[int]) -> float:
    """Risk based on position in multi-step session."""
    if session_step is None or session_step <= 0:
        return 0.2
    if session_step == 1:
        return 0.2
    if session_step <= 3:
        return 0.3
    if session_step <= 7:
        return 0.4
    return 0.5


def _model_specific_risk(
    model_id: Optional[str],
    fingerprint_hallucination_rate: Optional[float],
) -> float:
    """Risk from model's hallucination tendency.

    Uses agent fingerprint data when available, falls back to model defaults.
    """
    if fingerprint_hallucination_rate is not None:
        return min(1.0, max(0.0, fingerprint_hallucination_rate))
    if model_id:
        # Normalize model_id for lookup
        model_lower = model_id.lower().strip()
        for key, risk in _MODEL_DEFAULT_RISK.items():
            if key in model_lower:
                return risk
    return _DEFAULT_MODEL_RISK


def _propagation_amplifier(dep_level: Optional[DependencyLevel]) -> float:
    """Amplifier based on dependency classification.

    INDEPENDENT=0.0, PARTIAL=0.3, DEPENDENT=0.6, CRITICAL=1.0
    Maps to: 1.0 + dep_score * 0.5, then normalize to [0, 1].
    """
    if dep_level is None:
        return 0.0
    dep_scores = {
        DependencyLevel.INDEPENDENT: 0.0,
        DependencyLevel.PARTIAL: 0.3,
        DependencyLevel.DEPENDENT: 0.6,
        DependencyLevel.CRITICAL: 1.0,
    }
    dep_score = dep_scores.get(dep_level, 0.0)
    # Normalize: raw range is 1.0-1.5, map to 0.0-1.0
    return dep_score


def _complexity_risk(complexity_score: float) -> float:
    """Transform complexity score through sigmoid centered at 0.5."""
    return _sigmoid((complexity_score - 0.5) * 6)


class RiskScoringEngine:
    """Computes composite risk scores for gateway requests."""

    def __init__(self, config: Optional[RiskScoringConfig] = None) -> None:
        self._config = config or RiskScoringConfig()
        self._extractor = StructuralExtractor()
        self._classifier = DependencyClassifier()
        self._detector = HallucinationDetector()

    def fast_estimate(
        self,
        prompt: str,
        model_id: Optional[str] = None,
        fingerprint_hallucination_rate: Optional[float] = None,
        session_step: Optional[int] = None,
    ) -> RiskBreakdown:
        """Synchronous fast risk estimate for the gateway critical path.

        Target: <2ms. Skips Model C global pool query.

        Args:
            prompt: The user prompt.
            model_id: The model being used.
            fingerprint_hallucination_rate: From AgentFingerprint if available.
            session_step: Current step in multi-step session.

        Returns:
            RiskBreakdown with is_fast_estimate=True.
        """
        start = time.perf_counter()
        cfg = self._config

        # Factor 1: Sequence position
        seq_risk = _sequence_position_risk(session_step)

        # Factor 2: Model-specific risk
        model_risk = _model_specific_risk(model_id, fingerprint_hallucination_rate)

        # Factor 3: Propagation amplifier via dependency classifier
        dep_classification = self._classifier.classify(prompt, session_step=session_step)
        prop_risk = _propagation_amplifier(dep_classification.level)

        # Factor 4: Complexity risk
        messages = [{"content": prompt}]
        complexity_result = self._extractor.query_complexity_score(messages)
        comp_risk = _complexity_risk(complexity_result.score)

        # Factor 5: Global pattern risk — skipped in fast path
        global_risk = 0.5  # neutral default

        # Weighted composite
        composite = (
            cfg.sequence_position_weight * seq_risk
            + cfg.model_specific_weight * model_risk
            + cfg.propagation_weight * prop_risk
            + cfg.complexity_weight * comp_risk
            + cfg.global_pattern_weight * global_risk
        )
        composite = round(min(1.0, max(0.0, composite)), 4)

        elapsed_ms = (time.perf_counter() - start) * 1000

        return RiskBreakdown(
            composite_score=composite,
            sequence_position_risk=round(seq_risk, 4),
            model_specific_risk=round(model_risk, 4),
            propagation_amplifier=round(prop_risk, 4),
            complexity_risk=round(comp_risk, 4),
            global_pattern_risk=round(global_risk, 4),
            is_fast_estimate=True,
            computation_time_ms=round(elapsed_ms, 2),
            factors={
                "dependency_level": dep_classification.level.value,
                "complexity_score": complexity_result.score,
                "model_id": model_id,
                "session_step": session_step,
            },
        )

    async def full_computation(
        self,
        prompt: str,
        response: str,
        model_id: Optional[str] = None,
        fingerprint_hallucination_rate: Optional[float] = None,
        session_step: Optional[int] = None,
        agent_type: Optional[str] = None,
        model_c_pool=None,
    ) -> RiskBreakdown:
        """Full async risk computation including Model C and hallucination check.

        Used in background processing after the LLM call completes.

        Args:
            prompt: The user prompt.
            response: The LLM response.
            model_id: The model used.
            fingerprint_hallucination_rate: From AgentFingerprint if available.
            session_step: Current step in multi-step session.
            agent_type: Agent type classification for Model C query.
            model_c_pool: ModelCPool instance for global risk prior.

        Returns:
            RiskBreakdown with is_fast_estimate=False.
        """
        start = time.perf_counter()
        cfg = self._config

        # Factor 1: Sequence position
        seq_risk = _sequence_position_risk(session_step)

        # Factor 2: Model-specific risk — enhanced with hallucination check
        halluc_result = self._detector.check(prompt, response)
        if halluc_result.detected:
            # If hallucination detected in this response, boost model risk
            model_risk = max(
                _model_specific_risk(model_id, fingerprint_hallucination_rate),
                halluc_result.confidence,
            )
        else:
            model_risk = _model_specific_risk(model_id, fingerprint_hallucination_rate)

        # Factor 3: Propagation amplifier
        dep_classification = self._classifier.classify(prompt, session_step=session_step)
        prop_risk = _propagation_amplifier(dep_classification.level)

        # Factor 4: Complexity risk
        messages = [{"content": prompt}]
        complexity_result = self._extractor.query_complexity_score(messages)
        comp_risk = _complexity_risk(complexity_result.score)

        # Factor 5: Global pattern risk via Model C
        global_risk = 0.5  # default
        if model_c_pool is not None:
            try:
                complexity_bucket = round(complexity_result.score * 10) / 10
                risk_prior = await model_c_pool.query_risk_prior(
                    agent_type=agent_type or "CHATBOT",
                    complexity_bucket=complexity_bucket,
                )
                if risk_prior.confidence > 0:
                    global_risk = risk_prior.risk_score
            except Exception:
                logger.debug("Model C query failed, using neutral prior")

        # Weighted composite
        composite = (
            cfg.sequence_position_weight * seq_risk
            + cfg.model_specific_weight * model_risk
            + cfg.propagation_weight * prop_risk
            + cfg.complexity_weight * comp_risk
            + cfg.global_pattern_weight * global_risk
        )
        composite = round(min(1.0, max(0.0, composite)), 4)

        elapsed_ms = (time.perf_counter() - start) * 1000

        return RiskBreakdown(
            composite_score=composite,
            sequence_position_risk=round(seq_risk, 4),
            model_specific_risk=round(model_risk, 4),
            propagation_amplifier=round(prop_risk, 4),
            complexity_risk=round(comp_risk, 4),
            global_pattern_risk=round(global_risk, 4),
            is_fast_estimate=False,
            computation_time_ms=round(elapsed_ms, 2),
            factors={
                "dependency_level": dep_classification.level.value,
                "complexity_score": complexity_result.score,
                "model_id": model_id,
                "session_step": session_step,
                "hallucination_detected": halluc_result.detected,
                "hallucination_confidence": halluc_result.confidence,
                "global_prior_confidence": global_risk,
            },
        )
