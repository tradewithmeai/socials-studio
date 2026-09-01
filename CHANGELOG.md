# Changelog

This project doesn't yet follow a strict versioning scheme beyond `MAJOR.MINOR.PATCH-beta.N` --
that will firm up once it leaves beta. Dates are when a release was tagged, not when work started.

## Unreleased

### Added

- **TikTok and Facebook, as community-contributed extras** (`auth/publish_tiktok.py`,
  `auth/publish_facebook.py`) -- real, working implementations, held to a lower bar of live
  verification than the five core platforms (YouTube, X, Bluesky, LinkedIn, Instagram). See
  README.md's "Community extras" section, and the `onboard-tiktok`/`publish-tiktok`/
  `onboard-facebook`/`publish-facebook` skills.
  - **TikTok** publishes via OAuth + the official Content Posting API (never a browser), the same
    shape as YouTube. `python -m auth.setup_tiktok_oauth` handles developer-app registration
    through a verified token; `python -m auth.publish_tiktok --check-status <publish_id>` re-checks
    an already-submitted publish without publishing again. Every post is forced to
    private/self-only until the connected developer app passes TikTok's own audit, regardless of
    the requested `--visibility` -- see `publish-tiktok`'s "unaudited-app reality" section for the
    sanctioned manual per-post workaround. This has been exercised against a real developer app and
    account, including two real upload/init failures found and fixed live (an always-chunking bug
    that broke any video at or under TikTok's 64 MiB single-chunk threshold, and a 403 that's
    actually a hard "the connected account must be Private" prerequisite for an unaudited app, not
    just a visibility downgrade) -- both now surface as an actionable message instead of a raw API
    error. **Guardrail, not just documentation:** never make repeated real (`--confirm-publish`)
    TikTok attempts back-to-back, even to debug the same failure -- see
    `troubleshoot-publishing`/`CLAUDE.md` for why this matters in practice, not just in theory.
  - **Facebook** publishes to a personal profile timeline via a saved browser session, the same
    shape as X/Bluesky/LinkedIn/Instagram. **Unlike every other publisher in this repo, it has not
    been exercised against a live account at all** -- every selector is a first-draft guess. Treat
    the first login and first publish as the live test of this code, not a routine connection --
    `onboard-facebook`, `publish-facebook`, and `troubleshoot-publishing` all say so explicitly.
  - Added Facebook to `auth/platforms.py`, `doctor.py`'s session checks, and the shared
    safe-by-default test suite; added a dedicated TikTok OAuth check group to `doctor.py`
    (`python doctor.py --tiktok`). Still safe by default either way -- `--confirm-publish` is
    required for a real publish on both, exactly as for every other platform.
  - **Ten further issues found by code review before any live retest, none of them guessed:**
    (1) `auth/publish_facebook.py` never forced its browser context to English like every other
    publisher does -- fixed with the same `FORCE_ENGLISH_LOCALE` constant. (2) The documented
    `--client-secrets path/to/tiktok_client.json` setup form silently broke every token refresh
    once the file lived outside `profiles/tiktok/` -- `setup_tiktok_oauth.py` now also copies the
    resolved config to the default location. (3) `doctor.py`'s TikTok creator-info check sent a
    possibly-stale `access_token` straight to the API without ever checking whether it had
    expired, unlike the publisher itself, which always refreshes first -- the first fix (calling
    the publisher's own refresh helper) introduced a *second* problem: that helper makes a real
    network call and writes refreshed credentials to disk, exactly the side effect doctor.py's own
    module docstring promises it never has ("Nothing here launches a browser, publishes anything,
    or spends money"). Fixed properly by extracting a read-only staleness check
    (`_token_is_stale`) that doctor.py uses to skip the live check with a warning instead, never
    calling the persisting refresh helper at all. (4) TikTok's real, documented chunking rule
    (confirmed against its Media Transfer Guide, not guessed) is floor division with the final
    chunk absorbing the remainder -- the original implementation used ceiling division with an
    undersized trailing chunk instead, which would have mismatched the chunk count already
    announced to TikTok's init endpoint for any video over 64 MiB. (5) An over-length TikTok
    caption (over 2,200 UTF-16 code units) used to pass a dry run as "valid" and only get rejected
    by the real API after the video upload had already happened -- now checked up front, in UTF-16
    code units rather than Python character count. (6) `auth/publish_facebook.py`'s
    timeline-verification check searched the whole page's text, which could false-positive on the
    profile bio, nav text, or an older post -- scoped to `[role="article"]` post containers
    instead. (7) `publish_tiktok()` always returned `"status": "uploaded"` regardless of what the
    post-upload status check actually said -- a terminal `FAILED` response (TikTok's own
    documented status, with a `fail_reason` field) would have been reported as if it succeeded
    unless the caller manually inspected the nested `status_response`. Now raises on a genuine
    `FAILED` status, and honestly reports `"processing"` rather than `"published"` for anything
    short of TikTok's own `PUBLISH_COMPLETE`. A related, disclosed-but-unfixed gap: this module
    still doesn't check a creator's own account restrictions (e.g. comments disabled globally)
    against the flags it sends before publishing -- confirmed against TikTok's public docs that
    the `creator_info/query` endpoint exposes this, but fixing it properly needs a live account to
    confirm what the init endpoint actually does when a flag doesn't match, so it's left as an
    explicit, documented gap rather than guessed. (8) The FAILED-status fix above was applied to
    `publish_tiktok()`'s immediate post-upload check but not to `check_publish_status()` --
    exactly the documented `--check-status` recovery path a user is told to use *instead* of
    retrying blind. Extracted the shared validation into `_raise_on_terminal_failure()` so both
    call sites behave identically; that recovery path won't tell you a failed post "succeeded"
    either now. (9) `auth/publish_facebook.py`'s article-scoped verification (added earlier this
    round) narrowed false positives from the profile bio/nav text, but could still match an
    *older* post with similar leading text (a repeated caption, or a common generic opening).
    Fixed by snapshotting the profile timeline's existing posts before submitting anything, then
    only counting a match in a post that's genuinely new since that snapshot. (10) That
    before-snapshot only covered the initially-loaded viewport, but the post-submit verification
    loop scrolls to reveal more posts -- so an OLDER post sitting below the fold at snapshot time
    would get revealed by the verification loop's own scrolling and wrongly look "new" too. Fixed
    by having the before-snapshot scroll through the exact same depth
    (`VERIFY_SCROLL_ATTEMPTS` x `VERIFY_SCROLL_PIXELS`) the verification loop does, accumulating
    every article seen at each step (Facebook's feed can remove off-screen articles from the DOM
    as new ones load in, so a single final-position snapshot isn't enough either).
- **YouTube's upload category is no longer hardcoded.** `auth/publish_youtube.py` gained
  `--category-id` (default unchanged: `22`, People & Blogs) -- closes a previously-documented
  defect in the upload path.
- **Every browser this repo launches for X, Bluesky, LinkedIn, and Instagram publishing is now
  forced to English**, not just the login-wizard's own verification step. Extends the existing
  `fix/non-english-onboarding` locale fix (`auth/login_wizard.py`'s `FORCE_ENGLISH_LOCALE`) to each
  publisher's own `launch_persistent_context` call -- a session established under a forced-English
  login could still hit the same class of selector failure at actual publish time, since that
  browser context never inherited the same locale pin.
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
- **Fixed a second, unrelated real hang, in Step 3 (`bootstrap.py`), found only once the `uv`
  redirection hang above was actually fixed.** With `uv`'s output no longer the problem, the
  Windows CI smoke test still hung for the full step timeout -- the self-polling diagnostics added
  above (`Get-CimInstance Win32_Process`, plus heartbeat lines in `setup-python.bat`) showed `uv
  venv`/`uv pip install` had both already succeeded, and `bootstrap.py`'s own `python.exe` was the
  process still running. Root cause: `main()` unconditionally calls `maybe_offer_claude_install`,
  whose default confirm function calls `input()` and only treats a *closed* stdin (`EOFError`) as
  "no" -- but Inno's `runhidden` gives Step 3 a hidden-but-*open* console, which never reaches EOF,
  so it blocked forever instead of declining. `bootstrap.py` gained
  `--no-interactive-claude-offer`, which `setup.iss`'s Step 3 now passes, to skip this prompt
  entirely -- Windows's real, working opt-in for installing Claude Code is the separate finish-page
  checkbox from the bullet above, not this CLI-style stdin prompt.
- **A failed `uv venv`/`uv pip install` on Windows now genuinely stops setup, instead of silently
  reporting success.** Two real bugs, found by review rather than a live CI hang this time:
  `setup-python.bat` only ever checked `uv venv`'s exit code, and even that check was broken --
  `if errorlevel 1` ran *after* an intervening heartbeat `echo`, so it was checking `echo`'s exit
  code, not `uv`'s. Fixed by capturing each `uv` call's exit code into a variable immediately after
  it runs, before anything else touches `%errorlevel%`, and exiting the script with that same
  non-zero code on failure. That alone wasn't enough, though: Inno Setup's `[Run]` section has no
  documented way to inspect a previous entry's exit code at all, so a non-zero `setup-python.bat`
  wouldn't have stopped anything downstream regardless. `setup.iss` now runs `setup-python.bat` from
  `[Code]`'s `CurStepChanged(ssPostInstall)` as a real `Exec()` call instead of a declarative `[Run]`
  entry, checks its `ResultCode`, and shows an error box pointing at `_setup-python.log` when a
  wizard is actually visible (never during a silent/CI install -- gated on `WizardSilent()`). A
  *third* real bug surfaced here too:
  `bootstrap.py`'s invocation was first changed to a declarative `[Run]` entry gated on a
  `PythonSetupSucceeded()` `Check:`, on the assumption that `Check:` would skip it if
  `RunPythonSetup` (running from the same `CurStepChanged(ssPostInstall)`) had already flagged
  failure. Confirmed live: that's backwards -- regular (non-`postinstall`) `[Run]` entries execute
  automatically as soon as `[Files]` are staged, *before* `CurStepChanged(ssPostInstall)` fires, so
  `bootstrap.py`'s entry ran (and could only fail to find a `.venv\Scripts\python.exe` that didn't
  exist yet) before `RunPythonSetup` ever got to run -- meaning `.first-run-pending` was never
  written even on a fully successful Python setup. Fixed by calling `bootstrap.py` directly from
  `[Code]` too (`RunBootstrapPy`), sequenced explicitly after `RunPythonSetup` succeeds. The Claude
  Code offer and "Launch Socials Studio now" -- which genuinely do run later, on the finish page --
  keep their `PythonSetupSucceeded()` `Check:` as an independent second line of defense. A
  *fourth* real bug: making Setup's own exit code non-zero on failure needed a dedicated
  mechanism -- an earlier attempt raised a script exception in `RunPythonSetup`, assuming an
  uncaught exception would itself make Setup exit non-zero. Confirmed live that it doesn't, at
  least under `/VERYSILENT /SUPPRESSMSGBOXES`: the new failure-path CI smoke test (below) showed
  every functional guarantee held -- `bootstrap.py` never ran, `.first-run-pending` never got
  created, `profiles/` stayed untouched -- while Setup's own exit code was still 0. Fixed with
  `GetCustomSetupExitCode()`, the function Setup calls specifically when it would otherwise report
  success, to return a non-zero code when Python setup failed -- the documented mechanism for
  exactly this. A new CI smoke test builds a second installer with a deliberately-broken
  `requirements.txt` and proves, against the real packaged installer: it reports failure (non-zero
  exit code), never writes `.first-run-pending`, and leaves existing `profiles/` data untouched.
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

- **The Windows installer stamped itself as beta.3 after v0.1.0-beta.4 was released.** Reported by
  Codex review: `installer/windows/setup.iss`'s `MyAppVersion` -- baked into the built `.exe` as
  its `AppVersion`, visible in Windows' Programs & Features and the installer's own properties --
  was left at `0.1.0-beta.3`, so the advertised beta.4 download would install and register itself
  as beta.3, misleading for version reporting and upgrade diagnosis. Fixed by bumping
  `MyAppVersion` to `0.1.0-beta.4`. Added a regression test cross-checking it against
  `docs/index.html`'s JSON-LD `softwareVersion` field, since there's no single VERSION file in this
  repo to check against instead.
- **Linux setup no longer mistakes Chromium for the required Google Chrome.** Reported by Codex
  review: `installer/bootstrap.py`'s Linux Chrome detection accepted `chromium` and
  `chromium-browser` in addition to real Chrome executable names, but
  `auth/chrome_setup.find_system_chrome()` (used at runtime for the manual login step) has never
  accepted either -- so the installer could report Chrome as present while onboarding then refused
  the very executable it found. Socials Studio deliberately requires real Google Chrome, not
  Chromium, because its login/publishing design depends on it (see `auth/chrome_setup.py`'s module
  docstring). Fixed by removing `chromium`/`chromium-browser` from the installer's accepted names
  and adding `google-chrome-stable` to the runtime check, so both now recognise exactly the same
  three real-Chrome executable names (`chrome`, `google-chrome`, `google-chrome-stable`) --
  Chromium remains unsupported on both. A new parity test guards against the two lists silently
  diverging again.
- **First real Windows 11 hardware test of the guided installer (PR #7) found one issue.**
  Socials Studio installed and launched successfully through the Start menu, folder trust worked
  as expected, and Claude Code opened correctly inside it -- but the optional desktop shortcut
  failed with `IPersistFile::Save failed; code 0x80070005. Access is denied.`, targeting
  `C:\Users\Public\Desktop\Socials Studio.lnk`. Root cause: `setup.iss` uses
  `PrivilegesRequired=lowest`, but the shortcut targeted `{commondesktop}` (the shared, all-users
  desktop), which can require administrator rights to write to. Fixed by using `{userdesktop}` (the
  current user's own desktop) instead -- the shortcut stays optional via the existing `desktopicon`
  task, still targets `launch.bat`, and still needs no elevation. The rebuilt installer still needs
  one short Windows hardware retest (confirming the desktop shortcut itself) before this platform
  can be described as fully verified.
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
