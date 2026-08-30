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

import shutil
import subprocess
import sys
from pathlib import Path

# Plain, non-Playwright-managed system Chrome, used ONLY for the manual login
# step (see login_wizard.py). Never launched with any CDP/automation switch --
# that's the whole point. This is deliberately separate from the Playwright
# "chrome" channel below, which IS automation-controlled and is only ever
# pointed at an already-authenticated profile, never at a login page.
_WINDOWS_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe",
]

# Real Google Chrome executable names on PATH (Linux, plus a generic "chrome"
# checked on every platform before the OS-specific paths below). Deliberately
# excludes chromium/chromium-browser -- see this module's docstring for why
# Chromium isn't an acceptable substitute. Must stay in sync with
# installer/bootstrap.py's LINUX_CHROME_NAMES -- enforced by
# tests/test_chrome_linux_detection_parity.py, not by importing across that
# boundary: bootstrap.py has to run standalone, before this package's own
# dependencies are installed.
_CHROME_EXECUTABLE_NAMES = ["chrome", "google-chrome", "google-chrome-stable"]


def find_system_chrome() -> Path:
    """Locate a plain, human-launched Chrome executable for manual login.

    Raises SystemExit with install instructions if none is found -- this
    must be a real system Chrome install, not Playwright's managed binary.
    """
    for name in _CHROME_EXECUTABLE_NAMES:
        which = shutil.which(name)
        if which:
            return Path(which)
    which = shutil.which("chrome.exe")
    if which:
        return Path(which)

    if sys.platform == "win32":
        import os

        for candidate in _WINDOWS_CANDIDATES:
            path = Path(os.path.expandvars(candidate))
            if path.is_file():
                return path
    elif sys.platform == "darwin":
        mac_path = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        if mac_path.is_file():
            return mac_path

    raise SystemExit(
        "Could not find a system Chrome install. Install Chrome from "
        "https://www.google.com/chrome/ and try again -- the manual login "
        "step needs a plain, non-automated Chrome, separate from Playwright's "
        "managed browser."
    )


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
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise SystemExit(
            "Failed to install Chrome for Playwright.\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
