"""One-time YouTube OAuth setup -- run this instead of the login wizard.

YouTube doesn't go through auth/login_wizard.py: Google actively detects and
blocks sign-in attempts from automation-controlled browsers ("This browser
or app may not be secure"), confirmed live against this exact tool. OAuth +
the YouTube Data API is the correct, Google-sanctioned integration path --
no browser automation involved.

Prereqs (one-time, per Google account -- this is how every third-party
YouTube tool works, there's no way around it):
  1. Create a Google Cloud project: https://console.cloud.google.com/
  2. Enable the "YouTube Data API v3" for that project.
  3. Create OAuth client credentials, type "Desktop app".
  4. Download the client secret JSON Google gives you.

Run:
    python -m auth.setup_youtube_oauth --client-secrets path/to/client_secret.json

Opens a browser to Google's real consent screen (not automated -- you click
through it yourself, same as installing any app that wants YouTube access).
On approval, the resulting token is saved to profiles/youtube/token.json.
"""

from __future__ import annotations

import argparse
from pathlib import Path

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube",
]

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CLIENT_SECRETS = REPO_ROOT / "profiles" / "youtube" / "client_secret.json"
TOKEN_PATH = REPO_ROOT / "profiles" / "youtube" / "token.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="One-time YouTube OAuth setup")
    parser.add_argument(
        "--client-secrets",
        default=str(DEFAULT_CLIENT_SECRETS),
        help=f"Path to the client secret JSON downloaded from Google Cloud Console "
        f"(default: {DEFAULT_CLIENT_SECRETS})",
    )
    args = parser.parse_args()

    client_secrets_path = Path(args.client_secrets).expanduser()
    if not client_secrets_path.is_file():
        raise SystemExit(
            f"Client secrets file not found: {client_secrets_path}\n\n"
            "Create one at https://console.cloud.google.com/ (APIs & Services -> "
            "Credentials -> Create OAuth client ID -> Desktop app), download it, "
            f"then either pass --client-secrets or place it at {DEFAULT_CLIENT_SECRETS}"
        )

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        raise SystemExit("Run: pip install google-auth-oauthlib google-api-python-client")

    flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets_path), scopes=SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")

    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    print(f"\nToken saved to {TOKEN_PATH}")
    print("YouTube publish should now work: python -m auth.publish_youtube ...")


if __name__ == "__main__":
    main()
