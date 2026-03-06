"""Public ASAHIO SDK clients."""

from __future__ import annotations

import os
from typing import Any, Optional, Union, overload

from asahio._base_client import AsyncBaseClient, BaseClient
from asahio._exceptions import AsahioError
from asahio._streaming import AsyncStream, Stream
from asahio.types.chat import ChatCompletion

_DEFAULT_BASE_URL = "https://api.asahio.dev"


def _resolve_api_key(api_key: Optional[str]) -> str:
    resolved = (
        api_key
        or os.environ.get("ASAHIO_API_KEY")
        or os.environ.get("ASAHI_API_KEY")
        or os.environ.get("ACORN_API_KEY")
    )
    if not resolved:
        raise AsahioError(
            "No API key provided. Pass api_key= or set ASAHIO_API_KEY."
        )
    return resolved


def _build_body(
    *,
    messages: list[dict[str, str]],
    model: str,
    stream: bool,
    routing_mode: str,
    intervention_mode: str,
    quality_preference: str,
    latency_preference: str,
    agent_id: Optional[str],
    session_id: Optional[str],
    model_endpoint_id: Optional[str],
    extra: dict[str, Any],
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": stream,
        "routing_mode": routing_mode,
        "intervention_mode": intervention_mode,
        "quality_preference": quality_preference,
        "latency_preference": latency_preference,
        **extra,
    }
    if agent_id is not None:
        body["agent_id"] = agent_id
    if session_id is not None:
        body["session_id"] = session_id
    if model_endpoint_id is not None:
        body["model_endpoint_id"] = model_endpoint_id
    return body


class Completions:
    def __init__(self, client: BaseClient) -> None:
        self._client = client

    @overload
    def create(
        self,
        *,
        messages: list[dict[str, str]],
        model: str = "gpt-4o",
        stream: None = None,
        routing_mode: str = "AUTO",
        intervention_mode: str = "OBSERVE",
        quality_preference: str = "high",
        latency_preference: str = "normal",
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        model_endpoint_id: Optional[str] = None,
        **kwargs: Any,
    ) -> ChatCompletion: ...

    @overload
    def create(
        self,
        *,
        messages: list[dict[str, str]],
        model: str = "gpt-4o",
        stream: bool = ...,
        routing_mode: str = "AUTO",
        intervention_mode: str = "OBSERVE",
        quality_preference: str = "high",
        latency_preference: str = "normal",
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        model_endpoint_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletion, Stream]: ...

    def create(
        self,
        *,
        messages: list[dict[str, str]],
        model: str = "gpt-4o",
        stream: Optional[bool] = None,
        routing_mode: str = "AUTO",
        intervention_mode: str = "OBSERVE",
        quality_preference: str = "high",
        latency_preference: str = "normal",
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        model_endpoint_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletion, Stream]:
        body = _build_body(
            messages=messages,
            model=model,
            stream=bool(stream),
            routing_mode=routing_mode,
            intervention_mode=intervention_mode,
            quality_preference=quality_preference,
            latency_preference=latency_preference,
            agent_id=agent_id,
            session_id=session_id,
            model_endpoint_id=model_endpoint_id,
            extra=kwargs,
        )
        if stream:
            response = self._client.post_stream("/v1/chat/completions", json=body)
            return Stream(response)
        response = self._client.post("/v1/chat/completions", json=body)
        return ChatCompletion.from_dict(response.json())


class Chat:
    def __init__(self, client: BaseClient) -> None:
        self.completions = Completions(client)


class Asahio:
    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = 120.0,
        max_retries: int = 2,
        org_slug: Optional[str] = None,
    ) -> None:
        resolved_key = _resolve_api_key(api_key)
        self._client = BaseClient(
            base_url=base_url,
            api_key=resolved_key,
            timeout=timeout,
            max_retries=max_retries,
            org_slug=org_slug,
        )
        self.chat = Chat(self._client)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "Asahio":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class AsyncCompletions:
    def __init__(self, client: AsyncBaseClient) -> None:
        self._client = client

    @overload
    async def create(
        self,
        *,
        messages: list[dict[str, str]],
        model: str = "gpt-4o",
        stream: None = None,
        routing_mode: str = "AUTO",
        intervention_mode: str = "OBSERVE",
        quality_preference: str = "high",
        latency_preference: str = "normal",
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        model_endpoint_id: Optional[str] = None,
        **kwargs: Any,
    ) -> ChatCompletion: ...

    @overload
    async def create(
        self,
        *,
        messages: list[dict[str, str]],
        model: str = "gpt-4o",
        stream: bool = ...,
        routing_mode: str = "AUTO",
        intervention_mode: str = "OBSERVE",
        quality_preference: str = "high",
        latency_preference: str = "normal",
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        model_endpoint_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletion, AsyncStream]: ...

    async def create(
        self,
        *,
        messages: list[dict[str, str]],
        model: str = "gpt-4o",
        stream: Optional[bool] = None,
        routing_mode: str = "AUTO",
        intervention_mode: str = "OBSERVE",
        quality_preference: str = "high",
        latency_preference: str = "normal",
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        model_endpoint_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Union[ChatCompletion, AsyncStream]:
        body = _build_body(
            messages=messages,
            model=model,
            stream=bool(stream),
            routing_mode=routing_mode,
            intervention_mode=intervention_mode,
            quality_preference=quality_preference,
            latency_preference=latency_preference,
            agent_id=agent_id,
            session_id=session_id,
            model_endpoint_id=model_endpoint_id,
            extra=kwargs,
        )
        if stream:
            response = await self._client.post_stream("/v1/chat/completions", json=body)
            return AsyncStream(response)
        response = await self._client.post("/v1/chat/completions", json=body)
        return ChatCompletion.from_dict(response.json())


class AsyncChat:
    def __init__(self, client: AsyncBaseClient) -> None:
        self.completions = AsyncCompletions(client)


class AsyncAsahio:
    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = 120.0,
        max_retries: int = 2,
        org_slug: Optional[str] = None,
    ) -> None:
        resolved_key = _resolve_api_key(api_key)
        self._client = AsyncBaseClient(
            base_url=base_url,
            api_key=resolved_key,
            timeout=timeout,
            max_retries=max_retries,
            org_slug=org_slug,
        )
        self.chat = AsyncChat(self._client)

    async def close(self) -> None:
        await self._client.close()

    async def __aenter__(self) -> "AsyncAsahio":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()


Asahi = Asahio
AsyncAsahi = AsyncAsahio


Acorn = Asahio
AsyncAcorn = AsyncAsahio



