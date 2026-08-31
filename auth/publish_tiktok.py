"""Upload a video to TikTok via the OAuth-authorized Content Posting API.

This is deliberately NOT browser automation, for the same reason as auth/publish_youtube.py:
TikTok actively detects and blocks sign-in attempts from automation-controlled browsers. OAuth +
the official Content Posting API (https://developers.tiktok.com/doc/content-posting-api-get-started)
is the correct, TikTok-sanctioned integration path.

Requires: `python -m auth.setup_tiktok_oauth` already run successfully
(profiles/tiktok/token.json must exist).

Safe by default: this validates and returns without calling the API unless you pass
`--confirm-publish` (CLI) or `confirm_publish=True` (library call). `--dry-run` is an explicit,
equivalent way to request the same validate-only behavior, and always wins if both are passed --
same shared gate as every other publisher here, via auth.publish_safety.should_publish.

## The unaudited-app reality -- read this before publishing "publicly"

Every new TikTok app starts "unaudited". Until TikTok's own review team audits and approves your
app, EVERY post made through the Content Posting API is forced to private/self-only visibility --
this tool can request `--visibility public` and TikTok will silently downgrade it, not error.
UNAUDITED_APP_NOTICE below is printed unconditionally on every real-publish attempt so this is
never a surprise discovered after the fact.

The practical workaround, confirmed in TikTok's own Content Sharing Guidelines
(https://developers.tiktok.com/doc/content-sharing-guidelines): the account owner can make a post
public afterward by hand, from inside the TikTok app -- first set the account itself to public (if
it isn't already), then open the specific post and change ITS privacy to "Everyone". This is a
documented, sanctioned path, not a workaround of TikTok's rules -- it just has to happen manually,
per video, until the app passes audit.

Honesty note: this module implements TikTok's publicly documented Content Posting API
(direct-post, FILE_UPLOAD source). It has now been exercised against a live TikTok developer app
and a real upload (2026-08-17): the OAuth flow, token exchange, and post-init/upload/status-fetch
call sequence all work. The first live attempt failed with a 400 "the total chunk count is
invalid" error caused by chunking videos under 64 MiB, which TikTok requires to be sent as a
single chunk -- see MIN_CHUNK_SIZE/MAX_CHUNK_SIZE above for the fix. Chunked upload of videos over
64 MiB has not itself been exercised live yet (the test video was smaller), so treat the first
real upload of a large video as still-unverified for that path specifically.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from auth.publish_safety import NOT_PUBLISHED_NOTE, should_publish

# Must match auth.setup_tiktok_oauth.SCOPES exactly.
SCOPES = ["video.publish"]

REPO_ROOT = Path(__file__).resolve().parent.parent
TOKEN_PATH = REPO_ROOT / "profiles" / "tiktok" / "token.json"

CREATOR_INFO_URL = "https://open.tiktokapis.com/v2/post/publish/creator_info/query/"
VIDEO_INIT_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"
STATUS_FETCH_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"

# Friendly names mapped to TikTok's actual privacy_level values (see
# https://developers.tiktok.com/doc/content-posting-api-reference-direct-post). Default is the
# most restrictive option -- matching what an unaudited app is forced to anyway, and matching the
# "default to private" convention every other publisher in this repo follows.
VISIBILITY_TO_PRIVACY_LEVEL = {
    "private": "SELF_ONLY",
    "followers": "FOLLOWER_OF_CREATOR",
    "friends": "MUTUAL_FOLLOW_FRIENDS",
    "public": "PUBLIC_TO_EVERYONE",
}
VALID_VISIBILITY = set(VISIBILITY_TO_PRIVACY_LEVEL)

# Printed unconditionally on every real-publish attempt -- see module docstring for why this is
# never merely a documentation footnote. Unlike YouTube's UPLOAD_TERMS_NOTICE (a permanent legal
# requirement for every upload forever), this note describes a status (unaudited) that is
# expected to change once the app passes TikTok's review -- it's informational, not a
# confirm-required gate, since gating on it forever would misdescribe an app that has since been
# audited.
UNAUDITED_APP_NOTICE = (
    "Reminder: until this TikTok app passes TikTok's own audit, the connected TikTok account "
    "itself must be set to Private for ANY publish call to succeed at all -- confirmed live "
    "2026-08-17, TikTok returns 403 unaudited_client_can_only_post_to_private_accounts and "
    "uploads nothing if the account is public. This is stricter than just downgrading the "
    "post's own visibility: the account-level Private toggle is a hard prerequisite, checked "
    "before the upload is even accepted. Fix: in the TikTok app, Settings and privacy -> "
    "Privacy -> turn on 'Private account', then retry. Once the app passes audit, the account "
    "owner can set the account back to public and manage each post's own visibility "
    "individually inside the TikTok app."
)

# TikTok's exact error code (in the `error.code` field of a failed init/publish response) when
# the connected account is not set to Private and this app is still unaudited. Used to turn a raw
# API error into an actionable message instead of a bare JSON dump.
UNAUDITED_PRIVATE_ACCOUNT_REQUIRED_CODE = "unaudited_client_can_only_post_to_private_accounts"

# TikTok's Content Posting API chunking rules for FILE_UPLOAD (confirmed live on 2026-08-17,
# after an initial "the total chunk count is invalid" 400 from a naive always-chunk approach):
# videos at or under MAX_CHUNK_SIZE (64 MiB) MUST be sent as exactly ONE chunk -- chunk_size equal
# to the full file size and total_chunk_count == 1. TikTok rejects the init call if a
# small/medium video is split into more than one chunk. Only videos larger than MAX_CHUNK_SIZE are
# split into multiple chunks, each between MIN_CHUNK_SIZE and MAX_CHUNK_SIZE. DEFAULT_CHUNK_SIZE is
# only the per-chunk size used once a video is big enough to require chunking at all -- it has no
# effect on videos under the single-chunk threshold.
MIN_CHUNK_SIZE = 5 * 1024 * 1024  # 5 MiB -- TikTok's documented minimum per chunk
MAX_CHUNK_SIZE = 64 * 1024 * 1024  # 64 MiB -- TikTok's documented maximum per chunk, and also the
# largest video size that must still be sent as a single chunk rather than split at all.
DEFAULT_CHUNK_SIZE = MAX_CHUNK_SIZE


def _load_token() -> dict:
    if not TOKEN_PATH.is_file():
        raise FileNotFoundError(
            f"No TikTok token found at {TOKEN_PATH}\n"
            "Run: python -m auth.setup_tiktok_oauth --client-secrets path/to/tiktok_client.json"
        )
    try:
        return json.loads(TOKEN_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        raise ValueError(f"TikTok token at {TOKEN_PATH} could not be read: {e}") from e


def _refresh_token_if_needed(token: dict) -> dict:
    from datetime import datetime, timedelta, timezone

    obtained_at_raw = token.get("obtained_at")
    expires_in = token.get("expires_in")
    if not obtained_at_raw or expires_in is None:
        return token  # can't tell if it's stale; let the API itself reject it if so

    try:
        obtained_at = datetime.fromisoformat(obtained_at_raw)
    except ValueError:
        return token

    expiry = obtained_at + timedelta(seconds=int(expires_in))
    if datetime.now(timezone.utc) < expiry - timedelta(minutes=2):
        return token  # still fresh, with a small safety margin

    refresh_token = token.get("refresh_token")
    if not refresh_token:
        raise ValueError(
            "TikTok access token has expired and no refresh_token is stored. Re-run "
            "python -m auth.setup_tiktok_oauth to re-authorize."
        )

    client_secrets_path = REPO_ROOT / "profiles" / "tiktok" / "client_secret.json"
    if not client_secrets_path.is_file():
        raise ValueError(
            f"Access token expired and {client_secrets_path} (needed to refresh it) is missing. "
            "Re-run python -m auth.setup_tiktok_oauth."
        )
    client_config = json.loads(client_secrets_path.read_text(encoding="utf-8"))

    import urllib.error
    import urllib.request
    from urllib.parse import urlencode

    body = urlencode(
        {
            "client_key": client_config["client_key"],
            "client_secret": client_config["client_secret"],
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
    ).encode("ascii")
    req = urllib.request.Request(
        TOKEN_URL, data=body, method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            refreshed = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise ValueError(
            f"Refreshing the TikTok token failed ({e.code}): {detail}\n"
            "Re-run python -m auth.setup_tiktok_oauth to re-authorize from scratch."
        ) from e

    if "access_token" not in refreshed:
        raise ValueError(f"Token refresh did not return an access_token. Response: {refreshed}")

    refreshed["obtained_at"] = datetime.now(timezone.utc).isoformat()
    refreshed["scopes"] = token.get("scopes", SCOPES)
    TOKEN_PATH.write_text(json.dumps(refreshed, indent=2), encoding="utf-8")
    return refreshed


def _api_post_json(url: str, access_token: str, body: dict) -> dict:
    import urllib.error
    import urllib.request

    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        try:
            error_code = json.loads(detail).get("error", {}).get("code")
        except (json.JSONDecodeError, AttributeError):
            error_code = None
        if error_code == UNAUDITED_PRIVATE_ACCOUNT_REQUIRED_CODE:
            raise RuntimeError(
                "TikTok rejected this publish because the connected account is not set to "
                "Private. Until this app passes TikTok's audit, the account itself must be "
                "Private for any publish call to succeed -- go to the TikTok app, Settings and "
                "privacy -> Privacy -> turn on 'Private account', then retry. "
                f"(Raw TikTok error: {detail})"
            ) from e
        raise RuntimeError(f"TikTok API call to {url} failed ({e.code}): {detail}") from e


def _compute_chunking(total_size: int, chunk_size: int) -> tuple[int, int]:
    """Return (effective_chunk_size, total_chunk_count) per TikTok's FILE_UPLOAD rules.

    Videos at or under MAX_CHUNK_SIZE MUST be a single chunk -- TikTok's init endpoint rejects
    the request with "the total chunk count is invalid" otherwise (confirmed live 2026-08-17).
    Only videos larger than that are split, using chunk_size clamped to
    [MIN_CHUNK_SIZE, MAX_CHUNK_SIZE].
    """
    if total_size <= MAX_CHUNK_SIZE:
        return total_size, 1
    effective_chunk = min(max(chunk_size, MIN_CHUNK_SIZE), MAX_CHUNK_SIZE)
    total_chunk_count = -(-total_size // effective_chunk)  # ceil division
    return effective_chunk, total_chunk_count


def _upload_video_chunks(upload_url: str, video_file: Path, chunk_size: int, total_size: int) -> None:
    import urllib.error
    import urllib.request

    with video_file.open("rb") as f:
        offset = 0
        while offset < total_size:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            last_byte = offset + len(chunk) - 1
            req = urllib.request.Request(
                upload_url,
                data=chunk,
                method="PUT",
                headers={
                    "Content-Type": "video/mp4",
                    "Content-Length": str(len(chunk)),
                    "Content-Range": f"bytes {offset}-{last_byte}/{total_size}",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=120):
                    pass
            except urllib.error.HTTPError as e:
                detail = e.read().decode("utf-8", errors="replace")
                raise RuntimeError(
                    f"TikTok chunk upload failed at bytes {offset}-{last_byte} ({e.code}): {detail}"
                ) from e
            offset += len(chunk)


def publish_tiktok(
    video_path: str,
    title: str = "",
    visibility: str = "private",
    dry_run: bool = False,
    confirm_publish: bool = False,
    disable_duet: bool = False,
    disable_stitch: bool = False,
    disable_comment: bool = False,
    is_aigc: bool = False,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> dict:
    do_publish = should_publish(dry_run=dry_run, confirm_publish=confirm_publish)

    if visibility not in VALID_VISIBILITY:
        raise SystemExit(f"visibility must be one of {sorted(VALID_VISIBILITY)}")

    video_file = Path(video_path).expanduser().resolve()
    if not video_file.is_file():
        raise SystemExit(f"video_path not found: {video_file}")

    token_exists = TOKEN_PATH.is_file()
    privacy_level = VISIBILITY_TO_PRIVACY_LEVEL[visibility]

    if not do_publish:
        return {
            "dry_run": True,
            "platform": "tiktok",
            "would_publish": str(video_file),
            "title": title,
            "visibility": visibility,
            "privacy_level": privacy_level,
            "token_found": token_exists,
            "message": (
                (NOT_PUBLISHED_NOTE if not dry_run else "Dry run requested explicitly.")
                + (
                    " No API call was made, nothing was uploaded."
                    if token_exists
                    else " Also: no saved TikTok token was found -- "
                    "run `python -m auth.setup_tiktok_oauth` before a real publish."
                )
                + " " + UNAUDITED_APP_NOTICE
            ),
        }

    # Printed unconditionally, before any credentials are touched -- see module docstring and
    # UNAUDITED_APP_NOTICE's own comment for why this is informational rather than a required
    # acknowledgment flag (unlike YouTube's permanent legal disclosures).
    print(f"\n{UNAUDITED_APP_NOTICE}\n")

    token = _load_token()
    token = _refresh_token_if_needed(token)
    access_token = token["access_token"]

    total_size = video_file.stat().st_size
    effective_chunk, total_chunk_count = _compute_chunking(total_size, chunk_size)

    init_body = {
        "post_info": {
            "title": title,
            "privacy_level": privacy_level,
            "disable_duet": disable_duet,
            "disable_stitch": disable_stitch,
            "disable_comment": disable_comment,
            "is_aigc": is_aigc,
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": total_size,
            "chunk_size": effective_chunk,
            "total_chunk_count": total_chunk_count,
        },
    }
    init_response = _api_post_json(VIDEO_INIT_URL, access_token, init_body)
    error = init_response.get("error", {})
    if error.get("code") not in (None, "ok"):
        raise RuntimeError(f"TikTok rejected the post init request: {error}")

    data = init_response.get("data", {})
    publish_id = data.get("publish_id")
    upload_url = data.get("upload_url")
    if not publish_id or not upload_url:
        raise RuntimeError(f"TikTok init response missing publish_id/upload_url: {init_response}")

    _upload_video_chunks(upload_url, video_file, effective_chunk, total_size)

    status_response = _api_post_json(STATUS_FETCH_URL, access_token, {"publish_id": publish_id})

    return {
        "dry_run": False,
        "platform": "tiktok",
        "status": "uploaded",
        "visibility": visibility,
        "privacy_level": privacy_level,
        "publish_id": publish_id,
        "title": title,
        "status_response": status_response,
        "note": UNAUDITED_APP_NOTICE,
    }


def check_publish_status(publish_id: str) -> dict:
    """Look up the CURRENT status of an already-submitted publish_id, independent of whatever
    was returned right after upload. Added 2026-08-18 after a real publish_id came back
    "PROCESSING_UPLOAD" (a transient state) and the video never actually appeared in the TikTok
    app -- the original code only ever checked status once, immediately after uploading, and
    never found out whether processing later succeeded or failed."""
    token = _load_token()
    token = _refresh_token_if_needed(token)
    status_response = _api_post_json(STATUS_FETCH_URL, token["access_token"], {"publish_id": publish_id})
    return {"publish_id": publish_id, "status_response": status_response}


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish a video to TikTok")
    parser.add_argument("video_path", nargs="?", default=None)
    parser.add_argument(
        "--check-status",
        dest="check_status",
        default=None,
        metavar="PUBLISH_ID",
        help="Look up the current status of an already-submitted publish_id (from a prior run's "
        "'publish_id' field) instead of publishing anything new. video_path is not required "
        "with this flag.",
    )
    parser.add_argument("--title", default="", help="Caption/title, max 2200 UTF-16 code units")
    parser.add_argument(
        "--visibility",
        choices=sorted(VALID_VISIBILITY),
        default="private",
        help="Defaults to private -- pass --visibility public explicitly to request it live. "
        "Forced to private anyway until this app passes TikTok's own audit; see module docstring.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Explicitly validate only -- this is also the default with no flags at all.",
    )
    parser.add_argument(
        "--confirm-publish",
        action="store_true",
        help="Required to actually upload for real. Without it, this only validates.",
    )
    parser.add_argument("--disable-duet", action="store_true")
    parser.add_argument("--disable-stitch", action="store_true")
    parser.add_argument("--disable-comment", action="store_true")
    parser.add_argument(
        "--is-aigc", action="store_true",
        help="Label this video as AI-generated content, per TikTok's disclosure requirements.",
    )
    args = parser.parse_args()

    if args.check_status:
        print(json.dumps(check_publish_status(args.check_status), indent=2))
        return

    if not args.video_path:
        raise SystemExit("video_path is required unless --check-status is given.")

    result = publish_tiktok(
        args.video_path,
        title=args.title,
        visibility=args.visibility,
        dry_run=args.dry_run,
        confirm_publish=args.confirm_publish,
        disable_duet=args.disable_duet,
        disable_stitch=args.disable_stitch,
        disable_comment=args.disable_comment,
        is_aigc=args.is_aigc,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
