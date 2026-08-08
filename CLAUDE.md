# Socials Studio

Read `README.md` first -- it's the source of truth for install, setup, supported platforms, and
current testing status.

## Working in this repo

- `auth/platforms.py` -- per-platform login config (URLs, logged-in detection).
- `auth/login_wizard.py` -- interactive login, saves a session per platform.
- `auth/publish_youtube.py` -- the only publish path implemented so far. Uses OAuth + the YouTube
  Data API, NOT browser automation -- Google blocks automated sign-in. Onboarding this from
  scratch goes through `.claude/skills/onboard-youtube/SKILL.md`, not the login wizard.
- `.claude/skills/platform-login/SKILL.md` -- the browser-login wizard for X/Bluesky/LinkedIn/Instagram
  (not YouTube); read it before driving a login on someone's behalf.

## Rules for an agent operating here

- **Never read, print, or otherwise surface `profiles/*/storage_state.json` or anything under
  `profiles/`.** It holds live session cookies. Treat it like a credential store.
- **Never fill in credentials or 2FA codes programmatically.** The login wizard opens a real
  browser specifically so a human completes login by hand -- automating that defeats the point and
  is what gets accounts flagged.
- Default to `--dry-run` when demonstrating or testing `publish_youtube` unless the user explicitly
  wants a real, live publish.
- Default to `--visibility private` on any real publish unless told otherwise.
- If you're extending this to a new platform's publish flow, match the existing pattern: real
  Chrome (not bundled Chromium), safe defaults, dry-run support, and be upfront in your PR/commit
  about whether you actually ran it against a live account.
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
