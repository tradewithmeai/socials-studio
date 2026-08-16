---
name: publish-youtube
description: Prepare, validate, review and publish a video to an already-authorized YouTube channel. Use when the user wants to draft, review or upload a YouTube video -- not for first-time OAuth setup (see onboard-youtube) and not for diagnosing a failed/uncertain publish (see troubleshoot-publishing).
---

# Publish to YouTube

## When to use it

Drafting, reviewing, or uploading a YouTube video to an already-authorized channel. Not for
first-time OAuth setup (`onboard-youtube`) or diagnosing a failed/uncertain publish
(`troubleshoot-publishing`).

## Instructions

```bash
python -m auth.publish_youtube path/to/video.mp4 --title "..."                  # validates only (default)

python -m auth.publish_youtube path/to/video.mp4 \
    --title "..." --description "..." --tags "a,b,c" --visibility private \
    --not-made-for-kids --acknowledge-upload-terms --confirm-publish
```

Requires `python -m auth.setup_youtube_oauth` to have already been run.

Title/description rules:
- **100-character title limit is a hard API limit** -- an over-length title is rejected outright.
  Count before presenting a title for approval.
- No `<` or `>` characters anywhere in title or description.
- Lead with the single most surprising, specific fact in the first ~55 characters.

Verify after upload: read the video back with `videos.list` and confirm title, description, tags,
category and privacy actually stuck -- don't trust the insert response alone (tags intermittently
fail to persist; re-apply with `videos.update` if missing).

## Guardrails

- A real upload requires `--confirm-publish`, exactly one of `--made-for-kids` /
  `--not-made-for-kids`, and `--acknowledge-upload-terms`.
- The upload notice prints unconditionally on every real-upload attempt -- show it to the user and
  get their real answer on Made for Kids; don't just add flags to satisfy the CLI.
- `--visibility` defaults to `private`. Only pass `--visibility public` once the user has explicitly
  confirmed they want it live.

## Known failures and recovery

- **Upload fails with `401 youtubeSignupRequired`**: authorized as the wrong Google account.
  Verify with `youtube.channels().list(part="id,snippet", mine=True).execute()` before relying on
  the token -- exactly 1 item, your channel, is correct.
- Category is hardcoded to `22` (People & Blogs), with no override.
- No thumbnail support -- needs a separate `thumbnails().set()` call after upload.
- If a publish fails, looks uncertain, or you suspect a duplicate, use `troubleshoot-publishing`
  rather than retrying blind.
