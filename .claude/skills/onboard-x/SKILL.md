---
name: onboard-x
description: Set up X (Twitter) publishing for Socials Studio from scratch (login through a verified post + reply-with-link roundtrip test). Use when the user wants to connect, set up, or onboard X/Twitter, or a publish fails because no session exists yet.
---

# X (Twitter) onboarding

Confirmed working end-to-end on a real account (2026-08-08 for the rebuilt login path; the post
mechanics themselves were separately verified live earlier in the same project). This is the
platform where the core login-architecture bug was first found and fixed -- read "The login
architecture" section even if X itself seems to be working, because the same fix underpins every
other platform's login in this repo.

## The login architecture (read this first)

X's own sign-in flow can include "Sign in with Google" as an option, and Google actively detects
and blocks sign-in attempts from automation-controlled browsers with **"This browser or app may
not be secure."** This is confirmed live, and it is NOT specific to Google-flavored sign-in --
the block triggers on the automation signals themselves (`navigator.webdriver`, the CDP control
port, automation launch switches), not on which login method is used. Other platforms challenge
automated logins too, just with different UI (SMS codes, "suspicious login" interstitials).

**The fix: never attempt the login itself from inside automation.** `auth/login_wizard.py` opens
a completely plain, human-launched Chrome process (no CDP, no automation flags -- indistinguishable
from double-clicking the Chrome icon) for the login step. You log in yourself and close that
window; only then does Playwright touch the profile, to verify the session and later replay it for
publishing. A session a human already established is not subject to these defenses -- the
automated browser is just reusing normal cookies at that point.

## One-time login

```bash
python -m auth.login_wizard --platform x
```

Opens the plain Chrome window to X's login page. Log in yourself (2FA included, dismiss cookie
banners), then **close the Chrome window completely**. The script waits for the window to close,
then verifies the session by checking for the home-timeline nav link -- not by revisiting the
login page.

## Verify before a real publish

```bash
python -m auth.publish_x "test text" --dry-run
```

Check for `"session_found": true`. No browser launched, nothing posted.

## Real publish

```bash
python -m auth.publish_x "post text"
python -m auth.publish_x "post text" --video path/to/video.mp4
```

No draft/review step -- a successful call posts immediately and publicly (X has no
private/unlisted post state).

## How the publish flow finds its own post ID

X does not return a post ID or URL directly from the compose action. `auth/publish_x.py` navigates
to the account's own profile afterward and reads the newest matching post from there -- **find the
profile handle dynamically rather than hardcoding it**:

```python
href = page.evaluate("""() => {
    const link = document.querySelector('a[data-testid="AppTabBar_Profile_Link"]');
    return link ? link.getAttribute('href') : null;
}""")
```

Then navigate to `https://x.com` + that href and search the loaded articles for text unique to
the post you just made.

## Independent verification

X has no public unauthenticated read API usable here. Verify using the same saved session, in a
**separate** script/process from whatever posted -- don't reuse a page reference from a context
that already closed:

```python
page.goto(f"https://x.com{profile_href}", timeout=30000)
found = page.get_by_text("<unique text from your post>").count()
```

For a reply-with-link (the pattern used for including a URL, since X's own character-cost
weighting makes putting links in the body expensive -- see character-limit notes below), find the
original post's article, click its reply action, then verify the reply the same way: search the
profile page (or the post's own page) for the reply text after posting.

## Cleaning up a test post

From the profile page, locate the article containing the post text, open its caret/more-options
menu, select Delete, and confirm in the dialog. Match buttons by exact innerText rather than role
where multiple similar controls exist on screen (the same pattern used across every platform in
this repo). Verify deletion by re-searching the profile afterward, same method as above -- don't
trust the delete action's own return value.

## Character limit

X counts are weighted, not a plain character count: most characters are 1, **each URL costs a
flat 23 characters** regardless of its real length, and emoji cost 2. Compose to fit the limit
before typing, accounting for the URL cost up front if a link will be in the same post -- this is
why replying with the link separately (rather than including it in the main post body) is often
the better pattern here.

## Known quirks

- **Chrome will show "Didn't shut down correctly, restore pages?" on the next launch of this
  profile, every time** -- this is a known, harmless upstream Playwright/Chrome interaction
  (`launch_persistent_context` doesn't give Chrome the chance to write a clean-exit flag before
  the process ends, even on a normal `context.close()`), not a sign of data loss or a bug in this
  code. Verified repeatedly: cookies and session state persist correctly across it regardless.
- If a publish result looks suspicious, don't try to "keep the browser open" with a standalone
  script blocking on `input()` or a heartbeat loop -- a browser launched by
  `launch_persistent_context` is a child of that script's process and dies the instant the process
  ends, whether or not `.close()` ran; a backgrounded script also has no TTY, so `input()` raises
  `EOFError` immediately and takes the browser with it. Debug instead with a tool whose browser
  outlives any single action (an MCP-driven browser, not a one-shot script), and verify state by
  querying the page/DOM -- never by counting OS processes, which stay elevated (renderer, GPU,
  network, per-tab utility processes) even mid-teardown and prove nothing about whether the window
  you care about is still open. This exact failure mode (a script reporting success while nothing
  had actually happened) was confirmed live on other platforms in this repo; don't assume X is
  immune just because its mechanics are simpler.
