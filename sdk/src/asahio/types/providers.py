"""Provider-related types (chains, keys, Ollama) for the ASAHIO Python SDK."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ChainSlot:
    """A slot in a GUIDED chain."""

    id: str
    chain_id: str
    provider: str
    model: str
    priority: int
    max_latency_ms: Optional[int]
    max_cost_per_1k_tokens: Optional[float]

    @classmethod
    def from_dict(cls, data: dict) -> "ChainSlot":
        return cls(
            id=data["id"],
            chain_id=data["chain_id"],
            provider=data["provider"],
            model=data["model"],
            priority=data["priority"],
            max_latency_ms=data.get("max_latency_ms"),
            max_cost_per_1k_tokens=data.get("max_cost_per_1k_tokens"),
        )


@dataclass
class Chain:
    """A GUIDED routing chain."""

    id: str
    organisation_id: str
    name: str
    fallback_triggers: list[str]
    is_default: bool
    is_active: bool
    slots: list[ChainSlot]
    created_at: str

    @classmethod
    def from_dict(cls, data: dict) -> "Chain":
        return cls(
            id=data["id"],
            organisation_id=data["organisation_id"],
            name=data["name"],
            fallback_triggers=data.get("fallback_triggers") or [],
            is_default=data.get("is_default", False),
            is_active=data.get("is_active", True),
            slots=[ChainSlot.from_dict(s) for s in data.get("slots", [])],
            created_at=data["created_at"],
        )


@dataclass
class ChainTestResult:
    """Result of testing a GUIDED chain."""

    chain_id: str
    selected_model: str
    selected_provider: str
    slot_priority: int
    test_status: str
    test_message: Optional[str]

    @classmethod
    def from_dict(cls, data: dict) -> "ChainTestResult":
        return cls(
            chain_id=data["chain_id"],
            selected_model=data["selected_model"],
            selected_provider=data["selected_provider"],
            slot_priority=data["slot_priority"],
            test_status=data["test_status"],
            test_message=data.get("test_message"),
        )


@dataclass
class ProviderKey:
    """A BYOK (Bring Your Own Key) provider key."""

    id: str
    organisation_id: str
    provider: str
    key_hint: str
    is_valid: bool
    created_at: str

    @classmethod
    def from_dict(cls, data: dict) -> "ProviderKey":
        return cls(
            id=data["id"],
            organisation_id=data["organisation_id"],
            provider=data["provider"],
            key_hint=data["key_hint"],
            is_valid=data.get("is_valid", True),
            created_at=data["created_at"],
        )


@dataclass
class OllamaConfig:
    """A self-hosted Ollama instance configuration."""

    id: str
    organisation_id: str
    name: str
    base_url: str
    is_verified: bool
    available_models: list[str]
    created_at: str

    @classmethod
    def from_dict(cls, data: dict) -> "OllamaConfig":
        return cls(
            id=data["id"],
            organisation_id=data["organisation_id"],
            name=data["name"],
            base_url=data["base_url"],
            is_verified=data.get("is_verified", False),
            available_models=data.get("available_models") or [],
            created_at=data["created_at"],
        )
