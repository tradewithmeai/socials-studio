---
name: publish-instagram
description: Prepare, adapt, validate, review and publish a reel (video) or image post to an already-connected Instagram account. Use when the user wants to draft, review or publish Instagram content -- not for first-time login (see onboard-instagram) and not for diagnosing a failed/uncertain publish (see troubleshoot-publishing).
---

# Publish to Instagram

## When to use it

Drafting, reviewing, or publishing Instagram content for an already-connected account. Not for
first-time login (`onboard-instagram`) or diagnosing a failed/uncertain publish
(`troubleshoot-publishing`).

## Instructions

```bash
python -m auth.publish_instagram path/to/video.mp4 --caption "..."                    # validates only (default)
python -m auth.publish_instagram path/to/video.mp4 --caption "your caption" --confirm-publish
```

Requires a saved session (`python -m auth.login_wizard --platform instagram`).

Before uploading, check the video:
- **Aspect**: reels are 9:16. Build a purpose-made vertical version rather than pillarboxing a
  landscape source.
- **Cover frame**: frame 0 becomes the cover. If the source fades in from black, check with
  `ffmpeg -i video.mp4 -vf "signalstats,metadata=print:file=-" -frames:v 1 -f null -` and read
  `YAVG` -- ~7 is black (trim the fade first), ~12+ is real content.

Caption: 2,200 characters. Instagram doesn't linkify text -- point people at the bio instead of
pasting a URL. Put hashtags at the end.

Verify after posting: reload `https://www.instagram.com/p/<code>/` fresh (never `/reel/<code>/`,
which can render another account's caption) and confirm the caption rendered and the served video
is 720x1280 (720x720 means it was cropped).

## Guardrails

- `--confirm-publish` is required for a real publish; without it, this only validates.
- **Reel (video) publishing is live-verified end-to-end.** Image publishing is implemented but has
  **not** been independently live-verified -- treat a real image publish with the caution of
  untested code: dry-run first, then verify the result carefully.
- Never read, print, or surface `profiles/*/storage_state.json`.

## Known failures and recovery

- **Caption can silently drop on publish** -- Instagram's hashtag autocomplete can still be open
  when Share is clicked, swallowing the commit. Cap fix attempts at two clean tries; if still gone,
  tell the user to add it by hand.
- **Crop can default to 1:1** even on sources already vertical -- confirm the served resolution
  after publishing (see Instructions).
- If a publish fails, looks uncertain, or you suspect a duplicate, use `troubleshoot-publishing`
  rather than retrying blind.
