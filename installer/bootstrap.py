#!/usr/bin/env python3
"""Cross-platform first-time setup for Socials Studio's installer route.

Run once by the platform-specific installer (Windows .exe, macOS .command,
Linux install.sh) after the plain repository source has been copied/cloned
onto disk. This script never touches a social platform, never launches a
publish/login flow, and never overwrites `profiles/` -- it only prepares a
Python virtual environment, checks for Claude Code and Chrome, and writes a
launcher.

This is deliberately readable, ordinary Python -- not compiled or obfuscated
-- so an agent (or a curious human) can open it and see exactly what it does.
It has no dependency on the rest of this repository, so it can run before
`requirements.txt` is installed.

Usage:
    python bootstrap.py --project-dir /path/to/socials-studio
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import venv
from pathlib import Path
from typing import Callable

RunFn = Callable[..., subprocess.CompletedProcess]
WhichFn = Callable[[str], "str | None"]

FIRST_RUN_MARKER = ".first-run-pending"

# Common Chrome install locations, checked only if `shutil.which` misses --
# this never launches or downloads anything, it just looks.
WINDOWS_CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]
MACOS_CHROME_PATHS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]
LINUX_CHROME_NAMES = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]


class SetupStep:
    """One line of the setup report: what was checked, and the result."""

    def __init__(self, name: str, ok: bool, detail: str = "") -> None:
        self.name = name
        self.ok = ok
        self.detail = detail

    def __repr__(self) -> str:  # pragma: no cover - cosmetic only
        mark = "OK" if self.ok else "ACTION NEEDED"
        return f"[{mark}] {self.name}: {self.detail}" if self.detail else f"[{mark}] {self.name}"


def find_claude_cli(which: WhichFn = shutil.which) -> str | None:
    """Locate an installed Claude Code CLI on PATH. Never installs it."""
    return which("claude")


def official_claude_install_command(platform_name: str) -> list[str] | None:
    """The shell command for Anthropic's own official Claude Code installer.

    Returns None on Windows: the native Windows installer is a browser
    download, not a scriptable command this installer can safely pipe into a
    shell -- so Windows always gets a link, not an auto-run command. This
    project never bundles or redistributes Claude Code itself either way.
    """
    if platform_name in ("darwin", "linux"):
        return ["bash", "-c", "curl -fsSL https://claude.ai/install.sh | bash"]
    return None


def maybe_offer_claude_install(
    claude_step: SetupStep,
    platform_name: str,
    confirm: Callable[[str], bool] | None = None,
    run: RunFn = subprocess.run,
) -> None:
    """If Claude Code is missing, offer to run Anthropic's official installer.

    Does nothing if Claude Code was already found. Never runs anything
    without explicit confirmation, and never on Windows (see
    official_claude_install_command). This project does not redistribute
    Claude Code -- it only offers to invoke Anthropic's own installer.
    """
    if claude_step.ok:
        return
    command = official_claude_install_command(platform_name)
    if command is None:
        print(
            "Install Claude Code from https://claude.com/claude-code, sign in with a "
            "qualifying Claude account, then run this setup again."
        )
        return
    ask = confirm or (lambda prompt: input(prompt).strip().lower() == "y")
    if ask("Install Claude Code now using Anthropic's official installer? [y/N] "):
        run(command)
    else:
        print("Skipped. Install it later from https://claude.com/claude-code.")


def find_chrome(
    platform_name: str,
    which: WhichFn = shutil.which,
    path_exists: Callable[[str], bool] = lambda p: Path(p).exists(),
) -> str | None:
    """Locate an installed Chrome browser. Never downloads or installs it."""
    if platform_name == "win32":
        for candidate in WINDOWS_CHROME_PATHS:
            if path_exists(candidate):
                return candidate
        return None
    if platform_name == "darwin":
        for candidate in MACOS_CHROME_PATHS:
            if path_exists(candidate):
                return candidate
        return None
    for name in LINUX_CHROME_NAMES:
        found = which(name)
        if found:
            return found
    return None


def check_claude_code(which: WhichFn = shutil.which) -> SetupStep:
    path = find_claude_cli(which)
    if path:
        return SetupStep("Claude Code CLI", True, path)
    return SetupStep(
        "Claude Code CLI",
        False,
        "Not found on PATH. Install it from https://claude.com/claude-code, then "
        "run this setup again. A qualifying Claude account and sign-in are required "
        "-- this installer does not create one for you.",
    )


def check_chrome(platform_name: str, which: WhichFn = shutil.which) -> SetupStep:
    path = find_chrome(platform_name, which)
    if path:
        return SetupStep("Google Chrome", True, path)
    return SetupStep(
        "Google Chrome",
        False,
        "Not found. X, Bluesky, LinkedIn, and Instagram publishing all drive a real "
        "Chrome window -- install it from https://www.google.com/chrome/ before "
        "connecting those platforms. YouTube doesn't need it.",
    )


def create_virtualenv(project_dir: Path, venv_dir: Path) -> SetupStep:
    """Create the .venv Socials Studio's own scripts will run in.

    Idempotent: if venv_dir already has a python executable, this is a no-op
    (an upgrade re-run should not need to rebuild it from scratch).
    """
    existing_python = venv_dir / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python3")
    if existing_python.exists():
        return SetupStep("Python virtual environment", True, f"Already present at {venv_dir}")

    venv.EnvBuilder(with_pip=True, clear=False).create(str(venv_dir))
    return SetupStep("Python virtual environment", True, f"Created at {venv_dir}")


def install_requirements(
    venv_dir: Path,
    project_dir: Path,
    run: RunFn = subprocess.run,
) -> SetupStep:
    pip = venv_dir / ("Scripts/pip.exe" if sys.platform == "win32" else "bin/pip")
    requirements = project_dir / "requirements.txt"
    if not requirements.is_file():
        return SetupStep("Python dependencies", False, f"{requirements} not found")

    result = run(
        [str(pip), "install", "-r", str(requirements)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return SetupStep(
            "Python dependencies",
            False,
            f"pip install failed (exit {result.returncode}): {result.stderr[-400:]}",
        )
    return SetupStep("Python dependencies", True, "Installed")


def preserve_existing_profile_data(project_dir: Path) -> SetupStep:
    """Confirm `profiles/` is untouched by this run.

    This function does not copy, move, or delete anything under `profiles/` --
    it exists to make the guarantee explicit and testable: an upgrade or
    re-run of this script must never disturb saved logins, OAuth tokens, or
    anything else a user has already connected.
    """
    profiles_dir = project_dir / "profiles"
    if profiles_dir.exists():
        return SetupStep(
            "Existing profiles/ data",
            True,
            "Found and left untouched -- saved logins and tokens are preserved.",
        )
    return SetupStep("Existing profiles/ data", True, "None yet -- nothing to preserve.")


def write_first_run_marker(project_dir: Path) -> SetupStep:
    """Drop a marker file so Claude knows to run the welcome flow on first launch.

    CLAUDE.md instructs an agent to check for this file, welcome the user,
    explain what Socials Studio can do, offer guided platform setup, and then
    delete the marker -- so the welcome only happens once, not every session.
    """
    marker = project_dir / FIRST_RUN_MARKER
    if marker.exists():
        return SetupStep("First-run welcome marker", True, "Already present")
    marker.write_text(
        "This file tells Claude Code to run the first-time welcome flow.\n"
        "See CLAUDE.md. Claude deletes this file once the welcome is done.\n",
        encoding="utf-8",
    )
    return SetupStep("First-run welcome marker", True, f"Written to {marker}")


def run_setup(
    project_dir: Path,
    platform_name: str = sys.platform,
    which: WhichFn = shutil.which,
    run: RunFn = subprocess.run,
) -> list[SetupStep]:
    """Run every setup step in order and return the full report.

    Never logs into a platform, never publishes anything, never contacts a
    social platform's servers. The only network activity here is `pip
    install` fetching Python packages, and only after Chrome/Claude checks
    (which are local-only) have already run.
    """
    venv_dir = project_dir / ".venv"
    steps = [
        check_claude_code(which),
        check_chrome(platform_name, which),
        create_virtualenv(project_dir, venv_dir),
    ]
    steps.append(install_requirements(venv_dir, project_dir, run))
    steps.append(preserve_existing_profile_data(project_dir))
    steps.append(write_first_run_marker(project_dir))
    return steps


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", required=True, help="Path to the Socials Studio checkout")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    if not project_dir.is_dir():
        print(f"Project directory not found: {project_dir}")
        return 1

    print(f"Setting up Socials Studio in {project_dir}\n")
    steps = run_setup(project_dir)
    for step in steps:
        print(step)

    claude_step = steps[0]
    if not claude_step.ok:
        print()
        maybe_offer_claude_install(claude_step, sys.platform)

    failed = [s for s in steps if not s.ok]
    if failed:
        print("\nSetup needs your attention before Socials Studio is ready -- see above.")
        return 1
    print("\nSetup complete. Launch Socials Studio to get started.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
