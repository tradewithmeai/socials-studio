---
name: troubleshoot-publishing
description: Diagnose a publish that failed, hung, produced an uncertain result, or may have duplicated -- across YouTube, Bluesky, LinkedIn or Instagram. Use when a publish attempt errored, the browser closed unexpectedly, a result looks wrong, or you're unsure whether something already posted. Not for first-time login (see the platform's onboard-* skill) and not for a normal, successful publish (see the platform's publish-* skill).
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
  `/p/<code>/` fresh.
- **Cap at ~2 clean attempts.** After that, hand the copy to the user to post by hand rather than
  burn the session.
- Never log in from inside automation to "fix" an auth failure -- use the platform's login wizard.
- Never surface `profiles/*/storage_state.json`.

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

Before reporting success: reload the post fresh and confirm the content rendered -- don't trust the
composer or the script's own return value alone.
