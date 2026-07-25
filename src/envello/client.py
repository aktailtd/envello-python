"""The Envello API client.

HTTP is done with `httpx` (sync `httpx.Client`) rather than `requests`,
chosen because it ships type hints natively, supports HTTP/2, and gives a
straightforward upgrade path to an async client (`httpx.AsyncClient`) later
without swapping libraries. See README.md's "Why httpx" section.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, cast

import httpx

from .exceptions import AuthenticationError, EnvelloAPIError, RateLimitedError
from .resources.emails import EmailsResource

DEFAULT_BASE_URL = "https://api.envello.dev"
DEFAULT_TIMEOUT = 10.0


class Envello:
    """Client for the Envello transactional email API.

    Example:
        >>> from envello import Envello
        >>> client = Envello(api_key="env_test_xxx")
        >>> client.emails.send(
        ...     from_="you@yourdomain.com",
        ...     to="user@example.com",
        ...     subject="Hello",
        ...     html="<p>Hi there</p>",
        ... )
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._client = http_client or httpx.Client(base_url=self.base_url, timeout=timeout)
        # Set explicitly per request (rather than relying on the httpx
        # client's default headers) so auth still works if a caller injects
        # their own pre-built `http_client`.
        self._default_headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "envello-python/0.1.0",
        }
        self.emails = EmailsResource(self)

    def request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Low-level request helper used by resource classes. Not usually
        called directly by SDK users."""
        merged_headers = {**self._default_headers, **(headers or {})}
        response = self._client.request(method, path, json=json, headers=merged_headers)
        if response.status_code >= 400:
            self._raise_for_error(response)
        if response.status_code == 204 or not response.content:
            return {}
        return cast(Dict[str, Any], response.json())

    @staticmethod
    def _raise_for_error(response: httpx.Response) -> None:
        body: Optional[Dict[str, Any]]
        try:
            body = response.json()
        except ValueError:
            body = None
        error_code = body.get("error") if body else None
        message = body.get("message") if body else (response.text or None)
        if response.status_code == 401:
            raise AuthenticationError(response.status_code, error_code, message, body)
        if response.status_code == 429:
            raise RateLimitedError(response.status_code, error_code, message, body)
        raise EnvelloAPIError(response.status_code, error_code, message, body)

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._client.close()

    def __enter__(self) -> "Envello":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
