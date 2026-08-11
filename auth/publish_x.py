"""Post to X (Twitter) using a saved login session from the platform-login wizard.

Like Instagram, this does NOT hit Google-style automated-browser blocking -- verified working via
Playwright + a saved session in live testing, including with an attached video.

Requires: `python -m auth.login_wizard --platform x` already run successfully
(profiles/x/ must exist with a logged-in session).

Safe by default: this validates and returns without touching a browser unless you pass
`--confirm-publish` (CLI) or `confirm_publish=True` (library call). `--dry-run` is an explicit,
equivalent way to request the same validate-only behavior, and always wins if both are passed.

Usage:
    python -m auth.publish_x "post text" --video path/to/video.mp4 --confirm-publish
    python -m auth.publish_x "post text" --image path/to/photo.jpg --alt-text "..." --confirm-publish
    python -m auth.publish_x "post text" --dry-run   # validate only -- also the default with no flags
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


def _click_post_button(page) -> bool:
    return page.evaluate("""() => {
        const btn = [...document.querySelectorAll('button')]
            .find(b => b.innerText.trim() === 'Post' && !b.disabled);
        if (btn) { btn.click(); return true; }
        return false;
    }""")


def publish_x(
    text: str,
    video_path: str = "",
    image_path: str = "",
    alt_text: str = "",
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
    # X shows an accessibility reminder ("Don't forget to make your image
    # accessible") after the first Post click whenever an image has no alt
    # text, and it blocks the actual submit until handled. Fall back to the
    # post text itself as a description rather than dismissing the prompt.
    if media_type == "image" and not alt_text:
        alt_text = text

    profile_dir = PROFILES_DIR / "x"
    session_exists = profile_dir.exists()

    if not do_publish:
        return {
            "dry_run": True,
            "platform": "x",
            "text": text,
            "media_type": media_type,
            "media": str(media_file) if media_file else None,
            "session_found": session_exists,
            "message": (
                (NOT_PUBLISHED_NOTE if not dry_run else "Dry run requested explicitly.")
                + (
                    " No browser was launched, nothing was posted."
                    if session_exists
                    else " Also: no saved X session was found -- "
                    "run `python -m auth.login_wizard --platform x` before a real post."
                )
            ),
        }

    if not session_exists:
        raise SystemExit("No saved X session found. Run `python -m auth.login_wizard --platform x` first.")

    ensure_chrome_installed()

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            channel="chrome",
            headless=False,
        )
        page = context.pages[0] if context.pages else context.new_page()

        try:
            page.goto("https://x.com/compose/post", timeout=STEP_TIMEOUT_MS)
            page.wait_for_timeout(1500)

            editor = page.locator('[role="dialog"] div[role="textbox"]').first
            if editor.count() == 0:
                editor = page.locator('div[role="textbox"]').first
            editor.click()
            page.wait_for_timeout(1000)
            page.keyboard.type(text, delay=15)
            page.wait_for_timeout(500)

            if media_file:
                # Do NOT click the hidden <input type="file"> via JS first --
                # confirmed live: a raw .click() on a real file input opens the
                # actual native OS file-picker dialog, completely outside
                # Playwright's control (same failure mode documented for
                # Bluesky's and LinkedIn's "Add media" buttons). Locator
                # .set_input_files() sets the files directly over CDP and does
                # not need -- and must not be preceded by -- any click at all.
                file_input = page.locator('input[type="file"]')
                file_input.first.set_input_files(str(media_file))
                page.wait_for_timeout(1000)

                if media_type == "video":
                    for _ in range(30):
                        processing = page.get_by_text("Processing", exact=False).count()
                        removable = page.locator('[aria-label*="Remove"]').count()
                        if processing == 0 and removable > 0:
                            break
                        page.wait_for_timeout(2000)
                    page.wait_for_timeout(3000)
                else:
                    # Images process near-instantly -- just wait for the
                    # thumbnail's remove control to confirm attachment.
                    for _ in range(15):
                        if page.locator('[aria-label*="Remove"]').count() > 0:
                            break
                        page.wait_for_timeout(1000)
                    page.wait_for_timeout(1000)

            clicked = _click_post_button(page)
            if not clicked:
                raise RuntimeError(
                    "Could not click Post -- likely over the character limit or a dialog is "
                    "blocking the composer. Check the browser window."
                )
            page.wait_for_timeout(1500)

            # Handle the alt-text/accessibility reminder if it appeared --
            # confirmed live (2026-08-08): this dialog silently blocks the
            # post from ever submitting until "Add description" or "Not this
            # time" is clicked. Always fill in real alt text here.
            add_desc = page.get_by_role("button", name="Add description")
            if add_desc.count() > 0:
                add_desc.first.click()
                page.wait_for_timeout(1000)
                alt_box = page.locator(
                    '[role="dialog"] textarea, [role="dialog"] [contenteditable="true"]'
                ).first
                alt_box.click()
                page.keyboard.type(alt_text, delay=10)
                page.wait_for_timeout(500)
                page.evaluate("""() => {
                    const dlg = document.querySelector('[role="dialog"]');
                    if (!dlg) return false;
                    const btn = [...dlg.querySelectorAll('button')]
                        .find(b => /^(save|done)$/i.test((b.innerText||'').trim()));
                    if (btn) { btn.click(); return true; }
                    return false;
                }""")
                page.wait_for_timeout(1000)

                clicked_again = _click_post_button(page)
                if not clicked_again:
                    raise RuntimeError(
                        "Could not click Post after filling in alt text -- check the browser window."
                    )

            page.wait_for_timeout(4000)
            current_url = page.url
            if "compose" in current_url:
                raise RuntimeError(
                    "Still on the compose page after clicking Post -- it probably did not submit. "
                    "Check for a beforeunload dialog or an over-limit counter."
                )

            result = {
                "dry_run": False,
                "platform": "x",
                "status": "posted",
                "text": text,
                "media_type": media_type,
                "url": None,
                "verify_note": "Navigate to your profile and confirm the post appears; this "
                "script does not scrape the post's own URL back out.",
            }
        finally:
            context.close()

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Post to X (Twitter)")
    parser.add_argument("text")
    parser.add_argument("--video", default="", help="Optional path to a video to attach")
    parser.add_argument("--image", default="", help="Optional path to an image to attach")
    parser.add_argument(
        "--alt-text",
        default="",
        help="Accessibility description for --image; defaults to the post text if omitted",
    )
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

    result = publish_x(
        args.text,
        video_path=args.video,
        image_path=args.image,
        alt_text=args.alt_text,
        dry_run=args.dry_run,
        confirm_publish=args.confirm_publish,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
