"""Async ABA observation writer — fire-and-forget behavioral analytics pipeline.

Runs as asyncio.create_task() from the gateway, never blocking the critical path.
Each write gets its own DB session.

Pipeline per observation:
  1. Structural extraction (sync, <5ms)
  2. Hallucination check (sync, <2ms)
  3. Upsert AgentFingerprint
  4. Create StructuralRecord
  5. Update fingerprint via FingerprintBuilder
  6. Commit
"""

import logging
import uuid
from dataclasses import dataclass
from typing import Optional

from app.db.engine import async_session_factory

logger = logging.getLogger(__name__)

# Re-classify agent type every N observations
_AGENT_TYPE_RECLASSIFY_INTERVAL = 10


@dataclass
class ABAObservationPayload:
    """All data needed for a single ABA observation."""

    org_id: str
    agent_id: str
    call_trace_id: Optional[str] = None
    prompt: str = ""
    response: str = ""
    model_used: str = ""
    latency_ms: Optional[int] = None
    cache_hit: bool = False
    input_tokens: int = 0
    output_tokens: int = 0


async def write_aba_observation(payload: ABAObservationPayload) -> None:
    """Process and persist an ABA observation. Fire-and-forget."""
    try:
        from app.db.models import (
            AgentFingerprint,
            AgentTypeClassification,
            StructuralRecord,
        )
        from app.services.fingerprint_builder import FingerprintBuilder, FingerprintUpdate
        from app.services.hallucination_detector import HallucinationDetector
        from app.services.structural_extractor import StructuralExtractor

        extractor = StructuralExtractor()
        detector = HallucinationDetector()
        builder = FingerprintBuilder()

        # 1. Structural extraction (sync, <5ms)
        messages = [{"content": payload.prompt}] if payload.prompt else []
        complexity_result = extractor.query_complexity_score(messages)
        output_type_result = extractor.classify_output_type(payload.response)

        # 2. Hallucination check (sync, <2ms)
        hallucination_result = detector.check(
            prompt=payload.prompt,
            response=payload.response,
        )

        # 3-7. DB operations
        async with async_session_factory() as session:
            from sqlalchemy import select

            org_uuid = uuid.UUID(payload.org_id)
            agent_uuid = uuid.UUID(payload.agent_id)
            trace_uuid = uuid.UUID(payload.call_trace_id) if payload.call_trace_id else None

            # Upsert AgentFingerprint (get or create)
            result = await session.execute(
                select(AgentFingerprint).where(AgentFingerprint.agent_id == agent_uuid)
            )
            fingerprint = result.scalar_one_or_none()

            if fingerprint is None:
                fingerprint = AgentFingerprint(
                    id=uuid.uuid4(),
                    agent_id=agent_uuid,
                    organisation_id=org_uuid,
                    total_observations=0,
                    avg_complexity=0.0,
                    avg_context_length=0.0,
                    hallucination_rate=0.0,
                    model_distribution={},
                    cache_hit_rate=0.0,
                    baseline_confidence=0.0,
                )
                session.add(fingerprint)
                await session.flush()

            # Determine agent type — reclassify every N observations
            current_type = AgentTypeClassification.CHATBOT
            if fingerprint.total_observations > 0 and fingerprint.total_observations % _AGENT_TYPE_RECLASSIFY_INTERVAL == 0:
                # Query recent structural records for reclassification
                recent_result = await session.execute(
                    select(StructuralRecord)
                    .where(StructuralRecord.agent_id == agent_uuid)
                    .order_by(StructuralRecord.created_at.desc())
                    .limit(50)
                )
                recent_records = recent_result.scalars().all()
                if recent_records:
                    history = [
                        {"response": "", "output_type": r.output_type_classification.value}
                        for r in recent_records
                    ]
                    agent_type_result = extractor.classify_agent_type(history)
                    current_type = agent_type_result.classification
            else:
                # Use the last record's type or default
                last_result = await session.execute(
                    select(StructuralRecord.agent_type_classification)
                    .where(StructuralRecord.agent_id == agent_uuid)
                    .order_by(StructuralRecord.created_at.desc())
                    .limit(1)
                )
                last_type = last_result.scalar_one_or_none()
                if last_type is not None:
                    current_type = last_type

            # Create StructuralRecord
            record = StructuralRecord(
                id=uuid.uuid4(),
                agent_id=agent_uuid,
                organisation_id=org_uuid,
                call_trace_id=trace_uuid,
                query_complexity_score=complexity_result.score,
                agent_type_classification=current_type,
                output_type_classification=output_type_result.classification,
                token_count=payload.input_tokens + payload.output_tokens,
                latency_ms=payload.latency_ms,
                model_used=payload.model_used or "unknown",
                cache_hit=payload.cache_hit,
                hallucination_detected=hallucination_result.detected,
            )
            session.add(record)

            # Update fingerprint via builder
            update = FingerprintUpdate(
                agent_id=payload.agent_id,
                org_id=payload.org_id,
                complexity_score=complexity_result.score,
                context_length=payload.input_tokens + payload.output_tokens,
                model_used=payload.model_used or "unknown",
                cache_hit=payload.cache_hit,
                hallucination_detected=hallucination_result.detected,
                call_trace_id=payload.call_trace_id,
            )
            builder.update_fingerprint(fingerprint, update)

            await session.commit()
            logger.debug(
                "ABA observation written: agent=%s complexity=%.4f hallucination=%s",
                payload.agent_id,
                complexity_result.score,
                hallucination_result.detected,
            )

    except Exception:
        logger.exception("Failed to write ABA observation for agent %s", payload.agent_id)
