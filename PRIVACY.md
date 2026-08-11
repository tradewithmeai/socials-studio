# Privacy Policy

Socials Studio is a local command-line tool. There is no server, no account system, and no
hosted service operated by this project -- everything described below happens on your own
machine, using your own credentials, for your own accounts.

## What is stored, and where

| Data | Location | Purpose |
|---|---|---|
| Browser session (cookies, local storage) for Bluesky, LinkedIn, Instagram | `profiles/<platform>/` in this repository's working directory | Lets a later publish command reuse a session you already logged into by hand, instead of asking you to log in every time |
| YouTube OAuth token (access token + refresh token) | `profiles/youtube/token.json` | Authorizes API calls to upload/manage video on your behalf, per the scopes described below |
| Google Cloud OAuth client secret (the file you download when setting up YouTube) | Wherever you choose to save it -- the default path this tool looks for is `profiles/youtube/client_secret.json`, but `--client-secrets <path>` can point anywhere | Identifies *your* Google Cloud project to Google during the one-time OAuth setup step; not itself a per-user credential, but should still be treated as sensitive |

`profiles/` is excluded from version control by `.gitignore`. `python doctor.py` includes a check
that confirms nothing under `profiles/` has been accidentally committed.

## What this tool does NOT do

- It does not send any of the above to this project's maintainer, or to any server this project
  operates -- there is no such server.
- It does not include telemetry or usage analytics (see [SECURITY.md](SECURITY.md) for the exact
  scope of that claim).
- It does not share your credentials with any third party beyond the platform each credential is
  *for* (your Bluesky session only ever talks to Bluesky; your YouTube token only ever talks to
  Google's YouTube Data API).

## Third-party services this tool talks to

- **The platform you're publishing to** (Bluesky, LinkedIn, Instagram, YouTube) -- necessarily, to
  do the thing you asked it to do. Each platform has its own privacy policy governing what they do
  with your account and activity; this tool doesn't change or extend that in any way.
- **Google**, specifically for YouTube: the OAuth consent flow and the YouTube Data API calls this
  tool makes are covered by
  [Google's Privacy Policy](https://policies.google.com/privacy) and the
  [YouTube API Services Terms of Service](https://developers.google.com/youtube/terms/api-services-terms-of-service).
  By using the YouTube publishing feature, you're also subject to those terms as an end user of a
  third-party API Client (this tool).
- **Playwright / Chrome for Testing**, when `playwright install chrome` fetches a browser build.
  This is a one-time (or occasional) download managed by Playwright itself, not by this project's
  code.

## OAuth scopes requested for YouTube

This tool requests only the scopes its own code demonstrably uses:

- `https://www.googleapis.com/auth/youtube.upload` -- required to publish a video.
- `https://www.googleapis.com/auth/youtube.readonly` -- required by `python doctor.py` to confirm
  which channel your token is authorized for, so you can catch a wrong-account authorization
  before it causes a confusing upload failure.

An earlier version of this tool also requested the broad
`https://www.googleapis.com/auth/youtube` scope, which grants read/write access to playlists,
comments, and other channel management this tool's code never uses. That scope has been dropped.
**If you authorized this tool before that change, you need to re-authorize**: delete
`profiles/youtube/token.json` and re-run `python -m auth.setup_youtube_oauth`. A token issued
under the old scope set will fail to refresh with a "scope has changed" error rather than
silently continue working under the new, narrower scopes.

## Retention and deletion

Every credential this tool stores lives entirely under `profiles/` in your own local working
directory, for as long as that directory exists on your machine. There is no remote copy anywhere
this project controls.

To remove a credential:

- **A platform's browser session**: delete `profiles/<platform>/` (e.g. `profiles/bluesky/`).
  Re-run `python -m auth.login_wizard --platform <platform>` to create a new one when you next
  need it.
- **The YouTube OAuth token**: delete `profiles/youtube/token.json`. This does not revoke the
  authorization on Google's side by itself -- to fully revoke it, also visit
  [Google Account permissions](https://myaccount.google.com/permissions) and remove this
  application's access there.
- **Everything**: delete the entire `profiles/` directory. Every publisher will report "no saved
  session" / "no saved token" until you reconnect each platform you still want to use.

## Changes to this policy

This is a beta project under active development. If the scopes requested, the data stored, or the
third-party services contacted change in a future release, this file will be updated alongside
that change, and [CHANGELOG.md](CHANGELOG.md) will call out anything that requires you to take
action (like the scope change above).

## Questions or concerns

Open an issue, or see [SECURITY.md](SECURITY.md) if what you've found is a genuine security
vulnerability rather than a privacy question.
