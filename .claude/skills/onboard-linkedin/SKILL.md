---
name: onboard-linkedin
description: Set up LinkedIn publishing for Socials Studio from scratch (login through a verified text + video roundtrip test). Use when the user wants to connect, set up, or onboard LinkedIn, or a LinkedIn publish fails because no session exists yet.
---

# LinkedIn onboarding

## When to use it

Connecting LinkedIn for the first time, or a publish fails because no session exists yet. Not for
routine publishing once connected (`publish-linkedin`) or diagnosing a failed publish
(`troubleshoot-publishing`).

## Instructions

1. Log in:
   ```bash
   python -m auth.login_wizard --platform linkedin
   ```
   Opens a plain Chrome window to LinkedIn's login page. Log in yourself (2FA included, dismiss
   cookie banners), then close the window completely -- the wizard waits, then verifies the session.
2. Verify before a real publish:
   ```bash
   python -m auth.publish_linkedin "test text"
   ```
   Validates only by default. Check for `"session_found": true`.
3. Real publish, once verified:
   ```bash
   python -m auth.publish_linkedin "post text" --confirm-publish
   python -m auth.publish_linkedin "post text" --video path/to/video.mp4 --confirm-publish
   ```
4. Verify independently: reload `https://www.linkedin.com/in/<profile-slug>/recent-activity/all/`
   and search by text unique to the post -- the top item is not reliably the newest.
5. Clean up the test post from the activity feed: open its "..." menu, click "Delete post", confirm
   in the dialog, then reload the feed to confirm it's gone.

## Guardrails

- Never log in from inside automation -- always the human-driven wizard above.
- `--confirm-publish` is required for a real publish; without it, this only validates.
- **This publishes immediately** -- there is no draft/review step once Post is clicked.
- **Media can never be added to a LinkedIn post after publishing.** Text and media must go in the
  same call, or accept two separate posts.
- LinkedIn carries more reputational weight than most platforms this repo publishes to. Before the
  first real publish, ask the user how they want to use it here -- milestones only, routine
  posting, or something else -- and follow whatever they say.
- Never read, print, or surface `profiles/*/storage_state.json`.
- Close every Chrome process/context you open and verify none remain before finishing.

## Known failures and recovery

- **Post button stays disabled while a video is processing** -- wait, this is not an error.
- **The composer closing does not mean the post is done.** LinkedIn continues an attached video's
  upload in the background. Don't navigate away while it could still be running -- doing so kills
  the upload. Wait for the composer to close, then verify via the activity feed.
- **Don't trust a script's own `"status": "posted"` result on its own** -- verify via the activity
  feed every time (see Instructions above).
