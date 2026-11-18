# envello

Official Python SDK for the [Envello](https://envello.dev) transactional
email API — EU-hosted, Resend-compatible request shapes.

## Install

```bash
pip install envello
```

## Quickstart

```python
from envello import Envello

client = Envello(api_key="env_test_xxx")

result = client.emails.send(
    from_="you@yourdomain.com",
    to="user@example.com",
    subject="Hello from Envello",
    html="<p>Hi there</p>",
)

print(result.id, result.status)  # e.g. "3fa8...", "queued"
```

Use a context manager if you want the underlying connection pool closed
automatically:

```python
with Envello(api_key="env_test_xxx") as client:
    client.emails.send(from_="you@yourdomain.com", to="user@example.com",
                        subject="Hello", text="Hi there")
```

## API

### `Envello(api_key, base_url="https://api.envello.dev", timeout=10.0, http_client=None)`

- `api_key` — your `env_live_...` or `env_test_...` key. Required.
- `base_url` — override for self-hosted or local dev (e.g.
  `http://localhost:3000`). Must be `https`; plain `http` is only accepted
  for `localhost`, `127.0.0.1` and `[::1]`. Anything else raises
  `EnvelloError` so the API key never goes out unencrypted.
- `timeout` — request timeout in seconds.
- `http_client` — inject your own `httpx.Client` (used by the test suite to
  mock the network layer without hitting a real server).

### `client.emails.send(...) -> SendEmailResponse`

Maps to `POST /emails`. Keyword-only, mirroring the Envello API's
`sendEmailRequestSchema` request shape:

| Argument | Type | Notes |
|---|---|---|
| `from_` | `str` | required (named `from_` since `from` is a Python keyword) |
| `to` | `str \| list[str]` | required, up to 50 addresses |
| `subject` | `str` | required |
| `html` / `text` | `str \| None` | at least one is required |
| `cc`, `bcc` | `str \| list[str] \| None` | |
| `reply_to` | `str \| None` | |
| `headers` | `dict[str, str] \| None` | custom headers |
| `attachments` | `list[Attachment] \| None` | base64 or remote-URL attachments, see `envello.types` |
| `send_at` | `str \| None` | ISO 8601 timestamp with offset; schedules instead of sending immediately |
| `idempotency_key` | `str \| None` | sent as the `Idempotency-Key` header; safe retries of the same request |

Raises `ValueError` locally (before any network call) if neither `html`
nor `text` is given.

### `client.emails.send_batch(emails: list[dict]) -> BatchSendResponse`

Maps to `POST /emails/batch`. Up to 100 emails per call, wire-format dicts
(`from`, `to`, `subject`, ...). Failures are per-item — check
`result.results[i].status`.

### `client.emails.get(email_id: str) -> GetEmailResponse`

Maps to `GET /emails/:id`.

### `client.emails.cancel(email_id: str) -> CancelEmailResponse`

Maps to `DELETE /emails/:id`. Only works on a send that's `scheduled` and
hasn't fired yet.

### `client.emails.validate(email: str) -> ValidateEmailResponse`

Maps to `POST /emails/validate`. Free on every plan (still requires a
valid API key).

## Verifying webhooks

Every webhook request carries an `Envello-Signature` header. Check it with
`verify_webhook` before trusting the payload:

```python
from flask import Flask, abort, request

from envello import verify_webhook

app = Flask(__name__)
WEBHOOK_SECRET = "whsec_..."  # the endpoint's signing secret, prefix included


@app.post("/webhooks/envello")
def envello_webhook():
    raw_body = request.get_data()  # raw bytes, before any JSON parsing
    if not verify_webhook(WEBHOOK_SECRET, raw_body, request.headers.get("Envello-Signature")):
        abort(400)
    event = request.get_json()
    ...
    return "", 204
```

Pass the **raw request body** exactly as received. If you parse the JSON
and serialize it again, the bytes change and the signature won't match.
`bytes` and `str` bodies both work.

`verify_webhook(secret, raw_body, header, *, tolerance_seconds=300, now=None) -> bool`

- Returns `False` (never raises) for a missing or malformed header, a wrong
  signature, or a timestamp more than `tolerance_seconds` away from now in
  either direction (replay protection).
- During secret rotation the header carries several `v1=` values; a match
  on any of them passes.
- `now` overrides the current Unix time, mainly for tests.

## Errors

Non-2xx responses raise `EnvelloAPIError` (or a subclass):

- `AuthenticationError` — HTTP 401 (missing/invalid/revoked key)
- `RateLimitedError` — HTTP 429 (per-key send rate limit)
- `EnvelloAPIError` — everything else (422 suppressed recipient, 409
  idempotency conflict or not-cancelable, 413 attachment too large, etc.)

Each carries `.status_code`, `.error` (the API's machine-readable error
code, e.g. `"recipient_suppressed"`), `.message`, and the full parsed
`.body`:

```python
from envello import EnvelloAPIError

try:
    client.emails.send(from_="you@yourdomain.com", to="user@example.com",
                        subject="Hi", text="hello")
except EnvelloAPIError as e:
    print(e.status_code, e.error, e.message)
```

## Why httpx

This SDK uses [`httpx`](https://www.python-httpx.org/) rather than
`requests`: it ships type hints natively (this package is fully typed and
`py.typed`-marked), and it gives a clean path to an async client
(`httpx.AsyncClient`) later without swapping HTTP libraries. If you need
async today, construct your own `httpx.AsyncClient`-backed caller against
the same endpoints — an `AsyncEnvello` client is on the roadmap but not
built yet.

## Development

```bash
pip install -e ".[dev]"
pytest
mypy src
```
