"""One-time TikTok OAuth setup -- run this instead of the login wizard.

Like YouTube, TikTok doesn't go through auth/login_wizard.py: TikTok actively detects and
blocks sign-in attempts from automation-controlled browsers, the same anti-automation reality
documented in auth/login_wizard.py's module docstring for X/Instagram/LinkedIn. OAuth + the
official Content Posting API is the correct, TikTok-sanctioned integration path -- no browser
automation involved.

## Why this setup script looks different from auth/setup_youtube_oauth.py

Google's OAuth flow for a desktop app can redirect to a bare `http://localhost:<port>` URL, so
setup_youtube_oauth.py can spin up a tiny local server and catch the redirect automatically.
TikTok's OAuth does not support that: every redirect_uri must be an absolute HTTPS URL that is
pre-registered in the TikTok for Developers portal for your app (see
https://developers.tiktok.com/doc/login-kit-web) -- a bare localhost URL is not accepted.

The practical fix, and what this script does: you register a redirect_uri that is any page on a
domain you already control (for example `https://<your-domain>/tiktok-callback`) -- it does not
need to run any server-side code, it only needs to exist so the browser lands somewhere after you
approve access instead of showing a broken-page error. After approving, TikTok redirects your
browser there with `?code=...&state=...` in the address bar -- you copy that full URL and paste it
back into this script when prompted. This is the same manual "authorization code" pattern used by
many CLI tools for OAuth providers that don't support a localhost redirect.

Prereqs (one-time, per TikTok account):
  1. Register an app at https://developers.tiktok.com/ (TikTok for Developers).
  2. Add the "Content Posting API" product to that app, and request/get approval for the
     `video.publish` scope (see https://developers.tiktok.com/doc/content-posting-api-get-started).
     NOTE: until your app passes TikTok's own audit, every post made through it is forced to
     private/self-only visibility, regardless of what this tool requests -- see
     auth/publish_tiktok.py's module docstring and the publish-tiktok skill for the full
     implication and the manual per-video workaround.
  3. Add a Login Kit redirect URI: any HTTPS page on a domain you control (must be added in the
     app's Login Kit configuration before it will be accepted).
  4. Note your Client Key and Client Secret from the app's "Basic Information" page.

Run:
    python -m auth.setup_tiktok_oauth --client-secrets path/to/tiktok_client.json

where that JSON file looks like:
    {
      "client_key": "aw...",
      "client_secret": "...",
      "redirect_uri": "https://your-domain.example/tiktok-callback"
    }

Opens your default browser to TikTok's real authorization screen (not automated -- you approve it
yourself, same as any app requesting TikTok access). After you approve and land on your
redirect_uri, paste the full resulting URL back into this script. On success, the token is saved
to profiles/tiktok/token.json.

SCOPES below must match auth.publish_tiktok.SCOPES exactly, or a stale/mismatched token can behave
unpredictably against a re-scoped app. If you change the scope your app requests, delete
profiles/tiktok/token.json and re-run this script.

Honesty note: this integration follows TikTok's publicly documented Content Posting API and OAuth
flow (https://developers.tiktok.com/doc/content-posting-api-get-started,
https://developers.tiktok.com/doc/oauth-user-access-token-management) as of when this was written,
but has not been exercised against a live TikTok developer app -- some details (exact PKCE
parameter names on the authorization request, precise chunk-size limits) were not fully confirmed
against TikTok's own docs and may need adjusting the first time this actually runs. Treat the
first real run as a live test, not a guaranteed-working integration.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import secrets
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

# Must match auth.publish_tiktok.SCOPES exactly -- see that module's docstring for why.
SCOPES = ["video.publish"]

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CLIENT_SECRETS = REPO_ROOT / "profiles" / "tiktok" / "client_secret.json"
TOKEN_PATH = REPO_ROOT / "profiles" / "tiktok" / "token.json"

AUTHORIZE_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"


def _load_client_config(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(
            f"Client config file not found: {path}\n\n"
            "Create one from your TikTok for Developers app (Basic Information page for "
            "client_key/client_secret, Login Kit page for the redirect_uri you registered "
            "there), then either pass --client-secrets or place it at "
            f"{DEFAULT_CLIENT_SECRETS}. See this module's docstring for the exact JSON shape."
        )
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        raise SystemExit(f"Could not read/parse {path}: {e}") from e

    missing = [k for k in ("client_key", "client_secret", "redirect_uri") if not config.get(k)]
    if missing:
        raise SystemExit(f"{path} is missing required field(s): {', '.join(missing)}")
    return config


def _make_pkce_pair() -> tuple[str, str]:
    """RFC 7636 PKCE. TikTok's token-exchange docs say `code_verifier` is required for desktop
    apps but don't spell out the authorization-request parameter names for the challenge side --
    this follows the RFC 7636 standard (S256) that essentially every OAuth 2.0 provider that
    supports PKCE implements the same way."""
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).rstrip(b"=").decode("ascii")
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode("ascii")).digest()
    ).rstrip(b"=").decode("ascii")
    return verifier, challenge


def _build_authorize_url(client_key: str, redirect_uri: str, state: str, code_challenge: str) -> str:
    params = {
        "client_key": client_key,
        "scope": ",".join(SCOPES),
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


def _extract_code(redirected_url: str, expected_state: str) -> str:
    parsed = urlparse(redirected_url.strip())
    query = parse_qs(parsed.query)

    if "error" in query:
        raise SystemExit(
            f"TikTok returned an error instead of a code: {query.get('error')} "
            f"{query.get('error_description', [''])[0]}"
        )

    code = query.get("code", [None])[0]
    if not code:
        raise SystemExit(
            "Could not find a 'code' parameter in the URL you pasted. Make sure you copied the "
            "FULL address-bar URL from right after TikTok redirected you, not the TikTok "
            "authorization page's own URL."
        )

    state = query.get("state", [None])[0]
    if state != expected_state:
        raise SystemExit(
            "The 'state' parameter in the pasted URL does not match what this run sent -- "
            "refusing to continue (this check exists to catch a stale/copy-pasted URL from a "
            "previous attempt, or a mixed-up authorization flow). Re-run this command fresh."
        )
    return code


def _exchange_code_for_token(
    client_key: str, client_secret: str, code: str, redirect_uri: str, code_verifier: str
) -> dict:
    import urllib.error
    import urllib.request

    body = urlencode(
        {
            "client_key": client_key,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
        }
    ).encode("ascii")

    req = urllib.request.Request(
        TOKEN_URL,
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Token exchange failed ({e.code}): {detail}") from e

    if "access_token" not in payload:
        raise SystemExit(f"Token exchange did not return an access_token. Response: {payload}")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="One-time TikTok OAuth setup")
    parser.add_argument(
        "--client-secrets",
        default=str(DEFAULT_CLIENT_SECRETS),
        help=f"Path to a JSON file with client_key/client_secret/redirect_uri "
        f"(default: {DEFAULT_CLIENT_SECRETS})",
    )
    args = parser.parse_args()

    client_secrets_path = Path(args.client_secrets).expanduser()
    config = _load_client_config(client_secrets_path)

    state = secrets.token_urlsafe(24)
    verifier, challenge = _make_pkce_pair()
    auth_url = _build_authorize_url(config["client_key"], config["redirect_uri"], state, challenge)

    print("\nOpening your default browser to TikTok's authorization page.")
    print("Log in and approve access yourself -- this is not automated.")
    print(f"If the browser doesn't open automatically, visit this URL:\n\n{auth_url}\n")
    webbrowser.open(auth_url)

    print(
        f"After you approve, TikTok redirects you to {config['redirect_uri']} with a code in "
        "the address bar."
    )
    redirected_url = input("Paste the FULL URL you land on here, then press Enter:\n> ").strip()

    code = _extract_code(redirected_url, expected_state=state)
    token = _exchange_code_for_token(
        client_key=config["client_key"],
        client_secret=config["client_secret"],
        code=code,
        redirect_uri=config["redirect_uri"],
        code_verifier=verifier,
    )

    token["obtained_at"] = datetime.now(timezone.utc).isoformat()
    token["scopes"] = SCOPES

    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(json.dumps(token, indent=2), encoding="utf-8")

    # auth/publish_tiktok.py's token-refresh step reads the client secret from exactly
    # DEFAULT_CLIENT_SECRETS -- it has no way to know where --client-secrets originally pointed.
    # Without this, following the documented `--client-secrets path/to/tiktok_client.json` form
    # with a file outside profiles/tiktok/ works for the initial token exchange above, but every
    # refresh after the access token expires fails once it can't find the secret at the hardcoded
    # path. Copy it to the default location too (unless it's already there) so refresh always
    # works regardless of where the source file lives.
    client_secrets_resolved = client_secrets_path.resolve()
    if client_secrets_resolved != DEFAULT_CLIENT_SECRETS.resolve():
        DEFAULT_CLIENT_SECRETS.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_CLIENT_SECRETS.write_text(
            json.dumps(config, indent=2), encoding="utf-8"
        )
        print(f"Client secret also copied to {DEFAULT_CLIENT_SECRETS} (used for token refresh).")

    print(f"\nToken saved to {TOKEN_PATH}")
    print("TikTok publish should now work: python -m auth.publish_tiktok ...")
    print(
        "\nReminder: until your app passes TikTok's own audit, every post is forced to "
        "private/self-only regardless of what you request -- see the publish-tiktok skill for "
        "how to make a post public afterward from inside the TikTok app."
    )


if __name__ == "__main__":
    main()
