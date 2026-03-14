"""ABA Anomaly Detector — detects behavioral deviations from agent baselines.

Compares current fingerprint metrics against historical baselines to detect:
- hallucination_spike: hallucination rate exceeds baseline significantly
- complexity_shift: avg_complexity shifted >30% from baseline
- model_drift: model_distribution entropy changed (dominant model shifted)
- cache_degradation: cache_hit_rate dropped significantly
"""

import logging
import math
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# Severity thresholds — deviation percentages
THRESHOLDS = {
    "hallucination_spike": {"low": 0.3, "medium": 0.6, "high": 1.0},
    "complexity_shift": {"low": 0.3, "medium": 0.5, "high": 0.8},
    "model_drift": {"low": 0.3, "medium": 0.5, "high": 0.8},
    "cache_degradation": {"low": 0.2, "medium": 0.4, "high": 0.6},
}

# Minimum observations before anomalies are reliable
MIN_OBSERVATIONS = 10


@dataclass
class AnomalySignal:
    """A single detected anomaly."""

    anomaly_type: str
    severity: str  # low, medium, high
    current_value: float
    baseline_value: float
    deviation_pct: float


class ABAAnomalyDetector:
    """Detects behavioral anomalies by comparing fingerprints to baselines."""

    def __init__(
        self,
        thresholds: Optional[dict] = None,
        min_observations: int = MIN_OBSERVATIONS,
    ) -> None:
        self._thresholds = thresholds or THRESHOLDS
        self._min_observations = min_observations

    def detect_anomalies(self, fingerprint) -> list[AnomalySignal]:
        """Detect anomalies in a fingerprint.

        Args:
            fingerprint: An AgentFingerprint ORM object (or any object with
                total_observations, hallucination_rate, avg_complexity,
                cache_hit_rate, model_distribution, baseline_confidence).

        Returns:
            List of detected anomaly signals.
        """
        if fingerprint.total_observations < self._min_observations:
            return []

        anomalies: list[AnomalySignal] = []

        # Check hallucination spike
        h = self._check_hallucination_spike(fingerprint)
        if h:
            anomalies.append(h)

        # Check complexity shift
        c = self._check_complexity_shift(fingerprint)
        if c:
            anomalies.append(c)

        # Check model drift
        m = self._check_model_drift(fingerprint)
        if m:
            anomalies.append(m)

        # Check cache degradation
        d = self._check_cache_degradation(fingerprint)
        if d:
            anomalies.append(d)

        return anomalies

    def _check_hallucination_spike(self, fp) -> Optional[AnomalySignal]:
        """Detect hallucination rate exceeding safe baseline."""
        rate = fp.hallucination_rate
        # Baseline: low hallucination rate expected (<10%)
        baseline = 0.1
        if rate <= baseline:
            return None

        deviation = (rate - baseline) / max(baseline, 0.01)
        severity = self._classify_severity("hallucination_spike", deviation)
        if not severity:
            return None

        return AnomalySignal(
            anomaly_type="hallucination_spike",
            severity=severity,
            current_value=round(rate, 4),
            baseline_value=baseline,
            deviation_pct=round(deviation * 100, 1),
        )

    def _check_complexity_shift(self, fp) -> Optional[AnomalySignal]:
        """Detect avg_complexity shifting significantly from expected range."""
        current = fp.avg_complexity
        # Baseline: expected mid-range complexity (0.5)
        baseline = 0.5
        deviation = abs(current - baseline) / max(baseline, 0.01)

        severity = self._classify_severity("complexity_shift", deviation)
        if not severity:
            return None

        return AnomalySignal(
            anomaly_type="complexity_shift",
            severity=severity,
            current_value=round(current, 4),
            baseline_value=baseline,
            deviation_pct=round(deviation * 100, 1),
        )

    def _check_model_drift(self, fp) -> Optional[AnomalySignal]:
        """Detect model distribution becoming unexpectedly skewed."""
        distribution = fp.model_distribution or {}
        if not distribution:
            return None

        # Calculate normalized entropy
        total = sum(distribution.values())
        if total == 0:
            return None

        n_models = len(distribution)
        if n_models <= 1:
            return None  # Single model is expected, not anomalous

        # Shannon entropy, normalized to [0, 1]
        entropy = 0.0
        for count in distribution.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        max_entropy = math.log2(n_models)
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0

        # Baseline: expect moderate entropy (0.6 = balanced usage)
        baseline = 0.6
        # Low entropy = one model dominates = potential drift
        if normalized_entropy >= baseline:
            return None

        deviation = (baseline - normalized_entropy) / max(baseline, 0.01)
        severity = self._classify_severity("model_drift", deviation)
        if not severity:
            return None

        return AnomalySignal(
            anomaly_type="model_drift",
            severity=severity,
            current_value=round(normalized_entropy, 4),
            baseline_value=baseline,
            deviation_pct=round(deviation * 100, 1),
        )

    def _check_cache_degradation(self, fp) -> Optional[AnomalySignal]:
        """Detect cache hit rate dropping below expected level."""
        rate = fp.cache_hit_rate
        # Baseline: expect moderate cache usage (30%)
        baseline = 0.3
        if rate >= baseline:
            return None

        deviation = (baseline - rate) / max(baseline, 0.01)
        severity = self._classify_severity("cache_degradation", deviation)
        if not severity:
            return None

        return AnomalySignal(
            anomaly_type="cache_degradation",
            severity=severity,
            current_value=round(rate, 4),
            baseline_value=baseline,
            deviation_pct=round(deviation * 100, 1),
        )

    def _classify_severity(self, anomaly_type: str, deviation: float) -> Optional[str]:
        """Map deviation to severity level using configured thresholds."""
        thresholds = self._thresholds.get(anomaly_type, {})
        if deviation >= thresholds.get("high", float("inf")):
            return "high"
        elif deviation >= thresholds.get("medium", float("inf")):
            return "medium"
        elif deviation >= thresholds.get("low", float("inf")):
            return "low"
        return None
