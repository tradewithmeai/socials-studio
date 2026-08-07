# Instagram Skill

Playwright automation for posting and deleting on Instagram (@yourhandle / YourInstagramHandle).
Browser tab 3 is Instagram — already logged in.

---

## Post (photo / video / reel)

### ⭐ STEP 0 (video only) — TRIM THE FADE-IN BEFORE YOU UPLOAD (added 2026-08-03)

**Do this first and the entire cover-frame problem disappears.** Instagram defaults a reel's cover to
FRAME 0. Our reels (and most screen recordings) fade in from black, so frame 0 is a black square on
the profile grid — historically the #1 reel-quality bug here, "fixed" three separate times and still
recurring.

Root cause measured 2026-08-03: an `ig-spoke.mp4` frame 0 has mean luminance **7/255** (black); by
1s in it's 15.7 and showing the "#1 TODAY'S #1 IN AI" card. The fade is under ~1.2s.

So cut it off before upload — one command, no re-encode:
```bash
ffmpeg -y -ss 1.2 -i <source>.mp4 -c copy <source>-cover.mp4
```
(ffmpeg lives at `C:\Users\<USER>\ffmpeg\bin\ffmpeg.exe`.) Verify frame 0 is now content:
```bash
ffmpeg -i <trimmed>.mp4 -vf "select=eq(n\,0),signalstats,metadata=print:key=lavfi.signalstats.YAVG" -vframes 1 -f null -
```
YAVG under ~10 = still black, trim further. Upload the TRIMMED file. Frame 0 is now the content card,
IG's default cover is correct, and you can skip the cover-setting dance in step 8 entirely.

Costs ~1.2s off the clip (16s → 14.9s on a typical ig-spoke) — no meaningful content lost, the fade is
dead air. If for some reason you can't trim, fall back to the scrubber drag in step 8.

⚠️ **Measure the file you are actually uploading — the hero and the spoke differ** (learned the hard
way 2026-08-04). project-bright fixed the fade-in on the `ig-spoke` but NOT on the `yt-hero`:

| 2026-08-04 delivery | frame 0 luminance | |
|---|---|---|
| `ig-spoke.mp4` | 12.5 | content card — no trim needed |
| `yt-hero.mp4` | **7.9** | still a black fade-in — needs trim or a cover drag |

So "the spoke's frame 0 is fine now" does NOT mean the hero's is. This matters whenever the full 16:9
hero is posted to Instagram instead of the spoke. Always run the luminance check on the exact file
being uploaded rather than assuming from a sibling output.

```
1. Navigate to https://www.instagram.com/yourhandle/
2. Wait 3 seconds.
3. Click the "Continue as yourhandle" button IF it appears (first-visit prompt).
   ⚠️  This button is NOT reachable via querySelector — do browser_snapshot first and use
   the ref returned (e.g. button "Continue as yourhandle" [ref=eXXX]), then browser_click the ref.
4. Click the "New post" / "+" create button (top nav or sidebar).
   Selector: a[href="/create/style/"] or the + icon. Use browser_snapshot to confirm the ref.
5. Click "Post" from the creation type menu (as opposed to Reel/Story/etc.)
   — OR if creating a Reel: click "Reel"
6. A file select dialog opens — browser_file_upload with the ABSOLUTE path.
   ⚠️  Allowed roots: file MUST live under the project dir
   `D:\Documents\11Projects\socials-studio` (or its `.playwright-mcp`). External media
   (Screenshots, Screen Recordings) is rejected — copy it INTO the project first:
     Copy-Item "D:\Documents\Screen Recordings\<clip>.mp4" "D:\Documents\11Projects\socials-studio\<clip>.mp4"
   Trigger: document.querySelector('input[type="file"]').click() then browser_file_upload.
   ⚠️ **That JS trigger can silently no-op** (seen 2026-08-05): the file chooser accepts the path but
   the dialog stays on "Drag photos and videos here" — there appears to be a stale/decoy file input in
   the current DOM. **Fallback that works first time: click the actual "Select From Computer" button,
   then `browser_file_upload`.** If the upload seems to vanish, this is why — don't retry the JS route.
7. The Crop step dialog appears (heading: "Crop").
   SIMPLEST (verified 2026-06-12): IG dialog buttons are div[role=button]/div[tabindex] and
   respond to plain JS .click() — find by text and click:
     const d=document.querySelector('[role="dialog"]');
     [...d.querySelectorAll('button,[role="button"],div[tabindex]')]
       .find(b=>/^next$/i.test((b.innerText||'').trim()))?.click()
   (The depth=8 snapshot-ref approach also works as a fallback, but JS .click() is reliable.)
   ► LANDSCAPE source (screen recording)? Click svg[aria-label="Select Crop"] → choose
     "Original" so it isn't force-cropped to 9:16, THEN Next.
   ⚠️ **CHECK THE CROP ON EVERY UPLOAD — including PORTRAIT sources** (verified 2026-08-03). The
     Crop step defaulted to **1:1** on a 1080x1920 portrait ig-spoke, which would have centre-cropped
     it square and cut the top and bottom off every story card. This rule used to say crop only
     mattered for landscape; that was wrong. How to catch it: compare the `<video>` element's
     rendered box against its container — e.g. a 501x893 video inside a 501x501 container means it's
     being squared. Fix: Back → "Select Crop" → pick 9:16 (or Original). The cover-slider position
     survives the back-and-forth, so you don't lose that work.
8. The Edit step dialog appears (heading: "Edit"). COVER FRAME.
   **If you did STEP 0 (trimmed the fade-in), frame 0 is already the content card — just confirm the
   cover preview isn't black and click Next. Nothing else to do.** The rest of this step is the
   fallback for when you couldn't trim.

   Skipping the cover entirely defaults the thumbnail to FRAME 0, which on an untrimmed fade-in reel
   is a BLACK grid thumbnail.

   ⚠️ **"Select from computer" IS BROKEN — DO NOT USE IT.** (2026-08-02, 2026-08-03.) The custom-still
   upload appears to accept the file but the cover silently stays on black frame 0. It was previously
   documented here as an equal alternative to the drag, which is exactly why this bug kept recurring —
   agents reached for it, it failed silently, and a publish's worth of attempts went with it. It is
   NOT a fallback. It is a dead end.

   ✅ The ONLY working in-browser method is **dragging the cover slider**:
   - It's a `slider` element — **drag it with `browser_drag`** (or real `page.mouse` down/move/up).
   - Clicking filmstrip frames (`elementFromPoint().click()`) and pressing ArrowRight on the focused
     slider both DO NOTHING (verified 2026-07-16).
   - ⚠️ Geometry (measured 2026-08-03): the handle is **74px wide inside a 307px track**, so usable
     travel is only ~233px. A naive "drag to 50% of track width" lands wrong — account for the handle
     offset or you'll undershoot.
   - Screenshot to confirm the cover preview shows content, not black, before Next.
9. The Caption/Details step dialog appears (heading: "Create new post" or "New reel").
   browser_snapshot the dialog → find the "textarea" or contenteditable caption field → type the caption.
   Character limit: 2200 characters.
10. Click the "Share" button to publish.
    browser_snapshot the dialog → find ref for "Share" button → browser_click.
11. Wait for success text: "Reel shared." / "Your reel has been shared." then click "Done".
    ⚠️ **ALWAYS reload the post URL fresh after this and verify the caption actually rendered** — a
    recurring bug (5+ occurrences across 2026-07-28 to 08-02) drops the caption silently even when
    the composer showed it correctly right before Share. Root cause + fix: see
    `post-troubleshooting.md` Symptom E (it's browser-contention-driven — don't attempt the fix while
    other platform-publishing agents may still be running).
    ⚠️  If it shows "Something went wrong. Please try again." with NO retry button (seen
    2026-06-12): the web composer is wedged. A plain re-trigger of the file input on the stuck
    dialog will NOT reload the video. FULLY reload instagram.com and redo from step 4. (It
    failed once then succeeded after a clean reload.)
12. Navigate to https://www.instagram.com/yourhandle/ and confirm the new post appears.
```

**Key rule: re-snapshot after every navigation step.** Refs are session-scoped and snapshot-scoped — they become stale after any page change or dialog transition. Always re-snapshot and get a fresh ref before clicking.

---

## Dialog navigation (the critical flow)

The Create-New-Post dialog cycles through these headings:
1. **Crop** → Next
2. **Edit** (Adjustments, Filters) → Next
3. **Create new post** / **New reel** (Caption + Share button)

At each step:
```
browser_snapshot                           # get the dialog ref, e.g. e940
browser_snapshot target=<dialog_ref> depth=8   # get inner buttons including "Next"/"Share"
browser_click ref=<button_ref>             # click it
```

Do NOT use:
- `button:has-text("Next")` — fails (Playwright has-text locator doesn't work here)
- `document.querySelector('button[type="button"]')` — returns wrong button or undefined
- `getByRole('button', { name: 'Next' })` — strict mode violation (multiple matches)

---

## Selector notes

- "Continue as yourhandle" button: use `browser_snapshot` → ref (light DOM button, not shadow)
- Create button: `a[href="/create/style/"]` or `[aria-label="New post"]`
- Dialog container: identified in snapshot as `dialog` role with the current step heading
- Caption textarea: inside the final dialog step — snapshot + ref to type into
- Share button: inside the final dialog step — snapshot + ref to click
- Success indicator: "Reel shared." text on page / in dialog

---

## Allowed roots (file upload)

`browser_file_upload` is scoped to THIS project: `D:\Documents\11Projects\socials-studio`
(and its `.playwright-mcp`). Media stored elsewhere (Screenshots, Screen Recordings, the old
mygov-hackathon repo) is rejected with "outside allowed roots". Copy it INTO this project first:
```powershell
Copy-Item "D:\Documents\Screen Recordings\<clip>.mp4" "D:\Documents\11Projects\socials-studio\<clip>.mp4"
```

---

## Scrape (engagement data)

Navigate to https://www.instagram.com/yourhandle/ and get post URLs:
```js
() => {
  const links = [...document.querySelectorAll('a[href*="/p/"], a[href*="/reel/"]')];
  return links.map(a => a.href).filter((v, i, arr) => arr.indexOf(v) === i);
}
```

For each post URL, navigate to it, wait 2s, then:
```js
() => {
  const lines = document.body.innerText.split('\n').map(l => l.trim()).filter(l => l.length > 0);
  const insightsIdx = lines.findIndex(l => l === 'View Insights');
  const url = window.location.href;
  const postId = url.match(/\/p\/([^/]+)/)?.[1] || url.match(/\/reel\/([^/]+)/)?.[1] || '';
  const nums = lines.slice(insightsIdx + 1, insightsIdx + 5)
    .concat(lines.slice(Math.max(0, insightsIdx - 10), insightsIdx))
    .filter(l => /^\d+$/.test(l)).map(l => parseInt(l));
  const caption = lines.slice(2, insightsIdx - 3)
    .filter(l => !l.match(/^\d+$/) && l !== 'Reply' && !l.includes('yourhandle')).join(' ').slice(0, 200);
  return {
    postId, isOwn: true, preview: caption.slice(0, 100),
    likes: nums[0] || 0,
    comments: lines.filter(l => l === 'Reply').length,
    reposts: 0, bookmarks: null, views: null, quotes: null, videoViews: null,
    rawMetrics: `View Insights | nums: ${JSON.stringify(nums)} | replies: ${lines.filter(l => l === 'Reply').length}`
  };
}
```

---

## Delete

```
Navigate to the post URL.
Click the three-dot "..." menu (top right of post).
Select "Delete" from the dropdown.
Confirm deletion in the dialog.
```

---

## Known quirks

- Profile URL: https://www.instagram.com/yourhandle/
- The "Continue as yourhandle" account-switch prompt appears intermittently — always handle it before interacting with the page
- Dialog "Next"/"Share" buttons: JS .click() on the div[role=button] (found by innerText)
  works reliably (verified 2026-06-12). `button:has-text()` / getByRole strict-mode fail; the
  depth=8 snapshot-ref approach is a fallback.
- Cover frame: prefer STEP 0 (trim the fade-in before upload) so frame 0 is already content. If you
  didn't trim, you MUST set the cover by DRAGGING the slider at the Edit step — "Select from
  computer" is broken and fails silently (see step 8).
- A reel's cover can't be changed on web after posting — get it right at Edit, or delete+repost.
- The Crop and Edit steps are mandatory even if you don't change anything — you must click Next through each
- After "Reel shared." the dialog auto-closes; navigate to profile to verify
- Login persists via `--user-data-dir` profile — if logged out, re-authenticate and the profile will save for next time
- Views/impressions on Instagram are behind "View Insights" (only visible to account owner) — only visible when logged in
