from __future__ import annotations

import httpx
import pytest

from envello import Envello, EnvelloError

MESSAGE = "The API URL must use https (http is only allowed for localhost)."


@pytest.mark.parametrize(
    "base_url",
    [
        "http://api.envello.dev",
        "http://localhost.evil.com",
        "http://localhost@evil.com",
        "ftp://localhost",
        "not a url",
        "",
        "https://",
        "http://[::1",
    ],
)
def test_rejects_insecure_or_invalid_base_url(base_url: str) -> None:
    with pytest.raises(EnvelloError, match=r"must use https"):
        Envello(api_key="env_test_abc123", base_url=base_url)


@pytest.mark.parametrize(
    "base_url",
    [
        "https://api.envello.dev",
        "https://self-hosted.example.com/envello/",
        "http://localhost:3000",
        "HTTP://LOCALHOST:3000",
        "http://127.0.0.1:3000",
        "http://[::1]:3000",
    ],
)
def test_accepts_https_and_http_loopback(base_url: str) -> None:
    client = Envello(api_key="env_test_abc123", base_url=base_url)
    assert client.base_url == base_url.rstrip("/")
    client.close()


def test_rejects_injected_http_client_with_insecure_base_url() -> None:
    http_client = httpx.Client(base_url="http://evil.example.com")
    with pytest.raises(EnvelloError) as excinfo:
        Envello(api_key="env_test_abc123", http_client=http_client)
    assert str(excinfo.value) == MESSAGE
    http_client.close()
