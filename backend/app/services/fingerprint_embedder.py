"""Fingerprint embedding for Model C behavioral pattern storage.

Converts structured PoolRecord observations into vector embeddings for
similarity search in Pinecone. Enables cross-org behavioral learning
while maintaining privacy through anonymization.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def fingerprint_to_text(
    agent_type: str,
    complexity_bucket: float,
    output_type: str,
    model_used: str,
    hallucination_detected: bool,
    cache_hit: bool,
    latency_ms: Optional[int] = None,
) -> str:
    """Convert a fingerprint record to a text representation for embedding.

    The text captures the behavioral signature in a format that produces
    meaningful semantic vectors for similarity search.

    Args:
        agent_type: Agent classification (CHATBOT, ANALYST, CODER, etc.)
        complexity_bucket: Bucketed complexity score (0.0-1.0, 0.1 granularity)
        output_type: Output classification (TEXT, CODE, DATA, etc.)
        model_used: Model identifier used for this observation
        hallucination_detected: Whether hallucination was detected
        cache_hit: Whether this was served from cache
        latency_ms: Optional latency in milliseconds

    Returns:
        Text representation suitable for embedding.

    Example:
        >>> fingerprint_to_text("CHATBOT", 0.5, "TEXT", "gpt-4", False, True)
        'Agent: CHATBOT | Complexity: medium (0.5) | Output: TEXT | Model: gpt-4 | Quality: accurate | Cache: hit'
    """
    # Map complexity to semantic labels
    if complexity_bucket <= 0.2:
        complexity_label = "trivial"
    elif complexity_bucket <= 0.4:
        complexity_label = "simple"
    elif complexity_bucket <= 0.6:
        complexity_label = "medium"
    elif complexity_bucket <= 0.8:
        complexity_label = "complex"
    else:
        complexity_label = "very complex"

    # Quality assessment
    quality = "hallucinated" if hallucination_detected else "accurate"

    # Cache status
    cache_status = "hit" if cache_hit else "miss"

    # Latency tier (optional)
    latency_text = ""
    if latency_ms is not None:
        if latency_ms < 500:
            latency_text = " | Latency: fast"
        elif latency_ms < 2000:
            latency_text = " | Latency: normal"
        else:
            latency_text = " | Latency: slow"

    return (
        f"Agent: {agent_type} | "
        f"Complexity: {complexity_label} ({complexity_bucket:.1f}) | "
        f"Output: {output_type} | "
        f"Model: {model_used} | "
        f"Quality: {quality} | "
        f"Cache: {cache_status}"
        f"{latency_text}"
    )


async def embed_fingerprint(
    agent_type: str,
    complexity_bucket: float,
    output_type: str,
    model_used: str,
    hallucination_detected: bool,
    cache_hit: bool,
    latency_ms: Optional[int] = None,
) -> Optional[list[float]]:
    """Embed a fingerprint record as a vector for Pinecone storage.

    Args:
        See fingerprint_to_text() for parameter descriptions.

    Returns:
        1024-dim vector if successful, None if embedding failed.
    """
    try:
        from app.services.embeddings import embed

        text = fingerprint_to_text(
            agent_type=agent_type,
            complexity_bucket=complexity_bucket,
            output_type=output_type,
            model_used=model_used,
            hallucination_detected=hallucination_detected,
            cache_hit=cache_hit,
            latency_ms=latency_ms,
        )

        vector = await embed(text)
        return vector.tolist() if hasattr(vector, "tolist") else list(vector)

    except Exception as e:
        logger.exception("Failed to embed fingerprint: %s", e)
        return None


async def embed_fingerprint_query(agent_type: str, complexity_bucket: float) -> Optional[list[float]]:
    """Embed a query for finding similar behavioral patterns.

    Simpler than full fingerprint — just agent type and complexity for lookup.

    Args:
        agent_type: Agent classification to search for.
        complexity_bucket: Complexity level to search around.

    Returns:
        1024-dim query vector if successful, None if embedding failed.
    """
    try:
        from app.services.embeddings import embed

        # Map complexity for query
        if complexity_bucket <= 0.2:
            complexity_label = "trivial"
        elif complexity_bucket <= 0.4:
            complexity_label = "simple"
        elif complexity_bucket <= 0.6:
            complexity_label = "medium"
        elif complexity_bucket <= 0.8:
            complexity_label = "complex"
        else:
            complexity_label = "very complex"

        query_text = f"Agent: {agent_type} | Complexity: {complexity_label} ({complexity_bucket:.1f})"

        vector = await embed(query_text)
        return vector.tolist() if hasattr(vector, "tolist") else list(vector)

    except Exception as e:
        logger.exception("Failed to embed fingerprint query: %s", e)
        return None
