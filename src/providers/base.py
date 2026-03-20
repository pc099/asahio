"""Provider abstraction layer — base classes and DTOs.

Every LLM provider (OpenAI, Anthropic, Google, DeepSeek, Mistral, Ollama)
implements the ``ProviderAdapter`` interface.  The adapters are stateless:
API keys are passed per-call so a single adapter instance can be shared
across threads safely.

All ``call()`` methods are **synchronous** because the legacy optimizer
runs inside ``run_in_executor`` on a thread pool.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from src.exceptions import AsahiException


# ── Exceptions ──────────────────────────────────────────────────────────


class BillingException(AsahiException):
    """No API key available and insufficient billing credits."""


class ProviderRequestError(AsahiException):
    """Provider returned a non-retryable error (4xx except 429)."""

    def __init__(self, message: str, status_code: int = 0) -> None:
        super().__init__(message)
        self.status_code = status_code


class ProviderRateLimitError(AsahiException):
    """Provider returned HTTP 429 — rate limited."""


class ProviderServerError(AsahiException):
    """Provider returned HTTP 5xx."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.status_code = status_code


# ── DTOs ────────────────────────────────────────────────────────────────


@dataclass
class InferenceRequest:
    """Provider-agnostic inference request."""

    model: str
    prompt: str
    max_tokens: int = 1024
    temperature: float = 1.0
    system_prompt: Optional[str] = None


@dataclass
class InferenceResponse:
    """Provider-agnostic inference response."""

    text: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    model: str
    provider: str


# ── Abstract Base ───────────────────────────────────────────────────────


class ProviderAdapter(ABC):
    """Abstract base for all LLM provider adapters."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Canonical provider identifier (e.g. ``'openai'``, ``'google'``)."""

    @abstractmethod
    def call(self, request: InferenceRequest, api_key: str) -> InferenceResponse:
        """Execute inference synchronously.

        Args:
            request: Provider-agnostic request DTO.
            api_key: API key (or dummy string for Ollama).

        Returns:
            Provider-agnostic response DTO.

        Raises:
            ProviderRateLimitError: HTTP 429.
            ProviderServerError: HTTP 5xx.
            ProviderRequestError: Other non-retryable errors.
        """

    @abstractmethod
    def supports_model(self, model_id: str) -> bool:
        """Return True if this adapter handles the given model ID."""
