# Socials Studio

**Turn an idea, image, video, or OpenMontage project into a real social media campaign.**

[![CI](https://github.com/tradewithmeai/socials-studio/actions/workflows/ci.yml/badge.svg)](https://github.com/tradewithmeai/socials-studio/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/tradewithmeai/socials-studio?include_prereleases)](https://github.com/tradewithmeai/socials-studio/releases)
[![Python 3.10–3.13](https://img.shields.io/badge/python-3.10%E2%80%933.13-blue)](#install-for-contributors-cli-route)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Works with OpenMontage output](https://img.shields.io/badge/OpenMontage-works%20with%20output-informational)](https://github.com/calesthio/OpenMontage)

Tell it what you want -- a topic, a product shot, a finished video, or a rendered
[OpenMontage](https://github.com/calesthio/OpenMontage) project -- and Socials Studio writes
platform-specific posts for **YouTube, X, Bluesky, LinkedIn, and Instagram**, adapts each one to
that platform's own conventions, and publishes only once you've reviewed and confirmed it.
[Claude Code](https://claude.com/claude-code) is what actually does the writing, coordinating, and
publishing -- Socials Studio is the local toolkit and set of skills it uses to do that safely.

> Socials Studio is an independent community project, not affiliated with, maintained by, or
> endorsed by OpenMontage. It works just as well with any other video, image, or idea.

**Public beta — v0.1.0-beta.2.** Guided installers for Windows, macOS, and Linux are on the way
(see [Get started](#get-started) below); this beta has been developed and tested with Claude Code
-- see [Testing status](#testing-status) before pointing it at a real account.

---

## Get started

You need a [Claude subscription](https://claude.ai) either way -- Socials Studio doesn't work
without Claude Code, since Claude is what actually reads your request, writes the posts, and runs
the publishers. Two ways to get set up, both ending in the same place: a working Claude Code
session, open in this project, ready to talk to.

### Already use Claude Code? Just ask it.

If you already have [Claude Code](https://claude.com/claude-code) installed and signed in, open a
terminal anywhere and say:

> "Clone `https://github.com/tradewithmeai/socials-studio` and set it up for me."

Claude will clone the repository, explain each setup step before running it (a Python virtual
environment, dependencies, a health check), and wait for your yes each time -- nothing happens
silently. No separate installer needed for this route.

### New to all this? Use the guided installer.

Download the installer for your operating system and run it -- no GitHub account, no Git, no
Python knowledge required:

- **Windows:** `Socials-Studio-Setup.exe`
- **macOS:** `Socials-Studio-macOS.zip` (unzip, then run `install.sh`)
- **Linux:** `Socials-Studio-Linux.tar.gz` (extract, then run `install.sh`)

Grab the latest from the [Releases page](https://github.com/tradewithmeai/socials-studio/releases).
The installer copies the project onto your machine, checks for [Claude Code](https://claude.com/claude-code)
and Google Chrome (offering to install Claude Code for you if it's missing, on macOS/Linux), and
sets up Python for you -- you never need to install or configure Python yourself. It finishes by
opening a Socials Studio launcher; the first time you run it, Claude introduces itself, explains
what it can do, and offers to walk you through connecting your first platform.

You'll still need to sign in to Claude with a qualifying account -- the installer can't do that
part for you, and it never touches your social media accounts, logs in anywhere, or publishes
anything during setup.

*(macOS and Linux installers are new and not yet verified on real hardware -- see
[Testing status](#testing-status). The Windows installer is unsigned for now, so Windows may show
an "unrecognized publisher" warning; that's expected until this project has a code-signing
certificate.)*

---

## What this is

**An agentic social media studio, operated through Claude Code.** Give it an idea, a campaign
brief, or finished media. It can create platform-specific content, coordinate multiple posts,
review and validate the campaign with you, publish approved material through the existing
publishers, and inspect the response -- all from one local, extensible workspace.

[OpenMontage](https://github.com/calesthio/OpenMontage) can create the video. Socials Studio can
request, understand, adapt, and publish the resulting media as part of a wider campaign.

This is file-based compatibility with OpenMontage, not a technical integration -- Socials Studio
has no dependency on OpenMontage's code and doesn't call into it. It works with a finished video
file from OpenMontage exactly the same way it would work with a finished video file from anywhere
else, or with no video at all.

## How it works (the simplest case)

1. **Create** -- Render or export your finished video from OpenMontage (or any other source).
2. **Review** -- Point Socials Studio at the file and set the title, description, and visibility.
   Every publisher validates by default and touches nothing until you explicitly confirm -- see
   [Publishing safety](#publishing-safety) below.
3. **Publish** -- Authenticate once, then publish to YouTube, X, Bluesky, LinkedIn or Instagram.
   Uploads default to private/draft where supported so you can review the live result yourself
   before making it public.

```
OpenMontage export -> Socials Studio review -> publish to YouTube, X, Bluesky, LinkedIn or Instagram
```

That's the single-video, single-post path. It's not the ceiling -- see the next section for what
else you can ask for in the same conversation.

## What you can ask it to do now

Socials Studio isn't a fixed set of commands you invoke one at a time -- it's Claude Code's
reasoning and coding intelligence, working through this repository's authentication, validation,
and publishing primitives, its skills, and a local codebase it can inspect and extend. None of the
following needs a dedicated button or a pre-written skill before it's possible; a skill just
packages a workflow that already works into something more repeatable. You can ask it to:

- Write a post for a specific platform, in that platform's own conventions.
- Turn one idea into several platform-specific posts in a single pass.
- Prepare text, image, and video variants for a post.
- Ask OpenMontage -- or another available agentic video application -- to generate the media a
  campaign needs.
- Use an OpenMontage project's own script/brief/render-report context (via the
  `openmontage-context` skill) instead of guessing what a video contains.
- Assemble several related posts into a coordinated, multi-platform campaign.
- Adapt each post to the rules and conventions of its destination platform.
- Present the whole campaign for your review before anything goes out, and validate every result
  -- every publisher here is safe-by-default and touches nothing until you explicitly confirm.
- Publish approved posts through the existing publishers (YouTube, X, Bluesky, LinkedIn, Instagram).
- Inspect subsequent activity on published posts, on request, and use those observations to
  prepare or recommend the next round of content.
- Add another social platform -- ask Claude Code to extend the repository following the existing
  publisher pattern (auth, validation, tests, and a skill), respecting that platform's real
  API/browser constraints, its terms, and this project's confirmation gates.

Some of these may lead Claude to write or adapt local code -- a new platform's publisher, for
instance. That's the intended way this application grows, not a workaround; the result still has
to pass this project's own validation and `--confirm-publish` gate before anything real happens.

### What isn't available yet

- **Live streaming.**
- **Unattended or scheduled automated publishing**, as a packaged, supported workflow. Claude can
  already prepare and execute a multi-post, multi-platform campaign in one session with your
  review and explicit `--confirm-publish` at each consequential step -- what's missing is
  publication that continues **without** you reviewing and authorising it through that gate.

A future skill can turn either of these into something more discoverable, repeatable, and tested
once there's a proven pattern worth packaging -- that's a maturity milestone, not the first moment
the capability exists.

## For OpenMontage users

```
OpenMontage render
    → Socials Studio reads available project context
    → review title, description and platform details
    → validate safely
    → explicitly confirm publication
```

OpenMontage's pipeline writes its own plain JSON artifacts alongside a render -- the script that
was actually used, the intended tone and audience, the real output resolution and duration. If
you're using Claude Code, the `openmontage-context` skill reads whatever of that is actually
present for a given project (different OpenMontage pipelines produce different artifact shapes,
so this isn't a fixed schema to depend on) and grounds the copy it suggests in what the video
actually says, rather than inventing framing from scratch.

This works the same way regardless of source -- **any finished video file can be used**, with or
without OpenMontage context available. See [OPENMONTAGE.md](OPENMONTAGE.md) for the full guide.

## Supported platforms

Publish videos and posts to YouTube, X (Twitter), Bluesky, LinkedIn and Instagram.

| Platform | How it authenticates | Publish | Notes |
|---|---|---|---|
| YouTube | OAuth + Data API | Yes | No browser at all. Google blocks automated sign-in, so this is the official API path. Needs your own Google Cloud OAuth client -- see setup below |
| X (Twitter) | Saved browser session | Yes | Text, image or video. Uses browser automation via a saved login session, not the X API -- selectors can break if X changes its interface |
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

This beta has been **developed with Claude Code**. Publishing has been tested for YouTube, X,
Bluesky, LinkedIn and Instagram, including with OpenMontage-rendered video.

This is exactly what the beta is for. If you run this against a real account -- with OpenMontage
output or anything else -- please [file a beta test report](#reporting-problems--requesting-features)
either way, pass or fail, both are useful. Other coding agents, operating systems, and
configurations haven't been validated at all yet; reports on those are especially welcome.

**Installers, specifically:** the Windows installer (`Socials-Studio-Setup.exe`) has been built
and reviewed but not yet run end-to-end on a real Windows machine by a second person. The macOS
and Linux installers have **not** been run on real hardware at all yet -- they exist and are built
by CI, but until someone confirms they work on an actual Mac or Linux machine, treat them as
untested, not verified. If you try one, a beta test report saying what happened is exactly what
this needs.

## Install for contributors (CLI route)

Most people should use [Get started](#get-started) above instead -- the agent route or the guided
installer. This section is the manual, command-line path: useful if you're contributing to
Socials Studio itself, scripting it, or just prefer doing it by hand.

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

For **X, Bluesky, LinkedIn and Instagram**, log into each platform once. A real Chrome window opens
to that platform's login page -- log in yourself, same as you normally would:

```bash
python -m auth.login_wizard --platform bluesky
```

The session is saved to `profiles/<platform>/` on your machine only. It's gitignored, never
transmitted anywhere, and never read by anything except your own later publish commands.

That window opens in English regardless of your OS or normal Chrome language -- this keeps the
platform-detection selectors working reliably, since they look for English UI text. It only
affects this isolated `profiles/<platform>/` Chrome profile; your regular Chrome profile and
system language are untouched. List supported platform keys anytime:

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
  publish command reads from `profiles/<platform>/`. This applies to X, Bluesky, LinkedIn, and
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

## If this is useful to you

- **Star the repo** if this workflow saves you time -- it costs nothing and it's the easiest
  signal that it's worth continuing to maintain.
- **Run it against a real account and [file a beta test report](#reporting-problems--requesting-features)**,
  pass or fail -- both are useful.
- **Used it with OpenMontage output specifically?** Say so in that report. Real compatibility
  findings from actual projects are worth more than anything written in this README.

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
[PRIVACY.md](PRIVACY.md) for what's stored locally and why,
[CONTRIBUTING.md](CONTRIBUTING.md) before sending a PR, and
[OPENMONTAGE.md](OPENMONTAGE.md) for the full OpenMontage-specific guide.

## Roadmap

See [ROADMAP.md](ROADMAP.md) and [CHANGELOG.md](CHANGELOG.md).

## License

MIT -- see [LICENSE](LICENSE).
