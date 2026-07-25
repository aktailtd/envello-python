from __future__ import annotations

import json
from typing import Any, Callable, Dict

import httpx
import pytest

from envello import AuthenticationError, Envello, RateLimitedError


def make_client(handler: Callable[[httpx.Request], httpx.Response]) -> Envello:
    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport, base_url="https://api.test")
    return Envello(api_key="env_test_abc123", http_client=http_client)


def test_send_email_success() -> None:
    captured: Dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["url"] = str(request.url)
        captured["auth"] = request.headers.get("authorization")
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            202, json={"id": "11111111-1111-1111-1111-111111111111", "status": "queued"}
        )

    client = make_client(handler)
    result = client.emails.send(
        from_="you@yourdomain.com",
        to="user@example.com",
        subject="Hello",
        html="<p>hi</p>",
    )

    assert result.id == "11111111-1111-1111-1111-111111111111"
    assert result.status == "queued"
    assert captured["method"] == "POST"
    assert captured["url"].endswith("/emails")
    assert captured["auth"] == "Bearer env_test_abc123"
    assert captured["body"] == {
        "from": "you@yourdomain.com",
        "to": "user@example.com",
        "subject": "Hello",
        "html": "<p>hi</p>",
    }


def test_send_requires_html_or_text() -> None:
    client = make_client(lambda request: httpx.Response(202, json={}))
    with pytest.raises(ValueError):
        client.emails.send(from_="a@b.com", to="c@d.com", subject="x")


def test_send_with_idempotency_key_sets_header() -> None:
    captured: Dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["idempotency_key"] = request.headers.get("idempotency-key")
        return httpx.Response(202, json={"id": "some-id", "status": "queued"})

    client = make_client(handler)
    client.emails.send(
        from_="a@b.com", to="c@d.com", subject="x", text="hi", idempotency_key="my-key-1"
    )
    assert captured["idempotency_key"] == "my-key-1"


def test_rate_limited_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            429, json={"error": "rate_limited", "message": "slow down", "limit": 100}
        )

    client = make_client(handler)
    with pytest.raises(RateLimitedError) as exc_info:
        client.emails.send(from_="a@b.com", to="c@d.com", subject="x", text="hi")
    assert exc_info.value.status_code == 429
    assert exc_info.value.error == "rate_limited"


def test_invalid_api_key_raises_authentication_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "invalid_api_key", "message": "bad key"})

    client = make_client(handler)
    with pytest.raises(AuthenticationError):
        client.emails.get("11111111-1111-1111-1111-111111111111")


def test_get_email_status() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path.endswith("/emails/abc-123")
        return httpx.Response(
            200,
            json={
                "id": "abc-123",
                "status": "sent",
                "to": ["user@example.com"],
                "subject": "Hello",
                "send_at": None,
                "sent_at": "2026-07-13T00:00:00+00:00",
                "error": None,
                "created_at": "2026-07-13T00:00:00+00:00",
            },
        )

    client = make_client(handler)
    result = client.emails.get("abc-123")
    assert result.status == "sent"
    assert result.to == ["user@example.com"]
    assert result.error is None


def test_validate_email() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/emails/validate")
        return httpx.Response(
            200,
            json={
                "email": "user@example.com",
                "valid": True,
                "syntax_valid": True,
                "disposable": False,
                "role_account": False,
                "mx_found": True,
            },
        )

    client = make_client(handler)
    result = client.emails.validate("user@example.com")
    assert result.valid is True
    assert result.role_account is False
    assert result.reason is None


def test_batch_send_partial_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            207,
            json={
                "results": [
                    {"index": 0, "status": "queued", "id": "id-0"},
                    {"index": 1, "status": "failed", "error": "recipient suppressed"},
                ]
            },
        )

    client = make_client(handler)
    result = client.emails.send_batch(
        [
            {"from": "a@b.com", "to": "c@d.com", "subject": "x", "text": "hi"},
            {"from": "a@b.com", "to": "e@f.com", "subject": "y", "text": "hi"},
        ]
    )
    assert len(result.results) == 2
    assert result.results[0].status == "queued"
    assert result.results[0].id == "id-0"
    assert result.results[1].status == "failed"
    assert result.results[1].error == "recipient suppressed"


def test_cancel_scheduled_email() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        return httpx.Response(200, json={"id": "abc-123", "status": "canceled"})

    client = make_client(handler)
    result = client.emails.cancel("abc-123")
    assert result.status == "canceled"


def test_not_cancelable_raises_api_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            409,
            json={
                "error": "not_cancelable",
                "message": "Only a send that hasn't fired yet can be canceled",
            },
        )

    client = make_client(handler)
    with pytest.raises(Exception) as exc_info:
        client.emails.cancel("abc-123")
    assert exc_info.value.status_code == 409  # type: ignore[attr-defined]
    assert exc_info.value.error == "not_cancelable"  # type: ignore[attr-defined]


def test_client_requires_api_key() -> None:
    with pytest.raises(ValueError):
        Envello(api_key="")
