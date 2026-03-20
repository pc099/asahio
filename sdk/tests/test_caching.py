"""Tests for SDK cache metadata parsing on responses."""

import pytest

from asahio import Asahio, AsyncAsahio


class DummyResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def json(self) -> dict:
        return self._payload


def _cached_payload(cache_hit: bool = True, cache_tier: str = "exact") -> dict:
    return {
        "id": "chatcmpl_cache_test",
        "object": "chat.completion",
        "model": "gpt-4o-mini",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "cached response"},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
        },
        "asahio": {
            "cache_hit": cache_hit,
            "cache_tier": cache_tier if cache_hit else None,
            "model_requested": "gpt-4o",
            "model_used": "gpt-4o-mini",
            "cost_without_asahio": 0.03,
            "cost_with_asahio": 0.0 if cache_hit else 0.01,
            "savings_usd": 0.03 if cache_hit else 0.02,
            "savings_pct": 100.0 if cache_hit else 66.7,
            "routing_mode": "AUTO",
            "intervention_mode": "OBSERVE",
            "request_id": "req_cache_test",
        },
    }


def test_cache_hit_exact(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify SDK parses exact cache hit metadata correctly."""
    client = Asahio(api_key="asahio_live_test", base_url="https://example.com")
    monkeypatch.setattr(
        client._client, "post",
        lambda *args, **kwargs: DummyResponse(_cached_payload(True, "exact")),
    )

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": "hello"}],
    )

    assert response.asahio.cache_hit is True
    assert response.asahio.cache_tier == "exact"
    assert response.asahio.cost_with_asahio == 0.0
    assert response.asahio.savings_pct == 100.0
    client.close()


def test_cache_hit_semantic(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify SDK parses semantic cache hit metadata."""
    client = Asahio(api_key="asahio_live_test", base_url="https://example.com")
    monkeypatch.setattr(
        client._client, "post",
        lambda *args, **kwargs: DummyResponse(_cached_payload(True, "semantic")),
    )

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": "hello"}],
    )

    assert response.asahio.cache_hit is True
    assert response.asahio.cache_tier == "semantic"
    client.close()


def test_cache_miss(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify SDK parses cache miss metadata."""
    client = Asahio(api_key="asahio_live_test", base_url="https://example.com")
    monkeypatch.setattr(
        client._client, "post",
        lambda *args, **kwargs: DummyResponse(_cached_payload(False)),
    )

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": "hello"}],
    )

    assert response.asahio.cache_hit is False
    assert response.asahio.cache_tier is None
    assert response.asahio.cost_with_asahio == 0.01
    client.close()


def test_cache_metadata_on_async(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify async client also parses cache metadata."""
    client = Asahio(api_key="asahio_live_test", base_url="https://example.com")
    monkeypatch.setattr(
        client._client, "post",
        lambda *args, **kwargs: DummyResponse(_cached_payload(True, "exact")),
    )

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": "test"}],
    )

    assert response.asahio.cache_hit is True
    assert response.asahio.request_id == "req_cache_test"
    client.close()


def test_cache_savings_calculation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify 100% savings on cache hit."""
    client = Asahio(api_key="asahio_live_test", base_url="https://example.com")
    monkeypatch.setattr(
        client._client, "post",
        lambda *args, **kwargs: DummyResponse(_cached_payload(True, "exact")),
    )

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": "what is python"}],
    )

    assert response.asahio.savings_usd == 0.03
    assert response.asahio.savings_pct == 100.0
    client.close()
