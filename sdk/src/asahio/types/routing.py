"""Routing-related types for the ASAHIO Python SDK."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class RoutingDecision:
    """A routing decision log entry."""

    id: str
    agent_id: Optional[str]
    routing_mode: str
    selected_model: str
    selected_provider: str
    confidence: float
    decision_summary: str
    factors: dict
    created_at: str

    @classmethod
    def from_dict(cls, data: dict) -> "RoutingDecision":
        return cls(
            id=data["id"],
            agent_id=data.get("agent_id"),
            routing_mode=data["routing_mode"],
            selected_model=data["selected_model"],
            selected_provider=data["selected_provider"],
            confidence=data["confidence"],
            decision_summary=data["decision_summary"],
            factors=data.get("factors") or {},
            created_at=data["created_at"],
        )


@dataclass
class RoutingConstraint:
    """A GUIDED routing constraint/rule."""

    id: str
    organisation_id: str
    agent_id: Optional[str]
    rule_type: str
    rule_config: dict
    priority: int
    is_active: bool
    created_at: str

    @classmethod
    def from_dict(cls, data: dict) -> "RoutingConstraint":
        return cls(
            id=data["id"],
            organisation_id=data["organisation_id"],
            agent_id=data.get("agent_id"),
            rule_type=data["rule_type"],
            rule_config=data.get("rule_config") or {},
            priority=data["priority"],
            is_active=data.get("is_active", True),
            created_at=data["created_at"],
        )


@dataclass
class DryRunResult:
    """Result of a routing rule dry-run test."""

    selected_model: str
    selected_provider: str
    confidence: float
    reason: str
    factors: dict

    @classmethod
    def from_dict(cls, data: dict) -> "DryRunResult":
        return cls(
            selected_model=data["selected_model"],
            selected_provider=data["selected_provider"],
            confidence=data["confidence"],
            reason=data["reason"],
            factors=data.get("factors") or {},
        )
