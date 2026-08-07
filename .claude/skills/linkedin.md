# LinkedIn Skill

Playwright automation for posting and deleting on LinkedIn (Your Name).
Browser tab 2 is LinkedIn — already logged in.

**Voice** (register + split logic in `multi-platform-post.md`): **the credible hub** — professional,
measured, the substantive write-up other socials link back to. Milestones/announcements only. No memes,
no aggression, no spice.

---

## 📌 Posting policy (set 2026-06-20): MILESTONES ONLY — not daily

LinkedIn is **NOT** part of the daily Hermes rotation. Post here only for **headlines /
milestones**: launches, big results, major announcements. The daily Day-N reel goes to
Instagram, Twitter, Bluesky, and YouTube — **not** LinkedIn.

Rationale: every daily LinkedIn reel landed flat while the one win was a milestone
announcement. This is a cadence/fit decision, not a verdict on LinkedIn's audience — the
dataset is still too thin for firm conclusions. Do not auto-mirror the daily reel here.

---

## ⚠️ New UI: the composer lives in a SHADOW DOM (verified 2026-06-08)

LinkedIn migrated the composer into a web-component shadow root: `#interop-outlet` (a host div
in the light DOM with an open `shadowRoot`). Consequences:
- `document.querySelector('[role="dialog"]')` / `.ql-editor` in the LIGHT dom return NOTHING —
  the dialog, editor, media buttons and Post button are all INSIDE `#interop-outlet.shadowRoot`.
- Playwright role locators (`getByRole`, `getByText`) DO pierce open shadow roots, so
  `browser_type`/`browser_click` via a snapshot **ref** or role still work. `browser_snapshot`
  also traverses the shadow DOM and assigns refs — use it to get current refs.
- To inspect state in `browser_evaluate`, reach in explicitly:
  `document.querySelector('#interop-outlet').shadowRoot.querySelector(...)`.

## Post

```
1. Navigate to https://www.linkedin.com/feed/ (logged in).
2. Open the composer. "Start a post" is a div[role="button"] in the LIGHT dom, but an
   #interop-outlet overlay intercepts clicks. Two-step:
     a. document.querySelector('#interop-outlet').style.pointerEvents = 'none'
     b. real click the "Start a post" button (getByRole / snapshot ref).
   The composer then renders INSIDE #interop-outlet.shadowRoot. RE-ENABLE the overlay
   afterwards: document.querySelector('#interop-outlet').style.pointerEvents = ''
   (the dialog lives in that subtree — leaving it disabled blocks all composer clicks).
3. browser_snapshot to a file → grep for refs:
     - textbox "Text editor for creating content"  (the editor)
     - button "Add media"
     - button "Post"  (exact; NOT "Strengthen post")
4. Type into the editor ref with browser_type (fill — Quill editor, clean newlines, no
   Draft.js doubling issue). **UPDATE 2026-08-01: the "no hashtags / 0 emoji" rule below is stale** —
   multiple LinkedIn posts this period (Skellator, Percy PA, Project Bright) shipped successfully with
   both `#buildinpublic`-style hashtags and emoji (🤞, →), matching the account's established voice.
   Use hashtags/emoji same as the other platforms unless a specific post calls for a more formal tone.
5. Click Post via its ref / getByRole('button',{name:'Post',exact:true}).
6. Verify at /in/your-linkedin-slug/recent-activity/all/ — see "Verify" note below.
```

**Selector notes:**
- Everything is under `#interop-outlet.shadowRoot`. Get refs from a fresh `browser_snapshot`.
- Editor: role `textbox` name "Text editor for creating content".
- Submit: role `button` name "Post" with **exact:true** (avoids "Strengthen post").
- Console floods 100-200+ errors — LinkedIn internals, ignore.

## Attach video / image (verified 2026-06-08)

```
1. Type the text first.
2. Click button "Add media" (ref) — opens the file-chooser modal state directly.
3. browser_file_upload with the ABSOLUTE path.
4. A media-edit step appears with a "Next" button — click it to return to the composer.
5. Video keeps "processing" but you can usually Post; the <video> element reaching
   readyState 4 in the shadow root means it's loaded. Then click Post.
6. Do NOT trust /processing|error/ regex on shadowRoot.textContent — it matches embedded
   CSS (`.upi-processing`, `signal-error-small`). Check real elements, not textContent.
```

**⚠️ A URL in the post text blocks video (verified 2026-06-12):** if the body contains a link
(e.g. `https://stratbot.solvx.uk`), LinkedIn auto-attaches a **link-preview card** that takes
the media slot — the "Add media" button DISAPPEARS and a "Remove media" button appears instead.
To attach a video anyway:
```
1. Find and click "Remove media" (it refers to the link-preview card, not your video) — get
   its ref from a shadow-DOM snapshot.
2. "Add media" returns. Re-snapshot for its fresh ref, click it, upload the video.
```
The URL stays clickable in the post text, so you lose only the preview card, not the link.
Refs shift after typing/removing — always re-snapshot before each click.

**File upload sandbox:** `browser_file_upload` only accepts paths under the project dir
(`D:\Documents\11Projects\socials-studio` or its `.playwright-mcp`). Copy external media
(Screenshots, Screen Recordings, renders elsewhere) into the project first.

**⚠️ A published LinkedIn post CANNOT have media added to it afterwards** (confirmed 2026-08-02 —
this caused real confusion: a video was meant to go out with a same-day text post, the text post
published first without the video attached, and by the time the video was ready to attach there was
no edit path to add it — only a brand-new post). If text and media are meant to ship together,
**attach the media BEFORE clicking Post**, in the same composer session. If the media isn't ready
yet and the text can't wait, either hold the whole post until both are ready, or accept it'll be two
separate posts and say so up front.

**⚠️ Don't navigate immediately after clicking Post on a large video (verified 2026-08-04).** With a
32 MB upload still in flight, navigating away fires a `beforeunload` dialog and the navigation times
out at 60s — which looks like a failed post but isn't. Handle it with `browser_handle_dialog
accept:false` (stay on the page), wait ~45s for the upload to finish, confirm the composer has closed,
THEN verify. The post lands fine; it's the early navigation that breaks.

**Verify (IMPORTANT):** the activity feed's top post is NOT always your newest — the Day 2
post (also contains "Hermes") sat above it briefly. Match on text UNIQUE to this post
(e.g. "half-blind", "Chrome DevTools Protocol") and read the first item's `data-urn`
(`urn:li:activity:<id>`) to capture the real post id. Reload once if it hasn't appeared.

---

## Delete

```
Navigate to https://www.linkedin.com/in/your-linkedin-slug/recent-activity/all/
Wait 3 seconds.
Find and click the three-dot control menu on the target post:
  document.querySelector('#ember91').click()
  — NOTE: ember IDs change on reload. Better: find the first listitem containing the post text,
    then click its [aria-label*="control menu"] button.
Wait 1 second for dropdown.
Click "Delete post" button via accessibility tree snapshot: getByRole('button', { name: 'Delete post' })
A confirmation modal appears: "Delete post? Are you sure you want to permanently remove this post from LinkedIn?"
Confirm by clicking the Delete button:
  const btns = [...document.querySelectorAll('button')];
  btns.find(b => b.innerText.trim() === 'Delete')?.click();
Wait 2 seconds and verify post is gone from page.
```

**Selector notes:**
- Control menu button: `button[aria-label="Open control menu for post by Your Name"]`
  — There are multiple (one per own post). Target by finding the listitem containing the post text first,
    then querying within it.
- Delete post button: `getByRole('button', { name: 'Delete post' })` — works once dropdown is open
- Confirmation Delete button: plain innerText match `'Delete'` — no aria-label
- Do NOT use `getByRole('button', { name: 'Delete' })` — strict mode violation when multiple match

---

## Scrape (engagement data)

Uses `[role="listitem"]` selector (2025+ DOM). Fallback: `.feed-shared-update-v2`

```js
() => {
  window.scrollTo(0, 800);
  let posts = [...document.querySelectorAll('[role="listitem"]')]
    .filter(el => el.innerText && el.innerText.trim().length > 30);
  if (posts.length === 0)
    posts = [...document.querySelectorAll('.feed-shared-update-v2')]
      .filter(el => el.closest('.feed-shared-update-v2') === el);
  // ... extract likes, comments, reposts, views from each post
}
```

**Views:** only visible on own posts — regex match `/([\d,]+)\s*(impression|view|people saw)/i` on post text.

---

## Known quirks
- Feed page (`/feed/`) works; activity page (`/recent-activity/all/`) needed for own post metrics
- LinkedIn console floods with errors (180+) — these are LinkedIn internals, ignore them
- `ember*` IDs regenerate on every page load — always re-snapshot, never hardcode
- The confirmation dialog has no ARIA label on the final Delete button — must match by innerText
- Cookie banner: `document.querySelectorAll('button').forEach(b => { if (b.innerText.includes('Accept')) b.click(); })`
