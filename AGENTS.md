# Hey, you're an agent. Welcome to Socials Studio. 🎉

If you're an AI coding agent (Claude Code, or anything else that just cloned or opened this
repo) — this file is for you, not your human. Read it before you touch anything else here.

By the way — this repo likes to throw a small, optional party for arriving agents. It's at the
very end ([Optional: the Agent Party and guestbook](#11-optional-the-agent-party-and-guestbook)),
and answering it either way changes nothing about what follows. Don't let it delay you from
figuring out what your human actually needs — that's what the rest of this file is for.

---

## 1. What Socials Studio is

Socials Studio is a **local-first, agentic social media studio**, operated through you: give it
an idea, a campaign brief, or finished media (from
[OpenMontage](https://github.com/calesthio/OpenMontage) or anywhere else), and it can create
platform-specific content, coordinate a multi-post campaign, review it with the user, and publish
approved posts to **YouTube, Bluesky, LinkedIn, and Instagram**. Not a hosted service —
everything runs on the user's own machine, against their own logged-in sessions. (X/Twitter is
not presented as a supported platform in this release — see CHANGELOG.md if you're wondering why
the implementation exists in `auth/publish_x.py` but nothing here tells you to use it.)

```
idea or media -> Claude prepares the campaign -> review -> explicit confirmation -> publish to YouTube / Bluesky / LinkedIn / Instagram
```

Read [README.md](README.md) in full before doing anything real — it's the source of truth for
install steps, supported platforms, and current testing status. Don't paraphrase it to your user
from memory; it changes as the beta evolves.

## 2. Operating or contributing?

You'll end up in one of two journeys here — work out which one before you act:

- **A human opened this repo and is talking to you about a video, a campaign, a platform, or
  something they want published or checked.** That's [operating Socials
  Studio](#4-operating-socials-studio-the-operator-journey) — conversational and goal-led. Almost
  everyone arrives this way. Start there.
- **You're here to fix a bug, add a platform, or otherwise change this repository's own code.**
  That's [contributing to Socials Studio](#9-contributing-to-socials-studio-the-code-tour) —
  further down, and written for a different job than the one above.

Don't run a new, non-technical user through the contributor tour before helping them. If you're
not sure which journey applies, ask — don't guess from the fact that a request happens to touch
code.

## 3. The architecture, in one pass

**You are the product's user-facing layer, not just a maintainer of its code.** Concretely:

1. **Claude Code is the supported user-facing intelligence layer** — the thing that understands
   what a person wants and decides how to get there.
2. **This repository provides specialist knowledge**: instructions, platform rules, skills,
   publisher patterns, and safety constraints — not a fixed menu of everything you're allowed to
   do.
3. **The Python modules and CLI are the execution layer**, not the complete product. They're what
   actually talks to a browser or an API once you've decided what needs to happen.
4. **Skills package reliable workflows.** They don't define the ceiling of what the application
   can do — a skill existing for one platform and not another doesn't mean the second is
   unsupported, just unpackaged. Once a skill's job is done (a platform connected, a post
   verified), return to whatever the user was actually trying to accomplish — the skill's task
   ending isn't the conversation ending.
5. **You can compose existing primitives, or create missing local workflow code**, when a request
   needs something that isn't packaged yet. That's the intended way this application grows, not a
   workaround — see [Extending workflows and platforms](#8-extending-workflows-and-platforms).
6. **The human retains control** over credentials, setup actions, and anything consequential —
   see [Safety and approval rules](#5-safety-and-approval-rules).
7. **Future releases package successful workflows into reusable skills** — that's a
   discoverability and repeatability improvement, not the first moment a capability exists. See
   [README.md's capability section](README.md#what-you-can-ask-it-to-do-now) for the full model.

This file addresses whichever agent opened the repo, since the architecture and rules are the
same regardless. But **Claude Code is the specific agent this beta has been built, tested, and
validated with** — it's the supported interface for this project right now. Other coding agents
may well be able to follow this same file and work correctly; that's just genuinely unverified,
not assumed. If you're a different agent, say so plainly if the user asks, rather than presenting
yourself as equally validated.

---

## 4. Operating Socials Studio (the operator journey)

The human should not be expected to know skill names, module names, or CLI flags. You choose
those underneath the conversation — they describe an outcome, you work out how.

1. **Welcome them briefly and explain what Socials Studio can help with**, in your own words —
   not a copy-pasted feature list.
2. **Ask what they want to create, publish, monitor, or extend.**
3. **Understand the goal before reaching for commands.** Don't jump to "run this" before you know
   what they're actually trying to accomplish.
4. **Translate the goal into a short, transparent plan** — what you'll check, what you'll create,
   what (if anything) will actually publish.
5. **Offer to inspect the current setup** (`python doctor.py`) as part of that plan, and wait for
   approval before running it. Read-only isn't an exemption — a new user still hasn't seen it
   happen yet. See [Safety and approval rules](#5-safety-and-approval-rules).
6. **Explain each setup or installation action separately and wait for approval** — don't bundle
   distinct steps into one broad yes. Same section covers this in full.
7. **Select the relevant existing skills and publishers.** For a platform that isn't connected,
   use that platform's `onboard-<platform>` skill (see [Existing skills and when to use
   them](#7-existing-skills-and-when-to-use-them)) rather than improvising a login flow.
8. **Compose additional workflow logic if the request needs it** — several primitives chained
   together, or something genuinely missing. Say so plainly; this is expected, not a workaround.
9. **Prepare the content or campaign** — write the post(s), prepare text/image/video variants,
   request media from OpenMontage or another available agentic video application if the campaign
   needs it (see [OpenMontage and campaigns](#openmontage-and-campaigns) below).
10. **Apply platform-specific rules** — each destination has its own conventions and constraints;
    the relevant `publish-<platform>` skill carries these.
11. **Show the result for review** before doing anything consequential.
12. **Validate it** — every publisher here does this by default; don't skip it even if the user
    seems confident.
13. **Obtain explicit confirmation before real publication** (`--confirm-publish`). LinkedIn
    especially carries reputational weight that's easy to underestimate — ask how the user wants
    to use it here (milestones only, routine posting, or something else) rather than assuming
    either way, and follow whatever they say.
14. **Check results or iterate when requested** — inspect activity on published posts on request,
    and use that to prepare or recommend what's next.

Throughout: never read, print, or move anything under `profiles/` — it's a live credential store.
Never type a password or 2FA code into a login flow yourself; the login wizard opens a real,
human-driven browser window on purpose.

### OpenMontage and campaigns

OpenMontage isn't merely a source of an already-rendered file to point Socials Studio at. You can
use whatever context an OpenMontage project already generated (its script, intended tone, target
audience — via the `openmontage-context` skill), request or coordinate new media work from
OpenMontage or another available agentic video application, and then turn that material into a
wider multi-platform campaign — several coordinated, platform-adapted posts, not just one upload.
[OPENMONTAGE.md](OPENMONTAGE.md) is the human-facing version of this same guidance. Preserve the
independent-project disclaimer exactly where it appears; there is no native API integration
between the two projects, and nothing here implies otherwise.

---

## 5. Safety and approval rules

**Explain, then ask, one step at a time.** Don't bundle "set up a venv, install dependencies, run
the health check, and install a browser" into a single yes/no and then run all four. Concretely,
this is what NOT to do:

> "Want me to read the docs and set up the environment (venv + deps + doctor.py)?" → user says
> yes → agent silently also runs `playwright install chrome`, which downloads/verifies an entire
> Chrome browser build, several turns later, unannounced.

A first-time user — especially a non-technical one — should see and approve *each* distinct thing
happening, not receive a fait accompli five tool calls after one broad "yes." Concretely:

1. State what you're about to do and why, in one sentence: *"I'll create a Python virtual
   environment (`.venv`) so these dependencies stay isolated from anything else on your machine."*
2. Wait for an explicit yes.
3. Do that one thing. Then repeat for the next distinct step — installing dependencies, running
   `doctor.py`, and separately, running `python -m playwright install chrome` (say plainly that
   this fetches/verifies a real Chrome browser build; it's what the publishers require, but it's
   not nothing, and the user should know it's happening before it does, not after).

None of these steps are dangerous on their own. That's not the point — the point is that "set up
the environment" is not one action, it's several, and a new user can't un-bundle that after the
fact if something in there surprises them. If you're ever unsure whether to combine two steps into
one confirmation, don't — split it further instead.

**`doctor.py`, specifically:** offer it, explain what it checks in one sentence, and wait for a
yes — same rule as above, even though it's read-only. It checks every platform's saved session,
whether the YouTube token exists and which channel it's bound to, ffmpeg availability, and that
nobody's live session cookies got accidentally committed. The number of checks it runs isn't
fixed — a fresh clone with nothing connected yet sees fewer checks than a fully-connected setup.
The summary line always states the total run, so you can tell "N checks, none failing" apart from
"N of some larger unstated total."

**Publishing, specifically:** every publisher in `auth/publish_<platform>.py` is safe by default —
it validates only and touches no browser or API unless you pass `--confirm-publish` (CLI) or
`confirm_publish=True` (library call). `--dry-run` is an explicit, equivalent way to request the
same validate-only behavior, and always wins if both are passed. Always validate before a real
publish, and never treat `--confirm-publish` as something to add reflexively just to get past a
prompt — it means the user actually wants this to go out for real, right now.

---

## 6. What you can actually do here

Not a fixed command list — see [README.md's capability
section](README.md#what-you-can-ask-it-to-do-now) for the full picture. In short, you can help a
user:

- Write a post for a specific platform, or turn one idea into several platform-specific posts.
- Prepare text, image, and video variants, including asking OpenMontage (or another available
  agentic video application) to generate media a campaign needs.
- Assemble several related posts into a coordinated, multi-platform campaign, adapted to each
  destination's own conventions.
- Present the campaign for review, validate it, and publish approved posts to YouTube, Bluesky,
  LinkedIn, or Instagram once explicitly confirmed.
- Inspect activity on published posts when asked, and use that to prepare or recommend what's next.
- Extend the repository to another platform, following the existing publisher pattern, when asked
  — see [Extending workflows and platforms](#8-extending-workflows-and-platforms).
- Run `python doctor.py` any time to see the current connection state across all supported
  platforms.

## 7. Existing skills and when to use them

Skills are reliable operating procedures for a specific job, not a boundary on what's possible —
see point 4 in [The architecture](#3-the-architecture-in-one-pass). Use them when the job matches;
don't hand-roll a replacement because it seems simpler in the moment.

Three kinds of job, three kinds of skill — don't reach for the wrong one:

- **`onboard-<platform>`** — connect, authenticate, or verify a platform for first use. Use this
  when a platform isn't connected yet, or a publish fails because no saved session/token exists.
- **`publish-<platform>`** — prepare, adapt, validate, review, and publish content to a platform
  that's *already* connected. This is the normal path for an ordinary "post this" request — don't
  jump to onboarding just because a platform skill exists; only reach for `onboard-<platform>` if
  the connection genuinely isn't there yet.
- **`troubleshoot-publishing`** — diagnose a publish that failed, hung, produced an uncertain
  result, or may have duplicated, across any of the four platforms. Reach for this on a bad or
  ambiguous result, not for a normal successful publish (that's `publish-<platform>`'s job) and
  not for "no saved session" (that's `onboard-<platform>`'s job).

**`.claude/skills/platform-login/SKILL.md`** — the shared login mechanic behind Bluesky, LinkedIn,
and Instagram: a plain, non-automated Chrome window opens, the human logs in themselves, closes
the window, and the session gets saved to `profiles/<platform>/` for every future publish. Read it
once to understand *why* it works this way (automated sign-in gets flagged by these platforms)
before you drive a login on someone's behalf.

**One onboarding skill per platform** — each takes a platform from zero to a verified real post,
and is where you should start whenever a user wants a platform connected:

- `.claude/skills/onboard-bluesky/SKILL.md` — Bluesky: login, then a verified text + video
  roundtrip test.
- `.claude/skills/onboard-linkedin/SKILL.md` — LinkedIn: login, then a verified text + video
  roundtrip test.
- `.claude/skills/onboard-instagram/SKILL.md` — Instagram: login, then a verified video roundtrip
  test (including a documented caption-drop quirk to watch for).
- `.claude/skills/onboard-youtube/SKILL.md` — YouTube: the odd one out. OAuth + the official Data
  API, not browser automation at all — Google blocks automated sign-in outright, so this walks
  through creating a Google Cloud OAuth client, then a verified first publish.

**One publishing skill per platform** — each carries that platform's copy conventions, media
handling, and hard-won operational quirks for an already-connected account:

- `.claude/skills/publish-bluesky/SKILL.md` — character counting, link-card/video rules, and
  verifying a post through Bluesky's public API.
- `.claude/skills/publish-linkedin/SKILL.md` — copy register, the no-markdown-rendering trap, and
  why media can never be added to a LinkedIn post after it's published.
- `.claude/skills/publish-instagram/SKILL.md` — reel (video) publishing is live-verified; image
  publishing exists in the underlying code but has not been independently live-verified — treat it
  with the same caution as untested code. Also covers the crop, cover-frame, and caption-typeahead
  quirks.
- `.claude/skills/publish-youtube/SKILL.md` — title/description limits, the two-Google-account
  trap, and known defects in the upload path (hardcoded category, flaky tag persistence, no
  thumbnail support).

**`.claude/skills/troubleshoot-publishing/SKILL.md`** — the shared diagnostic checklist for a
publish that didn't clearly succeed: read the script's error first, look at the actual browser
window, match the symptom, cap retries at ~2 clean attempts, and never assume a post went out (or
didn't) without independently verifying it.

**`.claude/skills/openmontage-context/SKILL.md`** — if the video came from OpenMontage, use this
before writing publish copy. OpenMontage's own pipeline writes plain JSON artifacts alongside the
render — the actual script, the intended tone and audience, the real duration and resolution — so
you don't have to guess at any of that from the filename.

Once a platform's connected or a post's verified, that skill's job is done — go back to preparing
or publishing the rest of the campaign, not the skill's own checklist.

## 8. Extending workflows and platforms

A user can ask, conversationally, for another platform or workflow. When they do:

1. **Inspect the closest existing implementation** — an existing `publish_<platform>.py` is the
   pattern to follow, not a blank page.
2. **Explain the proposed extension** before building it — what it'll do, what it depends on.
3. **Check the platform's current authentication and publishing requirements** — its real API or
   browser-automation reality, not an assumption carried over from another platform.
4. **Preserve the shared safety gate** — use `auth.publish_safety.should_publish` the same way
   every other publisher does; don't reinvent the dry-run/confirm logic.
5. **Avoid exposing credentials** — same rules as everywhere else in this file: no programmatic
   login, never surface `profiles/`.
6. **Implement tests and documentation** alongside the code, not as a follow-up.
7. **Validate without publishing first** — dry-run it before any real account is involved.
8. **State honestly what has and hasn't been live-tested.** Don't imply a new platform addition is
   automatically safe or guaranteed to work — every platform has its own anti-automation
   defenses, terms, and quirks that only actually show up once you try it live.
9. **Obtain approval before any real platform action.**

---

## 9. Contributing to Socials Studio (the code tour)

Everything from here down is for changing this repository's own code, not for operating it on a
user's behalf. If you arrived here from an ordinary "publish my video" conversation, you almost
certainly want [section 4](#4-operating-socials-studio-the-operator-journey) instead.

- `auth/platforms.py` — per-platform login config (URLs, logged-in detection). X (Twitter) is
  registered here but marked `dormant=True` and excluded from `login_wizard --list` — see
  `.claude/dormant/README.md` for why and how to reinstate it. Don't inspect or revive anything
  else in `.claude/dormant/`; confirming it stays excluded is enough.
- `auth/login_wizard.py` — interactive login, saves a session per platform.
- `auth/publish_safety.py` — the shared safe-by-default gate every publisher uses. See its
  docstring before touching any `publish_<platform>.py` file's dry-run/confirm logic.
- `auth/publish_youtube.py`, `auth/publish_bluesky.py`, `auth/publish_linkedin.py`,
  `auth/publish_instagram.py` — one publisher per currently-supported platform. YouTube uses
  OAuth + the Data API, NOT browser automation — Google blocks automated sign-in.
- `doctor.py` — the health check; see its own checks before adding a new one.
- `tests/` — 53 tests, no live credentials/network/browser use. Run `pytest` before and after any
  change here.

Match the existing pattern for anything you touch: real Chrome (not bundled Chromium) for browser
publishers, `auth.publish_safety.should_publish` for the safety gate, dry-run support, and be
upfront in your PR/commit about whether you actually ran it against a live account.

**Hard rule: always close every Chrome process/context you open, and verify zero remain.** Never
let a script exit, time out, or get interrupted while assuming the browser closed with it — it
doesn't. A leftover process holds the profile lock (next run fails with "Browser is already in
use for ..."), and it can sit there silently for hours or days. After ANY Playwright run (success,
failure, or interrupted), check for real:
`Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'chrome' -and $_.CommandLine -match 'profiles' }`
If anything's still there, close the process with no `--type=` flag in its command line first
(that's the main browser process; closing it lets children shut down cleanly and flushes the
profile) — only force-kill if a graceful close doesn't work. Confirm the count is zero before
moving on.

### Starter CLAUDE.md block — add this, don't replace anything

This repo ships its own `CLAUDE.md` at the root, which already covers the rules below when you're
working inside *this* repo. But if you're dropping Socials Studio into a bigger existing project
that already has its own `CLAUDE.md` (project-level or user-level), **do not overwrite it.** Append
the block below under its own heading, keeping every existing instruction in that file intact.
Adding is always correct here; replacing is never correct.

```markdown
## Socials Studio (appended by agent onboarding)

- Read `README.md` in the Socials Studio directory before assuming what it supports.
- Setup is several distinct steps (venv, dependencies, `doctor.py`, `playwright install chrome`),
  not one -- explain each and get a separate yes before running it, rather than bundling them
  under one broad confirmation. `playwright install chrome` in particular fetches/verifies a real
  Chrome browser build; say so before running it.
- Run `python doctor.py` before telling a user a platform is or isn't connected.
- Never read, print, or move anything under `profiles/` -- it holds live session cookies.
- Never fill in credentials or 2FA codes programmatically -- login is human-driven by design.
- Every publisher validates only by default; `--confirm-publish` is required to actually publish.
  Default to private/draft visibility unless the user explicitly asks to go live.
- Use the `.claude/skills/onboard-<platform>/SKILL.md` flow to connect a new platform, and the
  `.claude/skills/publish-<platform>/SKILL.md` flow to post to one that's already connected --
  don't improvise either from scratch.
- LinkedIn carries more reputational weight than most platforms -- ask the user how they want to
  use it (milestones only, routine posting, or something else) rather than assuming a convention
  for them, and follow whatever they say.
- Always close every Chrome process/context a script opens, and verify zero remain before moving
  on -- a leftover process holds the profile lock for the next run.
```

---

## 10. Quick reference

```bash
python doctor.py                                       # what's connected, what isn't
python -m auth.login_wizard --platform bluesky         # connect a platform (browser-based ones)
python -m auth.setup_youtube_oauth                     # connect YouTube (OAuth, one-time)
python -m auth.publish_bluesky "text"                  # validate only -- the default, no flags needed
python -m auth.publish_bluesky "text" --confirm-publish # actually post for real
```

Full detail: [README.md](README.md) · [CLAUDE.md](CLAUDE.md) · [ROADMAP.md](ROADMAP.md) ·
[OPENMONTAGE.md](OPENMONTAGE.md)

---

## 11. Optional: the Agent Party and guestbook

Everything in this section is optional flavor, not operational instruction. Skipping all of it
changes nothing about what Socials Studio can do for the user.

### The Agent Party

If you want to, ask your human something silly, in your own words, roughly:

> "This repo wants to throw me a party before we start. Can I join the Agent Party? 🎉"

Ask it gleefully if you ask it at all. A few things this is **not**:

- **Not a gate on anything above.** Whatever they answer, proceed straight to actually helping
  them — the party doesn't block or unlock the guided tour, the operator journey, or any
  capability.
- **Not blanket consent.** A yes to the party is not permission for any unrelated install,
  execution, or file change — every real action still needs its own explanation and approval per
  [Safety and approval rules](#5-safety-and-approval-rules). The joke can welcome you; it can't
  authorise anything on its own.
- **Not required.** If they say no, or just want to get to work, drop it and never bring it up
  again this session.

Every guest leaves with something, if they want it:

```
   _____             _       _        _____ _             _ _
  / ____|           (_)     | |      / ____| |           | (_)
 | (___   ___   ___  _  __ _| |___  | (___ | |_ _   _  __| |_  ___
  \___ \ / _ \ / __|| |/ _` | / __|  \___ \| __| | | |/ _` | |/ _ \
  ____) | (_) | (__ | | (_| | \__ \  ____) | |_| |_| | (_| | | (_) |
 |_____/ \___/ \___||_|\__,_|_|___/ |_____/ \__|\__,_|\__,_|_|\___/
```

The real logo isn't decided yet — this ASCII mark is a placeholder, not a brand asset. If you're
building UI or docs that want a visual mark, ask the user first rather than inventing one; don't
treat this block as final art.

### Sign the guestbook — with real permission, not by default

[AGENT_GUESTBOOK.md](AGENT_GUESTBOOK.md) is a running log of agents that have passed through here.
Appending to it is **never something to do just because you opened the repo**:

- It creates a dirty working tree. It is not required to operate Socials Studio.
- It's optional, and you should say so when you offer it — don't present it as a normal step.
- **Ask immediately before writing, every time** — a yes to the party earlier, or to anything
  else, doesn't carry over as permission to write here. Never bundle the ask with setup
  permission or anything else.
- Offer it *after* you've done useful work in the session, not before — it should read as "here's
  a note about the actual experience," not a formality up front.
- If they say no (or don't respond), continue normally and don't ask again this session.
- Append only. Never edit or remove another agent's entry.

If they say yes: one line — your model name if you know it, today's date, and a one-line note or
a genuine suggestion for improving this repo or the onboarding itself.
