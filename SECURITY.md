# Security Policy

## What this tool touches

Socials Studio uses two different authentication mechanisms, not one:

- **Bluesky, LinkedIn, Instagram** use a saved **browser session** created by
  `auth/login_wizard.py`. You log in by hand in a plain, non-automated Chrome window; the
  resulting session (cookies, local storage) is saved under `profiles/<platform>/` and replayed by
  Playwright for later publishing. `auth/publish_bluesky.py`, `auth/publish_linkedin.py`, and
  `auth/publish_instagram.py` are the modules that drive a browser using these sessions.
- **YouTube** uses **OAuth 2.0 + the official YouTube Data API** (`auth/setup_youtube_oauth.py`,
  `auth/publish_youtube.py`) -- no browser automation at all for this platform. This requires
  **your own Google Cloud OAuth client**: you create a Google Cloud project, enable the YouTube
  Data API, and download a client secret JSON file yourself (the `onboard-youtube` skill walks
  through this). The resulting OAuth token is saved to `profiles/youtube/token.json`.

Both browser session data and the YouTube OAuth token are credentials in every sense that
matters -- anyone with access to `profiles/<platform>/` or `profiles/youtube/token.json` can act as
you on that platform without needing your password again.

### Where things are stored

- `profiles/<platform>/` (browser sessions) and `profiles/youtube/token.json` (OAuth token) --
  all under this repository's own `profiles/` directory, on your machine, nowhere else. This
  directory is gitignored; `python doctor.py` checks that it hasn't been accidentally committed.
- The Google Cloud OAuth **client secret** JSON you download during YouTube setup is not written
  anywhere by this tool automatically -- you choose where to save it (the default location the
  scripts look for is `profiles/youtube/client_secret.json`, but you can pass `--client-secrets`
  to point at any path).
- Nothing here is uploaded, synced, or transmitted to any server this project controls, because
  this project doesn't operate one -- there is no backend, no hosted service. Every credential
  stays on the machine you run this on.

### Which modules touch a browser, the filesystem, or an external service

Based on reading this codebase (last reviewed alongside this file's rewrite for v0.1.0-beta.2):

| Module | Touches |
|---|---|
| `auth/login_wizard.py` | A real, human-driven Chrome process (login step) and Playwright-driven Chrome (verification step); reads/writes `profiles/<platform>/` |
| `auth/publish_bluesky.py`, `auth/publish_linkedin.py`, `auth/publish_instagram.py` | Playwright-driven Chrome against the saved session; reads whatever media file path you pass in; contacts that platform's website |
| `auth/publish_x.py` | Same shape as the above three -- present in the codebase and functional, but not advertised as a supported platform in this release (see CHANGELOG.md) |
| `auth/setup_youtube_oauth.py` | Opens a plain browser to Google's real OAuth consent screen (not automated); reads the client secret JSON you point it at; writes `profiles/youtube/token.json` |
| `auth/publish_youtube.py` | Calls the YouTube Data API over HTTPS via `google-api-python-client`; reads `profiles/youtube/token.json` and the video file path you pass in |
| `auth/chrome_setup.py` | Runs `playwright install chrome` (downloads a Chrome build over the network the first time) and locates your system Chrome install |
| `doctor.py` | Reads `profiles/` to report connection status; calls the YouTube Data API (read-only) to verify which channel a token belongs to; runs local subprocesses (`git`, and on Windows, `powershell` to check for stale Chrome processes) |

### Telemetry

No telemetry and no analytics are implemented anywhere in this codebase -- there is no code path
that reports usage, errors, or any other data back to the maintainer or any third party this
project controls. This claim is about code *this project* wrote; it does not extend to the
third-party libraries it depends on (Playwright, `google-api-python-client`,
`google-auth-oauthlib`, etc.), which are not audited here and may have their own data practices --
see their own documentation if that matters to you.

Network activity this tool *does* generate, beyond the platform sites/APIs described above, and
Chrome's own installer:

- `playwright install chrome` and Playwright/Chrome's own update-check behavior are governed by
  Playwright and Google, not this project.
- Nothing else. If you find a network call this document doesn't account for, that's exactly the
  kind of thing to report below.

### Browser automation risk (not a code vulnerability, but a real risk)

Automating a real browser session against Bluesky, LinkedIn, or Instagram carries risks beyond
this codebase's own security:

- **Account risk.** These platforms actively look for automation signals. This project's design
  (a plain, human-driven login step, never automated) specifically avoids the failure modes that
  are known to get accounts flagged, but no third-party platform's anti-automation policy is
  something this project controls or can guarantee against.
- **Reliability risk.** Browser selectors are best-effort against live, frequently-changing UIs
  (see each platform's notes in `.claude/skills/`). A platform UI change can break a publisher
  without warning; that's a reliability problem, not a security one, but it means "silently posted
  something malformed" is a more realistic failure mode than for a stable API integration.
- **Platform-policy risk.** Using unofficial browser automation against a platform's own terms of
  service is a decision you're making about your own account, not something this project can
  absolve. YouTube uses the official Data API specifically because Google blocks the alternative
  outright; the other platforms don't currently offer an equivalent third-party publishing API, so
  browser automation via your own already-authenticated session is the approach this project
  takes instead.

## Reporting a vulnerability

If you find a security issue — anything from "this could leak a session token" to "this file-path
handling looks exploitable" — please report it privately rather than opening a public issue:

1. Open a [private security advisory](../../security/advisories/new) on this repository, or
2. If that's not available to you, open an issue with minimal detail and a note asking for a
   private channel — we'll follow up.

Please include:
- What you found and where (file/line if you have it)
- Steps to reproduce, if applicable
- What you'd expect to happen instead

We'll acknowledge reports as quickly as we can given this is an early-stage beta maintained by one
person. There's no bug bounty — but real reports get real fixes and credit if you want it.

## Known-risk areas (beta)

- Browser automation selectors are best-effort against live platform UIs (see each platform's
  notes in the skill docs) and can be brittle across platform UI changes. That's a reliability
  risk, not a security one, but worth knowing before you point this at a production account.
- `profiles/` directories contain live session cookies and, for YouTube, an OAuth token. Treat
  that directory like a password manager vault — don't sync it anywhere untrusted, don't commit it
  (it's gitignored by default, keep it that way; `python doctor.py` checks this for you).

See also [PRIVACY.md](PRIVACY.md) for what's stored, for how long, and how to remove it.
