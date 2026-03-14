"""Legacy compatibility package for `from asahi import Asahi`."""

from asahio import (  # noqa: F401
    APIConnectionError,
    APIError,
    Asahi,
    AsyncAsahi,
    AsahioError,
    AuthenticationError,
    BudgetExceededError,
    RateLimitError,
    __version__,
)

__all__ = [
    "Asahi",
    "AsyncAsahi",
    "AsahioError",
    "AuthenticationError",
    "RateLimitError",
    "BudgetExceededError",
    "APIError",
    "APIConnectionError",
    "__version__",
]
