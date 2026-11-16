# fix/https-base-url-pinned-actions

## Goal
T18: stop the SDK sending the API key over plain http. T19: pin GitHub Actions to commit SHAs and scope the OIDC permission.

## What changed
- `src/envello/client.py`: `_validate_base_url()` runs in `Envello.__init__`. Allows `https`, or `http` on `localhost` / `127.0.0.1` / `[::1]`. Anything else, or an unparseable URL, raises `EnvelloError("The API URL must use https (http is only allowed for localhost).")`. Also checks an injected `http_client.base_url`, since requests go there.
- `tests/test_base_url.py`: rejected and accepted URL cases, including `http://localhost.evil.com`, `http://localhost@evil.com`, uppercase scheme/host, path kept with trailing slash stripped, insecure injected client.
- `README.md`: documents the rule on `base_url`.
- `.github/workflows/publish.yml`: actions pinned to SHAs, `id-token: write` moved from workflow level to the `publish` job, `build` pinned to `1.6.1` (uploaded 2026-09-10).

## Decisions
- Raises `EnvelloError` (the SDK base class) rather than `ValueError`, so callers can catch one SDK type.
- Kept the same major versions of each action, pinned to the latest release in that major. The floating tags (`v4`, `v5`, `release/v1`) resolved to these same SHAs on 2026-11-16, so no behaviour change.

| Action | Commit | Tag |
| --- | --- | --- |
| actions/checkout | 11d5960a326750d5838078e36cf38b85af677262 | v4.4.0 |
| actions/setup-python | a26af69be951a213d495a4c3e4e4022e16d87065 | v5.6.0 |
| pypa/gh-action-pypi-publish | 7245906fb61fa33a13554f9d5fb856fe61758086 | v1.14.3 (annotated tag, dereferenced) |

## State
Done. Not released; no tag pushed.

## Verify
```
python3 -m venv /tmp/v && /tmp/v/bin/pip install -e ".[dev]"
/tmp/v/bin/python -m pytest -q   # 26 passed
/tmp/v/bin/python -m mypy src    # clean
```

## Gotchas
- The repo's `.venv` is a publish venv without pytest; use a fresh venv.
- The only job both tests and publishes, so it keeps `id-token: write`. There is no CI on pull requests in this repo, so the workflow change is only exercised on the next tag push.
- `pip install -e ".[dev]"` in the workflow is still unpinned (pytest, mypy ranges from `pyproject.toml`).
