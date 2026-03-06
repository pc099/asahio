"""Legacy compatibility package for `from acorn import Acorn`."""

from asahio import (  # noqa: F401
    APIConnectionError,
    APIError,
    Acorn,
    AsyncAcorn,
    AsahioError,
    AuthenticationError,
    BudgetExceededError,
    RateLimitError,
    __version__,
)

__all__ = [
    "Acorn",
    "AsyncAcorn",
    "AsahioError",
    "AuthenticationError",
    "RateLimitError",
    "BudgetExceededError",
    "APIError",
    "APIConnectionError",
    "__version__",
]
