from httpx import AsyncClient


def _auth_header(raw_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {raw_key}"}


async def test_chat_completions_success(
    client: AsyncClient,
    seed_org: dict[str, object],
) -> None:
    raw_key = seed_org["raw_key"]  # type: ignore[index]

    body = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": "Hello from test"}],
        "routing_mode": "AUTO",
        "quality_preference": "high",
        "latency_preference": "normal",
    }
    resp = await client.post(
        "/v1/chat/completions",
        json=body,
        headers=_auth_header(raw_key),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["object"] == "chat.completion"
    assert "choices" in data and data["choices"]
    assert "usage" in data
    assert "asahio" in data
    assert "asahi" in data
    meta = data["asahio"]
    assert "cache_hit" in meta
    assert "model_used" in meta
    assert meta["routing_mode"] == "AUTO"


async def test_chat_completions_supports_agent_session(
    client: AsyncClient,
    seed_org: dict[str, object],
) -> None:
    raw_key = seed_org["raw_key"]  # type: ignore[index]

    create_agent = await client.post(
        "/agents",
        json={"name": "Support Agent", "routing_mode": "AUTO", "intervention_mode": "OBSERVE"},
        headers=_auth_header(raw_key),
    )
    assert create_agent.status_code == 201
    agent = create_agent.json()

    resp = await client.post(
        "/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": "Route this through the agent"}],
            "routing_mode": "AUTO",
            "agent_id": agent["id"],
            "session_id": "session-1",
        },
        headers=_auth_header(raw_key),
    )
    assert resp.status_code == 200
    data = resp.json()
    meta = data["asahio"]
    assert meta["agent_id"] == agent["id"]
    assert meta["session_id"] == "session-1"


async def test_chat_completions_missing_user_message_400(
    client: AsyncClient,
    seed_org: dict[str, object],
) -> None:
    raw_key = seed_org["raw_key"]  # type: ignore[index]
    body = {
        "model": "gpt-4o",
        "messages": [{"role": "system", "content": "no user message"}],
    }
    resp = await client.post(
        "/v1/chat/completions",
        json=body,
        headers=_auth_header(raw_key),
    )
    assert resp.status_code == 400


async def test_chat_completions_requires_auth(client: AsyncClient) -> None:
    body = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": "No auth"}],
    }
    resp = await client.post("/v1/chat/completions", json=body)
    assert resp.status_code == 401
