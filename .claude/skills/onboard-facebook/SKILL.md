---
name: onboard-facebook
description: Set up Facebook publishing for Socials Studio from scratch -- but this integration is a community-contributed extra, unverified against a live account. Use when the user wants to connect, set up, or onboard Facebook, or a Facebook publish fails because no session exists yet.
---

# Facebook onboarding (experimental extra)

## Before you start

**Unlike every other platform this repo publishes to, Facebook has not been exercised against a
live account at all.** `auth/publish_facebook.py` and `auth/platforms.py`'s Facebook entry are a
first-draft implementation, pattern-matched against the same general composer shape that worked
for LinkedIn and Bluesky -- every selector is a best guess, not a confirmed-live value. Tell the
user this plainly before starting: the first login and first publish attempt are the live test of
this code, not a routine connection, and selectors will likely need fixing together with the user
against whatever Facebook's actual DOM turns out to be.

Do a **text-only** test post before ever attaching media -- if the composer selectors are wrong,
you want to find that out without also debugging a file-chooser interaction at the same time.

## When to use it

Connecting Facebook for the first time, or a publish fails because no session exists yet. Not for
routine publishing once connected (`publish-facebook`) or diagnosing a failed publish
(`troubleshoot-publishing`).

## Instructions

1. Log in:
   ```bash
   python -m auth.login_wizard --platform facebook
   ```
   Opens a plain Chrome window to Facebook's login page. Log in yourself (2FA included, dismiss
   cookie/consent banners), then close the window completely -- the wizard waits, then verifies
   the session using `auth/platforms.py`'s Facebook `logged_in_selector`
   (`div[aria-label="Create a post"]`), which is itself unverified.
   - If verification reports "not logged in" right after a real, successful login, the selector
     has likely gone stale (or was simply wrong to begin with) -- open the home feed yourself in
     that same profile and inspect the actual composer-opener element before assuming the login
     failed.
2. Verify before a real publish:
   ```bash
   python -m auth.publish_facebook "test text"
   ```
   Validates only by default. Check for `"session_found": true`.
3. **First real publish -- text only, no media**:
   ```bash
   python -m auth.publish_facebook "test text" --confirm-publish
   ```
   Watch the browser window while this runs. If it fails, `auth/publish_facebook.py` saves a
   screenshot to `profiles/facebook/last_failure_screenshot.png` right before raising -- use it to
   see what the composer actually looked like and fix the selector, rather than guessing blind.
4. Only once a text-only post is confirmed working, try media:
   ```bash
   python -m auth.publish_facebook "test text" --image path/to/photo.jpg --confirm-publish
   python -m auth.publish_facebook "test text" --video path/to/video.mp4 --confirm-publish
   ```
5. Verify independently: reload the profile's own timeline and search for text unique to the test
   post -- don't trust the script's own `"status": "posted"` / `"verified"` result alone. The
   result dict deliberately says so too when it couldn't confirm the post itself.
6. Clean up the test post from the profile timeline by hand once confirmed.

## Guardrails

- Never log in from inside automation -- always the human-driven wizard above.
- `--confirm-publish` is required for a real publish; without it, this only validates.
- Never read, print, or surface `profiles/*/storage_state.json`.
- Close every Chrome process/context you open and verify none remain before finishing.
- Don't tell the user a Facebook post "should just work" the way X/Bluesky/LinkedIn/Instagram now
  do -- say plainly that this is untested and the first attempt is a joint debugging session.

## Known failures and recovery

- **Composer opener not found** -- the "What's on your mind?" click target didn't match. Check
  `profiles/facebook/last_failure_screenshot.png`, then update `_open_composer`'s selector in
  `auth/publish_facebook.py` against what's actually on screen.
- **Post button stays disabled** -- likely attached media still processing; the code already
  retries for a while, but if it still fails, wait longer by hand and re-check.
- **Post button never found at all** -- Facebook's dialog markup differs from what
  `_click_dialog_button` expects; inspect the failure screenshot and update the selector.
- If a publish fails, looks uncertain, or you suspect a duplicate, use `troubleshoot-publishing`
  rather than retrying blind.
