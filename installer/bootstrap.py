#!/usr/bin/env python3
"""Cross-platform first-time setup for Socials Studio's installer route.

Run once by the platform-specific installer (Windows .exe, macOS .command,
Linux install.sh) after the plain repository source has been copied/cloned
onto disk. This script never touches a social platform, never launches a
publish/login flow, and never overwrites `profiles/` -- it checks for Claude
Code and Chrome, prepares a Python virtual environment (see "Python
provisioning" below), and writes a first-run marker.

This is deliberately readable, ordinary Python -- not compiled or obfuscated
-- so an agent (or a curious human) can open it and see exactly what it does.
It has no dependency on the rest of this repository, so it can run before
`requirements.txt` is installed.

## Python provisioning: why Windows is different

Windows: the installer bundles a pinned `uv` binary (https://github.com/astral-sh/uv) and passes
its path via `--uv-path`. `uv` creates the venv and installs dependencies; this script's own
`create_virtualenv`/`install_requirements` are skipped in that case. This exists because Python's
official embeddable distribution for Windows -- the obvious-looking alternative to avoid asking
a user to install Python -- ships without `ensurepip`, so `venv.EnvBuilder(with_pip=True)` cannot
bootstrap pip into a new venv created from it; a straightforward embeddable-Python + `venv`
approach genuinely does not work on Windows without extra unpacking that the embeddable
distribution deliberately omits. `uv` sidesteps this entirely -- it manages Python and venvs
itself and doesn't depend on `ensurepip`. This is proven by the Windows CI smoke test in
`.github/workflows/build-installers.yml`, not assumed.

macOS/Linux: this script uses the system's own `python3` (via the plain `venv` module, which
works fine there -- only the Windows *embeddable* distribution has the `ensurepip` gap) to create
`.venv` and install `requirements.txt` with `pip`, exactly like the CLI route in README.md. The
install scripts (`installer/macos/install.sh`, `installer/linux/install.sh`) require a system
Python 3.10+ and explain clearly, without attempting a silent/sudo install, if none is found --
this is a genuine limitation of the current macOS/Linux installers, not something the public
docs claim is fully automatic.

Usage:
    python bootstrap.py --project-dir /path/to/socials-studio [--uv-path /path/to/uv] [--skip-python-setup]
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
MIN_PYTHON_VERSION = (3, 10)

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


def python_version_supported(version_info: tuple[int, int]) -> bool:
    """Whether a (major, minor) Python version meets Socials Studio's minimum.

    Used by installer\\macos\\install.sh and installer\\linux\\install.sh (via a
    one-line `python3 -c` invocation, since the version check has to happen
    *before* any Python script -- including this one -- can be trusted to
    run) to reject an old system `python3` rather than silently accepting
    whatever the name resolves to.
    """
    return version_info >= MIN_PYTHON_VERSION


def create_virtualenv(project_dir: Path, venv_dir: Path) -> SetupStep:
    """Create the .venv Socials Studio's own scripts will run in, using the
    system Python this script itself is running under (via the stdlib `venv`
    module). This works reliably on macOS/Linux; see the module docstring
    for why Windows uses `create_virtualenv_with_uv` instead.

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


def create_virtualenv_with_uv(uv_path: Path, venv_dir: Path, run: RunFn = subprocess.run) -> SetupStep:
    """Windows path: create .venv using a bundled, pinned `uv` binary instead
    of the stdlib `venv` module. See the module docstring for why -- the
    Windows embeddable Python distribution can't bootstrap pip via
    `ensurepip`, so `uv` (which manages its own Python provisioning and
    doesn't depend on `ensurepip` at all) replaces that step entirely.

    Idempotent, same as create_virtualenv.
    """
    existing_python = venv_dir / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python3")
    if existing_python.exists():
        return SetupStep("Python virtual environment (uv)", True, f"Already present at {venv_dir}")

    result = run([str(uv_path), "venv", str(venv_dir)], capture_output=True, text=True)
    if result.returncode != 0:
        return SetupStep(
            "Python virtual environment (uv)",
            False,
            f"uv venv failed (exit {result.returncode}): {result.stderr[-400:]}",
        )
    return SetupStep("Python virtual environment (uv)", True, f"Created at {venv_dir}")


def install_requirements_with_uv(
    uv_path: Path,
    venv_dir: Path,
    project_dir: Path,
    run: RunFn = subprocess.run,
) -> SetupStep:
    requirements = project_dir / "requirements.txt"
    if not requirements.is_file():
        return SetupStep("Python dependencies (uv)", False, f"{requirements} not found")

    venv_python = venv_dir / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python3")
    result = run(
        [str(uv_path), "pip", "install", "--python", str(venv_python), "-r", str(requirements)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return SetupStep(
            "Python dependencies (uv)",
            False,
            f"uv pip install failed (exit {result.returncode}): {result.stderr[-400:]}",
        )
    return SetupStep("Python dependencies (uv)", True, "Installed")


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
    uv_path: Path | None = None,
    skip_python_setup: bool = False,
) -> list[SetupStep]:
    """Run every setup step in order and return the full report.

    Never logs into a platform, never publishes anything, never contacts a
    social platform's servers. The only network activity here is dependency
    installation (`pip install` or `uv pip install`), and only after
    Chrome/Claude checks (which are local-only) have already run.

    `uv_path`, when given, routes venv creation and dependency installation
    through the bundled `uv` binary instead of the stdlib `venv` module --
    see the module docstring for why Windows needs this.

    `skip_python_setup=True` skips venv creation and dependency installation
    entirely -- for the Windows installer, where the Inno Setup `[Run]`
    section already invoked `uv` directly before calling this script, so
    redoing it here would be redundant, not incorrect, but wasteful.
    """
    venv_dir = project_dir / ".venv"
    steps = [
        check_claude_code(which),
        check_chrome(platform_name, which),
    ]

    if not skip_python_setup:
        if uv_path is not None:
            steps.append(create_virtualenv_with_uv(uv_path, venv_dir, run))
            steps.append(install_requirements_with_uv(uv_path, venv_dir, project_dir, run))
        else:
            steps.append(create_virtualenv(project_dir, venv_dir))
            steps.append(install_requirements(venv_dir, project_dir, run))

    steps.append(preserve_existing_profile_data(project_dir))
    steps.append(write_first_run_marker(project_dir))
    return steps


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", required=True, help="Path to the Socials Studio checkout")
    parser.add_argument(
        "--uv-path",
        default=None,
        help="Path to a bundled uv binary (Windows only) -- routes venv/dependency setup through it",
    )
    parser.add_argument(
        "--skip-python-setup",
        action="store_true",
        help="Skip venv creation and dependency install (Windows: already done via uv in [Run])",
    )
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    if not project_dir.is_dir():
        print(f"Project directory not found: {project_dir}")
        return 1

    uv_path = Path(args.uv_path).expanduser().resolve() if args.uv_path else None

    print(f"Setting up Socials Studio in {project_dir}\n")
    steps = run_setup(project_dir, uv_path=uv_path, skip_python_setup=args.skip_python_setup)
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
