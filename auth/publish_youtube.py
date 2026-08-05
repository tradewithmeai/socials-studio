"""First real publish tool: upload a video to YouTube Studio using a saved
login session from the platform-login wizard.

This drives the YouTube Studio upload UI directly (not the YouTube Data API)
so it reuses the exact same persisted Chrome profile/session the login
wizard created -- no separate OAuth/API-credential setup required. An MCP
server should eventually wrap this (and its sibling platforms) as a proper
agent tool, but this script proves the mechanism first.

Requires: `python -m auth.login_wizard --platform youtube` already run
successfully (profiles/youtube/ must exist with a logged-in session).

YouTube Studio's DOM is not a stable public contract -- the selectors below
are best-effort and may need adjusting against the live UI. Run this
visibly (headless=False, the default) for the first attempt so a human can
watch and correct course if a step doesn't match.

Usage:
    python -m auth.publish_youtube <video_path> --title "..." --description "..." \
        --visibility private
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

from auth.chrome_setup import ensure_chrome_installed
from auth.login_wizard import PROFILES_DIR

VISIBILITY_LABELS = {
    "private": "PRIVATE",
    "unlisted": "UNLISTED",
    "public": "PUBLIC",
}

STEP_TIMEOUT_MS = 30_000


def _click_next(page: Page) -> None:
    page.get_by_role("button", name="Next").click()
    page.wait_for_timeout(500)


def publish_youtube(
    video_path: str,
    title: str,
    description: str = "",
    visibility: str = "private",
    dry_run: bool = False,
) -> dict:
    if visibility not in VISIBILITY_LABELS:
        raise SystemExit(f"visibility must be one of {list(VISIBILITY_LABELS)}")

    video_file = Path(video_path).expanduser().resolve()
    if not video_file.is_file():
        raise SystemExit(f"video_path not found: {video_file}")

    profile_dir = PROFILES_DIR / "youtube"
    session_exists = profile_dir.exists()

    if dry_run:
        return {
            "dry_run": True,
            "platform": "youtube",
            "would_publish": str(video_file),
            "title": title,
            "description": description,
            "visibility": visibility,
            "session_found": session_exists,
            "message": (
                "Inputs are valid; no browser was launched, nothing was uploaded."
                if session_exists
                else "Inputs are valid, but no saved YouTube session was found -- "
                "run `python -m auth.login_wizard --platform youtube` before a real publish."
            ),
        }

    if not session_exists:
        raise SystemExit(
            "No saved YouTube session found. Run "
            "`python -m auth.login_wizard --platform youtube` first."
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
            page.goto("https://studio.youtube.com", timeout=STEP_TIMEOUT_MS)
            page.get_by_role("button", name="Create").first.click()
            page.get_by_role("menuitem", name="Upload videos").click()

            file_input = page.locator("input[type=file]")
            file_input.set_input_files(str(video_file))

            title_box = page.locator("ytcp-social-suggestions-textbox#title-textarea #textbox")
            title_box.click()
            page.keyboard.press("Control+A")
            page.keyboard.type(title)

            if description:
                desc_box = page.locator(
                    "ytcp-social-suggestions-textbox#description-textarea #textbox"
                )
                desc_box.click()
                page.keyboard.press("Control+A")
                page.keyboard.type(description)

            # "No, it's not made for kids" -- required before Next is enabled.
            page.get_by_role("radio", name="No, it's not made for kids").check()

            _click_next(page)  # Details -> Video elements
            _click_next(page)  # Video elements -> Checks
            page.wait_for_timeout(3000)  # let the copyright check run
            _click_next(page)  # Checks -> Visibility

            label = VISIBILITY_LABELS[visibility]
            page.locator(f'tp-yt-paper-radio-button[name="{label}"]').click()

            video_url = None
            link_input = page.locator("[data-error-search] input, .video-url-fadeable a")
            if link_input.count() > 0:
                video_url = link_input.first.get_attribute("href") or link_input.first.input_value()

            page.get_by_role("button", name="Save").click()
            page.wait_for_timeout(2000)

            result = {
                "platform": "youtube",
                "status": "published" if visibility == "public" else "draft",
                "visibility": visibility,
                "url": video_url,
                "title": title,
            }
        finally:
            context.close()

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish a video to YouTube")
    parser.add_argument("video_path")
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument(
        "--visibility",
        choices=sorted(VISIBILITY_LABELS),
        default="private",
        help="Defaults to private -- pass --visibility public explicitly to go live.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs and print what would happen -- no browser, no upload.",
    )
    args = parser.parse_args()

    result = publish_youtube(
        args.video_path,
        title=args.title,
        description=args.description,
        visibility=args.visibility,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
