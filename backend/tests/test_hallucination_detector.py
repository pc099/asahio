"""Tests for the hallucination detector service."""

import pytest

from app.services.hallucination_detector import HallucinationDetector


@pytest.fixture
def detector() -> HallucinationDetector:
    return HallucinationDetector()


class TestHallucinationDetector:
    def test_clean_response_no_hallucination(self, detector: HallucinationDetector) -> None:
        result = detector.check(
            prompt="What is Python?",
            response="Python is a programming language created by Guido van Rossum.",
        )
        assert result.detected is False
        assert result.confidence < 0.5

    def test_confidence_hedging_detected(self, detector: HallucinationDetector) -> None:
        result = detector.check(
            prompt="What year was Python created?",
            response="Python was absolutely definitely created in 1991, but maybe it could be 1989, perhaps earlier.",
        )
        assert any("confidence_hedging" in s for s in result.signals)

    def test_self_contradiction_detected(self, detector: HallucinationDetector) -> None:
        result = detector.check(
            prompt="Can Python do X?",
            response="Python can handle concurrent tasks efficiently. However, Python cannot handle concurrent tasks due to the GIL.",
        )
        assert any("self_contradiction" in s for s in result.signals)

    def test_fabricated_urls_detected(self, detector: HallucinationDetector) -> None:
        result = detector.check(
            prompt="Give me references",
            response="See https://www.example-research.org/papers/deep-learning-survey-2024 for more details.",
        )
        assert any("fabricated_citations" in s for s in result.signals)

    def test_fact_inconsistency_with_prior(self, detector: HallucinationDetector) -> None:
        result = detector.check(
            prompt="How many packages does Python have?",
            response="Python has 500,000 packages on PyPI.",
            prior_facts=["Python has 300,000 packages on PyPI."],
        )
        assert any("fact_inconsistency" in s for s in result.signals)

    def test_empty_response(self, detector: HallucinationDetector) -> None:
        result = detector.check(prompt="Hello", response="")
        assert result.detected is False
        assert "empty_response" in result.signals

    def test_no_prior_facts_skips_check(self, detector: HallucinationDetector) -> None:
        result = detector.check(
            prompt="What is 2+2?",
            response="2+2 is 4.",
            prior_facts=None,
        )
        assert result.detected is False
        assert not any("fact_inconsistency" in s for s in result.signals)

    def test_multiple_signals_increase_confidence(self, detector: HallucinationDetector) -> None:
        result = detector.check(
            prompt="Tell me about quantum computing",
            response=(
                "Quantum computing is definitely absolutely the future. "
                "It can solve all problems. It cannot solve all problems. "
                "Perhaps maybe it is limited. "
                "See https://www.example-research.org/quantum-computing-breakthrough-2024"
            ),
        )
        assert result.detected is True
        assert result.confidence > 0.5
        assert len(result.signals) >= 2
