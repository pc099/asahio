import pytest

from asahio._streaming import AsyncStream, Stream


class SyncResponse:
    def __init__(self, lines: list[str]) -> None:
        self._lines = lines
        self.closed = False

    def iter_lines(self):
        for line in self._lines:
            yield line

    def close(self) -> None:
        self.closed = True


class AsyncResponse:
    def __init__(self, lines: list[str]) -> None:
        self._lines = lines
        self.closed = False

    async def aiter_lines(self):
        for line in self._lines:
            yield line

    async def aclose(self) -> None:
        self.closed = True


def test_stream_ignores_metadata_event_payload() -> None:
    response = SyncResponse(
        [
            'data: {"id":"chatcmpl_1","object":"chat.completion.chunk","model":"gpt-4o-mini","choices":[{"index":0,"delta":{"content":"hello"},"finish_reason":null}]}',
            'event: asahio',
            'data: {"request_id":"req_123","routing_mode":"AUTO"}',
            'data: [DONE]',
        ]
    )

    chunks = list(Stream(response))

    assert len(chunks) == 1
    assert chunks[0].choices[0].delta.content == "hello"
    assert response.closed is True


@pytest.mark.asyncio
async def test_async_stream_ignores_metadata_event_payload() -> None:
    response = AsyncResponse(
        [
            'data: {"id":"chatcmpl_1","object":"chat.completion.chunk","model":"gpt-4o-mini","choices":[{"index":0,"delta":{"content":"hello"},"finish_reason":null}]}',
            'event: asahio',
            'data: {"request_id":"req_123","routing_mode":"AUTO"}',
            'data: [DONE]',
        ]
    )

    chunks = []
    async for chunk in AsyncStream(response):
        chunks.append(chunk)

    assert len(chunks) == 1
    assert chunks[0].choices[0].delta.content == "hello"
    assert response.closed is True
