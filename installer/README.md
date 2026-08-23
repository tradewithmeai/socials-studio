# Installer architecture

This directory packages Socials Studio for someone with a Claude subscription but no GitHub, Git,
or Python experience. It is a **source-visible bootstrap installer**, not an app-freezing build:

- The Windows `.exe` (built with [Inno Setup](https://jrsoftware.org/isinfo.php)), the macOS
  `.zip`, and the Linux `.tar.gz` all copy the plain repository -- every `.md` skill, every `.py`
  module -- onto disk exactly as it exists here. None of it is compiled, obfuscated, or hidden
  from Claude Code once installed.
- `bootstrap.py` is the one piece of setup logic shared by all three platforms. It's ordinary,
  readable Python with no dependency on the rest of this repo, so it can run before
  `requirements.txt` is installed. It:
  - checks for Claude Code and Google Chrome on PATH/common install locations (never installs
    Chrome; on macOS/Linux, offers to run Anthropic's own official Claude Code installer after
    explicit confirmation -- never on Windows, and never bundling Claude Code itself),
  - creates the project's `.venv` and installs `requirements.txt` into it,
  - confirms (without ever writing to) an existing `profiles/` directory, so a reinstall or
    upgrade never touches saved logins or OAuth tokens,
  - writes `.first-run-pending`, which `CLAUDE.md` instructs Claude to notice, act on once (a
    welcome + offer to connect a platform), and delete.
- Windows needs a way to run `bootstrap.py` before the user has any Python installed at all. The
  Inno Setup script bundles a minimal
  [embeddable Python](https://docs.python.org/3/using/windows.html#the-embeddable-package) that
  CI downloads at build time, used only to run `bootstrap.py` once. That embeddable copy is not
  the runtime Socials Studio uses day to day -- `bootstrap.py` creates a normal `.venv` for that,
  same as the CLI route.
- macOS and Linux expect a system Python 3.10+ already present (common on both); if it's missing,
  the install script explains how to get one rather than trying to install it silently.

## Files

| File | Purpose |
|---|---|
| `bootstrap.py` | Shared setup logic, tested in `tests/test_installer_bootstrap.py` |
| `windows/setup.iss` | Inno Setup script producing `Socials-Studio-Setup.exe` |
| `windows/launch.bat` | Desktop/Start Menu launcher |
| `macos/install.sh` | Stages the repo, runs `bootstrap.py`, installs the launcher |
| `macos/SocialsStudio.command` | Double-click launcher |
| `linux/install.sh` | Stages the repo, runs `bootstrap.py`, installs the launcher + `.desktop` entry |
| `linux/socials-studio-launch.sh` | Launcher script |
| `linux/socials-studio.desktop` | Applications-menu entry template |

## Building

CI builds all three artifacts with checksums -- see
`.github/workflows/build-installers.yml`. It doesn't run automatically on every push; trigger it
manually (`workflow_dispatch`) or by pushing an `installer-v*` tag. It never publishes a GitHub
release by itself -- reviewing and publishing the built artifacts is still a manual step.

## What this deliberately does NOT do

- Log into any social platform, or collect a platform credential, at any point during install.
- Publish anything.
- Require Git or a GitHub account for the download route.
- Bundle or redistribute Claude Code -- it's detected, and installed only via Anthropic's own
  official installer, only after the user says yes.
- Freeze the repository into a binary Claude Code can't read from.
