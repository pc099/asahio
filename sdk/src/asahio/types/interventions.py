"""Intervention-related types for the ASAHIO Python SDK."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class InterventionLog:
    """An intervention log entry."""

    id: str
    organisation_id: str
    agent_id: Optional[str]
    call_trace_id: Optional[str]
    request_id: Optional[str]
    intervention_level: int
    intervention_mode: str
    risk_score: float
    risk_factors: dict
    action_taken: str
    action_detail: Optional[str]
    original_model: Optional[str]
    final_model: Optional[str]
    prompt_modified: bool
    was_blocked: bool
    created_at: str

    @classmethod
    def from_dict(cls, data: dict) -> "InterventionLog":
        return cls(
            id=data["id"],
            organisation_id=data["organisation_id"],
            agent_id=data.get("agent_id"),
            call_trace_id=data.get("call_trace_id"),
            request_id=data.get("request_id"),
            intervention_level=data["intervention_level"],
            intervention_mode=data["intervention_mode"],
            risk_score=data["risk_score"],
            risk_factors=data.get("risk_factors") or {},
            action_taken=data["action_taken"],
            action_detail=data.get("action_detail"),
            original_model=data.get("original_model"),
            final_model=data.get("final_model"),
            prompt_modified=data.get("prompt_modified", False),
            was_blocked=data.get("was_blocked", False),
            created_at=data["created_at"],
        )


@dataclass
class InterventionStats:
    """Intervention statistics by level."""

    data: list[dict]
    days: int

    @classmethod
    def from_dict(cls, data: dict) -> "InterventionStats":
        return cls(
            data=data.get("data", []),
            days=data["days"],
        )


@dataclass
class FleetOverview:
    """Fleet-wide intervention overview."""

    mode_distribution: dict
    intervention_summary: dict

    @classmethod
    def from_dict(cls, data: dict) -> "FleetOverview":
        return cls(
            mode_distribution=data.get("mode_distribution") or {},
            intervention_summary=data.get("intervention_summary") or {},
        )
