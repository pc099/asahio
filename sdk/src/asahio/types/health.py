"""Health check types for the ASAHIO Python SDK."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ProviderHealth:
    """Health status of a provider."""

    provider: str
    status: str
    last_checked: Optional[str]
    error: Optional[str]

    @classmethod
    def from_dict(cls, data: dict) -> "ProviderHealth":
        return cls(
            provider=data["provider"],
            status=data["status"],
            last_checked=data.get("last_checked"),
            error=data.get("error"),
        )


@dataclass
class HealthStatus:
    """Overall health status."""

    status: str
    version: Optional[str]
    components: dict

    @classmethod
    def from_dict(cls, data: dict) -> "HealthStatus":
        return cls(
            status=data["status"],
            version=data.get("version"),
            components=data.get("components") or {},
        )
