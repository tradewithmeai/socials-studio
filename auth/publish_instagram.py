"""Upload a video/reel or photo to Instagram using a saved login session from the platform-login wizard.

Unlike YouTube, Google-style automated-browser blocking does NOT apply here -- Instagram's own web
upload flow was driven successfully via Playwright + a saved session in live testing. This is
still fragile in a different way: Instagram's web UI is not a stable public contract, and its
"Create" entry point moves around in the DOM. This module uses the accessible-name selectors that
were verified working, with a direct-URL fallback.

Requires: `python -m auth.login_wizard --platform instagram` already run successfully
(profiles/instagram/ must exist with a logged-in session).

Known issue NOT handled by this script (see the onboard-instagram skill): if the source video
fades in from black, Instagram may default the cover thumbnail to a black frame. Trim the fade
before uploading, or fix the cover by hand afterward -- there is no reliable automated fix.

Safe by default: this validates and returns without touching a browser unless you pass
`--confirm-publish` (CLI) or `confirm_publish=True` (library call). `--dry-run` is an explicit,
equivalent way to request the same validate-only behavior, and always wins if both are passed.

Usage:
    python -m auth.publish_instagram <video_or_image_path> --caption "..." --confirm-publish
    python -m auth.publish_instagram <video_or_image_path> --dry-run   # validate only -- also the default
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

from auth.chrome_setup import ensure_chrome_installed
from auth.login_wizard import FORCE_ENGLISH_LOCALE, PROFILES_DIR
from auth.publish_safety import NOT_PUBLISHED_NOTE, should_publish

STEP_TIMEOUT_MS = 30_000

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def _media_type(path: Path) -> str:
    return "image" if path.suffix.lower() in IMAGE_EXTENSIONS else "video"


def _click_by_text(page: Page, text: str, tag_filter: str = "a,button,[role=link],[role=button],div[tabindex]") -> bool:
    """Click an element by exact innerText match via direct JS, bypassing
    Playwright's role-based locators.

    Confirmed necessary (2026-08-08): Instagram's "Post" flyout item is a
    real `<a role="link">Post</a>` in the DOM (verified via querySelector),
    but `page.get_by_role("link", name="Post")` finds ZERO matches -- some
    quirk in how Playwright computes the accessible name for these elements.
    A plain JS click by innerText works every time. Don't reach for
    get_by_role on Instagram's composer chrome; it silently fails here.
    """
    return page.evaluate(
        """([tagFilter, targetText]) => {
            const els = [...document.querySelectorAll(tagFilter)]
                .filter(el => (el.innerText || '').trim() === targetText);
            if (els.length) { els[0].click(); return true; }
            return false;
        }""",
        [tag_filter, text],
    )


def _open_create_post_dialog(page: Page) -> None:
    """Open the file-chooser step of Instagram's post composer.

    Clicking "New post" opens a "Post / AI" flyout regardless of media type
    (this differs from older notes claiming video skips straight to the
    file chooser -- that was true as of 2026-06-08 but Instagram's UI has
    since changed to always show the flyout, confirmed live 2026-08-08).
    Always click "Post" from the flyout before expecting a file input."""
    page.goto("https://www.instagram.com/", timeout=STEP_TIMEOUT_MS)
    page.wait_for_timeout(1500)

    continue_as = page.get_by_role("button", name="Continue as", exact=False)
    if continue_as.count() > 0:
        continue_as.first.click()
        page.wait_for_timeout(1000)

    new_post_link = page.locator('a:has(svg[aria-label="New post"])')
    if new_post_link.count() > 0:
        new_post_link.first.click()
    else:
        # Fallback: the icon-only collapsed sidebar sometimes needs the plus icon directly.
        plus_icon = page.get_by_role("link", name="New post")
        plus_icon.first.click()
    page.wait_for_timeout(1500)

    if not _click_by_text(page, "Post"):
        raise RuntimeError(
            "Could not find the 'Post' option in the New post flyout -- "
            "Instagram's composer UI may have changed again."
        )
    page.wait_for_timeout(1500)


def publish_instagram(
    video_path: str,
    caption: str = "",
    dry_run: bool = False,
    confirm_publish: bool = False,
) -> dict:
    do_publish = should_publish(dry_run=dry_run, confirm_publish=confirm_publish)

    media_file = Path(video_path).expanduser().resolve()
    if not media_file.is_file():
        raise SystemExit(f"video_path not found: {media_file}")
    media_type = _media_type(media_file)

    profile_dir = PROFILES_DIR / "instagram"
    session_exists = profile_dir.exists()

    if not do_publish:
        return {
            "dry_run": True,
            "platform": "instagram",
            "would_publish": str(media_file),
            "media_type": media_type,
            "caption": caption,
            "session_found": session_exists,
            "message": (
                (NOT_PUBLISHED_NOTE if not dry_run else "Dry run requested explicitly.")
                + (
                    " No browser was launched, nothing was uploaded."
                    if session_exists
                    else " Also: no saved Instagram session was found -- "
                    "run `python -m auth.login_wizard --platform instagram` before a real publish."
                )
            ),
        }

    if not session_exists:
        raise SystemExit(
            "No saved Instagram session found. Run "
            "`python -m auth.login_wizard --platform instagram` first."
        )

    ensure_chrome_installed()

    with sync_playwright() as p:
        # Forced to English for the same reason login_wizard's verification step is -- this
        # profile's selectors are English strings, and the platform renders them in whatever
        # locale the browser reports if the account itself carries no stored preference. See
        # login_wizard.py's module docstring for the live-confirmed failure this prevents.
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            channel="chrome",
            headless=False,
            locale=FORCE_ENGLISH_LOCALE,
        )
        page = context.pages[0] if context.pages else context.new_page()

        try:
            _open_create_post_dialog(page)

            file_input = page.locator('input[type="file"]')
            file_input.first.set_input_files(str(media_file))
            page.wait_for_timeout(2000)

            # Crop step -- for landscape sources, avoid the default 1:1 square crop.
            # Plain .click() times out here: a dialog overlay intercepts pointer events
            # even though the element is "visible, enabled and stable" per Playwright's
            # own check. JS .click() bypasses the overlay entirely (same fix as the
            # New-post flyout above).
            crop_select = page.locator('svg[aria-label="Select Crop"]')
            if crop_select.count() > 0:
                media_el = page.locator("video").first
                if media_el.count() == 0:
                    media_el = page.locator('[role="dialog"] img[src^="blob:"]').first
                box = media_el.bounding_box() if media_el.count() > 0 else None
                if box and box["width"] > box["height"]:
                    page.evaluate("""() => {
                        const svg = document.querySelector('svg[aria-label="Select Crop"]');
                        const clickable = svg && svg.closest('div[role="button"],button,a');
                        if (clickable) clickable.click();
                    }""")
                    page.wait_for_timeout(500)
                    if _click_by_text(page, "Original"):
                        page.wait_for_timeout(500)

            def _click_next() -> bool:
                clicked = page.evaluate("""() => {
                    const dlg = document.querySelector('[role="dialog"]');
                    if (!dlg) return false;
                    const btn = [...dlg.querySelectorAll('button,[role="button"],div[tabindex]')]
                        .find(b => /^next$/i.test((b.innerText || '').trim()));
                    if (btn) { btn.click(); return true; }
                    return false;
                }""")
                page.wait_for_timeout(1000)
                return clicked

            _click_next()  # Crop -> Edit
            _click_next()  # Edit -> Caption/details

            caption_box = page.locator('[role="dialog"] [contenteditable="true"]').first
            if caption and caption_box.count() > 0:
                caption_box.click()
                page.wait_for_timeout(500)
                page.keyboard.type(caption, delay=15)
                page.wait_for_timeout(500)

            shared = page.evaluate("""() => {
                const dlg = document.querySelector('[role="dialog"]');
                if (!dlg) return false;
                const btn = [...dlg.querySelectorAll('button,[role="button"],div[tabindex]')]
                    .find(b => /^share$/i.test((b.innerText || '').trim()));
                if (btn) { btn.click(); return true; }
                return false;
            }""")
            if not shared:
                raise RuntimeError("Could not find the Share button -- Instagram's dialog layout may have changed.")

            share_confirmed = False
            for _ in range(30):
                text = page.locator('[role="dialog"]').inner_text() if page.locator('[role="dialog"]').count() > 0 else ""
                if "shared" in text.lower():
                    share_confirmed = True
                    break
                page.wait_for_timeout(2000)
            if not share_confirmed:
                raise RuntimeError("Timed out waiting for share confirmation -- check the browser window.")

            done_btn = page.get_by_role("button", name="Done")
            if done_btn.count() > 0:
                done_btn.first.click()

            page.wait_for_timeout(2000)

            # Find OWN profile URL dynamically, then read the first post from THAT
            # page -- not the home feed. Grabbing the first /p/ or /reel/ link off
            # the home feed picks up someone else's post (confirmed bug: it returned
            # a different account's post entirely).
            page.goto("https://www.instagram.com/", timeout=STEP_TIMEOUT_MS)
            page.wait_for_timeout(1000)
            profile_href = page.evaluate("""() => {
                const link = document.querySelector('a[href*="/accounts/edit/"]');
                if (link) return null;  // not the pattern we want
                const nav = [...document.querySelectorAll('a')].find(a =>
                    a.querySelector('img[alt*="profile picture"]'));
                return nav ? nav.getAttribute('href') : null;
            }""")
            post_url = None
            if profile_href:
                page.goto(f"https://www.instagram.com{profile_href}", timeout=STEP_TIMEOUT_MS)
                page.wait_for_timeout(1500)
                links = page.evaluate("""() => [...document.querySelectorAll('a[href*="/reel/"], a[href*="/p/"]')]
                    .map(a => a.href).filter((v, i, arr) => arr.indexOf(v) === i)""")
                post_url = links[0] if links else None

            result = {
                "dry_run": False,
                "platform": "instagram",
                "status": "published",
                "url": post_url,
                "media_type": media_type,
                "caption": caption,
                "caption_verify_note": "Instagram has a known bug where the caption drops on "
                "publish even when the composer showed it correctly. Reload the post URL fresh "
                "and confirm the caption is actually there before trusting this result.",
            }
        finally:
            context.close()

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish a video to Instagram")
    parser.add_argument("video_path")
    parser.add_argument("--caption", default="")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Explicitly validate only -- this is also the default with no flags at all.",
    )
    parser.add_argument(
        "--confirm-publish",
        action="store_true",
        help="Required to actually publish for real. Without it, this only validates.",
    )
    args = parser.parse_args()

    result = publish_instagram(
        args.video_path,
        caption=args.caption,
        dry_run=args.dry_run,
        confirm_publish=args.confirm_publish,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
