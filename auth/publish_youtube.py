"""Upload a video to YouTube via the OAuth-authorized Data API.

This is deliberately NOT browser automation. Google actively detects and
blocks sign-in attempts from automation-controlled browsers ("This browser
or app may not be secure"), confirmed live against this exact tool -- OAuth
+ the YouTube Data API is the correct, Google-sanctioned integration path.

Requires: `python -m auth.setup_youtube_oauth` already run successfully
(profiles/youtube/token.json must exist).

Usage:
    python -m auth.publish_youtube <video_path> --title "..." --description "..." \
        --visibility private
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

# Must match auth.setup_youtube_oauth.SCOPES exactly, or token refresh raises
# a "scope has changed" error.
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube",
]

REPO_ROOT = Path(__file__).resolve().parent.parent
TOKEN_PATH = REPO_ROOT / "profiles" / "youtube" / "token.json"

VALID_VISIBILITY = {"private", "unlisted", "public"}


def _load_credentials() -> Any:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    if not TOKEN_PATH.is_file():
        raise FileNotFoundError(
            f"No YouTube token found at {TOKEN_PATH}\n"
            "Run: python -m auth.setup_youtube_oauth --client-secrets path/to/client_secret.json"
        )

    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        try:
            TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
        except OSError:
            pass

    if not creds.valid:
        raise ValueError(
            "YouTube credentials invalid or expired. Run "
            "`python -m auth.setup_youtube_oauth` again to re-authorize."
        )
    return creds


def publish_youtube(
    video_path: str,
    title: str,
    description: str = "",
    tags: str = "",
    visibility: str = "private",
    dry_run: bool = False,
) -> dict:
    if visibility not in VALID_VISIBILITY:
        raise SystemExit(f"visibility must be one of {sorted(VALID_VISIBILITY)}")

    video_file = Path(video_path).expanduser().resolve()
    if not video_file.is_file():
        raise SystemExit(f"video_path not found: {video_file}")

    token_exists = TOKEN_PATH.is_file()

    if dry_run:
        return {
            "dry_run": True,
            "platform": "youtube",
            "would_publish": str(video_file),
            "title": title,
            "description": description,
            "visibility": visibility,
            "token_found": token_exists,
            "message": (
                "Inputs are valid; no API call was made, nothing was uploaded."
                if token_exists
                else "Inputs are valid, but no saved YouTube token was found -- "
                "run `python -m auth.setup_youtube_oauth` before a real publish."
            ),
        }

    creds = _load_credentials()

    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        raise SystemExit(
            "Run: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2"
        )

    youtube = build("youtube", "v3", credentials=creds)

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    body = {
        "snippet": {"title": title, "description": description, "tags": tag_list, "categoryId": "22"},
        "status": {"privacyStatus": visibility},
    }

    media = MediaFileUpload(str(video_file), chunksize=-1, resumable=True)
    insert_req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        _, response = insert_req.next_chunk()

    video_id = response.get("id", "")
    url = f"https://www.youtube.com/watch?v={video_id}" if video_id else None

    return {
        "platform": "youtube",
        "status": "published" if visibility == "public" else visibility,
        "visibility": visibility,
        "url": url,
        "title": title,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish a video to YouTube")
    parser.add_argument("video_path")
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--tags", default="", help="Comma-separated tags, e.g. 'a,b,c'")
    parser.add_argument(
        "--visibility",
        choices=sorted(VALID_VISIBILITY),
        default="private",
        help="Defaults to private -- pass --visibility public explicitly to go live.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs and print what would happen -- no API call, no upload.",
    )
    args = parser.parse_args()

    result = publish_youtube(
        args.video_path,
        title=args.title,
        description=args.description,
        tags=args.tags,
        visibility=args.visibility,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
