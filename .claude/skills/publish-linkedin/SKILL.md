---
name: publish-linkedin
description: Prepare, adapt, validate, review and publish text/image/video posts to an already-connected LinkedIn account. Use when the user wants to draft, review or publish a LinkedIn post -- not for first-time login (see onboard-linkedin) and not for diagnosing a failed/uncertain publish (see troubleshoot-publishing).
---

# Publish to LinkedIn

## When to use it

Drafting, reviewing, or publishing a LinkedIn post for an already-connected account. Not for
first-time login (`onboard-linkedin`) or diagnosing a failed/uncertain publish
(`troubleshoot-publishing`).

## Instructions

```bash
python -m auth.publish_linkedin "post text"                                     # validates only (default)
python -m auth.publish_linkedin "post text" --confirm-publish                   # real publish
python -m auth.publish_linkedin "post text" --image path/to/photo.jpg --confirm-publish
python -m auth.publish_linkedin "post text" --video path/to/clip.mp4 --confirm-publish
```

Requires a saved session (`python -m auth.login_wizard --platform linkedin`).

Copy rules:
- **3,000 characters**, counted literally.
- **LinkedIn renders markdown literally** -- `**bold**` shows as literal asterisks. Strip every
  `*` before posting; use line breaks and short paragraphs for emphasis instead.
- Register: fuller paragraphs and natural narrative rhythm, not chopped one-line-per-thought copy.
- A URL in the body auto-attaches a preview card, which takes the media slot -- if you want a
  video or image, the preview card has to go.

Verify after posting: reload the activity feed and match on text unique to the post -- the top
item is not reliably the newest.

## Guardrails

- `--confirm-publish` is required for a real publish; without it, this only validates.
- **This publishes immediately** -- there is no draft/review step once Post is clicked.
- **Media can never be added to a LinkedIn post after publishing** -- text and media must go in
  the same call.
- Never read, print, or surface `profiles/*/storage_state.json`.

## Known failures and recovery

- **Post button disabled** -- media still processing; wait, it's not an error.
- **Navigation hangs after posting a video** -- an upload still in flight fires a `beforeunload`
  dialog. Stay on the page, let it finish, confirm the composer closed, then verify.
- Don't trust a script's own `"status": "posted"` result on its own -- verify via the activity feed.
- If a publish fails, looks uncertain, or you suspect a duplicate, use `troubleshoot-publishing`
  rather than retrying blind.
