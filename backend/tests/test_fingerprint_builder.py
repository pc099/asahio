"""Tests for the fingerprint builder service."""

import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone

from app.services.fingerprint_builder import FingerprintBuilder, FingerprintUpdate


def _make_fingerprint(**overrides):
    """Create a mock fingerprint object with default values."""
    fp = MagicMock()
    fp.total_observations = overrides.get("total_observations", 0)
    fp.avg_complexity = overrides.get("avg_complexity", 0.0)
    fp.avg_context_length = overrides.get("avg_context_length", 0.0)
    fp.hallucination_rate = overrides.get("hallucination_rate", 0.0)
    fp.model_distribution = overrides.get("model_distribution", {})
    fp.cache_hit_rate = overrides.get("cache_hit_rate", 0.0)
    fp.baseline_confidence = overrides.get("baseline_confidence", 0.0)
    fp.last_updated_at = overrides.get("last_updated_at", datetime.now(timezone.utc))
    return fp


def _make_record(**overrides):
    """Create a FingerprintUpdate with default values."""
    defaults = {
        "agent_id": "agent-1",
        "org_id": "org-1",
        "complexity_score": 0.5,
        "context_length": 100,
        "model_used": "gpt-4o",
        "cache_hit": False,
        "hallucination_detected": False,
    }
    defaults.update(overrides)
    return FingerprintUpdate(**defaults)


@pytest.fixture
def builder() -> FingerprintBuilder:
    return FingerprintBuilder(alpha=0.1)


# ── EMA Updates ─────────────────────────────────────────────────────────


class TestEMAUpdate:
    def test_first_observation_uses_raw_value(self, builder: FingerprintBuilder) -> None:
        fp = _make_fingerprint(total_observations=0, avg_complexity=0.0)
        record = _make_record(complexity_score=0.7)
        builder.update_fingerprint(fp, record)
        assert fp.avg_complexity == 0.7
        assert fp.total_observations == 1

    def test_subsequent_observations_use_ema(self, builder: FingerprintBuilder) -> None:
        fp = _make_fingerprint(total_observations=5, avg_complexity=0.5)
        record = _make_record(complexity_score=1.0)
        builder.update_fingerprint(fp, record)
        # EMA: 0.1 * 1.0 + 0.9 * 0.5 = 0.55
        assert fp.avg_complexity == pytest.approx(0.55, abs=0.01)

    def test_multiple_updates_converge(self, builder: FingerprintBuilder) -> None:
        fp = _make_fingerprint(total_observations=0, avg_complexity=0.0)
        # Feed 20 observations all at 0.8
        for _ in range(20):
            record = _make_record(complexity_score=0.8)
            builder.update_fingerprint(fp, record)
        # Should converge towards 0.8
        assert fp.avg_complexity == pytest.approx(0.8, abs=0.05)
        assert fp.total_observations == 20


# ── Model Distribution ──────────────────────────────────────────────────


class TestModelDistribution:
    def test_single_model_tracking(self, builder: FingerprintBuilder) -> None:
        fp = _make_fingerprint()
        builder.update_fingerprint(fp, _make_record(model_used="gpt-4o"))
        assert fp.model_distribution == {"gpt-4o": 1}

    def test_multiple_models_tracked(self, builder: FingerprintBuilder) -> None:
        fp = _make_fingerprint()
        builder.update_fingerprint(fp, _make_record(model_used="gpt-4o"))
        builder.update_fingerprint(fp, _make_record(model_used="claude-3-5-sonnet"))
        builder.update_fingerprint(fp, _make_record(model_used="gpt-4o"))
        assert fp.model_distribution == {"gpt-4o": 2, "claude-3-5-sonnet": 1}

    def test_distribution_preserved_across_updates(self, builder: FingerprintBuilder) -> None:
        fp = _make_fingerprint(model_distribution={"gpt-4o": 5})
        builder.update_fingerprint(fp, _make_record(model_used="gpt-4o"))
        assert fp.model_distribution["gpt-4o"] == 6


# ── Cache Hit Rate ──────────────────────────────────────────────────────


class TestCacheHitRate:
    def test_all_hits(self, builder: FingerprintBuilder) -> None:
        fp = _make_fingerprint()
        for _ in range(10):
            builder.update_fingerprint(fp, _make_record(cache_hit=True))
        assert fp.cache_hit_rate == pytest.approx(1.0, abs=0.05)

    def test_all_misses(self, builder: FingerprintBuilder) -> None:
        fp = _make_fingerprint()
        for _ in range(10):
            builder.update_fingerprint(fp, _make_record(cache_hit=False))
        assert fp.cache_hit_rate == pytest.approx(0.0, abs=0.01)

    def test_mixed_cache(self, builder: FingerprintBuilder) -> None:
        fp = _make_fingerprint()
        # 5 hits then 5 misses — EMA will be closer to 0 (recent misses)
        for _ in range(5):
            builder.update_fingerprint(fp, _make_record(cache_hit=True))
        rate_after_hits = float(fp.cache_hit_rate)
        for _ in range(5):
            builder.update_fingerprint(fp, _make_record(cache_hit=False))
        assert float(fp.cache_hit_rate) < rate_after_hits


# ── Baseline Confidence ─────────────────────────────────────────────────


class TestBaselineConfidence:
    def test_low_observations_low_confidence(self, builder: FingerprintBuilder) -> None:
        fp = _make_fingerprint(total_observations=3, hallucination_rate=0.0, model_distribution={"gpt-4o": 3})
        conf = builder.calculate_baseline_confidence(fp)
        assert conf < 0.8  # Low volume penalty

    def test_many_observations_high_confidence(self, builder: FingerprintBuilder) -> None:
        fp = _make_fingerprint(
            total_observations=100,
            hallucination_rate=0.0,
            model_distribution={"gpt-4o": 100},
        )
        conf = builder.calculate_baseline_confidence(fp)
        assert conf > 0.8  # Full volume + accuracy + consistency

    def test_high_hallucination_lowers_confidence(self, builder: FingerprintBuilder) -> None:
        fp_clean = _make_fingerprint(
            total_observations=50, hallucination_rate=0.0, model_distribution={"gpt-4o": 50},
        )
        fp_dirty = _make_fingerprint(
            total_observations=50, hallucination_rate=0.5, model_distribution={"gpt-4o": 50},
        )
        conf_clean = builder.calculate_baseline_confidence(fp_clean)
        conf_dirty = builder.calculate_baseline_confidence(fp_dirty)
        assert conf_dirty < conf_clean
