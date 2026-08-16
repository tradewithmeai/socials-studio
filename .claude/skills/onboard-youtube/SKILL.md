---
name: onboard-youtube
description: Set up YouTube publishing for Socials Studio from scratch (OAuth setup through a verified first publish). Use when the user wants to connect, set up, or onboard YouTube, or a YouTube publish fails because no token exists yet.
---

# YouTube onboarding

## When to use it

Connecting YouTube for the first time, or a publish fails because no token exists yet. Not for
routine publishing once connected (`publish-youtube`) or diagnosing a failed publish
(`troubleshoot-publishing`).

## Instructions

1. One-time Google Cloud setup (the user does this themselves, in their own browser):
   - Create a project at https://console.cloud.google.com/, logged into the account that owns the
     target YouTube channel.
   - Enable "YouTube Data API v3" (APIs & Services -> Library).
   - APIs & Services -> OAuth consent screen -> External -> fill in the minimal required fields,
     then **publish the app** (move it out of Testing) -- leaving it in Testing blocks the flow.
   - Create Credentials -> OAuth client ID -> Application type **Desktop app** (required: the
     redirect URI needs to be `http://localhost`).
   - Download the client secret JSON and save it as `profiles/youtube/client_secret.json` (or pass
     `--client-secrets <path>`).
2. Run setup:
   ```bash
   python -m auth.setup_youtube_oauth
   ```
   Opens a real, non-automated browser to Google's consent screen. The user approves it themselves.
   Writes `profiles/youtube/token.json` on success. Only `youtube.upload` and `youtube.readonly`
   scopes are requested -- see [PRIVACY.md](../../../PRIVACY.md).
3. Verify before a real publish:
   ```bash
   python -m auth.publish_youtube <video.mp4> --title "..." --dry-run
   ```
   Check for `"token_found": true`.
4. First real publish -- requires `--confirm-publish`, exactly one of `--made-for-kids` /
   `--not-made-for-kids`, and `--acknowledge-upload-terms`:
   ```bash
   python -m auth.publish_youtube <video.mp4> --title "..." --description "..." --tags "a,b,c" \
       --visibility private --not-made-for-kids --acknowledge-upload-terms --confirm-publish
   ```
   Defaults to `--visibility private` if omitted; only pass `--visibility public` once the user has
   explicitly confirmed they want it live.
5. Verify: read the video back with `videos.list`, check the public oEmbed endpoint
   (`https://www.youtube.com/oembed?url=...&format=json`), and to delete a test upload:
   ```python
   from auth.publish_youtube import _load_credentials
   from googleapiclient.discovery import build
   creds = _load_credentials()
   build("youtube", "v3", credentials=creds).videos().delete(id="<VIDEO_ID>").execute()
   ```
   Confirm deletion both via `videos().list` (0 items) and the oEmbed check (404).

## Guardrails

- Never fill in Google credentials programmatically -- the consent screen is always completed by
  the user, in a real, non-automated browser window.
- The upload notice (`auth.publish_youtube.UPLOAD_TERMS_NOTICE`) prints unconditionally on every
  real-upload attempt. Actually show it to the user and get their real answer on Made for Kids --
  don't just add flags to satisfy the CLI.
- `--confirm-publish` is required for a real upload; without it, this only validates.

## Known failures and recovery

- **OAuth consent flow fails / "access blocked"**: consent screen still in Testing mode -- publish
  the app in Cloud Console. (Testing mode also expires refresh tokens after 7 days.)
- **Upload fails with `401 youtubeSignupRequired`**: authorized as the wrong Google account (the
  Cloud project owner instead of the channel owner). Verify first with
  `youtube.channels().list(part="id,snippet", mine=True).execute()` -- exactly 1 item, your
  channel, is correct; 0 items means delete the token and re-authorize as the channel owner.
  `python doctor.py --youtube` runs this check.
- **Token exists but API calls fail with a scope error**: token was issued under different scopes.
  Delete `profiles/youtube/token.json` and re-run setup.
- Category is hardcoded to `22` (People & Blogs); tags intermittently don't persist (verify after
  upload, re-apply with `videos.update` if missing); no thumbnail support (needs a separate
  `thumbnails().set()` call).
