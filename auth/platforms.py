"""Per-platform login config for the auth wizard.

`logged_in_selector` and `login_url_contains` are best-effort signals for
detecting a completed login and WILL need periodic verification against the
live site — platforms change their DOM/URLs without notice. Treat these as
a starting point, not a guarantee.

YouTube is deliberately NOT here. It uses OAuth + the official Data API
instead (see auth/setup_youtube_oauth.py) -- Google blocks automated
browser sign-in outright ("This browser or app may not be secure"), so
publish_youtube.py never touches a saved browser session at all.

Platforms listed here (Instagram, X) are NOT immune to anti-automation
defenses either -- see auth/login_wizard.py's module docstring. The login
step for these must happen in a plain, non-Playwright Chrome; only a
session a human already established gets reused by automation afterward.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlatformConfig:
    key: str
    label: str
    login_url: str
    # Login is considered complete once the page URL no longer contains this
    # substring (e.g. leaving "/login" or "/accounts/login/").
    login_url_marker: str
    # Optional: a selector that only appears once logged in. Checked in
    # addition to the URL marker when present — more reliable, verify first.
    logged_in_selector: str | None = None
    # When True, a platform is excluded from login_wizard --list and the CLI's advertised
    # surface, but get_platform() and the login wizard still work for it if invoked
    # explicitly by key. No platform is currently dormant.
    dormant: bool = False


PLATFORMS: dict[str, PlatformConfig] = {
    "instagram": PlatformConfig(
        key="instagram",
        label="Instagram",
        login_url="https://www.instagram.com/accounts/login/",
        login_url_marker="accounts/login",
        logged_in_selector='svg[aria-label="Home"]',
    ),
    "x": PlatformConfig(
        key="x",
        label="X (Twitter)",
        login_url="https://x.com/login",
        login_url_marker="/login",
        logged_in_selector='a[data-testid="AppTabBar_Home_Link"]',
    ),
    "bluesky": PlatformConfig(
        key="bluesky",
        label="Bluesky",
        # Bluesky is a single-page app -- there's no separate /login URL that
        # goes away on success, so login_url_marker below is a marker that will
        # never match (forcing the check to rely on logged_in_selector alone).
        login_url="https://bsky.app",
        login_url_marker="__no_url_marker_for_bluesky__",
        logged_in_selector='[aria-label="Compose new post"]',
    ),
    "linkedin": PlatformConfig(
        key="linkedin",
        label="LinkedIn",
        login_url="https://www.linkedin.com/login",
        login_url_marker="/login",
        logged_in_selector='div[role="button"]:has-text("Start a post")',
    ),
}


def get_platform(key: str) -> PlatformConfig:
    try:
        return PLATFORMS[key]
    except KeyError as exc:
        available = ", ".join(sorted(PLATFORMS))
        raise SystemExit(f"Unknown platform '{key}'. Available: {available}") from exc
