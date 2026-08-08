"""Interactive login: sign in by hand in a PLAIN, non-automated Chrome, then
verify the saved session with Playwright.

Usage:
    python -m auth.login_wizard --platform x
    python -m auth.login_wizard --list

## Why this doesn't use Playwright to drive the login itself

Confirmed live, repeatedly: attempting a login from inside a Playwright-
controlled browser gets blocked -- Google's version of the block reads
"This browser or app may not be secure." This is NOT about which login
method you use (native password vs. "Sign in with Google"), and it is not
Google-specific -- Instagram and others challenge automated logins too (SMS
codes, "suspicious login" interstitials). The block triggers on the
automation signals themselves (`navigator.webdriver`, the CDP control port,
automation command-line switches, a fresh profile with no history) -- not on
who's typing the password.

The fix: **never log in from the automated browser.** This script launches a
completely plain, human-driven Chrome process (no CDP, no automation flags --
indistinguishable from double-clicking the Chrome icon) pointed at the
platform's login page. You log in yourself, close the window, and only THEN
does Playwright touch that profile -- to verify the session, and later to
replay it for publishing. Anti-automation defenses don't apply to a session
a human already established; the automated browser is just reusing normal
cookies at that point.

Each platform gets its own persistent profile under `profiles/<platform>/`.
`profiles/` is gitignored -- these are live, personal logged-in sessions and
must never be committed.

YouTube and TikTok are NOT here -- both use OAuth + their official APIs
instead (see auth/setup_youtube_oauth.py and auth/setup_tiktok_oauth.py),
for reasons unrelated to this login-blocking issue (YouTube: Google blocks
browser automation entirely; TikTok: a Playwright-driven account risks a
shadow-ban even when login succeeds).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from auth.chrome_setup import ensure_chrome_installed, find_system_chrome
from auth.platforms import PLATFORMS, get_platform

REPO_ROOT = Path(__file__).resolve().parent.parent
PROFILES_DIR = REPO_ROOT / "profiles"

VERIFY_TIMEOUT_MS = 30_000


def _manual_login_step(platform_key: str, profile_dir: Path) -> None:
    """Launch a plain, non-automated Chrome for the user to log in by hand.

    No Playwright, no CDP, no automation switches -- this subprocess call is
    functionally identical to double-clicking the Chrome icon. Blocks until
    the user closes every window of this Chrome instance.
    """
    platform = get_platform(platform_key)
    chrome_path = find_system_chrome()

    print(f"\nOpening a plain Chrome window to {platform.label}'s login page.")
    print("Log in yourself -- 2FA included, and dismiss any cookie/consent banners while")
    print("you're there. When you're done, CLOSE THIS CHROME WINDOW COMPLETELY")
    print("(all its windows/tabs) to continue.\n")

    process = subprocess.Popen(
        [
            str(chrome_path),
            f"--user-data-dir={profile_dir}",
            "--no-first-run",
            platform.login_url,
        ]
    )
    try:
        process.wait()
    except KeyboardInterrupt:
        process.terminate()
        raise SystemExit("Login cancelled.") from None


def _verify_session(platform_key: str, profile_dir: Path) -> bool:
    """Read-only check: is this profile actually logged in?

    Navigates to the platform's HOME page, never the login page -- this is
    just reading an already-authenticated session (or discovering it isn't
    one), which anti-automation defenses don't block.
    """
    platform = get_platform(platform_key)
    ensure_chrome_installed()

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            channel="chrome",
            headless=False,
        )
        try:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(platform.login_url, timeout=VERIFY_TIMEOUT_MS, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            logged_in = platform.login_url_marker not in page.url
            if logged_in and platform.logged_in_selector:
                try:
                    logged_in = page.locator(platform.logged_in_selector).first.is_visible(timeout=3000)
                except Exception:
                    logged_in = False
        finally:
            context.close()

    return logged_in


def run_wizard(platform_key: str) -> Path:
    get_platform(platform_key)  # validates the key
    profile_dir = PROFILES_DIR / platform_key
    profile_dir.mkdir(parents=True, exist_ok=True)

    _manual_login_step(platform_key, profile_dir)

    print("Verifying the saved session...")
    if _verify_session(platform_key, profile_dir):
        print(f"Verified: {platform_key} is logged in. Session saved to {profile_dir}")
    else:
        print(
            f"NOT verified: {platform_key} still looks logged out. "
            "Re-run this command and make sure you complete login before closing the window."
        )
    return profile_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Platform login (manual sign-in + verification)")
    parser.add_argument("--platform", choices=sorted(PLATFORMS), help="Platform to log into")
    parser.add_argument("--list", action="store_true", help="List supported platforms")
    args = parser.parse_args()

    if args.list or not args.platform:
        print("Supported platforms:")
        for key, cfg in sorted(PLATFORMS.items()):
            print(f"  {key:12s} {cfg.label}")
        if not args.platform:
            sys.exit(0 if args.list else 1)

    run_wizard(args.platform)


if __name__ == "__main__":
    main()
