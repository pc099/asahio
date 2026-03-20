"""Tests for the OpenAI-compatible mixin."""

from unittest.mock import MagicMock, patch

import pytest

from src.providers._openai_compat import OpenAICompatMixin
from src.providers.base import (
    InferenceRequest,
    InferenceResponse,
    ProviderAdapter,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderServerError,
)


# Minimal concrete class that uses the mixin
class _TestProvider(OpenAICompatMixin, ProviderAdapter):
    _base_url = "https://api.test.com/v1"

    @property
    def provider_name(self) -> str:
        return "test"

    def call(self, request: InferenceRequest, api_key: str) -> InferenceResponse:
        return self._call_openai_compat(request, api_key)

    def supports_model(self, model_id: str) -> bool:
        return model_id.startswith("test-")


def _mock_response(status_code: int = 200, json_data: dict | None = None):
    """Build a mock httpx.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = "error body"
    resp.json.return_value = json_data or {
        "choices": [{"message": {"content": "Hello back!"}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }
    return resp


class TestOpenAICompatMixin:
    def test_successful_call(self) -> None:
        provider = _TestProvider()
        req = InferenceRequest(model="test-v1", prompt="Hi")

        with patch("src.providers._openai_compat.httpx.Client") as MockClient:
            mock_client = MagicMock()
            mock_client.post.return_value = _mock_response()
            MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
            MockClient.return_value.__exit__ = MagicMock(return_value=False)

            result = provider.call(req, "sk-test-key")

        assert result.text == "Hello back!"
        assert result.input_tokens == 10
        assert result.output_tokens == 5
        assert result.provider == "test"
        assert result.model == "test-v1"

        # Verify the request body
        call_args = mock_client.post.call_args
        body = call_args.kwargs["json"]
        assert body["model"] == "test-v1"
        assert body["messages"] == [{"role": "user", "content": "Hi"}]
        assert body["max_tokens"] == 1024

    def test_system_prompt_inserted(self) -> None:
        provider = _TestProvider()
        req = InferenceRequest(
            model="test-v1", prompt="Hi", system_prompt="Be helpful."
        )

        with patch("src.providers._openai_compat.httpx.Client") as MockClient:
            mock_client = MagicMock()
            mock_client.post.return_value = _mock_response()
            MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
            MockClient.return_value.__exit__ = MagicMock(return_value=False)

            provider.call(req, "sk-key")

        body = mock_client.post.call_args.kwargs["json"]
        assert body["messages"][0] == {"role": "system", "content": "Be helpful."}
        assert body["messages"][1] == {"role": "user", "content": "Hi"}

    def test_auth_header(self) -> None:
        provider = _TestProvider()
        req = InferenceRequest(model="test-v1", prompt="Hi")

        with patch("src.providers._openai_compat.httpx.Client") as MockClient:
            mock_client = MagicMock()
            mock_client.post.return_value = _mock_response()
            MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
            MockClient.return_value.__exit__ = MagicMock(return_value=False)

            provider.call(req, "sk-my-key")

        headers = mock_client.post.call_args.kwargs["headers"]
        assert headers["Authorization"] == "Bearer sk-my-key"

    def test_rate_limit_error(self) -> None:
        provider = _TestProvider()
        req = InferenceRequest(model="test-v1", prompt="Hi")

        with patch("src.providers._openai_compat.httpx.Client") as MockClient:
            mock_client = MagicMock()
            mock_client.post.return_value = _mock_response(status_code=429)
            MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
            MockClient.return_value.__exit__ = MagicMock(return_value=False)

            with pytest.raises(ProviderRateLimitError):
                provider.call(req, "sk-key")

    def test_server_error(self) -> None:
        provider = _TestProvider()
        req = InferenceRequest(model="test-v1", prompt="Hi")

        with patch("src.providers._openai_compat.httpx.Client") as MockClient:
            mock_client = MagicMock()
            mock_client.post.return_value = _mock_response(status_code=503)
            MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
            MockClient.return_value.__exit__ = MagicMock(return_value=False)

            with pytest.raises(ProviderServerError) as exc_info:
                provider.call(req, "sk-key")
            assert exc_info.value.status_code == 503

    def test_request_error(self) -> None:
        provider = _TestProvider()
        req = InferenceRequest(model="test-v1", prompt="Hi")

        with patch("src.providers._openai_compat.httpx.Client") as MockClient:
            mock_client = MagicMock()
            mock_client.post.return_value = _mock_response(status_code=401)
            MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
            MockClient.return_value.__exit__ = MagicMock(return_value=False)

            with pytest.raises(ProviderRequestError) as exc_info:
                provider.call(req, "bad-key")
            assert exc_info.value.status_code == 401

    def test_base_url_override(self) -> None:
        """Ollama uses a custom base_url passed per-call."""

        class OllamaLike(OpenAICompatMixin, ProviderAdapter):
            _base_url = ""

            @property
            def provider_name(self) -> str:
                return "ollama"

            def call(self, request, api_key):
                return self._call_openai_compat(
                    request, api_key, base_url="http://localhost:11434/v1"
                )

            def supports_model(self, model_id):
                return True

        provider = OllamaLike()
        req = InferenceRequest(model="llama3", prompt="Hi")

        with patch("src.providers._openai_compat.httpx.Client") as MockClient:
            mock_client = MagicMock()
            mock_client.post.return_value = _mock_response()
            MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
            MockClient.return_value.__exit__ = MagicMock(return_value=False)

            result = provider.call(req, "")

        url_called = mock_client.post.call_args.args[0]
        assert url_called == "http://localhost:11434/v1/chat/completions"
        assert result.provider == "ollama"
