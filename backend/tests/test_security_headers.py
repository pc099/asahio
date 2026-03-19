"""Tests for security headers middleware."""

import pytest
from httpx import AsyncClient


class TestSecurityHeaders:
    @pytest.mark.asyncio
    async def test_hsts_header_present(self, client: AsyncClient) -> None:
        response = await client.get("/health/live")
        assert response.headers.get("strict-transport-security") == "max-age=31536000; includeSubDomains"

    @pytest.mark.asyncio
    async def test_content_type_options(self, client: AsyncClient) -> None:
        response = await client.get("/health/live")
        assert response.headers.get("x-content-type-options") == "nosniff"

    @pytest.mark.asyncio
    async def test_frame_options(self, client: AsyncClient) -> None:
        response = await client.get("/health/live")
        assert response.headers.get("x-frame-options") == "DENY"

    @pytest.mark.asyncio
    async def test_xss_protection(self, client: AsyncClient) -> None:
        response = await client.get("/health/live")
        assert response.headers.get("x-xss-protection") == "1; mode=block"

    @pytest.mark.asyncio
    async def test_referrer_policy(self, client: AsyncClient) -> None:
        response = await client.get("/health/live")
        assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"

    @pytest.mark.asyncio
    async def test_permissions_policy(self, client: AsyncClient) -> None:
        response = await client.get("/health/live")
        assert response.headers.get("permissions-policy") == "camera=(), microphone=(), geolocation=()"

    @pytest.mark.asyncio
    async def test_headers_on_api_endpoint(self, client: AsyncClient) -> None:
        """Security headers should be present on all endpoints, not just health."""
        response = await client.get("/health/ready")
        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("x-frame-options") == "DENY"
