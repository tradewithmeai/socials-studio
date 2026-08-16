---
name: onboard-bluesky
description: Set up Bluesky publishing for Socials Studio from scratch (login through a verified text + video roundtrip test). Use when the user wants to connect, set up, or onboard Bluesky, or a Bluesky publish fails because no session exists yet.
---

# Bluesky onboarding

## When to use it

Connecting Bluesky for the first time, or a publish fails because no session exists yet. Not for
routine publishing once connected (`publish-bluesky`) or diagnosing a failed publish
(`troubleshoot-publishing`).

## Instructions

1. Log in:
   ```bash
   python -m auth.login_wizard --platform bluesky
   ```
   Opens a plain Chrome window to bsky.app. Log in yourself, then close the window completely --
   the wizard waits for it to close, then verifies the session.
2. Verify before a real publish:
   ```bash
   python -m auth.publish_bluesky "test text"
   ```
   Validates only by default. Check for `"session_found": true`.
3. Real publish, once verified:
   ```bash
   python -m auth.publish_bluesky "post text" --confirm-publish
   python -m auth.publish_bluesky "post text" --video path/to/video.mp4 --confirm-publish
   ```
   Bluesky has no draft/visibility concept -- a successful publish is immediately live.
4. Verify independently via Bluesky's public API, not the browser:
   ```bash
   curl -s "https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed?actor=<handle>&limit=3"
   ```
   For a video post, confirm the record's `embed.$type` is `app.bsky.embed.video`.
5. Clean up the test post from `https://bsky.app/profile/<handle>` (open its menu, Delete), then
   re-check the public API to confirm it's gone.

## Guardrails

- Never log in from inside automation -- always the human-driven wizard above.
- `--confirm-publish` is required for a real publish; every command above validates only without it.
- Never read, print, or surface `profiles/*/storage_state.json`.
- Close every Chrome process/context you open and verify none remain before finishing.

## Known failures and recovery

- If verification reports "not logged in" right after a real login, Bluesky's login-verification
  selector (`[aria-label="Compose new post"]`) may have gone stale -- check it still exists on
  bsky.app before assuming the wizard is broken.
- Video length/size limits are looser than commonly quoted -- don't pre-emptively trim a clip
  expecting a refusal; let the platform reject it if it will.
- 300-character limit, counted literally (emoji count as 1; a URL counts its full length) -- see
  `publish-bluesky` for copy rules.
