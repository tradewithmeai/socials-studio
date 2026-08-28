# Changelog

This project doesn't yet follow a strict versioning scheme beyond `MAJOR.MINOR.PATCH-beta.N` --
that will firm up once it leaves beta. Dates are when a release was tagged, not when work started.

## Unreleased

### Added

- **Guided installers for Windows, macOS, and Linux** (`installer/`), aimed at someone with a
  Claude subscription but no GitHub, Git, or Python experience. `Socials-Studio-Setup.exe`
  (Windows), plus `.zip`/`.tar.gz` installer bundles for macOS/Linux, are built by CI (see
  `.github/workflows/build-installers.yml`) with SHA256 checksums, and smoke-tested on each
  platform's own GitHub runner before merge -- silent install, verify the expected files exist,
  verify a reinstall never touches a file under `profiles/`. Each installer copies the plain
  repository source onto disk -- it is not compiled or frozen into an opaque binary, so Claude
  Code retains full access to every skill, Markdown file, and Python module -- then prepares a
  Python virtual environment and installs dependencies. It checks for Claude Code and Google
  Chrome without installing either silently: it offers to run Anthropic's own official Claude
  Code installer after explicit confirmation on every platform (via WinGet on Windows when
  available, otherwise Anthropic's PowerShell installer -- an opt-in checkbox on the packaged
  installer's finish page, not an auto-run command). It never logs into a platform, never
  publishes anything, and never touches an
  existing `profiles/` directory, so a reinstall or upgrade preserves saved logins and OAuth
  tokens. A first-run marker (`.first-run-pending`) tells Claude Code to welcome the user and
  offer guided platform setup on the very first launch only -- see the note in `CLAUDE.md`.
- **Windows Python provisioning uses `uv`, not an embeddable-Python + `venv` approach.** The
  official Windows embeddable Python distribution ships without `ensurepip`, so
  `venv.EnvBuilder(with_pip=True)` cannot bootstrap pip into a venv created from it -- this was
  caught before shipping, not assumed to work. The installer now bundles a pinned
  [`uv`](https://github.com/astral-sh/uv) binary, which manages its own Python provisioning and
  has no `ensurepip` dependency; `uv venv` + `uv pip install` now do this work on Windows, with a
  CI smoke test proving the resulting `.venv` actually exists after a silent install.
- macOS/Linux `install.sh` now checks the *actual runtime version* of any candidate `python3`
  (rejecting anything older than 3.10) instead of trusting a `python3.1x`-looking filename.
- `installer/bootstrap.py` gained `--uv-path` and `--skip-python-setup`, and
  `create_virtualenv_with_uv`/`install_requirements_with_uv` alongside the existing
  venv/pip-based functions, so the same script serves both provisioning paths.
- **Windows now genuinely offers to install Claude Code, not just a link.** Verified against
  Anthropic's current documentation (https://code.claude.com/docs/en/setup): `winget install
  Anthropic.ClaudeCode` when WinGet is available, otherwise the official PowerShell installer
  (`irm https://claude.ai/install.ps1 | iex`). The packaged Windows installer offers this as an
  unchecked, opt-in checkbox on its finish page (`setup.iss`'s `ClaudeCodeMissing()` check +
  `[Run]` entry), exactly like the existing "Launch Socials Studio now" checkbox -- it only
  appears if Claude Code isn't already found, and only runs if the user checks it and clicks
  Finish. Declining leaves the Socials Studio launcher installed and explains that Claude Code is
  still required.
- **Windows' venv now provably comes from uv's own managed Python 3.12, not the machine's.**
  `uv venv --python 3.12 --python-preference only-managed` -- `only-managed` verified against uv
  0.5.11's real `PythonPreference` enum, not guessed. The Windows CI smoke test proves this by
  reading the resulting `.venv\pyvenv.cfg` and confirming it does not reference the GitHub
  runner's own pre-installed Python, confirming the venv's python reports `3.12.x`, and confirming
  a real dependency (`playwright`) imports -- both after the first install and again after a
  reinstall.
- **Fixed a real hang: `uv`'s output pipe filling up blocked it forever when run through Inno
  Setup's `[Run]` mechanism.** Caught live, twice, by the Windows CI smoke test genuinely hanging
  for 9+ minutes with zero progress. A direct diagnostic step (added permanently -- see
  `.github/workflows/build-installers.yml`) proved `uv venv --python 3.12 --python-preference
  only-managed` completes in seconds when run on its own; the same command via Inno Setup's Exec
  never returned. Root cause: `uv` writes a live-updating progress display while downloading, and
  Inno Setup's `[Run]` entries don't drain a child process's output pipes -- once uv's writes fill
  the OS pipe buffer, it blocks indefinitely waiting for a reader that never comes. Fixing this took
  three attempts, each caught live by CI: redirecting to `NUL` stopped the hang but hid a genuine
  `uv` failure with no way to see why (the venv silently never got created); redirecting to a real
  log file via an inline `cmd.exe /C "..." >"...log" 2>&1` Parameters string kept the hang fixed but
  introduced a *different* silent failure, because cmd.exe's `/C` argument parser mishandles a
  command line that both starts with a quoted path and contains a `>` redirection -- it failed
  instantly with "The filename, directory name, or volume label syntax is incorrect" before `uv`
  ever ran, and Inno Setup surfaced no error for it. Moving the redirection into a real bundled
  script, `installer/windows/setup-python.bat`, removed that quoting hazard -- but calling that
  `.bat` directly as the `[Run]` entry's `Filename` hit a *third*, also live-confirmed failure: Inno's
  plain `Exec` calls Win32's `CreateProcess`, which doesn't support a `.bat`/`.cmd` file as the
  application image directly, and the CI job hung for the full 8-minute step timeout with zero
  output. The actual fix: `setup.iss`'s `[Run]` entry now wraps the script in `cmd.exe /C "path"`
  with a single quoted argument and no redirection at that outer level -- the redirection stays
  inside the `.bat` itself. The "Smoke test -- silent install" step prints `_setup-python.log`'s
  contents if the expected files are still missing. Also added `timeout-minutes` to every Windows
  step that can plausibly hang, so a future regression fails cleanly within minutes instead of
  running for hours unnoticed.
- **macOS/Linux CI smoke tests no longer mask failures.** Removed every `|| true` on the installer
  script invocation and the post-extraction `chmod +x` repair -- the packaged archive must contain
  executable scripts as downloaded (`test -x` now asserts this before running anything), and any
  unexpected non-zero exit from `install.sh` now genuinely fails the test. A harmless fake
  `claude` stub on `PATH` (Chrome is already present on both runner images) gets an unambiguous,
  fully-successful result instead of one partially masked by "Claude Code missing." Verification
  now also runs the installed Python and imports a real dependency, not just checking `.venv`
  exists.
- Focused unit tests for the installer's setup logic (`tests/test_installer_bootstrap.py`) --
  fully mocked, no real virtual environment, network call, or `profiles/` access.
- README and the website got a plain-language pass: the two supported installation routes (ask
  an existing Claude Code install, or use the guided installer) are now explained above the fold,
  ahead of the command-line instructions, which remain available for contributors. Wording was
  corrected to stop claiming "the installer sets up Python for you" on macOS/Linux, where that
  isn't true yet -- only Windows currently provisions Python fully automatically.

**Testing status, stated per-platform, not as one blanket claim:** Windows has automated build and
installation testing (CI smoke test) but is still awaiting a human test on a normal Windows
machine. Linux has had its installer mechanics manually tested on Ubuntu 24.04 x64 (source
install, venv creation, dependency install, launcher/desktop entry, byte-for-byte `profiles/`
preservation on reinstall) in addition to the CI smoke test -- real Chrome/account publishing was
not tested through this package. macOS has only the automated CI runner test; no human hardware
test has been received. No platform is described as fully verified until a person completes
installation and successfully launches Socials Studio -- see README.md's Testing status section.

### Fixed

- **Onboarding could fail on a non-English machine.** `auth/platforms.py`'s `logged_in_selector`
  values are English strings (e.g. `svg[aria-label="Home"]`), so on a machine with the OS/Chrome
  display language set to something else, a real, successful login could still fail verification
  because the platform rendered that control's accessible name in the local language instead.
  `auth/login_wizard.py` now forces English (`--lang=en-US` / `locale="en-US"`) inside the
  isolated `profiles/<platform>/` Chrome profile it already creates for each platform -- for both
  the manual login window and the Playwright verification step -- without touching the user's own
  Chrome profile or system language.

## v0.1.0-beta.2 (2026-08-17)

An agentic social media studio, operated through Claude Code -- not a fixed CLI toolkit. Give it
an idea, a campaign brief, or finished media, and it creates platform-specific content, coordinates
a multi-platform campaign, reviews it with you, and publishes approved posts to **YouTube, X
(Twitter), Bluesky, LinkedIn, and Instagram**. Works with OpenMontage output specifically -- and
with a finished video file from anywhere else, or with no video at all -- as an independent
project, not an official integration.

### Supported platforms

- **All five platforms are supported: YouTube, X (Twitter), Bluesky, LinkedIn, and Instagram.**
  X publishes through a saved, human-created browser session via Playwright, the same as Bluesky,
  LinkedIn, and Instagram -- not the X API. YouTube uses OAuth + the official Data API, the only
  platform here that doesn't touch a browser at all, since Google blocks automated sign-in
  outright. Every platform is discoverable through `login_wizard --list`, `doctor.py`, and an
  active `onboard-<platform>`/`publish-<platform>` skill pair.

### Safety

- **Every publisher is now safe by default.** Previously, calling a `publish_<platform>.py`
  library function or its CLI with no explicit `dry_run` flag would publish for real, immediately
  -- private-by-default visibility on YouTube didn't fix this, since it only helps if you already
  remembered to make it a dry run in the first place. Now, `--confirm-publish` (CLI) or
  `confirm_publish=True` (library call) is required to actually publish anything; everything else,
  including calling with no flags at all, validates only. `--dry-run` remains available as an
  explicit, equivalent way to request validate-only behavior, and always wins if both are passed.
  See `auth/publish_safety.py` and the README's "Publishing safety" section.
- **YouTube uploads now require explicit Made for Kids declaration and upload-terms
  acknowledgment** before a real upload can proceed, per the YouTube API Services Terms of
  Service, Section 9.1. Neither is required for a dry run. See
  `auth/publish_youtube.py`'s module docstring for the exact policy citations.
- **YouTube OAuth scopes were narrowed** to the minimum `doctor.py` and publishing actually use
  (`youtube.upload`, `youtube.readonly`) -- the broad `youtube` manage scope was requested but
  never used by any code path in this repo, and has been dropped. **Existing users must
  re-authorize**: delete `profiles/youtube/token.json` and re-run
  `python -m auth.setup_youtube_oauth`. A token issued under the old scopes will fail on refresh
  with a "scope has changed" error rather than silently keep working.

### The agentic application model

- **Positioned as an agentic application operated through Claude Code, not a fixed set of CLI
  commands.** Give it an idea, a campaign brief, or finished media; it can create
  platform-specific content, coordinate a multi-post campaign, review it with you, publish
  approved posts, inspect subsequent activity on request, and extend itself to another platform
  when asked -- composing or adapting this repository's authentication, validation, and
  publishing primitives rather than being limited to a fixed command list. `AGENTS.md` is a full
  guided tour for an agent operating or contributing to this repo; `README.md`'s capability
  section and `docs/index.html` describe the same model for a human reader.
- **`openmontage-context` skill and OpenMontage positioning strengthened.** OpenMontage can create
  the video; Socials Studio can request, understand, adapt, and publish the resulting media as
  part of a wider campaign -- file-based compatibility, not a technical integration, with no
  dependency on OpenMontage's code. The independent-project, not-affiliated-with-OpenMontage
  disclaimer is preserved everywhere this positioning appears.
- **TikTok removed entirely.** It was never implemented as a real publisher; references to it as
  a planned or draft platform have been removed from docs, skills, and the roadmap rather than
  left as an unfulfilled claim.

### Added

- `PRIVACY.md` -- what's stored locally, where, for how long, and why. Linked from the README,
  the website footer, and the YouTube OAuth setup docs.
- A unit test suite (`tests/`) covering every publisher's default-safe behavior, the
  confirm-publish gate, invalid/missing media paths, YouTube's visibility/Made-for-Kids/upload-
  warning handling, and OAuth scope constants. No live credentials, browser profiles, or network
  access required.
- GitHub Actions CI running the test suite and a syntax check across supported Python versions.
- `requirements-dev.txt` for test/lint dependencies, kept separate from runtime dependencies.
- `.claude/skills/openmontage-context/SKILL.md` (carried over from the prior beta.1 development
  cycle, listed here for completeness) -- grounds publish copy in an OpenMontage project's own
  script/brief/render-report artifacts.
- `onboard-<platform>` and `publish-<platform>` skills for every supported platform (YouTube, X,
  Bluesky, LinkedIn, Instagram), plus `platform-login` and `troubleshoot-publishing`, each
  restructured to a consistent when-to-use / instructions / guardrails / known-failures format
  and independently discoverable as a Claude Code skill (a directory containing `SKILL.md`, not a
  flat file).

### Fixed

- **X (Twitter) is supported.** X is listed alongside YouTube, Bluesky, LinkedIn, and Instagram
  everywhere a platform list appears, `auth/platforms.py` carries no dormant flag for it, and
  `onboard-x`/`publish-x` are active, discoverable skills. X publishes through a saved,
  human-created browser session via Playwright, not the X API -- the same safe-by-default
  validation and `--confirm-publish` gate apply as every other platform.
- **Agent capability detection now follows the current local code, configuration, and active
  skills, not `README.md`.** `CLAUDE.md` and `AGENTS.md` previously told an agent to treat the
  README as "the source of truth" for supported platforms. Both now say to read the README for
  install guidance and declared release status, but to determine actual capabilities from what's
  actually in the repository -- and to report a discrepancy rather than suppress a working
  capability when the two disagree.
- `SECURITY.md` inaccurately claimed there were "no platform API keys or OAuth client
  credentials involved" and that only two files touch a browser or filesystem outside the project
  directory -- both were true when YouTube was the only publisher and false since Bluesky,
  LinkedIn, Instagram, and OAuth-based YouTube publishing were added. Rewritten to describe what's
  actually in the codebase.
- README troubleshooting referred to "no saved YouTube session" -- YouTube has never used a
  browser session; it uses an OAuth token. Corrected to describe the actual failure mode and fix.
- `CLAUDE.md` claimed YouTube was "the only publish path implemented so far" -- stale since
  Bluesky, LinkedIn, and Instagram publishers were added. Corrected.
- The website (`docs/index.html`) linked to the `v0.1.0-beta.1` release tag while `main` had
  diverged with substantially more functionality -- pointed at the repository's releases listing
  instead, so it never sends a visitor to stale code. The website currently still links to the
  releases listing while beta.2 remains untagged; `RELEASE_CHECKLIST.md` covers updating that link
  to this release specifically once it's published.
- Runtime dependency declarations had no upper bounds. Added major-version ceilings so a future
  breaking release upstream can't silently break this project's install.

## v0.1.0-beta.1 (2026-08-05)

Initial public beta. Login wizard and publishing for YouTube, X, Bluesky, LinkedIn, and Instagram.
See the [v0.1.0-beta.1 release](https://github.com/tradewithmeai/socials-studio/releases/tag/v0.1.0-beta.1)
for the original notes.
