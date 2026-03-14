"""Tests for the Model C global pool service."""

import pytest

from app.services.model_c_pool import (
    COLD_START_THRESHOLD,
    PRIVACY_THRESHOLD,
    ModelCPool,
    PoolRecord,
    RiskPrior,
)


@pytest.fixture
def pool() -> ModelCPool:
    return ModelCPool()


def _make_record(**overrides) -> PoolRecord:
    defaults = {
        "agent_type": "CHATBOT",
        "complexity_bucket": 0.5,
        "output_type": "CONVERSATIONAL",
        "model_used": "gpt-4o",
        "hallucination_detected": False,
        "cache_hit": False,
        "latency_ms": 100,
    }
    defaults.update(overrides)
    return PoolRecord(**defaults)


# ── Conditional Add ─────────────────────────────────────────────────────


class TestConditionalAdd:
    @pytest.mark.asyncio
    async def test_below_threshold_rejected(self, pool: ModelCPool) -> None:
        record = _make_record()
        result = await pool.conditional_add("org-1", 10, record)
        assert result is False
        # Pool should be empty
        prior = await pool.query_risk_prior("CHATBOT", 0.5)
        assert prior.observation_count == 0

    @pytest.mark.asyncio
    async def test_above_threshold_accepted(self, pool: ModelCPool) -> None:
        record = _make_record()
        result = await pool.conditional_add("org-1", 100, record)
        assert result is True
        prior = await pool.query_risk_prior("CHATBOT", 0.5)
        assert prior.observation_count == 1

    @pytest.mark.asyncio
    async def test_no_org_id_stored(self, pool: ModelCPool) -> None:
        """Records in the pool must not contain org_id or agent_id."""
        record = _make_record()
        await pool.conditional_add("org-secret", 100, record)
        # Check the stored record
        key = ("CHATBOT", 0.5)
        stored = pool._memory_pool[key]
        assert len(stored) == 1
        # PoolRecord has no org_id or agent_id fields
        assert not hasattr(stored[0], "org_id")
        assert not hasattr(stored[0], "agent_id")


# ── Query Risk Prior ────────────────────────────────────────────────────


class TestQueryRiskPrior:
    @pytest.mark.asyncio
    async def test_empty_pool_returns_neutral(self, pool: ModelCPool) -> None:
        prior = await pool.query_risk_prior("CHATBOT", 0.5)
        assert prior.risk_score == 0.5
        assert prior.observation_count == 0
        assert prior.confidence == 0.0

    @pytest.mark.asyncio
    async def test_populated_pool_returns_aggregated(self, pool: ModelCPool) -> None:
        # Add 10 records: 2 with hallucination
        for i in range(10):
            record = _make_record(hallucination_detected=(i < 2))
            await pool.conditional_add("org-1", 100, record)

        prior = await pool.query_risk_prior("CHATBOT", 0.5)
        assert prior.observation_count == 10
        assert prior.risk_score == pytest.approx(0.2, abs=0.01)  # 2/10
        assert prior.confidence > 0

    @pytest.mark.asyncio
    async def test_different_buckets_different_priors(self, pool: ModelCPool) -> None:
        # Low complexity: no hallucinations
        for _ in range(5):
            await pool.conditional_add("org-1", 100, _make_record(complexity_bucket=0.1))
        # High complexity: all hallucinations
        for _ in range(5):
            await pool.conditional_add(
                "org-1", 100,
                _make_record(complexity_bucket=0.9, hallucination_detected=True),
            )

        low = await pool.query_risk_prior("CHATBOT", 0.1)
        high = await pool.query_risk_prior("CHATBOT", 0.9)
        assert low.risk_score < high.risk_score

    @pytest.mark.asyncio
    async def test_recommended_model(self, pool: ModelCPool) -> None:
        # gpt-4o: 5 clean
        for _ in range(5):
            await pool.conditional_add("org-1", 100, _make_record(model_used="gpt-4o"))
        # claude: 5 with 3 hallucinations
        for i in range(5):
            await pool.conditional_add(
                "org-1", 100,
                _make_record(model_used="claude-3-5-sonnet", hallucination_detected=(i < 3)),
            )

        prior = await pool.query_risk_prior("CHATBOT", 0.5)
        assert prior.recommended_model == "gpt-4o"


# ── Cold Start Initializer ──────────────────────────────────────────────


class TestColdStartInitializer:
    @pytest.mark.asyncio
    async def test_empty_pool_returns_defaults(self, pool: ModelCPool) -> None:
        defaults = await pool.cold_start_initializer("agent-new")
        assert defaults["avg_complexity"] == 0.5
        assert defaults["bootstrap_source"] is None

    @pytest.mark.asyncio
    async def test_populated_pool_bootstraps(self, pool: ModelCPool) -> None:
        # Seed pool with known data
        for _ in range(20):
            await pool.conditional_add(
                "org-1", 100,
                _make_record(complexity_bucket=0.3, cache_hit=True),
            )

        defaults = await pool.cold_start_initializer("agent-new", agent_type="CHATBOT")
        assert defaults["bootstrap_source"] == "model_c"
        assert defaults["avg_complexity"] == pytest.approx(0.3, abs=0.01)
        assert defaults["cache_hit_rate"] == pytest.approx(1.0, abs=0.01)

    @pytest.mark.asyncio
    async def test_uses_agent_type_filter(self, pool: ModelCPool) -> None:
        # Add CHATBOT records
        for _ in range(10):
            await pool.conditional_add("org-1", 100, _make_record(agent_type="CHATBOT"))
        # Add CODING records with different characteristics
        for _ in range(10):
            await pool.conditional_add(
                "org-1", 100,
                _make_record(agent_type="CODING", complexity_bucket=0.8, hallucination_detected=True),
            )

        chatbot = await pool.cold_start_initializer("agent-1", agent_type="CHATBOT")
        coding = await pool.cold_start_initializer("agent-2", agent_type="CODING")
        assert chatbot["avg_complexity"] != coding["avg_complexity"]


# ── Complexity Bucketing ────────────────────────────────────────────────


class TestComplexityBucketing:
    def test_bucketing_rounds_correctly(self) -> None:
        assert ModelCPool._bucket_complexity(0.0) == 0.0
        assert ModelCPool._bucket_complexity(0.15) == 0.2
        assert ModelCPool._bucket_complexity(0.34) == 0.3
        assert ModelCPool._bucket_complexity(0.99) == 1.0
        assert ModelCPool._bucket_complexity(1.5) == 1.0  # clamped
        assert ModelCPool._bucket_complexity(-0.1) == 0.0  # clamped
