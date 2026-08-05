"""Ensures a real Chrome build is available for Playwright's "chrome" channel.

We deliberately use the `channel="chrome"` real-Chrome build rather than the
bundled Chromium: social platforms are aggressive about flagging automation,
and login flows in particular (captchas, "suspicious activity" holds) are
noticeably more likely to trip on Chromium's fingerprint than on Chrome.

`playwright install chrome` pulls a Chrome-for-Testing build via Playwright's
own channel mechanism -- this is independent of any Chrome the user may or
may not already have installed system-wide, and is idempotent (a no-op if
already present).
"""

from __future__ import annotations

import subprocess
import sys


def ensure_chrome_installed() -> None:
    """Install the Playwright-managed Chrome channel if it's missing.

    Safe to call every run: `playwright install chrome` no-ops quickly when
    the build is already present. Raises SystemExit with a readable message
    if the install itself fails (e.g. no network).
    """
    result = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chrome"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(
            "Failed to install Chrome for Playwright.\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
