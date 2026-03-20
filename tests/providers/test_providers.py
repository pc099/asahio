"""Tests for all six concrete provider adapters."""

from unittest.mock import MagicMock, patch

import pytest

from src.providers.base import (
    InferenceRequest,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderServerError,
)
from src.providers.providers import (
    AnthropicProvider,
    DeepSeekProvider,
    GoogleProvider,
    MistralProvider,
    OllamaProvider,
    OpenAIProvider,
)


# ── Helpers ─────────────────────────────────────────────────────────────


def _mock_httpx_response(status_code: int = 200, json_data: dict | None = None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = "error body"
    resp.json.return_value = json_data or {}
    return resp


def _patch_httpx():
    """Return a context-manager that patches httpx.Client for OpenAI-compat."""
    return patch("src.providers._openai_compat.httpx.Client")


def _patch_httpx_providers():
    """Return a context-manager that patches httpx.Client in providers module."""
    return patch("src.providers.providers.httpx.Client")


def _setup_mock_client(MockClient, response):
    """Wire up the mock context manager."""
    mock_client = MagicMock()
    mock_client.post.return_value = response
    mock_client.get.return_value = response
    MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
    MockClient.return_value.__exit__ = MagicMock(return_value=False)
    return mock_client


# ── OpenAI ──────────────────────────────────────────────────────────────


class TestOpenAIProvider:
    def test_provider_name(self) -> None:
        assert OpenAIProvider().provider_name == "openai"

    def test_supports_model(self) -> None:
        p = OpenAIProvider()
        assert p.supports_model("gpt-4o")
        assert p.supports_model("gpt-4o-mini")
        assert p.supports_model("o3")
        assert not p.supports_model("claude-sonnet-4-6")
        assert not p.supports_model("gemini-2.5-pro")

    def test_call_success(self) -> None:
        p = OpenAIProvider()
        req = InferenceRequest(model="gpt-4o", prompt="Hello")

        with _patch_httpx() as MockClient:
            mock_client = _setup_mock_client(
                MockClient,
                _mock_httpx_response(200, {
                    "choices": [{"message": {"content": "Hi there!"}}],
                    "usage": {"prompt_tokens": 5, "completion_tokens": 3},
                }),
            )
            result = p.call(req, "sk-test")

        assert result.text == "Hi there!"
        assert result.input_tokens == 5
        assert result.output_tokens == 3
        assert result.provider == "openai"

        url = mock_client.post.call_args.args[0]
        assert url == "https://api.openai.com/v1/chat/completions"


# ── Anthropic ───────────────────────────────────────────────────────────


class TestAnthropicProvider:
    def test_provider_name(self) -> None:
        assert AnthropicProvider().provider_name == "anthropic"

    def test_supports_model(self) -> None:
        p = AnthropicProvider()
        assert p.supports_model("claude-opus-4-6")
        assert p.supports_model("claude-haiku-4-5")
        assert not p.supports_model("gpt-4o")

    def test_call_success(self) -> None:
        p = AnthropicProvider()
        req = InferenceRequest(model="claude-sonnet-4-6", prompt="Hi")

        with _patch_httpx_providers() as MockClient:
            mock_client = _setup_mock_client(
                MockClient,
                _mock_httpx_response(200, {
                    "content": [{"text": "Hello!"}],
                    "usage": {"input_tokens": 8, "output_tokens": 4},
                }),
            )
            result = p.call(req, "sk-ant-test")

        assert result.text == "Hello!"
        assert result.input_tokens == 8
        assert result.output_tokens == 4
        assert result.provider == "anthropic"

        headers = mock_client.post.call_args.kwargs["headers"]
        assert headers["x-api-key"] == "sk-ant-test"
        assert headers["anthropic-version"] == "2023-06-01"

    def test_system_prompt(self) -> None:
        p = AnthropicProvider()
        req = InferenceRequest(
            model="claude-sonnet-4-6", prompt="Hi", system_prompt="Be concise."
        )

        with _patch_httpx_providers() as MockClient:
            _setup_mock_client(
                MockClient,
                _mock_httpx_response(200, {
                    "content": [{"text": "ok"}],
                    "usage": {"input_tokens": 10, "output_tokens": 1},
                }),
            )
            mock_client = MockClient.return_value.__enter__()
            p.call(req, "key")

        body = mock_client.post.call_args.kwargs["json"]
        assert body["system"] == "Be concise."

    def test_rate_limit(self) -> None:
        p = AnthropicProvider()
        req = InferenceRequest(model="claude-sonnet-4-6", prompt="Hi")

        with _patch_httpx_providers() as MockClient:
            _setup_mock_client(MockClient, _mock_httpx_response(429))
            with pytest.raises(ProviderRateLimitError):
                p.call(req, "key")


# ── Google ──────────────────────────────────────────────────────────────


class TestGoogleProvider:
    def test_provider_name(self) -> None:
        assert GoogleProvider().provider_name == "google"

    def test_supports_model(self) -> None:
        p = GoogleProvider()
        assert p.supports_model("gemini-2.5-pro")
        assert p.supports_model("gemini-2.0-flash")
        assert not p.supports_model("gpt-4o")

    def test_call_success(self) -> None:
        p = GoogleProvider()
        req = InferenceRequest(model="gemini-2.5-pro", prompt="Hello")

        with _patch_httpx_providers() as MockClient:
            mock_client = _setup_mock_client(
                MockClient,
                _mock_httpx_response(200, {
                    "candidates": [
                        {"content": {"parts": [{"text": "Hi from Gemini!"}]}}
                    ],
                    "usageMetadata": {
                        "promptTokenCount": 6,
                        "candidatesTokenCount": 4,
                    },
                }),
            )
            result = p.call(req, "AIza-test")

        assert result.text == "Hi from Gemini!"
        assert result.input_tokens == 6
        assert result.output_tokens == 4
        assert result.provider == "google"

        # Verify URL has model and api key
        url = mock_client.post.call_args.args[0]
        assert "gemini-2.5-pro:generateContent" in url
        assert "key=AIza-test" in url

    def test_system_instruction(self) -> None:
        p = GoogleProvider()
        req = InferenceRequest(
            model="gemini-2.5-pro", prompt="Hi", system_prompt="Be brief."
        )

        with _patch_httpx_providers() as MockClient:
            mock_client = _setup_mock_client(
                MockClient,
                _mock_httpx_response(200, {
                    "candidates": [{"content": {"parts": [{"text": "ok"}]}}],
                    "usageMetadata": {"promptTokenCount": 5, "candidatesTokenCount": 1},
                }),
            )
            p.call(req, "key")

        body = mock_client.post.call_args.kwargs["json"]
        assert body["systemInstruction"]["parts"][0]["text"] == "Be brief."

    def test_server_error(self) -> None:
        p = GoogleProvider()
        req = InferenceRequest(model="gemini-2.5-pro", prompt="Hi")

        with _patch_httpx_providers() as MockClient:
            _setup_mock_client(MockClient, _mock_httpx_response(500))
            with pytest.raises(ProviderServerError):
                p.call(req, "key")


# ── DeepSeek ────────────────────────────────────────────────────────────


class TestDeepSeekProvider:
    def test_provider_name(self) -> None:
        assert DeepSeekProvider().provider_name == "deepseek"

    def test_supports_model(self) -> None:
        p = DeepSeekProvider()
        assert p.supports_model("deepseek-chat")
        assert p.supports_model("deepseek-reasoner")
        assert not p.supports_model("gpt-4o")

    def test_call_success(self) -> None:
        p = DeepSeekProvider()
        req = InferenceRequest(model="deepseek-chat", prompt="Hello")

        with _patch_httpx() as MockClient:
            mock_client = _setup_mock_client(
                MockClient,
                _mock_httpx_response(200, {
                    "choices": [{"message": {"content": "Hi from DeepSeek!"}}],
                    "usage": {"prompt_tokens": 4, "completion_tokens": 5},
                }),
            )
            result = p.call(req, "ds-key")

        assert result.text == "Hi from DeepSeek!"
        assert result.provider == "deepseek"

        url = mock_client.post.call_args.args[0]
        assert url == "https://api.deepseek.com/v1/chat/completions"


# ── Mistral ─────────────────────────────────────────────────────────────


class TestMistralProvider:
    def test_provider_name(self) -> None:
        assert MistralProvider().provider_name == "mistral"

    def test_supports_model(self) -> None:
        p = MistralProvider()
        assert p.supports_model("mistral-large-latest")
        assert p.supports_model("codestral-latest")
        assert p.supports_model("open-mixtral-8x7b")
        assert not p.supports_model("gpt-4o")

    def test_call_success(self) -> None:
        p = MistralProvider()
        req = InferenceRequest(model="mistral-large-latest", prompt="Hello")

        with _patch_httpx() as MockClient:
            mock_client = _setup_mock_client(
                MockClient,
                _mock_httpx_response(200, {
                    "choices": [{"message": {"content": "Bonjour!"}}],
                    "usage": {"prompt_tokens": 3, "completion_tokens": 2},
                }),
            )
            result = p.call(req, "ms-key")

        assert result.text == "Bonjour!"
        assert result.provider == "mistral"

        url = mock_client.post.call_args.args[0]
        assert url == "https://api.mistral.ai/v1/chat/completions"


# ── Ollama ──────────────────────────────────────────────────────────────


class TestOllamaProvider:
    def test_provider_name(self) -> None:
        assert OllamaProvider().provider_name == "ollama"

    def test_supports_model_any_when_no_list(self) -> None:
        p = OllamaProvider()
        assert p.supports_model("llama3")
        assert p.supports_model("anything")

    def test_supports_model_with_registered_list(self) -> None:
        p = OllamaProvider()
        p.register_models(["llama3", "codellama"])
        assert p.supports_model("llama3")
        assert p.supports_model("codellama")
        assert not p.supports_model("mistral-7b")

    def test_call_success(self) -> None:
        p = OllamaProvider(base_url="http://my-server:11434")
        req = InferenceRequest(model="llama3", prompt="Hello")

        with _patch_httpx() as MockClient:
            mock_client = _setup_mock_client(
                MockClient,
                _mock_httpx_response(200, {
                    "choices": [{"message": {"content": "Hi from Ollama!"}}],
                    "usage": {"prompt_tokens": 4, "completion_tokens": 4},
                }),
            )
            result = p.call(req, "")

        assert result.text == "Hi from Ollama!"
        assert result.provider == "ollama"

        url = mock_client.post.call_args.args[0]
        assert url == "http://my-server:11434/v1/chat/completions"

        # No auth header for Ollama
        headers = mock_client.post.call_args.kwargs["headers"]
        assert "Authorization" not in headers

    def test_list_available_models(self) -> None:
        p = OllamaProvider(base_url="http://localhost:11434")

        with _patch_httpx_providers() as MockClient:
            mock_resp = _mock_httpx_response(200, {
                "models": [
                    {"name": "llama3:latest"},
                    {"name": "codellama:latest"},
                ],
            })
            mock_resp.raise_for_status = MagicMock()
            mock_client = _setup_mock_client(MockClient, mock_resp)
            mock_client.get.return_value = mock_resp

            models = p.list_available_models()

        assert models == ["llama3:latest", "codellama:latest"]
        assert p.supports_model("llama3:latest")
        assert not p.supports_model("unknown")
