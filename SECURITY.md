# Security Policy

## What this tool touches

This project drives a real Chrome browser (via Playwright) to log into and publish on social
platforms using **your own login session**, saved locally:

- Login sessions live in `profiles/<platform>/` on your machine only. This directory is
  gitignored and is never read, transmitted, or uploaded by this tool.
- There are no platform API keys or OAuth client credentials involved — the tool automates the
  normal web login/upload flow you'd use by hand.
- No telemetry, no analytics, no network calls other than the platform sites themselves.

If you're auditing this before running it: `auth/login_wizard.py` and `auth/publish_youtube.py`
are the only two entry points that touch a browser or the filesystem outside your project
directory. Read those two files first.

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
- `profiles/` directories contain live session cookies. Treat that directory like a password
  manager vault — don't sync it anywhere untrusted, don't commit it (it's gitignored by default,
  keep it that way).
