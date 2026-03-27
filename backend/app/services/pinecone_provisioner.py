"""Pinecone index provisioning and lifecycle management.

Handles creation and configuration of:
- Per-org semantic cache indexes: asahio-cache-{org_id}
- Master Model C index: asahio-model-c (cross-org behavioral patterns)
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def ensure_model_c_index_exists() -> bool:
    """Ensure the master Model C index exists. Idempotent — safe to call on every startup.

    Returns:
        True if index exists or was created, False if creation failed.
    """
    try:
        from app.config import get_settings

        settings = get_settings()
        if not settings.pinecone_api_key:
            logger.warning("Pinecone API key not set — Model C index check skipped")
            return False

        from pinecone import Pinecone, ServerlessSpec

        pc = Pinecone(api_key=settings.pinecone_api_key)
        index_name = "asahio-model-c"

        # Check if index already exists
        existing_indexes = pc.list_indexes()
        index_names = [idx["name"] for idx in existing_indexes]

        if index_name in index_names:
            logger.info("Model C index '%s' already exists", index_name)
            return True

        # Create new index
        logger.info("Creating Model C index '%s'...", index_name)
        pc.create_index(
            name=index_name,
            dimension=1024,  # Cohere embed-english-v3.0
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region=settings.pinecone_environment or "us-east-1",
            ),
        )
        logger.info("Model C index '%s' created successfully", index_name)
        return True

    except Exception as e:
        logger.exception("Failed to ensure Model C index exists: %s", e)
        return False


async def provision_org_cache_index(org_id: str) -> Optional[str]:
    """Provision a dedicated semantic cache index for an organisation.

    Args:
        org_id: Organisation UUID as string.

    Returns:
        Index name if successful, None if provisioning failed.
    """
    try:
        from app.config import get_settings

        settings = get_settings()
        if not settings.pinecone_api_key:
            logger.warning("Pinecone API key not set — cannot provision org index")
            return None

        from pinecone import Pinecone, ServerlessSpec

        pc = Pinecone(api_key=settings.pinecone_api_key)
        index_name = f"asahio-cache-{org_id}"

        # Check if index already exists
        existing_indexes = pc.list_indexes()
        index_names = [idx["name"] for idx in existing_indexes]

        if index_name in index_names:
            logger.info("Org cache index '%s' already exists", index_name)
            return index_name

        # Create new index
        logger.info("Provisioning cache index '%s' for org %s...", index_name, org_id)
        pc.create_index(
            name=index_name,
            dimension=1024,  # Cohere embed-english-v3.0
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region=settings.pinecone_environment or "us-east-1",
            ),
        )
        logger.info("Org cache index '%s' created successfully", index_name)
        return index_name

    except Exception as e:
        logger.exception("Failed to provision org cache index for %s: %s", org_id, e)
        return None


async def delete_org_cache_index(org_id: str, index_name: Optional[str] = None) -> bool:
    """Delete an org's cache index (e.g., on org deletion or cleanup).

    Args:
        org_id: Organisation UUID as string.
        index_name: Explicit index name, or will use default naming.

    Returns:
        True if deleted or already absent, False if deletion failed.
    """
    try:
        from app.config import get_settings

        settings = get_settings()
        if not settings.pinecone_api_key:
            logger.warning("Pinecone API key not set — cannot delete org index")
            return False

        from pinecone import Pinecone

        pc = Pinecone(api_key=settings.pinecone_api_key)
        target_index = index_name or f"asahio-cache-{org_id}"

        # Check if index exists
        existing_indexes = pc.list_indexes()
        index_names = [idx["name"] for idx in existing_indexes]

        if target_index not in index_names:
            logger.info("Org cache index '%s' does not exist (already deleted)", target_index)
            return True

        # Delete index
        logger.info("Deleting org cache index '%s'...", target_index)
        pc.delete_index(target_index)
        logger.info("Org cache index '%s' deleted successfully", target_index)
        return True

    except Exception as e:
        logger.exception("Failed to delete org cache index '%s': %s", target_index, e)
        return False


def get_model_c_index():
    """Get the master Model C Pinecone index connection.

    Returns None if Pinecone is not configured or index doesn't exist.
    Lazy singleton pattern — caches the connection.
    """
    global _model_c_index
    if _model_c_index is _UNAVAILABLE:
        return None
    if _model_c_index is not None:
        return _model_c_index

    try:
        from app.config import get_settings

        settings = get_settings()
        if not settings.pinecone_api_key:
            logger.debug("Pinecone API key not set — Model C disabled")
            _model_c_index = _UNAVAILABLE
            return None

        from pinecone import Pinecone

        pc = Pinecone(api_key=settings.pinecone_api_key)
        index_name = "asahio-model-c"

        # Connect to index
        idx = pc.Index(index_name)
        logger.info("Connected to Model C index: %s", index_name)

        _model_c_index = idx
        return _model_c_index

    except Exception as e:
        logger.warning("Could not connect to Model C index: %s", e)
        _model_c_index = _UNAVAILABLE
        return None


def reset_model_c_index() -> None:
    """Clear cached Model C index connection. Used in tests."""
    global _model_c_index
    _model_c_index = None


# Module-level singleton for Model C index connection
_model_c_index = None
_UNAVAILABLE = "UNAVAILABLE"  # sentinel: init attempted and failed
