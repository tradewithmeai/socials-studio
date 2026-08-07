# YouTube Skill

Playwright automation for publishing a **standalone** video to YouTube via YouTube Studio
(studio.youtube.com). Browser uses the persistent profile (socials-mcp-profile).
Verified end-to-end 2026-06-13 (standalone publish) and 2026-06-17 (16:9 video WITH an
end screen — the "A week with Hermes (Week 1)" round-up, youtu.be/vdT-oIXBndA).

Channel: **SolvX** — `UC_S2gc65dDBS61OIzHWHU9g`.

---

## ⚠️ Account / channel (read first)

The logged-in Google account has MORE THAN ONE channel. Getting the wrong one is the easy
mistake here:
- `Rich Watson` (UCCQzPUG6KLxw-IPrV6D0GAw) = WRONG (personal).
- `SolvX` (UC_S2gc65dDBS61OIzHWHU9g) = the one we publish to.

Always confirm: navigate to https://studio.youtube.com/ and check the channel name in the
left rail / `body.innerText` ("Your channel | SolvX"). If it's wrong: click `#avatar-btn`
→ "Switch account" → pick the SolvX channel (or the user logs into the right Google account).

### ⚠️ OAuth API upload — sign in as the CHANNEL OWNER (verified 2026-07-04)

The reliable upload path is the **OAuth API**, not the browser: `youtube_uploader.py`
(`upload_video(video_path, title, description, tags, visibility, dry_run)`), token at repo-root
`youtube_token.json`, re-auth with `setup_youtube_oauth.py`. It's clean (no browser) and returns the
watch URL. Used it to publish the AI Top 5 (jugz_yzfJo8).

### ⚠️ AI Top 5: the DELIVERED thumbnail is always unusable — regenerate it

project-bright's `yt-hero.thumb.jpg` lands on the blank "AI TOP 5 · LIVE" interstitial TV shot, not
a story card. Every delivered thumb carries a `#3 · <CATEGORY> · CUE` marker top-right, so the render
is being taken at the "#3 cue" point — and that cue sits on the transition. True on **every** edition
2026-07-28 → 2026-08-03 (six straight), each fixed by hand until this was automated.

Measured (2026-08-03, 1920x1080 / 130.05s): delivered thumb mean luminance **~30** (interstitial),
frame 0 **~8** (fade-in), t=115s **~53** (the #1 story "WHAT HAPPENED" card).

Fix — never hand-pick frames for this:
```bash
py fix_thumb.py campaigns/ai-top5/media/<date>-daily/yt-hero.mp4
```
Writes `yt-hero.thumb-fixed.jpg` at `duration - 15s`, with a luminance floor that scans outward if
that lands dark. Pass the `-fixed` file as the upload thumbnail. Upstream fix (project-bright moving
its thumbnail cue off the interstitial) is still owed — this is our side of it.

**This is now the primary path for EVERY upload, not just AI Top 5** — used exclusively and
successfully across every daily AI Top 5 edition plus several ad-hoc uploads (Skellator, Percy PA)
in the 2026-07-27–08-01 period. It also supports a **custom thumbnail** (confirmed working
repeatedly — e.g. fixing project-bright's recurring blank-intro-frame delivered thumbnails by
pulling a real frame from the video and passing it as the thumbnail arg). The browser-wizard flow
below (`studio.youtube.com`) is the older/fallback path — reach for the API first; only fall back to
the browser wizard for things the API doesn't cover (e.g. end screens, which the API upload call
doesn't set — add those via the wizard afterwards if needed).

TWO ACCOUNTS, don't confuse them — this cost us an hour:
- **OAuth app** (GCP project "<GCP_PROJECT_NAME>" <GCP_PROJECT_NUMBER>, client_id `<OAUTH_CLIENT_ID>…`) is owned
  by **<OAUTH_APP_OWNER_EMAIL>**.
- **The SolvX channel** (`UC_S2gc65dDBS61OIzHWHU9g`) is owned by **<CHANNEL_OWNER_EMAIL>**.
- **At the `setup_youtube_oauth.py` consent screen, sign in as `<CHANNEL_OWNER_EMAIL>`** (the channel
  owner). If you sign in as <OAUTH_APP_OWNER>, the token authenticates and can READ stats, but has **0
  channels**, so `videos.insert` 401s with **`youtubeSignupRequired`**. Reading needs any account;
  UPLOAD needs the channel-owner account.
- Verify the token is pointed at the right channel BEFORE uploading:
  `yt.channels().list(part='snippet', mine=True).execute()` → must return 1 item titled **SolvX**
  (`UC_S2gc65dDBS61OIzHWHU9g`). 0 items = wrong account, re-auth as <CHANNEL_OWNER>.
- Description gotcha: YouTube rejects `<` and `>` in the description (`invalidDescription`) — use `→`
  or words, not `->`.

Full account/app notes also in CLAUDE.md (YouTube OAuth) and [[reference-auto-scrape]].

---

## ⚠️ Format: YouTube wants 16:9 widescreen (1920×1080)

Our reel renders are **vertical 9:16** (1080×1920) and some clips are odd ratios
(the StratBot screen-rec is 2.05:1). On YouTube:
- Vertical 9:16 → treated as a **Short** → NO end screens, different surface.
- **End screens & cards require 16:9 AND a video ≥25 seconds.** On a 12s/non-16:9 clip the
  "Add" buttons in Video elements are greyed out ("wrong format" on hover).
- For proper YouTube videos (end screens, better performance) render a **16:9 widescreen**
  version in Remotion. The vertical reels are fine as Shorts but won't take end screens.
- For end-screen-bearing videos, build the outro to be **end-screen-safe**: keep content in
  the left ~60% and out of the bottom-right, leave the final ~15-20s as a clean card, and
  BAKE the site CTA (stratbot.solvx.uk) into that outro — see the Link-element note below for
  why the end screen itself can't link out. `HermesWeek1` (1920×1080, 37s) is the template.

---

## Upload flow (standalone video)

```
1. studio.youtube.com → confirm channel = SolvX (see above).
2. Click Create:  document.querySelector('#create-icon').click()
   then the menu item "Upload videos".
3. File: trigger the hidden input — document.querySelector('input[type="file"]').click()
   then browser_file_upload with the ABSOLUTE path (must be UNDER the project dir; copy
   external media into socials-studio first — same sandbox as the other platforms).
   Upload + processing run in the BACKGROUND while you fill details.
4. Wizard has 4 steps (tabs, role="tab"):  Details → Video elements → Initial check → Visibility.
   The dialog element is `ytcp-uploads-dialog`; advance with its `#next-button`, go back by
   clicking the step tab. Final button is `#done-button` ("Save" until Public is picked,
   then "Publish").
```

### Step 1 — Details
All fields live inside `ytcp-uploads-dialog`:
- **Title** (required): `#title-textarea #textbox` (contenteditable). It's PREFILLED with the
  filename — click in, Ctrl+A, Delete, then type. Max 100 chars.
- **Description**: `#description-textarea #textbox` (contenteditable). fill() works.
- **Thumbnail**: `#thumbnail-uploader` (custom thumb needs a still ≤2MB; optional).
- **Playlists**: `ytcp-video-metadata-playlists`.
- **Audience (REQUIRED)**: `tp-yt-paper-radio-button` —
  `name="VIDEO_MADE_FOR_KIDS_NOT_MFK"` ("No, it's not Made for Kids") for our content.
  You cannot advance past Details without choosing this.
- **Age restriction**: `name="VIDEO_AGE_RESTRICTION_NONE"` (default fine).
- **"Show more"** (`#toggle-button`) reveals: tags, category, language, captions cert,
  recording date/location, licence, comments & ratings settings.

### Step 2 — Video elements (END SCREEN + cards) — VERIFIED 2026-06-17
- The "Add" buttons are **disabled** unless the video is **16:9 and ≥25s**. On a qualifying
  video they enable (confirmed: all greyed on the 12s StratBot clip, all enabled on the 37s
  16:9 round-up).
- Add an end screen:
  1. Click the **Add** button on the "Add an end screen" row. Robust selector: find the
     smallest element whose text matches /end screen/i AND contains a button, then click its
     `Add`. (Don't blind-index the Add buttons — there are ~10 on the step.)
  2. The **End Screens** editor opens (`ytve-endscreen-modal`). Pick a prebuilt template tile
     (e.g. one labelled "1 video, 1 subscribe") — click the tile. This drops a Subscribe
     element + a Video element ("Best for viewer") into the final ~17s.
  3. **`+ Element` menu** offers: Video, Playlist, Subscribe, Channel, **Link**.
     ⚠️ **"Link" is GREYED OUT** for this channel — external-link end-screen elements need
     YouTube Partner Program / an approved associated website. So you CANNOT link to
     stratbot.solvx.uk from the end screen. Drive the site via the baked-in outro + the
     description instead. (Re-check if the channel later joins YPP.)
  4. Click **Save** (`ytcp-button` text "Save" inside the End Screens modal). It returns to
     the wizard on the Video elements tab.
- ⚠️ **Overlay-intercept bug:** after saving the end screen, a leftover
  `div#touch-area` inside `ytve-endscreen-marker` intercepts pointer events, so a normal
  Playwright click on `#next-button` TIMES OUT ("subtree intercepts pointer events"). Fix:
  advance with a JS click — `document.querySelector('ytcp-uploads-dialog #next-button').click()`.
- Note: while editing you may see "End screen elements won't display on the watch page for
  private videos" — that's just informational; they show once the video is Public/Unlisted.

### Step 3 — Initial check
- Automated copyright/policy scan. Wait for "Checks complete. No issues found." Usually fast.
- Same overlay caveat can apply right after the end-screen step — prefer the JS
  `#next-button`.click() to advance through Initial check → Visibility.

### Step 4 — Visibility
- Radios `tp-yt-paper-radio-button` name = `PRIVATE` | `UNLISTED` | `PUBLIC`.
- "Schedule" option for a future public date/time.
- Click `#done-button` ("Publish" once Public selected, or "Save"/"Schedule").

### Verify
- Success dialog gives the share link `youtu.be/<id>`.
- Confirm on the Content page (`/videos/upload`): the top row shows the title, duration and
  visibility = Public.

---

## Notes / quirks
- Studio floods the console with errors — ignore.
- Upload sandbox: file must be under `D:\Documents\11Projects\socials-studio` (copy external
  renders in first — same as the other platforms).
- Title is PREFILLED from the filename (e.g. "hermes week1") — always clear (click → Ctrl+A →
  Delete) before typing the real title, or it concatenates.
- The video keeps processing (SD→HD) after publish; that's normal, the post is live. Publish
  is NOT blocked by processing as long as the visibility radio is set.
- After Publish, the success state exposes the share link `youtu.be/<id>` in body text; also
  verify on `/videos/upload` (top row shows title + duration + Public).
- The em-dash `—` types fine in the title/description boxes (they're contenteditable, not
  length-weighted like Twitter).
- Series/playlist "story" uploads are a separate flow — this skill is standalone only.

## Fixes/fails/omissions log (from the 2026-06-17 Week-1 publish)
- FIXED the prior omission: end-screen add flow is now fully documented & verified (Step 2).
- FAIL→workaround: `#next-button` click intercepted by the end-screen-marker overlay → use JS
  `.click()` (documented in Step 2/3).
- OMISSION found: end-screen **Link** to an external site is unavailable (no YPP) — the skill
  now says to bake the CTA into the outro + description rather than expecting an end-screen link.
- Confirmed audience radio `VIDEO_MADE_FOR_KIDS_NOT_MFK` and the 16:9-&-≥25s end-screen gate.
