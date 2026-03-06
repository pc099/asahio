"""Metering middleware for gateway traffic."""

import asyncio
import logging
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.db.engine import async_session_factory
from app.db.models import CallTrace, CacheType, Organisation, RequestLog, RoutingDecisionLog
from app.services.metering import record_usage
from app.services.stripe import record_stripe_usage

logger = logging.getLogger(__name__)


class MeteringMiddleware(BaseHTTPMiddleware):
    """Track usage for every gateway request via Redis and PostgreSQL."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        if not request.url.path.startswith("/v1/"):
            return response

        inference_result = getattr(request.state, "inference_result", None)
        if not inference_result:
            return response

        org_id = getattr(request.state, "org_id", None)
        api_key_id = getattr(request.state, "api_key_id", None)
        if not org_id:
            return response

        redis = getattr(request.app.state, "redis", None)
        asyncio.create_task(
            _meter_request(
                redis=redis,
                org_id=org_id,
                api_key_id=api_key_id,
                inference_result=inference_result,
                status_code=response.status_code,
            )
        )
        return response


async def _meter_request(redis, org_id: str, api_key_id: str | None, inference_result: object, status_code: int) -> None:
    input_tokens = getattr(inference_result, "input_tokens", 0)
    output_tokens = getattr(inference_result, "output_tokens", 0)
    cost_with = getattr(inference_result, "cost_with_asahi", 0.0)
    savings_usd = getattr(inference_result, "savings_usd", 0.0)
    cache_hit = getattr(inference_result, "cache_hit", False)

    if redis:
        try:
            await record_usage(
                redis=redis,
                org_id=org_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_hit=cache_hit,
                savings_usd=savings_usd,
                cost_usd=cost_with,
            )
        except Exception:
            logger.exception("Redis metering failed for org %s", org_id)

    try:
        await _write_request_log(org_id, api_key_id, inference_result, status_code)
    except Exception:
        logger.exception("DB metering failed for org %s", org_id)


async def _write_request_log(org_id: str, api_key_id: str | None, inference_result: object, status_code: int) -> None:
    model_used = getattr(inference_result, "model_used", "unknown")
    model_requested = getattr(inference_result, "model_requested", None)
    provider = getattr(inference_result, "provider", None)
    routing_mode = getattr(inference_result, "routing_mode", None)
    intervention_mode = getattr(inference_result, "intervention_mode", None)
    request_id = getattr(inference_result, "request_id", None)
    agent_id = getattr(inference_result, "agent_id", None)
    agent_session_id = getattr(inference_result, "agent_session_id", None)
    model_endpoint_id = getattr(inference_result, "model_endpoint_id", None)
    input_tokens = getattr(inference_result, "input_tokens", 0)
    output_tokens = getattr(inference_result, "output_tokens", 0)
    cost_without = getattr(inference_result, "cost_without_asahi", 0.0)
    cost_with = getattr(inference_result, "cost_with_asahi", 0.0)
    savings_usd = getattr(inference_result, "savings_usd", 0.0)
    savings_pct = getattr(inference_result, "savings_pct", None)
    cache_hit = getattr(inference_result, "cache_hit", False)
    cache_tier_str = getattr(inference_result, "cache_tier", None)
    latency_ms = getattr(inference_result, "latency_ms", None)
    error_message = getattr(inference_result, "error_message", None)
    routing_reason = getattr(inference_result, "routing_reason", None)
    routing_factors = getattr(inference_result, "routing_factors", {}) or {}
    routing_confidence = getattr(inference_result, "routing_confidence", None)
    policy_action = getattr(inference_result, "policy_action", None)
    policy_reason = getattr(inference_result, "policy_reason", None)

    cache_tier = None
    if cache_tier_str:
        tier_map = {
            "exact": CacheType.EXACT,
            "semantic": CacheType.SEMANTIC,
            "intermediate": CacheType.INTERMEDIATE,
            "miss": CacheType.MISS,
        }
        cache_tier = tier_map.get(cache_tier_str.lower())

    async with async_session_factory() as session:
        log_entry = RequestLog(
            id=uuid.uuid4(),
            organisation_id=uuid.UUID(org_id),
            api_key_id=uuid.UUID(api_key_id) if api_key_id else None,
            agent_id=uuid.UUID(agent_id) if agent_id else None,
            agent_session_id=uuid.UUID(agent_session_id) if agent_session_id else None,
            model_endpoint_id=uuid.UUID(model_endpoint_id) if model_endpoint_id else None,
            request_id=request_id,
            model_requested=model_requested,
            model_used=model_used,
            provider=provider,
            routing_mode=routing_mode,
            intervention_mode=intervention_mode,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_without_asahi=cost_without,
            cost_with_asahi=cost_with,
            savings_usd=savings_usd,
            savings_pct=savings_pct,
            cache_hit=cache_hit,
            cache_tier=cache_tier,
            latency_ms=latency_ms,
            status_code=status_code,
            error_message=error_message,
        )
        session.add(log_entry)
        await session.flush()

        call_trace = CallTrace(
            organisation_id=uuid.UUID(org_id),
            agent_id=uuid.UUID(agent_id) if agent_id else None,
            agent_session_id=uuid.UUID(agent_session_id) if agent_session_id else None,
            request_log_id=log_entry.id,
            request_id=request_id,
            model_requested=model_requested,
            model_used=model_used,
            provider=provider,
            routing_mode=routing_mode,
            intervention_mode=intervention_mode,
            policy_action=policy_action,
            policy_reason=policy_reason,
            cache_hit=cache_hit,
            cache_tier=cache_tier_str,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            trace_metadata={"status_code": status_code, "error_message": error_message},
        )
        session.add(call_trace)
        await session.flush()

        routing_decision = RoutingDecisionLog(
            organisation_id=uuid.UUID(org_id),
            agent_id=uuid.UUID(agent_id) if agent_id else None,
            call_trace_id=call_trace.id,
            routing_mode=routing_mode,
            intervention_mode=intervention_mode,
            selected_model=model_used,
            selected_provider=provider,
            confidence=routing_confidence,
            decision_summary=routing_reason,
            factors=routing_factors,
        )
        session.add(routing_decision)

        org = await session.get(Organisation, uuid.UUID(org_id))
        if org:
            await record_stripe_usage(org, input_tokens + output_tokens, request_id or str(log_entry.id))

        await session.commit()
