# Twitter Skill

Playwright automation for posting and deleting on Twitter (@YourHandle).
Browser tab 1 is Twitter — already logged in.

**Voice** (register + split logic in `multi-platform-post.md`): **kick the door in** — aggressive,
dense, inline hashtags, @-tag the real players, on-topic trend/figure piggyback, meme energy. This is
the spicy/political channel; lead with the punch. Opinion is fine, fabrication is not.

---

## Post

```
Navigate to https://x.com/home
Click the Post button in the left nav: [data-testid="SideNav_NewTweet_Button"]
Wait for compose dialog to open.
browser_snapshot → find textbox "Post text" [ref=eXXX] — use the ref, NOT the CSS selector (see below)
Type the post content into that ref with browser_type slowly:true
Attach video if needed (see Attach media below)
Submit via JS: [...document.querySelectorAll('button')].find(b => b.innerText.trim() === 'Post' && !b.disabled)?.click()
Verify: page redirects to https://x.com/YourHandle — check for beforeunload dialog (means post FAILED, see below)
Navigate to https://x.com/YourHandle and find the post in articles.
```

### ⚠️ Two fixes for concurrent-agent tab contention (verified 2026-08-02)

When several publishing agents share the browser, the MCP "current tab" gets stolen between calls and
your click/type lands on another platform's page. Two workarounds that actually hold:

1. **Bypass "active tab" entirely** — grab the page object by URL under `browser_run_code_unsafe`:
   `page.context().pages().find(p => p.url().includes('x.com'))`, then drive that page directly. This
   is immune to which tab is currently selected, so no re-select race.
2. **Disambiguate the modal composer** — `[data-testid="tweetTextarea_0"]` matches BOTH the modal
   composer and the inline home-timeline composer behind it, tripping Playwright strict mode. Scope it
   (`[role="dialog"] div[role="textbox"]…`) or tag the modal with a temporary `id` first.

Also useful: guard every JS action with a `location.hostname` check so a stolen tab aborts rather than
acting on the wrong site. Full multi-agent dispatch pattern: `post-troubleshooting.md`.

**Selector notes:**
- Compose button: `[data-testid="SideNav_NewTweet_Button"]` — but see the interstitial note below;
  **navigating straight to `https://x.com/compose/post` is the more reliable way in.**

### 🚨 NEVER START A TWEET WITH AN @-MENTION — it becomes a reply and loses most of its reach

**A tweet whose text begins with `@handle` is classified by X as a reply.** Consequences:
- It does **not** appear on your Posts tab (only Replies / Media).
- It is only surfaced to people who follow **both** you and the mentioned account — a fraction of
  normal reach.

This is worst exactly where we use mentions most: **brand-piggyback posts**, whose whole purpose is
reach. Burned us 2026-08-04 on a `@OpenAI just shipped a @binance connector…` post.

**Fixes** (either is fine — reordering usually reads better):
```
Just shipped by @OpenAI: a @binance connector…     ← reorder, mention not first
.@OpenAI just shipped a @binance connector…        ← leading dot, the classic trick
```

⚠️ **This also breaks post-publish verification.** An @-leading tweet is missing from the Posts tab,
which looks exactly like a failed post. On 2026-08-04 an agent concluded it had silently dropped,
retried, and created a **duplicate**. If a tweet seems missing after publishing, check the **Replies
and Media tabs** and the `CreateTweet` GraphQL response BEFORE retrying.

### ⚠️ Account interstitials block the composer — go direct to /compose/post (verified 2026-08-04)

X periodically shows a full-screen account prompt on `/home` (seen: **"Review your email"**, offering
only "Yes, that's correct" / "No, update email", with no close button and Escape doing nothing). It
lays a `[data-testid="mask"]` overlay over the page, so **every click on the compose button times out**
with "mask ... intercepts pointer events". This looks exactly like a wedged browser or profile lock and
cost several failed publish attempts before it was spotted.

**Fix: `browser_navigate` directly to `https://x.com/compose/post`.** That bypasses the interstitial
entirely and opens a clean empty composer.

⚠️ Do NOT click the interstitial's buttons to dismiss it — they change account settings. Leave it for
the operator.
- Text box: **do NOT use** `div[role="textbox"][data-testid="tweetTextarea_0"]` — times out. Instead: `browser_snapshot` → look for `textbox "Post text" [ref=eXXX]` → use that ref with `browser_type`
- Submit: **do NOT use** `document.querySelector('[data-testid="tweetButtonInline"]')` — returns the button but `.disabled` reports `true` even when visually enabled. Use: `[...document.querySelectorAll('button')].find(b => b.innerText.trim() === 'Post' && !b.disabled)?.click()`
- Verify post went through: page should redirect to `https://x.com/YourHandle`. If a `beforeunload` dialog fires when navigating away, the post did NOT submit — handle with `browser_handle_dialog accept:true` then redo from scratch

---

## Character limit — WRITE TO THE LIMIT (do this BEFORE typing)

Free accounts: **280 weighted characters.** A post must NEVER be drafted over the limit and
trimmed reactively — that wastes a clear/retype cycle every time. Compose to fit on the first
pass, and *use* the budget: a near-280 post that's been optimised beats a short one.

**The counter is weighted, not raw `.length`:**
- Most characters = 1
- Emoji (e.g. 🤖) = **2** (the usual reason a post is silently 1–3 over)
- **EACH URL = 23** regardless of real length (t.co wrapping). ⚠️ **Count EVERY link** — a post with
  two URLs (e.g. `solvx.uk` **and** a `youtu.be/…` link) pays **46**, and even a short bare domain like
  `solvx.uk` still costs 23, not 8. Under-counting a second link is how a post that "should be ~270"
  comes out **7 over** and the Post button greys out.
- Em dash `—`, hashtags, @mentions, newlines = 1 each

**Pre-flight (mandatory before `fill()`):** compute the weighted length of the drafted text
and confirm ≤ 280. Quick budget for our format:
`"Day N with Hermes 🤖"` = ~20 (the 🤖 is 2) · each blank line between paragraphs = 1 ·
`"#BuildInPublic"` = 14. Subtract fixed costs, that leaves ~225 for the body — write the body
to ~that, don't guess. If a draft comes out long, CUT IT DOWN before typing, then verify the
on-screen counter shows a small positive remainder (aim 0–20 left, not 100+).

To compute weighted length in JS before typing:
```js
// emoji ≈ surrogate pairs counted x2; URLs as 23. Rough but catches over-limit.
const weighted = s => {
  let n = [...s].length;                          // code points
  n += [...s].filter(c => c.codePointAt(0) > 0xFFFF).length;  // emoji = +1 extra (=2)
  return n;
};
```
(URLs: replace each with a 23-char placeholder before counting.)

**If the Post button stays disabled with text present, you are almost certainly OVER the limit —
SCREENSHOT and READ THE COUNTER (the circle bottom-right shows a negative number when over) before
assuming Draft.js/browser failure.** (2026-07-04: burned ~10 tool calls "fixing" a phantom Draft.js bug
when the tweet was simply 7 over — two links counted 46, not 23. A screenshot showed the −7 instantly.)
The counter's overflow text is highlighted red; trim that. If the Post button stays disabled with valid
text + finished media, you're over the limit — but with the pre-flight you should never get there. Never trim by editing in place
(see "Editing text"); if you must fix, clear + retype the already-fitted text.

---

## ✅ IMAGE TWEETS: SET ALT TEXT IN-COMPOSER, THEN AUTOMATION CAN POST (proven 2026-07-07)

**The full-auto flow (experiment PASSED on a live image reply):** attach image → thumbnail
`[aria-label="Edit media"]` → ALT tab → `[data-testid="altTextInput"]` → fill → Save
`[data-testid="endEditingButton"]`. If the editor stays open on the Crop tab afterwards (Save
disabled = alt persisted), close it with a JS `click()` on `button[aria-label="Back"]` (role-click
fails) — the draft keeps text + image + ALT badge. Then click Post/submit — with alt text set, the
accessibility reminder NEVER fires. In a reply modal the enabled submit is `[data-testid="tweetButton"]`
(text "Post"); the disabled `tweetButtonInline` "Reply" belongs to the inline composer behind it.
ALWAYS set alt text (accessibility rule 2026-07-07) — it is also what unlocks the automation.

## ⚠️ LEGACY: image tweets WITHOUT alt text still wedge (verified 2026-07-03)

**In-composer alt text WORKS and survives to publish (verified 2026-07-07):** attached thumbnail →
`[aria-label="Edit media"]` → media editor opens at /compose/post/media with Crop/ALT tabs → ALT tab
→ `[data-testid="altTextInput"]` → fill → Save via `[data-testid="endEditingButton"]` (top right) →
back in the draft with alt set. Since the accessibility reminder only fires on images WITHOUT alt
text, setting it in-composer should mean automation CAN click Post on image tweets — pending one
controlled test. Until that passes, keep the hand-off flow below. ALWAYS set alt text either way
(accessibility rule 2026-07-07).

**Automation cannot reliably publish an image tweet in the current X UI.** After clicking Post, the
"Don't forget to make your image accessible" reminder appears; dismissing it ("Not this time", even
via a real Playwright click) redirects to /home and the post **never appears** — ~5 attempts failed
across the full-page and modal routes, with and without a link, while a plain **text-only** tweet
posted first try. Do NOT keep retrying (it wastes the session and risks silent duplicates).

**The workflow that works:** use automation to PREPARE the composer — fill the text (fill via the
`Post text` ref) and attach the image (fileInput → browser_file_upload) — then **hand off to the user
to click Post** and clear the accessibility reminder by hand. Text-only tweets still automate fine.
Also: do NOT press Escape in the composer to dismiss the @-mention typeahead — it opens a "Save post?/
Discard" sheet that stacks a second `confirmationSheetCancel` and muddies everything. Put outbound
links in a REPLY, not the post body (better reach; and rules out link-based silent drops).

## Attach media (photo / video)

The visible "Add photos or video" button is frequently intercepted by an invisible overlay div,
so a normal click times out. Drive the hidden file input directly instead:

```
1. Open the composer and type/fill the text FIRST (see "Editing text").
2. Trigger the hidden file input via JS:
     document.querySelector('[data-testid="fileInput"]').click()
3. browser_file_upload with the ABSOLUTE path.
   ⚠️  File must be within Playwright's allowed roots (the social-monitor project dir).
   If the video is in socials-studio, copy it first:
     Copy-Item D:\Documents\11Projects\socials-studio\<video>.mp4 D:\Documents\11Projects\mygov-hackathon\social-monitor\<video>.mp4
4. WAIT for processing. Poll until "Uploaded (100%)" appears:
     browser_wait_for text:"Uploaded (100%)" time:60
5. Wait an extra 5s after 100% — Twitter does server-side processing after the upload bar clears.
6. Confirm attachment present: [aria-label="Remove media"] exists.
```

Notes:
- A 3–5 MB / ~25s 1080×1920 mp4 processes in ~15–40 s. Don't click Post early.
- `browser_file_upload` errors with "can only be used when there is related modal state
  present" if no chooser is open — you MUST do step 2 first to open it.
- **Upload sandbox (verified 2026-06-12):** uploads only accept paths under the project dir
  (`D:\Documents\11Projects\socials-studio` or its `.playwright-mcp`). External media
  (Screenshots, Screen Recordings) is rejected ("outside allowed roots") — copy it into the
  project first, then upload that copy.

---

## Posting an IMAGE — alt-text reminder (verified 2026-06-14)

When you Post a tweet that has an **image with no alt text**, X does NOT post immediately —
it pops an alertdialog **"Don't forget to make your image accessible"** that BLOCKS the post
(a `[data-testid="mask"]` overlay also appears, which is why a plain Post-button click then
"does nothing"). Two buttons inside `[role="alertdialog"]`:
- `[data-testid="confirmationSheetCancel"]` = **"Not this time"** → posts as-is (no alt text).
- `[data-testid="confirmationSheetConfirm"]` = **"Add description"** → opens the alt-text editor.

To post without alt text: click `confirmationSheetCancel`. (Videos don't trigger this.)
Better practice: add alt text via "Add description" first. This reminder only appears once
you hit Post, so it's the LAST step, not part of the compose form.

## Post flow timing — don't navigate too early (verified 2026-06-14)

After clicking Post, **wait for the composer dialog to actually close** (poll
`[role="dialog"] [data-testid="tweetTextarea_0"]` gone) BEFORE navigating away. Navigating
while the composer still has content fires a `beforeunload` dialog and can leave the page
wedged with a `mask` overlay. If that happens: `browser_handle_dialog accept:false` to stay,
then press Escape / handle the alt-text or Save dialog, and finish the post.

---

## Editing text — DO NOT edit in place

The composer is a **Draft.js** editor. Re-editing existing content corrupts it:
- `fill()` on a non-empty editor **APPENDS** (you get doubled text).
- `document.execCommand('insertText', …)` mangles block structure and silently DROPS the
  first line (especially when an emoji is involved).
- ⚠️ RE-CONFIRMED THE HARD WAY (2026-07-20): execCommand-inserted multi-paragraph text can LOOK
  perfect in the DOM (innerText verifies fine) yet Draft.js's internal state holds almost nothing —
  the published tweet came out as ONLY the trailing hashtag, twice; both had to be deleted. The DOM
  read-back is NOT proof. **Never use execCommand insertText in this composer, even on an empty
  editor** — use `browser_type` (real keystrokes, slowly:true for multi-paragraph) into the
  snapshot-ref'd `textbox "Post text"`, every time.

**Rule: TYPE the FINAL, length-checked text exactly once into an EMPTY editor — real keystrokes only.**

If the text is wrong or doubled, do NOT patch it — **discard the whole draft and start fresh:**
```
1. Click Close: [data-testid="app-bar-close"]   (or press Escape)
2. A "Save post?" alertdialog appears → click the "Discard" button
   (verified 2026-07-07: Discard = `confirmationSheetCancel`, Save = `confirmationSheetConfirm`)
3. Reopen the composer (now empty) and fill once.
   NOTE: discarding also removes any uploaded media — you must re-upload after a discard.
```

---

## Delete

```
Navigate to https://x.com/YourHandle
Wait 2 seconds for feed to load.
Find the target article using JS:
  const articles = document.querySelectorAll('article');
  for (const a of articles) {
    if (a.innerText.includes('<POST_TEXT>')) {
      const btn = a.querySelector('[data-testid="caret"]');
      if (btn) btn.click();
    }
  }
Wait 1 second for menu to open.
Click the Delete menuitem: getByRole('menuitem', { name: 'Delete' })
A confirmation dialog appears — find and click the Delete button:
  const btns = [...document.querySelectorAll('button')];
  btns.find(b => b.innerText.trim() === 'Delete')?.click();
Wait 2 seconds and verify post is gone.
```

**Selector notes:**
- Three-dot menu: `[data-testid="caret"]` inside the article
- Delete menu item: `getByRole('menuitem', { name: 'Delete' })`
- Confirmation: plain `<button>Delete</button>` (no aria-label) — use innerText match

---

## Known quirks
- Twitter profile page URL: https://x.com/YourHandle
- The "Post" button is disabled until text is typed — do not click early
- The "Post" button also stays disabled while a video is still processing — check both
- Confirm the active account BEFORE posting: left nav profile link should be `/YourHandle`
- Pinned posts appear at top but `lines[0] !== 'Pinned'` distinguishes them
- Views are scraped from `a[href*="analytics"]` aria-label on each article
- Persistent login via global playwright config `--user-data-dir` (see memory: reference-browser-profile)
