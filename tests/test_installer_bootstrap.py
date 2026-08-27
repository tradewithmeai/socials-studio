"""Unit tests for installer/bootstrap.py.

No real virtual environment is created, no pip install runs, no network
call is made, and no file under a real `profiles/` directory is touched --
`venv.EnvBuilder`, `subprocess.run`, and `shutil.which` are all mocked or
pointed at a pytest tmp_path.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "installer"))

import bootstrap  # noqa: E402


def test_find_claude_cli_found():
    which = MagicMock(return_value="/usr/local/bin/claude")
    assert bootstrap.find_claude_cli(which) == "/usr/local/bin/claude"
    which.assert_called_once_with("claude")


def test_find_claude_cli_missing():
    which = MagicMock(return_value=None)
    assert bootstrap.find_claude_cli(which) is None


def test_check_claude_code_reports_install_url_when_missing():
    step = bootstrap.check_claude_code(which=MagicMock(return_value=None))
    assert step.ok is False
    assert "claude.com/claude-code" in step.detail
    assert "qualifying Claude account" in step.detail


def test_find_chrome_windows_uses_known_paths_not_which():
    exists = MagicMock(side_effect=lambda p: p == bootstrap.WINDOWS_CHROME_PATHS[1])
    which = MagicMock(return_value=None)
    found = bootstrap.find_chrome("win32", which=which, path_exists=exists)
    assert found == bootstrap.WINDOWS_CHROME_PATHS[1]
    which.assert_not_called()


def test_find_chrome_linux_uses_which():
    which = MagicMock(side_effect=lambda name: "/usr/bin/chromium" if name == "chromium" else None)
    found = bootstrap.find_chrome("linux", which=which)
    assert found == "/usr/bin/chromium"


def test_check_chrome_missing_explains_why_it_matters():
    step = bootstrap.check_chrome("darwin", which=MagicMock(return_value=None))
    assert step.ok is False
    assert "chrome" in step.detail.lower()
    assert "youtube" in step.detail.lower()


def test_create_virtualenv_is_idempotent(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    venv_dir = project_dir / ".venv"
    scripts_dir = venv_dir / ("Scripts" if sys.platform == "win32" else "bin")
    scripts_dir.mkdir(parents=True)
    python_name = "python.exe" if sys.platform == "win32" else "python3"
    (scripts_dir / python_name).write_text("fake", encoding="utf-8")

    with patch("bootstrap.venv.EnvBuilder") as mock_builder:
        step = bootstrap.create_virtualenv(project_dir, venv_dir)

    assert step.ok is True
    assert "Already present" in step.detail
    mock_builder.assert_not_called()


def test_create_virtualenv_creates_when_missing(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    venv_dir = project_dir / ".venv"

    fake_builder = MagicMock()
    with patch("bootstrap.venv.EnvBuilder", return_value=fake_builder) as mock_builder_cls:
        step = bootstrap.create_virtualenv(project_dir, venv_dir)

    mock_builder_cls.assert_called_once_with(with_pip=True, clear=False)
    fake_builder.create.assert_called_once_with(str(venv_dir))
    assert step.ok is True


def test_install_requirements_missing_file_is_reported(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    venv_dir = project_dir / ".venv"

    run = MagicMock()
    step = bootstrap.install_requirements(venv_dir, project_dir, run=run)

    assert step.ok is False
    run.assert_not_called()


def test_install_requirements_runs_pip_against_the_venv(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "requirements.txt").write_text("playwright\n", encoding="utf-8")
    venv_dir = project_dir / ".venv"

    run = MagicMock(return_value=MagicMock(returncode=0, stderr=""))
    step = bootstrap.install_requirements(venv_dir, project_dir, run=run)

    assert step.ok is True
    called_cmd = run.call_args[0][0]
    assert str(project_dir / "requirements.txt") in called_cmd
    assert "install" in called_cmd
    assert "-r" in called_cmd


def test_install_requirements_reports_pip_failure(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "requirements.txt").write_text("playwright\n", encoding="utf-8")
    venv_dir = project_dir / ".venv"

    run = MagicMock(return_value=MagicMock(returncode=1, stderr="boom"))
    step = bootstrap.install_requirements(venv_dir, project_dir, run=run)

    assert step.ok is False
    assert "boom" in step.detail


def test_preserve_existing_profile_data_never_touches_profiles(tmp_path):
    """Regression guard: this function must not write into, move, or delete
    anything under profiles/ -- it only reports whether the directory exists."""
    project_dir = tmp_path / "project"
    profiles_dir = project_dir / "profiles" / "bluesky"
    profiles_dir.mkdir(parents=True)
    marker = profiles_dir / "storage_state.json"
    marker.write_text('{"cookies": "fake-not-real"}', encoding="utf-8")

    step = bootstrap.preserve_existing_profile_data(project_dir)

    assert step.ok is True
    assert "untouched" in step.detail
    # The exact same content must still be there, byte for byte.
    assert marker.read_text(encoding="utf-8") == '{"cookies": "fake-not-real"}'


def test_preserve_existing_profile_data_when_absent(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    step = bootstrap.preserve_existing_profile_data(project_dir)
    assert step.ok is True
    assert "None yet" in step.detail


def test_write_first_run_marker_creates_once(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    first = bootstrap.write_first_run_marker(project_dir)
    assert first.ok is True
    marker = project_dir / bootstrap.FIRST_RUN_MARKER
    assert marker.is_file()

    second = bootstrap.write_first_run_marker(project_dir)
    assert second.ok is True
    assert "Already present" in second.detail


def test_official_claude_install_command_mac_and_linux():
    cmd = bootstrap.official_claude_install_command("darwin")
    assert cmd is not None
    assert "curl" in " ".join(cmd)
    assert bootstrap.official_claude_install_command("linux") == cmd


def test_official_claude_install_command_windows_is_none():
    """Windows never gets an auto-run command -- only a manual download link."""
    assert bootstrap.official_claude_install_command("win32") is None


def test_maybe_offer_claude_install_skips_when_already_found():
    step = bootstrap.SetupStep("Claude Code CLI", True, "/usr/bin/claude")
    confirm = MagicMock()
    run = MagicMock()
    bootstrap.maybe_offer_claude_install(step, "linux", confirm=confirm, run=run)
    confirm.assert_not_called()
    run.assert_not_called()


def test_maybe_offer_claude_install_runs_only_after_explicit_yes():
    step = bootstrap.SetupStep("Claude Code CLI", False, "missing")
    run = MagicMock()

    bootstrap.maybe_offer_claude_install(step, "darwin", confirm=lambda _: False, run=run)
    run.assert_not_called()

    bootstrap.maybe_offer_claude_install(step, "darwin", confirm=lambda _: True, run=run)
    run.assert_called_once()
    assert "curl" in " ".join(run.call_args[0][0])


def test_maybe_offer_claude_install_never_runs_on_windows():
    step = bootstrap.SetupStep("Claude Code CLI", False, "missing")
    confirm = MagicMock()
    run = MagicMock()
    bootstrap.maybe_offer_claude_install(step, "win32", confirm=confirm, run=run)
    confirm.assert_not_called()
    run.assert_not_called()


def test_maybe_offer_claude_install_default_confirm_handles_closed_stdin():
    """Regression test: a non-interactive invocation (no terminal attached --
    caught live by the Linux/macOS CI smoke tests, which run non-interactively)
    must not crash with EOFError when no explicit `confirm` callable is given.
    The default confirm function should treat EOF as "no" and let setup
    finish reporting its other steps."""
    step = bootstrap.SetupStep("Claude Code CLI", False, "missing")
    run = MagicMock()

    with patch("builtins.input", side_effect=EOFError):
        # Must not raise.
        bootstrap.maybe_offer_claude_install(step, "darwin", run=run)

    run.assert_not_called()


def test_python_version_supported():
    assert bootstrap.python_version_supported((3, 10)) is True
    assert bootstrap.python_version_supported((3, 12)) is True
    assert bootstrap.python_version_supported((3, 13)) is True
    assert bootstrap.python_version_supported((3, 9)) is False
    assert bootstrap.python_version_supported((2, 7)) is False


def test_create_virtualenv_with_uv_is_idempotent(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    venv_dir = project_dir / ".venv"
    scripts_dir = venv_dir / ("Scripts" if sys.platform == "win32" else "bin")
    scripts_dir.mkdir(parents=True)
    python_name = "python.exe" if sys.platform == "win32" else "python3"
    (scripts_dir / python_name).write_text("fake", encoding="utf-8")

    run = MagicMock()
    step = bootstrap.create_virtualenv_with_uv(tmp_path / "uv.exe", venv_dir, run=run)

    assert step.ok is True
    assert "Already present" in step.detail
    run.assert_not_called()


def test_create_virtualenv_with_uv_runs_uv_venv(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    venv_dir = project_dir / ".venv"
    uv_path = tmp_path / "uv.exe"

    run = MagicMock(return_value=MagicMock(returncode=0, stderr=""))
    step = bootstrap.create_virtualenv_with_uv(uv_path, venv_dir, run=run)

    assert step.ok is True
    called_cmd = run.call_args[0][0]
    assert called_cmd == [str(uv_path), "venv", str(venv_dir)]


def test_create_virtualenv_with_uv_reports_failure(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    venv_dir = project_dir / ".venv"
    uv_path = tmp_path / "uv.exe"

    run = MagicMock(return_value=MagicMock(returncode=1, stderr="no python found"))
    step = bootstrap.create_virtualenv_with_uv(uv_path, venv_dir, run=run)

    assert step.ok is False
    assert "no python found" in step.detail


def test_install_requirements_with_uv_runs_uv_pip_install(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "requirements.txt").write_text("playwright\n", encoding="utf-8")
    venv_dir = project_dir / ".venv"
    uv_path = tmp_path / "uv.exe"

    run = MagicMock(return_value=MagicMock(returncode=0, stderr=""))
    step = bootstrap.install_requirements_with_uv(uv_path, venv_dir, project_dir, run=run)

    assert step.ok is True
    called_cmd = run.call_args[0][0]
    assert str(uv_path) in called_cmd
    assert "pip" in called_cmd
    assert "install" in called_cmd
    assert "--python" in called_cmd
    assert str(project_dir / "requirements.txt") in called_cmd


def test_install_requirements_with_uv_missing_file_is_reported(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    venv_dir = project_dir / ".venv"
    uv_path = tmp_path / "uv.exe"

    run = MagicMock()
    step = bootstrap.install_requirements_with_uv(uv_path, venv_dir, project_dir, run=run)

    assert step.ok is False
    run.assert_not_called()


def test_run_setup_uses_uv_when_uv_path_given(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "requirements.txt").write_text("playwright\n", encoding="utf-8")
    uv_path = tmp_path / "uv.exe"

    which = MagicMock(return_value=None)
    run = MagicMock(return_value=MagicMock(returncode=0, stderr=""))

    with patch("bootstrap.venv.EnvBuilder") as mock_builder_cls:
        steps = bootstrap.run_setup(
            project_dir, platform_name="win32", which=which, run=run, uv_path=uv_path
        )

    names = [s.name for s in steps]
    assert "Python virtual environment (uv)" in names
    assert "Python dependencies (uv)" in names
    assert "Python virtual environment" not in names
    mock_builder_cls.assert_not_called()
    # Two uv invocations (venv + pip install), nothing else.
    assert run.call_count == 2
    for call in run.call_args_list:
        assert str(uv_path) in call.args[0]


def test_run_setup_skip_python_setup_skips_venv_and_deps(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    which = MagicMock(return_value=None)
    run = MagicMock()

    with patch("bootstrap.venv.EnvBuilder") as mock_builder_cls:
        steps = bootstrap.run_setup(
            project_dir, platform_name="win32", which=which, run=run, skip_python_setup=True
        )

    names = [s.name for s in steps]
    assert names == ["Claude Code CLI", "Google Chrome", "Existing profiles/ data", "First-run welcome marker"]
    mock_builder_cls.assert_not_called()
    run.assert_not_called()


def test_run_setup_never_calls_login_or_publish_modules(tmp_path):
    """Full pipeline, fully mocked -- confirms no network/browser/profile
    side effects beyond the mocked pip install."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "requirements.txt").write_text("playwright\n", encoding="utf-8")

    which = MagicMock(return_value=None)
    run = MagicMock(return_value=MagicMock(returncode=0, stderr=""))

    with patch("bootstrap.venv.EnvBuilder") as mock_builder_cls:
        mock_builder_cls.return_value = MagicMock()
        steps = bootstrap.run_setup(project_dir, platform_name="linux", which=which, run=run)

    names = [s.name for s in steps]
    assert names == [
        "Claude Code CLI",
        "Google Chrome",
        "Python virtual environment",
        "Python dependencies",
        "Existing profiles/ data",
        "First-run welcome marker",
    ]
    # pip install is the only subprocess call in the whole pipeline.
    assert run.call_count == 1
    assert (project_dir / bootstrap.FIRST_RUN_MARKER).is_file()
