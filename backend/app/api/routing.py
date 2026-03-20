"""Routing decision audit routes, constraint CRUD, dry-run, and weight overrides."""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_db
from app.db.models import MemberRole, Organisation, RoutingConstraint, RoutingDecisionLog
from app.middleware.rbac import require_role
from app.schemas.routing import ConstraintCreate, ConstraintResponse, ConstraintUpdate
from app.services.rule_validator import validate_rule
from app.services.routing import RoutingContext, RoutingEngine

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


# ---------------------------------------------------------------------------
# Constraint CRUD
# ---------------------------------------------------------------------------

def _serialize_constraint(row: RoutingConstraint) -> dict:
    """Convert a RoutingConstraint row to a response dict."""
    return {
        "id": str(row.id),
        "organisation_id": str(row.organisation_id),
        "agent_id": str(row.agent_id) if row.agent_id else None,
        "rule_type": row.rule_type,
        "rule_config": row.rule_config or {},
        "priority": row.priority,
        "is_active": row.is_active,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


@router.post("/constraints", status_code=201, dependencies=[require_role(MemberRole.ADMIN)])
async def create_constraint(
    body: ConstraintCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a routing constraint. Validates rule config before persisting."""
    org_id = await _get_org_id(request)

    errors = validate_rule(body.rule_type, body.rule_config)
    if errors:
        raise HTTPException(status_code=422, detail={"validation_errors": errors})

    constraint = RoutingConstraint(
        organisation_id=org_id,
        agent_id=body.agent_id,
        rule_type=body.rule_type,
        rule_config=body.rule_config,
        priority=body.priority,
    )
    db.add(constraint)
    await db.flush()
    await db.refresh(constraint)
    await db.commit()
    return {"data": _serialize_constraint(constraint)}


@router.get("/constraints")
async def list_constraints(
    request: Request,
    db: AsyncSession = Depends(get_db),
    agent_id: str | None = Query(default=None),
    active_only: bool = Query(default=True),
) -> dict:
    """List routing constraints for the organisation."""
    org_id = await _get_org_id(request)
    query = select(RoutingConstraint).where(RoutingConstraint.organisation_id == org_id)
    if agent_id:
        query = query.where(RoutingConstraint.agent_id == uuid.UUID(agent_id))
    if active_only:
        query = query.where(RoutingConstraint.is_active.is_(True))
    query = query.order_by(RoutingConstraint.priority.desc(), RoutingConstraint.created_at)

    result = await db.execute(query)
    rows = result.scalars().all()
    return {"data": [_serialize_constraint(row) for row in rows]}


@router.put("/constraints/{constraint_id}", dependencies=[require_role(MemberRole.ADMIN)])
async def update_constraint(
    constraint_id: uuid.UUID,
    body: ConstraintUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update a routing constraint."""
    org_id = await _get_org_id(request)
    result = await db.execute(
        select(RoutingConstraint).where(
            RoutingConstraint.id == constraint_id,
            RoutingConstraint.organisation_id == org_id,
        )
    )
    constraint = result.scalar_one_or_none()
    if not constraint:
        raise HTTPException(status_code=404, detail="Constraint not found")

    if body.rule_config is not None:
        errors = validate_rule(constraint.rule_type, body.rule_config)
        if errors:
            raise HTTPException(status_code=422, detail={"validation_errors": errors})
        constraint.rule_config = body.rule_config

    if body.priority is not None:
        constraint.priority = body.priority
    if body.is_active is not None:
        constraint.is_active = body.is_active

    await db.flush()
    await db.refresh(constraint)
    await db.commit()
    return {"data": _serialize_constraint(constraint)}


@router.delete("/constraints/{constraint_id}", dependencies=[require_role(MemberRole.ADMIN)])
async def delete_constraint(
    constraint_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Soft-delete a routing constraint (set is_active=False)."""
    org_id = await _get_org_id(request)
    result = await db.execute(
        select(RoutingConstraint).where(
            RoutingConstraint.id == constraint_id,
            RoutingConstraint.organisation_id == org_id,
        )
    )
    constraint = result.scalar_one_or_none()
    if not constraint:
        raise HTTPException(status_code=404, detail="Constraint not found")

    constraint.is_active = False
    await db.flush()
    await db.refresh(constraint)
    await db.commit()
    return {"data": _serialize_constraint(constraint)}


# ---------------------------------------------------------------------------
# Rule Dry-Run
# ---------------------------------------------------------------------------


class DryRunRequest(BaseModel):
    rule_type: str
    rule_config: dict
    prompt: str = "Test prompt for dry-run"
    session_step: Optional[int] = None
    utc_hour: Optional[int] = None


@router.post("/rules/dry-run")
async def dry_run_rule(
    body: DryRunRequest,
    request: Request,
) -> dict:
    """Dry-run a routing rule: returns which model would be selected without executing.

    Validates the rule config first, then simulates routing through the engine.
    """
    await _get_org_id(request)

    errors = validate_rule(body.rule_type, body.rule_config)
    if errors:
        raise HTTPException(status_code=422, detail={"validation_errors": errors})

    # Build guided rules dict from the single rule
    guided_rules: dict = {}
    if body.rule_type == "step_based":
        guided_rules["step_based"] = body.rule_config.get("rules", [])
    elif body.rule_type == "time_based":
        guided_rules["time_based"] = body.rule_config.get("rules", [])
    elif body.rule_type == "fallback_chain":
        guided_rules["fallback_chain"] = body.rule_config.get("chain", [])
    elif body.rule_type == "cost_ceiling_per_1k":
        guided_rules["cost_ceiling_per_1k"] = body.rule_config.get("value")
    elif body.rule_type == "model_allowlist":
        guided_rules["model_allowlist"] = body.rule_config.get("models", [])
    elif body.rule_type == "provider_restriction":
        guided_rules["provider_restriction"] = body.rule_config.get("provider")

    ctx = RoutingContext(
        prompt=body.prompt,
        routing_mode="GUIDED",
        guided_rules=guided_rules,
        session_step=body.session_step,
        utc_hour=body.utc_hour,
    )

    engine = RoutingEngine()
    decision = engine.route(ctx)

    return {
        "data": {
            "selected_model": decision.selected_model,
            "selected_provider": decision.selected_provider,
            "confidence": decision.confidence,
            "reason": decision.reason,
            "factors": decision.factors,
        }
    }


# ---------------------------------------------------------------------------
# Routing Weight Overrides
# ---------------------------------------------------------------------------

DEFAULT_ROUTING_WEIGHTS = {
    "quality": 0.40,
    "cost": 0.25,
    "complexity_match": 0.15,
    "latency": 0.10,
    "health": 0.05,
    "budget": 0.05,
}


@router.get("/weights")
async def get_routing_weights(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get the current Auto routing factor weights for this org."""
    org_id = await _get_org_id(request)
    result = await db.execute(
        select(Organisation).where(Organisation.id == org_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")

    overrides = org.routing_weight_overrides or {}
    merged = {**DEFAULT_ROUTING_WEIGHTS, **overrides}
    return {"data": merged, "is_custom": bool(overrides)}


class WeightUpdateRequest(BaseModel):
    weights: dict


@router.put("/weights", dependencies=[require_role(MemberRole.ADMIN)])
async def update_routing_weights(
    body: WeightUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update Auto routing factor weights for this org. Requires admin role."""
    org_id = await _get_org_id(request)
    result = await db.execute(
        select(Organisation).where(Organisation.id == org_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")

    # Validate weight keys
    valid_keys = set(DEFAULT_ROUTING_WEIGHTS.keys())
    invalid_keys = set(body.weights.keys()) - valid_keys
    if invalid_keys:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid weight keys: {sorted(invalid_keys)}. Valid: {sorted(valid_keys)}",
        )

    # Validate all values are numeric and positive
    for key, value in body.weights.items():
        if not isinstance(value, (int, float)) or value < 0:
            raise HTTPException(
                status_code=422,
                detail=f"Weight '{key}' must be a non-negative number, got: {value}",
            )

    org.routing_weight_overrides = body.weights
    await db.flush()
    await db.commit()

    merged = {**DEFAULT_ROUTING_WEIGHTS, **body.weights}
    return {"data": merged, "is_custom": True}
