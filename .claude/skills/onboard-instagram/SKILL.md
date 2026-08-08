---
name: onboard-instagram
description: Set up Instagram publishing for Socials Studio from scratch (login through a verified video roundtrip test, including the known caption-drop bug). Use when the user wants to connect, set up, or onboard Instagram, or a publish fails because no session exists yet.
---

# Instagram onboarding

Confirmed working end-to-end on a real account (2026-08-08): login, video upload with crop and
share all working, independently verified live. One real, reproducible platform bug was found and
is documented below rather than "fixed," because two clean attempts at the standard fix both
failed the same way -- don't keep retrying it blindly.

## The login architecture (read this first)

Instagram challenges automated logins (SMS codes, "suspicious login" interstitials) the same way
Google does for YouTube, just with different UI. **Never attempt the login itself from inside
automation.** `auth/login_wizard.py` opens a completely plain, human-launched Chrome process (no
CDP, no automation flags) for the login step. You log in yourself and close that window; only then
does Playwright touch the profile, to verify the session and later replay it for publishing.

## One-time login

```bash
python -m auth.login_wizard --platform instagram
```

Opens the plain Chrome window to Instagram's login page. Log in yourself (2FA included, dismiss
cookie/consent banners), then **close the Chrome window completely**. The script waits for the
window to close, then verifies the session.

## Verify before a real publish

```bash
python -m auth.publish_instagram video.mp4 --caption "test" --dry-run
```

Check for `"session_found": true`. No browser launched, nothing uploaded.

## Real publish

```bash
python -m auth.publish_instagram video.mp4 --caption "post caption"
```

## Required patterns for the upload flow

These are already implemented in `auth/publish_instagram.py` -- don't remove or weaken them. Each
exists because the simpler version failed live.

### Click "Post" from the New-post flyout via direct JS text match, not `get_by_role`

```python
clicked = page.evaluate("""() => {
    const els = [...document.querySelectorAll('a,button,[role=link],[role=button],div[tabindex]')]
        .filter(el => (el.innerText || '').trim() === 'Post');
    if (els.length) { els[0].click(); return true; }
    return false;
}""")
```

Confirmed live: `page.get_by_role("link", name="Post")` found **zero** matches even though the
element is a real `<a role="link">Post</a>` in the DOM (verified independently via
`querySelector`) -- some quirk in how Playwright computes the accessible name for this specific
element. A plain JS click by exact innerText works every time; this is also the private repo's
own long-standing convention for Instagram's dialog controls, not something invented for this fix.

### Use direct JS `.click()` for the crop-selector control, not Playwright's `.click()`

```python
page.evaluate("""() => {
    const svg = document.querySelector('svg[aria-label="Select Crop"]');
    const clickable = svg && svg.closest('div[role="button"],button,a');
    if (clickable) clickable.click();
}""")
```

Confirmed live: a plain `.click()` here times out with "element is visible, enabled and stable"
yet still failing, because a dialog overlay intercepts the pointer event even though Playwright's
own actionability check says the element should be clickable. Same fix pattern as the flyout click
above.

### Find your own profile dynamically before reading back the post URL -- never assume the home feed's first post is yours

```python
profile_href = page.evaluate("""() => {
    const nav = [...document.querySelectorAll('a')].find(a =>
        a.querySelector('img[alt*="profile picture"]'));
    return nav ? nav.getAttribute('href') : null;
}""")
# then navigate to https://www.instagram.com + profile_href and read posts from THAT page
```

Confirmed live: grabbing the first `/p/` or `/reel/` link off the home feed returned a **different
account's post entirely** (the home feed is algorithmic, not your own timeline). Always resolve
your own profile URL first, then read posts from that specific page.

## Known bug: the caption can silently drop on publish

Confirmed live, twice, with two independent clean attempts at the standard fix (reopen via "More
Options" -> Edit, retype the caption with real keystrokes, confirm the on-screen character
counter shows the right count, click Done, then reload the post fresh) -- both attempts showed the
caption correctly in the editor and in the counter immediately before confirming, and both still
showed **no caption at all** on a completely fresh page reload afterward. This matches the private
repo's own long-documented history of this exact bug (see `.claude/skills/instagram.md`,
`post-troubleshooting.md` Symptom E) -- it is a genuine, known-flaky platform behavior, not a
scripting mistake in this codebase.

**Do not keep retrying the fix.** Cap at two clean attempts, same as the private repo's own rule.
If it's still gone after that, tell the user directly that the caption needs to be added by hand,
rather than continuing to grind on an automated fix. The video/media itself publishes reliably;
it's specifically the caption-after-publish path that's flaky.

## Independent verification

Navigate to your own profile (resolved dynamically, see above), find the post's URL, then
**reload it fresh in a completely new page load** (not just reading the DOM state right after
publish -- that can show stale/pre-drop content) before checking for the caption or any other
detail. This distinction is exactly what separates a real verification from the false-positive
that caused the caption bug to go unnoticed initially.

## Cleaning up a test post

Open the post's "More Options" menu (svg with an aria-label matching `/more options/i`), click
Delete, confirm in the dialog. Verify by checking the profile grid afterward for the post's
specific ID -- don't trust the delete action's own return value.

## Known quirks

- **A reel's cover frame defaults to frame 0**, which is black if the source video fades in from
  black -- not encountered as a live bug in this session's specific test video, but documented
  extensively in the private repo's history (`.claude/skills/instagram.md`) as the single most
  recurring Instagram quality issue there. If a published video's thumbnail looks black on the
  profile grid, that's almost certainly this, not a publish failure -- see that file for the
  trim-before-upload fix.
- **Chrome will show "Didn't shut down correctly, restore pages?" on the next launch of this
  profile, every time** -- known, harmless upstream Playwright/Chrome interaction, not data loss.
- If a publish result looks suspicious, don't try to "keep the browser open" with a standalone
  script blocking on `input()` or a heartbeat loop -- a browser launched by
  `launch_persistent_context` is a child of that script's process and dies the instant the process
  ends, whether or not `.close()` ran; a backgrounded script also has no TTY, so `input()` raises
  `EOFError` immediately and takes the browser with it. Debug instead with a tool whose browser
  outlives any single action (an MCP-driven browser, not a one-shot script), and verify state by
  querying the page/DOM -- never by counting OS processes, which stay elevated (renderer, GPU,
  network, per-tab utility processes) even mid-teardown and prove nothing about whether the window
  you care about is still open.
