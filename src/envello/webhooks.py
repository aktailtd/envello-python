"""Verify the ``Envello-Signature`` header on incoming webhook requests.

Header format: ``t=<unix-seconds>,v1=<hex hmac-sha256>[,v1=<hex>...]``.
Several ``v1`` values appear while an endpoint secret is being rotated; a
match on any one of them passes. The signed content is ``<t>.<raw body>``,
keyed with the endpoint secret exactly as shown in the dashboard (including
the ``whsec_`` prefix).
"""
from __future__ import annotations

import hashlib
import hmac
import time

DEFAULT_TOLERANCE_SECONDS = 300

_TIMESTAMP_KEY = "t"
_SIGNATURE_KEY = "v1"


def _parse_header(header: str) -> tuple[str, list[str]] | None:
    """Return (timestamp, v1 signatures), or None if the header is malformed."""
    timestamp: str | None = None
    signatures: list[str] = []
    for part in header.split(","):
        key, separator, value = part.partition("=")
        if not separator or not value:
            continue
        if key == _TIMESTAMP_KEY:
            timestamp = value
        elif key == _SIGNATURE_KEY:
            signatures.append(value)
    if timestamp is None or not signatures:
        return None
    return timestamp, signatures


def _parse_timestamp(raw: str) -> int | None:
    # isascii + isdigit rejects "+5", " 5", "1_000" and non-ASCII digits that
    # int() would accept. The server signs the canonical decimal form, so the
    # string we sign over must be exactly that.
    if not (raw.isascii() and raw.isdigit()):
        return None
    timestamp = int(raw)
    return timestamp if timestamp > 0 else None


def verify_webhook(
    secret: str,
    raw_body: bytes | str,
    header: str | None,
    *,
    tolerance_seconds: int = DEFAULT_TOLERANCE_SECONDS,
    now: int | None = None,
) -> bool:
    """Return True if ``header`` is a valid, fresh Envello signature for ``raw_body``.

    Pass the raw request body exactly as received. Parsing and re-serializing
    the JSON changes the bytes and the signature will not match. Malformed or
    missing headers return False; this never raises for bad input.
    """
    if not header:
        return False
    parsed = _parse_header(header)
    if parsed is None:
        return False
    raw_timestamp, signatures = parsed
    timestamp = _parse_timestamp(raw_timestamp)
    if timestamp is None:
        return False

    current = int(time.time()) if now is None else now
    if abs(current - timestamp) > tolerance_seconds:
        return False

    # errors="replace" so a str with lone surrogates fails verification
    # instead of raising.
    body = raw_body.encode("utf-8", errors="replace") if isinstance(raw_body, str) else raw_body
    expected = hmac.new(
        secret.encode("utf-8"),
        raw_timestamp.encode("ascii") + b"." + body,
        hashlib.sha256,
    ).hexdigest().encode("ascii")

    # Check every v1 with no early exit so timing doesn't reveal which one
    # matched (or how many were tried).
    matched = False
    for signature in signatures:
        candidate = signature.encode("utf-8", errors="replace")
        matched |= hmac.compare_digest(expected, candidate)
    return matched
