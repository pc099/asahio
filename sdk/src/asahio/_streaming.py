"""SSE stream parsers for chat completion chunks."""

from __future__ import annotations

import json
from typing import AsyncIterator, Iterator

import httpx

from asahio.types.chat import ChatCompletionChunk


class Stream:
    def __init__(self, response: httpx.Response) -> None:
        self._response = response

    def __iter__(self) -> Iterator[ChatCompletionChunk]:
        try:
            for line in self._response.iter_lines():
                chunk = _parse_sse_line(line)
                if chunk is _DONE:
                    break
                if chunk is not None:
                    yield chunk
        finally:
            self._response.close()

    def close(self) -> None:
        self._response.close()


class AsyncStream:
    def __init__(self, response: httpx.Response) -> None:
        self._response = response

    async def __aiter__(self) -> AsyncIterator[ChatCompletionChunk]:
        try:
            async for line in self._response.aiter_lines():
                chunk = _parse_sse_line(line)
                if chunk is _DONE:
                    break
                if chunk is not None:
                    yield chunk
        finally:
            await self._response.aclose()

    async def close(self) -> None:
        await self._response.aclose()


_DONE = object()


def _parse_sse_line(line: str) -> ChatCompletionChunk | object | None:
    line = line.strip()
    if not line or line.startswith(":"):
        return None
    if not line.startswith("data:"):
        return None

    payload = line[len("data:"):].strip()
    if payload == "[DONE]":
        return _DONE

    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return None

    if not isinstance(data, dict) or data.get("object") != "chat.completion.chunk":
        return None

    return ChatCompletionChunk.from_dict(data)
