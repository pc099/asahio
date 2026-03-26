"""Trace and session resource for the ASAHIO Python SDK."""

from __future__ import annotations

from typing import Optional

from asahio.resources import AsyncResource, PaginatedList, SyncResource, _strip_none
from asahio.types.traces import Session, SessionGraph, SessionStep, Trace


class Traces(SyncResource):
    """Sync trace resource."""

    def get(self, trace_id: str) -> Trace:
        """Get a specific trace by ID."""
        response = self._client.get(f"/traces/{trace_id}")
        return Trace.from_dict(response.json())

    def list(
        self,
        *,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> PaginatedList[Trace]:
        """List traces."""
        params = _strip_none({
            "agent_id": agent_id,
            "session_id": session_id,
            "limit": limit,
            "offset": offset,
        })
        response = self._client.get("/traces", params=params)
        data = response.json()
        return PaginatedList(
            data=[Trace.from_dict(t) for t in data.get("data", [])],
            total=data.get("pagination", {}).get("total", 0),
            limit=limit,
            offset=offset,
        )

    def get_session(self, session_id: str) -> Session:
        """Get a specific session by ID."""
        response = self._client.get(f"/traces/sessions/{session_id}")
        return Session.from_dict(response.json())

    def list_sessions(
        self,
        *,
        agent_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> PaginatedList[Session]:
        """List sessions."""
        params = _strip_none({
            "agent_id": agent_id,
            "limit": limit,
            "offset": offset,
        })
        response = self._client.get("/traces/sessions", params=params)
        data = response.json()
        return PaginatedList(
            data=[Session.from_dict(s) for s in data.get("data", [])],
            total=data.get("pagination", {}).get("total", 0),
            limit=limit,
            offset=offset,
        )

    def get_session_graph(self, session_id: str) -> SessionGraph:
        """Get session graph visualization data."""
        response = self._client.get(f"/traces/sessions/{session_id}/graph")
        return SessionGraph.from_dict(response.json())

    def list_session_steps(self, session_id: str) -> list[SessionStep]:
        """List all steps in a session."""
        response = self._client.get(f"/traces/sessions/{session_id}/steps")
        data = response.json()
        return [SessionStep.from_dict(s) for s in data.get("data", [])]


class AsyncTraces(AsyncResource):
    """Async trace resource."""

    async def get(self, trace_id: str) -> Trace:
        """Get a specific trace by ID."""
        response = await self._client.get(f"/traces/{trace_id}")
        return Trace.from_dict(response.json())

    async def list(
        self,
        *,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> PaginatedList[Trace]:
        """List traces."""
        params = _strip_none({
            "agent_id": agent_id,
            "session_id": session_id,
            "limit": limit,
            "offset": offset,
        })
        response = await self._client.get("/traces", params=params)
        data = response.json()
        return PaginatedList(
            data=[Trace.from_dict(t) for t in data.get("data", [])],
            total=data.get("pagination", {}).get("total", 0),
            limit=limit,
            offset=offset,
        )

    async def get_session(self, session_id: str) -> Session:
        """Get a specific session by ID."""
        response = await self._client.get(f"/traces/sessions/{session_id}")
        return Session.from_dict(response.json())

    async def list_sessions(
        self,
        *,
        agent_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> PaginatedList[Session]:
        """List sessions."""
        params = _strip_none({
            "agent_id": agent_id,
            "limit": limit,
            "offset": offset,
        })
        response = await self._client.get("/traces/sessions", params=params)
        data = response.json()
        return PaginatedList(
            data=[Session.from_dict(s) for s in data.get("data", [])],
            total=data.get("pagination", {}).get("total", 0),
            limit=limit,
            offset=offset,
        )

    async def get_session_graph(self, session_id: str) -> SessionGraph:
        """Get session graph visualization data."""
        response = await self._client.get(f"/traces/sessions/{session_id}/graph")
        return SessionGraph.from_dict(response.json())

    async def list_session_steps(self, session_id: str) -> list[SessionStep]:
        """List all steps in a session."""
        response = await self._client.get(f"/traces/sessions/{session_id}/steps")
        data = response.json()
        return [SessionStep.from_dict(s) for s in data.get("data", [])]
