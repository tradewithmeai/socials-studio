# Socials Studio

**Publish your OpenMontage videos**

OpenMontage creates the video. Socials Studio handles the next stage: review, authentication and
publication.

> Socials Studio is an independent community project. It is not affiliated with, maintained by or
> endorsed by OpenMontage.

**Public beta — v0.1.0-beta.2.** Publish videos and posts to YouTube, Bluesky, LinkedIn and
Instagram -- see [Testing status](#testing-status) below before you point this at a real account.
X (Twitter) is not presented as a supported platform in this release -- see
[CHANGELOG.md](CHANGELOG.md) for why.

> **This beta is built and tested with [Claude Code](https://claude.com/claude-code)** -- it's the
> only coding agent this has been validated with so far (see
> [Testing status](#testing-status)). Using Claude Code? Have it read [AGENTS.md](AGENTS.md)
> first -- it's a guided tour built for agents, not humans. Everything here also works driven by
> hand, with no agent at all.

---

## What this is

[OpenMontage](https://github.com/calesthio/OpenMontage) is an open-source AI video production
pipeline. Socials Studio is an independent companion workflow for OpenMontage users: it accepts
finished video output, helps you review the publishing details, and publishes the video to
YouTube, Bluesky, LinkedIn and Instagram.

This is file-based compatibility, not a technical integration -- Socials Studio has no dependency
on OpenMontage's code and doesn't call into it. It works with a finished video file from
OpenMontage exactly the same way it would work with a finished video file from anywhere else.

## How it works

1. **Create** -- Render or export your finished video from OpenMontage (or any other source).
2. **Review** -- Point Socials Studio at the file and set the title, description, and visibility.
   Every publisher validates by default and touches nothing until you explicitly confirm -- see
   [Publishing safety](#publishing-safety) below.
3. **Publish** -- Authenticate once, then publish to YouTube, Bluesky, LinkedIn or Instagram.
   Uploads default to private/draft where supported so you can review the live result yourself
   before making it public.

```
OpenMontage export -> Socials Studio review -> publish to YouTube, Bluesky, LinkedIn or Instagram
```

If you're using Claude Code and the video came from OpenMontage, point it at the
`openmontage-context` skill before asking it to write your caption or description -- OpenMontage's
own pipeline writes out the video's script, intended tone, and target audience as plain JSON next
to the render, so copy can be grounded in what the video actually says instead of guessed from the
filename.

## Supported platforms

Publish videos and posts to YouTube, Bluesky, LinkedIn and Instagram.

| Platform | How it authenticates | Publish | Notes |
|---|---|---|---|
| YouTube | OAuth + Data API | Yes | No browser at all. Google blocks automated sign-in, so this is the official API path. Needs your own Google Cloud OAuth client -- see setup below |
| Bluesky | Saved browser session | Yes | Text, image or video |
| LinkedIn | Saved browser session | Yes | Text, image or video. Media can never be added to a post after publishing |
| Instagram | Saved browser session | Yes | Reels (video) |

`python doctor.py` checks all of the above and tells you what is missing.

See [ROADMAP.md](ROADMAP.md) for what's next.

## Publishing safety

Every publisher in this repo -- the library function *and* its CLI wrapper -- validates only and
touches no browser, no API, and no network call to a platform **unless you explicitly confirm**:

```bash
python -m auth.publish_bluesky "post text" --confirm-publish      # actually posts
python -m auth.publish_bluesky "post text"                        # validates only (the default)
python -m auth.publish_bluesky "post text" --dry-run               # validates only (explicit)
```

`--confirm-publish` (CLI) / `confirm_publish=True` (library call) is required to actually publish
anything. `--dry-run` / `dry_run=True` always wins if both are passed, so there's no way to
accidentally force a real publish through code that still passes `dry_run=True` out of habit.
Every result includes a `"dry_run"` field and a plain-language `"message"` stating whether
anything was actually published.

YouTube additionally requires exactly one of `--made-for-kids` / `--not-made-for-kids` and
`--acknowledge-upload-terms` for a real upload -- see
[YouTube-specific requirements](#youtube-specific-requirements) below.

## Testing status

This beta has been **developed with Claude Code**. Publishing has been tested for YouTube,
Bluesky, LinkedIn and Instagram, including with OpenMontage-rendered video.

This is exactly what the beta is for. If you run this against a real account -- with OpenMontage
output or anything else -- please [file a beta test report](#reporting-problems--requesting-features)
either way, pass or fail, both are useful. Other coding agents, operating systems, and
configurations haven't been validated at all yet; reports on those are especially welcome.

## Install

```bash
git clone https://github.com/tradewithmeai/socials-studio.git
cd socials-studio
```

Create and activate a virtual environment first -- this keeps the project's dependencies isolated
from anything else on your machine:

```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

Then install:

```bash
pip install -r requirements.txt
python -m playwright install chrome
```

Playwright drives a real Chrome build here (not bundled Chromium) -- social platforms flag
automation fingerprints more readily on Chromium, so this uses the same Chrome you'd log into by
hand. `playwright install chrome` is idempotent; safe to re-run. It also fetches/verifies a real
Chrome browser build (a few hundred MB) -- know that before running it.

Supported Python versions: 3.10 through 3.13 (matching what this project's dependencies actually
require and what's been tested in CI -- see [.github/workflows](.github/workflows)).

If you're contributing or running the test suite, also install the development dependencies:

```bash
pip install -r requirements-dev.txt
```

## Setup and authentication

**YouTube is different from the rest** -- it uses the official Data API, not a browser at all.
Google blocks automated browser sign-in outright, so OAuth is the only supported path. See the
`onboard-youtube` skill, or run:

```bash
python -m auth.setup_youtube_oauth
```

(one-time; requires your own Google Cloud OAuth client -- the skill walks through creating one).
This tool requests only the minimum OAuth scopes publishing and `python doctor.py` demonstrably
need (`youtube.upload` and `youtube.readonly` -- see [PRIVACY.md](PRIVACY.md)). If a future version
changes the requested scopes, a token issued under the old ones will fail on refresh with a "scope
has changed" error rather than silently keep working -- delete `profiles/youtube/token.json` and
re-run setup if that happens.

For **Bluesky, LinkedIn and Instagram**, log into each platform once. A real Chrome window opens
to that platform's login page -- log in yourself, same as you normally would:

```bash
python -m auth.login_wizard --platform bluesky
```

The session is saved to `profiles/<platform>/` on your machine only. It's gitignored, never
transmitted anywhere, and never read by anything except your own later publish commands. List
supported platform keys anytime:

```bash
python -m auth.login_wizard --list
```

## Example usage

**Validate first -- this is also the default with no flags at all:**

```bash
python -m auth.publish_youtube render.mp4 --title "My video" --dry-run
```

**Real publish, private by default:**

```bash
python -m auth.publish_youtube render.mp4 --title "My video" --description "..." \
    --visibility private --not-made-for-kids --acknowledge-upload-terms --confirm-publish
```

Pass `--visibility public` explicitly to go live immediately; otherwise review the private/draft
upload on YouTube yourself before flipping it public.

## YouTube-specific requirements

Per the [YouTube API Services Terms of Service](https://developers.google.com/youtube/terms/api-services-terms-of-service),
Section 9.1, a real upload requires two things beyond what other platforms need:

- **`--made-for-kids` / `--not-made-for-kids`** -- mutually exclusive; you must pass exactly one
  before upload, declaring whether the video is directed at children. Argparse itself rejects
  passing both, and a real upload refuses to proceed if neither is given -- this is never
  defaulted or inferred. Sent as the API's `status.selfDeclaredMadeForKids` field (`true` or
  `false`).
- **`--acknowledge-upload-terms`** -- confirms the required upload notice was shown and accepted.
  `python -m auth.publish_youtube` prints the exact required text (see
  `auth.publish_youtube.UPLOAD_TERMS_NOTICE`) **unconditionally on every real-publish attempt** --
  whether or not this flag is already set -- so the flag can never merely suppress a notice
  nobody saw; it only gates whether the upload proceeds past that point. This is enforced in
  code, not just documented here -- a real upload cannot proceed past it silently.

Neither is required for `--dry-run`.

## Troubleshooting

- **`No saved <platform> session found`** -- run the login wizard for that platform first; the
  publish command reads from `profiles/<platform>/`. This applies to Bluesky, LinkedIn, and
  Instagram, which authenticate via a saved browser session.
- **`No YouTube token found`** -- YouTube doesn't use a browser session at all; run
  `python -m auth.setup_youtube_oauth` first. It writes `profiles/youtube/token.json`.
- **Chrome install fails** -- `playwright install chrome` needs network access; check your
  connection and re-run (it's a no-op if already installed).
- **A step doesn't match what's on screen** -- these platforms' UIs are not a stable public contract.
  Run with the browser visible (the default) so you can see where it diverges, and
  [file a bug report](#reporting-problems--requesting-features) with what you saw. Selectors going
  stale after a platform UI change is the single most likely failure mode for this kind of tool.
- **Login wizard times out** -- default wait is 10 minutes; re-run with `--timeout <seconds>` if you
  need longer (2FA app switching, etc.).

## Reporting problems / requesting features

- **Report a problem** -> Bug report issue template.
- **Feature/platform request** -> Feature request issue template.
- **Share test results** -> Beta test report issue template. Please include:
  whether installation worked; your operating system; whether you used Claude Code or another
  coding agent; whether authentication worked; whether YouTube publication succeeded; where the
  instructions were unclear; and anything specific to OpenMontage-rendered output, if that's what
  you tested with.
- **Broader feedback or ideas** -> GitHub Discussions.

See [SECURITY.md](SECURITY.md) to report a security issue specifically,
[PRIVACY.md](PRIVACY.md) for what's stored locally and why, and
[CONTRIBUTING.md](CONTRIBUTING.md) before sending a PR.

## Roadmap

See [ROADMAP.md](ROADMAP.md) and [CHANGELOG.md](CHANGELOG.md).

## License

MIT -- see [LICENSE](LICENSE).
