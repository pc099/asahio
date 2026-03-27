"""Model C Global Pool — anonymized cross-org behavioral knowledge.

Aggregates structural record observations across organisations to provide
risk priors and cold-start bootstrapping for new agents.

Privacy: No org_id or agent_id stored in the pool. Complexity bucketed
to 0.1 granularity. Minimum 50 org observations before contributing.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

PRIVACY_THRESHOLD = 50  # Minimum org observations before contributing
COLD_START_THRESHOLD = 10  # Agent needs this many observations before it's "warm"


@dataclass
class RiskPrior:
    """Risk assessment from the global behavioral pool."""

    risk_score: float  # 0.0–1.0, higher = more risky
    observation_count: int
    confidence: float  # 0.0–1.0
    recommended_model: Optional[str] = None


@dataclass
class PoolRecord:
    """An anonymized observation in the global pool."""

    agent_type: str
    complexity_bucket: float  # 0.0, 0.1, ..., 1.0
    output_type: str
    model_used: str
    hallucination_detected: bool
    cache_hit: bool
    latency_ms: Optional[int] = None


class ModelCPool:
    """Global behavioral knowledge pool. Anonymized, cross-org.

    In production: backed by a Pinecone index (separate from cache).
    In tests/dev: in-memory dictionary.
    """

    def __init__(self, pinecone_index=None) -> None:
        self._index = pinecone_index
        # In-memory fallback: keyed by (agent_type, complexity_bucket)
        self._memory_pool: dict[tuple[str, float], list[PoolRecord]] = defaultdict(list)

    @staticmethod
    def _bucket_complexity(score: float) -> float:
        """Bucket complexity score to 0.1 granularity for privacy."""
        return round(min(max(score, 0.0), 1.0) * 10) / 10

    async def conditional_add(
        self,
        org_id: str,
        org_observation_count: int,
        record: PoolRecord,
    ) -> bool:
        """Add to global pool only if org exceeds privacy threshold.

        Args:
            org_id: Used only for threshold check, NOT stored.
            org_observation_count: Total observations for this org.
            record: Anonymized observation data.

        Returns:
            True if added, False if rejected (below threshold).
        """
        if org_observation_count < PRIVACY_THRESHOLD:
            logger.debug(
                "Model C: org below privacy threshold (%d < %d), skipping",
                org_observation_count, PRIVACY_THRESHOLD,
            )
            return False

        key = (record.agent_type, record.complexity_bucket)

        if self._index is not None:
            # Production: upsert to Pinecone
            try:
                from app.services.fingerprint_embedder import embed_fingerprint
                import uuid as uuid_module

                # Embed the fingerprint as a vector
                vector = await embed_fingerprint(
                    agent_type=record.agent_type,
                    complexity_bucket=record.complexity_bucket,
                    output_type=record.output_type,
                    model_used=record.model_used,
                    hallucination_detected=record.hallucination_detected,
                    cache_hit=record.cache_hit,
                    latency_ms=record.latency_ms,
                )

                if vector is None:
                    logger.warning("Model C: failed to embed fingerprint, skipping upsert")
                    return False

                # Upsert to Pinecone with anonymized metadata
                vector_id = f"{record.agent_type}-{record.complexity_bucket:.1f}-{uuid_module.uuid4()}"
                self._index.upsert(vectors=[{
                    "id": vector_id,
                    "values": vector,
                    "metadata": {
                        "agent_type": record.agent_type,
                        "complexity": record.complexity_bucket,
                        "output_type": record.output_type,
                        "model": record.model_used,
                        "hallucination": record.hallucination_detected,
                        "cache_hit": record.cache_hit,
                        "latency_ms": record.latency_ms or 0,
                    }
                }])

                logger.debug(
                    "Model C: upserted vector %s to Pinecone",
                    vector_id[:16],
                )

            except Exception:
                logger.exception("Model C: Pinecone upsert failed")
                return False
        else:
            # In-memory fallback
            self._memory_pool[key].append(record)

        logger.debug(
            "Model C: added record type=%s bucket=%.1f",
            record.agent_type, record.complexity_bucket,
        )
        return True

    async def query_risk_prior(
        self,
        agent_type: str,
        complexity_bucket: float,
    ) -> RiskPrior:
        """Query the global pool for a risk prior.

        Returns aggregated hallucination rate, recommended model, and confidence.
        """
        bucket = self._bucket_complexity(complexity_bucket)

        if self._index is not None:
            # Production: query Pinecone
            try:
                from app.services.fingerprint_embedder import embed_fingerprint_query

                # Embed the query
                query_vector = await embed_fingerprint_query(agent_type, bucket)
                if query_vector is None:
                    logger.warning("Model C: failed to embed query, falling back to in-memory")
                else:
                    # Query Pinecone for similar fingerprints
                    results = self._index.query(
                        vector=query_vector,
                        top_k=100,
                        include_metadata=True,
                    )

                    if results and results.get("matches"):
                        matches = results["matches"]
                        logger.debug(
                            "Model C: found %d similar fingerprints for type=%s bucket=%.1f",
                            len(matches), agent_type, bucket,
                        )

                        # Aggregate statistics from matches
                        hallucination_count = sum(
                            1 for m in matches
                            if m.get("metadata", {}).get("hallucination", False)
                        )
                        risk_score = hallucination_count / len(matches) if matches else 0.5

                        # Find best performing model
                        model_stats: dict[str, dict] = {}
                        for m in matches:
                            meta = m.get("metadata", {})
                            model = meta.get("model", "unknown")
                            hallucinated = meta.get("hallucination", False)

                            stats = model_stats.setdefault(model, {"total": 0, "hallucinations": 0})
                            stats["total"] += 1
                            if hallucinated:
                                stats["hallucinations"] += 1

                        recommended = None
                        best_rate = 1.0
                        for model, stats in model_stats.items():
                            rate = stats["hallucinations"] / stats["total"] if stats["total"] > 0 else 1.0
                            if rate < best_rate and stats["total"] >= 3:
                                best_rate = rate
                                recommended = model

                        confidence = min(1.0, len(matches) / 100)

                        return RiskPrior(
                            risk_score=round(risk_score, 4),
                            observation_count=len(matches),
                            confidence=round(confidence, 4),
                            recommended_model=recommended,
                        )

            except Exception:
                logger.exception("Model C: Pinecone query failed, falling back to in-memory")

        # In-memory fallback
        key = (agent_type, bucket)
        records = self._memory_pool.get(key, [])

        if not records:
            # Check nearby buckets as fallback
            for delta in [0.1, -0.1, 0.2, -0.2]:
                nearby_key = (agent_type, round(bucket + delta, 1))
                if nearby_key in self._memory_pool:
                    records = self._memory_pool[nearby_key]
                    break

        if not records:
            return RiskPrior(
                risk_score=0.5,  # neutral prior
                observation_count=0,
                confidence=0.0,
                recommended_model=None,
            )

        # Aggregate
        hallucination_count = sum(1 for r in records if r.hallucination_detected)
        risk_score = hallucination_count / len(records)

        # Find most successful model (lowest hallucination rate)
        model_stats: dict[str, dict] = {}
        for r in records:
            stats = model_stats.setdefault(r.model_used, {"total": 0, "hallucinations": 0})
            stats["total"] += 1
            if r.hallucination_detected:
                stats["hallucinations"] += 1

        recommended = None
        best_rate = 1.0
        for model, stats in model_stats.items():
            rate = stats["hallucinations"] / stats["total"] if stats["total"] > 0 else 1.0
            if rate < best_rate and stats["total"] >= 3:
                best_rate = rate
                recommended = model

        confidence = min(1.0, len(records) / 100)

        return RiskPrior(
            risk_score=round(risk_score, 4),
            observation_count=len(records),
            confidence=round(confidence, 4),
            recommended_model=recommended,
        )

    async def cold_start_initializer(
        self,
        agent_id: str,
        agent_type: Optional[str] = None,
    ) -> dict:
        """Bootstrap fingerprint defaults from global pool for new agents.

        Args:
            agent_id: The agent to bootstrap (for logging).
            agent_type: Optional agent type to query specific priors.

        Returns:
            Dict of suggested fingerprint defaults.
        """
        search_type = agent_type or "CHATBOT"

        # Query across complexity buckets for this agent type
        all_records: list[PoolRecord] = []
        for bucket in [round(i * 0.1, 1) for i in range(11)]:
            key = (search_type, bucket)
            all_records.extend(self._memory_pool.get(key, []))

        if not all_records:
            logger.debug("Model C: no data for cold start of agent %s type=%s", agent_id, search_type)
            return {
                "avg_complexity": 0.5,
                "hallucination_rate": 0.0,
                "cache_hit_rate": 0.0,
                "baseline_confidence": 0.1,
                "bootstrap_source": None,
            }

        # Aggregate defaults from global pool
        avg_complexity = sum(r.complexity_bucket for r in all_records) / len(all_records)
        hallucination_rate = sum(1 for r in all_records if r.hallucination_detected) / len(all_records)
        cache_hit_rate = sum(1 for r in all_records if r.cache_hit) / len(all_records)
        confidence = min(0.5, len(all_records) / 200)  # Capped at 0.5 for cold start

        logger.info(
            "Model C: cold start for agent %s from %d global records",
            agent_id, len(all_records),
        )

        return {
            "avg_complexity": round(avg_complexity, 4),
            "hallucination_rate": round(hallucination_rate, 4),
            "cache_hit_rate": round(cache_hit_rate, 4),
            "baseline_confidence": round(confidence, 4),
            "bootstrap_source": "model_c",
        }
