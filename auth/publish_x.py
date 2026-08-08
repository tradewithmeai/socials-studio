"""Post to X (Twitter) using a saved login session from the platform-login wizard.

Like Instagram, this does NOT hit Google-style automated-browser blocking -- verified working via
Playwright + a saved session in live testing, including with an attached video.

Requires: `python -m auth.login_wizard --platform x` already run successfully
(profiles/x/ must exist with a logged-in session).

Usage:
    python -m auth.publish_x "post text" --video path/to/video.mp4 [--dry-run]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from auth.chrome_setup import ensure_chrome_installed
from auth.login_wizard import PROFILES_DIR

STEP_TIMEOUT_MS = 30_000


def publish_x(text: str, video_path: str = "", dry_run: bool = False) -> dict:
    if not text.strip():
        raise SystemExit("Post text is required.")

    video_file = None
    if video_path:
        video_file = Path(video_path).expanduser().resolve()
        if not video_file.is_file():
            raise SystemExit(f"video_path not found: {video_file}")

    profile_dir = PROFILES_DIR / "x"
    session_exists = profile_dir.exists()

    if dry_run:
        return {
            "dry_run": True,
            "platform": "x",
            "text": text,
            "video": str(video_file) if video_file else None,
            "session_found": session_exists,
            "message": (
                "Inputs are valid; no browser was launched, nothing was posted."
                if session_exists
                else "Inputs are valid, but no saved X session was found -- "
                "run `python -m auth.login_wizard --platform x` before a real post."
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

            if video_file:
                page.evaluate("""() => {
                    const input = document.querySelector('[data-testid="fileInput"]');
                    if (input) input.click();
                }""")
                page.wait_for_timeout(500)
                file_input = page.locator('input[type="file"]')
                file_input.first.set_input_files(str(video_file))

                for _ in range(30):
                    processing = page.get_by_text("Processing", exact=False).count()
                    removable = page.locator('[aria-label*="Remove"]').count()
                    if processing == 0 and removable > 0:
                        break
                    page.wait_for_timeout(2000)
                page.wait_for_timeout(3000)

            clicked = page.evaluate("""() => {
                const btn = [...document.querySelectorAll('button')]
                    .find(b => b.innerText.trim() === 'Post' && !b.disabled);
                if (btn) { btn.click(); return true; }
                return false;
            }""")
            if not clicked:
                raise RuntimeError(
                    "Could not click Post -- likely over the character limit or a dialog is "
                    "blocking the composer. Check the browser window."
                )

            page.wait_for_timeout(2000)
            current_url = page.url
            if "compose" in current_url:
                raise RuntimeError(
                    "Still on the compose page after clicking Post -- it probably did not submit. "
                    "Check for a beforeunload dialog or an over-limit counter."
                )

            result = {
                "platform": "x",
                "status": "posted",
                "text": text,
                "had_video": video_file is not None,
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
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs and print what would happen -- no browser, no post.",
    )
    args = parser.parse_args()

    result = publish_x(args.text, video_path=args.video, dry_run=args.dry_run)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
