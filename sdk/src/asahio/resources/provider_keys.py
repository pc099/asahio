"""Provider key resource for the ASAHIO Python SDK."""

from __future__ import annotations

from typing import Any, Optional

from asahio.resources import AsyncResource, SyncResource
from asahio.types.providers import ProviderKey


class ProviderKeys(SyncResource):
    """Sync provider key resource."""

    def list(self) -> list[ProviderKey]:
        """List all provider keys for the organization."""
        response = self._client.get("/providers/keys")
        data = response.json()
        return [ProviderKey.from_dict(k) for k in data.get("data", [])]

    def create(
        self,
        *,
        provider: str,
        api_key: str,
        name: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> ProviderKey:
        """Create a new provider key (BYOM)."""
        body: dict[str, Any] = {
            "provider": provider,
            "api_key": api_key,
        }
        if name is not None:
            body["name"] = name
        if metadata is not None:
            body["metadata"] = metadata

        response = self._client.post("/providers/keys", json=body)
        return ProviderKey.from_dict(response.json())

    def get(self, key_id: str) -> ProviderKey:
        """Get a specific provider key by ID."""
        response = self._client.get(f"/providers/keys/{key_id}")
        return ProviderKey.from_dict(response.json())

    def delete(self, key_id: str) -> dict:
        """Delete a provider key."""
        response = self._client.delete(f"/providers/keys/{key_id}")
        return response.json()

    def rotate(self, key_id: str, *, new_api_key: str) -> ProviderKey:
        """Rotate a provider key."""
        body = {"new_api_key": new_api_key}
        response = self._client.post(f"/providers/keys/{key_id}/rotate", json=body)
        return ProviderKey.from_dict(response.json())


class AsyncProviderKeys(AsyncResource):
    """Async provider key resource."""

    async def list(self) -> list[ProviderKey]:
        """List all provider keys for the organization."""
        response = await self._client.get("/providers/keys")
        data = response.json()
        return [ProviderKey.from_dict(k) for k in data.get("data", [])]

    async def create(
        self,
        *,
        provider: str,
        api_key: str,
        name: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> ProviderKey:
        """Create a new provider key (BYOM)."""
        body: dict[str, Any] = {
            "provider": provider,
            "api_key": api_key,
        }
        if name is not None:
            body["name"] = name
        if metadata is not None:
            body["metadata"] = metadata

        response = await self._client.post("/providers/keys", json=body)
        return ProviderKey.from_dict(response.json())

    async def get(self, key_id: str) -> ProviderKey:
        """Get a specific provider key by ID."""
        response = await self._client.get(f"/providers/keys/{key_id}")
        return ProviderKey.from_dict(response.json())

    async def delete(self, key_id: str) -> dict:
        """Delete a provider key."""
        response = await self._client.delete(f"/providers/keys/{key_id}")
        return response.json()

    async def rotate(self, key_id: str, *, new_api_key: str) -> ProviderKey:
        """Rotate a provider key."""
        body = {"new_api_key": new_api_key}
        response = await self._client.post(f"/providers/keys/{key_id}/rotate", json=body)
        return ProviderKey.from_dict(response.json())
