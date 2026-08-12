# Socials Studio

Read `README.md` first -- it's the source of truth for install, setup, supported platforms, and
current testing status.

## Working in this repo

- `auth/platforms.py` -- per-platform login config (URLs, logged-in detection). X (Twitter) is
  registered here but marked `dormant=True` and excluded from `login_wizard --list` -- see
  `.claude/dormant/README.md` for why and how to reinstate it.
- `auth/login_wizard.py` -- interactive login, saves a session per platform.
- `auth/publish_safety.py` -- the shared safe-by-default gate every publisher uses. See its
  docstring before touching any `publish_<platform>.py` file's dry-run/confirm logic.
- `auth/publish_youtube.py`, `auth/publish_bluesky.py`, `auth/publish_linkedin.py`,
  `auth/publish_instagram.py` -- one publisher per currently-supported platform. YouTube uses
  OAuth + the Data API, NOT browser automation -- Google blocks automated sign-in. Onboarding it
  from scratch goes through `.claude/skills/onboard-youtube/SKILL.md`, not the login wizard.
- `.claude/skills/platform-login/SKILL.md` -- the browser-login wizard for Bluesky/LinkedIn/Instagram
  (not YouTube, not X); read it before driving a login on someone's behalf.

## Rules for an agent operating here

- **Never read, print, or otherwise surface `profiles/*/storage_state.json` or anything under
  `profiles/`.** It holds live session cookies. Treat it like a credential store.
- **Never fill in credentials or 2FA codes programmatically.** The login wizard opens a real
  browser specifically so a human completes login by hand -- automating that defeats the point and
  is what gets accounts flagged.
- Every publisher validates only by default; **`--confirm-publish` (CLI) or `confirm_publish=True`
  (library call) is required to actually publish anything for real.** Don't pass it when
  demonstrating or testing a publisher unless the user explicitly wants a real, live publish.
- Default to `--visibility private` on any real YouTube publish unless told otherwise. A real
  YouTube upload additionally requires exactly one of `--made-for-kids` / `--not-made-for-kids`
  (mutually exclusive, never defaulted or inferred) and `--acknowledge-upload-terms` -- see
  `auth/publish_youtube.py`'s module docstring.
- X (Twitter) is not presented as a supported platform in this release. Don't reference it in
  anything user-facing (docs, onboarding, quick-reference) without checking CHANGELOG.md first.
- If you're extending this to a new platform's publish flow, match the existing pattern: real
  Chrome (not bundled Chromium), `auth.publish_safety.should_publish` for the safety gate, and be
  upfront in your PR/commit about whether you actually ran it against a live account.
- **Hard rule: always close every Chrome process/context you open, and verify zero remain.**
  Never let a script exit, time out, or get interrupted while assuming the browser closed with
  it -- it doesn't. A leftover process holds the profile lock (next run fails with "Browser is
  already in use for ..."), and it can sit there silently for hours or days. After ANY Playwright
  run (success, failure, or interrupted), check for real:
  `Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'chrome' -and $_.CommandLine -match 'profiles' }`
  If anything's still there, close the process with no `--type=` flag in its command line first
  (that's the main browser process; closing it lets children shut down cleanly and flushes the
  profile) -- only force-kill if a graceful close doesn't work. Confirm the count is zero before
  moving on.
