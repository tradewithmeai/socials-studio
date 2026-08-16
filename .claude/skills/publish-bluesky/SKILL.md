---
name: publish-bluesky
description: Prepare, adapt, validate, review and publish text/image/video posts to an already-connected Bluesky account. Use when the user wants to draft, review or publish a Bluesky post -- not for first-time login (see onboard-bluesky) and not for diagnosing a failed/uncertain publish (see troubleshoot-publishing).
---

# Publish to Bluesky

Publishing runs through `auth/publish_bluesky.py`, which drives a saved browser session.
**You do not drive the browser yourself.** Call the script.

```bash
python -m auth.publish_bluesky "post text" --confirm-publish
python -m auth.publish_bluesky "post text" --image path/to/photo.jpg --confirm-publish
python -m auth.publish_bluesky "post text" --video path/to/clip.mp4 --confirm-publish
python -m auth.publish_bluesky "post text"    # validates only -- the default, no flags needed
```

Safe by default: every call above validates only unless `--confirm-publish` is present.

Requires a saved session: `python -m auth.login_wizard --platform bluesky`.

## What the script already handles

- **Attaching media** via `set_input_files()`. ⚠️ Never click an "Add media" button to open a
  picker — that opens the native OS file dialog, which blocks everything and kills the run.
- **Waiting for video processing** before posting.

## What YOU are responsible for — the copy

**300 characters, counted literally** — no URL shortening, no weighting. What you type is what
counts. (Bluesky *displays* a long URL trimmed, but the underlying link is stored in full and the
character count uses the real text.)

**One link per post.** A second URL takes the link card away from the first.

**Link cards attach automatically** when the post contains a URL — the script types the text with
real keystrokes, which is what triggers detection. You do not need to click "Add link card".

**A video and a link card are mutually exclusive.** Bluesky allows one embed. If you attach a video,
the link stays as plain linked text in the body — that is expected, not a failure.

**Register:** dry, understated, slightly wry. Light on hashtags — often none at all.

## Video limits

The widely-quoted **"~60s / 50 MB" ceiling is wrong**, or at least not enforced here. Verified twice
(2026-08-07 and 08-08): **67-second clips at 4.1 MB and 13.3 MB both uploaded and published without
complaint**. Do not pre-emptively trim a clip expecting a refusal. If the composer ever does refuse
one, record the real limit here rather than restoring a guess.

## Verify after posting — properly

Bluesky is the one platform with a **free, unauthenticated read API**, so verification here can be
genuinely independent of whatever the browser claims:

```bash
curl -s "https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed?actor=<handle>&limit=3"
```

Check the post text, the link facet, and the embed type (`app.bsky.embed.video` or
`app.bsky.embed.external`). Prefer this over trusting a screenshot — a browser session can report
success on a post that never landed.

## Selector note

`[aria-label="Compose new post"]` now matches **two** elements (the home-screen button and the nav
one), so a bare selector fails Playwright's strict mode. Scope it — `nav [aria-label="Compose new
post"]` — or take `.first`. This also affects the `logged_in_selector` in `auth/platforms.py`.

If a publish fails, looks uncertain, or you suspect a duplicate, use the `troubleshoot-publishing`
skill rather than retrying blind.
