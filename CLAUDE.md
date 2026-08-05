# Socials Studio

Read `README.md` first -- it's the source of truth for install, setup, supported platforms, and
current testing status.

## Working in this repo

- `auth/platforms.py` -- per-platform login config (URLs, logged-in detection).
- `auth/login_wizard.py` -- interactive login, saves a session per platform.
- `auth/publish_youtube.py` -- the only publish path implemented so far.
- `.claude/skills/platform-login/SKILL.md` -- the skill wrapping the login wizard; read it before
  driving a login on someone's behalf.

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
