---
name: publish-bluesky
description: Prepare, adapt, validate, review and publish text/image/video posts to an already-connected Bluesky account. Use when the user wants to draft, review or publish a Bluesky post -- not for first-time login (see onboard-bluesky) and not for diagnosing a failed/uncertain publish (see troubleshoot-publishing).
---

# Publish to Bluesky

## When to use it

Drafting, reviewing, or publishing a Bluesky post for an already-connected account. Not for
first-time login (`onboard-bluesky`) or diagnosing a failed/uncertain publish
(`troubleshoot-publishing`).

## Instructions

```bash
python -m auth.publish_bluesky "post text"                                      # validates only (default)
python -m auth.publish_bluesky "post text" --confirm-publish                    # real publish
python -m auth.publish_bluesky "post text" --image path/to/photo.jpg --confirm-publish
python -m auth.publish_bluesky "post text" --video path/to/clip.mp4 --confirm-publish
```

Requires a saved session (`python -m auth.login_wizard --platform bluesky`).

Copy rules:
- **300 characters, counted literally** -- no URL shortening or weighting.
- **One link per post** -- a second URL takes the link card away from the first.
- A link card attaches automatically when the text contains a URL.
- **Video and a link card are mutually exclusive.** With a video attached, the link stays as plain
  linked text -- expected, not a failure.
- Register: dry, understated, slightly wry; light on hashtags.

Verify after posting via Bluesky's public API, not the browser:
```bash
curl -s "https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed?actor=<handle>&limit=3"
```
Check the post text, link facet, and embed type (`app.bsky.embed.video` or
`app.bsky.embed.external`).

## Guardrails

- `--confirm-publish` is required for a real publish; without it, every call above only validates.
- Never click an "Add media" button yourself -- the script attaches files directly.
- Never read, print, or surface `profiles/*/storage_state.json`.

## Known failures and recovery

If a publish fails, looks uncertain, or you suspect a duplicate, use `troubleshoot-publishing`
rather than retrying blind.
