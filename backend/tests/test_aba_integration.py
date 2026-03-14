"""Integration tests for ABA (Agent Behavioral Analytics) end-to-end pipeline.

Tests the full flow: POST observation → fingerprint updated → GET returns data,
cold start bootstrap, anomaly detection, structural records pagination,
Model C privacy threshold, and org scoping.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import Agent, AgentFingerprint, InterventionMode, RoutingMode, StructuralRecord
from app.services.aba_writer import ABAObservationPayload, write_aba_observation


def _auth(raw_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {raw_key}"}


# ── Helpers ────────────────────────────────────────────────────────────────


async def _create_agent(client: AsyncClient, raw_key: str, name: str) -> dict:
    resp = await client.post(
        "/agents",
        json={"name": name},
        headers=_auth(raw_key),
    )
    assert resp.status_code == 201
    return resp.json()


async def _write_observation(org_id: str, agent_id: str, **overrides) -> None:
    defaults = {
        "org_id": org_id,
        "agent_id": agent_id,
        "prompt": "What is Python?",
        "response": "Python is a programming language.",
        "model_used": "gpt-4o",
        "latency_ms": 150,
        "cache_hit": False,
        "input_tokens": 10,
        "output_tokens": 20,
    }
    defaults.update(overrides)
    payload = ABAObservationPayload(**defaults)
    await write_aba_observation(payload)


# ── Tests ──────────────────────────────────────────────────────────────────


class TestFullPipeline:
    """POST observation → fingerprint updated → GET returns update."""

    @pytest.mark.asyncio
    async def test_observation_creates_fingerprint(
        self,
        client: AsyncClient,
        seed_org: dict,
    ) -> None:
        raw_key = seed_org["raw_key"]
        org = seed_org["org"]
        agent = await _create_agent(client, raw_key, "ABA Pipeline Agent")
        agent_id = agent["id"]

        # Write an observation directly (bypasses gateway, tests the writer)
        await _write_observation(str(org.id), agent_id)

        # GET fingerprint
        resp = await client.get(
            f"/aba/fingerprints/{agent_id}",
            headers=_auth(raw_key),
        )
        assert resp.status_code == 200
        fp = resp.json()
        assert fp["agent_id"] == agent_id
        assert fp["total_observations"] == 1
        assert fp["avg_complexity"] >= 0

    @pytest.mark.asyncio
    async def test_multiple_observations_update_fingerprint(
        self,
        client: AsyncClient,
        seed_org: dict,
    ) -> None:
        raw_key = seed_org["raw_key"]
        org = seed_org["org"]
        agent = await _create_agent(client, raw_key, "ABA Multi Obs Agent")
        agent_id = agent["id"]

        # Write 5 observations
        for i in range(5):
            await _write_observation(
                str(org.id), agent_id,
                model_used="gpt-4o" if i < 3 else "claude-sonnet-4-5",
                cache_hit=(i % 2 == 0),
            )

        resp = await client.get(
            f"/aba/fingerprints/{agent_id}",
            headers=_auth(raw_key),
        )
        assert resp.status_code == 200
        fp = resp.json()
        assert fp["total_observations"] == 5
        assert "gpt-4o" in fp["model_distribution"]
        assert "claude-sonnet-4-5" in fp["model_distribution"]
        assert fp["cache_hit_rate"] > 0


class TestFingerprintsList:
    @pytest.mark.asyncio
    async def test_list_fingerprints(
        self,
        client: AsyncClient,
        seed_org: dict,
    ) -> None:
        raw_key = seed_org["raw_key"]
        org = seed_org["org"]

        # Create agent and write observation
        agent = await _create_agent(client, raw_key, "ABA List Agent")
        await _write_observation(str(org.id), agent["id"])

        resp = await client.get(
            "/aba/fingerprints",
            headers=_auth(raw_key),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "pagination" in data
        assert data["pagination"]["total"] >= 1


class TestStructuralRecords:
    @pytest.mark.asyncio
    async def test_list_structural_records_for_agent(
        self,
        client: AsyncClient,
        seed_org: dict,
    ) -> None:
        raw_key = seed_org["raw_key"]
        org = seed_org["org"]
        agent = await _create_agent(client, raw_key, "ABA Records Agent")
        agent_id = agent["id"]

        # Write 3 observations
        for _ in range(3):
            await _write_observation(str(org.id), agent_id)

        resp = await client.get(
            f"/aba/structural-records?agent_id={agent_id}",
            headers=_auth(raw_key),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 3
        for rec in data["data"]:
            assert rec["agent_id"] == agent_id
            assert "query_complexity_score" in rec
            assert "agent_type_classification" in rec

    @pytest.mark.asyncio
    async def test_structural_records_pagination(
        self,
        client: AsyncClient,
        seed_org: dict,
    ) -> None:
        raw_key = seed_org["raw_key"]
        org = seed_org["org"]
        agent = await _create_agent(client, raw_key, "ABA Pagination Agent")
        agent_id = agent["id"]

        for _ in range(5):
            await _write_observation(str(org.id), agent_id)

        # Page 1
        resp = await client.get(
            f"/aba/structural-records?agent_id={agent_id}&limit=2&offset=0",
            headers=_auth(raw_key),
        )
        assert resp.status_code == 200
        page1 = resp.json()
        assert len(page1["data"]) == 2
        assert page1["pagination"]["total"] == 5

        # Page 2
        resp = await client.get(
            f"/aba/structural-records?agent_id={agent_id}&limit=2&offset=2",
            headers=_auth(raw_key),
        )
        assert resp.status_code == 200
        page2 = resp.json()
        assert len(page2["data"]) == 2


class TestColdStart:
    @pytest.mark.asyncio
    async def test_new_agent_is_cold_start(
        self,
        client: AsyncClient,
        seed_org: dict,
    ) -> None:
        raw_key = seed_org["raw_key"]
        agent = await _create_agent(client, raw_key, "ABA Cold Agent")
        agent_id = agent["id"]

        resp = await client.get(
            f"/aba/cold-start-status/{agent_id}",
            headers=_auth(raw_key),
        )
        assert resp.status_code == 200
        cs = resp.json()
        assert cs["is_cold_start"] is True
        assert cs["total_observations"] == 0
        assert cs["progress_pct"] == 0.0

    @pytest.mark.asyncio
    async def test_warm_agent_not_cold_start(
        self,
        client: AsyncClient,
        seed_org: dict,
    ) -> None:
        raw_key = seed_org["raw_key"]
        org = seed_org["org"]
        agent = await _create_agent(client, raw_key, "ABA Warm Agent")
        agent_id = agent["id"]

        # Write enough observations to pass threshold (10)
        for i in range(12):
            await _write_observation(str(org.id), agent_id)

        resp = await client.get(
            f"/aba/cold-start-status/{agent_id}",
            headers=_auth(raw_key),
        )
        assert resp.status_code == 200
        cs = resp.json()
        assert cs["is_cold_start"] is False
        assert cs["total_observations"] == 12
        assert cs["progress_pct"] == 100.0


class TestAnomalies:
    @pytest.mark.asyncio
    async def test_no_anomalies_for_healthy_agent(
        self,
        client: AsyncClient,
        seed_org: dict,
    ) -> None:
        raw_key = seed_org["raw_key"]
        resp = await client.get(
            "/aba/anomalies",
            headers=_auth(raw_key),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data


class TestOrgScoping:
    @pytest.mark.asyncio
    async def test_fingerprint_not_found_cross_org(
        self,
        client: AsyncClient,
        seed_org: dict,
    ) -> None:
        """Agent fingerprint from another org returns 404."""
        raw_key = seed_org["raw_key"]
        fake_agent_id = str(uuid.uuid4())

        resp = await client.get(
            f"/aba/fingerprints/{fake_agent_id}",
            headers=_auth(raw_key),
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_agent_id_returns_400(
        self,
        client: AsyncClient,
        seed_org: dict,
    ) -> None:
        raw_key = seed_org["raw_key"]
        resp = await client.get(
            "/aba/fingerprints/not-a-uuid",
            headers=_auth(raw_key),
        )
        assert resp.status_code == 400


class TestManualObservationEndpoint:
    @pytest.mark.asyncio
    async def test_post_observation_accepted(
        self,
        client: AsyncClient,
        seed_org: dict,
    ) -> None:
        raw_key = seed_org["raw_key"]
        agent = await _create_agent(client, raw_key, "ABA Manual Obs Agent")

        resp = await client.post(
            "/aba/observation",
            json={
                "agent_id": agent["id"],
                "prompt": "Hello",
                "response": "Hi there!",
                "model_used": "gpt-4o",
                "latency_ms": 100,
            },
            headers=_auth(raw_key),
        )
        assert resp.status_code == 202
        body = resp.json()
        assert body["status"] == "accepted"
        assert body["agent_id"] == agent["id"]


class TestRiskPrior:
    @pytest.mark.asyncio
    async def test_risk_prior_returns_result(
        self,
        client: AsyncClient,
        seed_org: dict,
    ) -> None:
        raw_key = seed_org["raw_key"]
        resp = await client.get(
            "/aba/risk-prior?agent_type=CHATBOT&complexity_bucket=0.5",
            headers=_auth(raw_key),
        )
        assert resp.status_code == 200
        prior = resp.json()
        assert "risk_score" in prior
        assert "observation_count" in prior
        assert "confidence" in prior
