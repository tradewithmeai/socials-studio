---
name: onboard-x
description: Set up X (Twitter) publishing for Socials Studio from scratch (login through a verified post roundtrip test). Use when the user wants to connect, set up, or onboard X/Twitter, or a publish fails because no session exists yet.
---

# X (Twitter) onboarding

## When to use it

Connecting X for the first time, or a publish fails because no session exists yet. Not for
routine publishing once connected (`publish-x`) or diagnosing a failed publish
(`troubleshoot-publishing`).

## Instructions

1. Log in:
   ```bash
   python -m auth.login_wizard --platform x
   ```
   Opens a plain Chrome window to X's login page. Log in yourself (2FA included, dismiss cookie
   banners), then close the window completely -- the wizard waits, then verifies the session by
   checking for the home-timeline nav link.
2. Verify before a real publish:
   ```bash
   python -m auth.publish_x "test text" --dry-run
   ```
   Validates only. Check for `"session_found": true`.
3. Real publish, once verified:
   ```bash
   python -m auth.publish_x "post text" --confirm-publish
   python -m auth.publish_x "post text" --video path/to/video.mp4 --confirm-publish
   ```
   No draft/review step -- a successful call posts immediately and publicly (X has no
   private/unlisted post state).
4. Verify independently: find the profile handle dynamically (don't hardcode it), navigate to
   `https://x.com<profile_href>`, and search the loaded posts for text unique to the one you just
   made. X has no public unauthenticated read API for this.
5. Clean up the test post: from the profile page, open the post's caret/more-options menu, select
   Delete, confirm, then re-search the profile to confirm it's gone.

## Guardrails

- Never log in from inside automation -- X's sign-in flow (including "Sign in with Google") is
  challenged by the same anti-automation defenses as other platforms.
- `--confirm-publish` is required for a real publish; `--dry-run` validates only.
- Never read, print, or surface `profiles/*/storage_state.json`.
- Close every Chrome process/context you open and verify none remain before finishing.
- X publishing uses a saved, human-created browser session driven by Playwright -- it does not use
  the X API. Browser automation can break if X changes its interface, and may trigger platform
  restrictions; treat that as a reliability risk to watch for, not a reason to avoid the platform.

## Known failures and recovery

- **The alt-text/accessibility reminder can silently block a post with an image attached.** X
  shows "Don't forget to make your image accessible" after the first Post click if there's no alt
  text; the post does not submit while it's open. `auth/publish_x.py` handles this by filling in
  real alt text (falling back to the post's own text) and clicking Post again. If it recurs, the
  dialog's buttons likely changed.
- **A post opening with `@handle` is classified as a reply**, reaching only people who follow both
  accounts -- reorder the sentence rather than lead with a handle.
- 280-character limit is weighted, not literal -- see `publish-x` for the exact counting rules.
