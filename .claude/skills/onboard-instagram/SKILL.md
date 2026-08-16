---
name: onboard-instagram
description: Set up Instagram publishing for Socials Studio from scratch (login through a verified video roundtrip test, including the known caption-drop bug). Use when the user wants to connect, set up, or onboard Instagram, or a publish fails because no session exists yet.
---

# Instagram onboarding

## When to use it

Connecting Instagram for the first time, or a publish fails because no session exists yet. Not for
routine publishing once connected (`publish-instagram`) or diagnosing a failed publish
(`troubleshoot-publishing`).

## Instructions

1. Log in:
   ```bash
   python -m auth.login_wizard --platform instagram
   ```
   Opens a plain Chrome window to Instagram's login page. Log in yourself (2FA included, dismiss
   cookie banners), then close the window completely -- the wizard waits, then verifies the session.
2. Verify before a real publish:
   ```bash
   python -m auth.publish_instagram video.mp4 --caption "test"
   ```
   Validates only by default. Check for `"session_found": true`.
3. Real publish, once verified:
   ```bash
   python -m auth.publish_instagram video.mp4 --caption "post caption" --confirm-publish
   ```
4. Verify independently: find your own profile, then reload `https://www.instagram.com/p/<code>/`
   fresh (never `/reel/<code>/`, which can render another account's caption) and confirm the
   caption rendered and the served video is 720x1280.
5. Clean up: open the post's "More Options" menu, click Delete, confirm, then check the profile
   grid afterward for the post's ID.

## Guardrails

- Never log in from inside automation -- Instagram challenges automated logins the same way
  Google does for YouTube.
- `--confirm-publish` is required for a real publish; without it, this only validates.
- Never read, print, or surface `profiles/*/storage_state.json`.
- Close every Chrome process/context you open and verify none remain before finishing.
- Reel (video) publishing is live-verified end-to-end. `auth/publish_instagram.py` also accepts
  image files, but that path has not been independently live-verified -- treat a real image
  publish with the caution of untested code: dry-run first, verify the result carefully.

## Known failures and recovery

- **Caption can silently drop on publish.** Root cause: the caption ends in hashtags, so
  Instagram's autocomplete typeahead is still open when Share is clicked, and the commit is
  swallowed. Cap fix attempts at two clean tries; if still gone, tell the user to add it by hand
  rather than keep grinding.
- **Reel cover can be a black square** if the source video fades in from black (frame 0 becomes
  the cover). Check before uploading: `ffmpeg -i video.mp4 -vf "signalstats,metadata=print:file=-"
  -frames:v 1 -f null -` and read `YAVG` -- ~7 is black (trim the fade first), ~12+ is real content.
- **Crop can default to 1:1** even on sources already at 1080x1920. After publishing, confirm the
  served video is 720x1280, not 720x720 -- 720x720 means it was cropped.
- Always verify at `/p/<code>/`, never `/reel/<code>/`.
