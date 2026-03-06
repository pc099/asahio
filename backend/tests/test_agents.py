from httpx import AsyncClient


def _auth_header(raw_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {raw_key}"}


async def test_agents_crud_and_session(
    client: AsyncClient,
    seed_org: dict[str, object],
) -> None:
    raw_key = seed_org["raw_key"]  # type: ignore[index]

    create_resp = await client.post(
        "/agents",
        json={
            "name": "Ops Agent",
            "description": "Handles support operations",
            "routing_mode": "AUTO",
            "intervention_mode": "OBSERVE",
        },
        headers=_auth_header(raw_key),
    )
    assert create_resp.status_code == 201
    agent = create_resp.json()
    assert agent["slug"] == "ops-agent"

    list_resp = await client.get("/agents", headers=_auth_header(raw_key))
    assert list_resp.status_code == 200
    rows = list_resp.json()["data"]
    assert any(row["id"] == agent["id"] for row in rows)

    session_resp = await client.post(
        f"/agents/{agent['id']}/sessions",
        json={"external_session_id": "session-123"},
        headers=_auth_header(raw_key),
    )
    assert session_resp.status_code == 201
    session = session_resp.json()
    assert session["external_session_id"] == "session-123"
