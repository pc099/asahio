"""Billing routes for ASAHIO."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_db
from app.db.models import Organisation, RequestLog
from app.services.metering import get_monthly_budget
from app.services.stripe import (
    PLANS,
    create_checkout_session,
    create_portal_session,
    get_billing_summary,
    handle_webhook,
    list_invoices,
)

router = APIRouter()


class CheckoutRequest(BaseModel):
    plan: str
    success_url: str
    cancel_url: str


class PortalRequest(BaseModel):
    return_url: str


class BillingPlanResponse(BaseModel):
    id: str
    name: str
    monthly_request_limit: int
    monthly_token_limit: int
    monthly_budget_usd: Optional[float]
    price_monthly_usd: Optional[float]
    features: list[str]


class BillingUsageResponse(BaseModel):
    month: str
    requests_used: int
    tokens_used: int
    spend_usd: float
    request_limit: int
    token_limit: int
    request_usage_pct: float
    token_usage_pct: float


async def _get_org(request: Request, db: AsyncSession) -> Organisation:
    org_id = getattr(request.state, "org_id", None)
    if not org_id:
        raise HTTPException(status_code=403, detail="Organisation context required")
    org = await db.get(Organisation, uuid.UUID(org_id))
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")
    return org


@router.get("/plans", response_model=list[BillingPlanResponse])
async def billing_plans() -> list[BillingPlanResponse]:
    return [BillingPlanResponse(id=plan_id, **plan) for plan_id, plan in PLANS.items()]


@router.get("/subscription")
async def billing_subscription(request: Request, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    org = await _get_org(request, db)
    return await get_billing_summary(db, org)


@router.post("/checkout")
async def billing_checkout(
    body: CheckoutRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    org = await _get_org(request, db)
    try:
        return await create_checkout_session(db, org, body.plan, body.success_url, body.cancel_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/portal")
async def billing_portal(
    body: PortalRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    org = await _get_org(request, db)
    return await create_portal_session(db, org, body.return_url)


@router.get("/usage", response_model=BillingUsageResponse)
async def billing_usage(request: Request, db: AsyncSession = Depends(get_db)) -> BillingUsageResponse:
    org = await _get_org(request, db)
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    token_result = await db.execute(
        select(
            func.coalesce(func.sum(RequestLog.input_tokens + RequestLog.output_tokens), 0),
            func.coalesce(func.sum(RequestLog.cost_with_asahi), 0),
            func.count(RequestLog.id),
        ).where(
            RequestLog.organisation_id == org.id,
            RequestLog.created_at >= month_start,
        )
    )
    total_tokens, spend_usd, request_count = token_result.one()

    redis = getattr(request.app.state, "redis", None)
    meter = await get_monthly_budget(redis, str(org.id)) if redis else {"request_count": request_count or 0}
    requests_used = int(meter.get("request_count", request_count or 0))
    tokens_used = int(total_tokens or 0)
    request_limit = int(org.monthly_request_limit)
    token_limit = int(org.monthly_token_limit)

    request_pct = 0.0 if request_limit <= 0 else min(100.0, requests_used / request_limit * 100)
    token_pct = 0.0 if token_limit <= 0 else min(100.0, tokens_used / token_limit * 100)

    return BillingUsageResponse(
        month=month_start.strftime("%Y-%m"),
        requests_used=requests_used,
        tokens_used=tokens_used,
        spend_usd=round(float(spend_usd or 0), 4),
        request_limit=request_limit,
        token_limit=token_limit,
        request_usage_pct=round(request_pct, 2),
        token_usage_pct=round(token_pct, 2),
    )


@router.get("/invoices")
async def billing_invoices(request: Request, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    org = await _get_org(request, db)
    return {"data": await list_invoices(org)}


@router.post("/webhooks")
async def billing_webhooks(
    request: Request,
    db: AsyncSession = Depends(get_db),
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
) -> dict[str, Any]:
    payload = await request.body()
    redis = getattr(request.app.state, "redis", None)
    return await handle_webhook(db, payload, stripe_signature, redis=redis)
