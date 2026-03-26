"""Agent resource for the ASAHIO Python SDK."""

from __future__ import annotations

from typing import Any, Optional

from asahio.resources import AsyncResource, SyncResource, _strip_none
from asahio.types.agents import (
    Agent,
    AgentSession,
    AgentStats,
    ModeEligibility,
    ModeHistoryEntry,
    ModeTransition,
)


class Agents(SyncResource):
    """Sync agent resource."""

    def list(self) -> list[Agent]:
        """List all agents for the organization."""
        response = self._client.get("/agents")
        data = response.json()
        return [Agent.from_dict(a) for a in data.get("data", [])]

    def create(
        self,
        *,
        name: str,
        slug: Optional[str] = None,
        description: Optional[str] = None,
        routing_mode: str = "AUTO",
        intervention_mode: str = "OBSERVE",
        model_endpoint_id: Optional[str] = None,
        metadata: Optional[dict] = None,
        blueprint_id: Optional[str] = None,
    ) -> Agent:
        """Create a new agent."""
        body: dict[str, Any] = {
            "name": name,
            "routing_mode": routing_mode,
            "intervention_mode": intervention_mode,
        }
        if slug is not None:
            body["slug"] = slug
        if description is not None:
            body["description"] = description
        if model_endpoint_id is not None:
            body["model_endpoint_id"] = model_endpoint_id
        if metadata is not None:
            body["metadata"] = metadata
        if blueprint_id is not None:
            body["blueprint_id"] = blueprint_id

        response = self._client.post("/agents", json=body)
        return Agent.from_dict(response.json())

    def get(self, agent_id: str) -> Agent:
        """Get a specific agent by ID."""
        response = self._client.get(f"/agents/{agent_id}")
        return Agent.from_dict(response.json())

    def update(self, agent_id: str, **kwargs: Any) -> Agent:
        """Update an agent."""
        response = self._client.patch(f"/agents/{agent_id}", json=kwargs)
        return Agent.from_dict(response.json())

    def archive(self, agent_id: str) -> Agent:
        """Archive an agent (soft delete)."""
        response = self._client.post(f"/agents/{agent_id}/archive", json={})
        return Agent.from_dict(response.json())

    def stats(self, agent_id: str) -> AgentStats:
        """Get agent statistics."""
        response = self._client.get(f"/agents/{agent_id}/stats")
        return AgentStats.from_dict(response.json())

    def mode_eligibility(self, agent_id: str) -> ModeEligibility:
        """Check if agent is eligible for mode transition."""
        response = self._client.get(f"/agents/{agent_id}/mode-eligibility")
        return ModeEligibility.from_dict(response.json())

    def transition_mode(
        self,
        agent_id: str,
        *,
        target_mode: str,
        operator_authorized: bool = False,
    ) -> ModeTransition:
        """Transition agent to a new mode."""
        body = {
            "target_mode": target_mode,
            "operator_authorized": operator_authorized,
        }
        response = self._client.post(f"/agents/{agent_id}/mode-transition", json=body)
        return ModeTransition.from_dict(response.json())

    def mode_history(self, agent_id: str, *, limit: int = 50) -> list[ModeHistoryEntry]:
        """Get agent mode transition history."""
        params = _strip_none({"limit": limit})
        response = self._client.get(f"/agents/{agent_id}/mode-history", params=params)
        data = response.json()
        return [ModeHistoryEntry.from_dict(e) for e in data.get("data", [])]

    def create_session(self, agent_id: str, *, external_session_id: str) -> AgentSession:
        """Create a new session for an agent."""
        body = {"external_session_id": external_session_id}
        response = self._client.post(f"/agents/{agent_id}/sessions", json=body)
        return AgentSession.from_dict(response.json())


class AsyncAgents(AsyncResource):
    """Async agent resource."""

    async def list(self) -> list[Agent]:
        """List all agents for the organization."""
        response = await self._client.get("/agents")
        data = response.json()
        return [Agent.from_dict(a) for a in data.get("data", [])]

    async def create(
        self,
        *,
        name: str,
        slug: Optional[str] = None,
        description: Optional[str] = None,
        routing_mode: str = "AUTO",
        intervention_mode: str = "OBSERVE",
        model_endpoint_id: Optional[str] = None,
        metadata: Optional[dict] = None,
        blueprint_id: Optional[str] = None,
    ) -> Agent:
        """Create a new agent."""
        body: dict[str, Any] = {
            "name": name,
            "routing_mode": routing_mode,
            "intervention_mode": intervention_mode,
        }
        if slug is not None:
            body["slug"] = slug
        if description is not None:
            body["description"] = description
        if model_endpoint_id is not None:
            body["model_endpoint_id"] = model_endpoint_id
        if metadata is not None:
            body["metadata"] = metadata
        if blueprint_id is not None:
            body["blueprint_id"] = blueprint_id

        response = await self._client.post("/agents", json=body)
        return Agent.from_dict(response.json())

    async def get(self, agent_id: str) -> Agent:
        """Get a specific agent by ID."""
        response = await self._client.get(f"/agents/{agent_id}")
        return Agent.from_dict(response.json())

    async def update(self, agent_id: str, **kwargs: Any) -> Agent:
        """Update an agent."""
        response = await self._client.patch(f"/agents/{agent_id}", json=kwargs)
        return Agent.from_dict(response.json())

    async def archive(self, agent_id: str) -> Agent:
        """Archive an agent (soft delete)."""
        response = await self._client.post(f"/agents/{agent_id}/archive", json={})
        return Agent.from_dict(response.json())

    async def stats(self, agent_id: str) -> AgentStats:
        """Get agent statistics."""
        response = await self._client.get(f"/agents/{agent_id}/stats")
        return AgentStats.from_dict(response.json())

    async def mode_eligibility(self, agent_id: str) -> ModeEligibility:
        """Check if agent is eligible for mode transition."""
        response = await self._client.get(f"/agents/{agent_id}/mode-eligibility")
        return ModeEligibility.from_dict(response.json())

    async def transition_mode(
        self,
        agent_id: str,
        *,
        target_mode: str,
        operator_authorized: bool = False,
    ) -> ModeTransition:
        """Transition agent to a new mode."""
        body = {
            "target_mode": target_mode,
            "operator_authorized": operator_authorized,
        }
        response = await self._client.post(f"/agents/{agent_id}/mode-transition", json=body)
        return ModeTransition.from_dict(response.json())

    async def mode_history(self, agent_id: str, *, limit: int = 50) -> list[ModeHistoryEntry]:
        """Get agent mode transition history."""
        params = _strip_none({"limit": limit})
        response = await self._client.get(f"/agents/{agent_id}/mode-history", params=params)
        data = response.json()
        return [ModeHistoryEntry.from_dict(e) for e in data.get("data", [])]

    async def create_session(self, agent_id: str, *, external_session_id: str) -> AgentSession:
        """Create a new session for an agent."""
        body = {"external_session_id": external_session_id}
        response = await self._client.post(f"/agents/{agent_id}/sessions", json=body)
        return AgentSession.from_dict(response.json())
