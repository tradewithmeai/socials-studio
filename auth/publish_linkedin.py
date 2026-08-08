"""Post to LinkedIn using a saved login session from the platform-login wizard.

Like X, Instagram, and Bluesky, this does NOT hit automation-detection
blocking -- the login step goes through the same plain-Chrome-then-verify
flow as the others (see auth/login_wizard.py).

LinkedIn's composer lives inside a shadow DOM (#interop-outlet), and a
transparent overlay from that same host intercepts the "Start a post" click
in the light DOM. Both are handled below based on prior verified findings.

Requires: `python -m auth.login_wizard --platform linkedin` already run
successfully (profiles/linkedin/ must exist with a logged-in session).

⚠️ This publishes immediately -- there is no LinkedIn-side draft/review step
once you click Post. There is also no known caption-drop bug here (unlike
Instagram); what you type is what gets posted.

Usage:
    python -m auth.publish_linkedin "post text" --video path/to/video.mp4 [--dry-run]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from auth.chrome_setup import ensure_chrome_installed
from auth.login_wizard import PROFILES_DIR

STEP_TIMEOUT_MS = 30_000


def publish_linkedin(text: str, video_path: str = "", dry_run: bool = False) -> dict:
    if not text.strip():
        raise SystemExit("Post text is required.")

    video_file = None
    if video_path:
        video_file = Path(video_path).expanduser().resolve()
        if not video_file.is_file():
            raise SystemExit(f"video_path not found: {video_file}")

    profile_dir = PROFILES_DIR / "linkedin"
    session_exists = profile_dir.exists()

    if dry_run:
        return {
            "dry_run": True,
            "platform": "linkedin",
            "text": text,
            "video": str(video_file) if video_file else None,
            "session_found": session_exists,
            "message": (
                "Inputs are valid; no browser was launched, nothing was posted."
                if session_exists
                else "Inputs are valid, but no saved LinkedIn session was found -- "
                "run `python -m auth.login_wizard --platform linkedin` before a real post."
            ),
        }

    if not session_exists:
        raise SystemExit(
            "No saved LinkedIn session found. Run "
            "`python -m auth.login_wizard --platform linkedin` first."
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
            page.goto("https://www.linkedin.com/feed/", timeout=STEP_TIMEOUT_MS)
            page.wait_for_timeout(2000)

            # Dismiss a cookie banner if present -- it can block the composer overlay.
            page.evaluate("""() => {
                document.querySelectorAll('button').forEach(b => {
                    if ((b.innerText || '').includes('Accept')) b.click();
                });
            }""")
            page.wait_for_timeout(500)

            # #interop-outlet overlays the page and intercepts the "Start a post"
            # click even though the button itself is in the light DOM. Disable
            # pointer-events on the overlay just long enough to click through it,
            # then re-enable -- the composer dialog that then renders lives INSIDE
            # that same element's shadow root, so leaving it disabled would block
            # every subsequent click.
            page.evaluate("""() => {
                const el = document.querySelector('#interop-outlet');
                if (el) el.style.pointerEvents = 'none';
            }""")
            start_post = page.get_by_role("button", name="Start a post")
            start_post.first.click()
            page.wait_for_timeout(500)
            page.evaluate("""() => {
                const el = document.querySelector('#interop-outlet');
                if (el) el.style.pointerEvents = '';
            }""")
            page.wait_for_timeout(1000)

            # Playwright's role locators pierce open shadow roots, so the editor
            # inside #interop-outlet.shadowRoot is reachable directly.
            editor = page.get_by_role("textbox", name="Text editor for creating content")
            editor.click()
            page.wait_for_timeout(500)
            page.keyboard.type(text, delay=15)
            page.wait_for_timeout(500)

            if video_file:
                add_media = page.get_by_role("button", name="Add media")
                if add_media.count() > 0:
                    # expect_file_chooser intercepts the chooser Playwright-side --
                    # without this the click can fall through to a REAL native OS
                    # file dialog (confirmed live, same failure mode as Bluesky's
                    # "Add media to post" button).
                    with page.expect_file_chooser(timeout=10_000) as fc_info:
                        add_media.first.click()
                    fc_info.value.set_files(str(video_file))
                    page.wait_for_timeout(3000)

                    # get_by_role("button", name="Next") is AMBIGUOUS here --
                    # confirmed live it matched a document-viewer pagination
                    # control ("Go to next page of document"), not the media
                    # wizard's Next button, and hung waiting to click something
                    # that was never the right element. Scope to the dialog's
                    # shadow-DOM subtree and match by exact visible text instead.
                    next_clicked = page.evaluate("""() => {
                        const outlet = document.querySelector('#interop-outlet');
                        const root = outlet && outlet.shadowRoot;
                        if (!root) return false;
                        const btn = [...root.querySelectorAll('button')]
                            .find(b => (b.innerText || '').trim() === 'Next');
                        if (btn) { btn.click(); return true; }
                        return false;
                    }""")
                    if next_clicked:
                        page.wait_for_timeout(1000)
                else:
                    raise RuntimeError(
                        "'Add media' button not found -- a URL in the post text auto-attaches a "
                        "link-preview card that takes the media slot, so it may have already "
                        "claimed it. Attach media BEFORE typing any URL that would trigger the card."
                    )

            post_btn = page.get_by_role("button", name="Post", exact=True)
            post_btn.first.click()

            # After clicking Post with a video attached, LinkedIn shows an inline
            # "Uploading... Keep the page open to finish uploading" banner with a
            # percentage -- the composer closing does NOT mean the upload (or the
            # post) is actually done. Confirmed live: closing the browser 2-3s
            # after the Post click, while that banner still read 15%, meant the
            # video never finished uploading and the post never actually appeared
            # anywhere. Wait for the banner to fully clear before returning.
            if video_file:
                for _ in range(60):
                    uploading = page.get_by_text("Keep the page open to finish uploading", exact=False).count()
                    if uploading == 0:
                        break
                    page.wait_for_timeout(2000)
                else:
                    raise RuntimeError(
                        "Video upload did not finish within the wait window -- do not close "
                        "the browser; check the LinkedIn tab directly."
                    )
                page.wait_for_timeout(2000)
            else:
                page.wait_for_timeout(3000)

            # Find own profile URL dynamically for the verify step. Read `.href`
            # (the resolved absolute URL), NOT getAttribute('href') -- LinkedIn's
            # profile links are already absolute, and prepending the domain to an
            # already-absolute URL doubles it (confirmed live: produced
            # "https://www.linkedin.comhttps://www.linkedin.com/in/...").
            page.wait_for_timeout(1000)
            profile_url = page.evaluate("""() => {
                const link = document.querySelector('a[href*="/in/"]');
                return link ? link.href : null;
            }""")

            result = {
                "platform": "linkedin",
                "status": "posted",
                "text": text,
                "had_video": video_file is not None,
                "profile_url": profile_url,
                "verify_note": "The activity feed's top post is not always the newest -- "
                "match on text unique to this post, and read the item's data-urn "
                "(urn:li:activity:<id>) to capture the real post id. Reload once if it "
                "hasn't appeared yet.",
            }
        finally:
            context.close()

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Post to LinkedIn")
    parser.add_argument("text")
    parser.add_argument("--video", default="", help="Optional path to a video to attach")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs and print what would happen -- no browser, no post.",
    )
    args = parser.parse_args()

    result = publish_linkedin(args.text, video_path=args.video, dry_run=args.dry_run)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
