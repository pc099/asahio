"""Ollama configuration resource for the ASAHIO Python SDK."""

from __future__ import annotations

from typing import Optional

from asahio.resources import AsyncResource, SyncResource
from asahio.types.providers import OllamaConfig


class Ollama(SyncResource):
    """Sync Ollama resource."""

    def get_config(self) -> OllamaConfig:
        """Get current Ollama configuration."""
        response = self._client.get("/providers/ollama/config")
        return OllamaConfig.from_dict(response.json())

    def update_config(
        self,
        *,
        base_url: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> OllamaConfig:
        """Update Ollama configuration."""
        body = {}
        if base_url is not None:
            body["base_url"] = base_url
        if enabled is not None:
            body["enabled"] = enabled

        response = self._client.patch("/providers/ollama/config", json=body)
        return OllamaConfig.from_dict(response.json())

    def test_connection(self) -> dict:
        """Test Ollama connection."""
        response = self._client.post("/providers/ollama/test", json={})
        return response.json()


class AsyncOllama(AsyncResource):
    """Async Ollama resource."""

    async def get_config(self) -> OllamaConfig:
        """Get current Ollama configuration."""
        response = await self._client.get("/providers/ollama/config")
        return OllamaConfig.from_dict(response.json())

    async def update_config(
        self,
        *,
        base_url: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> OllamaConfig:
        """Update Ollama configuration."""
        body = {}
        if base_url is not None:
            body["base_url"] = base_url
        if enabled is not None:
            body["enabled"] = enabled

        response = await self._client.patch("/providers/ollama/config", json=body)
        return OllamaConfig.from_dict(response.json())

    async def test_connection(self) -> dict:
        """Test Ollama connection."""
        response = await self._client.post("/providers/ollama/test", json={})
        return response.json()
