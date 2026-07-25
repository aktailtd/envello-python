"""The `emails` resource — `/emails*` per `packages/schemas/src/email.ts`."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional
from urllib.parse import quote

from ..types import (
    Attachment,
    BatchSendResponse,
    CancelEmailResponse,
    GetEmailResponse,
    Recipients,
    SendEmailResponse,
    ValidateEmailResponse,
)

if TYPE_CHECKING:
    from ..client import Envello


def _build_send_payload(
    *,
    from_: str,
    to: Recipients,
    cc: Optional[Recipients],
    bcc: Optional[Recipients],
    reply_to: Optional[str],
    subject: str,
    html: Optional[str],
    text: Optional[str],
    headers: Optional[Dict[str, str]],
    attachments: Optional[List[Attachment]],
    send_at: Optional[str],
) -> Dict[str, Any]:
    if not html and not text:
        raise ValueError("At least one of `html` or `text` is required")
    payload: Dict[str, Any] = {"from": from_, "to": to, "subject": subject}
    if cc is not None:
        payload["cc"] = cc
    if bcc is not None:
        payload["bcc"] = bcc
    if reply_to is not None:
        payload["reply_to"] = reply_to
    if html is not None:
        payload["html"] = html
    if text is not None:
        payload["text"] = text
    if headers is not None:
        payload["headers"] = headers
    if attachments is not None:
        payload["attachments"] = attachments
    if send_at is not None:
        payload["send_at"] = send_at
    return payload


class EmailsResource:
    """Wraps send, batch send, status lookup, cancel, and validate."""

    def __init__(self, client: "Envello") -> None:
        self._client = client

    def send(
        self,
        *,
        from_: str,
        to: Recipients,
        subject: str,
        cc: Optional[Recipients] = None,
        bcc: Optional[Recipients] = None,
        reply_to: Optional[str] = None,
        html: Optional[str] = None,
        text: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        attachments: Optional[List[Attachment]] = None,
        send_at: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> SendEmailResponse:
        """Send a single email. Maps to `POST /emails`.

        Keyword args mirror `sendEmailRequestSchema` in
        `packages/schemas/src/email.ts`. At least one of `html` or `text`
        is required (raises `ValueError` locally if both are omitted,
        matching the API's own validation). `send_at`, if given, must be
        an ISO 8601 timestamp with a UTC offset (e.g.
        "2026-08-01T09:00:00+00:00") and schedules the send instead of
        firing immediately. `idempotency_key`, if given, is sent as the
        `Idempotency-Key` header so retries of the same request are safe.
        """
        payload = _build_send_payload(
            from_=from_,
            to=to,
            cc=cc,
            bcc=bcc,
            reply_to=reply_to,
            subject=subject,
            html=html,
            text=text,
            headers=headers,
            attachments=attachments,
            send_at=send_at,
        )
        extra_headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        data = self._client.request("POST", "/emails", json=payload, headers=extra_headers)
        return SendEmailResponse.from_dict(data)

    def send_batch(self, emails: List[Dict[str, Any]]) -> BatchSendResponse:
        """Send up to 100 emails in one call. Maps to `POST /emails/batch`.

        Each item in `emails` is a dict using the wire field names (`from`,
        `to`, `subject`, `html`/`text`, ...) rather than `send()`'s Python
        keyword names, since batch items are passed through largely as-is.
        The API processes items independently, so check each result's
        `status` -- one item failing (e.g. a suppressed recipient) doesn't
        fail the whole batch.
        """
        data = self._client.request("POST", "/emails/batch", json={"emails": emails})
        return BatchSendResponse.from_dict(data)

    def get(self, email_id: str) -> GetEmailResponse:
        """Fetch the current status of a send. Maps to `GET /emails/:id`."""
        data = self._client.request("GET", f"/emails/{quote(email_id, safe='')}")
        return GetEmailResponse.from_dict(data)

    def cancel(self, email_id: str) -> CancelEmailResponse:
        """Cancel a scheduled (not-yet-fired) send. Maps to
        `DELETE /emails/:id`. Raises `EnvelloAPIError` (409) if the send
        already fired or wasn't scheduled to begin with."""
        data = self._client.request("DELETE", f"/emails/{quote(email_id, safe='')}")
        return CancelEmailResponse.from_dict(data)

    def validate(self, email: str) -> ValidateEmailResponse:
        """Validate an email address (syntax + disposable-domain check +
        MX lookup). Free on every plan, but still requires a valid API
        key. Maps to `POST /emails/validate`."""
        data = self._client.request("POST", "/emails/validate", json={"email": email})
        return ValidateEmailResponse.from_dict(data)
