"""ABA (Agent Behavioral Analytics) types for the ASAHIO Python SDK."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Fingerprint:
    """Agent behavioral fingerprint."""

    agent_id: str
    organisation_id: str
    total_observations: int
    avg_complexity: float
    avg_context_length: float
    hallucination_rate: float
    model_distribution: dict
    cache_hit_rate: float
    baseline_confidence: float
    tool_usage_distribution: Optional[dict]
    tool_success_rates: Optional[dict]
    tool_risk_correlation: Optional[dict]
    preferred_model_by_tool: Optional[dict]
    last_updated_at: str
    created_at: str

    @classmethod
    def from_dict(cls, data: dict) -> "Fingerprint":
        return cls(
            agent_id=data["agent_id"],
            organisation_id=data["organisation_id"],
            total_observations=data["total_observations"],
            avg_complexity=data["avg_complexity"],
            avg_context_length=data["avg_context_length"],
            hallucination_rate=data["hallucination_rate"],
            model_distribution=data.get("model_distribution") or {},
            cache_hit_rate=data["cache_hit_rate"],
            baseline_confidence=data["baseline_confidence"],
            tool_usage_distribution=data.get("tool_usage_distribution"),
            tool_success_rates=data.get("tool_success_rates"),
            tool_risk_correlation=data.get("tool_risk_correlation"),
            preferred_model_by_tool=data.get("preferred_model_by_tool"),
            last_updated_at=data["last_updated_at"],
            created_at=data["created_at"],
        )


@dataclass
class StructuralRecord:
    """A structural analysis record."""

    id: str
    agent_id: str
    organisation_id: str
    call_trace_id: Optional[str]
    query_complexity_score: float
    agent_type_classification: str
    output_type_classification: str
    token_count: int
    latency_ms: Optional[int]
    model_used: str
    cache_hit: bool
    hallucination_detected: bool
    created_at: str

    @classmethod
    def from_dict(cls, data: dict) -> "StructuralRecord":
        return cls(
            id=data["id"],
            agent_id=data["agent_id"],
            organisation_id=data["organisation_id"],
            call_trace_id=data.get("call_trace_id"),
            query_complexity_score=data["query_complexity_score"],
            agent_type_classification=data["agent_type_classification"],
            output_type_classification=data["output_type_classification"],
            token_count=data["token_count"],
            latency_ms=data.get("latency_ms"),
            model_used=data["model_used"],
            cache_hit=data["cache_hit"],
            hallucination_detected=data["hallucination_detected"],
            created_at=data["created_at"],
        )


@dataclass
class RiskPrior:
    """Global risk prior from Model C."""

    agent_type: str
    complexity_bucket: float
    risk_score: float
    sample_size: int

    @classmethod
    def from_dict(cls, data: dict) -> "RiskPrior":
        return cls(
            agent_type=data["agent_type"],
            complexity_bucket=data["complexity_bucket"],
            risk_score=data["risk_score"],
            sample_size=data["sample_size"],
        )


@dataclass
class AnomalyItem:
    """An anomaly detection result."""

    id: str
    agent_id: str
    anomaly_type: str
    severity: str
    description: str
    detected_at: str
    metadata: dict

    @classmethod
    def from_dict(cls, data: dict) -> "AnomalyItem":
        return cls(
            id=data["id"],
            agent_id=data["agent_id"],
            anomaly_type=data["anomaly_type"],
            severity=data["severity"],
            description=data["description"],
            detected_at=data["detected_at"],
            metadata=data.get("metadata") or {},
        )


@dataclass
class ColdStartStatus:
    """Cold start status for an agent."""

    agent_id: str
    is_cold_start: bool
    observations_collected: int
    observations_needed: int
    baseline_confidence: float
    estimated_days_remaining: Optional[int]

    @classmethod
    def from_dict(cls, data: dict) -> "ColdStartStatus":
        return cls(
            agent_id=data["agent_id"],
            is_cold_start=data["is_cold_start"],
            observations_collected=data["observations_collected"],
            observations_needed=data["observations_needed"],
            baseline_confidence=data["baseline_confidence"],
            estimated_days_remaining=data.get("estimated_days_remaining"),
        )


@dataclass
class OrgOverview:
    """Organization-wide ABA overview."""

    total_agents: int
    agents_in_cold_start: int
    total_observations: int
    avg_baseline_confidence: float
    top_anomalies: list[AnomalyItem]

    @classmethod
    def from_dict(cls, data: dict) -> "OrgOverview":
        return cls(
            total_agents=data["total_agents"],
            agents_in_cold_start=data["agents_in_cold_start"],
            total_observations=data["total_observations"],
            avg_baseline_confidence=data["avg_baseline_confidence"],
            top_anomalies=[AnomalyItem.from_dict(a) for a in data.get("top_anomalies", [])],
        )
