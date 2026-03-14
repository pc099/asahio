"""Tests for the structural record extractor service."""

import pytest

from app.db.models import AgentTypeClassification, OutputTypeClassification
from app.services.structural_extractor import StructuralExtractor


@pytest.fixture
def extractor() -> StructuralExtractor:
    return StructuralExtractor()


# ── Query Complexity Score ──────────────────────────────────────────────


class TestQueryComplexityScore:
    def test_simple_query_low_score(self, extractor: StructuralExtractor) -> None:
        messages = [{"content": "What is Python?"}]
        result = extractor.query_complexity_score(messages)
        assert result.score < 0.4

    def test_complex_query_high_score(self, extractor: StructuralExtractor) -> None:
        messages = [{"content": (
            "First, analyze the distributed microservice architecture for latency optimization. "
            "Then, design an asynchronous pipeline with containerized orchestration. "
            "Next, implement the gradient-based optimization algorithm. "
            "Finally, deploy the infrastructure using kubernetes with proper middleware serialization."
        )}]
        result = extractor.query_complexity_score(messages)
        assert result.score > 0.5
        assert any("domain_terms" in s for s in result.signals)
        assert any("multi_step" in s for s in result.signals)

    def test_code_presence_boosts_score(self, extractor: StructuralExtractor) -> None:
        messages = [{"content": "```python\ndef hello():\n    return 'world'\n```\nExplain this function."}]
        result = extractor.query_complexity_score(messages)
        assert any("code_presence" in s for s in result.signals)

    def test_multi_step_indicators(self, extractor: StructuralExtractor) -> None:
        messages = [{"content": "First do X, then do Y, finally check Z."}]
        result = extractor.query_complexity_score(messages)
        assert any("multi_step" in s for s in result.signals)

    def test_empty_input(self, extractor: StructuralExtractor) -> None:
        result = extractor.query_complexity_score([])
        assert result.score == 0.0
        result2 = extractor.query_complexity_score([{"content": ""}])
        assert result2.score == 0.0

    def test_score_clamped_to_one(self, extractor: StructuralExtractor) -> None:
        # Even extremely complex queries should not exceed 1.0
        messages = [{"content": " ".join(["algorithm infrastructure optimization pipeline"] * 50)}]
        result = extractor.query_complexity_score(messages)
        assert result.score <= 1.0


# ── Agent Type Classification ───────────────────────────────────────────


class TestClassifyAgentType:
    def test_chatbot_detection(self, extractor: StructuralExtractor) -> None:
        history = [
            {"prompt": "Hi there, how are you?", "response": "I'm doing well, thanks!"},
            {"prompt": "Please help me understand something", "response": "Sure, I'd be happy to help."},
            {"prompt": "Thanks for your help", "response": "You're welcome!"},
        ]
        result = extractor.classify_agent_type(history)
        assert result.classification == AgentTypeClassification.CHATBOT

    def test_rag_detection(self, extractor: StructuralExtractor) -> None:
        history = [
            {"prompt": "Find relevant documents", "response": "Retrieved from source: document A. Citation [1]."},
            {"prompt": "Summarize the context", "response": "Based on the retrieved reference material..."},
            {"prompt": "What does the document say?", "response": "The source document states..."},
        ]
        result = extractor.classify_agent_type(history)
        assert result.classification == AgentTypeClassification.RAG

    def test_coding_detection(self, extractor: StructuralExtractor) -> None:
        history = [
            {"prompt": "Write a function", "response": "```python\ndef foo(): pass\n```"},
            {"prompt": "Add error handling", "response": "```python\ndef foo():\n  try: pass\n  except: pass\n```"},
            {"prompt": "Create a class", "response": "class MyClass:\n  def __init__(self): pass"},
        ]
        result = extractor.classify_agent_type(history)
        assert result.classification == AgentTypeClassification.CODING

    def test_workflow_detection(self, extractor: StructuralExtractor) -> None:
        history = [
            {"prompt": "Process the data", "response": "Done", "tool_calls": ["read_file"]},
            {"prompt": "Transform the output", "response": "Transformed", "tool_calls": ["write_file"]},
            {"prompt": "Validate results", "response": "Valid", "tool_calls": ["validate"]},
        ]
        result = extractor.classify_agent_type(history)
        assert result.classification in (AgentTypeClassification.WORKFLOW, AgentTypeClassification.AUTONOMOUS)

    def test_autonomous_detection(self, extractor: StructuralExtractor) -> None:
        history = [
            {"prompt": "Plan the deployment", "response": "Planning: goal: deploy v2. Subtask 1...",
             "tool_calls": ["plan", "search", "execute"]},
            {"prompt": "Execute the plan", "response": "Decomposing into subtasks...",
             "tool_calls": ["shell", "git", "deploy", "verify"]},
        ]
        result = extractor.classify_agent_type(history)
        assert result.classification == AgentTypeClassification.AUTONOMOUS

    def test_empty_history(self, extractor: StructuralExtractor) -> None:
        result = extractor.classify_agent_type([])
        assert result.classification == AgentTypeClassification.CHATBOT
        assert result.confidence < 0.3


# ── Output Type Classification ──────────────────────────────────────────


class TestClassifyOutputType:
    def test_factual_detection(self, extractor: StructuralExtractor) -> None:
        response = (
            "Python was created in 1991 by Guido van Rossum [1]. "
            "As of 2024, it has over 300,000 packages on PyPI. "
            "The language achieved 28.11% market share in the TIOBE index (et al 2024)."
        )
        result = extractor.classify_output_type(response)
        assert result.classification == OutputTypeClassification.FACTUAL

    def test_creative_detection(self, extractor: StructuralExtractor) -> None:
        response = (
            "Once upon a time, in a world where code could speak, "
            "imagine a journey through the silicon forest. "
            "Picture this: every function tells a story."
        )
        result = extractor.classify_output_type(response)
        assert result.classification == OutputTypeClassification.CREATIVE

    def test_code_detection(self, extractor: StructuralExtractor) -> None:
        response = "Here's the solution:\n```python\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n```"
        result = extractor.classify_output_type(response)
        assert result.classification == OutputTypeClassification.CODE

    def test_structured_detection(self, extractor: StructuralExtractor) -> None:
        response = '{"name": "test", "value": 42, "nested": {"key": "value"}}'
        result = extractor.classify_output_type(response)
        assert result.classification == OutputTypeClassification.STRUCTURED

    def test_conversational_detection(self, extractor: StructuralExtractor) -> None:
        response = "Sure, I can help you with that! I think you should try the other approach. You can also use my suggestion."
        result = extractor.classify_output_type(response)
        assert result.classification == OutputTypeClassification.CONVERSATIONAL

    def test_empty_response(self, extractor: StructuralExtractor) -> None:
        result = extractor.classify_output_type("")
        assert result.classification == OutputTypeClassification.CONVERSATIONAL
        assert result.confidence < 0.5
