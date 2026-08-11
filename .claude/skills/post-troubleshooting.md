# Skill: diagnose a failed post

When a post won't go out, **do not guess and do not keep retrying the same action.** Work the
checklist. Each publisher runs a **visible** Chrome window (`headless=False`), so you have two
sources of truth: the script's error message, and what is actually on screen.

## The loop

1. **Read the script's output first.** The publishers raise specific errors — "Could not click Post",
   "Still on the compose page after clicking Post" — that name the failure. Don't skip past them.
2. **Look at the browser window** before touching anything: a counter, a dialog, a spinner, a
   progress bar. The pixels, not an assumption.
3. **Match a cause below and apply its fix.** Re-check.
4. **If nothing matches, you have found something new.** Note what is on screen, add the symptom,
   tell and fix to this file, and then retry. This file is meant to grow.
5. **Cap at ~2 clean attempts.** After that, hand the copy to the user to post by hand rather than
   burn the session. Never grind a wedged state.
6. **Before any retry, check whether the post actually went out.** A duplicate is worse than a delay.

---

## Symptom A — a native "Open" file dialog appears, then everything dies

**This is the one that looks most mysterious and has the simplest cause.**

| Tell | Cause | Fix |
|---|---|---|
| A Windows/macOS file-picker window opens. The run then hangs and exits with "could not post". | Something **clicked** a file input or an "Add media" button. That opens the real OS dialog, which lives outside the browser, blocks every subsequent automation call, and takes the process down with it. | **Never click to open a picker.** Set the file directly: `page.locator('input[type="file"]').first.set_input_files(path)`. No click before it, and none needed. All the publishers already do this — if you see a dialog, something deviated. |

If a dialog is already open, nothing else will work until a human closes it.

## Symptom B — the browser closes on its own, mid-run

| Tell | Cause | Fix |
|---|---|---|
| The window vanishes the moment the script finishes, even without `.close()`. | A browser launched by a script is owned by that process. When the process ends, the browser goes with it. There is no way around this from inside the script. | Expected behaviour, not a bug. Do the work **inside** the script's lifetime. Don't try to hold it open with `input()` — a backgrounded process has no stdin, so `input()` raises `EOFError` immediately and kills the browser faster. |
| "It's still open" — but it isn't. | Counting `chrome.exe` processes proves nothing; Chrome spawns a renderer, GPU and utility process each, and they linger during teardown. | Verify by querying the page, never by counting processes. |

## Symptom C — Post/Publish button disabled, text is present

| # | Cause | Tell | Fix |
|---|---|---|---|
| C1 | **Over the character limit** (most common) | Counter shows a negative number; overflow highlighted red | Trim. Bluesky counts literally to 300 graphemes; LinkedIn to 3,000 |
| C2 | **Media still processing** | Progress bar not complete, spinner on the thumbnail | Wait. A disabled button during upload means *processing*, not error — a 67s video can take ~45s |
| C3 | **A modal is on top** | A dialog covers the composer | Handle it with a **real** click. A scripted `.click()` frequently fails to fire the site's handler |
| C4 | **Editor state didn't register** | Counter reads 0 despite visible text | Clear and retype with real keystrokes, not `fill()` |

An "Upgrade to Premium" nag is **not** a blocker — it is an upsell. The blocker is almost always C1.

## Symptom D — clicked Post, page moved on, nothing posted

| # | Cause | Tell | Fix |
|---|---|---|---|
| D2 | **Pressing Escape opened a "Save/Discard" sheet** stacked on another dialog | Two confirmation sheets present | Never press Escape to dismiss a typeahead. Target buttons by accessible name |
| D3 | **Content silently filtered** | Nothing on the profile after several checks; a text-only version works | Try without the link, or move the link to a reply |

(D1 was X-specific and moved to `.claude/dormant/x-troubleshooting-symptoms.md` -- X is not a
supported platform in this release. Numbering kept as D2/D3 rather than renumbered, since nothing
else in this repo references D1 by number and renumbering existing IDs risks a future reader
misreading a stale external note.)

## Symptom E — Instagram reel published but the caption is empty

Two distinct causes. **E2 is far more common**, and used to be misfiled as E1.

| # | Cause | Tell | Fix |
|---|---|---|---|
| **E2** | **The caption ends in a hashtag, so the hashtag typeahead was still open when Share was clicked, and the commit was silently swallowed** | Composer showed the full caption and the right count; the live post has none. **The session was quiet** — nothing else running. That rules out E1 | **Dismiss the typeahead first**: click a neutral area of the dialog, confirm the counter still shows the full caption, then Share with a **real** click. A scripted `.click()` does not persist here |
| E1 | Two browser sessions fighting over the same profile | Only possible when something else is genuinely running at the same time | Wait until nothing else is running, then one clean attempt |

Since every caption ends in hashtags, the typeahead is open at Share on essentially every publish —
so dismiss it every time, whether or not the caption has dropped before.

**Verify at `/p/<code>/`, never `/reel/<code>/`** — the reel URL redirects into the feed player,
which renders other accounts' captions and gives a confident false result.

## Symptom F — Instagram reel is square, or cropped

Instagram defaults the crop to **1:1**, even when the source is already 1080×1920. Six consecutive
posts hit this.

**Measuring the `<video>` element will not detect it** — it can read a clean 9:16 while the real
crop viewport, up to five ancestors above it, is square. The depth varies between uploads. Walk the
whole ancestor chain and measure the outermost crop container.

Fix: "Select Crop" → 9:16 or Original. Confirm afterwards that the **served** video is 720×1280;
720×720 means it was cropped.

## Symptom G — Instagram reel tile is a black square

Frame 0 became the cover and it was mid-fade-in. Measure `YAVG` on frame 0: ~7 is black, ~12+ is
content. Trim the fade before uploading. **Never try to fix the cover via "Select from computer"** —
it fails silently.

## Symptom H — LinkedIn navigation hangs after posting a video

Not a failed post. With an upload still in flight, navigating away fires a `beforeunload` dialog and
the navigation hangs. Stay on the page, let the upload finish, confirm the composer closed, then
verify. Early navigation is what breaks it.

## Symptom I — "No saved session" / a login page appears

The session for that platform expired, or was never established.

**Never attempt to log in from inside automation.** It triggers Google's "This browser or app may
not be secure" and Instagram/LinkedIn suspicious-login challenges — those fire on automation
signals, not on how you log in.

Fix: `python -m auth.login_wizard --platform <name>`, which opens a plain human-driven Chrome for
you to sign in, then verifies the session read-only.

## Symptom J — "profile is already in use" / the browser won't start

Only one process can use a profile directory at a time. Another publisher run, or a stale one, still
holds it.

This reads as "logged out" or "auth broken" and is **neither** — it is a stale process. Close the
other run. Don't kill processes blind while a publish may be in flight.

---

## Before reporting success

- Reload the post fresh and confirm the text rendered — do not trust the composer.
- On Bluesky, verify through the public API rather than the DOM:
  `https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed?actor=<handle>&limit=3`
- On LinkedIn, match on text unique to that post; the top feed item is not reliably your newest.
- Confirm media is attached and plays.
