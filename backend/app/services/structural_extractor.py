"""Structural record extractor — classifies query complexity, agent type, and output type.

All functions are synchronous and target <5ms per call.
Uses precompiled regex heuristics (no ML dependencies).
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

from app.db.models import AgentTypeClassification, OutputTypeClassification

logger = logging.getLogger(__name__)


@dataclass
class ComplexityResult:
    """Result of query complexity scoring."""

    score: float  # 0.0–1.0
    signals: list[str] = field(default_factory=list)


@dataclass
class AgentTypeResult:
    """Result of agent type classification."""

    classification: AgentTypeClassification
    confidence: float
    signals: list[str] = field(default_factory=list)


@dataclass
class OutputTypeResult:
    """Result of output type classification."""

    classification: OutputTypeClassification
    confidence: float
    signals: list[str] = field(default_factory=list)


# ── Precompiled patterns ────────────────────────────────────────────────

# Complexity signals
_RE_CODE_BLOCK = re.compile(r"```")
_RE_CODE_KEYWORDS = re.compile(
    r"\b(def |class |import |function |const |let |var |return |async |await )\b"
)
_RE_MULTI_STEP = re.compile(
    r"\b(first|then|next|after that|step \d|finally|subsequently)\b", re.IGNORECASE
)
_RE_NESTED_CLAUSES = re.compile(r"[,;()\[\]{}]")
_RE_DOMAIN_TERMS = re.compile(
    r"\b(algorithm|architecture|infrastructure|kubernetes|microservice|"
    r"distributed|concurrent|asynchronous|latency|throughput|embedding|"
    r"transformer|gradient|backprop|neural|regression|optimization|"
    r"containeriz|orchestrat|pipeline|middleware|serializ)\w*\b",
    re.IGNORECASE,
)
_RE_QUESTION_MARKS = re.compile(r"\?")

# Agent type signals
_RE_TOOL_CALL = re.compile(r"\b(tool_call|function_call|action:|tool:|<tool>)\b", re.IGNORECASE)
_RE_RETRIEVAL = re.compile(
    r"\b(retrieved|source:|citation|reference|document|context:)\b", re.IGNORECASE
)
_RE_PLANNING = re.compile(
    r"\b(plan:|planning|goal:|objective|subtask|decompos)\b", re.IGNORECASE
)
_RE_CODING_OUTPUT = re.compile(r"(```\w+|def \w+|class \w+|function \w+|import \w+)")
_RE_CONVERSATIONAL_PATTERN = re.compile(
    r"\b(hi|hello|hey|thanks|thank you|please|sure|okay|yes|no)\b", re.IGNORECASE
)

# Output type signals
_RE_JSON_YAML = re.compile(r'(\{[\s\S]*"[\w]+"\s*:|^\s*[\w]+:\s)', re.MULTILINE)
_RE_TABLE_PATTERN = re.compile(r"\|[\s-]+\|")
_RE_CITATION = re.compile(r"\[\d+\]|\((?:et al|ibid|\d{4})\)")
_RE_NARRATIVE = re.compile(
    r"\b(once upon|imagine|picture this|in a world|metaphor|journey)\b", re.IGNORECASE
)
_RE_FIRST_SECOND_PERSON = re.compile(r"\b(I |you |we |my |your |our )\b")
_RE_NUMBERS_DATES = re.compile(r"\b\d{4}[-/]\d{2}|\b\d+\.\d+%|\b\d{1,3}(,\d{3})+\b")


class StructuralExtractor:
    """Classifies query complexity, agent type, and output type using regex heuristics."""

    def query_complexity_score(self, messages: list[dict]) -> ComplexityResult:
        """Score query complexity from 0.0 (trivial) to 1.0 (very complex).

        Args:
            messages: List of message dicts with 'content' key.

        Returns:
            ComplexityResult with score and debug signals.
        """
        text = " ".join(m.get("content", "") for m in messages if m.get("content"))
        if not text.strip():
            return ComplexityResult(score=0.0, signals=["empty_input"])

        signals: list[str] = []
        score = 0.0
        words = text.split()
        total_words = len(words)

        # Factor 1: Vocabulary diversity (unique / total)
        if total_words > 0:
            unique_ratio = len(set(w.lower() for w in words)) / total_words
            vocab_score = min(unique_ratio, 1.0) * 0.2
            score += vocab_score
            if unique_ratio > 0.7:
                signals.append(f"high_vocab_diversity:{unique_ratio:.2f}")

        # Factor 2: Nested clause depth (punctuation density)
        clause_count = len(_RE_NESTED_CLAUSES.findall(text))
        if total_words > 0:
            clause_density = clause_count / total_words
            clause_score = min(clause_density * 2, 1.0) * 0.15
            score += clause_score
            if clause_density > 0.15:
                signals.append(f"nested_clauses:{clause_count}")

        # Factor 3: Domain-specific terms
        domain_matches = _RE_DOMAIN_TERMS.findall(text)
        domain_score = min(len(domain_matches) / 5, 1.0) * 0.2
        score += domain_score
        if domain_matches:
            signals.append(f"domain_terms:{len(domain_matches)}")

        # Factor 4: Multi-step reasoning indicators
        step_matches = _RE_MULTI_STEP.findall(text)
        step_score = min(len(step_matches) / 3, 1.0) * 0.2
        score += step_score
        if step_matches:
            signals.append(f"multi_step:{len(step_matches)}")

        # Factor 5: Code presence
        code_blocks = len(_RE_CODE_BLOCK.findall(text))
        code_keywords = len(_RE_CODE_KEYWORDS.findall(text))
        code_score = min((code_blocks * 2 + code_keywords) / 5, 1.0) * 0.15
        score += code_score
        if code_blocks or code_keywords:
            signals.append(f"code_presence:blocks={code_blocks},keywords={code_keywords}")

        # Factor 6: Length bonus
        length_score = min(total_words / 200, 1.0) * 0.1
        score += length_score

        return ComplexityResult(
            score=round(min(score, 1.0), 4),
            signals=signals,
        )

    def classify_agent_type(
        self, agent_history: list[dict],
    ) -> AgentTypeResult:
        """Classify an agent's behavioral type from historical observations.

        Args:
            agent_history: List of observation dicts with optional keys:
                'prompt', 'response', 'tool_calls', 'output_type'.

        Returns:
            AgentTypeResult with classification, confidence, and signals.
        """
        if not agent_history:
            return AgentTypeResult(
                classification=AgentTypeClassification.CHATBOT,
                confidence=0.2,
                signals=["insufficient_history"],
            )

        signals: list[str] = []
        votes: dict[AgentTypeClassification, float] = {t: 0.0 for t in AgentTypeClassification}
        total = len(agent_history)

        for i, obs in enumerate(agent_history):
            # Recency weight: newer observations count more
            recency = 0.5 + 0.5 * (i / max(total - 1, 1))
            text = (obs.get("prompt", "") + " " + obs.get("response", "")).strip()

            if obs.get("tool_calls"):
                tool_count = len(obs["tool_calls"]) if isinstance(obs["tool_calls"], list) else 1
                if tool_count >= 3:
                    votes[AgentTypeClassification.AUTONOMOUS] += recency
                    signals.append("multi_tool_call")
                else:
                    votes[AgentTypeClassification.WORKFLOW] += recency
                    signals.append("tool_call")

            if _RE_RETRIEVAL.search(text):
                votes[AgentTypeClassification.RAG] += recency
                signals.append("retrieval_pattern")

            if _RE_CODING_OUTPUT.search(text):
                votes[AgentTypeClassification.CODING] += recency
                signals.append("coding_output")

            if _RE_PLANNING.search(text):
                votes[AgentTypeClassification.AUTONOMOUS] += recency * 0.5
                signals.append("planning_language")

            if _RE_CONVERSATIONAL_PATTERN.search(obs.get("prompt", "")):
                votes[AgentTypeClassification.CHATBOT] += recency * 0.5

            # Use pre-classified output_type if available
            otype = obs.get("output_type", "")
            if otype == "CODE":
                votes[AgentTypeClassification.CODING] += recency * 0.3
            elif otype == "STRUCTURED":
                votes[AgentTypeClassification.WORKFLOW] += recency * 0.3

        # Pick the winner
        best_type = max(votes, key=lambda k: votes[k])
        total_votes = sum(votes.values())
        confidence = votes[best_type] / total_votes if total_votes > 0 else 0.2

        # Boost confidence with more history
        confidence = min(1.0, confidence + min(total / 50, 0.3))

        return AgentTypeResult(
            classification=best_type,
            confidence=round(confidence, 4),
            signals=list(set(signals)),
        )

    def classify_output_type(self, response: str) -> OutputTypeResult:
        """Classify the structural type of a single LLM response.

        Args:
            response: The LLM response text.

        Returns:
            OutputTypeResult with classification, confidence, and signals.
        """
        if not response or not response.strip():
            return OutputTypeResult(
                classification=OutputTypeClassification.CONVERSATIONAL,
                confidence=0.3,
                signals=["empty_response"],
            )

        signals: list[str] = []
        votes: dict[OutputTypeClassification, float] = {t: 0.0 for t in OutputTypeClassification}

        # CODE: code blocks or programming keywords
        code_blocks = len(_RE_CODE_BLOCK.findall(response))
        code_keywords = len(_RE_CODE_KEYWORDS.findall(response))
        if code_blocks >= 1:
            votes[OutputTypeClassification.CODE] += 2.0
            signals.append(f"code_blocks:{code_blocks}")
        if code_keywords >= 2:
            votes[OutputTypeClassification.CODE] += 1.0
            signals.append(f"code_keywords:{code_keywords}")

        # STRUCTURED: JSON, YAML, tables, key-value pairs
        if _RE_JSON_YAML.search(response):
            votes[OutputTypeClassification.STRUCTURED] += 1.5
            signals.append("json_yaml_pattern")
        if _RE_TABLE_PATTERN.search(response):
            votes[OutputTypeClassification.STRUCTURED] += 1.5
            signals.append("table_pattern")

        # FACTUAL: citations, numbers, dates, declarative tone
        citations = len(_RE_CITATION.findall(response))
        numbers = len(_RE_NUMBERS_DATES.findall(response))
        if citations:
            votes[OutputTypeClassification.FACTUAL] += 1.5
            signals.append(f"citations:{citations}")
        if numbers >= 2:
            votes[OutputTypeClassification.FACTUAL] += 1.0
            signals.append(f"numbers_dates:{numbers}")

        # CREATIVE: narrative markers, metaphors
        if _RE_NARRATIVE.search(response):
            votes[OutputTypeClassification.CREATIVE] += 2.0
            signals.append("narrative_markers")

        # CONVERSATIONAL: first/second person, casual language
        person_refs = len(_RE_FIRST_SECOND_PERSON.findall(response))
        if person_refs >= 3:
            votes[OutputTypeClassification.CONVERSATIONAL] += 1.0
            signals.append(f"person_refs:{person_refs}")
        if _RE_CONVERSATIONAL_PATTERN.search(response):
            votes[OutputTypeClassification.CONVERSATIONAL] += 0.5
            signals.append("casual_language")

        # Pick winner
        best_type = max(votes, key=lambda k: votes[k])
        total_votes = sum(votes.values())

        if total_votes == 0:
            # Default to CONVERSATIONAL for ambiguous text
            return OutputTypeResult(
                classification=OutputTypeClassification.CONVERSATIONAL,
                confidence=0.4,
                signals=["no_strong_signals"],
            )

        confidence = votes[best_type] / total_votes
        confidence = min(1.0, confidence + 0.2)  # base confidence boost

        return OutputTypeResult(
            classification=best_type,
            confidence=round(confidence, 4),
            signals=signals,
        )
