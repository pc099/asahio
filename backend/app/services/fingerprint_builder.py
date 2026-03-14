"""Fingerprint builder — O(1) EMA updater for agent behavioral fingerprints.

Updates running averages using Exponential Moving Average so each observation
is a constant-time operation that never requires recomputing from full history.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# Default EMA smoothing factor (effective window ~10 observations)
DEFAULT_ALPHA = 0.1

# Baseline confidence weights
_W_VOLUME = 0.3
_W_ACCURACY = 0.4
_W_CONSISTENCY = 0.3


@dataclass
class FingerprintUpdate:
    """Input for a single fingerprint observation."""

    agent_id: str
    org_id: str
    complexity_score: float
    context_length: int
    model_used: str
    cache_hit: bool
    hallucination_detected: bool
    call_trace_id: Optional[str] = None


class FingerprintBuilder:
    """Builds and maintains agent behavioral fingerprints via O(1) EMA updates."""

    def __init__(self, alpha: float = DEFAULT_ALPHA) -> None:
        self._alpha = alpha

    @property
    def alpha(self) -> float:
        return self._alpha

    def update_fingerprint(self, fingerprint, record: FingerprintUpdate):
        """Update a fingerprint ORM object with a new observation.

        Mutates the fingerprint in place. Caller is responsible for DB commit.

        Args:
            fingerprint: AgentFingerprint ORM object.
            record: FingerprintUpdate with the new observation data.

        Returns:
            The mutated fingerprint object.
        """
        alpha = self._alpha
        n = fingerprint.total_observations

        # 1. Increment observation count
        fingerprint.total_observations = n + 1

        # 2. EMA update avg_complexity
        fingerprint.avg_complexity = self._ema(
            float(fingerprint.avg_complexity), record.complexity_score, alpha, n,
        )

        # 3. EMA update avg_context_length
        fingerprint.avg_context_length = self._ema(
            float(fingerprint.avg_context_length), float(record.context_length), alpha, n,
        )

        # 4. EMA update hallucination_rate
        hallucination_value = 1.0 if record.hallucination_detected else 0.0
        fingerprint.hallucination_rate = self._ema(
            float(fingerprint.hallucination_rate), hallucination_value, alpha, n,
        )

        # 5. Update model_distribution JSONB counter
        dist = dict(fingerprint.model_distribution) if fingerprint.model_distribution else {}
        dist[record.model_used] = dist.get(record.model_used, 0) + 1
        fingerprint.model_distribution = dist

        # 6. EMA update cache_hit_rate
        cache_value = 1.0 if record.cache_hit else 0.0
        fingerprint.cache_hit_rate = self._ema(
            float(fingerprint.cache_hit_rate), cache_value, alpha, n,
        )

        # 7. Recalculate baseline_confidence
        fingerprint.baseline_confidence = self.calculate_baseline_confidence(fingerprint)

        # 8. Update timestamp
        fingerprint.last_updated_at = datetime.now(timezone.utc)

        return fingerprint

    def calculate_baseline_confidence(self, fingerprint) -> float:
        """Calculate baseline confidence from fingerprint state.

        Weighted combination of:
        - volume: observation count saturation (0.3)
        - accuracy: inverse hallucination rate (0.4)
        - consistency: model usage concentration (0.3)
        """
        n = fingerprint.total_observations

        # Volume: saturates at 100 observations
        volume = min(1.0, n / 100.0)

        # Accuracy: 1.0 - hallucination_rate
        accuracy = 1.0 - float(fingerprint.hallucination_rate)

        # Consistency: how concentrated is model usage (Herfindahl index)
        dist = fingerprint.model_distribution or {}
        total_calls = sum(dist.values()) if dist else 0
        if total_calls > 0:
            shares = [count / total_calls for count in dist.values()]
            hhi = sum(s * s for s in shares)  # 1.0 = single model, ~0 = many models
            consistency = hhi
        else:
            consistency = 0.0

        confidence = _W_VOLUME * volume + _W_ACCURACY * accuracy + _W_CONSISTENCY * consistency
        return round(min(1.0, max(0.0, confidence)), 4)

    @staticmethod
    def _ema(old_avg: float, new_value: float, alpha: float, n: int) -> float:
        """Compute exponential moving average.

        For the first observation (n=0), just use the new value directly.
        """
        if n == 0:
            return round(new_value, 4)
        result = alpha * new_value + (1 - alpha) * old_avg
        return round(result, 4)
