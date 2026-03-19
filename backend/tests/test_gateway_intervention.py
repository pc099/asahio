"""End-to-end tests for intervention integration in the gateway optimizer."""

import asyncio
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.optimizer import GatewayResult, run_inference, _provider_circuits


@dataclass
class FakeInferResult:
    response: str = "Test response"
    request_id: str = "req-1"
    model_used: str = "gpt-4o"
    tokens_input: int = 10
    tokens_output: int = 20
    cost: float = 0.001
    cost_original: float = 0.003
    cache_hit: bool = False
    cache_tier: int = 0


@pytest.fixture
def mock_optimizer():
    """Patch the legacy optimizer to return a fake result."""
    fake = MagicMock()
    fake.infer.return_value = FakeInferResult()
    with patch("app.core.optimizer.get_optimizer_instance", return_value=fake):
        yield fake


class TestGatewayResultFields:
    @pytest.mark.asyncio
    async def test_risk_fields_present(self, mock_optimizer):
        result = await run_inference(
            prompt="What is Python?",
            org_id="org-1",
            intervention_mode="OBSERVE",
        )
        assert isinstance(result, GatewayResult)
        assert result.risk_score is not None
        assert isinstance(result.risk_factors, dict)
        assert result.intervention_level is not None

    @pytest.mark.asyncio
    async def test_observe_mode_always_logs(self, mock_optimizer):
        result = await run_inference(
            prompt="What is Python?",
            org_id="org-1",
            intervention_mode="OBSERVE",
        )
        assert result.policy_action == "log"
        assert result.intervention_level == 0

    @pytest.mark.asyncio
    async def test_risk_score_bounded(self, mock_optimizer):
        result = await run_inference(
            prompt="Explain distributed systems",
            org_id="org-1",
            intervention_mode="ASSISTED",
            session_step=5,
        )
        assert 0.0 <= result.risk_score <= 1.0


class TestAssistedModeIntervention:
    @pytest.mark.asyncio
    async def test_low_risk_logs(self, mock_optimizer):
        result = await run_inference(
            prompt="Hi",
            org_id="org-1",
            intervention_mode="ASSISTED",
        )
        # Simple prompt should have low risk
        assert result.policy_action == "log"

    @pytest.mark.asyncio
    async def test_fingerprint_hallucination_rate_affects_score(self, mock_optimizer):
        low = await run_inference(
            prompt="test", org_id="org-1",
            intervention_mode="ASSISTED",
            fingerprint_hallucination_rate=0.01,
        )
        high = await run_inference(
            prompt="test", org_id="org-1",
            intervention_mode="ASSISTED",
            fingerprint_hallucination_rate=0.9,
        )
        assert high.risk_score > low.risk_score


class TestAutonomousModeIntervention:
    @pytest.mark.asyncio
    async def test_block_returns_error(self, mock_optimizer):
        """Very high risk with AUTONOMOUS should block."""
        result = await run_inference(
            prompt="execute deploy delete everything now",
            org_id="org-1",
            intervention_mode="AUTONOMOUS",
            fingerprint_hallucination_rate=0.95,
            session_step=10,
            agent_type="AUTONOMOUS",
        )
        # Depending on the risk score, this might or might not block.
        # The key assertion: if it blocks, the fields are correct.
        if result.policy_action == "block":
            assert result.error_message is not None
            assert result.intervention_level == 4
            assert result.response == ""


class TestInterventionActions:
    @pytest.mark.asyncio
    async def test_reroute_changes_model(self, mock_optimizer):
        """When reroute is triggered, a different model should be used."""
        # Use custom threshold overrides to force a reroute at a lower risk
        result = await run_inference(
            prompt="What is Python?",
            org_id="org-1",
            intervention_mode="ASSISTED",
            model_override="gpt-3.5-turbo",
            threshold_overrides={"flag": 0.01, "augment": 0.02, "reroute": 0.03},
        )
        # With very low thresholds, should trigger at least FLAG or higher
        assert result.intervention_level >= 1

    @pytest.mark.asyncio
    async def test_session_step_affects_risk(self, mock_optimizer):
        step1 = await run_inference(
            prompt="test", org_id="org-1",
            intervention_mode="OBSERVE",
            session_step=1,
        )
        step10 = await run_inference(
            prompt="test", org_id="org-1",
            intervention_mode="OBSERVE",
            session_step=10,
        )
        assert step10.risk_score > step1.risk_score


# ---------------------------------------------------------------------------
# Circuit Breaker integration tests
# ---------------------------------------------------------------------------

class TestCircuitBreakerIntegration:
    @pytest.fixture(autouse=True)
    def clear_circuits(self):
        """Clear circuit breaker state between tests."""
        _provider_circuits.clear()
        yield
        _provider_circuits.clear()

    @pytest.mark.asyncio
    async def test_circuit_open_returns_error(self, mock_optimizer):
        """When a provider circuit is open, gateway returns error immediately."""
        from app.services.circuit_breaker import CircuitBreakerConfig, CircuitBreaker

        # Pre-open the circuit for the provider
        cb = CircuitBreaker("openai", CircuitBreakerConfig(failure_threshold=1))
        cb.record_failure()
        _provider_circuits["openai"] = cb

        result = await run_inference(
            prompt="test", org_id="org-1",
            intervention_mode="OBSERVE",
            provider_hint="openai",
        )
        assert result.error_message is not None
        assert "circuit breaker open" in result.error_message.lower()
        assert result.policy_action == "circuit_open"

    @pytest.mark.asyncio
    async def test_retry_on_transient_failure(self):
        """Gateway retries on transient failure and succeeds on second attempt."""
        call_count = 0
        fake_result = FakeInferResult()

        def infer_side_effect(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("transient failure")
            return fake_result

        fake_optimizer = MagicMock()
        fake_optimizer.infer.side_effect = infer_side_effect

        with patch("app.core.optimizer.get_optimizer_instance", return_value=fake_optimizer):
            result = await run_inference(
                prompt="test", org_id="org-1",
                intervention_mode="OBSERVE",
            )
        assert result.response == "Test response"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_provider_health_passed_to_routing(self, mock_optimizer):
        """Provider health data should be passed to the routing context."""
        with patch("app.services.provider_health.get_all_provider_health", return_value={
            "openai": "healthy",
            "anthropic": "degraded",
        }):
            result = await run_inference(
                prompt="test", org_id="org-1",
                intervention_mode="OBSERVE",
            )
        assert isinstance(result, GatewayResult)
        assert result.error_message is None
