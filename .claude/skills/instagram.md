# Skill: Post a reel to Instagram

Publishing runs through `auth/publish_instagram.py`, which drives a saved browser session.
**You do not drive the browser yourself.** Call the script.

```bash
python -m auth.publish_instagram path/to/video.mp4 --caption "your caption"
python -m auth.publish_instagram path/to/video.mp4 --caption "..." --dry-run
```

Video only — this posts reels. Requires `python -m auth.login_wizard --platform instagram`.

Instagram is the **most fragile** of the platforms. Everything below has actually happened,
repeatedly. Read it before posting, not after.

## Before you upload — check the video

**Aspect.** Reels are 9:16. A landscape source gets pillarboxed into a thin strip and looks bad.
Build a purpose-made vertical version instead — for a side-by-side comparison, stack the two panes
vertically rather than letterboxing them. Two rules learned the hard way when building these:

- Fit panes to **height** and centre them. Scaling to full width overflows 1920 and clips the bottom.
- **Never crop vertically on a full-figure shot** — it silently removes the subject of the post.

**Frame 0 becomes the cover.** If the video fades in from black, the reel's tile on the profile grid
is a black square. Measure it:

```bash
ffmpeg -i video.mp4 -vf "signalstats,metadata=print:file=-" -frames:v 1 -f null -
```

Read `YAVG`: **~7 = black**, trim the fade first (`ffmpeg -y -ss 1.2 -i in.mp4 -c copy out.mp4`);
**~12 or above = real content**, upload as-is. Measure the file you are actually uploading — in a
hero/spoke pair the two differ.

⚠️ **Never try to set a cover through "Select from computer"** — it fails silently, appearing to
work. Fix the source instead.

## ⚠️ The 1:1 crop bug — fires on essentially every upload

Instagram defaults the crop to **1:1**, squaring the frame and cutting the top and bottom off. Six
consecutive posts hit this, **including sources already at a true 1080×1920** — so it is not a
response to a landscape source, and "my video is already vertical" is not protection.

**Measuring the `<video>` element does not detect it.** In a real case the video measured 501×893 —
a clean 9:16 that passes any naive check — while the actual crop viewport, **five ancestors up**,
was 501×501. The depth varies (2, then 5, then 5 on consecutive posts), so a fixed-depth check
misses it. Walk the **whole ancestor chain** and measure the outermost crop container.

Fix: open "Select Crop" and choose 9:16 (or Original). After publishing, the served video should be
**720×1280** — if it is 720×720, it was cropped.

## ⚠️ The caption drop — dismiss the hashtag typeahead before Share

The caption shows perfectly in the composer, with the right character count, and the published post
has **no caption at all**.

Root cause, isolated across three trials in one quiet session: **the caption ends in hashtags, so
Instagram's hashtag autocomplete is still open when Share is clicked, and the commit is silently
swallowed.** Since every caption ends in hashtags, the typeahead is open at Share on essentially
every publish.

- Publish with the typeahead open → caption dropped.
- Repair with the typeahead open, using a scripted `.click()` → silently failed.
- Repair with the typeahead dismissed and a **real** click → worked immediately.

**Prevention:** click a neutral area of the dialog first, confirm the character counter still shows
the full caption, *then* Share. Cheap, and it removes the whole class of failure.

This was previously blamed on browser contention. That was wrong — it fires with nothing else
running. If the session is quiet, contention cannot be the cause.

## Verify after posting — at `/p/`, never `/reel/`

Reload the post and confirm the caption rendered.

⚠️ **Check `https://www.instagram.com/p/<code>/`.** The `/reel/<code>/` URL redirects into the reels
feed player, which renders **other accounts'** captions — so a check there returns a confident false
result either way.

Also confirm the served video is 720×1280, not 720×720.

## Caption

2,200 characters. Instagram doesn't linkify text, so point people at the bio rather than pasting a
URL. Hashtags at the end — and then dismiss the typeahead, per above.

Anything else: `post-troubleshooting.md`.
