"""Tests for the ABA Anomaly Detector service."""

from dataclasses import dataclass, field

import pytest

from app.services.aba_anomaly_detector import ABAAnomalyDetector


@dataclass
class FakeFingerprint:
    """Minimal fingerprint for testing anomaly detection."""

    total_observations: int = 50
    hallucination_rate: float = 0.05
    avg_complexity: float = 0.5
    cache_hit_rate: float = 0.4
    model_distribution: dict = field(default_factory=lambda: {"gpt-4o": 50, "claude-sonnet-4-5": 50})
    baseline_confidence: float = 0.8


class TestHallucinationSpike:
    def test_no_anomaly_below_baseline(self) -> None:
        detector = ABAAnomalyDetector()
        fp = FakeFingerprint(hallucination_rate=0.05)
        anomalies = detector.detect_anomalies(fp)
        halluc = [a for a in anomalies if a.anomaly_type == "hallucination_spike"]
        assert len(halluc) == 0

    def test_low_severity_spike(self) -> None:
        detector = ABAAnomalyDetector()
        fp = FakeFingerprint(hallucination_rate=0.15)
        anomalies = detector.detect_anomalies(fp)
        halluc = [a for a in anomalies if a.anomaly_type == "hallucination_spike"]
        assert len(halluc) == 1
        assert halluc[0].severity == "low"

    def test_high_severity_spike(self) -> None:
        detector = ABAAnomalyDetector()
        fp = FakeFingerprint(hallucination_rate=0.5)
        anomalies = detector.detect_anomalies(fp)
        halluc = [a for a in anomalies if a.anomaly_type == "hallucination_spike"]
        assert len(halluc) == 1
        assert halluc[0].severity == "high"


class TestComplexityShift:
    def test_no_anomaly_at_baseline(self) -> None:
        detector = ABAAnomalyDetector()
        fp = FakeFingerprint(avg_complexity=0.5)
        anomalies = detector.detect_anomalies(fp)
        complexity = [a for a in anomalies if a.anomaly_type == "complexity_shift"]
        assert len(complexity) == 0

    def test_high_complexity_shift(self) -> None:
        detector = ABAAnomalyDetector()
        fp = FakeFingerprint(avg_complexity=0.95)
        anomalies = detector.detect_anomalies(fp)
        complexity = [a for a in anomalies if a.anomaly_type == "complexity_shift"]
        assert len(complexity) == 1
        assert complexity[0].severity in ("medium", "high")


class TestModelDrift:
    def test_no_drift_balanced_distribution(self) -> None:
        detector = ABAAnomalyDetector()
        fp = FakeFingerprint(model_distribution={"gpt-4o": 50, "claude-sonnet-4-5": 50})
        anomalies = detector.detect_anomalies(fp)
        drift = [a for a in anomalies if a.anomaly_type == "model_drift"]
        assert len(drift) == 0

    def test_drift_when_single_model_dominates(self) -> None:
        detector = ABAAnomalyDetector()
        fp = FakeFingerprint(model_distribution={"gpt-4o": 95, "claude-sonnet-4-5": 5})
        anomalies = detector.detect_anomalies(fp)
        drift = [a for a in anomalies if a.anomaly_type == "model_drift"]
        assert len(drift) == 1

    def test_no_drift_single_model(self) -> None:
        """Single-model distribution is expected, not anomalous."""
        detector = ABAAnomalyDetector()
        fp = FakeFingerprint(model_distribution={"gpt-4o": 100})
        anomalies = detector.detect_anomalies(fp)
        drift = [a for a in anomalies if a.anomaly_type == "model_drift"]
        assert len(drift) == 0


class TestCacheDegradation:
    def test_no_anomaly_healthy_cache(self) -> None:
        detector = ABAAnomalyDetector()
        fp = FakeFingerprint(cache_hit_rate=0.4)
        anomalies = detector.detect_anomalies(fp)
        cache = [a for a in anomalies if a.anomaly_type == "cache_degradation"]
        assert len(cache) == 0

    def test_cache_degradation_detected(self) -> None:
        detector = ABAAnomalyDetector()
        fp = FakeFingerprint(cache_hit_rate=0.05)
        anomalies = detector.detect_anomalies(fp)
        cache = [a for a in anomalies if a.anomaly_type == "cache_degradation"]
        assert len(cache) == 1
        assert cache[0].severity in ("medium", "high")


class TestMinObservations:
    def test_skips_below_min_observations(self) -> None:
        detector = ABAAnomalyDetector()
        fp = FakeFingerprint(total_observations=5, hallucination_rate=0.9)
        anomalies = detector.detect_anomalies(fp)
        assert len(anomalies) == 0
