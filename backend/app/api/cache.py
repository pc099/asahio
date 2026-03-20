"""Cache management routes — cache warming, stats, and analytics."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_db
from app.middleware.rbac import require_role
from app.db.models import MemberRole

router = APIRouter()


async def _get_org_id(request: Request) -> uuid.UUID:
    org_id = getattr(request.state, "org_id", None)
    if not org_id:
        raise HTTPException(status_code=403, detail="Organisation context required")
    return uuid.UUID(org_id)


class CacheWarmEntry(BaseModel):
    query: str = Field(..., min_length=1)
    response: str = Field(..., min_length=1)
    model_used: str = Field(default="cached")


class CacheWarmRequest(BaseModel):
    entries: list[CacheWarmEntry] = Field(..., min_length=1, max_length=100)
    ttl: int = Field(default=86400, ge=60, le=604800)


@router.post("/warm", dependencies=[require_role(MemberRole.ADMIN)])
async def warm_cache(
    body: CacheWarmRequest,
    request: Request,
) -> dict:
    """Pre-populate exact cache from a list of query/response pairs.

    Useful for warming up frequently-asked queries after deployment or
    loading golden responses into cache for guided routing scenarios.
    """
    org_id = await _get_org_id(request)
    redis = getattr(request.app.state, "redis", None)
    if not redis:
        raise HTTPException(status_code=503, detail="Cache service unavailable")

    from app.services.cache import RedisCache

    cache = RedisCache(redis)
    entries_dicts = [
        {"query": e.query, "response": e.response, "model_used": e.model_used}
        for e in body.entries
    ]
    cached_count = await cache.warm(str(org_id), entries_dicts, ttl=body.ttl)

    return {
        "warmed": cached_count,
        "total": len(body.entries),
        "ttl": body.ttl,
    }


@router.get("/stats")
async def cache_stats(request: Request) -> dict:
    """Return in-memory cache metrics (exact hits, semantic hits, misses, promotions)."""
    redis = getattr(request.app.state, "redis", None)
    if not redis:
        return {"metrics": {"exact_hits": 0, "semantic_hits": 0, "misses": 0, "promotions": 0, "hit_rate": 0.0}}

    from app.services.cache import RedisCache

    cache = RedisCache(redis)
    return {"metrics": cache.metrics.to_dict()}
