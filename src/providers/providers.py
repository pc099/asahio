"""Concrete LLM provider adapters.

Each class implements ``ProviderAdapter`` for one provider.  The adapters
are stateless — API keys come in per-call — so a single instance is safe
to share across threads.

Providers using the OpenAI chat completions protocol (OpenAI, DeepSeek,
Mistral, Ollama) delegate to ``OpenAICompatMixin``.  Anthropic and Google
have bespoke HTTP implementations via ``httpx``.
"""

import logging
import time
from typing import Optional

import httpx

from src.providers._openai_compat import OpenAICompatMixin
from src.providers.base import (
    InferenceRequest,
    InferenceResponse,
    ProviderAdapter,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderServerError,
)

logger = logging.getLogger(__name__)

_TIMEOUT = 60.0


# ── Helper ──────────────────────────────────────────────────────────────


def _raise_for_status(provider: str, resp: httpx.Response) -> None:
    """Raise typed exceptions for non-200 responses."""
    if resp.status_code == 429:
        raise ProviderRateLimitError(f"{provider} rate limited: {resp.text}")
    if resp.status_code >= 500:
        raise ProviderServerError(
            f"{provider} server error: {resp.text}",
            status_code=resp.status_code,
        )
    if resp.status_code >= 400:
        raise ProviderRequestError(
            f"{provider} request error ({resp.status_code}): {resp.text}",
            status_code=resp.status_code,
        )


# ── OpenAI ──────────────────────────────────────────────────────────────


class OpenAIProvider(OpenAICompatMixin, ProviderAdapter):
    """OpenAI chat completions (gpt-4o, o3, etc.)."""

    _base_url = "https://api.openai.com/v1"

    @property
    def provider_name(self) -> str:
        return "openai"

    def call(self, request: InferenceRequest, api_key: str) -> InferenceResponse:
        return self._call_openai_compat(request, api_key)

    def supports_model(self, model_id: str) -> bool:
        return model_id.startswith(("gpt-", "o1-", "o3-", "o3"))


# ── Anthropic ───────────────────────────────────────────────────────────


class AnthropicProvider(ProviderAdapter):
    """Anthropic Messages API (claude-opus, claude-sonnet, claude-haiku)."""

    _BASE_URL = "https://api.anthropic.com/v1/messages"
    _API_VERSION = "2023-06-01"

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def call(self, request: InferenceRequest, api_key: str) -> InferenceResponse:
        headers = {
            "x-api-key": api_key,
            "anthropic-version": self._API_VERSION,
            "Content-Type": "application/json",
        }

        body: dict = {
            "model": request.model,
            "max_tokens": request.max_tokens,
            "messages": [{"role": "user", "content": request.prompt}],
        }
        if request.system_prompt:
            body["system"] = request.system_prompt
        if request.temperature != 1.0:
            body["temperature"] = request.temperature

        start = time.time()
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.post(self._BASE_URL, json=body, headers=headers)
        latency_ms = int((time.time() - start) * 1000)

        _raise_for_status(self.provider_name, resp)

        data = resp.json()
        text = ""
        content = data.get("content", [])
        if content:
            text = content[0].get("text", "") or ""

        usage = data.get("usage", {})
        return InferenceResponse(
            text=text,
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            latency_ms=latency_ms,
            model=request.model,
            provider=self.provider_name,
        )

    def supports_model(self, model_id: str) -> bool:
        return model_id.startswith("claude-")


# ── Google Gemini ───────────────────────────────────────────────────────


class GoogleProvider(ProviderAdapter):
    """Google Gemini via the generativelanguage REST API (pure httpx)."""

    _BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    @property
    def provider_name(self) -> str:
        return "google"

    def call(self, request: InferenceRequest, api_key: str) -> InferenceResponse:
        url = (
            f"{self._BASE_URL}/models/{request.model}:generateContent"
            f"?key={api_key}"
        )

        contents: list[dict] = [
            {"role": "user", "parts": [{"text": request.prompt}]},
        ]

        body: dict = {"contents": contents}

        # System instruction is a top-level field, not in contents
        if request.system_prompt:
            body["systemInstruction"] = {
                "parts": [{"text": request.system_prompt}],
            }

        body["generationConfig"] = {
            "maxOutputTokens": request.max_tokens,
            "temperature": request.temperature,
        }

        start = time.time()
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.post(
                url,
                json=body,
                headers={"Content-Type": "application/json"},
            )
        latency_ms = int((time.time() - start) * 1000)

        _raise_for_status(self.provider_name, resp)

        data = resp.json()
        text = ""
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                text = parts[0].get("text", "") or ""

        usage = data.get("usageMetadata", {})
        return InferenceResponse(
            text=text,
            input_tokens=usage.get("promptTokenCount", 0),
            output_tokens=usage.get("candidatesTokenCount", 0),
            latency_ms=latency_ms,
            model=request.model,
            provider=self.provider_name,
        )

    def supports_model(self, model_id: str) -> bool:
        return model_id.startswith("gemini-")


# ── DeepSeek ────────────────────────────────────────────────────────────


class DeepSeekProvider(OpenAICompatMixin, ProviderAdapter):
    """DeepSeek via OpenAI-compatible endpoint."""

    _base_url = "https://api.deepseek.com/v1"

    @property
    def provider_name(self) -> str:
        return "deepseek"

    def call(self, request: InferenceRequest, api_key: str) -> InferenceResponse:
        return self._call_openai_compat(request, api_key)

    def supports_model(self, model_id: str) -> bool:
        return model_id.startswith("deepseek-")


# ── Mistral ─────────────────────────────────────────────────────────────


class MistralProvider(OpenAICompatMixin, ProviderAdapter):
    """Mistral AI via OpenAI-compatible endpoint."""

    _base_url = "https://api.mistral.ai/v1"

    @property
    def provider_name(self) -> str:
        return "mistral"

    def call(self, request: InferenceRequest, api_key: str) -> InferenceResponse:
        return self._call_openai_compat(request, api_key)

    def supports_model(self, model_id: str) -> bool:
        return model_id.startswith((
            "mistral-",
            "codestral-",
            "open-mistral",
            "open-mixtral",
            "pixtral-",
        ))


# ── Ollama (Self-Hosted) ───────────────────────────────────────────────


class OllamaProvider(OpenAICompatMixin, ProviderAdapter):
    """Ollama via its OpenAI-compatible /v1/chat/completions endpoint.

    Each instance is bound to a customer-provided ``base_url``.
    API key is unused (Ollama is local).  Cost is always $0.
    """

    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self._base_url = base_url.rstrip("/")
        self._registered_models: set[str] = set()

    @property
    def provider_name(self) -> str:
        return "ollama"

    def _default_headers(self, api_key: str) -> dict[str, str]:
        return {"Content-Type": "application/json"}

    def call(self, request: InferenceRequest, api_key: str) -> InferenceResponse:
        return self._call_openai_compat(
            request, api_key, base_url=f"{self._base_url}/v1"
        )

    def supports_model(self, model_id: str) -> bool:
        if self._registered_models:
            return model_id in self._registered_models
        return True  # Accept any model if no explicit list

    def register_models(self, models: list[str]) -> None:
        """Set the list of models available on this Ollama instance."""
        self._registered_models = set(models)

    def list_available_models(self) -> list[str]:
        """Query the Ollama instance for pulled models."""
        url = f"{self._base_url}/api/tags"
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url)
                resp.raise_for_status()
            data = resp.json()
            models = [m["name"] for m in data.get("models", [])]
            self._registered_models = set(models)
            return models
        except Exception as exc:
            logger.warning("Failed to list Ollama models at %s: %s", url, exc)
            return []
