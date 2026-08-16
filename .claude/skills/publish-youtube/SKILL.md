---
name: publish-youtube
description: Prepare, validate, review and publish a video to an already-authorized YouTube channel. Use when the user wants to draft, review or upload a YouTube video -- not for first-time OAuth setup (see onboard-youtube) and not for diagnosing a failed/uncertain publish (see troubleshoot-publishing).
---

# Publish to YouTube

YouTube is **not browser automation**. It uses OAuth and the official Data API — deliberately, and
permanently. Google actively blocks sign-in from automation-controlled browsers ("This browser or
app may not be secure"), so there is no browser path to fix or fall back to.

This also makes it the most reliable publisher: no shared browser, no tab contention, no session
expiry beyond the token.

```bash
python -m auth.publish_youtube path/to/video.mp4 \
    --title "..." --description "..." --tags "a,b,c" --visibility public \
    --not-made-for-kids --acknowledge-upload-terms --confirm-publish

python -m auth.publish_youtube path/to/video.mp4 --title "..."   # validates only -- the default
```

Safe by default: the second form validates only. A real upload additionally requires exactly one
of `--made-for-kids` / `--not-made-for-kids` (mutually exclusive -- argparse itself rejects both
together, and neither is inferred or defaulted) and `--acknowledge-upload-terms` -- both required
by the YouTube API Services Terms of Service, Section 9.1, and enforced in code (not just
documented). The required upload notice prints **unconditionally** on every real-upload attempt,
even if `--acknowledge-upload-terms` is already set -- it's never just a flag that suppresses a
notice nobody saw. Actually show it to the user and get their real answer on Made for Kids before
passing either flag.

Requires `python -m auth.setup_youtube_oauth` to have been run, producing
`profiles/youtube/token.json`.

⚠️ **`--visibility` defaults to `private`.** Pass `--visibility public` explicitly to go live —
this is a deliberate safety default, not an oversight. Check it before you assume a video published.

## ⚠️ The two-account trap — the expensive one

Two Google accounts are usually involved, and they are often not the same:

- the account that owns the **Google Cloud project** (the OAuth app), and
- the account that owns the **YouTube channel** you publish to.

**You must authorise as the account that owns the channel.** Authorise as the app owner and
everything looks fine — the token is created, reading stats works — and then upload fails with
`401 youtubeSignupRequired`. That error never mentions accounts. It means "this account has no
YouTube channel."

**Verify before relying on the token**, rather than finding out at upload time:

```python
youtube.channels().list(part="id,snippet", mine=True).execute()
```

Exactly **1 item, and it's your channel** = correct. **0 items** = wrong account; delete the token
and re-authorise. `py doctor.py --youtube` runs this check for you and names the channel back.

## ⚠️ Publish the OAuth app, don't leave it in Testing

While the app is in *Testing*, Google expires **refresh tokens after 7 days**. Everything works,
then a week later uploads fail for no visible reason and it looks like the code broke. Publish the
app in the Cloud Console consent screen and the token persists.

## Title and description rules

**The title limit is 100 characters, and it is a hard API limit** — an over-length title is rejected
outright, not truncated. Count it *before* presenting a title for approval; a 102-character title
has cost a round trip. When trimming, prefer cutting a connective ("Plus") over a hedge
("Reportedly") — dropping a hedge changes what the title claims is true.

Lead with the single most surprising, specific fact in the first ~55 characters. Pack in named
entities and numbers — that is what search rewards.

**No `<` or `>` characters** anywhere in title or description; the API rejects them.

## Known defects in the upload path

- **Category is hardcoded to `22` (People & Blogs)** in `publish_youtube.py`, with no override. Any
  other category — 28 for Science & Technology, 20 for Gaming — needs the `categoryId` set on the
  insert call directly.
- **Tags intermittently do not persist.** They appear in the `videos.insert` response and are
  missing from the next `videos.list` read. Not deterministic — seen on some uploads, not others.
  **Always verify tags after upload** and re-apply with `videos.update` if missing (carrying title,
  description and categoryId forward so nothing is blanked).
- **No thumbnail support** in the script. A custom thumbnail needs a separate `thumbnails().set()`
  call after upload.
- Run with `PYTHONIOENCODING=utf-8` when printing video metadata — titles containing emoji crash on
  cp1252, and a crash *after* insert leaves a live video with no verification output.

## Verify after upload

Read the video back with `videos.list` and confirm title, description, tags, category and privacy
all actually stuck. Do not trust the insert response alone — see the tags defect above.

If a publish fails, looks uncertain, or you suspect a duplicate, use the `troubleshoot-publishing`
skill rather than retrying blind.
