"""Tests for the intervention engine."""

import pytest

from app.services.intervention_engine import (
    DOMAIN_PROFILES,
    InterventionDecision,
    InterventionEngine,
    InterventionLevel,
    InterventionThresholds,
    _select_stronger_model,
)


class TestInterventionLevel:
    def test_ordering(self):
        assert InterventionLevel.LOG < InterventionLevel.FLAG
        assert InterventionLevel.FLAG < InterventionLevel.AUGMENT
        assert InterventionLevel.AUGMENT < InterventionLevel.REROUTE
        assert InterventionLevel.REROUTE < InterventionLevel.BLOCK

    def test_values(self):
        assert InterventionLevel.LOG.value == 0
        assert InterventionLevel.BLOCK.value == 4


class TestSelectStrongerModel:
    def test_different_from_current(self):
        result = _select_stronger_model("gpt-4o")
        assert result != "gpt-4o"

    def test_none_returns_highest_quality(self):
        result = _select_stronger_model(None)
        # Should return some model from the catalog
        from app.services.routing import get_model_catalog
        assert result in get_model_catalog()

    def test_avoids_current_model(self):
        result = _select_stronger_model("claude-opus-4-6")
        assert result != "claude-opus-4-6"


# ── OBSERVE mode tests ──────────────────────────────────────────────


class TestObserveMode:
    def setup_method(self):
        self.engine = InterventionEngine()

    def test_low_risk_logs(self):
        d = self.engine.evaluate(0.1, "OBSERVE", "test")
        assert d.level == InterventionLevel.LOG
        assert d.action == "log"

    def test_high_risk_still_logs(self):
        """OBSERVE mode caps everything at LOG."""
        d = self.engine.evaluate(0.95, "OBSERVE", "test")
        assert d.level == InterventionLevel.LOG
        assert d.action == "log"
        assert "capped" in d.reason

    def test_medium_risk_still_logs(self):
        d = self.engine.evaluate(0.6, "OBSERVE", "test")
        assert d.level == InterventionLevel.LOG

    def test_never_blocks(self):
        d = self.engine.evaluate(1.0, "OBSERVE", "test")
        assert d.should_block is False

    def test_never_augments(self):
        d = self.engine.evaluate(0.55, "OBSERVE", "test")
        assert d.augmented_prompt is None

    def test_never_reroutes(self):
        d = self.engine.evaluate(0.8, "OBSERVE", "test")
        assert d.rerouted_model is None


# ── ASSISTED mode tests ─────────────────────────────────────────────


class TestAssistedMode:
    def setup_method(self):
        self.engine = InterventionEngine()

    def test_low_risk_logs(self):
        d = self.engine.evaluate(0.1, "ASSISTED", "test")
        assert d.level == InterventionLevel.LOG

    def test_flag_threshold(self):
        d = self.engine.evaluate(0.35, "ASSISTED", "test")
        assert d.level == InterventionLevel.FLAG
        assert d.action == "flag"

    def test_augment_threshold(self):
        d = self.engine.evaluate(0.55, "ASSISTED", "test prompt")
        assert d.level == InterventionLevel.AUGMENT
        assert d.action == "augment"
        assert d.augmented_prompt is not None
        assert "test prompt" in d.augmented_prompt

    def test_reroute_threshold(self):
        d = self.engine.evaluate(0.75, "ASSISTED", "test", current_model="gpt-4o")
        assert d.level == InterventionLevel.REROUTE
        assert d.action == "reroute"
        assert d.rerouted_model is not None
        assert d.rerouted_model != "gpt-4o"

    def test_block_capped_to_reroute(self):
        """ASSISTED mode caps at REROUTE — cannot BLOCK."""
        d = self.engine.evaluate(0.95, "ASSISTED", "test")
        assert d.level == InterventionLevel.REROUTE
        assert d.action == "reroute"
        assert d.should_block is False
        assert "capped" in d.reason


# ── AUTONOMOUS mode tests ───────────────────────────────────────────


class TestAutonomousMode:
    def setup_method(self):
        self.engine = InterventionEngine()

    def test_low_risk_logs(self):
        d = self.engine.evaluate(0.1, "AUTONOMOUS", "test")
        assert d.level == InterventionLevel.LOG

    def test_can_block(self):
        d = self.engine.evaluate(0.95, "AUTONOMOUS", "test")
        assert d.level == InterventionLevel.BLOCK
        assert d.action == "block"
        assert d.should_block is True

    def test_full_range(self):
        """AUTONOMOUS mode allows all 5 levels."""
        levels_seen = set()
        for score in [0.1, 0.35, 0.55, 0.75, 0.95]:
            d = self.engine.evaluate(score, "AUTONOMOUS", "test")
            levels_seen.add(d.level)
        assert len(levels_seen) == 5


# ── Threshold boundary tests ────────────────────────────────────────


class TestThresholdBoundaries:
    def setup_method(self):
        self.engine = InterventionEngine()

    def test_exactly_at_flag(self):
        d = self.engine.evaluate(0.3, "AUTONOMOUS", "test")
        assert d.level == InterventionLevel.FLAG

    def test_just_below_flag(self):
        d = self.engine.evaluate(0.299, "AUTONOMOUS", "test")
        assert d.level == InterventionLevel.LOG

    def test_exactly_at_block(self):
        d = self.engine.evaluate(0.9, "AUTONOMOUS", "test")
        assert d.level == InterventionLevel.BLOCK

    def test_just_below_block(self):
        d = self.engine.evaluate(0.899, "AUTONOMOUS", "test")
        assert d.level == InterventionLevel.REROUTE


# ── Domain profile tests ────────────────────────────────────────────


class TestDomainProfiles:
    def setup_method(self):
        self.engine = InterventionEngine()

    def test_rag_stricter_than_chatbot(self):
        rag = DOMAIN_PROFILES["RAG"]
        chatbot = DOMAIN_PROFILES["CHATBOT"]
        assert rag.flag < chatbot.flag
        assert rag.block < chatbot.block

    def test_autonomous_agent_strictest(self):
        auto = DOMAIN_PROFILES["AUTONOMOUS"]
        assert auto.flag <= DOMAIN_PROFILES["RAG"].flag
        assert auto.block <= DOMAIN_PROFILES["RAG"].block

    def test_rag_flags_at_lower_risk(self):
        # RAG flags at 0.25 while default is 0.30
        d = self.engine.evaluate(0.27, "ASSISTED", "test", agent_type="RAG")
        assert d.level == InterventionLevel.FLAG

    def test_chatbot_more_lenient(self):
        # CHATBOT flags at 0.35 instead of default 0.30
        d = self.engine.evaluate(0.32, "ASSISTED", "test", agent_type="CHATBOT")
        assert d.level == InterventionLevel.LOG


# ── Per-agent override tests ────────────────────────────────────────


class TestPerAgentOverrides:
    def setup_method(self):
        self.engine = InterventionEngine()

    def test_override_flag_threshold(self):
        d = self.engine.evaluate(
            0.15, "ASSISTED", "test",
            threshold_overrides={"flag": 0.1},
        )
        assert d.level == InterventionLevel.FLAG

    def test_override_block_threshold(self):
        d = self.engine.evaluate(
            0.6, "AUTONOMOUS", "test",
            threshold_overrides={"block": 0.5},
        )
        assert d.level == InterventionLevel.BLOCK

    def test_overrides_beat_domain_profile(self):
        # RAG flags at 0.25, but override raises it to 0.5
        d = self.engine.evaluate(
            0.3, "ASSISTED", "test",
            agent_type="RAG",
            threshold_overrides={"flag": 0.5},
        )
        assert d.level == InterventionLevel.LOG


# ── Mode × Level combination tests ──────────────────────────────────


class TestModeXLevelCombinations:
    """Test all 3 modes × 5 levels = 15 combinations."""

    def setup_method(self):
        self.engine = InterventionEngine()

    @pytest.mark.parametrize(
        "risk_score,expected_raw",
        [
            (0.1, InterventionLevel.LOG),
            (0.35, InterventionLevel.FLAG),
            (0.55, InterventionLevel.AUGMENT),
            (0.75, InterventionLevel.REROUTE),
            (0.95, InterventionLevel.BLOCK),
        ],
    )
    def test_observe_caps_all_to_log(self, risk_score, expected_raw):
        d = self.engine.evaluate(risk_score, "OBSERVE", "test")
        assert d.level == InterventionLevel.LOG

    @pytest.mark.parametrize(
        "risk_score,expected",
        [
            (0.1, InterventionLevel.LOG),
            (0.35, InterventionLevel.FLAG),
            (0.55, InterventionLevel.AUGMENT),
            (0.75, InterventionLevel.REROUTE),
            (0.95, InterventionLevel.REROUTE),  # capped
        ],
    )
    def test_assisted_caps_at_reroute(self, risk_score, expected):
        d = self.engine.evaluate(risk_score, "ASSISTED", "test")
        assert d.level == expected

    @pytest.mark.parametrize(
        "risk_score,expected",
        [
            (0.1, InterventionLevel.LOG),
            (0.35, InterventionLevel.FLAG),
            (0.55, InterventionLevel.AUGMENT),
            (0.75, InterventionLevel.REROUTE),
            (0.95, InterventionLevel.BLOCK),
        ],
    )
    def test_autonomous_no_cap(self, risk_score, expected):
        d = self.engine.evaluate(risk_score, "AUTONOMOUS", "test")
        assert d.level == expected


# ── Decision detail tests ────────────────────────────────────────────


class TestDecisionDetails:
    def setup_method(self):
        self.engine = InterventionEngine()

    def test_augmented_prompt_has_suffix(self):
        d = self.engine.evaluate(0.55, "ASSISTED", "What is Python?")
        assert d.augmented_prompt.startswith("What is Python?")
        assert "verified for accuracy" in d.augmented_prompt

    def test_reroute_selects_different_model(self):
        d = self.engine.evaluate(0.75, "ASSISTED", "test", current_model="gpt-4o")
        assert d.rerouted_model != "gpt-4o"
        assert d.rerouted_model is not None

    def test_block_sets_flag(self):
        d = self.engine.evaluate(0.95, "AUTONOMOUS", "test")
        assert d.should_block is True

    def test_risk_score_in_decision(self):
        d = self.engine.evaluate(0.42, "ASSISTED", "test")
        assert d.risk_score == 0.42

    def test_case_insensitive_mode(self):
        d = self.engine.evaluate(0.95, "observe", "test")
        assert d.level == InterventionLevel.LOG
