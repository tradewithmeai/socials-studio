---
name: publish-x
description: Prepare, adapt, validate, review and publish text/image/video posts to an already-connected X (Twitter) account. Use when the user wants to draft, review or publish a post to X -- not for first-time login (see onboard-x) and not for diagnosing a failed/uncertain publish (see troubleshoot-publishing).
---

# Publish to X

## When to use it

Drafting, reviewing, or publishing a post to X for an already-connected account. Not for
first-time login (`onboard-x`) or diagnosing a failed/uncertain publish
(`troubleshoot-publishing`).

## Instructions

```bash
python -m auth.publish_x "post text"                                            # validates only (default)
python -m auth.publish_x "post text" --dry-run                                  # validates only (explicit)
python -m auth.publish_x "post text" --confirm-publish                          # real publish
python -m auth.publish_x "post text" --image path/to/photo.jpg --alt-text "..." --confirm-publish
python -m auth.publish_x "post text" --video path/to/clip.mp4 --confirm-publish
```

Requires a saved session (`python -m auth.login_wizard --platform x`).

Copy rules:
- **280 characters, weighted, not a plain count.** Any URL costs a flat **23** regardless of real
  length; most characters cost 1, but anything outside four narrow ranges costs 2 (an em dash `—`
  is 1, an arrow `→` is 2, every emoji is 2); newlines cost 1. Count it properly before posting.
- **Never open a post with `@handle`** -- X classifies it as a reply, reaching only people who
  follow both accounts. Reorder the sentence instead.
- **One link per post** -- a second URL hijacks the unfurl card.
- Since a URL always costs 23 regardless of length, replying to your own post with the link (rather
  than including it in the main post body) is often the better pattern when space is tight.

Verify after posting: the script does not return the post's URL. Find the profile handle
dynamically, navigate to it, and search loaded posts for text unique to what you just posted.

## Guardrails

- `--confirm-publish` is required for a real publish; without it, every call above only validates.
- Never click a file input or an "Add media" button yourself -- the script sets files directly.
- Always fill in real alt text for an image that carries meaning the post text doesn't (the script
  defaults to the post text if `--alt-text` is omitted).
- Never read, print, or surface `profiles/*/storage_state.json`.
- Uses a saved browser session via Playwright, not the X API -- publishes only after
  `--confirm-publish`, same as every other platform here.

## Known failures and recovery

- **Post button never enables** -- usually over the (weighted) character limit, or a video is
  still processing.
- **Still on the compose page after clicking Post** -- the submit didn't go through. Check for the
  alt-text accessibility dialog blocking submission, or a beforeunload/other dialog. Don't blindly
  retry -- check the profile first to avoid a duplicate.
- **A native OS file dialog appears** -- something clicked a file input instead of setting it
  directly; that's a regression, not expected behavior.
- If a publish fails, looks uncertain, or you suspect a duplicate, use `troubleshoot-publishing`
  rather than retrying blind.
