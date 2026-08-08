---
name: onboard-linkedin
description: Set up LinkedIn publishing for Socials Studio from scratch (login through a verified text + video roundtrip test). Use when the user wants to connect, set up, or onboard LinkedIn, or a LinkedIn publish fails because no session exists yet.
---

# LinkedIn onboarding

Confirmed working end-to-end on a real account (2026-08-08): login, text post (independently
verified live), and video post (independently verified live, with a human watching the actual
browser window throughout). Getting the video path right took several real failures first --
read the "Do NOT do this" section before touching the video code, it will save you the same
debugging cycle.

## The known-working method

Same plain-Chrome-login-then-Playwright-replay pattern as X, Instagram, and Bluesky (see the
`platform-login` skill / `auth/login_wizard.py` module docstring for why: never attempt the
login itself from inside automation).

### One-time login

```bash
python -m auth.login_wizard --platform linkedin
```

Opens a plain, non-automated Chrome window to LinkedIn's login page. Log in yourself (2FA
included, dismiss cookie banners), then **close that Chrome window completely** -- the script
waits for the window to close, then verifies the session.

### Verify before a real publish

```bash
python -m auth.publish_linkedin "test text" --dry-run
```

Check for `"session_found": true`. No browser launched, nothing posted.

### Real publish

```bash
python -m auth.publish_linkedin "post text"
python -m auth.publish_linkedin "post text" --video path/to/video.mp4
```

⚠️ **This publishes immediately** -- there is no draft/review step once Post is clicked.
Per the account's own posting policy (carried over from the private repo, see
`.claude/skills/linkedin.md`): LinkedIn is milestones-only, not part of a daily rotation. Confirm
with the user this is actually a milestone/announcement before posting for real, not just before
running a mechanism test.

## Required patterns for the video path

These three are already implemented in `auth/publish_linkedin.py` -- don't remove or weaken any
of them. Each exists because skipping it produced a live-confirmed silent failure: the script
returned `{"status": "posted"}` while the post never actually went out, or a real native OS
dialog opened outside any script's control. Follow the pattern shown, not a simplified version.

### Always wrap the "Add media" click in `page.expect_file_chooser()`

```python
with page.expect_file_chooser(timeout=10_000) as fc_info:
    add_media.first.click()
fc_info.value.set_files(str(video_file))
```

Without this, the click can fall through to a real native OS file-picker dialog (confirmed live:
it opened Windows Explorer to an unrelated folder), completely outside Playwright's control --
the whole flow then dies silently once the context closes with that orphaned dialog still open.

### Scope the media wizard's "Next" button search to `#interop-outlet`'s shadow root, matched by exact text

```python
next_clicked = page.evaluate("""() => {
    const outlet = document.querySelector('#interop-outlet');
    const root = outlet && outlet.shadowRoot;
    if (!root) return false;
    const btn = [...root.querySelectorAll('button')]
        .find(b => (b.innerText || '').trim() === 'Next');
    if (btn) { btn.click(); return true; }
    return false;
}""")
```

An unscoped `get_by_role("button", name="Next")` can match a document-viewer pagination control
elsewhere on the page instead (confirmed live), hanging for the full timeout on the wrong element.

### After clicking Post with a video attached, wait for LinkedIn's upload banner to clear before doing anything else

```python
for _ in range(60):  # up to 2 minutes
    uploading = page.get_by_text("Keep the page open to finish uploading", exact=False).count()
    if uploading == 0:
        break
    page.wait_for_timeout(2000)
else:
    raise RuntimeError("Video upload did not finish -- do not close the browser.")
```

The composer dialog closing does **not** mean the post is done. LinkedIn shows an inline
**"Uploading... Keep the page open to finish uploading X%"** banner on the main feed page, and
the upload continues in the background after the dialog closes -- confirmed live, a 19MB video
was still at ~15% several seconds after the dialog closed. Closing the browser (or otherwise
ending the script) before that banner clears means the upload, and the post, never completes.
Skip this wait for text-only posts -- there's nothing to wait for.

### If a publish looks suspicious, keep the browser open and look at it directly

Do not trust a script's own `{"status": "posted"}` return value on its own, and do not diagnose a
suspicious result by repeatedly running short open-close-check scripts -- none of the three bugs
above were found that way; all three produced that exact success message while nothing had
actually happened. Instead: run a script that performs the action and then blocks (a loop that
never lets the browser process die) so the browser stays open indefinitely, and look at the actual
window. Only close it once the real state is confirmed.

## Independent verification

LinkedIn has no public unauthenticated API like Bluesky's -- verification means navigating the
same authenticated session to the activity feed:

```
https://www.linkedin.com/in/<profile-slug>/recent-activity/all/
```

**The top item is not always the newest post** -- LinkedIn's feed ordering is not strictly
chronological. Search all loaded items by unique text instead of assuming position 1:

```python
found = page.evaluate("""() => {
    const els = [...document.querySelectorAll('[data-urn]')];
    for (const el of els) {
        if ((el.innerText || '').includes('<unique text from your post>')) {
            return { urn: el.getAttribute('data-urn'), hasVideo: el.querySelector('video') !== null };
        }
    }
    return null;
}""")
```

If not found in the initially-loaded items, scroll (`page.mouse.wheel(0, 5000)`) and wait before
concluding it doesn't exist -- new posts can take a few seconds to be indexed into this feed view,
and a scroll loads more historical items that may push what you're looking for further down than
expected. `data-urn` gives the real `urn:li:activity:<id>` for the post.

## Cleaning up a test post

From the activity feed, open the post's control menu (`aria-label` containing "control menu" or
"More"), click "Delete post", then confirm in the dialog that appears (plain `<button>Delete</button>`
with no aria-label -- match by exact innerText, there are multiple "Delete" buttons on screen at
different steps so don't use a role-based query that could hit the wrong one). Verify by
re-searching the activity feed afterward, same method as above -- don't trust the click alone.

## Known quirks

- **The `#interop-outlet` shadow-DOM overlay intercepts the "Start a post" click** even though the
  button itself lives in the light DOM. Disable `pointerEvents` on that element just long enough
  to click through it, then re-enable immediately -- the composer that opens lives inside that
  same element's shadow root, so leaving it disabled blocks every subsequent click:
  ```python
  page.evaluate("() => { document.querySelector('#interop-outlet').style.pointerEvents = 'none'; }")
  page.get_by_role("button", name="Start a post").first.click()
  page.evaluate("() => { document.querySelector('#interop-outlet').style.pointerEvents = ''; }")
  ```
- **A URL in the post text auto-attaches a link-preview card that takes the media slot** -- if you
  need both a link and a video, attach the video first, before typing any URL that would trigger
  the card.
- **Chrome will show "Didn't shut down correctly, restore pages?" on the next launch of this
  profile, every time** -- this is a known, harmless upstream Playwright/Chrome interaction
  (`launch_persistent_context` doesn't give Chrome the chance to write a clean-exit flag before
  the process ends, even on a normal `context.close()`), not a sign of data loss or a bug in this
  code. Verified repeatedly: cookies and session state persist correctly across it regardless.
