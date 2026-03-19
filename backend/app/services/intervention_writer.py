"""Async intervention log writer — fire-and-forget persistence.

Runs as asyncio.create_task() from the gateway, never blocking the critical path.
Each write gets its own DB session.
"""

import logging
import uuid
from dataclasses import dataclass, field
from typing import Optional

from app.db.engine import async_session_factory

logger = logging.getLogger(__name__)


@dataclass
class InterventionLogPayload:
    """All data needed to persist an intervention log entry."""

    org_id: str
    intervention_level: int
    intervention_mode: str
    risk_score: float
    risk_factors: dict = field(default_factory=dict)
    action_taken: str = "log"
    action_detail: Optional[str] = None
    agent_id: Optional[str] = None
    call_trace_id: Optional[str] = None
    request_id: Optional[str] = None
    original_model: Optional[str] = None
    final_model: Optional[str] = None
    prompt_modified: bool = False
    was_blocked: bool = False


async def write_intervention_log(payload: InterventionLogPayload) -> None:
    """Persist an intervention log entry. Fire-and-forget."""
    try:
        from app.db.models import InterventionLog

        log_entry = InterventionLog(
            id=uuid.uuid4(),
            organisation_id=uuid.UUID(payload.org_id),
            agent_id=uuid.UUID(payload.agent_id) if payload.agent_id else None,
            call_trace_id=uuid.UUID(payload.call_trace_id) if payload.call_trace_id else None,
            request_id=payload.request_id,
            intervention_level=payload.intervention_level,
            intervention_mode=payload.intervention_mode,
            risk_score=payload.risk_score,
            risk_factors=payload.risk_factors,
            action_taken=payload.action_taken,
            action_detail=payload.action_detail,
            original_model=payload.original_model,
            final_model=payload.final_model,
            prompt_modified=payload.prompt_modified,
            was_blocked=payload.was_blocked,
        )

        async with async_session_factory() as session:
            session.add(log_entry)
            await session.commit()
            logger.debug(
                "Intervention log written: level=%d action=%s risk=%.4f",
                payload.intervention_level,
                payload.action_taken,
                payload.risk_score,
            )

    except Exception:
        logger.exception(
            "Failed to write intervention log for org %s", payload.org_id,
        )
