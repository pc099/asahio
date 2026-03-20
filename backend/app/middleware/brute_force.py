"""Brute-force protection middleware.

Tracks failed authentication attempts per IP address and applies
exponential backoff (1s, 2s, 4s, 8s, ... up to 15 min lockout)
after repeated failures. Auto-resets on successful authentication.
"""

import logging
import time
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

# In-memory tracker (for non-Redis deployments and testing).
# In production, use Redis keys: {env}:security:auth_failures:{ip}
_failure_tracker: dict[str, dict] = {}

MAX_FAILURES = 10
MAX_LOCKOUT_SECONDS = 900  # 15 minutes


def _get_client_ip(request: Request) -> str:
    """Extract client IP, respecting X-Forwarded-For behind a proxy."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def record_auth_failure(ip: str) -> None:
    """Record a failed authentication attempt for the given IP."""
    tracker = _failure_tracker.setdefault(ip, {"count": 0, "last_failure": 0.0})
    tracker["count"] += 1
    tracker["last_failure"] = time.time()
    logger.warning("Auth failure from %s (count=%d)", ip, tracker["count"])


def record_auth_success(ip: str) -> None:
    """Reset failure tracking for an IP on successful authentication."""
    if ip in _failure_tracker:
        del _failure_tracker[ip]


def get_lockout_seconds(ip: str) -> Optional[float]:
    """Return remaining lockout seconds for an IP, or None if not locked out."""
    tracker = _failure_tracker.get(ip)
    if not tracker or tracker["count"] < MAX_FAILURES:
        return None

    # Exponential backoff: 2^(failures - MAX_FAILURES) seconds, capped at MAX_LOCKOUT
    excess = tracker["count"] - MAX_FAILURES
    lockout = min(2 ** excess, MAX_LOCKOUT_SECONDS)
    elapsed = time.time() - tracker["last_failure"]

    if elapsed < lockout:
        return lockout - elapsed
    return None


def reset_tracker() -> None:
    """Reset all tracking data (for testing)."""
    _failure_tracker.clear()


class BruteForceMiddleware(BaseHTTPMiddleware):
    """Middleware that blocks requests from IPs with too many auth failures."""

    async def dispatch(self, request: Request, call_next) -> Response:
        ip = _get_client_ip(request)
        remaining = get_lockout_seconds(ip)

        if remaining is not None:
            logger.warning(
                "Brute force lockout: IP %s locked for %.0f more seconds", ip, remaining
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "AUTH_RATE_LIMITED",
                        "message": "Too many failed authentication attempts. Please try again later.",
                        "detail": {"retry_after_seconds": int(remaining)},
                    }
                },
                headers={"Retry-After": str(int(remaining))},
            )

        response = await call_next(request)

        # Track auth failures from 401 responses on auth-related paths
        if response.status_code == 401:
            record_auth_failure(ip)
        elif response.status_code in (200, 201, 204):
            # Successful request — reset failure counter
            tracker = _failure_tracker.get(ip)
            if tracker and tracker["count"] > 0:
                record_auth_success(ip)

        return response
