# Skill: Post to X (Twitter)

Publishing runs through `auth/publish_x.py`, which drives a saved browser session.
**You do not drive the browser yourself.** Call the script.

```bash
python -m auth.publish_x "post text"
python -m auth.publish_x "post text" --image path/to/photo.jpg --alt-text "description"
python -m auth.publish_x "post text" --video path/to/clip.mp4
python -m auth.publish_x "post text" --dry-run      # validate, no browser, nothing posted
```

Requires a saved session: `python -m auth.login_wizard --platform x`. If `profiles/x/` is
missing the script stops and tells you. Always `--dry-run` first when unsure.

## What the script already handles — don't reimplement it

- **Attaching media.** It uses `set_input_files()`, which hands the file straight to the page.
  ⚠️ **Never click a file input or an "Add media" button to open a picker.** That opens the real
  native OS file dialog, which sits outside the browser, blocks every subsequent action, and takes
  the whole run down with it. If you see a Windows "Open" dialog appear, that is the bug.
- **Waiting for video processing** before clicking Post.
- **The alt-text reminder.** X blocks the submit with an accessibility prompt when an image has no
  description. The script fills it in, defaulting to the post text if you didn't pass `--alt-text`.
  Pass a real description when the image carries meaning the text doesn't.
- **Detecting a failed submit** by checking it actually left the compose page.

## What YOU are responsible for — the copy

**280 characters, weighted.** Not a plain character count:

- Any URL counts as **23**, whatever its real length.
- Most characters count 1, but anything outside four narrow ranges counts **2** — an em dash `—`
  is 1, an arrow `→` is 2, and every emoji is 2.
- Newlines count 1.

Count it properly before posting; a two-character drift matters at 274/280.

**Never open a post with `@handle`.** X classifies it as a *reply*: it skips the Posts tab and only
reaches people who follow both accounts. Reorder the sentence or accept the reach penalty. This has
cost a post its whole audience before.

**One link per post.** A second URL hijacks the unfurl card — you get the site favicon instead of
the video or article preview.

**Hashtags:** lead with the campaign tag, plus one or two naming real brands or models. Inline
mentions of real products (`@OpenAI`, not "ChatGPT") reach further.

## Verify after posting

The script does **not** return the post's URL — it says so in its own output. Open the profile and
confirm the post is there, with the media attached and the text intact. If you are unsure whether a
post went out, **check the profile before retrying**; a duplicate is worse than a delay.

## When it fails

- **Post button never enables** — usually over the character limit, or video still processing.
- **Still on the compose page afterwards** — the submit did not go through. Check for a blocking
  dialog. Do not blindly retry: look first.
- **A native file dialog appears** — something clicked a file input. See above.

Anything not listed here: `post-troubleshooting.md`.
