import pytest

from asahio import AsyncAsahio, Asahio


class DummyResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def json(self) -> dict:
        return self._payload


def _completion_payload(metadata_key: str = "asahio") -> dict:
    return {
        "id": "chatcmpl_test",
        "object": "chat.completion",
        "model": "gpt-4o-mini",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "ok"},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
        },
        metadata_key: {
            "cache_hit": False,
            "cache_tier": None,
            "model_requested": "gpt-4o",
            "model_used": "gpt-4o-mini",
            "cost_without_asahio": 0.03,
            "cost_with_asahio": 0.01,
            "savings_usd": 0.02,
            "savings_pct": 66.7,
            "routing_mode": "AUTO",
            "intervention_mode": "OBSERVE",
            "request_id": "req_123",
        },
    }


def test_sync_client_parses_canonical_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    client = Asahio(api_key="asahio_live_test", base_url="https://example.com")
    monkeypatch.setattr(client._client, "post", lambda *args, **kwargs: DummyResponse(_completion_payload()))

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": "hello"}],
        routing_mode="AUTO",
        intervention_mode="OBSERVE",
    )

    assert response.asahio.model_used == "gpt-4o-mini"
    assert response.asahio.cost_with_asahio == 0.01
    assert response.asahi is response.asahio
    assert response.asahio.request_id == "req_123"
    client.close()


@pytest.mark.asyncio
async def test_async_client_accepts_legacy_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    client = AsyncAsahio(api_key="asahio_live_test", base_url="https://example.com")

    async def fake_post(*args, **kwargs):
        return DummyResponse(_completion_payload("asahi"))

    monkeypatch.setattr(client._client, "post", fake_post)

    response = await client.chat.completions.create(
        messages=[{"role": "user", "content": "hello"}],
        routing_mode="AUTO",
    )

    assert response.asahio.model_used == "gpt-4o-mini"
    assert response.asahio.cost_without_asahi == 0.03
    await client.close()
