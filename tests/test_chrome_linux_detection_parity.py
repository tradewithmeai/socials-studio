"""Regression tests for the Codex-reported Linux Chrome-detection mismatch.

installer/bootstrap.py's find_chrome() (used during setup, to report whether
Chrome is available) and auth/chrome_setup.find_system_chrome() (used at
runtime, for the manual login step) used to accept different Linux
executable names -- the installer also accepted `chromium`/`chromium-browser`,
which the runtime check has never accepted. That let the installer report
Chrome as present even though onboarding would then refuse the very
executable it found. Socials Studio deliberately requires real Google
Chrome, not Chromium -- see auth/chrome_setup.py's module docstring.

No test here launches a browser, touches the network, or touches a real
profiles/ directory -- shutil.which is mocked throughout.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "installer"))

import bootstrap  # noqa: E402

from auth import chrome_setup  # noqa: E402


def test_installer_and_runtime_linux_chrome_names_cannot_silently_diverge():
    """The two lists must name exactly the same set of real-Chrome
    executables -- this is the parity check that would have caught the
    original bug (the installer accepting chromium/chromium-browser, which
    the runtime check has never accepted)."""
    assert set(bootstrap.LINUX_CHROME_NAMES) == set(chrome_setup._CHROME_EXECUTABLE_NAMES)


def test_installer_and_runtime_reject_chromium():
    """Neither list may include Chromium under either common package name."""
    for names in (bootstrap.LINUX_CHROME_NAMES, chrome_setup._CHROME_EXECUTABLE_NAMES):
        assert "chromium" not in names
        assert "chromium-browser" not in names


def test_runtime_find_system_chrome_accepts_every_supported_real_chrome_name():
    for name in chrome_setup._CHROME_EXECUTABLE_NAMES:
        with patch(
            "auth.chrome_setup.shutil.which",
            side_effect=lambda candidate, _match=name: f"/usr/bin/{_match}" if candidate == _match else None,
        ):
            found = chrome_setup.find_system_chrome()
        assert found == Path(f"/usr/bin/{name}")


def test_runtime_find_system_chrome_rejects_chromium_alone():
    """`chromium` alone must not satisfy the runtime check -- with no other
    candidate present and a non-Windows/macOS platform, this must raise."""
    with patch("auth.chrome_setup.shutil.which", side_effect=lambda name: "/usr/bin/chromium" if name == "chromium" else None), \
         patch("auth.chrome_setup.sys.platform", "linux"):
        try:
            chrome_setup.find_system_chrome()
            raised = False
        except SystemExit:
            raised = True
    assert raised, "find_system_chrome() must not accept a bare 'chromium' executable"


def test_runtime_find_system_chrome_rejects_chromium_browser_alone():
    with patch(
        "auth.chrome_setup.shutil.which",
        side_effect=lambda name: "/usr/bin/chromium-browser" if name == "chromium-browser" else None,
    ), patch("auth.chrome_setup.sys.platform", "linux"):
        try:
            chrome_setup.find_system_chrome()
            raised = False
        except SystemExit:
            raised = True
    assert raised, "find_system_chrome() must not accept a bare 'chromium-browser' executable"
