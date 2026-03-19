"""Health check endpoints — liveness, readiness, and provider health.

Exposes no internal configuration. Designed for container orchestration
(Kubernetes, Railway) and monitoring dashboards.
"""

import logging

from fastapi import APIRouter, Request
from sqlalchemy import text

router = APIRouter(tags=["health"])

logger = logging.getLogger(__name__)


@router.get("/health/live")
async def health_live():
    """Liveness probe — always returns 200 if the process is running."""
    return {"status": "ok"}


@router.get("/health/ready")
async def health_ready(request: Request):
    """Readiness probe — checks all backend components."""
    components: dict[str, str] = {}

    # PostgreSQL
    try:
        from app.db.engine import async_session_factory

        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        components["postgres"] = "connected"
    except Exception as exc:
        logger.warning("Readiness: PostgreSQL check failed: %s", exc)
        components["postgres"] = "unavailable"

    # Redis
    redis = getattr(request.app.state, "redis", None)
    if redis:
        try:
            await redis.ping()
            components["redis"] = "connected"
        except Exception:
            components["redis"] = "unavailable"
    else:
        components["redis"] = "not_configured"

    # Pinecone
    try:
        from app.services.cache import RedisCache

        if redis:
            cache = RedisCache(redis)
            pc_index = cache._get_pinecone_index()
            components["pinecone"] = "connected" if pc_index is not None else "not_configured"
        else:
            components["pinecone"] = "not_configured"
    except Exception:
        components["pinecone"] = "unavailable"

    # Provider health
    try:
        from app.services.provider_health import get_all_provider_health

        provider_statuses = get_all_provider_health()
        components["providers"] = provider_statuses
    except Exception:
        components["providers"] = {}

    all_ok = all(
        v in ("connected", "not_configured")
        for k, v in components.items()
        if k != "providers"
    )

    return {
        "status": "ok" if all_ok else "degraded",
        "version": "1.0.0",
        "components": components,
    }


@router.get("/health/providers")
async def health_providers():
    """Detailed provider health status for monitoring dashboards."""
    try:
        from app.services.provider_health import (
            _health_registry,
        )

        providers = []
        for provider, status in _health_registry.items():
            providers.append({
                "provider": status.provider,
                "status": status.status,
                "last_checked": status.last_checked,
                "error": status.error,
            })

        return {"providers": providers}
    except Exception:
        return {"providers": []}
