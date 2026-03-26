"""Resource base classes and utilities for the ASAHIO Python SDK."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

from asahio._base_client import AsyncBaseClient, BaseClient

T = TypeVar("T")


class SyncResource:
    """Base for all sync resource namespaces."""

    def __init__(self, client: BaseClient) -> None:
        self._client = client


class AsyncResource:
    """Base for all async resource namespaces."""

    def __init__(self, client: AsyncBaseClient) -> None:
        self._client = client


@dataclass
class PaginatedList(Generic[T]):
    """Paginated list response."""

    data: list[T]
    total: int
    limit: int
    offset: int


def _strip_none(params: dict) -> dict:
    """Remove None values from query params."""
    return {k: v for k, v in params.items() if v is not None}
