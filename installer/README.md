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
    Chrome; offers to run Anthropic's own official Claude Code installer after explicit
    confirmation on every platform, never bundling Claude Code itself -- see "Offering to install
    Claude Code" below for how this differs between the CLI route and the packaged Windows
    installer specifically),
  - creates the project's `.venv` and installs `requirements.txt` into it (see the Python
    provisioning note below for how this differs on Windows),
  - confirms (without ever writing to) an existing `profiles/` directory, so a reinstall or
    upgrade never touches saved logins or OAuth tokens,
  - writes `.first-run-pending`, which `CLAUDE.md` instructs Claude to notice, act on once (a
    welcome + offer to connect a platform), and delete.

### Python provisioning: Windows uses a uv-*managed* Python, macOS/Linux use the system Python

**Windows is genuinely automatic, and genuinely doesn't depend on whatever Python (if any) is
already on the machine.** An earlier version of this installer bundled Python's official
[embeddable distribution](https://docs.python.org/3/using/windows.html#the-embeddable-package) to
run `bootstrap.py` before any Python existed on the machine. That doesn't work: the embeddable
distribution ships without `ensurepip`, so `venv.EnvBuilder(with_pip=True)` cannot bootstrap pip
into a fresh venv created from it -- this is a genuine limitation of that distribution, not
something specific to this project's code. The installer now bundles a pinned
[`uv`](https://github.com/astral-sh/uv) binary instead. `uv` manages its own Python provisioning
(downloading an isolated interpreter if it needs to) and has no `ensurepip` dependency, so the
Inno Setup `[Run]` section uses it directly: `uv venv --python 3.12 --python-preference
only-managed`, then `uv pip install`, before handing off to `bootstrap.py --skip-python-setup` for
the remaining checks. Both `uv` calls are routed through `cmd.exe /C ... >"{app}\_setup-python.log"
2>&1` -- confirmed live, running the same `uv` command directly completes in seconds, but run
exactly the same way through Inno Setup's plain Exec (no output redirection) the CI job hung
indefinitely: `uv`'s live-updating download progress fills the child process's output pipe, which
Inno's `[Run]` mechanism never drains, so the write blocks forever once the OS pipe buffer is full.
Redirecting to a real log file (not `NUL`) removes the pipe entirely while keeping any failure
diagnosable -- an earlier version of this fix redirected to `NUL`, which stopped the hang but also
hid a genuine `uv` failure with no way to see why; the smoke test now prints this log's contents on
failure. `--python-preference only-managed` is verified against uv 0.5.11's real
[`PythonPreference` enum](https://github.com/astral-sh/uv/blob/0.5.11/crates/uv-python/src/discovery.rs)
-- it forces uv to provision its own downloaded Python 3.12 rather than opportunistically using a
system Python if one happens to be present. The Windows CI smoke test proves this, not just the
build succeeding: it reads the resulting `.venv\pyvenv.cfg` and confirms it does *not* reference
the GitHub runner's own pre-installed Python (which lives under a well-known `hostedtoolcache`
path) or match whatever `python` the runner has on PATH, confirms the venv's own python reports
`3.12.x`, and confirms a real dependency (`playwright`) imports successfully -- both on first
install and again after a reinstall. See `.github/workflows/build-installers.yml`.

**macOS and Linux are not fully automatic yet.** `install.sh` on both looks for a system
`python3.10`+ (checking the real runtime version, not just trusting a `python3.1x`-looking binary
name) and runs `bootstrap.py` with it directly, the same way the CLI route works. If no qualifying
Python is found, the installer explains how to get one and stops -- it does not attempt a silent
or `sudo` install. This is a real, current limitation, not something the public docs describe as
fully automatic; see README.md's Testing status section for the exact wording used.

### Offering to install Claude Code

`bootstrap.py`'s `official_claude_install_command()` returns a real, verified command for every
platform (checked against [Anthropic's current documentation](https://code.claude.com/docs/en/setup)):
`curl -fsSL https://claude.ai/install.sh | bash` on macOS/Linux; on Windows, `winget install
Anthropic.ClaudeCode` when WinGet is available, otherwise Anthropic's official PowerShell
installer (`irm https://claude.ai/install.ps1 | iex`). This project never bundles or redistributes
Claude Code itself -- only Anthropic's own installers, and only after explicit consent.

On the CLI route (asking Claude Code to set the project up directly) this is an interactive
yes/no prompt on every platform, handled by `maybe_offer_claude_install()`. On the **packaged
Windows installer** specifically, `bootstrap.py` runs hidden (no console the user could answer a
prompt in), so the real opt-in there is a **checkbox on the Inno Setup finish page** -- unchecked
by default, exactly like "Launch Socials Studio now" -- that only appears if Claude Code isn't
already found (`ClaudeCodeMissing()` in `setup.iss`'s `[Code]` section), and only runs if the user
checks it and clicks Finish. Declining either way is fine: the launcher installs regardless, and
the user is told plainly that Claude Code is still required before Socials Studio will work.

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
runner -- see `.github/workflows/build-installers.yml`. Every smoke test treats an unexpected
non-zero exit from the installer script as a real failure: no `|| true`, no post-extraction
`chmod` repair (the archive must contain executable scripts as packaged -- `test -x` asserts this
before running anything). macOS/Linux get a harmless fake `claude` stub on `PATH` (Chrome is
already genuinely present on both runner images) so a clean run produces an unambiguous,
fully-successful result rather than one partially masked by "Claude Code missing" -- and beyond
file existence, each test actually runs the installed Python and imports a real dependency
(`playwright`). The Windows job additionally proves the venv came from uv's own managed Python,
not the runner's -- see the Python provisioning note above.

CI runs on a manual trigger, an `installer-v*` tag push, or any pull request that touches
installer files -- so an installer change is genuinely built and smoke-tested before merge, not
just reviewed as text. It never runs on every push to `main`, and it never publishes a GitHub
release by itself -- reviewing and publishing the built artifacts is still a manual step. A CI
smoke test is not a substitute for a human running the installer on their own machine; see
README.md's Testing status section for the current, honest state of each platform.

## What this deliberately does NOT do

- Log into any social platform, or collect a platform credential, at any point during install.
- Publish anything.
- Require Git or a GitHub account for the download route.
- Bundle or redistribute Claude Code -- it's detected, and installed only via Anthropic's own
  official installer, only after the user says yes.
- Freeze the repository into a binary Claude Code can't read from.
