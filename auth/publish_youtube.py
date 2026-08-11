"""Upload a video to YouTube via the OAuth-authorized Data API.

This is deliberately NOT browser automation. Google actively detects and
blocks sign-in attempts from automation-controlled browsers ("This browser
or app may not be secure"), confirmed live against this exact tool -- OAuth
+ the YouTube Data API is the correct, Google-sanctioned integration path.

Requires: `python -m auth.setup_youtube_oauth` already run successfully
(profiles/youtube/token.json must exist).

Safe by default: this validates and returns without calling the API unless you pass
`--confirm-publish` (CLI) or `confirm_publish=True` (library call). `--dry-run` is an explicit,
equivalent way to request the same validate-only behavior, and always wins if both are passed.

A real upload additionally requires:
  --made-for-kids / --not-made-for-kids   Exactly one, never both, never defaulted or inferred.
                                    Required by YouTube's API Client policy for third-party
                                    apps: https://developers.google.com/youtube/terms/api-services-terms-of-service
                                    Sent as status.selfDeclaredMadeForKids (true or false).
  --acknowledge-upload-terms        Required by the same policy (Section 9.1). The exact
                                    required notice (UPLOAD_TERMS_NOTICE) is printed
                                    UNCONDITIONALLY on every real-upload attempt -- whether or
                                    not this flag is already set -- so it is never merely
                                    suppressed by the flag; the flag only gates whether the
                                    upload proceeds past that point.

Usage:
    python -m auth.publish_youtube <video_path> --title "..." --description "..." \
        --visibility private --not-made-for-kids --acknowledge-upload-terms --confirm-publish
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from auth.publish_safety import NOT_PUBLISHED_NOTE, should_publish

# Must match auth.setup_youtube_oauth.SCOPES exactly, or token refresh raises a "scope has
# changed" error. Deliberately minimal: youtube.upload is what publishing needs, and
# youtube.readonly is what doctor.py's channel check needs (yt.channels().list(mine=True)).
# The broad "https://www.googleapis.com/auth/youtube" manage scope is NOT requested -- it
# grants read/write access to playlists, comments, and other channel management the code
# here never touches, and per the principle of least privilege there's no reason to ask a
# user for more access than the tool demonstrably uses.
#
# Changing this list requires existing users to re-authorize: delete profiles/youtube/token.json
# and re-run `python -m auth.setup_youtube_oauth`. A token issued under the old scope set will
# fail with a "scope has changed" error on refresh, not silently keep working under new scopes.
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]

REPO_ROOT = Path(__file__).resolve().parent.parent
TOKEN_PATH = REPO_ROOT / "profiles" / "youtube" / "token.json"

VALID_VISIBILITY = {"private", "unlisted", "public"}

# Verbatim text required by the YouTube API Services Terms of Service, Section 9.1(i), for any
# third-party application that lets a user upload video: https://developers.google.com/youtube/terms/api-services-terms-of-service
# The bracketed URL placeholder in the ToS's own text is resolved to the desktop/non-mobile
# variant (this tool has no mobile client): https://www.youtube.com/t/terms
UPLOAD_TERMS_NOTICE = (
    "By clicking 'upload,' you certify that the content you are uploading complies with the "
    "YouTube Terms of Service (including the YouTube Community Guidelines) at "
    "https://www.youtube.com/t/terms. Please be sure not to violate others' copyright or "
    "privacy rights."
)


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
    confirm_publish: bool = False,
    made_for_kids: bool | None = None,
    acknowledge_upload_terms: bool = False,
) -> dict:
    do_publish = should_publish(dry_run=dry_run, confirm_publish=confirm_publish)

    if visibility not in VALID_VISIBILITY:
        raise SystemExit(f"visibility must be one of {sorted(VALID_VISIBILITY)}")

    video_file = Path(video_path).expanduser().resolve()
    if not video_file.is_file():
        raise SystemExit(f"video_path not found: {video_file}")

    token_exists = TOKEN_PATH.is_file()

    if not do_publish:
        return {
            "dry_run": True,
            "platform": "youtube",
            "would_publish": str(video_file),
            "title": title,
            "description": description,
            "visibility": visibility,
            "made_for_kids": made_for_kids,
            "token_found": token_exists,
            "message": (
                (NOT_PUBLISHED_NOTE if not dry_run else "Dry run requested explicitly.")
                + (
                    " No API call was made, nothing was uploaded."
                    if token_exists
                    else " Also: no saved YouTube token was found -- "
                    "run `python -m auth.setup_youtube_oauth` before a real publish."
                )
            ),
        }

    # These two are only enforced once we're actually about to upload -- a dry run should
    # never fail on them, since it's meant to validate everything else regardless. Real
    # requirements from the YouTube API Services Terms of Service, Section 9.1: the upload
    # notice must be shown and acknowledged, and Made for Kids status must be declared, before
    # any upload -- never silently past them. See the module docstring for the exact citation.
    #
    # The notice is printed here UNCONDITIONALLY, before the acknowledgment flag is even
    # checked -- on every real-publish attempt, whether or not --acknowledge-upload-terms was
    # already supplied. This is deliberate: a flag that only prints the notice when it's
    # MISSING can be flipped true on the very first call, and the notice then never appears in
    # that run's output at all. Printing it unconditionally here means it's genuinely part of
    # every real-upload invocation's own output, not something only shown on a prior failure.
    print(f"\n{UPLOAD_TERMS_NOTICE}\n")
    if not acknowledge_upload_terms:
        raise SystemExit(
            "A real upload requires --acknowledge-upload-terms (or "
            "acknowledge_upload_terms=True), confirming the notice printed above was shown "
            "to the user and accepted."
        )
    if made_for_kids is None:
        raise SystemExit(
            "A real upload requires exactly one of --made-for-kids / --not-made-for-kids "
            "(or made_for_kids=True/False), declared before upload as required by YouTube's "
            "API Client policy. This is not optional and never inferred -- see the module "
            "docstring for the policy citation."
        )

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
        "status": {
            "privacyStatus": visibility,
            "selfDeclaredMadeForKids": made_for_kids,
        },
    }

    media = MediaFileUpload(str(video_file), chunksize=-1, resumable=True)
    insert_req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        _, response = insert_req.next_chunk()

    video_id = response.get("id", "")
    url = f"https://www.youtube.com/watch?v={video_id}" if video_id else None

    return {
        "dry_run": False,
        "platform": "youtube",
        "status": "published" if visibility == "public" else visibility,
        "visibility": visibility,
        "made_for_kids": made_for_kids,
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
        help="Explicitly validate only -- this is also the default with no flags at all.",
    )
    parser.add_argument(
        "--confirm-publish",
        action="store_true",
        help="Required to actually upload for real. Without it, this only validates.",
    )
    made_for_kids_group = parser.add_mutually_exclusive_group(required=False)
    made_for_kids_group.add_argument(
        "--made-for-kids",
        dest="made_for_kids",
        action="store_true",
        default=None,
        help="Declare this video as Made for Kids. Required (one of --made-for-kids / "
        "--not-made-for-kids, never both) for a real upload -- YouTube's API Client policy "
        "requires this be declared before upload, never defaulted or inferred. Not required "
        "for --dry-run.",
    )
    made_for_kids_group.add_argument(
        "--not-made-for-kids",
        dest="made_for_kids",
        action="store_false",
        default=None,
        help="Declare this video as NOT Made for Kids. Mutually exclusive with "
        "--made-for-kids; argparse itself rejects passing both.",
    )
    parser.add_argument(
        "--acknowledge-upload-terms",
        action="store_true",
        help="Required for a real upload -- confirms the YouTube-required upload notice "
        "(printed unconditionally by this tool on every real-upload attempt, see "
        "UPLOAD_TERMS_NOTICE) was shown and accepted. Not required for --dry-run.",
    )
    args = parser.parse_args()

    made_for_kids = args.made_for_kids

    result = publish_youtube(
        args.video_path,
        title=args.title,
        description=args.description,
        tags=args.tags,
        visibility=args.visibility,
        dry_run=args.dry_run,
        confirm_publish=args.confirm_publish,
        made_for_kids=made_for_kids,
        acknowledge_upload_terms=args.acknowledge_upload_terms,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
