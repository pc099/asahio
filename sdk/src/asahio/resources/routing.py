"""Routing resource for the ASAHIO Python SDK."""

from __future__ import annotations

from typing import Any, Optional

from asahio.resources import AsyncResource, SyncResource
from asahio.types.routing import DryRunResult, RoutingConstraint, RoutingDecision


class Routing(SyncResource):
    """Sync routing resource."""

    def dry_run(
        self,
        *,
        prompt: str,
        agent_id: Optional[str] = None,
        constraints: Optional[dict[str, Any]] = None,
    ) -> DryRunResult:
        """Dry run routing decision without executing."""
        body: dict[str, Any] = {"prompt": prompt}
        if agent_id is not None:
            body["agent_id"] = agent_id
        if constraints is not None:
            body["constraints"] = constraints

        response = self._client.post("/routing/dry-run", json=body)
        return DryRunResult.from_dict(response.json())

    def get_decision(self, call_id: str) -> RoutingDecision:
        """Get routing decision for a specific call."""
        response = self._client.get(f"/routing/decisions/{call_id}")
        return RoutingDecision.from_dict(response.json())

    def list_constraints(self, *, agent_id: Optional[str] = None) -> list[RoutingConstraint]:
        """List routing constraints."""
        params = {}
        if agent_id is not None:
            params["agent_id"] = agent_id

        response = self._client.get("/routing/constraints", params=params if params else None)
        data = response.json()
        return [RoutingConstraint.from_dict(c) for c in data.get("data", [])]

    def create_constraint(
        self,
        *,
        agent_id: str,
        constraint_type: str,
        value: Any,
        priority: int = 0,
    ) -> RoutingConstraint:
        """Create a new routing constraint."""
        body = {
            "agent_id": agent_id,
            "constraint_type": constraint_type,
            "value": value,
            "priority": priority,
        }
        response = self._client.post("/routing/constraints", json=body)
        return RoutingConstraint.from_dict(response.json())

    def delete_constraint(self, constraint_id: str) -> dict:
        """Delete a routing constraint."""
        response = self._client.delete(f"/routing/constraints/{constraint_id}")
        return response.json()


class AsyncRouting(AsyncResource):
    """Async routing resource."""

    async def dry_run(
        self,
        *,
        prompt: str,
        agent_id: Optional[str] = None,
        constraints: Optional[dict[str, Any]] = None,
    ) -> DryRunResult:
        """Dry run routing decision without executing."""
        body: dict[str, Any] = {"prompt": prompt}
        if agent_id is not None:
            body["agent_id"] = agent_id
        if constraints is not None:
            body["constraints"] = constraints

        response = await self._client.post("/routing/dry-run", json=body)
        return DryRunResult.from_dict(response.json())

    async def get_decision(self, call_id: str) -> RoutingDecision:
        """Get routing decision for a specific call."""
        response = await self._client.get(f"/routing/decisions/{call_id}")
        return RoutingDecision.from_dict(response.json())

    async def list_constraints(self, *, agent_id: Optional[str] = None) -> list[RoutingConstraint]:
        """List routing constraints."""
        params = {}
        if agent_id is not None:
            params["agent_id"] = agent_id

        response = await self._client.get("/routing/constraints", params=params if params else None)
        data = response.json()
        return [RoutingConstraint.from_dict(c) for c in data.get("data", [])]

    async def create_constraint(
        self,
        *,
        agent_id: str,
        constraint_type: str,
        value: Any,
        priority: int = 0,
    ) -> RoutingConstraint:
        """Create a new routing constraint."""
        body = {
            "agent_id": agent_id,
            "constraint_type": constraint_type,
            "value": value,
            "priority": priority,
        }
        response = await self._client.post("/routing/constraints", json=body)
        return RoutingConstraint.from_dict(response.json())

    async def delete_constraint(self, constraint_id: str) -> dict:
        """Delete a routing constraint."""
        response = await self._client.delete(f"/routing/constraints/{constraint_id}")
        return response.json()
