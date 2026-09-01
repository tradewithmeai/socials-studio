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

Safe by default: this validates and returns without touching a browser unless you pass
`--confirm-publish` (CLI) or `confirm_publish=True` (library call). `--dry-run` is an explicit,
equivalent way to request the same validate-only behavior, and always wins if both are passed.

Usage:
    python -m auth.publish_linkedin "post text" --video path/to/video.mp4 --confirm-publish
    python -m auth.publish_linkedin "post text" --image path/to/photo.jpg --confirm-publish
    python -m auth.publish_linkedin "post text" --dry-run   # validate only -- also the default
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from auth.chrome_setup import ensure_chrome_installed
from auth.login_wizard import FORCE_ENGLISH_LOCALE, PROFILES_DIR
from auth.publish_safety import NOT_PUBLISHED_NOTE, should_publish

STEP_TIMEOUT_MS = 30_000


def publish_linkedin(
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

    profile_dir = PROFILES_DIR / "linkedin"
    session_exists = profile_dir.exists()

    if not do_publish:
        return {
            "dry_run": True,
            "platform": "linkedin",
            "text": text,
            "media_type": media_type,
            "media": str(media_file) if media_file else None,
            "session_found": session_exists,
            "message": (
                (NOT_PUBLISHED_NOTE if not dry_run else "Dry run requested explicitly.")
                + (
                    " No browser was launched, nothing was posted."
                    if session_exists
                    else " Also: no saved LinkedIn session was found -- "
                    "run `python -m auth.login_wizard --platform linkedin` before a real post."
                )
            ),
        }

    if not session_exists:
        raise SystemExit(
            "No saved LinkedIn session found. Run "
            "`python -m auth.login_wizard --platform linkedin` first."
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

        # Decline any beforeunload prompt so an in-flight upload is never torn
        # down by a navigation. LinkedIn continues uploading a large video in
        # the background after the composer closes; navigating away while
        # that's happening fires a beforeunload dialog, and letting it through
        # (the default with no handler) can end the upload before it finishes.
        page.on("dialog", lambda dialog: dialog.dismiss())

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

            if media_file:
                add_media = page.get_by_role("button", name="Add media")
                if add_media.count() > 0:
                    # expect_file_chooser intercepts the chooser Playwright-side --
                    # without this the click can fall through to a REAL native OS
                    # file dialog (confirmed live, same failure mode as Bluesky's
                    # "Add media to post" button).
                    with page.expect_file_chooser(timeout=10_000) as fc_info:
                        add_media.first.click()
                    fc_info.value.set_files(str(media_file))
                    page.wait_for_timeout(3000)

                    # get_by_role("button", name="Next") is AMBIGUOUS here --
                    # confirmed live it matched a document-viewer pagination
                    # control ("Go to next page of document"), not the media
                    # wizard's Next button, and hung waiting to click something
                    # that was never the right element. Scope to the dialog's
                    # shadow-DOM subtree and match by exact visible text instead.
                    # Images may skip straight to the composer without a Next
                    # step at all, so a miss here is not an error.
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
            # The Post button stays disabled while the composer is still
            # processing an attached video -- that's "wait", not "error". Give
            # the click itself a long timeout instead of pre-polling for
            # "enabled"; Playwright's own actionability check already waits
            # for the disabled state to clear before clicking.
            post_btn.first.click(timeout=90_000 if media_type == "video" else STEP_TIMEOUT_MS)

            # LinkedIn continues uploading a large video in the background
            # after the composer closes. There's no reliable UI signal to poll
            # for here -- an earlier version of this script matched on the
            # banner's exact wording ("Keep the page open to finish
            # uploading"), which is LinkedIn's copy, not a contract, and is
            # brittle to any wording change. Instead: don't navigate, wait
            # long enough for a typical upload, then verify the post actually
            # exists by reloading the activity feed -- the post's existence is
            # the real success signal, not any particular banner string.
            # Images attach fast, so a short wait is enough.
            page.wait_for_timeout(45_000 if media_type == "video" else 3000)

            composer_open = page.get_by_role(
                "textbox", name="Text editor for creating content"
            ).count() > 0
            if composer_open:
                raise RuntimeError(
                    "The composer is still open after the wait -- the post likely hasn't "
                    "gone out yet. Do not close the browser; check the tab directly."
                )

            # Find own profile URL dynamically. Read `.href` (the resolved
            # absolute URL), NOT getAttribute('href') -- LinkedIn's profile
            # links are already absolute, and prepending the domain to an
            # already-absolute URL doubles it (confirmed live: produced
            # "https://www.linkedin.comhttps://www.linkedin.com/in/...").
            profile_url = page.evaluate("""() => {
                const link = document.querySelector('a[href*="/in/"]');
                return link ? link.href : null;
            }""")

            verified = False
            data_urn = None
            if profile_url:
                snippet = text[:40]
                activity_url = profile_url.rstrip("/") + "/recent-activity/all/"
                page.goto(activity_url, timeout=STEP_TIMEOUT_MS)
                # Confirmed live (2026-08-08): a freshly published post can take
                # longer than a few seconds to appear here even though the
                # publish itself already succeeded -- a short wait produces a
                # false "not verified" on a post that is genuinely live. Give
                # indexing real time before the first check.
                page.wait_for_timeout(8000)
                for attempt in range(3):
                    match = page.evaluate(
                        """(snippet) => {
                            const els = [...document.querySelectorAll('[data-urn]')];
                            for (const el of els) {
                                if ((el.innerText || '').includes(snippet)) {
                                    return { urn: el.getAttribute('data-urn'),
                                              hasVideo: el.querySelector('video') !== null };
                                }
                            }
                            return null;
                        }""",
                        snippet,
                    )
                    if match:
                        verified = True
                        data_urn = match.get("urn")
                        break
                    # The activity feed isn't strictly chronological and a new
                    # post can take a few seconds to be indexed -- scroll to
                    # load more items and give it one more look before giving up.
                    page.mouse.wheel(0, 5000)
                    page.wait_for_timeout(5000)

            result = {
                "dry_run": False,
                "platform": "linkedin",
                "status": "posted",
                "text": text,
                "media_type": media_type,
                "profile_url": profile_url,
                "verified": verified,
                "urn": data_urn,
                "verify_note": (
                    "Confirmed present on the activity feed."
                    if verified
                    else "Not found on the activity feed within the wait window -- indexing "
                    "can lag; reload the feed manually before assuming the post failed."
                ),
            }
        finally:
            context.close()

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Post to LinkedIn")
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

    result = publish_linkedin(
        args.text,
        video_path=args.video,
        image_path=args.image,
        dry_run=args.dry_run,
        confirm_publish=args.confirm_publish,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
