"""Mode transition engine — confidence-gated intervention mode progression.

Transition gates:
  OBSERVE → ASSISTED:    baseline_confidence >= 0.65 AND >= 14 days in OBSERVE
  ASSISTED → AUTONOMOUS: baseline_confidence >= 0.82 AND >= 30 days in ASSISTED
                          AND operator_authorized

Rules:
  - Cannot skip levels (OBSERVE → AUTONOMOUS not allowed)
  - Downgrade always allowed (any mode → lower mode)
  - Auto-downgrade to OBSERVE on high-severity anomaly
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# Mode ordering for progression checks
_MODE_ORDER = {"OBSERVE": 0, "ASSISTED": 1, "AUTONOMOUS": 2}


@dataclass
class ModeTransitionGates:
    """Thresholds for mode progression."""

    observe_to_assisted_confidence: float = 0.65
    observe_to_assisted_days: int = 14
    assisted_to_autonomous_confidence: float = 0.82
    assisted_to_autonomous_days: int = 30


@dataclass
class ModeEligibility:
    """Whether an agent is eligible for a mode upgrade."""

    eligible: bool
    suggested_mode: Optional[str] = None
    reason: str = ""
    evidence: dict = field(default_factory=dict)


class ModeTransitionEngine:
    """Manages intervention mode transitions with confidence gates."""

    def __init__(self, gates: Optional[ModeTransitionGates] = None) -> None:
        self._gates = gates or ModeTransitionGates()

    def check_eligibility(
        self,
        current_mode: str,
        baseline_confidence: float,
        mode_entered_at: Optional[datetime],
        total_observations: int = 0,
        anomaly_count: int = 0,
    ) -> ModeEligibility:
        """Check if an agent is eligible for a mode upgrade.

        Args:
            current_mode: Current intervention mode.
            baseline_confidence: From AgentFingerprint.
            mode_entered_at: When the agent entered current mode.
            total_observations: Total observations for the agent.
            anomaly_count: Active anomaly count.

        Returns:
            ModeEligibility with eligibility and reason.
        """
        mode = current_mode.upper()
        now = datetime.now(timezone.utc)

        if mode == "AUTONOMOUS":
            return ModeEligibility(
                eligible=False,
                reason="Already at highest intervention mode",
            )

        if mode == "OBSERVE":
            return self._check_observe_to_assisted(
                baseline_confidence, mode_entered_at, now, total_observations,
            )

        if mode == "ASSISTED":
            return self._check_assisted_to_autonomous(
                baseline_confidence, mode_entered_at, now, total_observations,
            )

        return ModeEligibility(eligible=False, reason=f"Unknown mode: {mode}")

    def _check_observe_to_assisted(
        self,
        confidence: float,
        entered_at: Optional[datetime],
        now: datetime,
        observations: int,
    ) -> ModeEligibility:
        gates = self._gates
        evidence: dict = {
            "baseline_confidence": confidence,
            "required_confidence": gates.observe_to_assisted_confidence,
            "observations": observations,
        }

        # Check confidence
        if confidence < gates.observe_to_assisted_confidence:
            evidence["gap"] = round(gates.observe_to_assisted_confidence - confidence, 4)
            return ModeEligibility(
                eligible=False,
                reason=f"Confidence {confidence:.4f} below threshold "
                       f"{gates.observe_to_assisted_confidence}",
                evidence=evidence,
            )

        # Check duration
        if entered_at:
            days_in_mode = (now - entered_at).days
            evidence["days_in_mode"] = days_in_mode
            evidence["required_days"] = gates.observe_to_assisted_days
            if days_in_mode < gates.observe_to_assisted_days:
                return ModeEligibility(
                    eligible=False,
                    reason=f"Only {days_in_mode} days in OBSERVE "
                           f"(need {gates.observe_to_assisted_days})",
                    evidence=evidence,
                )

        return ModeEligibility(
            eligible=True,
            suggested_mode="ASSISTED",
            reason="Meets confidence and duration requirements for ASSISTED",
            evidence=evidence,
        )

    def _check_assisted_to_autonomous(
        self,
        confidence: float,
        entered_at: Optional[datetime],
        now: datetime,
        observations: int,
    ) -> ModeEligibility:
        gates = self._gates
        evidence: dict = {
            "baseline_confidence": confidence,
            "required_confidence": gates.assisted_to_autonomous_confidence,
            "observations": observations,
        }

        # Check confidence
        if confidence < gates.assisted_to_autonomous_confidence:
            evidence["gap"] = round(gates.assisted_to_autonomous_confidence - confidence, 4)
            return ModeEligibility(
                eligible=False,
                reason=f"Confidence {confidence:.4f} below threshold "
                       f"{gates.assisted_to_autonomous_confidence}",
                evidence=evidence,
            )

        # Check duration
        if entered_at:
            days_in_mode = (now - entered_at).days
            evidence["days_in_mode"] = days_in_mode
            evidence["required_days"] = gates.assisted_to_autonomous_days
            if days_in_mode < gates.assisted_to_autonomous_days:
                return ModeEligibility(
                    eligible=False,
                    reason=f"Only {days_in_mode} days in ASSISTED "
                           f"(need {gates.assisted_to_autonomous_days})",
                    evidence=evidence,
                )

        return ModeEligibility(
            eligible=True,
            suggested_mode="AUTONOMOUS",
            reason="Meets confidence and duration requirements for AUTONOMOUS "
                   "(operator authorization still required)",
            evidence=evidence,
        )

    def validate_transition(
        self,
        current_mode: str,
        target_mode: str,
        baseline_confidence: float,
        mode_entered_at: Optional[datetime],
        operator_authorized: bool = False,
    ) -> tuple[bool, str]:
        """Validate a specific mode transition request.

        Args:
            current_mode: Current intervention mode.
            target_mode: Requested target mode.
            baseline_confidence: From AgentFingerprint.
            mode_entered_at: When the agent entered current mode.
            operator_authorized: Whether an operator authorized this.

        Returns:
            (valid, reason) tuple.
        """
        current = current_mode.upper()
        target = target_mode.upper()

        if current == target:
            return False, "Already in requested mode"

        current_order = _MODE_ORDER.get(current)
        target_order = _MODE_ORDER.get(target)

        if current_order is None:
            return False, f"Unknown current mode: {current}"
        if target_order is None:
            return False, f"Unknown target mode: {target}"

        # Downgrade always allowed
        if target_order < current_order:
            return True, f"Downgrade from {current} to {target} is always allowed"

        # Cannot skip levels
        if target_order - current_order > 1:
            return False, (
                f"Cannot skip from {current} to {target}. "
                f"Must transition through intermediate modes."
            )

        # Check eligibility for the upgrade
        eligibility = self.check_eligibility(
            current, baseline_confidence, mode_entered_at,
        )
        if not eligibility.eligible:
            return False, eligibility.reason

        # AUTONOMOUS requires operator authorization
        if target == "AUTONOMOUS" and not operator_authorized:
            return False, "AUTONOMOUS mode requires explicit operator authorization"

        return True, f"Transition from {current} to {target} approved"

    def should_auto_downgrade(
        self,
        current_mode: str,
        anomalies: list[dict],
    ) -> tuple[bool, str]:
        """Check if an agent should be auto-downgraded due to anomalies.

        Args:
            current_mode: Current intervention mode.
            anomalies: List of anomaly dicts with 'severity' and 'anomaly_type' keys.

        Returns:
            (should_downgrade, reason) tuple.
        """
        mode = current_mode.upper()

        if mode == "OBSERVE":
            return False, "Already at lowest mode"

        # Check for high-severity anomalies
        high_severity = [
            a for a in anomalies
            if a.get("severity", "").upper() in ("HIGH", "CRITICAL")
        ]

        if not high_severity:
            return False, "No high-severity anomalies"

        # Auto-downgrade on distribution shift or hallucination spike
        trigger_types = {"hallucination_spike", "model_drift", "complexity_shift"}
        triggers = [
            a for a in high_severity
            if a.get("anomaly_type", "") in trigger_types
        ]

        if triggers:
            types = ", ".join(set(a["anomaly_type"] for a in triggers))
            return True, (
                f"Auto-downgrade to OBSERVE: {len(triggers)} high-severity "
                f"anomalies detected ({types})"
            )

        return False, "High-severity anomalies present but not auto-downgrade triggers"
