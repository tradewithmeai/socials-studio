"""Post to Facebook (personal profile timeline) using a saved login session from the
platform-login wizard.

Like X, Bluesky, LinkedIn, and Instagram, this is meant to reuse a session a human already
established -- see `auth/login_wizard.py`'s module docstring for why automated sign-in itself is
never attempted here.

Requires: `python -m auth.login_wizard --platform facebook` already run successfully
(profiles/facebook/ must exist with a logged-in session).

Honesty note: unlike every other publisher in this repo, this one has NOT been exercised against
a live account at all as of 2026-08-18 -- it is a first-draft implementation, written by pattern-
matching Facebook's general composer structure (a modal dialog opened from "What's on your mind?",
a contenteditable text box, a file-chooser-based media attach, a Post button) against the same
shape used successfully for LinkedIn and Bluesky. Every selector below is a best guess, not a
confirmed-live value -- treat the first real run (even a dry run that reaches the browser step) as
the live test of this file, and expect to fix selectors against whatever Facebook's actual DOM
turns out to be. Do not tell a user a Facebook post "should just work" the way X/Bluesky/LinkedIn/
Instagram now can -- say plainly that this is untested and the first attempt is a joint debugging
session, the same honest framing this repo used for TikTok before its first live run.

Safe by default: this validates and returns without touching a browser unless you pass
`--confirm-publish` (CLI) or `confirm_publish=True` (library call). `--dry-run` is an explicit,
equivalent way to request the same validate-only behavior, and always wins if both are passed.
This gate applies identically here even though the browser steps below are unverified -- a dry run
never reaches them.

Usage:
    python -m auth.publish_facebook "post text" --video path/to/video.mp4 --confirm-publish
    python -m auth.publish_facebook "post text" --image path/to/photo.jpg --confirm-publish
    python -m auth.publish_facebook "post text" --dry-run   # validate only -- also the default
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

# How long to wait for an attached video to finish Facebook's own upload/processing before giving
# up on it ever finishing. Modeled on the same class of failure confirmed live for X and Bluesky
# (a fixed short wait was too short for a video with an added audio track) -- start with the same
# generous budget those ended up needing rather than repeating that discovery here from scratch.
VIDEO_PROCESSING_WAIT_ITERATIONS = 150
VIDEO_PROCESSING_WAIT_INTERVAL_MS = 2000


def _save_debug_screenshot(page) -> Path | None:
    """Best-effort screenshot saved BEFORE the calling code raises -- the browser context is
    always closed in a `finally` once this function's `with sync_playwright()` block exits, so
    inspecting the browser after the fact isn't possible. Never raises itself -- a failed
    screenshot must not mask the original error."""
    try:
        path = PROFILES_DIR / "facebook" / "last_failure_screenshot.png"
        page.screenshot(path=str(path))
        return path
    except Exception:
        return None


def _dismiss_cookie_banner(page) -> None:
    """Best-effort, non-fatal: Facebook shows an EU-style cookie consent dialog on a fresh
    profile that can sit on top of the composer. Never raises -- if this selector is wrong, the
    caller's own screenshot-on-failure path is what surfaces that, not this helper."""
    try:
        page.evaluate("""() => {
            const btn = [...document.querySelectorAll('div[role="button"], button')]
                .find(b => /allow all cookies|accept all/i.test((b.innerText || '').trim()));
            if (btn) btn.click();
        }""")
        page.wait_for_timeout(500)
    except Exception:
        pass


def _open_composer(page) -> bool:
    """Click the "What's on your mind?" opener on the home feed. The visible text includes the
    logged-in user's own first name (e.g. "What's on your mind, Alex?"), so this matches on the
    stable leading phrase rather than the full string. Returns whether a click happened -- NOT
    independently confirmed this is still Facebook's actual current markup."""
    return page.evaluate("""() => {
        const el = [...document.querySelectorAll('div[role="button"], span')]
            .find(e => (e.innerText || '').trim().startsWith("What's on your mind"));
        if (!el) return false;
        el.click();
        return true;
    }""")


def _click_dialog_button(page, name: str) -> str:
    """Try to click a button by exact visible text, scoped to the open composer dialog. Returns
    'clicked', 'disabled', or 'not_found' -- mirrors the same three-way result already used in
    publish_x.py, since "found but disabled" (still processing media) and "not found at all" (a
    different failure) need different handling by the caller."""
    return page.evaluate(
        """(name) => {
            const dlg = document.querySelector('[role="dialog"]');
            if (!dlg) return 'not_found';
            const btn = [...dlg.querySelectorAll('div[role="button"], button')]
                .find(b => (b.innerText || '').trim() === name);
            if (!btn) return 'not_found';
            if (btn.getAttribute('aria-disabled') === 'true' || btn.disabled) return 'disabled';
            btn.click();
            return 'clicked';
        }""",
        name,
    )


def publish_facebook(
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

    profile_dir = PROFILES_DIR / "facebook"
    session_exists = profile_dir.exists()

    if not do_publish:
        return {
            "dry_run": True,
            "platform": "facebook",
            "text": text,
            "media_type": media_type,
            "media": str(media_file) if media_file else None,
            "session_found": session_exists,
            "message": (
                (NOT_PUBLISHED_NOTE if not dry_run else "Dry run requested explicitly.")
                + (
                    " No browser was launched, nothing was posted."
                    if session_exists
                    else " Also: no saved Facebook session was found -- "
                    "run `python -m auth.login_wizard --platform facebook` before a real post."
                )
                + " Unverified integration: this publisher has not been exercised against a live "
                "Facebook account -- treat the first real run as a live test, not a known-working "
                "path."
            ),
        }

    if not session_exists:
        raise SystemExit(
            "No saved Facebook session found. Run "
            "`python -m auth.login_wizard --platform facebook` first."
        )

    ensure_chrome_installed()

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            channel="chrome",
            headless=False,
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.on("dialog", lambda dialog: dialog.dismiss())

        try:
            page.goto("https://www.facebook.com/", timeout=STEP_TIMEOUT_MS)
            page.wait_for_timeout(2000)
            _dismiss_cookie_banner(page)

            if not _open_composer(page):
                screenshot_path = _save_debug_screenshot(page)
                raise RuntimeError(
                    "Could not find the \"What's on your mind?\" composer opener on the home "
                    "feed -- this selector has not been verified live and Facebook's markup may "
                    "not match what this code expects. "
                    + (f"Screenshot saved to {screenshot_path}." if screenshot_path else "")
                )
            page.wait_for_timeout(1500)

            editor = page.locator('[role="dialog"] div[role="textbox"][contenteditable="true"]').first
            if editor.count() == 0:
                editor = page.locator('div[role="textbox"][contenteditable="true"]').first
            editor.click()
            page.wait_for_timeout(500)
            page.keyboard.type(text, delay=15)
            page.wait_for_timeout(500)

            if media_file:
                add_media = page.locator('[role="dialog"] div[aria-label="Photo/video"]')
                if add_media.count() == 0:
                    add_media = page.get_by_role("button", name="Photo/video")
                if add_media.count() == 0:
                    screenshot_path = _save_debug_screenshot(page)
                    raise RuntimeError(
                        "Could not find the Photo/video attach control in the composer dialog. "
                        + (f"Screenshot saved to {screenshot_path}." if screenshot_path else "")
                    )
                # expect_file_chooser intercepts the chooser Playwright-side -- without this the
                # click can fall through to a REAL native OS file dialog, the same failure mode
                # already confirmed live for Bluesky's and LinkedIn's "Add media" buttons.
                with page.expect_file_chooser(timeout=10_000) as fc_info:
                    add_media.first.click()
                fc_info.value.set_files(str(media_file))
                page.wait_for_timeout(1500)

                if media_type == "video":
                    for _ in range(VIDEO_PROCESSING_WAIT_ITERATIONS):
                        processing = page.get_by_text("Processing", exact=False).count()
                        if processing == 0:
                            break
                        page.wait_for_timeout(VIDEO_PROCESSING_WAIT_INTERVAL_MS)
                    page.wait_for_timeout(2000)
                else:
                    page.wait_for_timeout(2000)

            status = _click_dialog_button(page, "Post")
            retries = 0
            while status == "disabled" and retries < 10:
                page.wait_for_timeout(2000)
                status = _click_dialog_button(page, "Post")
                retries += 1

            if status != "clicked":
                screenshot_path = _save_debug_screenshot(page)
                reason = (
                    "the Post button was found but stayed disabled the whole time (usually means "
                    "attached media was still processing)"
                    if status == "disabled"
                    else "no Post button matching the expected text was found in the dialog "
                    "(this selector is unverified and Facebook's markup may differ)"
                )
                raise RuntimeError(
                    f"Could not click Post -- {reason}. "
                    + (f"Screenshot saved to {screenshot_path}." if screenshot_path else "")
                )
            page.wait_for_timeout(1500)

            # Wait for the composer dialog to actually close before trusting the click did
            # anything -- confirmed live on Bluesky that a click can silently do nothing while
            # still reporting "clicked" from the JS side. Apply the same caution here by default
            # since this path has never been run live at all.
            composer_closed = False
            for _ in range(20):
                if page.locator('[role="dialog"]').count() == 0:
                    composer_closed = True
                    break
                page.wait_for_timeout(1000)

            if not composer_closed:
                screenshot_path = _save_debug_screenshot(page)
                raise RuntimeError(
                    "Clicked Post but the composer dialog never closed -- the post likely did "
                    "NOT go out. Do not retry blind; verify independently first (reload the "
                    "profile timeline and look for the post) before trying again. "
                    + (f"Screenshot saved to {screenshot_path}." if screenshot_path else "")
                )

            # Find the user's own profile link dynamically, the same approach already used for
            # LinkedIn -- read `.href` (resolved absolute URL), not getAttribute('href').
            profile_url = page.evaluate("""() => {
                const link = document.querySelector('a[aria-label="Your profile"]')
                    || document.querySelector('a[href*="/profile.php?id="]')
                    || document.querySelector('div[data-pagelet="LeftRail"] a[role="link"]');
                return link ? link.href : null;
            }""")

            verified = False
            if profile_url:
                snippet = text[:40]
                page.goto(profile_url, timeout=STEP_TIMEOUT_MS)
                page.wait_for_timeout(4000)
                for attempt in range(3):
                    match = page.evaluate(
                        """(snippet) => document.body.innerText.includes(snippet)""",
                        snippet,
                    )
                    if match:
                        verified = True
                        break
                    page.mouse.wheel(0, 4000)
                    page.wait_for_timeout(3000)

            result = {
                "dry_run": False,
                "platform": "facebook",
                "status": "posted",
                "text": text,
                "media_type": media_type,
                "profile_url": profile_url,
                "verified": verified,
                "verify_note": (
                    "Confirmed present on the profile timeline."
                    if verified
                    else "Not found on the profile timeline within the wait window -- this whole "
                    "path is unverified against a live account, so treat this result with extra "
                    "caution and check the timeline by hand before assuming either success or "
                    "failure."
                ),
            }
        finally:
            context.close()

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Post to Facebook (personal profile timeline)")
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

    result = publish_facebook(
        args.text,
        video_path=args.video,
        image_path=args.image,
        dry_run=args.dry_run,
        confirm_publish=args.confirm_publish,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
