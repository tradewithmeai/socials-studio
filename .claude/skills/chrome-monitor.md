# Chrome Monitor Skill — scrape browser platforms via the user's real Chrome

Session-driven engagement scrape of the platforms the headless `auto_scrape` struggles with
(Twitter/LinkedIn/Instagram), by reading the user's **real logged-in Chrome** with the
`mcp__claude-in-chrome__*` tools. No profile lock, always logged in. Bluesky/YouTube stay on their APIs.

**When:** you're in a live session and want fresh browser-platform data (or the user says "update the
monitor" / "check engagement"). The unattended 04:00 task can't do this (no Claude there) — this is the
in-session path. Saves through the same pipeline as the normal scrape.

## Procedure

1. **Load the Chrome tools** (deferred) in ONE ToolSearch call:
   `select:mcp__claude-in-chrome__tabs_context_mcp,navigate,javascript_tool,get_page_text,tabs_create_mcp`
2. `tabs_context_mcp {createIfEmpty:true}` — get the tab group + a tabId. (Classifier may say
   "temporarily unavailable" → just retry.)
3. `navigate {url, tabId}` to the profile:
   - Twitter: `https://x.com/YourHandle`  ·  LinkedIn: `/in/your-linkedin-slug/recent-activity/all/`
   - Instagram: `https://www.instagram.com/yourhandle/`
4. **Scroll to load more** (the profile shows only the top of the feed): run via `javascript_tool`
   `window.scrollBy(0,20000)` a few times with a beat between, so older posts load.
5. **Run the platform extractor** via `javascript_tool` (get it with `py chrome_scrape.py js twitter`,
   or paste from below). It returns a JSON array of rows.
6. **Save:** write the returned rows to a scratch `.json`, then `py chrome_scrape.py save twitter
   <rows.json>` → CSV + deltas + reports refresh through `monitor.process_and_save`.

## The Twitter/X extractor (VALIDATED 2026-07-07)

Stored in `chrome_scrape.py:TWITTER_JS` (`py chrome_scrape.py js twitter`). Key gotchas it handles:
- **Counts are in an animated `<number-flow-react>`** whose `textContent` is polluted with injected CSS.
  The real number is **after the last `}`**. (This is why `get_page_text` is noisy and naive reads = 0.)
- **Reverse-associate** each `number-flow` to its nearest `aria-label` control (Reply/Repost/Like/View
  count) — walking DOWN/UP from the button grabs the wrong (first) count and yields identical triplets.
- `[data-testid="User-Name"]` and `[role="group"]` **do NOT exist** in the real-Chrome build — don't rely
  on the headless-scraper selectors. On the profile page, an article is own if its head text contains
  `@YourHandle` and isn't a repost.
- **Views come through** (the headless scraper rarely got them) via the "View count" label.

## LinkedIn / Instagram
No validated extractor yet — build one the SAME way when those pages are open: run diagnostics first
(what selectors exist, where the numbers live), then a reverse-association extractor, then add it to
`chrome_scrape.py:EXTRACTORS`. Do NOT assume the headless `monitor.py` selectors work — the real-Chrome
DOM differs (as X proved).

## Notes
- Distinct from `mcp__playwright__*` (which drives the `socials-mcp-profile` for POSTING). This reads
  the user's own everyday Chrome.
- Create a fresh MCP tab per session; don't reuse an existing tab unless asked.
- If the profile shows stale/old tweets, reload + scroll — confirm recent posts appear before saving.
- See memory `reference-chrome-access`.
