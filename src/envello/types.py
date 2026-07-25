"""Type definitions mirroring `packages/schemas/src/email.ts`.

This module is hand-written, not code-generated, so if the Zod schemas in
that file change, update these types in the same PR.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, TypedDict, Union

EmailStatus = Literal["queued", "scheduled", "sent", "send_error", "canceled"]

EmailAddress = str
"""A bare address ("a@b.com") or a "Display Name <a@b.com>" form."""

Recipients = Union[EmailAddress, List[EmailAddress]]
"""A single address or a list of up to 50 (MAX_RECIPIENTS_PER_FIELD)."""


class Base64Attachment(TypedDict, total=False):
    filename: str
    contentType: str
    content: str  # base64-encoded; required


class UrlAttachment(TypedDict, total=False):
    filename: str
    contentType: str
    url: str  # required


Attachment = Union[Base64Attachment, UrlAttachment]


@dataclass(frozen=True)
class SendEmailResponse:
    """Response body for `POST /emails`."""

    id: str
    status: EmailStatus

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SendEmailResponse":
        return cls(id=data["id"], status=data["status"])


@dataclass(frozen=True)
class BatchSendResultItem:
    """One entry in `POST /emails/batch`'s `results` array."""

    index: int
    status: Literal["queued", "scheduled", "failed"]
    id: Optional[str] = None
    error: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BatchSendResultItem":
        return cls(
            index=data["index"],
            status=data["status"],
            id=data.get("id"),
            error=data.get("error"),
        )


@dataclass(frozen=True)
class BatchSendResponse:
    """Response body for `POST /emails/batch`."""

    results: List[BatchSendResultItem]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BatchSendResponse":
        return cls(results=[BatchSendResultItem.from_dict(item) for item in data["results"]])


@dataclass(frozen=True)
class GetEmailResponse:
    """Response body for `GET /emails/:id`."""

    id: str
    status: EmailStatus
    to: List[str]
    subject: str
    send_at: Optional[str]
    sent_at: Optional[str]
    error: Optional[str]
    created_at: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GetEmailResponse":
        return cls(
            id=data["id"],
            status=data["status"],
            to=data["to"],
            subject=data["subject"],
            send_at=data.get("send_at"),
            sent_at=data.get("sent_at"),
            error=data.get("error"),
            created_at=data["created_at"],
        )


@dataclass(frozen=True)
class CancelEmailResponse:
    """Response body for `DELETE /emails/:id`."""

    id: str
    status: EmailStatus

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CancelEmailResponse":
        return cls(id=data["id"], status=data["status"])


@dataclass(frozen=True)
class ValidateEmailResponse:
    """Response body for `POST /emails/validate`."""

    email: str
    valid: bool
    syntax_valid: bool
    disposable: bool
    # Informational only (e.g. support@, admin@) - does not affect `valid`.
    # A role address is a real, permanently deliverable mailbox, unlike
    # `disposable`.
    role_account: bool
    mx_found: bool
    reason: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ValidateEmailResponse":
        return cls(
            email=data["email"],
            valid=data["valid"],
            syntax_valid=data["syntax_valid"],
            disposable=data["disposable"],
            role_account=data["role_account"],
            mx_found=data["mx_found"],
            reason=data.get("reason"),
        )
