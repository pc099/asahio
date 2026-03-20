"""Tests for the cache warming endpoint."""

import pytest


def _auth(seed: dict) -> dict:
    return {"Authorization": f"Bearer {seed['raw_key']}", "X-Org-Slug": seed["org"].slug}


class TestCacheWarm:
    """Tests for POST /cache/warm and GET /cache/stats."""

    @pytest.mark.asyncio
    async def test_warm_returns_503_without_redis(self, client, seed_org) -> None:
        """Without Redis, cache warm returns 503."""
        resp = await client.post(
            "/cache/warm",
            json={
                "entries": [
                    {"query": "What is Python?", "response": "A programming language.", "model_used": "gpt-4o-mini"},
                ],
                "ttl": 3600,
            },
            headers=_auth(seed_org),
        )
        # Test env has no Redis → 503
        assert resp.status_code == 503

    @pytest.mark.asyncio
    async def test_warm_rejects_empty_entries(self, client, seed_org) -> None:
        """Empty entries list should return 422."""
        resp = await client.post(
            "/cache/warm",
            json={"entries": []},
            headers=_auth(seed_org),
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_warm_rejects_invalid_ttl(self, client, seed_org) -> None:
        """TTL below minimum should return 422."""
        resp = await client.post(
            "/cache/warm",
            json={
                "entries": [{"query": "q", "response": "r"}],
                "ttl": 5,
            },
            headers=_auth(seed_org),
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_cache_stats(self, client, seed_org) -> None:
        """GET /cache/stats should return metrics dict."""
        resp = await client.get(
            "/cache/stats",
            headers=_auth(seed_org),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "metrics" in data
        assert "hit_rate" in data["metrics"]
        assert data["metrics"]["exact_hits"] == 0
