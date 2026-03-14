"""Pydantic schemas for ABA (Agent Behavioral Analytics) API."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FingerprintResponse(BaseModel):
    """Single agent behavioral fingerprint."""

    id: uuid.UUID
    agent_id: uuid.UUID
    organisation_id: uuid.UUID
    total_observations: int
    avg_complexity: float
    avg_context_length: float
    hallucination_rate: float
    model_distribution: dict[str, int]
    cache_hit_rate: float
    baseline_confidence: float
    last_updated_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class StructuralRecordResponse(BaseModel):
    """Single structural analysis record."""

    id: uuid.UUID
    agent_id: uuid.UUID
    call_trace_id: Optional[uuid.UUID] = None
    query_complexity_score: float
    agent_type_classification: str
    output_type_classification: str
    token_count: int
    latency_ms: Optional[int] = None
    model_used: str
    cache_hit: bool
    hallucination_detected: bool
    created_at: datetime

    class Config:
        from_attributes = True


class RiskPriorResponse(BaseModel):
    """Risk prior from the Model C global pool."""

    risk_score: float
    observation_count: int
    confidence: float
    recommended_model: Optional[str] = None


class AnomalyItem(BaseModel):
    """A detected behavioral anomaly."""

    agent_id: uuid.UUID
    anomaly_type: str = Field(description="hallucination_spike, complexity_shift, model_drift, cache_degradation")
    severity: str = Field(description="low, medium, high")
    current_value: float
    baseline_value: float
    deviation_pct: float
    detected_at: datetime


class ColdStartStatus(BaseModel):
    """Cold start progress for an agent."""

    agent_id: uuid.UUID
    total_observations: int
    cold_start_threshold: int = 10
    is_cold_start: bool
    bootstrap_source: Optional[str] = None
    progress_pct: float = Field(ge=0.0, le=100.0)


class ObservationCreate(BaseModel):
    """Request body for manual observation ingestion."""

    agent_id: uuid.UUID
    prompt: str = ""
    response: str = ""
    model_used: str = "unknown"
    latency_ms: Optional[int] = None
    cache_hit: bool = False
    input_tokens: int = 0
    output_tokens: int = 0
