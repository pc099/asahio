"""OpenAI-compatible chat completions mixin.

Shared by OpenAI, DeepSeek, Mistral, and Ollama — all of which expose
the ``POST /v1/chat/completions`` endpoint with the same request/response
schema.  Subclasses set ``_base_url`` and optionally override
``_default_headers``.
"""

import logging
import time
from typing import Optional

import httpx

from src.providers.base import (
    InferenceRequest,
    InferenceResponse,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderServerError,
)

logger = logging.getLogger(__name__)

_TIMEOUT = 60.0  # seconds


class OpenAICompatMixin:
    """Mixin for providers that speak the OpenAI chat completions protocol."""

    _base_url: str = ""

    # Subclasses may override
    provider_name: str  # provided by ProviderAdapter

    def _default_headers(self, api_key: str) -> dict[str, str]:
        """Return request headers.  Override for providers with custom auth."""
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _call_openai_compat(
        self,
        request: InferenceRequest,
        api_key: str,
        base_url: Optional[str] = None,
    ) -> InferenceResponse:
        """Execute a chat completion via the OpenAI-compatible protocol.

        Args:
            request: Provider-agnostic request DTO.
            api_key: Bearer token (or empty for Ollama).
            base_url: Override ``_base_url`` (used by Ollama per-instance).

        Returns:
            InferenceResponse with parsed token counts and latency.
        """
        url = f"{base_url or self._base_url}/chat/completions"
        headers = self._default_headers(api_key)

        messages: list[dict[str, str]] = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        body: dict = {
            "model": request.model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }

        start = time.time()
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.post(url, json=body, headers=headers)

        latency_ms = int((time.time() - start) * 1000)

        if resp.status_code == 429:
            raise ProviderRateLimitError(
                f"{self.provider_name} rate limited: {resp.text}"
            )
        if resp.status_code >= 500:
            raise ProviderServerError(
                f"{self.provider_name} server error: {resp.text}",
                status_code=resp.status_code,
            )
        if resp.status_code >= 400:
            raise ProviderRequestError(
                f"{self.provider_name} request error ({resp.status_code}): {resp.text}",
                status_code=resp.status_code,
            )

        data = resp.json()

        text = ""
        choices = data.get("choices", [])
        if choices:
            text = choices[0].get("message", {}).get("content", "") or ""

        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)

        return InferenceResponse(
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            model=request.model,
            provider=self.provider_name,
        )
