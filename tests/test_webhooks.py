from __future__ import annotations

import pytest

from envello import verify_webhook

# Test vector from the T24 spec, produced by the API's webhook-signing.ts.
SECRET = "whsec_test_secret"
OLD_SECRET = "whsec_old"
TIMESTAMP = 1795000000
BODY = '{"type":"email.delivered","data":{"id":"e_1"}}'
SIGNATURE = "01fd7cd18054befb25b082d367dca85a0494a916825e50896c202a70daf7d20c"
OLD_SIGNATURE = "2dd8bb6eb3a2f5b581fa0fa9b72bbc243b42fad944b73591035a7c34d521c271"
HEADER = f"t={TIMESTAMP},v1={SIGNATURE}"
ROTATION_HEADER = f"t={TIMESTAMP},v1={SIGNATURE},v1={OLD_SIGNATURE}"
DEFAULT_TOLERANCE = 300


def test_spec_vector_passes() -> None:
    assert verify_webhook(SECRET, BODY, HEADER, now=TIMESTAMP) is True


@pytest.mark.parametrize("secret", [SECRET, OLD_SECRET])
def test_rotation_header_passes_for_either_secret(secret: str) -> None:
    assert verify_webhook(secret, BODY, ROTATION_HEADER, now=TIMESTAMP) is True


def test_wrong_secret_fails() -> None:
    assert verify_webhook("whsec_wrong", BODY, HEADER, now=TIMESTAMP) is False


def test_tampered_body_fails() -> None:
    tampered = BODY.replace("e_1", "e_2")
    assert verify_webhook(SECRET, tampered, HEADER, now=TIMESTAMP) is False


def test_timestamp_at_tolerance_edge_passes() -> None:
    now = TIMESTAMP + DEFAULT_TOLERANCE
    assert verify_webhook(SECRET, BODY, HEADER, now=now) is True


def test_stale_timestamp_fails() -> None:
    now = TIMESTAMP + DEFAULT_TOLERANCE + 1
    assert verify_webhook(SECRET, BODY, HEADER, now=now) is False


def test_future_timestamp_fails() -> None:
    now = TIMESTAMP - DEFAULT_TOLERANCE - 1
    assert verify_webhook(SECRET, BODY, HEADER, now=now) is False


def test_custom_tolerance() -> None:
    now = TIMESTAMP + 1000
    assert verify_webhook(SECRET, BODY, HEADER, tolerance_seconds=1000, now=now) is True


@pytest.mark.parametrize(
    "header",
    [
        None,
        "",
        "t=abc,v1=x",
        f"v1={SIGNATURE}",
        f"t={TIMESTAMP}",
        f"t=0,v1={SIGNATURE}",
        f"t=-{TIMESTAMP},v1={SIGNATURE}",
        f"t=+{TIMESTAMP},v1={SIGNATURE}",
        f"t={TIMESTAMP}.0,v1={SIGNATURE}",
        f"t={TIMESTAMP},v1=",
        f"t={TIMESTAMP},v0={SIGNATURE}",
        f"t={TIMESTAMP},v1=éé",
        "garbage",
        ",,,",
        "===",
    ],
)
def test_malformed_or_missing_header_returns_false(header: str | None) -> None:
    assert verify_webhook(SECRET, BODY, header, now=TIMESTAMP) is False


def test_bytes_and_str_bodies_match() -> None:
    as_bytes = BODY.encode("utf-8")
    assert verify_webhook(SECRET, as_bytes, HEADER, now=TIMESTAMP) is True
    assert verify_webhook(SECRET, as_bytes, HEADER, now=TIMESTAMP) == verify_webhook(
        SECRET, BODY, HEADER, now=TIMESTAMP
    )
    tampered = b'{"type":"email.delivered","data":{"id":"e_2"}}'
    assert verify_webhook(SECRET, tampered, HEADER, now=TIMESTAMP) is False


def test_uses_current_time_when_now_omitted() -> None:
    # The vector's timestamp is far from the real clock, so it must be stale.
    assert verify_webhook(SECRET, BODY, HEADER) is False


def test_empty_secret_never_verifies() -> None:
    empty_key_signature = "73457d45da4254428de731ff81d20dd03d432f84fef02aead38b2fa7c7cd5c77"
    assert verify_webhook("", BODY, f"t={TIMESTAMP},v1={empty_key_signature}", now=TIMESTAMP) is False


@pytest.mark.parametrize("tolerance", [float("nan"), float("inf"), -1])
def test_bad_tolerance_fails_closed(tolerance: float) -> None:
    assert verify_webhook(SECRET, BODY, HEADER, tolerance_seconds=tolerance, now=TIMESTAMP + 10**7) is False  # type: ignore[arg-type]


def test_nan_now_fails_closed() -> None:
    assert verify_webhook(SECRET, BODY, HEADER, now=float("nan")) is False  # type: ignore[arg-type]


@pytest.mark.parametrize("secret, header", [(None, HEADER), (SECRET, ["t=1"]), (123, HEADER)])
def test_wrong_types_return_false(secret: object, header: object) -> None:
    assert verify_webhook(secret, BODY, header, now=TIMESTAMP) is False  # type: ignore[arg-type]
