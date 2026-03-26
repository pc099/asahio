"""Health check resource for the ASAHIO Python SDK."""

from __future__ import annotations

from asahio.resources import AsyncResource, SyncResource
from asahio.types.health import HealthStatus, ProviderHealth


class Health(SyncResource):
    """Sync health resource."""

    def check(self) -> HealthStatus:
        """Get overall health status."""
        response = self._client.get("/health")
        return HealthStatus.from_dict(response.json())

    def list_providers(self) -> list[ProviderHealth]:
        """Get health status of all providers."""
        response = self._client.get("/health/providers")
        data = response.json()
        return [ProviderHealth.from_dict(p) for p in data.get("data", [])]

    def get_provider(self, provider: str) -> ProviderHealth:
        """Get health status of a specific provider."""
        response = self._client.get(f"/health/providers/{provider}")
        return ProviderHealth.from_dict(response.json())


class AsyncHealth(AsyncResource):
    """Async health resource."""

    async def check(self) -> HealthStatus:
        """Get overall health status."""
        response = await self._client.get("/health")
        return HealthStatus.from_dict(response.json())

    async def list_providers(self) -> list[ProviderHealth]:
        """Get health status of all providers."""
        response = await self._client.get("/health/providers")
        data = response.json()
        return [ProviderHealth.from_dict(p) for p in data.get("data", [])]

    async def get_provider(self, provider: str) -> ProviderHealth:
        """Get health status of a specific provider."""
        response = await self._client.get(f"/health/providers/{provider}")
        return ProviderHealth.from_dict(response.json())
