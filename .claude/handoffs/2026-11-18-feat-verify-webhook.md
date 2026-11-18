# feat/verify-webhook

## Goal
T24: add a webhook signature verifier to the Python SDK, matching the API's `webhook-signing.ts` scheme.

## What changed
- `src/envello/webhooks.py`: new `verify_webhook(secret, raw_body, header, *, tolerance_seconds=300, now=None) -> bool`. Stdlib only (`hmac`, `hashlib`, `time`).
- `src/envello/__init__.py`: exports `verify_webhook` and adds it to `__all__`.
- `tests/test_webhooks.py`: spec test vector, rotation header (both secrets), wrong secret, tampered body, tolerance edge, stale and future timestamps, malformed/missing headers, bytes vs str body.
- `README.md`: "Verifying webhooks" section with a Flask `request.get_data()` example and the raw-body note.

## Decisions
- Signs over the `t` string as received, not a re-formatted int. `t` must be ASCII digits only and > 0, so `+5`, `1_000`, ` 5`, `5.0` are rejected even though `int()` or JS `Number()` would accept some of them. The server always sends canonical digits.
- Header parsing splits on `,` then the first `=`; unknown keys and empty values are skipped. Requires one `t` and at least one `v1`.
- Every `v1` is checked with `hmac.compare_digest` and the results OR'd, no early exit.
- Hex comparison is on bytes, so a non-ASCII `v1` can't raise `TypeError` from `compare_digest`. A `str` body or `v1` with lone surrogates is encoded with `errors="replace"` so it fails instead of raising.
- No CHANGELOG exists in this repo, so none was added. Version not bumped.

## State
Done. Branch pushed, no PR opened (as asked). Not released, no tag.

## Verify
```
python3 -m venv /tmp/v && /tmp/v/bin/pip install -e ".[dev]"
/tmp/v/bin/python -m pytest -q   # 52 passed
/tmp/v/bin/python -m mypy src    # clean
```

## Gotchas
- The repo has no ruff config. A user-level ruff config flags many pre-existing `Optional`/`Dict` usages in other files; only the new files were checked (`ruff check` clean). `ruff format` was not applied, to keep the existing file style.
- The API's own `verifySignatureHeader` keeps only the last `v1` in the header (its reducer overwrites earlier ones). The SDK accepts any `v1`, per the spec. Worth aligning the server-side helper if it's ever used for rotation.
- `__version__` in `__init__.py` says `0.1.0` while `pyproject.toml` says `0.1.1`. Pre-existing, left alone.
