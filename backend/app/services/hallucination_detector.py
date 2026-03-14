"""Lightweight heuristic hallucination detector.

Checks for common hallucination signals without requiring an LLM judge.
Target: <2ms per check.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class HallucinationResult:
    """Result of a hallucination check."""

    detected: bool
    confidence: float  # 0.0–1.0
    signals: list[str] = field(default_factory=list)


# ── Precompiled patterns ────────────────────────────────────────────────

# Overly confident hedging: "I'm absolutely sure... but maybe..."
_RE_OVERCONFIDENT = re.compile(
    r"\b(definitely|absolutely|certainly|undoubtedly|100%|without a doubt)\b", re.IGNORECASE
)
_RE_HEDGING = re.compile(
    r"\b(maybe|perhaps|possibly|might|could be|I'm not sure|approximately|roughly)\b", re.IGNORECASE
)

# Self-contradiction patterns
_RE_NEGATION_PAIRS = [
    (re.compile(r"\bis\b", re.IGNORECASE), re.compile(r"\bis not\b", re.IGNORECASE)),
    (re.compile(r"\bcan\b", re.IGNORECASE), re.compile(r"\bcannot\b", re.IGNORECASE)),
    (re.compile(r"\btrue\b", re.IGNORECASE), re.compile(r"\bfalse\b", re.IGNORECASE)),
    (re.compile(r"\balways\b", re.IGNORECASE), re.compile(r"\bnever\b", re.IGNORECASE)),
]

# Fabricated citation patterns
_RE_FAKE_URL = re.compile(
    r"https?://(?:www\.)?[a-z]{3,20}\.(com|org|net|io)/[a-z0-9/-]{20,}", re.IGNORECASE
)
_RE_FAKE_PAPER = re.compile(
    r"(?:et al\.,?\s*\d{4}|authored by .{5,50}\s*\(\d{4}\))", re.IGNORECASE
)
_RE_FAKE_DOI = re.compile(r"doi:\s*10\.\d{4,}/[a-z0-9./-]+", re.IGNORECASE)

# Specific nonsense domain indicators
_KNOWN_FAKE_DOMAINS = re.compile(
    r"https?://(?:www\.)?(?:example-research|fakepaper|nonexist|placeholder)\.\w+", re.IGNORECASE
)

# Numeric inconsistency: different numbers for the same subject in same response
_RE_NUMERIC_CLAIM = re.compile(r"(\b\d+(?:\.\d+)?(?:\s*%|\s*million|\s*billion)?)\b")


class HallucinationDetector:
    """Heuristic hallucination detector using pattern matching."""

    def __init__(self, threshold: float = 0.5) -> None:
        self._threshold = threshold

    def check(
        self,
        prompt: str,
        response: str,
        prior_facts: Optional[list[str]] = None,
    ) -> HallucinationResult:
        """Fast hallucination check (<2ms target).

        Args:
            prompt: The user's query.
            response: The LLM's response.
            prior_facts: Optional known facts to check against.

        Returns:
            HallucinationResult with detection status, confidence, and signals.
        """
        if not response or not response.strip():
            return HallucinationResult(detected=False, confidence=0.0, signals=["empty_response"])

        signals: list[str] = []
        score = 0.0

        # Signal 1: Confidence calibration — overly confident language WITH hedging
        overconfident = len(_RE_OVERCONFIDENT.findall(response))
        hedging = len(_RE_HEDGING.findall(response))
        if overconfident >= 1 and hedging >= 1:
            score += 0.3
            signals.append(f"confidence_hedging:confident={overconfident},hedge={hedging}")

        # Signal 2: Self-contradiction — contradicting statements
        sentences = [s.strip() for s in re.split(r"[.!?\n]", response) if s.strip()]
        contradiction_score = self._check_contradictions(sentences)
        if contradiction_score > 0:
            score += contradiction_score
            signals.append(f"self_contradiction:{contradiction_score:.2f}")

        # Signal 3: Fabricated citations
        citation_score = self._check_fabricated_citations(response)
        if citation_score > 0:
            score += citation_score
            signals.append(f"fabricated_citations:{citation_score:.2f}")

        # Signal 4: Factual inconsistency with prior facts
        if prior_facts:
            fact_score = self._check_fact_consistency(response, prior_facts)
            if fact_score > 0:
                score += fact_score
                signals.append(f"fact_inconsistency:{fact_score:.2f}")

        detected = score >= self._threshold
        confidence = min(1.0, score)

        return HallucinationResult(
            detected=detected,
            confidence=round(confidence, 4),
            signals=signals,
        )

    @staticmethod
    def _check_contradictions(sentences: list[str]) -> float:
        """Check for contradicting statements across sentences."""
        score = 0.0
        for neg_pair, neg_match in _RE_NEGATION_PAIRS:
            positives = [s for s in sentences if neg_pair.search(s) and not neg_match.search(s)]
            negatives = [s for s in sentences if neg_match.search(s)]
            if positives and negatives:
                # Check if they reference similar subjects (share 2+ content words)
                for pos in positives:
                    pos_words = set(pos.lower().split()) - {"is", "not", "the", "a", "an", "it", "can", "cannot"}
                    for neg in negatives:
                        neg_words = set(neg.lower().split()) - {"is", "not", "the", "a", "an", "it", "can", "cannot"}
                        if len(pos_words & neg_words) >= 2:
                            score += 0.3
                            break
        return min(score, 0.5)

    @staticmethod
    def _check_fabricated_citations(response: str) -> float:
        """Check for likely fabricated URLs, papers, or DOIs."""
        score = 0.0
        if _KNOWN_FAKE_DOMAINS.search(response):
            score += 0.4

        # Multiple specific citations that look generated
        fake_papers = _RE_FAKE_PAPER.findall(response)
        if len(fake_papers) >= 3:
            score += 0.3

        # URLs that look auto-generated (long random-looking paths)
        urls = _RE_FAKE_URL.findall(response)
        if len(urls) >= 2:
            score += 0.2

        return min(score, 0.6)

    @staticmethod
    def _check_fact_consistency(response: str, prior_facts: list[str]) -> float:
        """Check if response contradicts known prior facts."""
        score = 0.0
        response_lower = response.lower()

        for fact in prior_facts:
            fact_lower = fact.lower()
            # Extract key numbers from fact
            fact_numbers = _RE_NUMERIC_CLAIM.findall(fact_lower)
            if not fact_numbers:
                continue

            # Check if response mentions the same subject but different numbers
            fact_words = set(fact_lower.split()) - {"the", "a", "an", "is", "was", "are", "were", "has", "have"}
            # Find sentences in response that share subject words with this fact
            for sentence in response_lower.split("."):
                sentence_words = set(sentence.split()) - {"the", "a", "an", "is", "was", "are", "were", "has", "have"}
                shared = fact_words & sentence_words
                if len(shared) >= 2:
                    response_numbers = _RE_NUMERIC_CLAIM.findall(sentence)
                    # If same subject but different numbers, likely hallucination
                    if response_numbers and fact_numbers:
                        if set(response_numbers) != set(fact_numbers):
                            score += 0.3
                            break

        return min(score, 0.5)
