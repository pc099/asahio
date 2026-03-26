"""Model registry resource for the ASAHIO Python SDK."""

from __future__ import annotations

from typing import Any, Optional

from asahio.resources import AsyncResource, SyncResource


class Models(SyncResource):
    """Sync model registry resource."""

    def list(self) -> list[dict]:
        """List all available models from the registry."""
        response = self._client.get("/models")
        data = response.json()
        return data.get("data", [])

    def get(self, model_id: str) -> dict:
        """Get a specific model by ID."""
        response = self._client.get(f"/models/{model_id}")
        return response.json()

    def create_endpoint(
        self,
        *,
        name: str,
        base_model: str,
        endpoint_url: str,
        api_key: Optional[str] = None,
        headers: Optional[dict] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Create a custom model endpoint (fine-tuned or custom)."""
        body: dict[str, Any] = {
            "name": name,
            "base_model": base_model,
            "endpoint_url": endpoint_url,
        }
        if api_key is not None:
            body["api_key"] = api_key
        if headers is not None:
            body["headers"] = headers
        if metadata is not None:
            body["metadata"] = metadata

        response = self._client.post("/models/endpoints", json=body)
        return response.json()

    def list_endpoints(self) -> list[dict]:
        """List all custom model endpoints."""
        response = self._client.get("/models/endpoints")
        data = response.json()
        return data.get("data", [])

    def get_endpoint(self, endpoint_id: str) -> dict:
        """Get a specific model endpoint by ID."""
        response = self._client.get(f"/models/endpoints/{endpoint_id}")
        return response.json()

    def update_endpoint(self, endpoint_id: str, **kwargs: Any) -> dict:
        """Update a model endpoint."""
        response = self._client.patch(f"/models/endpoints/{endpoint_id}", json=kwargs)
        return response.json()

    def delete_endpoint(self, endpoint_id: str) -> dict:
        """Delete a model endpoint."""
        response = self._client.delete(f"/models/endpoints/{endpoint_id}")
        return response.json()


class AsyncModels(AsyncResource):
    """Async model registry resource."""

    async def list(self) -> list[dict]:
        """List all available models from the registry."""
        response = await self._client.get("/models")
        data = response.json()
        return data.get("data", [])

    async def get(self, model_id: str) -> dict:
        """Get a specific model by ID."""
        response = await self._client.get(f"/models/{model_id}")
        return response.json()

    async def create_endpoint(
        self,
        *,
        name: str,
        base_model: str,
        endpoint_url: str,
        api_key: Optional[str] = None,
        headers: Optional[dict] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Create a custom model endpoint (fine-tuned or custom)."""
        body: dict[str, Any] = {
            "name": name,
            "base_model": base_model,
            "endpoint_url": endpoint_url,
        }
        if api_key is not None:
            body["api_key"] = api_key
        if headers is not None:
            body["headers"] = headers
        if metadata is not None:
            body["metadata"] = metadata

        response = await self._client.post("/models/endpoints", json=body)
        return response.json()

    async def list_endpoints(self) -> list[dict]:
        """List all custom model endpoints."""
        response = await self._client.get("/models/endpoints")
        data = response.json()
        return data.get("data", [])

    async def get_endpoint(self, endpoint_id: str) -> dict:
        """Get a specific model endpoint by ID."""
        response = await self._client.get(f"/models/endpoints/{endpoint_id}")
        return response.json()

    async def update_endpoint(self, endpoint_id: str, **kwargs: Any) -> dict:
        """Update a model endpoint."""
        response = await self._client.patch(f"/models/endpoints/{endpoint_id}", json=kwargs)
        return response.json()

    async def delete_endpoint(self, endpoint_id: str) -> dict:
        """Delete a model endpoint."""
        response = await self._client.delete(f"/models/endpoints/{endpoint_id}")
        return response.json()
