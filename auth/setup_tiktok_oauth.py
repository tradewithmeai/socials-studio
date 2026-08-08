"""One-time TikTok OAuth setup -- run this instead of the login wizard.

Like YouTube, TikTok publish does NOT go through auth/login_wizard.py. TikTok's officially
supported integration path for posting video is the Content Posting API (OAuth), not a browser
session -- so this mirrors the YouTube OAuth setup, not the TikTok browser-login entry in
auth/platforms.py (that entry exists for a possible future login-only use, not for publishing).

Scope used here is `video.upload` -- the "upload to inbox" lane. This needs only the base TikTok
app review, not the full Content Posting API audit. It does NOT auto-publish (see
auth/publish_tiktok.py for exactly what that means).

Prereqs (one-time, per TikTok account):
  1. Create a TikTok developer app: https://developers.tiktok.com/
  2. Add "Login Kit" and "Content Posting API" products to the app.
  3. Enable the `video.upload` scope.
  4. Set the app's Redirect URI to EXACTLY http://localhost:8721/callback
  5. Note the app's client_key and client_secret.

Run:
    python -m auth.setup_tiktok_oauth --client-key <key> --client-secret <secret>
or set TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET env vars and run with no args.

Opens a browser to TikTok's real consent screen (not automated). On approval,
profiles/tiktok/token.json is written.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import http.server
import json
import os
import secrets
import threading
import time
import urllib.parse
import webbrowser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOKEN_PATH = REPO_ROOT / "profiles" / "tiktok" / "token.json"

REDIRECT_HOST = "localhost"
REDIRECT_PORT = 8721
REDIRECT_URI = f"http://{REDIRECT_HOST}:{REDIRECT_PORT}/callback"

# user.info.basic = identify the account; video.upload = push videos to the inbox as drafts.
SCOPES = "user.info.basic,video.upload"

AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"

_result: dict = {}


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return
        q = urllib.parse.parse_qs(parsed.query)
        _result["code"] = q.get("code", [None])[0]
        _result["state"] = q.get("state", [None])[0]
        _result["error"] = q.get("error_description", q.get("error", [None]))[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        ok = bool(_result.get("code"))
        msg = "TikTok authorisation complete -- you can close this tab." if ok \
            else f"Authorisation failed: {_result.get('error')}"
        self.wfile.write(f"<html><body style='font-family:sans-serif'><h2>{msg}</h2></body></html>".encode())

    def log_message(self, *_a):
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="One-time TikTok OAuth setup")
    parser.add_argument("--client-key", default=os.getenv("TIKTOK_CLIENT_KEY", ""))
    parser.add_argument("--client-secret", default=os.getenv("TIKTOK_CLIENT_SECRET", ""))
    args = parser.parse_args()

    ck, cs = args.client_key, args.client_secret
    if not ck or not cs:
        raise SystemExit(
            "TikTok client_key / client_secret not found.\n"
            "Pass --client-key/--client-secret, or set TIKTOK_CLIENT_KEY / "
            "TIKTOK_CLIENT_SECRET env vars. Get these from your TikTok developer app."
        )

    try:
        import requests
    except ImportError:
        raise SystemExit("Run: pip install requests")

    # PKCE (TikTok's web auth flow requires a code challenge).
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(48)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    state = secrets.token_urlsafe(16)

    url = AUTH_URL + "?" + urllib.parse.urlencode({
        "client_key": ck,
        "scope": SCOPES,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    })

    server = http.server.HTTPServer((REDIRECT_HOST, REDIRECT_PORT), _Handler)
    threading.Thread(target=server.handle_request, daemon=True).start()

    print("Opening the TikTok consent screen in your browser...")
    print("If it doesn't open, paste this into a browser:\n" + url + "\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass

    for _ in range(300):  # wait up to 5 min for the redirect
        if _result.get("code") or _result.get("error"):
            break
        time.sleep(1)
    try:
        server.server_close()
    except Exception:
        pass

    if _result.get("error") or not _result.get("code"):
        raise SystemExit(f"Authorisation failed: {_result.get('error') or 'no code returned'}")
    if _result.get("state") != state:
        raise SystemExit("State mismatch -- aborting for safety.")

    resp = requests.post(TOKEN_URL, data={
        "client_key": ck,
        "client_secret": cs,
        "code": _result["code"],
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code_verifier": verifier,
    }, headers={"Content-Type": "application/x-www-form-urlencoded"})
    data = resp.json()
    if "access_token" not in data:
        raise SystemExit(f"Token exchange failed:\n{json.dumps(data, indent=2)}")

    now = int(time.time())
    token = {
        "access_token": data["access_token"],
        "refresh_token": data.get("refresh_token", ""),
        "expires_at": now + int(data.get("expires_in", 86400)),
        "refresh_expires_at": now + int(data.get("refresh_expires_in", 31536000)),
        "open_id": data.get("open_id", ""),
        "scope": data.get("scope", SCOPES),
        "client_key": ck,
        "client_secret": cs,
    }
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(json.dumps(token, indent=2), encoding="utf-8")
    print(f"\nToken saved to {TOKEN_PATH}")
    print("open_id:", token["open_id"], "| scope:", token["scope"])
    print("TikTok publish should now work: python -m auth.publish_tiktok ...")


if __name__ == "__main__":
    main()
