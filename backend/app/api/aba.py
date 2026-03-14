"""ABA (Agent Behavioral Analytics) API endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_db
from app.db.models import AgentFingerprint, StructuralRecord
from app.schemas.aba import (
    AnomalyItem,
    ColdStartStatus,
    FingerprintResponse,
    ObservationCreate,
    RiskPriorResponse,
    StructuralRecordResponse,
)

router = APIRouter()


async def _get_org_id(request: Request) -> uuid.UUID:
    org_id = getattr(request.state, "org_id", None)
    if not org_id:
        raise HTTPException(status_code=403, detail="Organisation context required")
    return uuid.UUID(org_id)


# ── GET /aba/fingerprints/{agent_id} ────────────────────────────────────


@router.get("/aba/fingerprints/{agent_id}", response_model=FingerprintResponse)
async def get_fingerprint(
    agent_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Get the behavioral fingerprint for a single agent."""
    org_id = await _get_org_id(request)
    try:
        agent_uuid = uuid.UUID(agent_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid agent_id format")

    result = await db.execute(
        select(AgentFingerprint).where(
            AgentFingerprint.agent_id == agent_uuid,
            AgentFingerprint.organisation_id == org_id,
        )
    )
    fp = result.scalar_one_or_none()
    if not fp:
        raise HTTPException(status_code=404, detail="Fingerprint not found")
    return fp


# ── GET /aba/fingerprints ───────────────────────────────────────────────


@router.get("/aba/fingerprints")
async def list_fingerprints(
    request: Request,
    db: AsyncSession = Depends(get_db),
    min_observations: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """List behavioral fingerprints for the organisation."""
    org_id = await _get_org_id(request)
    query = (
        select(AgentFingerprint)
        .where(
            AgentFingerprint.organisation_id == org_id,
            AgentFingerprint.total_observations >= min_observations,
        )
        .order_by(AgentFingerprint.last_updated_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    fingerprints = result.scalars().all()

    count_query = select(func.count()).select_from(AgentFingerprint).where(
        AgentFingerprint.organisation_id == org_id,
        AgentFingerprint.total_observations >= min_observations,
    )
    total = (await db.execute(count_query)).scalar() or 0

    return {
        "data": [FingerprintResponse.model_validate(fp) for fp in fingerprints],
        "pagination": {"total": total, "limit": limit, "offset": offset},
    }


# ── GET /aba/structural-records ─────────────────────────────────────────


@router.get("/aba/structural-records")
async def list_structural_records(
    request: Request,
    db: AsyncSession = Depends(get_db),
    agent_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """List structural analysis records for the organisation."""
    org_id = await _get_org_id(request)
    conditions = [StructuralRecord.organisation_id == org_id]

    if agent_id:
        try:
            conditions.append(StructuralRecord.agent_id == uuid.UUID(agent_id))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid agent_id format")

    query = (
        select(StructuralRecord)
        .where(*conditions)
        .order_by(StructuralRecord.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    records = result.scalars().all()

    count_query = select(func.count()).select_from(StructuralRecord).where(*conditions)
    total = (await db.execute(count_query)).scalar() or 0

    return {
        "data": [
            StructuralRecordResponse(
                id=r.id,
                agent_id=r.agent_id,
                call_trace_id=r.call_trace_id,
                query_complexity_score=float(r.query_complexity_score),
                agent_type_classification=r.agent_type_classification.value,
                output_type_classification=r.output_type_classification.value,
                token_count=r.token_count,
                latency_ms=r.latency_ms,
                model_used=r.model_used,
                cache_hit=r.cache_hit,
                hallucination_detected=r.hallucination_detected,
                created_at=r.created_at,
            )
            for r in records
        ],
        "pagination": {"total": total, "limit": limit, "offset": offset},
    }


# ── GET /aba/risk-prior ─────────────────────────────────────────────────


@router.get("/aba/risk-prior", response_model=RiskPriorResponse)
async def get_risk_prior(
    request: Request,
    agent_type: str = Query(..., description="CHATBOT, RAG, CODING, WORKFLOW, AUTONOMOUS"),
    complexity_bucket: float = Query(..., ge=0.0, le=1.0),
):
    """Query the Model C global pool for a risk prior."""
    await _get_org_id(request)  # auth check
    from app.services.model_c_pool import ModelCPool

    pool = ModelCPool()
    prior = await pool.query_risk_prior(agent_type, complexity_bucket)
    return RiskPriorResponse(
        risk_score=prior.risk_score,
        observation_count=prior.observation_count,
        confidence=prior.confidence,
        recommended_model=prior.recommended_model,
    )


# ── GET /aba/anomalies ──────────────────────────────────────────────────


@router.get("/aba/anomalies")
async def list_anomalies(
    request: Request,
    db: AsyncSession = Depends(get_db),
    agent_id: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
):
    """List behavioral anomalies (deviations from baseline)."""
    org_id = await _get_org_id(request)
    from app.services.aba_anomaly_detector import ABAAnomalyDetector

    conditions = [AgentFingerprint.organisation_id == org_id]
    if agent_id:
        try:
            conditions.append(AgentFingerprint.agent_id == uuid.UUID(agent_id))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid agent_id format")

    result = await db.execute(
        select(AgentFingerprint).where(*conditions)
    )
    fingerprints = result.scalars().all()

    detector = ABAAnomalyDetector()
    anomalies: list[AnomalyItem] = []
    now = datetime.now(timezone.utc)

    for fp in fingerprints:
        detected = detector.detect_anomalies(fp)
        for a in detected:
            if severity and a.severity != severity:
                continue
            anomalies.append(AnomalyItem(
                agent_id=fp.agent_id,
                anomaly_type=a.anomaly_type,
                severity=a.severity,
                current_value=a.current_value,
                baseline_value=a.baseline_value,
                deviation_pct=a.deviation_pct,
                detected_at=now,
            ))

    return {"data": anomalies}


# ── GET /aba/cold-start-status/{agent_id} ───────────────────────────────


@router.get("/aba/cold-start-status/{agent_id}", response_model=ColdStartStatus)
async def get_cold_start_status(
    agent_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Get cold start progress for an agent."""
    org_id = await _get_org_id(request)
    try:
        agent_uuid = uuid.UUID(agent_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid agent_id format")

    result = await db.execute(
        select(AgentFingerprint).where(
            AgentFingerprint.agent_id == agent_uuid,
            AgentFingerprint.organisation_id == org_id,
        )
    )
    fp = result.scalar_one_or_none()

    from app.services.model_c_pool import COLD_START_THRESHOLD

    if not fp:
        return ColdStartStatus(
            agent_id=agent_uuid,
            total_observations=0,
            cold_start_threshold=COLD_START_THRESHOLD,
            is_cold_start=True,
            bootstrap_source=None,
            progress_pct=0.0,
        )

    is_cold = fp.total_observations < COLD_START_THRESHOLD
    progress = min(100.0, (fp.total_observations / COLD_START_THRESHOLD) * 100)

    return ColdStartStatus(
        agent_id=fp.agent_id,
        total_observations=fp.total_observations,
        cold_start_threshold=COLD_START_THRESHOLD,
        is_cold_start=is_cold,
        bootstrap_source="model_c" if is_cold and fp.total_observations > 0 else None,
        progress_pct=round(progress, 1),
    )


# ── POST /aba/observation ───────────────────────────────────────────────


@router.post("/aba/observation", status_code=202)
async def create_observation(
    body: ObservationCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Manually ingest an ABA observation (for testing/backfill)."""
    org_id = await _get_org_id(request)

    import asyncio
    from app.services.aba_writer import ABAObservationPayload, write_aba_observation

    payload = ABAObservationPayload(
        org_id=str(org_id),
        agent_id=str(body.agent_id),
        prompt=body.prompt,
        response=body.response,
        model_used=body.model_used,
        latency_ms=body.latency_ms,
        cache_hit=body.cache_hit,
        input_tokens=body.input_tokens,
        output_tokens=body.output_tokens,
    )
    asyncio.create_task(write_aba_observation(payload))

    return {"status": "accepted", "agent_id": str(body.agent_id)}
