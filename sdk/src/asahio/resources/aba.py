"""ABA (Agent Behavioral Analytics) resource for the ASAHIO Python SDK."""

from __future__ import annotations

from typing import Any, Optional

from asahio.resources import AsyncResource, PaginatedList, SyncResource, _strip_none
from asahio.types.aba import (
    AnomalyItem,
    ColdStartStatus,
    Fingerprint,
    OrgOverview,
    RiskPrior,
    StructuralRecord,
)


class ABA(SyncResource):
    """Sync ABA resource."""

    def get_fingerprint(self, agent_id: str) -> Fingerprint:
        """Get behavioral fingerprint for an agent."""
        response = self._client.get(f"/aba/fingerprints/{agent_id}")
        return Fingerprint.from_dict(response.json())

    def list_fingerprints(
        self,
        *,
        min_observations: int = 0,
        limit: int = 50,
        offset: int = 0,
    ) -> PaginatedList[Fingerprint]:
        """List all fingerprints."""
        params = _strip_none({
            "min_observations": min_observations,
            "limit": limit,
            "offset": offset,
        })
        response = self._client.get("/aba/fingerprints", params=params)
        data = response.json()
        return PaginatedList(
            data=[Fingerprint.from_dict(f) for f in data.get("data", [])],
            total=data.get("pagination", {}).get("total", 0),
            limit=limit,
            offset=offset,
        )

    def org_overview(self) -> OrgOverview:
        """Get organization-wide ABA overview."""
        response = self._client.get("/aba/org/overview")
        return OrgOverview.from_dict(response.json())

    def list_structural_records(
        self,
        *,
        agent_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> PaginatedList[StructuralRecord]:
        """List structural records."""
        params = _strip_none({
            "agent_id": agent_id,
            "limit": limit,
            "offset": offset,
        })
        response = self._client.get("/aba/structural-records", params=params)
        data = response.json()
        return PaginatedList(
            data=[StructuralRecord.from_dict(r) for r in data.get("data", [])],
            total=data.get("pagination", {}).get("total", 0),
            limit=limit,
            offset=offset,
        )

    def get_risk_prior(self, *, agent_type: str, complexity_bucket: float) -> RiskPrior:
        """Get risk prior from Model C global pool."""
        params = {
            "agent_type": agent_type,
            "complexity_bucket": complexity_bucket,
        }
        response = self._client.get("/aba/risk-prior", params=params)
        return RiskPrior.from_dict(response.json())

    def list_anomalies(
        self,
        *,
        agent_id: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> list[AnomalyItem]:
        """List anomalies."""
        params = _strip_none({
            "agent_id": agent_id,
            "severity": severity,
        })
        response = self._client.get("/aba/anomalies", params=params)
        data = response.json()
        return [AnomalyItem.from_dict(a) for a in data.get("data", [])]

    def cold_start_status(self, agent_id: str) -> ColdStartStatus:
        """Get cold start status for an agent."""
        response = self._client.get(f"/aba/cold-start-status/{agent_id}")
        return ColdStartStatus.from_dict(response.json())

    def create_observation(
        self,
        *,
        agent_id: str,
        prompt: str = "",
        response: str = "",
        model_used: str = "",
        **kwargs: Any,
    ) -> dict:
        """Create a manual ABA observation."""
        body = {
            "agent_id": agent_id,
            "prompt": prompt,
            "response": response,
            "model_used": model_used,
            **kwargs,
        }
        resp = self._client.post("/aba/observation", json=body)
        return resp.json()

    def tag_hallucination(
        self,
        call_id: str,
        *,
        hallucination_detected: bool = True,
        notes: str = "",
    ) -> dict:
        """Tag a call as hallucination."""
        body = {
            "hallucination_detected": hallucination_detected,
            "notes": notes,
        }
        resp = self._client.post(f"/aba/calls/{call_id}/tag", json=body)
        return resp.json()


class AsyncABA(AsyncResource):
    """Async ABA resource."""

    async def get_fingerprint(self, agent_id: str) -> Fingerprint:
        """Get behavioral fingerprint for an agent."""
        response = await self._client.get(f"/aba/fingerprints/{agent_id}")
        return Fingerprint.from_dict(response.json())

    async def list_fingerprints(
        self,
        *,
        min_observations: int = 0,
        limit: int = 50,
        offset: int = 0,
    ) -> PaginatedList[Fingerprint]:
        """List all fingerprints."""
        params = _strip_none({
            "min_observations": min_observations,
            "limit": limit,
            "offset": offset,
        })
        response = await self._client.get("/aba/fingerprints", params=params)
        data = response.json()
        return PaginatedList(
            data=[Fingerprint.from_dict(f) for f in data.get("data", [])],
            total=data.get("pagination", {}).get("total", 0),
            limit=limit,
            offset=offset,
        )

    async def org_overview(self) -> OrgOverview:
        """Get organization-wide ABA overview."""
        response = await self._client.get("/aba/org/overview")
        return OrgOverview.from_dict(response.json())

    async def list_structural_records(
        self,
        *,
        agent_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> PaginatedList[StructuralRecord]:
        """List structural records."""
        params = _strip_none({
            "agent_id": agent_id,
            "limit": limit,
            "offset": offset,
        })
        response = await self._client.get("/aba/structural-records", params=params)
        data = response.json()
        return PaginatedList(
            data=[StructuralRecord.from_dict(r) for r in data.get("data", [])],
            total=data.get("pagination", {}).get("total", 0),
            limit=limit,
            offset=offset,
        )

    async def get_risk_prior(self, *, agent_type: str, complexity_bucket: float) -> RiskPrior:
        """Get risk prior from Model C global pool."""
        params = {
            "agent_type": agent_type,
            "complexity_bucket": complexity_bucket,
        }
        response = await self._client.get("/aba/risk-prior", params=params)
        return RiskPrior.from_dict(response.json())

    async def list_anomalies(
        self,
        *,
        agent_id: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> list[AnomalyItem]:
        """List anomalies."""
        params = _strip_none({
            "agent_id": agent_id,
            "severity": severity,
        })
        response = await self._client.get("/aba/anomalies", params=params)
        data = response.json()
        return [AnomalyItem.from_dict(a) for a in data.get("data", [])]

    async def cold_start_status(self, agent_id: str) -> ColdStartStatus:
        """Get cold start status for an agent."""
        response = await self._client.get(f"/aba/cold-start-status/{agent_id}")
        return ColdStartStatus.from_dict(response.json())

    async def create_observation(
        self,
        *,
        agent_id: str,
        prompt: str = "",
        response: str = "",
        model_used: str = "",
        **kwargs: Any,
    ) -> dict:
        """Create a manual ABA observation."""
        body = {
            "agent_id": agent_id,
            "prompt": prompt,
            "response": response,
            "model_used": model_used,
            **kwargs,
        }
        resp = await self._client.post("/aba/observation", json=body)
        return resp.json()

    async def tag_hallucination(
        self,
        call_id: str,
        *,
        hallucination_detected: bool = True,
        notes: str = "",
    ) -> dict:
        """Tag a call as hallucination."""
        body = {
            "hallucination_detected": hallucination_detected,
            "notes": notes,
        }
        resp = await self._client.post(f"/aba/calls/{call_id}/tag", json=body)
        return resp.json()
