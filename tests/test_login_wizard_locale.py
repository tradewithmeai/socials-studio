"""Unit tests for the non-English onboarding fix in auth/login_wizard.py.

No real browser, network access, or profile data anywhere in this file --
subprocess.Popen, Playwright, and platform lookup are all mocked. Chrome is
never actually launched.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from auth import login_wizard


def _fake_platform():
    platform = MagicMock()
    platform.label = "Test Platform"
    platform.login_url = "https://example.com/login"
    platform.login_url_marker = "/login"
    platform.logged_in_selector = None
    return platform


def test_manual_login_command_is_isolated_and_forces_english(tmp_path):
    """The plain Chrome command must use the given profile dir, force English,
    and carry no CDP/automation-control flags."""
    profile_dir = tmp_path / "profiles" / "instagram"

    fake_process = MagicMock()
    fake_process.wait.return_value = None

    with patch("auth.login_wizard.get_platform", return_value=_fake_platform()), \
         patch("auth.login_wizard.find_system_chrome", return_value=Path("C:/chrome/chrome.exe")), \
         patch("auth.login_wizard.subprocess.Popen", return_value=fake_process) as mock_popen:
        login_wizard._manual_login_step("instagram", profile_dir)

    mock_popen.assert_called_once()
    command = mock_popen.call_args[0][0]

    assert f"--user-data-dir={profile_dir}" in command
    assert "--lang=en-US" in command

    automation_flags = {
        "--remote-debugging-port", "--remote-debugging-pipe",
        "--enable-automation", "--headless",
    }
    joined = " ".join(command)
    for flag in automation_flags:
        assert flag not in joined, f"unexpected automation flag in manual login command: {flag}"
    assert not any(arg.startswith("--remote-debugging") for arg in command)


def test_verify_session_passes_locale_and_args_to_playwright(tmp_path):
    """Playwright's launch_persistent_context must receive both the forced
    locale and the forced --lang argument for the verification step."""
    profile_dir = tmp_path / "profiles" / "instagram"

    fake_context = MagicMock()
    fake_page = MagicMock()
    fake_page.url = "https://example.com/home"
    fake_context.pages = [fake_page]

    fake_chromium = MagicMock()
    fake_chromium.launch_persistent_context.return_value = fake_context

    fake_playwright_cm = MagicMock()
    fake_playwright_cm.__enter__.return_value = MagicMock(chromium=fake_chromium)
    fake_playwright_cm.__exit__.return_value = False

    with patch("auth.login_wizard.get_platform", return_value=_fake_platform()), \
         patch("auth.login_wizard.ensure_chrome_installed"), \
         patch("auth.login_wizard.sync_playwright", return_value=fake_playwright_cm):
        login_wizard._verify_session("instagram", profile_dir)

    fake_chromium.launch_persistent_context.assert_called_once()
    kwargs = fake_chromium.launch_persistent_context.call_args.kwargs

    assert kwargs["locale"] == "en-US"
    assert kwargs["args"] == ["--lang=en-US"]
    assert kwargs["user_data_dir"] == str(profile_dir)


def test_force_english_constants():
    assert login_wizard.FORCE_ENGLISH_ARGS == ["--lang=en-US"]
    assert login_wizard.FORCE_ENGLISH_LOCALE == "en-US"
