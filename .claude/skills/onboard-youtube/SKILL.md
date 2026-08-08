---
name: onboard-youtube
description: Set up YouTube publishing for Socials Studio from scratch (OAuth setup through a verified first publish). Use when the user wants to connect, set up, or onboard YouTube, or a YouTube publish fails because no token exists yet.
---

# YouTube onboarding

Confirmed working end-to-end on a real account (2026-08-06): OAuth setup, dry-run, a real
publish with title/description/tags at public visibility, live verification via the API and a
public oEmbed check, and deletion verified two ways. This skill is the known-working method --
follow it, don't improvise a different one.

## Use OAuth, never browser automation, for YouTube/Google login

YouTube auth goes through Google's own sanctioned OAuth flow (`auth/setup_youtube_oauth.py`), not
`auth/login_wizard.py` or any other browser automation. Confirmed live: Google actively detects and
blocks sign-in attempts from automation-controlled browsers with **"This browser or app may not be
secure,"** even with Playwright's real-Chrome channel (not bundled Chromium) -- this is a deliberate
Google defense, not a stale-selector bug, and it is why YouTube auth works completely differently
from TikTok/Instagram/X in this repo. Let the user complete the OAuth consent screen themselves in
a real, non-automated browser window; never fill in Google credentials programmatically. Always run
the dry-run step before a real publish.

## The known-working method: OAuth + YouTube Data API

YouTube publishing goes through `auth/setup_youtube_oauth.py` (one-time) then
`auth/publish_youtube.py` (every publish) -- no browser automation involved at all, this is
Google's own sanctioned integration path for third-party apps.

### One-time setup (the user must do this themselves in their own browser)

1. Go to https://console.cloud.google.com/ logged into the Google account that owns the target
   YouTube channel.
2. Create a new project (any name).
3. **APIs & Services -> Library** -> search "YouTube Data API v3" -> **Enable**.
4. **APIs & Services -> OAuth consent screen** -> choose **External** -> fill in the minimal
   required fields (app name, your email).
5. ⚠️ **CRITICAL, confirmed the hard way**: leaving the consent screen in **Testing** mode blocked
   the OAuth flow from completing. **Publish the app** (move it out of Testing into Production) --
   this is what actually made it work. Don't assume "add yourself as a test user" is sufficient;
   publishing is the verified fix.
6. **APIs & Services -> Credentials -> Create Credentials -> OAuth client ID** -> Application
   type: **Desktop app**. (Must be Desktop app -- the redirect URI needs to be `http://localhost`,
   which is what `InstalledAppFlow.run_local_server` expects.)
7. Download the resulting client secret JSON.
8. Save it as `profiles/youtube/client_secret.json` in this repo (or anywhere, and pass
   `--client-secrets <path>` in the next step).

### Run the setup

```bash
python -m auth.setup_youtube_oauth
```

This opens a **real, non-automated** browser window to Google's actual consent screen -- the user
clicks through and approves it themselves, same as installing any app that wants YouTube access.
On success it writes `profiles/youtube/token.json` (gitignored, never commit it).

### Verify before a real publish

```bash
python -m auth.publish_youtube <video.mp4> --title "..." --dry-run
```

Check the JSON output: `"token_found": true` and no error. This makes no API call and uploads
nothing -- safe to run freely.

### First real publish

```bash
python -m auth.publish_youtube <video.mp4> --title "..." --description "..." --tags "a,b,c" --visibility private
```

Defaults to `--visibility private` if omitted. Only pass `--visibility public` once the user has
explicitly confirmed they want it live.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `UnicodeDecodeError` in a background thread, mentions `cp1252` | A subprocess call captured text output without specifying an encoding, and Windows' default codepage can't decode Playwright's Unicode box-drawing output | Already fixed in `auth/chrome_setup.py` (`encoding="utf-8", errors="replace"`). If it recurs in a new subprocess call on Windows, add the same. |
| `UnicodeEncodeError` printing search/API results, mentions an emoji like `\U0001f534` | Windows console (cp1252) can't print raw Unicode/emoji from API response text | Don't print raw API text directly in a Windows console script; strip non-ASCII or set `PYTHONIOENCODING=utf-8` first. |
| OAuth consent flow fails / "access blocked" | Consent screen still in Testing mode | Publish the app in Google Cloud Console -> OAuth consent screen (see step 5 above). |
| Token exists but API calls fail with a scope error | Token was issued for different scopes than `auth.publish_youtube.SCOPES` | Re-run `python -m auth.setup_youtube_oauth` to get a fresh token with the current scopes. |
| `No saved YouTube token found` | `profiles/youtube/token.json` doesn't exist | Run the one-time setup above first. |

## Cleaning up a test video

Not a built CLI feature (deliberately -- deletion is destructive and shouldn't be one flag away
from a normal publish). To delete a test upload during verification:

```python
from auth.publish_youtube import _load_credentials
from googleapiclient.discovery import build

creds = _load_credentials()
yt = build("youtube", "v3", credentials=creds)
yt.videos().delete(id="<VIDEO_ID>").execute()
```

Verify deletion actually took effect both ways -- via the API (`videos().list` returns 0 items)
and via the public check (`https://www.youtube.com/oembed?url=...&format=json` returns 404) --
don't trust a 200 response from `delete()` alone as proof.
