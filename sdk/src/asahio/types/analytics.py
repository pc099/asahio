"""Analytics types for the ASAHIO Python SDK."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Overview:
    """Analytics overview KPIs."""

    total_requests: int
    total_cost: float
    total_savings: float
    avg_latency_ms: float
    cache_hit_rate: float

    @classmethod
    def from_dict(cls, data: dict) -> "Overview":
        return cls(
            total_requests=data["total_requests"],
            total_cost=data["total_cost"],
            total_savings=data["total_savings"],
            avg_latency_ms=data["avg_latency_ms"],
            cache_hit_rate=data["cache_hit_rate"],
        )


@dataclass
class SavingsEntry:
    """Time-series savings entry."""

    timestamp: str
    cost_without_asahi: float
    cost_with_asahi: float
    savings_usd: float
    requests: int

    @classmethod
    def from_dict(cls, data: dict) -> "SavingsEntry":
        return cls(
            timestamp=data["timestamp"],
            cost_without_asahi=data["cost_without_asahi"],
            cost_with_asahi=data["cost_with_asahi"],
            savings_usd=data["savings_usd"],
            requests=data["requests"],
        )


@dataclass
class ModelBreakdown:
    """Model usage breakdown."""

    model: str
    requests: int
    total_cost: float
    total_savings: float

    @classmethod
    def from_dict(cls, data: dict) -> "ModelBreakdown":
        return cls(
            model=data["model"],
            requests=data["requests"],
            total_cost=data["total_cost"],
            total_savings=data["total_savings"],
        )


@dataclass
class CachePerformance:
    """Cache performance metrics."""

    total_requests: int
    cache_hit_rate: float
    tiers: dict

    @classmethod
    def from_dict(cls, data: dict) -> "CachePerformance":
        return cls(
            total_requests=data["total_requests"],
            cache_hit_rate=data["cache_hit_rate"],
            tiers=data.get("tiers") or {},
        )
