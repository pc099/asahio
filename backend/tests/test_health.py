"""Tests for health check endpoints."""

import pytest
from httpx import AsyncClient


class TestHealthLive:
    @pytest.mark.asyncio
    async def test_live_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_live_no_internal_config(self, client: AsyncClient) -> None:
        response = await client.get("/health/live")
        data = response.json()
        # Should only have "status", no config leak
        assert "cors_origins" not in data
        assert "debug" not in data
        assert "cors_env" not in data


class TestHealthReady:
    @pytest.mark.asyncio
    async def test_ready_returns_components(self, client: AsyncClient) -> None:
        response = await client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "components" in data
        assert "version" in data

    @pytest.mark.asyncio
    async def test_ready_no_internal_config(self, client: AsyncClient) -> None:
        response = await client.get("/health/ready")
        data = response.json()
        assert "cors_origins" not in data
        assert "debug" not in data
        assert "api_docs_enabled" not in data
        assert "cors_env" not in data
        assert "cors_origins_raw" not in data


class TestHealthProviders:
    @pytest.mark.asyncio
    async def test_providers_returns_list(self, client: AsyncClient) -> None:
        response = await client.get("/health/providers")
        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
        assert isinstance(data["providers"], list)


class TestHealthBackwardCompat:
    @pytest.mark.asyncio
    async def test_health_root_returns_readiness(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "components" in data
        # Should not expose internal config anymore
        assert "cors_origins" not in data
        assert "debug" not in data
