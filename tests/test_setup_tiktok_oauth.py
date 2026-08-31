"""Unit tests for auth/setup_tiktok_oauth.py's client-secret persistence.

No credentials, browser profiles, network access, or live accounts anywhere in this file --
webbrowser.open, input(), and the token exchange itself are all mocked.
"""
from __future__ import annotations

import json
import sys
from unittest.mock import MagicMock

import pytest

import auth.setup_tiktok_oauth as setup_tiktok_oauth


@pytest.fixture
def isolated_paths(monkeypatch, tmp_path):
    """Point TOKEN_PATH/DEFAULT_CLIENT_SECRETS at a throwaway directory so this test never
    touches a real profiles/tiktok/ directory."""
    token_path = tmp_path / "profiles" / "tiktok" / "token.json"
    default_secrets_path = tmp_path / "profiles" / "tiktok" / "client_secret.json"
    monkeypatch.setattr(setup_tiktok_oauth, "TOKEN_PATH", token_path)
    monkeypatch.setattr(setup_tiktok_oauth, "DEFAULT_CLIENT_SECRETS", default_secrets_path)
    return token_path, default_secrets_path


def _run_main_with(monkeypatch, argv, client_config):
    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setattr(setup_tiktok_oauth, "_load_client_config", lambda path: client_config)
    monkeypatch.setattr(setup_tiktok_oauth, "_make_pkce_pair", lambda: ("verifier", "challenge"))
    monkeypatch.setattr(setup_tiktok_oauth.webbrowser, "open", lambda url: None)
    monkeypatch.setattr("builtins.input", lambda prompt="": "https://example.com/cb?code=abc&state=STATE")
    monkeypatch.setattr(
        setup_tiktok_oauth, "_extract_code", lambda url, expected_state: "abc"
    )
    monkeypatch.setattr(
        setup_tiktok_oauth,
        "_exchange_code_for_token",
        MagicMock(return_value={"access_token": "tok", "refresh_token": "ref", "expires_in": 3600}),
    )
    setup_tiktok_oauth.main()


def test_client_secret_copied_to_default_location_when_source_is_elsewhere(monkeypatch, tmp_path, isolated_paths):
    """Regression test for a Codex-reported bug: auth/publish_tiktok.py's token-refresh step
    reads the client secret from exactly DEFAULT_CLIENT_SECRETS, with no way to know where
    --client-secrets originally pointed. Following the documented
    `--client-secrets path/to/tiktok_client.json` form with a file outside profiles/tiktok/ must
    still leave a usable copy at the default location, or every refresh after the access token
    expires fails."""
    token_path, default_secrets_path = isolated_paths
    external_secrets = tmp_path / "elsewhere" / "tiktok_client.json"
    client_config = {
        "client_key": "key123",
        "client_secret": "secret123",
        "redirect_uri": "https://example.com/cb",
    }

    assert not default_secrets_path.exists()
    _run_main_with(
        monkeypatch,
        ["setup_tiktok_oauth.py", "--client-secrets", str(external_secrets)],
        client_config,
    )

    assert default_secrets_path.is_file()
    assert json.loads(default_secrets_path.read_text(encoding="utf-8")) == client_config
    assert token_path.is_file()


def test_client_secret_not_duplicated_when_source_is_already_the_default(monkeypatch, tmp_path, isolated_paths):
    """When --client-secrets already points at DEFAULT_CLIENT_SECRETS (the documented default,
    and the common case), there's nothing to copy -- this must not error or overwrite anything
    unexpectedly."""
    token_path, default_secrets_path = isolated_paths
    client_config = {
        "client_key": "key123",
        "client_secret": "secret123",
        "redirect_uri": "https://example.com/cb",
    }
    default_secrets_path.parent.mkdir(parents=True, exist_ok=True)
    default_secrets_path.write_text(json.dumps(client_config), encoding="utf-8")

    _run_main_with(
        monkeypatch,
        ["setup_tiktok_oauth.py", "--client-secrets", str(default_secrets_path)],
        client_config,
    )

    assert token_path.is_file()
    assert json.loads(default_secrets_path.read_text(encoding="utf-8")) == client_config
