"""Tests for request ID middleware."""

import pytest
from httpx import AsyncClient


class TestRequestID:
    @pytest.mark.asyncio
    async def test_generates_request_id_when_absent(self, client: AsyncClient) -> None:
        response = await client.get("/health/live")
        rid = response.headers.get("x-request-id")
        assert rid is not None
        assert len(rid) == 32  # uuid4().hex is 32 chars

    @pytest.mark.asyncio
    async def test_preserves_provided_request_id(self, client: AsyncClient) -> None:
        custom_id = "my-custom-request-id-12345"
        response = await client.get(
            "/health/live",
            headers={"X-Request-ID": custom_id},
        )
        assert response.headers.get("x-request-id") == custom_id

    @pytest.mark.asyncio
    async def test_present_in_response_header(self, client: AsyncClient) -> None:
        response = await client.get("/health/ready")
        assert "x-request-id" in response.headers

    @pytest.mark.asyncio
    async def test_different_requests_get_different_ids(self, client: AsyncClient) -> None:
        r1 = await client.get("/health/live")
        r2 = await client.get("/health/live")
        id1 = r1.headers.get("x-request-id")
        id2 = r2.headers.get("x-request-id")
        assert id1 != id2

    @pytest.mark.asyncio
    async def test_request_id_filter(self) -> None:
        """RequestIDFilter injects request_id into log records."""
        import logging
        from app.middleware.request_id import RequestIDFilter, request_id_var

        filt = RequestIDFilter()
        record = logging.LogRecord("test", logging.INFO, "", 0, "msg", (), None)

        request_id_var.set("test-correlation-id")
        filt.filter(record)
        assert record.request_id == "test-correlation-id"  # type: ignore[attr-defined]
