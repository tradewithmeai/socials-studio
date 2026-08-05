---
name: platform-login
description: Log into a social platform (TikTok, Instagram, YouTube, X) once via a real Chrome window, saving the session so future posts don't require re-auth. Use when the user asks to connect/log in/authenticate a platform, or when a publish attempt fails because no saved session exists for that platform.
---

# Platform login wizard

Establishes and persists a logged-in browser session for one platform at a
time. This is a **manual, human-in-the-loop** step -- the wizard opens a
real Chrome window and waits for the user to complete login (including any
2FA/captcha) themselves. Do not attempt to fill in credentials
programmatically; that's what triggers the anti-bot flags this whole
approach exists to avoid.

## When to use this

- The user asks to "connect", "log in to", or "authenticate" a platform.
- A publish/post attempt reports no saved session for a platform.
- The user wants to refresh a session that's gone stale (expired cookies).

## How it works

1. Ensures Playwright's real-Chrome channel is installed
   (`auth/chrome_setup.py::ensure_chrome_installed`) -- pulls a Chrome build
   via Playwright if the machine doesn't have one Playwright can drive.
   Idempotent, safe to run every time.
2. Opens a persistent Chrome context scoped to `profiles/<platform>/` and
   navigates to that platform's login page (`auth/platforms.py`).
3. Polls for a logged-in signal (URL no longer contains the login path, plus
   an optional DOM selector check) every 2 seconds, up to a 10-minute
   default timeout.
4. On success, the session is already persisted (Playwright writes cookies
   and storage into the profile dir as the user interacts), and a portable
   `storage_state.json` snapshot is written alongside it.

## Running it

```
python -m auth.login_wizard --platform tiktok
```

Supported platform keys: `tiktok`, `instagram`, `youtube`, `x`. List them
with `python -m auth.login_wizard --list`.

## Notes for the agent

- Tell the user explicitly that a Chrome window will open and they need to
  log in by hand -- don't run this silently in the background.
- `profiles/` is gitignored. Never read, print, or otherwise surface the
  contents of `profiles/*/storage_state.json` -- it contains live session
  cookies.
- The per-platform "logged in" detection (`login_url_marker`,
  `logged_in_selector` in `auth/platforms.py`) is best-effort and can go
  stale if a platform changes its login flow. If the wizard times out
  repeatedly right after the user visibly completed login, that selector
  likely needs updating -- flag it rather than silently retrying forever.
- This only covers the login/session-creation step. Actually posting a
  video using the saved session is handled by the `auth.publish_*` modules
  -- see the roadmap for the MCP-server wrapper that isn't built yet.
