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
  - creates the project's `.venv` and installs `requirements.txt` into it (see the Python
    provisioning note below for how this differs on Windows),
  - confirms (without ever writing to) an existing `profiles/` directory, so a reinstall or
    upgrade never touches saved logins or OAuth tokens,
  - writes `.first-run-pending`, which `CLAUDE.md` instructs Claude to notice, act on once (a
    welcome + offer to connect a platform), and delete.

### Python provisioning: Windows uses `uv`, macOS/Linux use the system Python

**Windows is genuinely automatic.** An earlier version of this installer bundled Python's official
[embeddable distribution](https://docs.python.org/3/using/windows.html#the-embeddable-package) to
run `bootstrap.py` before any Python existed on the machine. That doesn't work: the embeddable
distribution ships without `ensurepip`, so `venv.EnvBuilder(with_pip=True)` cannot bootstrap pip
into a fresh venv created from it -- this is a genuine limitation of that distribution, not
something specific to this project's code. The installer now bundles a pinned
[`uv`](https://github.com/astral-sh/uv) binary instead. `uv` manages its own Python provisioning
(downloading an isolated interpreter if it needs to) and has no `ensurepip` dependency, so the
Inno Setup `[Run]` section uses it directly (`uv venv`, then `uv pip install`) before handing off
to `bootstrap.py --skip-python-setup` for the remaining checks. This is verified by an actual CI
smoke test on `windows-latest` (silent install, then confirming `.venv\Scripts\python.exe` and the
other expected files exist) -- see `.github/workflows/build-installers.yml`.

**macOS and Linux are not fully automatic yet.** `install.sh` on both looks for a system
`python3.10`+ (checking the real runtime version, not just trusting a `python3.1x`-looking binary
name) and runs `bootstrap.py` with it directly, the same way the CLI route works. If no qualifying
Python is found, the installer explains how to get one and stops -- it does not attempt a silent
or `sudo` install. This is a real, current limitation, not something the public docs describe as
fully automatic; see README.md's Testing status section for the exact wording used.

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

CI builds all three artifacts with checksums, and smoke-tests each one on its own OS's GitHub
runner (silent/non-interactive install, verify the expected files exist, verify a reinstall never
touches a file under `profiles/`) -- see `.github/workflows/build-installers.yml`. It runs on a
manual trigger, an `installer-v*` tag push, or any pull request that touches installer files --
so an installer change is genuinely built and smoke-tested before merge, not just reviewed as
text. It never runs on every push to `main`, and it never publishes a GitHub release by itself --
reviewing and publishing the built artifacts is still a manual step. A CI smoke test is not a
substitute for a human running the installer on their own machine; see README.md's Testing status
section for the current, honest state of each platform.

## What this deliberately does NOT do

- Log into any social platform, or collect a platform credential, at any point during install.
- Publish anything.
- Require Git or a GitHub account for the download route.
- Bundle or redistribute Claude Code -- it's detected, and installed only via Anthropic's own
  official installer, only after the user says yes.
- Freeze the repository into a binary Claude Code can't read from.
