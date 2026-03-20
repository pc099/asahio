"""Tests for the routing rule dry-run and weight override endpoints."""

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import ApiKey, KeyEnvironment, Member, MemberRole, Organisation, User


@pytest_asyncio.fixture
async def routing_org(session_factory: async_sessionmaker[AsyncSession]) -> dict:
    """Create an org with an API key for routing tests."""
    async with session_factory() as session:
        suffix = uuid.uuid4().hex[:8]
        user = User(email=f"routing-{suffix}@example.com", name="Routing User")
        session.add(user)
        await session.flush()

        org = Organisation(name="Routing Org", slug=f"routing-org-{suffix}")
        session.add(org)
        await session.flush()

        member = Member(
            organisation_id=org.id,
            user_id=user.id,
            role=MemberRole.OWNER,
        )
        session.add(member)

        raw_key, prefix, key_hash, last_four = ApiKey.generate(environment="live")
        api_key = ApiKey(
            organisation_id=org.id,
            created_by_user_id=user.id,
            name="Routing Test Key",
            environment=KeyEnvironment.LIVE,
            prefix=prefix,
            key_hash=key_hash,
            last_four=last_four,
            scopes=["*"],
            is_active=True,
        )
        session.add(api_key)
        await session.commit()

        return {"org": org, "user": user, "raw_key": raw_key}


def _auth(routing_org: dict) -> dict:
    return {"Authorization": f"Bearer {routing_org['raw_key']}"}


class TestDryRun:
    """Tests for POST /routing/rules/dry-run."""

    @pytest.mark.asyncio
    async def test_dry_run_step_based(self, client: AsyncClient, routing_org: dict) -> None:
        resp = await client.post("/routing/rules/dry-run", json={
            "rule_type": "step_based",
            "rule_config": {
                "rules": [
                    {"step": 1, "model": "gpt-4o-mini"},
                    {"step": 3, "model": "gpt-4o"},
                ]
            },
            "session_step": 1,
        }, headers=_auth(routing_org))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["selected_model"] == "gpt-4o-mini"

    @pytest.mark.asyncio
    async def test_dry_run_cost_ceiling(self, client: AsyncClient, routing_org: dict) -> None:
        resp = await client.post("/routing/rules/dry-run", json={
            "rule_type": "cost_ceiling_per_1k",
            "rule_config": {"value": 0.001},
        }, headers=_auth(routing_org))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["selected_model"] is not None
        assert data["selected_provider"] is not None

    @pytest.mark.asyncio
    async def test_dry_run_invalid_rule(self, client: AsyncClient, routing_org: dict) -> None:
        resp = await client.post("/routing/rules/dry-run", json={
            "rule_type": "step_based",
            "rule_config": {},
        }, headers=_auth(routing_org))
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_dry_run_fallback_chain(self, client: AsyncClient, routing_org: dict) -> None:
        resp = await client.post("/routing/rules/dry-run", json={
            "rule_type": "fallback_chain",
            "rule_config": {"chain": ["gpt-4o", "gpt-4o-mini"]},
        }, headers=_auth(routing_org))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["selected_model"] == "gpt-4o"

    @pytest.mark.asyncio
    async def test_dry_run_time_based(self, client: AsyncClient, routing_org: dict) -> None:
        resp = await client.post("/routing/rules/dry-run", json={
            "rule_type": "time_based",
            "rule_config": {
                "rules": [
                    {"hours": "0-11", "model": "gpt-4o-mini"},
                    {"hours": "12-23", "model": "gpt-4o"},
                ]
            },
            "utc_hour": 14,
        }, headers=_auth(routing_org))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["selected_model"] == "gpt-4o"


class TestRoutingWeights:
    """Tests for GET/PUT /routing/weights."""

    @pytest.mark.asyncio
    async def test_get_default_weights(self, client: AsyncClient, routing_org: dict) -> None:
        resp = await client.get("/routing/weights", headers=_auth(routing_org))
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_custom"] is False
        assert "quality" in data["data"]
        assert "cost" in data["data"]

    @pytest.mark.asyncio
    async def test_update_weights(self, client: AsyncClient, routing_org: dict) -> None:
        resp = await client.put("/routing/weights", json={
            "weights": {"quality": 0.6, "cost": 0.1}
        }, headers=_auth(routing_org))
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_custom"] is True
        assert data["data"]["quality"] == 0.6
        assert data["data"]["cost"] == 0.1

    @pytest.mark.asyncio
    async def test_update_weights_invalid_key(self, client: AsyncClient, routing_org: dict) -> None:
        resp = await client.put("/routing/weights", json={
            "weights": {"nonexistent": 0.5}
        }, headers=_auth(routing_org))
        assert resp.status_code == 422
