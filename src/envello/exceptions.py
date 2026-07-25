"""Exceptions raised by the Envello client."""
from __future__ import annotations

from typing import Any, Dict, Optional


class EnvelloError(Exception):
    """Base class for all errors raised by this SDK."""


class EnvelloAPIError(EnvelloError):
    """Raised when the Envello API returns a non-2xx response.

    Attributes:
        status_code: The HTTP status code returned.
        error: The machine-readable error code from the response body's
            `error` field (e.g. "rate_limited", "recipient_suppressed"),
            or None if the body couldn't be parsed as JSON.
        message: A human-readable message, if the API provided one.
        body: The full parsed JSON response body, if available.
    """

    def __init__(
        self,
        status_code: int,
        error: Optional[str],
        message: Optional[str],
        body: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.status_code = status_code
        self.error = error
        self.message = message
        self.body = body
        summary = f"Envello API error ({status_code}): {error or 'unknown_error'}"
        if message:
            summary += f" - {message}"
        super().__init__(summary)


class AuthenticationError(EnvelloAPIError):
    """Raised on HTTP 401 — missing or invalid API key."""


class RateLimitedError(EnvelloAPIError):
    """Raised on HTTP 429 — too many send requests for this API key."""
