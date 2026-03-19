"""Request ID middleware — propagates or generates X-Request-ID for log correlation."""

import contextvars
import logging
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Context variable accessible across the request scope
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Reads X-Request-ID from the request or generates a new one.

    Stores the request ID on ``request.state.request_id`` and in
    ``request_id_var`` (context variable) so it can be injected into log
    records by ``RequestIDFilter``.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex
        request.state.request_id = rid
        request_id_var.set(rid)

        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response


class RequestIDFilter(logging.Filter):
    """Logging filter that injects ``request_id`` into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get("")  # type: ignore[attr-defined]
        return True
