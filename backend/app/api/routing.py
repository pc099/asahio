"""Routing decision audit routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_db
from app.db.models import RoutingDecisionLog

router = APIRouter()


async def _get_org_id(request: Request) -> uuid.UUID:
    org_id = getattr(request.state, "org_id", None)
    if not org_id:
        raise HTTPException(status_code=403, detail="Organisation context required")
    return uuid.UUID(org_id)


@router.get("/decisions")
async def list_routing_decisions(
    request: Request,
    db: AsyncSession = Depends(get_db),
    agent_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> dict:
    org_id = await _get_org_id(request)
    query = select(RoutingDecisionLog).where(RoutingDecisionLog.organisation_id == org_id)
    if agent_id:
        query = query.where(RoutingDecisionLog.agent_id == uuid.UUID(agent_id))
    query = query.order_by(RoutingDecisionLog.created_at.desc()).limit(limit)

    result = await db.execute(query)
    rows = result.scalars().all()
    return {
        "data": [
            {
                "id": str(row.id),
                "agent_id": str(row.agent_id) if row.agent_id else None,
                "call_trace_id": str(row.call_trace_id) if row.call_trace_id else None,
                "routing_mode": row.routing_mode,
                "intervention_mode": row.intervention_mode,
                "selected_model": row.selected_model,
                "selected_provider": row.selected_provider,
                "confidence": float(row.confidence) if row.confidence is not None else None,
                "decision_summary": row.decision_summary,
                "factors": row.factors or {},
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
    }
