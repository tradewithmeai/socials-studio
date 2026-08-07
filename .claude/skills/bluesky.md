# Bluesky Skill

Playwright automation for posting and deleting on Bluesky (@yourhandle.bsky.social).
Browser tab 0 is Bluesky — already logged in.

**Voice** (register + split logic in `multi-platform-post.md`): **the wine bar** — dry, clever, dev-
focused, dense, hashtags OK. Same story as Twitter minus the rage: show the *insight / hypocrisy*.
No shock, no politics/Trump. Geek-sensational, not loud.

---

## Post

```
Select tab 0 (Bluesky): browser_tabs action=select index=0
Navigate to https://bsky.app (if not already there)
Wait 2 seconds.
Click the "New post" compose button (top-left or fixed button with pencil icon).
Type the post content into the textbox.
Click "Publish" or "Post" button.
Wait 2 seconds.
Navigate to https://bsky.app/profile/yourhandle.bsky.social to verify.
```

**Selector notes (verified 2026-06-08):**
- Compose button: `[aria-label="Compose new post"]`
- Text box: the composer is a single `div[contenteditable="true"]` (no testid). `fill()` works
  cleanly. innerText shows extra `\n` between paragraphs but it renders as single blank lines —
  that's a display artifact, not a problem.
- Submit: `[aria-label="Publish post"]` (its text reads "Post"). ⚠️ On a POST PAGE replying, the button is `[aria-label="Publish reply"]` (verified 2026-07-07).

## Character limit — WRITE TO THE LIMIT (before typing)

**300 graphemes** (emoji = 1, unlike Twitter; URLs count their full literal length, NOT 23).
Same rule as Twitter: never draft over and trim reactively — compose to fit the first time and
*use* the budget (a well-optimised ~290 beats a thin 180). Pre-flight: count `[...text].length`
(grapheme-ish) and confirm ≤ 300 BEFORE `fill()`; after filling, the on-screen circular counter
should read a small positive remainder (aim 0–25 left). If over, CUT before typing — to fix a
filled editor, select-all + Delete then retype the fitted text (don't patch in place).

NOTE: Bluesky's 300 ≠ Twitter's 280, and the weighting differs (emoji 1 vs 2, URLs literal vs
23). Write the Twitter version first to the tighter 280 weighted budget, then the Bluesky one
can be slightly longer / keep a real URL if needed.

---

## Attach video / image (verified 2026-06-08)

```
1. Type the text FIRST into the contenteditable.
2. Click [aria-label="Add media to post"] — this opens the file-chooser modal state directly
   (no overlay issue like Twitter).
3. browser_file_upload with the ABSOLUTE path (e.g. D:\...\hermes_day3.mp4).
4. CRITICAL — Bluesky processes video AFTER upload and shows "Processing video..." at the
   bottom of the composer. WAIT for that text to disappear (browser_wait_for textGone
   "Processing video", up to ~60s) before publishing. Publishing early is why a past post
   (post-005) went out TEXT-ONLY with no video.
5. Confirm a <video> element + [aria-label*="Remove"] exist and no "failed/error" text.
6. Click [aria-label="Publish post"].
7. Verify: open the post URL and confirm a <video> / play button is present — the feed-item
   thumbnail may NOT expose a <video> tag until opened, so check the post detail page.
```

Video limits: Bluesky max ~60s / 50 MB. The 52s 1080×1920 mp4 fits.

**Upload sandbox (verified 2026-06-12):** `browser_file_upload` only accepts paths under the
project dir (`D:\Documents\11Projects\socials-studio` or its `.playwright-mcp`). Copy external
media (Screenshots, Screen Recordings) into the project first, then upload that copy.

---

## Link card (external URL embed) — verified 2026-07-16

For a post whose ONE link should show a rich card (e.g. a YouTube video), the card is NOT automatic
after `fill()`:

- **`fill()` skips card detection.** It sets the text but does NOT fire the input events Bluesky's
  URL-facet detector listens for, so the **"Add link card"** suggestion never appears and you publish
  a plain (still-clickable) link with no card. This was once mis-diagnosed as "Bluesky flaky" — it is a
  PROCESS error, not a platform one. Do not repeat it.
- **Correct flow:** type the URL with REAL keystrokes so detection fires — either compose the whole
  post via `browser_type slowly:true` (pressSequentially) from an empty composer, or after filling the
  text, retype just the URL with real keystrokes. Bluesky then shows an **"Add link card"** button
  below the composer. Click it, WAIT for the card thumbnail to load, then Publish.
- ONE link only (link-cards rule): a 2nd URL / bare domain hijacks the card to the wrong favicon.
- A published post CANNOT gain a card retroactively — to add one, delete + repost with the card.

---

## Delete

```
Navigate to https://bsky.app/profile/yourhandle.bsky.social
Wait 3 seconds.
Find the target post using [data-testid^="feedItem"] or [data-testid^="postItem"].
Click the three-dot "..." menu on the post.
Select "Delete post" from the dropdown.
Confirm deletion if prompted.
```

**Selector notes:**
- Post containers: `[data-testid^="feedItem"]`, `[data-testid^="postItem"]`
- Post ID extracted from: `a[href*="/post/"]` — matches `/post/([a-z0-9]+)/`
- Own posts: text does NOT include "reposted by" or "Reposted by"
- Views: not exposed on Bluesky — always null

---

## Scrape (engagement data)

```js
() => {
  const results = [];
  const posts = document.querySelectorAll('[data-testid^="feedItem"], [data-testid^="postItem"]');
  for (const post of posts) {
    const text = post.innerText || '';
    if (!text || text.trim().length < 10) continue;
    const isOwn = !text.includes('reposted by') && !text.includes('Reposted by');
    const link = post.querySelector('a[href*="/post/"]');
    const postId = link ? (link.href.match(/\/post\/([a-z0-9]+)/i)?.[1] || '') : '';
    let likes = 0, comments = 0, reposts = 0, quotes = null;
    post.querySelectorAll('button, [role="button"]').forEach(btn => {
      const label = (btn.getAttribute('aria-label') || btn.innerText || '').toLowerCase();
      const m = label.match(/([\d,]+)/);
      const num = m ? parseInt(m[1].replace(/,/g, '')) : 0;
      if (label.includes('like')) likes = Math.max(likes, num);
      if (label.includes('repl') || label.includes('comment')) comments = Math.max(comments, num);
      if (label.includes('repost') || label.includes('reblog')) reposts = Math.max(reposts, num);
      if (label.includes('quote')) quotes = Math.max(quotes || 0, num);
    });
    results.push({ postId, isOwn, likes, comments, reposts, quotes, views: null });
  }
  return results;
}
```

---

## Known quirks
- Views are not available on Bluesky — store as null, do not attempt to scrape
- Profile URL: https://bsky.app/profile/yourhandle.bsky.social
- If tab is on Discover feed, own posts won't appear — navigate to profile first
- Quotes (requotes) ARE available via aria-label containing "quote"
- Tab index is 0 in the current session but may shift — use `browser_tabs list` to confirm
