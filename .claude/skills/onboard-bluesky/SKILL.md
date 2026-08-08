---
name: onboard-bluesky
description: Set up Bluesky publishing for Socials Studio from scratch (login through a verified text + video roundtrip test). Use when the user wants to connect, set up, or onboard Bluesky, or a Bluesky publish fails because no session exists yet.
---

# Bluesky onboarding

Confirmed working end-to-end on a real account (2026-08-08): login, text post, and video post, all
independently verified via Bluesky's public API and then cleaned up. This skill is the
known-working method -- follow it, don't improvise a different one.

## The known-working method

Bluesky does NOT need OAuth or an API key -- it goes through the same plain-Chrome-login-then-
Playwright-replay pattern as X and Instagram (see `platform-login` skill / `auth/login_wizard.py`
module docstring for why: never attempt the login itself from inside automation).

### One-time login

```bash
python -m auth.login_wizard --platform bluesky
```

Opens a plain, non-automated Chrome window to bsky.app. Log in yourself, then **close that Chrome
window completely** -- the script waits for the window to close, then verifies the session.

⚠️ Bluesky is a single-page app with no separate `/login` URL that disappears on success, so its
`login_url_marker` in `auth/platforms.py` is a placeholder that never matches. Verification relies
entirely on `logged_in_selector` (`[aria-label="Compose new post"]`) -- if that selector ever goes
stale, verification will falsely report "not logged in" even on a real success. Check the button
still exists on bsky.app before assuming the wizard itself is broken.

### Verify before a real publish

```bash
python -m auth.publish_bluesky "test text" --dry-run
```

Check for `"session_found": true`. No browser launched, nothing posted.

### Real publish

```bash
python -m auth.publish_bluesky "post text"
python -m auth.publish_bluesky "post text" --video path/to/video.mp4
```

No visibility/draft concept on Bluesky -- a successful publish is immediately live.

## Do NOT do this

- **Do not attach media by clicking the button and calling `set_input_files()` on a generic
  `input[type=file]` locator.** Confirmed live (2026-08-08): a plain click on
  `[aria-label="Add media to post"]` can fall through to a REAL native OS file-picker dialog
  outside Playwright's control (it opened Windows Explorer to an unrelated folder). The script
  then has no way to interact with that dialog, and closing the Playwright context afterward
  leaves the orphaned OS dialog and Chrome process behind. **Always wrap the click in
  `page.expect_file_chooser()`** so Playwright intercepts the chooser before it can become a real
  OS dialog -- this is what `auth/publish_bluesky.py` does now; don't remove it.
- **Do not wait only for "Processing video" to clear before publishing.** Confirmed live: the
  actual UI shows **"Uploading video..."** during upload, THEN briefly "Processing video...". A
  wait-loop checking only for "Processing" exits immediately during the upload phase (that text
  never appears yet), so the code moves on and either ships a text-only post with the video
  silently dropped, or clicks Post before the attachment finished and the post never goes out at
  all (both were observed live). Wait for **both** "Uploading video" and "Processing video" to be
  absent before checking the Publish button.
- **Do not trust a `{"status": "posted"}` return value as proof anything actually happened.**
  Confirmed live: a run reported success while the post never appeared on the account at all
  (traced back to a stale/locked profile from an earlier interrupted script, not a code bug --
  but the point stands). Always verify independently.
- **Never leave a Chrome process running after a script ends, especially after an interrupted
  or backgrounded run.** This is the single most common cause of Bluesky (and every other
  platform's) automation "mysteriously" failing on the next attempt -- see the hard rule in the
  root `CLAUDE.md`. If you background a Playwright script and then need to inspect or continue
  from where it left off, you generally CAN'T attach a second script to the same open profile
  (the profile lock prevents it) -- kill the first one cleanly, then start a fresh script that
  redoes the needed steps from scratch, screenshotting instead of narrating live.

## Independent verification (no auth needed)

Bluesky reads are unauthenticated via the public AT Protocol API -- use this instead of trusting
the script's own report, and instead of trusting the composer UI mid-flow:

```bash
curl -s "https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed?actor=<handle>&limit=3"
```

For a video post specifically, check the record has a genuine video embed, not just that a post
exists:

```python
import json
# parse the curl output, then:
print(post["record"].get("embed", {}).get("$type"))  # expect "app.bsky.embed.video"
```

## Cleaning up a test post

Not a built CLI feature. To delete during verification, from the profile page
(`https://bsky.app/profile/<handle>`), open the post's menu and click Delete -- the private repo's
proven selector pattern (menu button, then a menuitem/button whose innerText matches `/delete/i`)
works via direct JS click, same reasoning as the composer buttons: Playwright's role-based
locators are not reliably needed here, plain innerText matching is simpler and has worked
consistently. Verify deletion via the public API read above, not just a "confirmed" click result.

## Character limit

300 graphemes (emoji count as 1, unlike X's weighted-2; URLs count their full literal length, not
a fixed cost). Compose to fit before typing -- see the character-limit notes carried over in
`.claude/skills/bluesky.md` if you need the exact counting logic.
