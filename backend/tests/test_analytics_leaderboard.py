"""Tests for the /analytics/leaderboard endpoint."""

import uuid as _uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import (
    ApiKey,
    CallTrace,
    KeyEnvironment,
    Member,
    MemberRole,
    Organisation,
    RequestLog,
    User,
)


def _auth_header(raw_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {raw_key}"}


@pytest_asyncio.fixture
async def leaderboard_org(
    session_factory: async_sessionmaker[AsyncSession],
) -> dict[str, Any]:
    """Create org with seeded RequestLog and CallTrace data for leaderboard tests."""
    async with session_factory() as session:
        suffix = _uuid.uuid4().hex[:8]

        user = User(email=f"lb-{suffix}@example.com", name="LB User")
        session.add(user)
        await session.flush()

        org = Organisation(name="Leaderboard Org", slug=f"lb-org-{suffix}")
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
            name="LB Key",
            environment=KeyEnvironment.LIVE,
            prefix=prefix,
            key_hash=key_hash,
            last_four=last_four,
            scopes=["*"],
            is_active=True,
        )
        session.add(api_key)
        await session.flush()

        now = datetime.now(timezone.utc)

        # Seed RequestLog entries — 3 models
        for i in range(10):
            session.add(
                RequestLog(
                    organisation_id=org.id,
                    api_key_id=api_key.id,
                    model_used="gpt-4o",
                    provider="openai",
                    input_tokens=100 + i * 10,
                    output_tokens=50 + i * 5,
                    cost_without_asahi=0.01 * (i + 1),
                    cost_with_asahi=0.005 * (i + 1),
                    savings_usd=0.005 * (i + 1),
                    savings_pct=50.0,
                    cache_hit=(i % 3 == 0),  # 4 out of 10 are cache hits
                    latency_ms=100 + i * 20,
                    status_code=200,
                    created_at=now - timedelta(hours=i),
                )
            )

        for i in range(5):
            session.add(
                RequestLog(
                    organisation_id=org.id,
                    api_key_id=api_key.id,
                    model_used="claude-sonnet-4-6",
                    provider="anthropic",
                    input_tokens=200 + i * 20,
                    output_tokens=100 + i * 10,
                    cost_without_asahi=0.02 * (i + 1),
                    cost_with_asahi=0.01 * (i + 1),
                    savings_usd=0.01 * (i + 1),
                    savings_pct=50.0,
                    cache_hit=(i % 2 == 0),  # 3 out of 5
                    latency_ms=200 + i * 30,
                    status_code=200,
                    created_at=now - timedelta(hours=i),
                )
            )

        for i in range(3):
            session.add(
                RequestLog(
                    organisation_id=org.id,
                    api_key_id=api_key.id,
                    model_used="gemini-pro",
                    provider="google",
                    input_tokens=150 + i * 15,
                    output_tokens=75 + i * 8,
                    cost_without_asahi=0.005 * (i + 1),
                    cost_with_asahi=0.003 * (i + 1),
                    savings_usd=0.002 * (i + 1),
                    savings_pct=40.0,
                    cache_hit=False,
                    latency_ms=50 + i * 10,
                    status_code=200,
                    created_at=now - timedelta(hours=i),
                )
            )

        # Seed CallTrace entries with hallucination tags
        for i in range(10):
            session.add(
                CallTrace(
                    organisation_id=org.id,
                    model_used="gpt-4o",
                    provider="openai",
                    input_tokens=100,
                    output_tokens=50,
                    hallucination_tag="confirmed" if i < 2 else None,  # 2/10 = 20%
                    created_at=now - timedelta(hours=i),
                )
            )

        for i in range(5):
            session.add(
                CallTrace(
                    organisation_id=org.id,
                    model_used="claude-sonnet-4-6",
                    provider="anthropic",
                    input_tokens=200,
                    output_tokens=100,
                    hallucination_tag=None,  # 0% hallucination
                    created_at=now - timedelta(hours=i),
                )
            )

        await session.commit()

        return {
            "org": org,
            "user": user,
            "raw_key": raw_key,
            "org_id": str(org.id),
        }


@pytest_asyncio.fixture
async def other_org(
    session_factory: async_sessionmaker[AsyncSession],
) -> dict[str, Any]:
    """Create a second org to verify cross-org isolation."""
    async with session_factory() as session:
        suffix = _uuid.uuid4().hex[:8]

        user = User(email=f"other-{suffix}@example.com", name="Other User")
        session.add(user)
        await session.flush()

        org = Organisation(name="Other Org", slug=f"other-org-{suffix}")
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
            name="Other Key",
            environment=KeyEnvironment.LIVE,
            prefix=prefix,
            key_hash=key_hash,
            last_four=last_four,
            scopes=["*"],
            is_active=True,
        )
        session.add(api_key)
        await session.flush()

        now = datetime.now(timezone.utc)

        # Seed data for other org — different models
        for i in range(7):
            session.add(
                RequestLog(
                    organisation_id=org.id,
                    api_key_id=api_key.id,
                    model_used="deepseek-chat",
                    provider="deepseek",
                    input_tokens=300,
                    output_tokens=150,
                    cost_without_asahi=0.001 * (i + 1),
                    cost_with_asahi=0.0005 * (i + 1),
                    savings_usd=0.0005 * (i + 1),
                    savings_pct=50.0,
                    cache_hit=False,
                    latency_ms=80,
                    status_code=200,
                    created_at=now - timedelta(hours=i),
                )
            )

        await session.commit()

        return {
            "org": org,
            "user": user,
            "raw_key": raw_key,
            "org_id": str(org.id),
        }


# ── Tests ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_leaderboard_aggregation(
    client: AsyncClient,
    leaderboard_org: dict[str, Any],
) -> None:
    """Verify correct counts and averages in the leaderboard response."""
    resp = await client.get(
        "/analytics/leaderboard",
        params={"period": "30d", "sort_by": "request_count"},
        headers=_auth_header(leaderboard_org["raw_key"]),
    )
    assert resp.status_code == 200

    data = resp.json()
    assert data["period"] == "30d"
    assert data["sort_by"] == "request_count"
    assert len(data["entries"]) == 3

    # Default sort is request_count descending — gpt-4o has 10 requests
    first = data["entries"][0]
    assert first["model"] == "gpt-4o"
    assert first["provider"] == "openai"
    assert first["request_count"] == 10
    assert first["rank"] == 1

    second = data["entries"][1]
    assert second["model"] == "claude-sonnet-4-6"
    assert second["provider"] == "anthropic"
    assert second["request_count"] == 5
    assert second["rank"] == 2

    third = data["entries"][2]
    assert third["model"] == "gemini-pro"
    assert third["provider"] == "google"
    assert third["request_count"] == 3
    assert third["rank"] == 3


@pytest.mark.asyncio
async def test_leaderboard_cache_hit_rate(
    client: AsyncClient,
    leaderboard_org: dict[str, Any],
) -> None:
    """Verify cache hit rate calculation."""
    resp = await client.get(
        "/analytics/leaderboard",
        params={"period": "30d", "sort_by": "request_count"},
        headers=_auth_header(leaderboard_org["raw_key"]),
    )
    assert resp.status_code == 200
    entries = {e["model"]: e for e in resp.json()["entries"]}

    # gpt-4o: 4/10 cache hits (i % 3 == 0 for i in 0..9 → 0,3,6,9)
    assert entries["gpt-4o"]["cache_hit_rate"] == pytest.approx(0.4, abs=0.01)

    # claude-sonnet-4-6: 3/5 cache hits (i % 2 == 0 for i in 0..4 → 0,2,4)
    assert entries["claude-sonnet-4-6"]["cache_hit_rate"] == pytest.approx(0.6, abs=0.01)

    # gemini-pro: 0/3 cache hits
    assert entries["gemini-pro"]["cache_hit_rate"] == pytest.approx(0.0, abs=0.01)


@pytest.mark.asyncio
async def test_leaderboard_hallucination_rate(
    client: AsyncClient,
    leaderboard_org: dict[str, Any],
) -> None:
    """Verify hallucination rate from CallTrace data."""
    resp = await client.get(
        "/analytics/leaderboard",
        params={"period": "30d", "sort_by": "request_count"},
        headers=_auth_header(leaderboard_org["raw_key"]),
    )
    assert resp.status_code == 200
    entries = {e["model"]: e for e in resp.json()["entries"]}

    # gpt-4o: 2/10 hallucinations = 0.2
    assert entries["gpt-4o"]["hallucination_rate"] == pytest.approx(0.2, abs=0.01)

    # claude-sonnet-4-6: 0/5 hallucinations = 0.0
    assert entries["claude-sonnet-4-6"]["hallucination_rate"] == pytest.approx(0.0, abs=0.01)

    # gemini-pro: no CallTrace data = 0.0
    assert entries["gemini-pro"]["hallucination_rate"] == pytest.approx(0.0, abs=0.01)


@pytest.mark.asyncio
async def test_leaderboard_sort_by_latency(
    client: AsyncClient,
    leaderboard_org: dict[str, Any],
) -> None:
    """Verify sort_by=avg_latency_ms sorts ascending (lower is better)."""
    resp = await client.get(
        "/analytics/leaderboard",
        params={"period": "30d", "sort_by": "avg_latency_ms"},
        headers=_auth_header(leaderboard_org["raw_key"]),
    )
    assert resp.status_code == 200

    entries = resp.json()["entries"]
    latencies = [e["avg_latency_ms"] for e in entries]
    assert latencies == sorted(latencies), "Latency should be sorted ascending"

    # gemini-pro has lowest latency (50-70ms range)
    assert entries[0]["model"] == "gemini-pro"
    assert entries[0]["rank"] == 1


@pytest.mark.asyncio
async def test_leaderboard_sort_by_hallucination(
    client: AsyncClient,
    leaderboard_org: dict[str, Any],
) -> None:
    """Verify sort_by=hallucination_rate sorts ascending (lower is better)."""
    resp = await client.get(
        "/analytics/leaderboard",
        params={"period": "30d", "sort_by": "hallucination_rate"},
        headers=_auth_header(leaderboard_org["raw_key"]),
    )
    assert resp.status_code == 200

    entries = resp.json()["entries"]
    rates = [e["hallucination_rate"] for e in entries]
    assert rates == sorted(rates), "Hallucination rate should be sorted ascending"


@pytest.mark.asyncio
async def test_leaderboard_sort_by_cost_descending(
    client: AsyncClient,
    leaderboard_org: dict[str, Any],
) -> None:
    """Verify sort_by=total_cost_usd sorts descending (higher first)."""
    resp = await client.get(
        "/analytics/leaderboard",
        params={"period": "30d", "sort_by": "total_cost_usd"},
        headers=_auth_header(leaderboard_org["raw_key"]),
    )
    assert resp.status_code == 200

    entries = resp.json()["entries"]
    costs = [e["total_cost_usd"] for e in entries]
    assert costs == sorted(costs, reverse=True), "Cost should be sorted descending"


@pytest.mark.asyncio
async def test_leaderboard_org_scoped(
    client: AsyncClient,
    leaderboard_org: dict[str, Any],
    other_org: dict[str, Any],
) -> None:
    """Verify cross-org isolation — each org sees only its own data."""
    # Leaderboard org should see gpt-4o, claude-sonnet-4-6, gemini-pro
    resp1 = await client.get(
        "/analytics/leaderboard",
        params={"period": "30d"},
        headers=_auth_header(leaderboard_org["raw_key"]),
    )
    assert resp1.status_code == 200
    models1 = {e["model"] for e in resp1.json()["entries"]}
    assert "gpt-4o" in models1
    assert "claude-sonnet-4-6" in models1
    assert "deepseek-chat" not in models1

    # Other org should see deepseek-chat only
    resp2 = await client.get(
        "/analytics/leaderboard",
        params={"period": "30d"},
        headers=_auth_header(other_org["raw_key"]),
    )
    assert resp2.status_code == 200
    models2 = {e["model"] for e in resp2.json()["entries"]}
    assert "deepseek-chat" in models2
    assert "gpt-4o" not in models2


@pytest.mark.asyncio
async def test_leaderboard_empty(
    client: AsyncClient,
    seed_org: dict[str, Any],
) -> None:
    """An org with no RequestLog data should return an empty leaderboard."""
    resp = await client.get(
        "/analytics/leaderboard",
        params={"period": "7d"},
        headers=_auth_header(seed_org["raw_key"]),
    )
    assert resp.status_code == 200

    data = resp.json()
    assert data["entries"] == []
    assert data["period"] == "7d"


@pytest.mark.asyncio
async def test_leaderboard_invalid_period(
    client: AsyncClient,
    seed_org: dict[str, Any],
) -> None:
    """Invalid period should return 422 validation error."""
    resp = await client.get(
        "/analytics/leaderboard",
        params={"period": "999d"},
        headers=_auth_header(seed_org["raw_key"]),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_leaderboard_invalid_sort_by(
    client: AsyncClient,
    seed_org: dict[str, Any],
) -> None:
    """Invalid sort_by should return 422 validation error."""
    resp = await client.get(
        "/analytics/leaderboard",
        params={"sort_by": "invalid_field"},
        headers=_auth_header(seed_org["raw_key"]),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_leaderboard_token_fields(
    client: AsyncClient,
    leaderboard_org: dict[str, Any],
) -> None:
    """Verify total_input_tokens and total_output_tokens are populated."""
    resp = await client.get(
        "/analytics/leaderboard",
        params={"period": "30d", "sort_by": "request_count"},
        headers=_auth_header(leaderboard_org["raw_key"]),
    )
    assert resp.status_code == 200
    entries = {e["model"]: e for e in resp.json()["entries"]}

    # gpt-4o: sum of input_tokens = 100+110+120+...+190 = sum(100+i*10 for i in 0..9) = 1450
    assert entries["gpt-4o"]["total_input_tokens"] == 1450
    # gpt-4o: sum of output_tokens = 50+55+60+...+95 = sum(50+i*5 for i in 0..9) = 725
    assert entries["gpt-4o"]["total_output_tokens"] == 725


@pytest.mark.asyncio
async def test_leaderboard_requires_auth(
    client: AsyncClient,
) -> None:
    """Leaderboard should require authentication."""
    resp = await client.get("/analytics/leaderboard")
    assert resp.status_code in (401, 403)
