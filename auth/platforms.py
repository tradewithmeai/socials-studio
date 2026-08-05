"""Per-platform login config for the auth wizard.

`logged_in_selector` and `login_url_contains` are best-effort signals for
detecting a completed login and WILL need periodic verification against the
live site — platforms change their DOM/URLs without notice. Treat these as
a starting point, not a guarantee.
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


PLATFORMS: dict[str, PlatformConfig] = {
    "tiktok": PlatformConfig(
        key="tiktok",
        label="TikTok",
        login_url="https://www.tiktok.com/login",
        login_url_marker="/login",
        logged_in_selector='[data-e2e="profile-icon"]',
    ),
    "instagram": PlatformConfig(
        key="instagram",
        label="Instagram",
        login_url="https://www.instagram.com/accounts/login/",
        login_url_marker="accounts/login",
        logged_in_selector='svg[aria-label="Home"]',
    ),
    "youtube": PlatformConfig(
        key="youtube",
        label="YouTube (Google account)",
        login_url="https://accounts.google.com/ServiceLogin?service=youtube&continue=https://www.youtube.com/",
        login_url_marker="accounts.google.com",
        logged_in_selector="#avatar-btn",
    ),
    "x": PlatformConfig(
        key="x",
        label="X (Twitter)",
        login_url="https://x.com/login",
        login_url_marker="/login",
        logged_in_selector='a[data-testid="AppTabBar_Home_Link"]',
    ),
}


def get_platform(key: str) -> PlatformConfig:
    try:
        return PLATFORMS[key]
    except KeyError as exc:
        available = ", ".join(sorted(PLATFORMS))
        raise SystemExit(f"Unknown platform '{key}'. Available: {available}") from exc
