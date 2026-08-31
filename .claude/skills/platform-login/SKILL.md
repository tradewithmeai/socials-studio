---
name: platform-login
description: Log into a social platform (Instagram, Bluesky, LinkedIn, X, Facebook) once via a plain, non-automated Chrome window, saving the session so future posts don't require re-auth. Does NOT cover YouTube or TikTok -- see onboard-youtube / onboard-tiktok instead. Use when the user asks to connect/log in/authenticate a platform, or when a publish attempt fails because no saved session exists for that platform.
---

# Platform login wizard

## When to use it

The user asks to connect, log in to, or authenticate Instagram, Bluesky, LinkedIn, X, or Facebook,
a publish/post attempt reports no saved session, or a session has gone stale. Not for YouTube or
TikTok -- both use OAuth, see `onboard-youtube` / `onboard-tiktok`.

## Instructions

```
python -m auth.login_wizard --platform instagram
```

Supported platform keys: `instagram`, `bluesky`, `linkedin`, `x`, `facebook` (list with
`python -m auth.login_wizard --list`). Tell the user a Chrome window will open and they need to
log in by hand, then close that window completely when done. The wizard then verifies the session
read-only via Playwright, without touching a login form.

**Facebook is a community-contributed extra, unverified against a live account** -- see
`.claude/skills/publish-facebook/SKILL.md` before telling a user it's ready. Treat the first
login-wizard run against it as the live test of `auth/platforms.py`'s Facebook
`logged_in_selector`, not a known-good value.

That window opens in English regardless of the machine's OS/Chrome language -- the isolated
`profiles/<platform>/` profile is forced to `en-US` so `auth/platforms.py`'s English-language
selectors keep matching. This never changes the user's normal Chrome profile or system language.

## Guardrails

- Never attempt login from inside automation, and never fill in credentials or 2FA programmatically
  -- this is what triggers anti-automation defenses (Google's "This browser or app may not be
  secure", Instagram/LinkedIn suspicious-login challenges). A session a human already established
  is not subject to these defenses.
- Never read, print, or surface `profiles/*/storage_state.json`.
- Close every Chrome process/context you open and verify none remain before finishing.

## Known failures and recovery

If verification fails repeatedly right after the user visibly completed login, the platform's
"logged in" detection selector (`auth/platforms.py`) may have gone stale -- flag it rather than
silently retrying forever.
