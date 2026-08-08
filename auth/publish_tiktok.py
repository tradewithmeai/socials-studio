"""Upload a video to TikTok via the OAuth-authorized Content Posting API.

IMPORTANT -- read before you call this "publish": this uploads to the authorized account's TikTok
**inbox as a draft**. Nothing is auto-published. You (a human) open the TikTok app, tap the inbox
notification, add the caption/sound/cover, and publish it yourself. This is deliberate -- it's the
`video.upload` scope, which only needs TikTok's base app review; the full Content Posting API audit
(needed for direct, fully-automated publish) is a separate, heavier approval process TikTok grants
per app.

Requires: `python -m auth.setup_tiktok_oauth` already run successfully
(profiles/tiktok/token.json must exist).

Usage:
    python -m auth.publish_tiktok <video_path>
    python -m auth.publish_tiktok <video_path> --dry-run
    python -m auth.publish_tiktok --status <publish_id>
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOKEN_PATH = REPO_ROOT / "profiles" / "tiktok" / "token.json"

TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
INIT_URL = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"
STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"

MAX_SINGLE_CHUNK = 64 * 1024 * 1024  # TikTok single-PUT ceiling


def _load_token() -> dict:
    if not TOKEN_PATH.is_file():
        raise FileNotFoundError(
            f"No TikTok token found at {TOKEN_PATH}\n"
            "Run: python -m auth.setup_tiktok_oauth --client-key ... --client-secret ..."
        )
    return json.loads(TOKEN_PATH.read_text())


def _access_token(token: dict) -> str:
    import requests

    if int(time.time()) < int(token.get("expires_at", 0)) - 60:
        return token["access_token"]
    if not token.get("refresh_token"):
        raise SystemExit("Access token expired and no refresh_token. Re-run auth.setup_tiktok_oauth.")

    resp = requests.post(TOKEN_URL, data={
        "client_key": token["client_key"],
        "client_secret": token["client_secret"],
        "grant_type": "refresh_token",
        "refresh_token": token["refresh_token"],
    }, headers={"Content-Type": "application/x-www-form-urlencoded"})
    data = resp.json()
    if "access_token" not in data:
        raise SystemExit(f"Token refresh failed:\n{json.dumps(data, indent=2)}")

    now = int(time.time())
    token["access_token"] = data["access_token"]
    token["refresh_token"] = data.get("refresh_token", token["refresh_token"])
    token["expires_at"] = now + int(data.get("expires_in", 86400))
    TOKEN_PATH.write_text(json.dumps(token, indent=2), encoding="utf-8")
    return token["access_token"]


def check_status(publish_id: str) -> dict:
    import requests

    access = _access_token(_load_token())
    resp = requests.post(STATUS_URL, headers={
        "Authorization": f"Bearer {access}",
        "Content-Type": "application/json; charset=UTF-8",
    }, json={"publish_id": publish_id})
    return resp.json()


def publish_tiktok(video_path: str, dry_run: bool = False) -> dict:
    video_file = Path(video_path).expanduser().resolve()
    if not video_file.is_file():
        raise SystemExit(f"video_path not found: {video_file}")

    size = video_file.stat().st_size
    token_exists = TOKEN_PATH.is_file()

    if dry_run:
        return {
            "dry_run": True,
            "platform": "tiktok",
            "would_upload_to_inbox": str(video_file),
            "video_size_mb": round(size / 1e6, 1),
            "token_found": token_exists,
            "size_ok": size <= MAX_SINGLE_CHUNK,
            "message": (
                "Inputs are valid; no API call was made, nothing was uploaded. "
                "Remember: this uploads to the inbox as a draft, not a live post -- "
                "you finish publishing by hand in the TikTok app."
                if token_exists and size <= MAX_SINGLE_CHUNK
                else "Not ready: "
                + ("no saved token -- run auth.setup_tiktok_oauth first. " if not token_exists else "")
                + (f"video is {size/1e6:.1f}MB, over the 64MB single-chunk ceiling. " if size > MAX_SINGLE_CHUNK else "")
            ),
        }

    if not token_exists:
        raise SystemExit("No saved TikTok token found. Run `python -m auth.setup_tiktok_oauth` first.")
    if size > MAX_SINGLE_CHUNK:
        raise SystemExit(
            f"Video is {size/1e6:.1f}MB (>64MB single-chunk ceiling). Trim/re-encode first."
        )

    import requests

    token = _load_token()
    access = _access_token(token)

    init_resp = requests.post(INIT_URL, headers={
        "Authorization": f"Bearer {access}",
        "Content-Type": "application/json; charset=UTF-8",
    }, json={"source_info": {
        "source": "FILE_UPLOAD",
        "video_size": size,
        "chunk_size": size,
        "total_chunk_count": 1,
    }})
    init_data = init_resp.json()
    if init_data.get("error", {}).get("code") not in (None, "ok"):
        raise SystemExit(f"Init failed:\n{json.dumps(init_data, indent=2)}")

    upload_url = init_data["data"]["upload_url"]
    publish_id = init_data["data"]["publish_id"]

    put_resp = requests.put(upload_url, data=video_file.read_bytes(), headers={
        "Content-Type": "video/mp4",
        "Content-Range": f"bytes 0-{size - 1}/{size}",
        "Content-Length": str(size),
    })
    if put_resp.status_code not in (200, 201, 206):
        raise SystemExit(f"Upload PUT failed: {put_resp.status_code} {put_resp.text[:300]}")

    return {
        "platform": "tiktok",
        "status": "uploaded_to_inbox",
        "publish_id": publish_id,
        "video_size_mb": round(size / 1e6, 1),
        "message": "Uploaded to your TikTok inbox as a draft. Open the TikTok app -> tap the "
        "inbox notification -> add caption/cover -> publish by hand.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload a video to TikTok's inbox (draft, manual-post)")
    parser.add_argument("video_path", nargs="?")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--status", metavar="PUBLISH_ID", help="Check the status of a prior upload")
    args = parser.parse_args()

    if args.status:
        print(json.dumps(check_status(args.status), indent=2))
        return

    if not args.video_path:
        raise SystemExit("Usage: python -m auth.publish_tiktok <video_path> [--dry-run]")

    result = publish_tiktok(args.video_path, dry_run=args.dry_run)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
