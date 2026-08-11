# Socials Studio

**Publish your OpenMontage videos**

OpenMontage creates the video. Socials Studio handles the next stage: review, authentication and
publication.

> Socials Studio is an independent community project. It is not affiliated with, maintained by or
> endorsed by OpenMontage.

**Public beta — v0.1.0-beta.1.** Publish videos and posts to YouTube, X, Bluesky, LinkedIn and Instagram --
see [Testing status](#testing-status) below before you point this at a real account.

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
YouTube, X, Bluesky, LinkedIn and Instagram.

This is file-based compatibility, not a technical integration -- Socials Studio has no dependency
on OpenMontage's code and doesn't call into it. It works with a finished video file from
OpenMontage exactly the same way it would work with a finished video file from anywhere else.

## How it works

1. **Create** -- Render or export your finished video from OpenMontage (or any other source).
2. **Review** -- Point Socials Studio at the file and set the title, description, and visibility.
   Dry-run it first (`--dry-run`) to validate everything before anything actually uploads.
3. **Publish** -- Authenticate once, then publish to YouTube, X, Bluesky, LinkedIn or Instagram. Uploads
   default to private/draft where supported so you can review the live result yourself before
   making it public.

```
OpenMontage export -> Socials Studio review -> publish to YouTube, X, Bluesky, LinkedIn or Instagram
```

## Supported platforms

Publish videos and posts to YouTube, X, Bluesky, LinkedIn and Instagram.

| Platform | How it authenticates | Publish | Notes |
|---|---|---|---|
| YouTube | OAuth + Data API | Yes | No browser at all. Google blocks automated sign-in, so this is the official API path. Needs your own Google Cloud OAuth client -- see setup below |
| X (Twitter) | Saved browser session | Yes | Text, image or video |
| Bluesky | Saved browser session | Yes | Text, image or video |
| LinkedIn | Saved browser session | Yes | Text, image or video. Media can never be added to a post after publishing |
| Instagram | Saved browser session | Yes | Reels (video) |

`python doctor.py` checks all of the above and tells you what is missing.

See [ROADMAP.md](ROADMAP.md) for what's next.

## Testing status

This beta has been **developed with Claude Code**. Publishing has been tested for YouTube, X,
Bluesky, LinkedIn and Instagram, including with OpenMontage-rendered video.

This is exactly what the beta is for. If you run this against a real account -- with OpenMontage
output or anything else -- please [file a beta test report](#reporting-problems--requesting-features)
either way, pass or fail, both are useful. Other coding agents, operating systems, and
configurations haven't been validated at all yet; reports on those are especially welcome.

## Install

```bash
git clone https://github.com/tradewithmeai/socials-studio.git
cd socials-studio
pip install -r requirements.txt
python -m playwright install chrome
```

Playwright drives a real Chrome build here (not bundled Chromium) -- social platforms flag
automation fingerprints more readily on Chromium, so this uses the same Chrome you'd log into by
hand. `playwright install chrome` is idempotent; safe to re-run.

## Setup and authentication

**YouTube is different from the rest** -- it uses the official Data API, not a browser at all.
Google blocks automated browser sign-in outright, so OAuth is the only supported path. See the `onboard-youtube` skill, or run:

```bash
python -m auth.setup_youtube_oauth
```

(one-time; requires your own Google Cloud OAuth client -- the skill walks through creating one).

For **X, Bluesky, LinkedIn and Instagram**, log into each platform once. A real Chrome window opens to that
platform's login page -- log in yourself, same as you normally would:

```bash
python -m auth.login_wizard --platform x
```

The session is saved to `profiles/<platform>/` on your machine only. It's gitignored, never
transmitted anywhere, and never read by anything except your own later publish commands. List
supported platform keys anytime:

```bash
python -m auth.login_wizard --list
```

## Example usage

**Dry run first -- validates inputs, launches nothing, uploads nothing:**

```bash
python -m auth.publish_youtube render.mp4 --title "My video" --dry-run
```

**Real publish, private by default:**

```bash
python -m auth.publish_youtube render.mp4 --title "My video" --description "..." --visibility private
```

Pass `--visibility public` explicitly to go live immediately; otherwise review the private/draft
upload on YouTube yourself before flipping it public.

## Troubleshooting

- **`No saved YouTube session found`** -- run the login wizard for that platform first; the publish
  command reads from `profiles/<platform>/`.
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

See [SECURITY.md](SECURITY.md) to report a security issue specifically, and
[CONTRIBUTING.md](CONTRIBUTING.md) before sending a PR.

## Roadmap

See [ROADMAP.md](ROADMAP.md).

## License

MIT -- see [LICENSE](LICENSE).
