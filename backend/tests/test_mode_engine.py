"""Tests for the mode transition engine."""

from datetime import datetime, timedelta, timezone

import pytest

from app.services.mode_engine import (
    ModeEligibility,
    ModeTransitionEngine,
    ModeTransitionGates,
)


def _now():
    return datetime.now(timezone.utc)


class TestCheckEligibility:
    def setup_method(self):
        self.engine = ModeTransitionEngine()

    def test_observe_eligible(self):
        entered = _now() - timedelta(days=20)
        e = self.engine.check_eligibility("OBSERVE", 0.70, entered)
        assert e.eligible is True
        assert e.suggested_mode == "ASSISTED"

    def test_observe_low_confidence(self):
        entered = _now() - timedelta(days=20)
        e = self.engine.check_eligibility("OBSERVE", 0.50, entered)
        assert e.eligible is False
        assert "below threshold" in e.reason

    def test_observe_too_few_days(self):
        entered = _now() - timedelta(days=5)
        e = self.engine.check_eligibility("OBSERVE", 0.70, entered)
        assert e.eligible is False
        assert "days" in e.reason

    def test_assisted_eligible(self):
        entered = _now() - timedelta(days=35)
        e = self.engine.check_eligibility("ASSISTED", 0.85, entered)
        assert e.eligible is True
        assert e.suggested_mode == "AUTONOMOUS"

    def test_assisted_low_confidence(self):
        entered = _now() - timedelta(days=35)
        e = self.engine.check_eligibility("ASSISTED", 0.75, entered)
        assert e.eligible is False

    def test_assisted_too_few_days(self):
        entered = _now() - timedelta(days=10)
        e = self.engine.check_eligibility("ASSISTED", 0.90, entered)
        assert e.eligible is False

    def test_autonomous_already_highest(self):
        e = self.engine.check_eligibility("AUTONOMOUS", 0.95, _now())
        assert e.eligible is False
        assert "highest" in e.reason

    def test_evidence_populated(self):
        entered = _now() - timedelta(days=20)
        e = self.engine.check_eligibility("OBSERVE", 0.70, entered, total_observations=50)
        assert "baseline_confidence" in e.evidence
        assert e.evidence["observations"] == 50

    def test_no_entered_at_still_works(self):
        """If mode_entered_at is None, skip duration check."""
        e = self.engine.check_eligibility("OBSERVE", 0.70, None)
        assert e.eligible is True


class TestValidateTransition:
    def setup_method(self):
        self.engine = ModeTransitionEngine()

    def test_same_mode_rejected(self):
        ok, reason = self.engine.validate_transition("OBSERVE", "OBSERVE", 0.7, None)
        assert ok is False
        assert "Already" in reason

    def test_downgrade_always_allowed(self):
        ok, reason = self.engine.validate_transition("AUTONOMOUS", "OBSERVE", 0.1, None)
        assert ok is True
        assert "Downgrade" in reason

    def test_downgrade_assisted_to_observe(self):
        ok, _ = self.engine.validate_transition("ASSISTED", "OBSERVE", 0.1, None)
        assert ok is True

    def test_skip_observe_to_autonomous(self):
        entered = _now() - timedelta(days=60)
        ok, reason = self.engine.validate_transition("OBSERVE", "AUTONOMOUS", 0.95, entered)
        assert ok is False
        assert "skip" in reason.lower()

    def test_observe_to_assisted_valid(self):
        entered = _now() - timedelta(days=20)
        ok, _ = self.engine.validate_transition("OBSERVE", "ASSISTED", 0.70, entered)
        assert ok is True

    def test_assisted_to_autonomous_needs_auth(self):
        entered = _now() - timedelta(days=35)
        ok, reason = self.engine.validate_transition(
            "ASSISTED", "AUTONOMOUS", 0.85, entered, operator_authorized=False,
        )
        assert ok is False
        assert "authorization" in reason.lower()

    def test_assisted_to_autonomous_with_auth(self):
        entered = _now() - timedelta(days=35)
        ok, _ = self.engine.validate_transition(
            "ASSISTED", "AUTONOMOUS", 0.85, entered, operator_authorized=True,
        )
        assert ok is True

    def test_unknown_mode_rejected(self):
        ok, reason = self.engine.validate_transition("UNKNOWN", "OBSERVE", 0.7, None)
        assert ok is False
        assert "Unknown" in reason


class TestAutoDowngrade:
    def setup_method(self):
        self.engine = ModeTransitionEngine()

    def test_observe_never_downgrades(self):
        should, _ = self.engine.should_auto_downgrade("OBSERVE", [
            {"severity": "CRITICAL", "anomaly_type": "hallucination_spike"},
        ])
        assert should is False

    def test_no_anomalies(self):
        should, _ = self.engine.should_auto_downgrade("ASSISTED", [])
        assert should is False

    def test_hallucination_spike_triggers(self):
        should, reason = self.engine.should_auto_downgrade("ASSISTED", [
            {"severity": "HIGH", "anomaly_type": "hallucination_spike"},
        ])
        assert should is True
        assert "hallucination_spike" in reason

    def test_model_drift_triggers(self):
        should, _ = self.engine.should_auto_downgrade("AUTONOMOUS", [
            {"severity": "HIGH", "anomaly_type": "model_drift"},
        ])
        assert should is True

    def test_low_severity_does_not_trigger(self):
        should, _ = self.engine.should_auto_downgrade("ASSISTED", [
            {"severity": "LOW", "anomaly_type": "hallucination_spike"},
        ])
        assert should is False

    def test_cache_degradation_not_trigger(self):
        """cache_degradation is not a downgrade trigger."""
        should, _ = self.engine.should_auto_downgrade("ASSISTED", [
            {"severity": "HIGH", "anomaly_type": "cache_degradation"},
        ])
        assert should is False


class TestCustomGates:
    def test_relaxed_gates(self):
        gates = ModeTransitionGates(
            observe_to_assisted_confidence=0.3,
            observe_to_assisted_days=1,
        )
        engine = ModeTransitionEngine(gates=gates)
        entered = _now() - timedelta(days=2)
        e = engine.check_eligibility("OBSERVE", 0.35, entered)
        assert e.eligible is True

    def test_strict_gates(self):
        gates = ModeTransitionGates(
            observe_to_assisted_confidence=0.95,
            observe_to_assisted_days=60,
        )
        engine = ModeTransitionEngine(gates=gates)
        entered = _now() - timedelta(days=30)
        e = engine.check_eligibility("OBSERVE", 0.90, entered)
        assert e.eligible is False
