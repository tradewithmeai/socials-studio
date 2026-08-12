---
name: platform-login
description: Log into a social platform (Instagram, Bluesky, LinkedIn) once via a plain, non-automated Chrome window, saving the session so future posts don't require re-auth. Does NOT cover YouTube -- see onboard-youtube instead. Use when the user asks to connect/log in/authenticate a platform, or when a publish attempt fails because no saved session exists for that platform.
---

# Platform login wizard

Establishes and persists a logged-in browser session for one platform at a
time. This is a **manual, human-in-the-loop, two-step** process, not a
single Playwright run -- and the two-step split is load-bearing, not
incidental.

## Why it's two steps

Confirmed live across multiple platforms: attempting the login itself from
inside an automation-controlled browser (even Playwright's real-Chrome
channel, not bundled Chromium) triggers anti-automation defenses -- Google's
"This browser or app may not be secure", Instagram/LinkedIn "suspicious
login" interstitials and SMS challenges. These trigger on automation signals
themselves (`navigator.webdriver`, the CDP control port, automation launch
switches), not on the login method used. A session a human already
established is not subject to these defenses -- Playwright reusing normal
cookies afterward is fine.

The fix: **never attempt login from inside automation.**

1. `_manual_login_step` launches a completely plain, human-launched Chrome
   process via `subprocess.Popen` (no CDP, no automation flags --
   indistinguishable from double-clicking the Chrome icon), scoped to
   `profiles/<platform>/`, pointed at that platform's login page
   (`auth/platforms.py`). It blocks until the user closes that window
   themselves after completing login (2FA/captcha included).
2. `_verify_session` then opens the same profile with Playwright
   (`launch_persistent_context`, real-Chrome channel) in read-only mode --
   navigates to the login URL and checks `login_url_marker` no longer
   matches plus `logged_in_selector` is visible. It never fills in a login
   form; it only reads the already-authenticated state.

Do not attempt to fill in credentials programmatically at any point; that's
exactly what triggers the anti-bot flags this whole approach exists to
avoid.

## When to use this

- The user asks to "connect", "log in to", or "authenticate" a platform.
- A publish/post attempt reports no saved session for a platform.
- The user wants to refresh a session that's gone stale (expired cookies).

## Running it

```
python -m auth.login_wizard --platform instagram
```

Supported platform keys: `instagram`, `bluesky`, `linkedin`. List them
with `python -m auth.login_wizard --list`.

**YouTube is NOT in this list, deliberately.** It uses OAuth + the Data API
instead of browser login entirely -- see the `onboard-youtube` skill.

## Notes for the agent

- Tell the user explicitly that a Chrome window will open and they need to
  log in by hand, then close that window completely when done -- don't run
  this silently in the background.
- `profiles/` is gitignored. Never read, print, or otherwise surface the
  contents of `profiles/*/storage_state.json` -- it contains live session
  cookies.
- The per-platform "logged in" detection (`login_url_marker`,
  `logged_in_selector` in `auth/platforms.py`) is best-effort and can go
  stale if a platform changes its login flow. If verification fails
  repeatedly right after the user visibly completed login, that selector
  likely needs updating -- flag it rather than silently retrying forever.
- This only covers the login/session-creation step. Actually posting a
  video using the saved session is handled by the `auth.publish_*` modules
  -- see each platform's `onboard-*` skill for the verified working pattern.
- **Hard rule: always close every Chrome process/context you open, and
  verify zero remain** -- see the root `CLAUDE.md` for the check command.
