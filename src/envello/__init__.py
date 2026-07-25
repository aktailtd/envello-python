"""Envello — official Python SDK for the Envello transactional email API.

    from envello import Envello

    client = Envello(api_key="env_test_xxx")
    result = client.emails.send(
        from_="you@yourdomain.com",
        to="user@example.com",
        subject="Hello",
        html="<p>Hi there</p>",
    )
"""
from .client import DEFAULT_BASE_URL, Envello
from .exceptions import AuthenticationError, EnvelloAPIError, EnvelloError, RateLimitedError
from .types import (
    Attachment,
    Base64Attachment,
    BatchSendResponse,
    BatchSendResultItem,
    CancelEmailResponse,
    EmailStatus,
    GetEmailResponse,
    Recipients,
    SendEmailResponse,
    UrlAttachment,
    ValidateEmailResponse,
)

__version__ = "0.1.0"

__all__ = [
    "Envello",
    "DEFAULT_BASE_URL",
    "EnvelloError",
    "EnvelloAPIError",
    "AuthenticationError",
    "RateLimitedError",
    "Attachment",
    "Base64Attachment",
    "UrlAttachment",
    "EmailStatus",
    "Recipients",
    "SendEmailResponse",
    "BatchSendResponse",
    "BatchSendResultItem",
    "GetEmailResponse",
    "CancelEmailResponse",
    "ValidateEmailResponse",
    "__version__",
]
