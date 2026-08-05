"""Interactive login wizard: open a platform's login page in real Chrome,
let the user log in by hand, and persist the resulting session.

Usage:
    python -m auth.login_wizard --platform tiktok
    python -m auth.login_wizard --list

Each platform gets its own persistent browser profile under
`profiles/<platform>/`. Playwright's persistent context writes cookies and
local storage to that directory automatically on close -- no explicit "save"
step needed. We also snapshot `storage_state.json` alongside it, since a
plain JSON cookie/origin dump is easier to inspect, back up, or hand to a
headless run later than the raw profile directory.

`profiles/` is gitignored -- these are live, personal logged-in sessions and
must never be committed.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from auth.chrome_setup import ensure_chrome_installed
from auth.platforms import PLATFORMS, get_platform

REPO_ROOT = Path(__file__).resolve().parent.parent
PROFILES_DIR = REPO_ROOT / "profiles"

POLL_INTERVAL_SECONDS = 2
DEFAULT_TIMEOUT_SECONDS = 600  # 10 minutes to complete login by hand


def _is_logged_in(page, marker: str, selector: str | None) -> bool:
    if marker in page.url:
        return False
    if selector is None:
        return True
    try:
        return page.locator(selector).first.is_visible(timeout=500)
    except Exception:
        return False


def run_wizard(platform_key: str, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> Path:
    platform = get_platform(platform_key)
    ensure_chrome_installed()

    profile_dir = PROFILES_DIR / platform.key
    profile_dir.mkdir(parents=True, exist_ok=True)

    print(f"Opening {platform.label} login in Chrome -- log in as you normally would.")
    print(f"Waiting up to {timeout_seconds // 60} minutes for login to complete...")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            channel="chrome",
            headless=False,
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(platform.login_url)

        deadline = time.monotonic() + timeout_seconds
        try:
            while time.monotonic() < deadline:
                if _is_logged_in(page, platform.login_url_marker, platform.logged_in_selector):
                    break
                time.sleep(POLL_INTERVAL_SECONDS)
            else:
                context.close()
                raise SystemExit(
                    f"Timed out waiting for {platform.label} login after "
                    f"{timeout_seconds}s. Re-run and try again."
                )
        except KeyboardInterrupt:
            context.close()
            raise SystemExit("Login cancelled.") from None

        # Portable snapshot alongside the persistent profile dir.
        state_path = profile_dir / "storage_state.json"
        context.storage_state(path=str(state_path))
        context.close()

    print(f"{platform.label} login saved to {profile_dir}")
    return profile_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Platform login wizard")
    parser.add_argument("--platform", choices=sorted(PLATFORMS), help="Platform to log into")
    parser.add_argument("--list", action="store_true", help="List supported platforms")
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Seconds to wait for login before giving up",
    )
    args = parser.parse_args()

    if args.list or not args.platform:
        print("Supported platforms:")
        for key, cfg in sorted(PLATFORMS.items()):
            print(f"  {key:12s} {cfg.label}")
        if not args.platform:
            sys.exit(0 if args.list else 1)

    run_wizard(args.platform, timeout_seconds=args.timeout)


if __name__ == "__main__":
    main()
