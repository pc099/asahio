"""Tests for the agents resource."""

import pytest

from asahio import AsyncAsahio, Asahio
from asahio.types.agents import (
    Agent,
    AgentSession,
    AgentStats,
    ModeEligibility,
    ModeHistoryEntry,
    ModeTransition,
)


class DummyResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def json(self) -> dict:
        return self._payload


def _agent_payload() -> dict:
    return {
        "id": "agt_123",
        "organisation_id": "org_123",
        "name": "Test Agent",
        "slug": "test-agent",
        "description": "A test agent",
        "routing_mode": "AUTO",
        "intervention_mode": "OBSERVE",
        "is_active": True,
        "created_at": "2026-03-26T00:00:00Z",
        "updated_at": "2026-03-26T00:00:00Z",
    }


def _agent_stats_payload() -> dict:
    return {
        "agent_id": "agt_123",
        "total_calls": 100,
        "cache_hits": 45,
        "cache_hit_rate": 0.45,
        "avg_latency_ms": 250.5,
        "total_input_tokens": 10000,
        "total_output_tokens": 5000,
        "total_sessions": 20,
    }


def _mode_eligibility_payload() -> dict:
    return {
        "agent_id": "agt_123",
        "current_mode": "AUTO",
        "eligible": True,
        "suggested_mode": "GUIDED",
        "reason": "Agent has sufficient observations",
        "evidence": {},
    }


def _mode_transition_payload() -> dict:
    return {
        "agent_id": "agt_123",
        "previous_mode": "AUTO",
        "new_mode": "GUIDED",
        "transition_reason": "Manual transition requested",
    }


def _mode_history_payload() -> dict:
    return {
        "id": "hist_123",
        "agent_id": "agt_123",
        "previous_mode": "AUTO",
        "new_mode": "GUIDED",
        "trigger": "manual",
        "created_at": "2026-03-26T00:00:00Z",
    }


def _agent_session_payload() -> dict:
    return {
        "id": "sess_123",
        "agent_id": "agt_123",
        "external_session_id": "ext_sess_123",
        "started_at": "2026-03-26T00:00:00Z",
        "last_seen_at": "2026-03-26T00:00:00Z",
    }


def test_sync_list_agents(monkeypatch: pytest.MonkeyPatch) -> None:
    client = Asahio(api_key="test", base_url="https://example.com")
    monkeypatch.setattr(
        client._client,
        "get",
        lambda *args, **kwargs: DummyResponse({"data": [_agent_payload()]}),
    )

    agents = client.agents.list()
    assert len(agents) == 1
    assert isinstance(agents[0], Agent)
    assert agents[0].name == "Test Agent"


def test_sync_create_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    client = Asahio(api_key="test", base_url="https://example.com")
    monkeypatch.setattr(
        client._client,
        "post",
        lambda *args, **kwargs: DummyResponse(_agent_payload()),
    )

    agent = client.agents.create(name="Test Agent", slug="test-agent")
    assert isinstance(agent, Agent)
    assert agent.name == "Test Agent"
    assert agent.slug == "test-agent"


def test_sync_get_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    client = Asahio(api_key="test", base_url="https://example.com")
    monkeypatch.setattr(
        client._client,
        "get",
        lambda *args, **kwargs: DummyResponse(_agent_payload()),
    )

    agent = client.agents.get("agt_123")
    assert isinstance(agent, Agent)
    assert agent.id == "agt_123"


def test_sync_update_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    client = Asahio(api_key="test", base_url="https://example.com")
    payload = _agent_payload()
    payload["name"] = "Updated Agent"
    monkeypatch.setattr(
        client._client,
        "patch",
        lambda *args, **kwargs: DummyResponse(payload),
    )

    agent = client.agents.update("agt_123", name="Updated Agent")
    assert isinstance(agent, Agent)
    assert agent.name == "Updated Agent"


def test_sync_archive_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    client = Asahio(api_key="test", base_url="https://example.com")
    payload = _agent_payload()
    payload["is_active"] = False
    monkeypatch.setattr(
        client._client,
        "post",
        lambda *args, **kwargs: DummyResponse(payload),
    )

    agent = client.agents.archive("agt_123")
    assert isinstance(agent, Agent)
    assert agent.is_active is False


def test_sync_agent_stats(monkeypatch: pytest.MonkeyPatch) -> None:
    client = Asahio(api_key="test", base_url="https://example.com")
    monkeypatch.setattr(
        client._client,
        "get",
        lambda *args, **kwargs: DummyResponse(_agent_stats_payload()),
    )

    stats = client.agents.stats("agt_123")
    assert isinstance(stats, AgentStats)
    assert stats.total_calls == 100
    assert stats.cache_hit_rate == 0.45


def test_sync_mode_eligibility(monkeypatch: pytest.MonkeyPatch) -> None:
    client = Asahio(api_key="test", base_url="https://example.com")
    monkeypatch.setattr(
        client._client,
        "get",
        lambda *args, **kwargs: DummyResponse(_mode_eligibility_payload()),
    )

    eligibility = client.agents.mode_eligibility("agt_123")
    assert isinstance(eligibility, ModeEligibility)
    assert eligibility.eligible is True


def test_sync_transition_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    client = Asahio(api_key="test", base_url="https://example.com")
    monkeypatch.setattr(
        client._client,
        "post",
        lambda *args, **kwargs: DummyResponse(_mode_transition_payload()),
    )

    transition = client.agents.transition_mode("agt_123", target_mode="GUIDED")
    assert isinstance(transition, ModeTransition)
    assert transition.new_mode == "GUIDED"
    assert transition.previous_mode == "AUTO"


def test_sync_mode_history(monkeypatch: pytest.MonkeyPatch) -> None:
    client = Asahio(api_key="test", base_url="https://example.com")
    monkeypatch.setattr(
        client._client,
        "get",
        lambda *args, **kwargs: DummyResponse({"data": [_mode_history_payload()]}),
    )

    history = client.agents.mode_history("agt_123")
    assert len(history) == 1
    assert isinstance(history[0], ModeHistoryEntry)
    assert history[0].previous_mode == "AUTO"


def test_sync_create_session(monkeypatch: pytest.MonkeyPatch) -> None:
    client = Asahio(api_key="test", base_url="https://example.com")
    monkeypatch.setattr(
        client._client,
        "post",
        lambda *args, **kwargs: DummyResponse(_agent_session_payload()),
    )

    session = client.agents.create_session("agt_123", external_session_id="ext_sess_123")
    assert isinstance(session, AgentSession)
    assert session.agent_id == "agt_123"


@pytest.mark.asyncio
async def test_async_list_agents(monkeypatch: pytest.MonkeyPatch) -> None:
    client = AsyncAsahio(api_key="test", base_url="https://example.com")

    async def mock_get(*args, **kwargs):
        return DummyResponse({"data": [_agent_payload()]})

    monkeypatch.setattr(client._client, "get", mock_get)

    agents = await client.agents.list()
    assert len(agents) == 1
    assert isinstance(agents[0], Agent)


@pytest.mark.asyncio
async def test_async_create_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    client = AsyncAsahio(api_key="test", base_url="https://example.com")

    async def mock_post(*args, **kwargs):
        return DummyResponse(_agent_payload())

    monkeypatch.setattr(client._client, "post", mock_post)

    agent = await client.agents.create(name="Test Agent")
    assert isinstance(agent, Agent)
    assert agent.name == "Test Agent"
