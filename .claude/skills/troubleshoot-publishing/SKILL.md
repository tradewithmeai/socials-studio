---
name: troubleshoot-publishing
description: Diagnose a publish that failed, hung, produced an uncertain result, or may have duplicated -- across YouTube, X, Bluesky, LinkedIn, Instagram, TikTok, or Facebook. Use when a publish attempt errored, the browser closed unexpectedly, a result looks wrong, or you're unsure whether something already posted. Not for first-time login (see the platform's onboard-* skill) and not for a normal, successful publish (see the platform's publish-* skill).
---

# Diagnose a failed post

## When to use it

A publish attempt errored, the browser closed unexpectedly, a result looks wrong, or you're unsure
whether something already posted. Not for first-time login (the platform's `onboard-*` skill) or a
normal, successful publish (the platform's `publish-*` skill).

## Instructions

1. Read the script's error output first -- it names the failure ("Could not click Post", "Still on
   the compose page after clicking Post").
2. Look at the browser window (it always runs visible) before touching anything.
3. Match the symptom below and apply its fix. Re-check.
4. If nothing matches, note what's on screen -- it's a new symptom.

## Guardrails

- **Before any retry, verify independently whether the post actually went out.** A duplicate is
  worse than a delay. On Bluesky, use the public API
  (`https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed?actor=<handle>&limit=3`); on
  LinkedIn, match on text unique to the post via the activity feed; on Instagram, reload
  `/p/<code>/` fresh; on X, find the profile handle dynamically and search loaded posts for text
  unique to what you just posted (there's no public read API to check independently).
- **Cap at ~2 clean attempts.** After that, hand the copy to the user to post by hand rather than
  burn the session.
- Never log in from inside automation to "fix" an auth failure -- use the platform's login wizard.
- Never surface `profiles/*/storage_state.json`.
- **TikTok specifically: never make repeated real (`--confirm-publish`) attempts back-to-back,
  even to debug the same failure.** Observed live during initial TikTok integration testing: a
  burst of real publish attempts against a brand-new unaudited developer app was followed by the
  connected TikTok account being reset entirely -- new/changed username, zero
  followers/posts/friends, asked to redo birthdate/photo/bio, no warning or notification email.
  TikTok has not officially confirmed the cause. The most likely explanation is an agent (this one
  included) retrying a real publish repeatedly without being told to space attempts out --
  exactly the kind of rate-limit mistake that's easy to make without explicit instruction, not
  necessarily a TikTok-specific landmine. Treat it as one anyway: use
  `python -m auth.publish_tiktok --check-status <publish_id>` (read-only) to check an uncertain
  result instead of publishing again, space any further real attempts minutes apart, and stop to
  ask the user rather than retrying live against the API.

## Known failures and recovery

| Symptom | Cause | Fix |
|---|---|---|
| A native OS file-picker dialog opens, then everything dies | Something clicked a file input instead of setting it directly | Never click to open a picker; the publishers already set files directly. If you see a dialog, something deviated. |
| Browser window vanishes the moment the script finishes | The browser is owned by the script process; it dies when the process ends | Expected, not a bug. Do the work inside the script's lifetime -- don't try to hold it open with `input()`. |
| Post/Publish button disabled, text is present | Over the character limit (300 Bluesky / 3,000 LinkedIn), media still processing, a modal is on top, or editor state didn't register (retype instead of `fill()`) | Trim, wait, dismiss the modal with a real click, or retype. |
| Clicked Post, page moved on, nothing posted | Escape opened a "Save/Discard" sheet, or a link caused silent content filtering | Never press Escape to dismiss a typeahead; try posting without the link. |
| Instagram reel published but caption is empty | Caption ends in a hashtag, so the typeahead was still open when Share was clicked | Dismiss the typeahead (click a neutral area, confirm the counter), then Share with a real click. |
| Instagram reel is square or cropped | Crop defaulted to 1:1 | Open "Select Crop" -> 9:16 or Original; confirm the served video is 720x1280, not 720x720. |
| Instagram reel tile is a black square | Frame 0 was mid-fade-in | Measure `YAVG` on frame 0 with ffmpeg; trim the fade before uploading. Never fix the cover via "Select from computer" -- it fails silently. |
| LinkedIn navigation hangs after posting a video | Upload still in flight; navigating away fires `beforeunload` | Stay on the page, let it finish, confirm the composer closed, then verify. |
| "No saved session" / a login page appears | Session expired or never established | Run the platform's login wizard -- never log in from inside automation. |
| "Profile is already in use" / browser won't start | Another (or a stale) process holds the profile lock | Close the other run. Don't kill processes blind while a publish may be in flight. |
| X: clicked Post, page moved on, nothing posted, an accessibility dialog was visible | The alt-text reminder ("Don't forget to make your image accessible") blocks submission until handled | Fill in real alt text and click Post again -- `publish_x.py` does this automatically; if it recurs, the dialog's buttons likely changed. |
| X: the post reached almost nobody | Text began with `@handle`, which X classifies as a reply | Reorder the sentence so it doesn't open with a handle -- this is a reach failure, not a posting failure, so nothing will look wrong in the result. |
| TikTok: account got reset/wiped (new username, zero followers/posts/friends, asked to redo birthdate/photo/bio) after several real publish attempts in a short window | Believed to be a rate-limit/anti-abuse reaction to rapid repeated Content Posting API calls on a brand-new unaudited app -- not officially confirmed by TikTok, but the timing matches an agent retrying without being told to space attempts out | No known recovery -- prevention only. Never retry a real TikTok publish to "debug" an uncertain result; use `--check-status` (read-only) or stop and ask the user instead. Space real attempts minutes apart. |
| Facebook: any step -- this publisher is a community-contributed extra, unverified against a live account | Every selector is a first-draft guess (see `publish-facebook`'s module docstring) | Treat the first real attempt as a live test of the code itself, not a routine post. Use `_save_debug_screenshot`'s output (`profiles/facebook/last_failure_screenshot.png`) to see what the composer actually looked like, then fix the selector together with the user. |

Before reporting success: reload the post fresh and confirm the content rendered -- don't trust the
composer or the script's own return value alone.
