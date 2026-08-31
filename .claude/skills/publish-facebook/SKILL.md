---
name: publish-facebook
description: Prepare, validate, review and publish text/image/video posts to an already-connected Facebook account -- experimental, unverified against a live account. Use when the user wants to draft, review or publish a Facebook post -- not for first-time login (see onboard-facebook) and not for diagnosing a failed/uncertain publish (see troubleshoot-publishing).
---

# Publish to Facebook (experimental extra)

**Unverified against a live account.** Every selector in `auth/publish_facebook.py` is a
first-draft guess. Treat the first real publish attempt as a live test of the code itself, not a
routine post -- see `onboard-facebook` for the recommended text-only-first roundtrip. Don't tell
the user this "should just work" the way the other platforms now do.

## When to use it

Drafting, reviewing, or publishing a Facebook post for an already-connected account. Not for
first-time login (`onboard-facebook`) or diagnosing a failed/uncertain publish
(`troubleshoot-publishing`).

## Instructions

```bash
python -m auth.publish_facebook "post text"                                     # validates only (default)
python -m auth.publish_facebook "post text" --confirm-publish                   # real publish
python -m auth.publish_facebook "post text" --image path/to/photo.jpg --confirm-publish
python -m auth.publish_facebook "post text" --video path/to/clip.mp4 --confirm-publish
```

Requires a saved session (`python -m auth.login_wizard --platform facebook`). `--video` and
`--image` are mutually exclusive -- pass at most one.

Copy rules: none specific to Facebook are confirmed yet -- this hasn't been exercised live enough
to know its real character limits or rendering quirks. Keep posts short and simple until a live
run says otherwise.

Verify after posting: reload the profile timeline and match on text unique to the post. The
result dict's own `"verified"` field already tries this automatically (it revisits the profile and
searches the rendered page text), but its `"verify_note"` says plainly when it couldn't confirm --
treat that as "check by hand," not as a failure on its own.

## Guardrails

- `--confirm-publish` is required for a real publish; without it, this only validates.
- Never read, print, or surface `profiles/*/storage_state.json`.
- If a real publish raises, `auth/publish_facebook.py` saves a screenshot to
  `profiles/facebook/last_failure_screenshot.png` right before raising -- use it, don't guess.

## Known failures and recovery

- **Composer opener not found**, **Post button never found**, or **Post button stays disabled** --
  see `onboard-facebook`'s "Known failures and recovery" section; these are the same unverified
  selectors either way.
- **Composer dialog never closes after clicking Post** -- treat the post as possibly not sent; do
  not retry blind. Reload the profile timeline and check for it first (see
  `troubleshoot-publishing`'s general duplicate-avoidance guidance).
- If a publish fails, looks uncertain, or you suspect a duplicate, use `troubleshoot-publishing`
  rather than retrying blind.
