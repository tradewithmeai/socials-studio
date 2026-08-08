# Skill: Post to LinkedIn

Publishing runs through `auth/publish_linkedin.py`, which drives a saved browser session.
**You do not drive the browser yourself.** Call the script.

```bash
python -m auth.publish_linkedin "post text"
python -m auth.publish_linkedin "post text" --image path/to/photo.jpg
python -m auth.publish_linkedin "post text" --video path/to/clip.mp4
python -m auth.publish_linkedin "post text" --dry-run
```

Requires a saved session: `python -m auth.login_wizard --platform linkedin`.

## What YOU are responsible for — the copy

**3,000 characters**, counted literally.

**LinkedIn renders markdown literally.** `**bold**` appears on the live post as
`**bold**`, asterisks and all. There is no formatting syntax — strip every `*` before posting.
Use line breaks and short paragraphs for emphasis instead. This catches people repeatedly, usually
when copy has been drafted somewhere that does support markdown.

**Register:** fuller paragraphs and a natural narrative rhythm. LinkedIn is the one platform where
the chopped-up one-line-per-thought style reads as ad copy and underperforms. Short lines are for
genuine emphasis, not as the default rhythm.

**Link preview cards:** a URL in the body auto-attaches a preview card. That card occupies the same
slot as media — so **if you want a video or image, the preview card has to go**, and the URL stays
clickable in the text either way. With media attached, expect no card at all; that is correct.

## Two hard constraints

**⚠️ A published LinkedIn post can NEVER have media added afterwards.** There is no edit path — only
a brand-new post. If text and media are meant to ship together, they must go in the *same* call. If
the media isn't ready and the text can't wait, either hold the whole post or accept it will be two
separate posts, and say so before publishing rather than discovering it after.

**⚠️ Don't navigate immediately after posting a large video.** With an upload still in flight,
navigating away fires a `beforeunload` dialog and the navigation hangs — which looks like a failed
post but isn't. Stay on the page, let the upload finish, confirm the composer has closed, *then*
verify. The post lands fine; early navigation is what breaks it.

## Verify after posting

Reload the activity feed and match on text **unique to this post**. The top item is not reliably
your newest, and near-identical posts have been mistaken for each other before. Confirm:

- every paragraph rendered, with the blank lines intact
- **zero asterisks**
- any numbers survived exactly
- media is attached and plays

## When it fails

- **Post button disabled** — media still processing. Wait; it is not an error.
- **Navigation hangs after posting** — the `beforeunload` case above. Decline the dialog and stay.
- **A native file dialog appears** — something clicked a file input instead of setting it. The
  script uses `set_input_files()` and never needs a picker.

Anything else: `post-troubleshooting.md`.
