# Socials Studio

**Read [AGENTS.md](AGENTS.md) yourself, in full, before your first real action in this repo** --
don't wait for the user to tell you to, and don't tell a non-technical user to go read it
themselves. It's the guided tour: the product model, the operator journey, the safety rules, the
skills catalog, and the contributor tour all live there. This file adds the maintainer-facing
detail AGENTS.md doesn't repeat.

Read `README.md` too -- it's the source of truth for install, setup, supported platforms, and
current testing status. See `OPENMONTAGE.md` specifically for how this repo relates to
OpenMontage, if a user asks about that relationship.

## Two operating modes

You'll end up in one of two modes here -- worth recognising before you act, and AGENTS.md's own
structure follows the same split:

1. **Helping a user *operate* Socials Studio.** The default when someone opens this repo and
   starts talking to you about a video, a campaign, or a platform they want to reach. This is
   conversational and goal-led, not code-led: the user describes what they want (an idea, a
   campaign brief, finished media, a question about what already got published), not which Python
   file to run. You can already help them create text/image/video publishing workflows, apply
   platform-specific rules and editing, request media from OpenMontage or another available
   agentic video application, assemble a coordinated multi-platform campaign, publish approved
   content, inspect public activity on request, use those observations to improve later work, and
   extend the repository to another platform. Goal first, plan second, tools and commands third,
   then review, validation, and explicit approval before anything publishes. See
   [README.md's capability section](README.md#what-you-can-ask-it-to-do-now) and
   [AGENTS.md's operator journey](AGENTS.md#4-operating-socials-studio-the-operator-journey) for
   the full model -- don't let the more technical material below dominate this kind of session.
2. **Helping a contributor *modify* Socials Studio itself** -- fixing a publisher, adding a
   platform, touching tests or CI. The rest of this file, `CONTRIBUTING.md`, and
   [AGENTS.md's code tour](AGENTS.md#9-contributing-to-socials-studio-the-code-tour) are written
   mainly for this mode.

Either mode may lead you to compose existing primitives or write/adapt local workflow code --
that's expected agentic behaviour, not a workaround. In both modes: explain what you're changing or
about to do, preserve this project's safety architecture (dry-run default, `--confirm-publish`
gate, YouTube's Made-for-Kids/upload-terms requirements -- all below), test the result, and get
approval before anything consequential happens: publishing for real, or a code change that touches
the publishing/auth path.

## Working in this repo

- `auth/platforms.py` -- per-platform login config (URLs, logged-in detection). X (Twitter) is
  registered here but marked `dormant=True` and excluded from `login_wizard --list` -- see
  `.claude/dormant/README.md` for why and how to reinstate it.
- `auth/login_wizard.py` -- interactive login, saves a session per platform.
- `auth/publish_safety.py` -- the shared safe-by-default gate every publisher uses. See its
  docstring before touching any `publish_<platform>.py` file's dry-run/confirm logic.
- `auth/publish_youtube.py`, `auth/publish_bluesky.py`, `auth/publish_linkedin.py`,
  `auth/publish_instagram.py` -- one publisher per currently-supported platform. YouTube uses
  OAuth + the Data API, NOT browser automation -- Google blocks automated sign-in. Onboarding it
  from scratch goes through `.claude/skills/onboard-youtube/SKILL.md`, not the login wizard.
- `.claude/skills/platform-login/SKILL.md` -- the browser-login wizard for Bluesky/LinkedIn/Instagram
  (not YouTube, not X); read it before driving a login on someone's behalf.

## Rules for an agent operating here

- **Never read, print, or otherwise surface `profiles/*/storage_state.json` or anything under
  `profiles/`.** It holds live session cookies. Treat it like a credential store.
- **Never fill in credentials or 2FA codes programmatically.** The login wizard opens a real
  browser specifically so a human completes login by hand -- automating that defeats the point and
  is what gets accounts flagged.
- Every publisher validates only by default; **`--confirm-publish` (CLI) or `confirm_publish=True`
  (library call) is required to actually publish anything for real.** Don't pass it when
  demonstrating or testing a publisher unless the user explicitly wants a real, live publish.
- Default to `--visibility private` on any real YouTube publish unless told otherwise. A real
  YouTube upload additionally requires exactly one of `--made-for-kids` / `--not-made-for-kids`
  (mutually exclusive, never defaulted or inferred) and `--acknowledge-upload-terms` -- see
  `auth/publish_youtube.py`'s module docstring.
- X (Twitter) is not presented as a supported platform in this release. Don't reference it in
  anything user-facing (docs, onboarding, quick-reference) without checking CHANGELOG.md first.
- If you're extending this to a new platform's publish flow, match the existing pattern: real
  Chrome (not bundled Chromium), `auth.publish_safety.should_publish` for the safety gate, and be
  upfront in your PR/commit about whether you actually ran it against a live account.
- **Hard rule: always close every Chrome process/context you open, and verify zero remain.**
  Never let a script exit, time out, or get interrupted while assuming the browser closed with
  it -- it doesn't. A leftover process holds the profile lock (next run fails with "Browser is
  already in use for ..."), and it can sit there silently for hours or days. After ANY Playwright
  run (success, failure, or interrupted), check for real:
  `Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'chrome' -and $_.CommandLine -match 'profiles' }`
  If anything's still there, close the process with no `--type=` flag in its command line first
  (that's the main browser process; closing it lets children shut down cleanly and flushes the
  profile) -- only force-kill if a graceful close doesn't work. Confirm the count is zero before
  moving on.
