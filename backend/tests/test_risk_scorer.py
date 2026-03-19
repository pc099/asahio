"""Tests for the risk scoring engine."""

import asyncio
import math
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.risk_scorer import (
    RiskBreakdown,
    RiskScoringConfig,
    RiskScoringEngine,
    _complexity_risk,
    _model_specific_risk,
    _propagation_amplifier,
    _sequence_position_risk,
    _sigmoid,
)
from app.services.dependency_classifier import DependencyLevel
from app.services.model_c_pool import ModelCPool, RiskPrior


# ── Helper factor function tests ───────────────────────────────────────


class TestSigmoid:
    def test_center(self):
        assert _sigmoid(0.0) == pytest.approx(0.5, abs=0.001)

    def test_positive(self):
        assert _sigmoid(5.0) > 0.99

    def test_negative(self):
        assert _sigmoid(-5.0) < 0.01

    def test_no_overflow(self):
        assert _sigmoid(100.0) == pytest.approx(1.0, abs=0.001)
        assert _sigmoid(-100.0) == pytest.approx(0.0, abs=0.001)


class TestSequencePositionRisk:
    def test_none_session(self):
        assert _sequence_position_risk(None) == 0.2

    def test_step_1(self):
        assert _sequence_position_risk(1) == 0.2

    def test_step_2_3(self):
        assert _sequence_position_risk(2) == 0.3
        assert _sequence_position_risk(3) == 0.3

    def test_step_4_7(self):
        assert _sequence_position_risk(4) == 0.4
        assert _sequence_position_risk(7) == 0.4

    def test_step_8_plus(self):
        assert _sequence_position_risk(8) == 0.5
        assert _sequence_position_risk(20) == 0.5


class TestModelSpecificRisk:
    def test_fingerprint_overrides_default(self):
        assert _model_specific_risk("gpt-4o", 0.35) == 0.35

    def test_fingerprint_clamped(self):
        assert _model_specific_risk("gpt-4o", 1.5) == 1.0
        assert _model_specific_risk("gpt-4o", -0.1) == 0.0

    def test_known_model_default(self):
        assert _model_specific_risk("gpt-4o", None) == 0.08
        assert _model_specific_risk("gpt-3.5-turbo", None) == 0.22

    def test_known_model_case_insensitive(self):
        assert _model_specific_risk("GPT-4O", None) == 0.08

    def test_unknown_model_fallback(self):
        assert _model_specific_risk("some-unknown-model", None) == 0.12

    def test_no_model_no_fingerprint(self):
        assert _model_specific_risk(None, None) == 0.12


class TestPropagationAmplifier:
    def test_none(self):
        assert _propagation_amplifier(None) == 0.0

    def test_independent(self):
        assert _propagation_amplifier(DependencyLevel.INDEPENDENT) == 0.0

    def test_partial(self):
        assert _propagation_amplifier(DependencyLevel.PARTIAL) == 0.3

    def test_dependent(self):
        assert _propagation_amplifier(DependencyLevel.DEPENDENT) == 0.6

    def test_critical(self):
        assert _propagation_amplifier(DependencyLevel.CRITICAL) == 1.0


class TestComplexityRisk:
    def test_low_complexity(self):
        result = _complexity_risk(0.1)
        assert result < 0.1

    def test_mid_complexity(self):
        result = _complexity_risk(0.5)
        assert result == pytest.approx(0.5, abs=0.01)

    def test_high_complexity(self):
        result = _complexity_risk(0.9)
        assert result > 0.9

    def test_bounds(self):
        assert 0.0 <= _complexity_risk(0.0) <= 1.0
        assert 0.0 <= _complexity_risk(1.0) <= 1.0


# ── RiskScoringEngine tests ────────────────────────────────────────────


class TestFastEstimate:
    def setup_method(self):
        self.engine = RiskScoringEngine()

    def test_returns_risk_breakdown(self):
        result = self.engine.fast_estimate("Hello, how are you?")
        assert isinstance(result, RiskBreakdown)
        assert result.is_fast_estimate is True

    def test_score_in_bounds(self):
        result = self.engine.fast_estimate("What is Python?")
        assert 0.0 <= result.composite_score <= 1.0

    def test_all_factors_in_bounds(self):
        result = self.engine.fast_estimate(
            "Explain distributed systems architecture",
            model_id="gpt-4o",
            session_step=5,
        )
        assert 0.0 <= result.sequence_position_risk <= 1.0
        assert 0.0 <= result.model_specific_risk <= 1.0
        assert 0.0 <= result.propagation_amplifier <= 1.0
        assert 0.0 <= result.complexity_risk <= 1.0
        assert 0.0 <= result.global_pattern_risk <= 1.0

    def test_fast_estimate_speed(self):
        """Fast estimate must complete in <5ms (generous for CI)."""
        start = time.perf_counter()
        for _ in range(10):
            self.engine.fast_estimate("Explain Python decorators")
        elapsed = (time.perf_counter() - start) * 1000
        avg_ms = elapsed / 10
        assert avg_ms < 5.0, f"Fast estimate took {avg_ms:.2f}ms on average"

    def test_global_pattern_is_neutral(self):
        """Fast estimate skips Model C, so global_pattern_risk should be 0.5."""
        result = self.engine.fast_estimate("test prompt")
        assert result.global_pattern_risk == 0.5

    def test_fingerprint_used_when_provided(self):
        result_with = self.engine.fast_estimate(
            "test", model_id="gpt-4o", fingerprint_hallucination_rate=0.5,
        )
        result_without = self.engine.fast_estimate(
            "test", model_id="gpt-4o", fingerprint_hallucination_rate=None,
        )
        assert result_with.model_specific_risk == 0.5
        assert result_without.model_specific_risk == 0.08

    def test_higher_session_step_increases_risk(self):
        low = self.engine.fast_estimate("test", session_step=1)
        high = self.engine.fast_estimate("test", session_step=10)
        assert high.sequence_position_risk > low.sequence_position_risk

    def test_factors_dict_populated(self):
        result = self.engine.fast_estimate(
            "test prompt", model_id="gpt-4o", session_step=3,
        )
        assert "dependency_level" in result.factors
        assert "complexity_score" in result.factors
        assert result.factors["model_id"] == "gpt-4o"
        assert result.factors["session_step"] == 3

    def test_computation_time_recorded(self):
        result = self.engine.fast_estimate("test")
        assert result.computation_time_ms >= 0


class TestFullComputation:
    def setup_method(self):
        self.engine = RiskScoringEngine()

    @pytest.mark.asyncio
    async def test_returns_risk_breakdown(self):
        result = await self.engine.full_computation(
            prompt="What is Python?",
            response="Python is a programming language.",
        )
        assert isinstance(result, RiskBreakdown)
        assert result.is_fast_estimate is False

    @pytest.mark.asyncio
    async def test_score_in_bounds(self):
        result = await self.engine.full_computation(
            prompt="test", response="test response",
        )
        assert 0.0 <= result.composite_score <= 1.0

    @pytest.mark.asyncio
    async def test_hallucination_boosts_risk(self):
        # Response with multiple hallucination signals:
        # overconfident + hedging + fake citations (confidence >= 0.5 threshold)
        halluc_response = (
            "I am absolutely 100% certain that this is definitely correct. "
            "But maybe it could possibly be wrong, perhaps not. "
            "According to Smith et al., 2019 and Jones et al., 2020 and "
            "Brown et al., 2021 this is well established."
        )
        result = await self.engine.full_computation(
            prompt="Is this true?",
            response=halluc_response,
        )
        assert result.factors.get("hallucination_detected") is True
        # Should have higher model risk than baseline
        assert result.model_specific_risk > 0.12

    @pytest.mark.asyncio
    async def test_model_c_pool_integration(self):
        pool = ModelCPool()
        result = await self.engine.full_computation(
            prompt="test", response="test",
            model_c_pool=pool, agent_type="CHATBOT",
        )
        # With empty pool, should get neutral 0.5 prior but confidence=0
        assert isinstance(result.global_pattern_risk, float)

    @pytest.mark.asyncio
    async def test_model_c_pool_error_handled(self):
        """Model C errors should not crash scoring."""
        bad_pool = MagicMock()
        bad_pool.query_risk_prior = AsyncMock(side_effect=RuntimeError("pool down"))
        result = await self.engine.full_computation(
            prompt="test", response="test",
            model_c_pool=bad_pool,
        )
        # Should fall back to neutral
        assert result.global_pattern_risk == 0.5

    @pytest.mark.asyncio
    async def test_factors_include_hallucination_info(self):
        result = await self.engine.full_computation(
            prompt="test", response="A normal response.",
        )
        assert "hallucination_detected" in result.factors
        assert "hallucination_confidence" in result.factors


class TestCustomConfig:
    def test_custom_weights(self):
        config = RiskScoringConfig(
            sequence_position_weight=0.5,
            model_specific_weight=0.1,
            propagation_weight=0.1,
            complexity_weight=0.1,
            global_pattern_weight=0.2,
        )
        engine = RiskScoringEngine(config=config)
        result = engine.fast_estimate("test", session_step=10)
        # With session_step=10, sequence risk is 0.5, and weight is 0.5
        # So that factor alone contributes 0.25
        assert result.composite_score > 0.2
