"""Post to Bluesky using a saved login session from the platform-login wizard.

Like X and Instagram, this does NOT hit automation-detection blocking --
verified working via Playwright + a saved session, including with an
attached video, in live testing this session.

Requires: `python -m auth.login_wizard --platform bluesky` already run
successfully (profiles/bluesky/ must exist with a logged-in session).

Bluesky limits: ~300 graphemes per post (emoji count as 1, unlike X's
weighted count; URLs count their full literal length). Video: ~60s / 50MB.

Safe by default: this validates and returns without touching a browser unless you pass
`--confirm-publish` (CLI) or `confirm_publish=True` (library call). `--dry-run` is an explicit,
equivalent way to request the same validate-only behavior, and always wins if both are passed.

Usage:
    python -m auth.publish_bluesky "post text" --video path/to/video.mp4 --confirm-publish
    python -m auth.publish_bluesky "post text" --image path/to/photo.jpg --confirm-publish
    python -m auth.publish_bluesky "post text" --dry-run   # validate only -- also the default
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from auth.chrome_setup import ensure_chrome_installed
from auth.login_wizard import PROFILES_DIR
from auth.publish_safety import NOT_PUBLISHED_NOTE, should_publish

STEP_TIMEOUT_MS = 30_000


def publish_bluesky(
    text: str,
    video_path: str = "",
    image_path: str = "",
    dry_run: bool = False,
    confirm_publish: bool = False,
) -> dict:
    do_publish = should_publish(dry_run=dry_run, confirm_publish=confirm_publish)

    if not text.strip():
        raise SystemExit("Post text is required.")
    if video_path and image_path:
        raise SystemExit("Pass either --video or --image, not both.")

    media_file = None
    media_type = None
    if video_path:
        media_file = Path(video_path).expanduser().resolve()
        media_type = "video"
    elif image_path:
        media_file = Path(image_path).expanduser().resolve()
        media_type = "image"
    if media_file and not media_file.is_file():
        raise SystemExit(f"{media_type}_path not found: {media_file}")

    profile_dir = PROFILES_DIR / "bluesky"
    session_exists = profile_dir.exists()

    if not do_publish:
        return {
            "dry_run": True,
            "platform": "bluesky",
            "text": text,
            "media_type": media_type,
            "media": str(media_file) if media_file else None,
            "session_found": session_exists,
            "message": (
                (NOT_PUBLISHED_NOTE if not dry_run else "Dry run requested explicitly.")
                + (
                    " No browser was launched, nothing was posted."
                    if session_exists
                    else " Also: no saved Bluesky session was found -- "
                    "run `python -m auth.login_wizard --platform bluesky` before a real post."
                )
            ),
        }

    if not session_exists:
        raise SystemExit(
            "No saved Bluesky session found. Run "
            "`python -m auth.login_wizard --platform bluesky` first."
        )

    ensure_chrome_installed()

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            channel="chrome",
            headless=False,
        )
        page = context.pages[0] if context.pages else context.new_page()

        try:
            page.goto("https://bsky.app", timeout=STEP_TIMEOUT_MS)
            page.wait_for_timeout(1500)

            page.locator('[aria-label="Compose new post"]').first.click()
            page.wait_for_timeout(1000)

            editor = page.locator('div[contenteditable="true"]').first
            editor.click()
            page.wait_for_timeout(500)
            # Real keystrokes, not fill() -- fill() doesn't fire the input events
            # Bluesky's URL-facet/link-card detector listens for.
            page.keyboard.type(text, delay=15)
            page.wait_for_timeout(500)

            if media_file:
                # Use expect_file_chooser to intercept the file chooser Playwright-side --
                # without this, the click can fall through to a REAL native OS file
                # dialog (confirmed live 2026-08-08: it opened Explorer to an unrelated
                # directory, and the whole flow silently died once the context closed
                # with that orphaned dialog still open).
                with page.expect_file_chooser(timeout=10_000) as fc_info:
                    page.locator('[aria-label="Add media to post"]').first.click()
                fc_info.value.set_files(str(media_file))

                if media_type == "video":
                    # Video shows "Uploading video..." during upload, THEN briefly
                    # "Processing video..." -- confirmed live that checking only for
                    # "Processing video" is wrong: the wait-loop exited immediately
                    # during the "Uploading" phase (that text never matched), the code
                    # moved on, and the resulting post shipped without checking upload
                    # actually finished (it happened to still work by luck once, then
                    # failed silently the next time). Wait for BOTH to clear.
                    for _ in range(30):
                        uploading = page.get_by_text("Uploading video", exact=False).count()
                        processing = page.get_by_text("Processing video", exact=False).count()
                        if uploading == 0 and processing == 0:
                            break
                        page.wait_for_timeout(2000)
                    page.wait_for_timeout(1000)
                else:
                    # Images attach near-instantly -- just give the thumbnail a
                    # moment to render before checking the publish button.
                    page.wait_for_timeout(1500)

            publish_btn = page.get_by_test_id("composerPublishBtn")
            if publish_btn.count() == 0:
                publish_btn = page.locator('[aria-label="Publish post"]')
            if publish_btn.first.is_disabled():
                raise RuntimeError(
                    "Publish button is disabled -- likely over the 300-grapheme limit "
                    "or media still processing. Check the browser window."
                )
            publish_btn.first.click()
            page.wait_for_timeout(2000)

            result = {
                "dry_run": False,
                "platform": "bluesky",
                "status": "posted",
                "text": text,
                "media_type": media_type,
                "verify_note": "Verify independently via the public API (no auth needed): "
                "curl https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed"
                "?actor=<handle>&limit=1",
            }
        finally:
            context.close()

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Post to Bluesky")
    parser.add_argument("text")
    parser.add_argument("--video", default="", help="Optional path to a video to attach")
    parser.add_argument("--image", default="", help="Optional path to an image to attach")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Explicitly validate only -- this is also the default with no flags at all.",
    )
    parser.add_argument(
        "--confirm-publish",
        action="store_true",
        help="Required to actually post for real. Without it, this only validates.",
    )
    args = parser.parse_args()

    result = publish_bluesky(
        args.text,
        video_path=args.video,
        image_path=args.image,
        dry_run=args.dry_run,
        confirm_publish=args.confirm_publish,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
