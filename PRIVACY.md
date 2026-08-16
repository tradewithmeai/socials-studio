# Privacy Policy

Socials Studio is a local-first application, operated through Claude Code, with a Python
command-line layer underneath that does the actual authentication and publishing work. There is
no server, no account system, and no hosted service operated by this project -- everything
described below happens on your own machine, using your own credentials, for your own accounts.

## Claude Code is a separate service

This policy describes what **Socials Studio's own code** stores and does. If you operate this
repository through Claude Code, that's a separate, third-party service with its own
configuration, data handling, and privacy terms -- not something this project controls, audits,
or extends, and not something this document makes any claim about. Anything you provide to Claude
Code while operating this repository (files, conversation content, or otherwise) is governed by
Claude Code's own terms, not by this document. Review those separately at
[claude.com/claude-code](https://claude.com/claude-code) -- this project does not speculate about
what they say.

What *is* covered by this policy, regardless of which agent (or no agent at all) you use to drive
it: the platform session files and OAuth tokens under `profiles/`, described below. This
project's own instructions to any agent operating here are explicit that `profiles/` must never
be read, printed, or otherwise surfaced -- see `CLAUDE.md` and `AGENTS.md` in this repository. Calling
Socials Studio "local-first" is a claim about that data and about this project's own publishing
execution, not a claim that every part of using Claude Code to operate it is confined to your
machine.

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
- **This project's own code** does not direct your credentials to any destination beyond the
  platform each credential is *for* -- the code that reads a Bluesky session only ever navigates
  it to bsky.app; the code that reads the YouTube token only ever calls Google's YouTube Data API.

This is a claim about *this project's own code*, not about the software it runs on top of.
Bluesky/LinkedIn/Instagram publishing uses a real Chrome browser, driven by Playwright -- both are
third-party software this project does not control, audit, or modify. A real Chrome instance can
make its own network calls this project's code never initiates or sees: update checks, Safe
Browsing lookups, telemetry Google Chrome itself collects, DNS resolution, and so on. Playwright
similarly has its own update-check and browser-management behavior. None of that is inspected or
disclosed here because it isn't this project's code -- see each project's own documentation
(Chrome's privacy policy, Playwright's) if that level of detail matters to you.

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
