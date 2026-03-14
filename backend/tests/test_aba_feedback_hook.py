"""Tests for the ABA Feedback Hook in the routing engine."""

import pytest

from app.services.routing import ABAFeedbackHook


@pytest.fixture
def hook() -> ABAFeedbackHook:
    return ABAFeedbackHook(enabled=True)


class TestRecordObservation:
    def test_records_observation(self, hook: ABAFeedbackHook) -> None:
        hook.record_observation("agent-1", "gpt-4o", 150.0, quality_signal=0.9)
        assert len(hook._history["agent-1"]) == 1

    def test_noop_when_disabled(self) -> None:
        hook = ABAFeedbackHook(enabled=False)
        hook.record_observation("agent-1", "gpt-4o", 150.0)
        assert "agent-1" not in hook._history

    def test_caps_history_at_max(self) -> None:
        hook = ABAFeedbackHook(enabled=True, max_history=10)
        for i in range(20):
            hook.record_observation("agent-1", "gpt-4o", float(i))
        assert len(hook._history["agent-1"]) == 10

    def test_multiple_agents_tracked(self, hook: ABAFeedbackHook) -> None:
        hook.record_observation("agent-1", "gpt-4o", 100.0)
        hook.record_observation("agent-2", "claude-sonnet-4-5", 200.0)
        assert len(hook._history) == 2


class TestGetRoutingAdjustment:
    def test_returns_none_with_no_history(self, hook: ABAFeedbackHook) -> None:
        assert hook.get_routing_adjustment("agent-1") is None

    def test_returns_none_below_threshold(self, hook: ABAFeedbackHook) -> None:
        for _ in range(3):
            hook.record_observation("agent-1", "gpt-4o", 100.0)
        assert hook.get_routing_adjustment("agent-1") is None

    def test_returns_adjustments_with_history(self, hook: ABAFeedbackHook) -> None:
        for _ in range(10):
            hook.record_observation("agent-1", "gpt-4o", 150.0, quality_signal=0.8)
        adj = hook.get_routing_adjustment("agent-1")
        assert adj is not None
        assert "gpt-4o" in adj
        assert adj["gpt-4o"]["quality_boost"] > 0  # 0.8 > 0.5 baseline
        assert adj["gpt-4o"]["avg_latency"] == 150.0

    def test_low_quality_gives_negative_boost(self, hook: ABAFeedbackHook) -> None:
        for _ in range(10):
            hook.record_observation("agent-1", "gpt-4o", 200.0, quality_signal=0.2)
        adj = hook.get_routing_adjustment("agent-1")
        assert adj is not None
        assert adj["gpt-4o"]["quality_boost"] < 0

    def test_multiple_models_tracked(self, hook: ABAFeedbackHook) -> None:
        for _ in range(5):
            hook.record_observation("agent-1", "gpt-4o", 100.0, quality_signal=0.9)
        for _ in range(5):
            hook.record_observation("agent-1", "claude-sonnet-4-5", 200.0, quality_signal=0.6)
        adj = hook.get_routing_adjustment("agent-1")
        assert adj is not None
        assert "gpt-4o" in adj
        assert "claude-sonnet-4-5" in adj
        assert adj["gpt-4o"]["quality_boost"] > adj["claude-sonnet-4-5"]["quality_boost"]

    def test_confidence_boost_proportional(self, hook: ABAFeedbackHook) -> None:
        for _ in range(8):
            hook.record_observation("agent-1", "gpt-4o", 100.0)
        for _ in range(2):
            hook.record_observation("agent-1", "claude-sonnet-4-5", 100.0)
        adj = hook.get_routing_adjustment("agent-1")
        assert adj["gpt-4o"]["confidence_boost"] > adj["claude-sonnet-4-5"]["confidence_boost"]
