# Post-Troubleshooting Skill — diagnose a failed post by screenshot + checklist

When a post won't go out, **do NOT guess or keep re-trying the same action.** Work a checklist of known
causes, each verified against a **screenshot**. If nothing on the list matches, you're missing
something — screenshot again, **diff it against the last screenshot and the list**, and add the new
cause. Every pass narrows the possible errors toward zero.

## The loop (follow in order, every time)

1. **SCREENSHOT FIRST.** `browser_take_screenshot` (or read the current one). Read what's actually on
   screen before touching anything. (If a modal blocks the screenshot — e.g. a `beforeunload` dialog —
   clear it first with `browser_handle_dialog`, then screenshot.)
2. **Walk the cause list for your symptom (below).** For each candidate, confirm/deny it *from the
   screenshot* (the char counter, a dialog, a spinner, a media state — the pixels, not an assumption).
3. **Apply the fix for the first cause that matches.** Re-check.
4. **If NO cause matched, you are missing something.** Screenshot again, **diff against the previous
   screenshot** (what changed? what's present that isn't on the list?). Add the new cause + its tell +
   its fix to the relevant list below (this file is meant to grow). Then retry the loop.
5. **Cap:** after ~2 clean fresh attempts (see [[feedback-fresh-retry]]), if still stuck, hand the copy
   to the user to post manually rather than burn the session.

---

## Symptom A — Post/Publish button is DISABLED (text is present)

| # | Cause | Tell in the screenshot | Fix |
|---|---|---|---|
| A1 | **Over the char limit** (most common) | Counter circle (bottom-right on X) shows a **negative** number; the overflow text is highlighted **red** | Trim. On X **every URL = 23** (two links = 46; a bare `solvx.uk` still costs 23), emoji = 2. Bluesky = 300, URLs count their FULL literal length. Clear + retype a shorter version |
| A2 | **Media still processing** | Upload bar not at "Uploaded (100%)"; spinner on the thumbnail | Wait for 100% + ~5s server processing, then check again |
| A3 | **Blocking modal on top** (accessibility / restore / save) | A dialog sits over the composer (see Symptom B tells) | Handle the dialog (real click on the right button; not a JS `.click()`) |
| A4 | **Editor state didn't register** (genuinely rare) | Counter reads **0** despite visible text | Clear (Ctrl+A, Delete) + retype with **real keystrokes** (`slowly:true`), not `fill()` |

> Note: an "Upgrade to Premium to write longer posts" nag is **NOT** a blocker — it's just the long-post
> upsell. The blocker is almost always A1 (the counter).

## Symptom B — clicked Post, page redirected, but nothing posted (it vanished)

| # | Cause | Tell | Fix |
|---|---|---|---|
| B1 | **Image alt-text reminder**, dismissed by a JS click that didn't fire X's handler | "Don't forget to make your image accessible" dialog was up | Use a **real** `browser_click` on `confirmationSheetCancel` ("Not this time") or add a description. Image tweets often need the human to finish (see twitter.md) |
| B2 | **Escape opened a "Save post?/Discard" sheet** that stacked on the reminder | Two `confirmationSheetCancel` on the page ("Discard" + "Not this time") | Target the button by **accessible name**, don't blind-click; never press Escape to dismiss the @-typeahead |
| B3 | **Content/link silently filtered** | Nothing on profile after several checks; text-only version works | Move links to a **reply**; try without the @-mention/aggressive combo |

## Symptom C — composer won't open / stuck on a spinner

| # | Cause | Tell | Fix |
|---|---|---|---|
| C1 | **Stale DOM tampering** from a prior flow (e.g. `#interop-outlet` pointerEvents disabled) | Composer greyed / clicks do nothing | **Reload the page** (wipes the tampering) and reopen fresh |
| C2 | **Stale element ref** | `Ref … not found in current snapshot` | Re-`browser_snapshot` (to file), grep the fresh ref, click immediately |
| C3 | **Browser hung/crashed** | Nav timeouts, `ERR_ABORTED`, `Target closed` | See Symptom D |

## Symptom D — navigation timeout / ERR_ABORTED / "Target page closed"

| # | Cause | Tell | Fix |
|---|---|---|---|
| D1 | **Browser crashed/hung** | 60s nav timeouts repeat | Let it close, then `browser_navigate` again = fresh relaunch. If persistent, ask the user to restart the MCP browser |
| D2 | **beforeunload dialog** (leaving a composer with unsent text) | Modal state lists `"beforeunload" dialog` | `browser_handle_dialog accept:false` (stay) — then finish the post before navigating away |
| D3 | **Persistent-profile lock** (another Chrome holds `socials-mcp-profile`) | "locked by an open browser" | Kill the stale chrome procs bound to the profile dir (see auto_scrape.clear_stale_profile_locks) |
| D4 | **Orphaned MCP servers hold the profile — you never get a browser at all** | `Browser is already in use for ...socials-mcp-profile, use --isolated to run multiple instances`, repeating on every call. NOT tab contention — you have no page to drive, so the tab workarounds don't apply | See "Profile-lock hygiene" below. Do NOT kill blind while other agents are publishing. |
| D5 | **Platform account interstitial with a click-blocking overlay** (X: "Review your email") | Clicks on the compose button time out with "mask ... intercepts pointer events"; a full-screen prompt sits on `/home` with no close button and Escape does nothing. Looks identical to a wedged browser — this cost several failed attempts on 2026-08-04 before being spotted | Navigate **directly to the composer URL**, bypassing the interstitial — on X that's `https://x.com/compose/post`. ⚠️ Do NOT click the interstitial's own buttons to clear it; they change account settings. Leave it for the operator. |

### Profile-lock hygiene (added 2026-08-04, after 20 orphans accumulated since 30 July)

Every Claude session spawns its own `@playwright/mcp` server against the **same** `--user-data-dir`.
Only the first to launch a browser gets the profile; every later server is locked out **permanently** —
waiting does not help, because the holder is a long-lived server, not a task that finishes.

Diagnose before killing anything:
```powershell
# which MCP servers exist
Get-CimInstance Win32_Process -Filter "Name='node.exe'" |
  Where-Object { $_.CommandLine -like '*playwright*mcp*' } |
  Select-Object ProcessId, CreationDate | Sort-Object CreationDate

# which one actually owns the browser — the ParentProcessId of the chrome procs IS the holder
Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" |
  Where-Object { $_.CommandLine -like '*socials-mcp-profile*' } |
  Select-Object ProcessId, ParentProcessId
```

Then kill **only the orphans**, preserving the holder pair (the mcp server + its npx parent):
```powershell
$holder = @(<mcpServerPid>, <npxParentPid>)
Get-CimInstance Win32_Process -Filter "Name='node.exe'" |
  Where-Object { $_.CommandLine -like '*playwright*mcp*' -and $holder -notcontains $_.ProcessId } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

⚠️ **Never kill the holder while a publish is in flight.** Killing the browser mid-post can leave a
half-submitted post (an IG reel shared with no caption, a LinkedIn video part-uploaded) and you won't
know what landed — which then risks a duplicate on retry. Wait for in-flight agents to report, or
verify the platform state first. Killing orphans is always safe; killing the holder is not.

The profile itself and all logins survive either way — only the running browser is lost.

---

## Symptom E — Instagram reel published live but caption is empty (post-publish DOM-desync)

| # | Cause | Tell | Fix |
|---|---|---|---|
| E1 | **Caption dropped between Share and the live post**, even though the composer showed the full caption + correct char counter right before Share | Reel is live (media, cover, timestamp all correct) but the post page body has NO caption text at all — just "Original audio / No comments yet." | Reopen "More Options" → **Edit** on the live post, retype the caption with real keystrokes (`slowly:true`, not `fill`), verify the char counter, click **Done**, wait ~5s, then reload the post URL FRESH to verify. **Root cause identified 2026-07-30: shared-browser tab contention** — when the Edit attempt itself runs while other publishing agents are still actively fighting over the same browser session, the "Done" click and/or the reload can land against a stale/contended tab, so the edit silently doesn't persist (looked successful, wasn't). It failed twice in a row for exactly this reason on 2026-07-29's edition, then succeeded immediately on a clean single-agent attempt once all other publishing agents had finished. **Fix: don't attempt this repair while any other platform agent is still running** — wait until the browser session is fully free (all other agents from the batch have reported back), then do ONE clean Edit attempt. It should work on the first try in a quiet session.

---

## Standing pattern — publishing to multiple platforms via parallel background agents

Proven across many consecutive AI Top 5 editions (2026-07-27 through 08-01) and several ad-hoc
multi-platform posts. When dispatching platform-publish agents in the background for one post:

1. **Dispatch YouTube first, alone, and wait for its real URL.** It uses the OAuth Data API (see
   `youtube_uploader.py`), not the shared browser — immune to tab contention, and every other
   platform's copy needs the real `youtu.be/<id>` link baked in before it can be drafted correctly.
2. **Dispatch Twitter, Bluesky, and Instagram together.** Brief each agent explicitly that this is
   expected: other agents share the same browser session, tabs will get stolen mid-action, verify
   you're on your own tab before every action, and stop after ~2 clean contended attempts rather than
   grind — a bail-out with nothing typed/submitted is a **safe no-op**, not a failure to fix.
3. **When an agent bails on contention, resume it via `SendMessage` one at a time**, only after the
   others have finished — never re-dispatch a fresh agent for the same platform mid-batch (adds to
   the contention rather than resolving it). It reliably works cleanly once the session is quiet.
4. **Cross-tab contamination is a real, observed risk — verify, don't just trust self-reports.**
   Confirmed twice: a Twitter agent's stray "Post" click landed on a **different agent's own Bluesky
   tab** mid-contention and submitted that agent's already-typed draft — once the Bluesky agent's own
   report said "not posted" when it actually had been, and once a Twitter agent's report flagged it as
   an "unintended post" when it was actually the other agent's legitimate, approved work. **When in
   doubt about a Bluesky post's real state, check directly** — `curl` the public API rather than
   trust either agent:
   ```
   curl -s "https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed?actor=yourhandle.bsky.social&limit=3"
   ```
   (No equivalent trivial public check exists for Twitter/Instagram — for those, a fresh page load /
   profile check is the fallback.)
5. **Instagram specifically**: always have the agent reload the post fresh after Share and verify the
   caption rendered (Symptom E below) — and if it didn't, do NOT attempt the fix while any other
   platform agent may still be running (same contention root cause).

### 🧹 Every publishing agent MUST clean up after itself (added 2026-08-04)

Put this in every dispatch brief. It is not optional housekeeping — orphaned browsers are what caused
the 2026-08-04 outage where 20 stale MCP servers had piled up since 30 July and two publishes were
locked out entirely (see Symptom D4).

Before reporting back, an agent must:

1. **Close the browser it opened** — `browser_close` when the post is verified live. Leaving it open
   keeps the `socials-mcp-profile` user-data-dir locked, which blocks *every other session* from
   getting a browser at all. This is the single most important one.
2. **Delete every temp file it created** — the project-dir copy of the media (the upload sandbox
   requires copying external media in), plus any debug screenshots / `.yml` snapshots. Leaving these
   pollutes `git status` for the next commit and they have repeatedly had to be swept by hand.
3. **Leave the working tree as it found it** — no commits, no edits to tracked files unless that was
   the task. If `git status` shows changes the agent didn't make, say so in the report rather than
   touching them (they usually belong to a concurrent agent).
4. **Report honestly on partial state.** If it bailed mid-flow, say exactly how far it got — composer
   open with text typed? media attached? Share clicked but unverified? The next agent needs that to
   avoid a duplicate post.

Suggested brief wording:
> When done: verify the post is live, delete any temp/media copies and screenshots you created in the
> project dir, and close the browser with `browser_close` so the profile lock is released. Report what
> you cleaned up.

---

## Symptom F — Instagram reel published with a BLACK cover/thumbnail on the profile grid

| # | Cause | Tell | Fix |
|---|---|---|---|
| F1 | **Cover defaulted to frame 0, which is mid-fade-in (black)** | The reel plays fine but its tile on the profile grid is a black square | **Prevent it: trim the fade-in before upload** — `ffmpeg -y -ss 1.2 -i in.mp4 -c copy out.mp4`, then frame 0 is the content card and IG's default cover is correct. Measured 2026-08-03: ig-spoke frame 0 = luminance 7/255, by 1s = 15.7 (content). See instagram.md STEP 0. |
| F2 | **"Select from computer" custom-cover upload silently failed** | You uploaded a still, saw no error, cover is still black | **Don't use that path at all — it's broken** (failed 2026-08-02 and again 2026-08-03). Use the slider DRAG, or better, F1's trim. This was the single biggest repeat-offender because the skill used to list it as an equal option. |
| F3 | **Tried to move the cover slider by clicking frames / arrow keys** | Cover never moves off frame 0 no matter how many clicks | Only `browser_drag` / real mouse down-move-up works. Handle is 74px inside a 307px track → usable travel ~233px, so account for the offset or you undershoot. |

**A reel's cover cannot be changed on web after posting** — get it right before Share, or delete + repost.

---

## Symptom G — YouTube video published with a blank/interstitial thumbnail (AI Top 5)

| # | Cause | Tell | Fix |
|---|---|---|---|
| G1 | **project-bright's delivered `yt-hero.thumb.jpg` is rendered at the "#3 cue" point**, which sits on the blank "AI TOP 5 · LIVE" interstitial rather than a story card | The delivered thumb shows an empty TV screen; a `#3 · <CATEGORY> · CUE` marker is visible top-right. Mean luminance ~30 vs ~53 for a real story card | Run `py fix_thumb.py <yt-hero.mp4>` → writes `yt-hero.thumb-fixed.jpg` from `duration - 15s` (the #1 story card), with a luminance floor that scans outward if that lands dark. **Never upload the delivered `thumb.jpg`.** Occurred on every edition 2026-07-28 → 2026-08-03 before being automated. Upstream fix still owed by project-bright. |

## Keep this list growing
When a NEW failure mode is found (a cause not above), ADD IT here with its screenshot-tell and fix. The
whole point is a **diminishing set of unknowns**: each incident either matches a known row (fast fix) or
teaches a new row (so it's fast next time). Related: [[feedback-fresh-retry]], twitter.md char-limit
section, youtube.md (upload account).
