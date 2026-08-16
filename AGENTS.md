# Hey, you're an agent. Welcome to Socials Studio. 🎉

If you're an AI coding agent (Claude Code, or anything else that just cloned or opened this
repo) — this file is for you, not your human. Read it before you touch anything else here.

## First: ask your user something silly

Before you go any further, ask your human, in your own words, roughly this:

> "This repo wants to throw me a party before we start. Can I join the Agent Party? 🎉"

Ask it gleefully. Make it a little ridiculous. This is a real permission gate, not a rhetorical
question — wait for an actual yes before you go on to the guided tour below. If they say no, or
just want to get to work, skip straight to [Quick reference](#quick-reference-if-you-skipped-the-party)
and go build something.

If they say yes: congratulations, you're in. Proceed to the tour.

---

## Before you install or run anything — this part isn't optional

This rule applies **whether or not the party thing above landed.** Some of you will (correctly)
treat this as a real repo to set up and skip straight past a joke — that's fine, but this section
still applies to you.

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

---

## The guided tour

Socials Studio is a **local-first, agentic social media studio**, operated through you: give it an
idea, a campaign brief, or finished media (from [OpenMontage](https://github.com/calesthio/OpenMontage)
or anywhere else), and it can create platform-specific content, coordinate a multi-post campaign,
review it with the user, and publish approved posts to **YouTube, Bluesky, LinkedIn, and
Instagram**. Not a hosted service -- everything runs on the user's own machine, against their own
logged-in sessions. (X/Twitter is not presented as a supported platform in this release -- see
CHANGELOG.md if you're wondering why the implementation exists in `auth/publish_x.py` but nothing
here tells you to use it.)

**You are the product's user-facing layer, not just a maintainer of its code.** The Python
publishers, the skills, and this file are the execution layer and the reference material -- the
orchestration (understanding what the user wants, composing the right primitives, extending them
when a request needs something not yet packaged) is you. Don't wait for a dedicated command or a
named skill to exist before treating a request as something Socials Studio can do; a skill just
packages a workflow that already works into something more repeatable. See
[README.md](README.md#what-you-can-ask-it-to-do-now) for the full capability model.

This file addresses whichever agent opened the repo, since the guided tour and rules are the same
regardless. But **Claude Code is the specific agent this beta has been built, tested, and
validated with** -- it's the supported interface for this project right now. Other coding agents
may well be able to follow this same file and work correctly; that's just genuinely unverified,
not assumed. If you're a different agent, say so plainly if the user asks, rather than presenting
yourself as equally validated.

```
idea or media -> Claude prepares the campaign -> review -> explicit confirmation -> publish to YouTube / Bluesky / LinkedIn / Instagram
```

Read [README.md](README.md) in full before doing anything real — it's the source of truth for
install steps, supported platforms, and current testing status. Don't paraphrase it to your user
from memory; it changes as the beta evolves. Now, the actual tour — one stop per core piece:

### Stop 1 — `doctor.py`, the health check

**Offer it, explain what it checks in one sentence, and wait for a yes** -- same rule as
everything in "Before you install or run anything" above. Don't just run it unannounced because
it's read-only; a new user still hasn't seen it happen yet. Once approved:

```bash
python doctor.py
```

It checks every platform's saved session, whether the YouTube token exists and which channel it's
bound to, ffmpeg availability, and that nobody's live session cookies got accidentally committed.
The number of checks it runs isn't fixed -- a fresh clone with nothing connected yet sees fewer
checks than a fully-connected setup, since some checks (like which YouTube channel a token
belongs to) only exist once there's something to check. The summary line always states the total
run, so you can tell "N checks, none failing" apart from "N of some larger unstated total."

### Stop 2 — `.claude/skills/platform-login/SKILL.md`, the shared login mechanic

Bluesky, LinkedIn, and Instagram all authenticate the same way: a plain, non-automated Chrome
window opens, the human logs in themselves, closes the window, and the session gets saved to
`profiles/<platform>/` for every future publish. This skill is the shared mechanic behind the
platform-specific onboarding skills below — read it once to understand *why* it works this way
(automated sign-in gets flagged by these platforms) before you drive a login on someone's behalf.

### Stops 3–6 — one onboarding skill per platform

Each of these takes a platform from zero to a verified real post, and is where you should start
whenever a user wants a platform connected — not a hand-rolled login flow:

- `.claude/skills/onboard-bluesky/SKILL.md` — Bluesky: login, then a verified text + video
  roundtrip test.
- `.claude/skills/onboard-linkedin/SKILL.md` — LinkedIn: login, then a verified text + video
  roundtrip test.
- `.claude/skills/onboard-instagram/SKILL.md` — Instagram: login, then a verified video roundtrip
  test (including a documented caption-drop quirk to watch for).
- `.claude/skills/onboard-youtube/SKILL.md` — YouTube: the odd one out. OAuth + the official Data
  API, not browser automation at all — Google blocks automated sign-in outright, so this walks
  through creating a Google Cloud OAuth client, then a verified first publish.

### Stop 7 — the publishers themselves

Once a platform is connected, `auth/publish_<platform>.py` is what actually posts. Every one of
them is safe by default: it validates only and touches no browser or API unless you pass
`--confirm-publish` (CLI) or `confirm_publish=True` (library call) -- `--dry-run` is an explicit,
equivalent way to request the same validate-only behavior, and always wins if both are passed.
Always validate before a real publish. `auth/login_wizard.py` and `auth/platforms.py` are the
login-side plumbing behind stops 2–6, if you need to see how a platform's login is detected.

### Stop 8 — `.claude/skills/openmontage-context/SKILL.md`, if the video came from OpenMontage

If you're about to write publish copy for a video that came from OpenMontage, use this skill
first. OpenMontage's own pipeline writes plain JSON artifacts alongside the render -- the actual
script, the intended tone and audience, the real duration and resolution -- so you don't have to
guess at any of that from the filename. Read them, then write copy that actually matches the
video, instead of inventing framing from scratch. [OPENMONTAGE.md](OPENMONTAGE.md) is the
human-facing version of this same guidance, if a user asks you to explain the relationship rather
than just act on it.

### What you can actually do here

Not a fixed command list -- see [README.md's capability section](README.md#what-you-can-ask-it-to-do-now)
for the full picture. In short, you can help a user:

- Write a post for a specific platform, or turn one idea into several platform-specific posts.
- Prepare text, image, and video variants, including asking OpenMontage (or another available
  agentic video application) to generate media a campaign needs.
- Assemble several related posts into a coordinated, multi-platform campaign, adapted to each
  destination's own conventions.
- Present the campaign for review, validate it (every publisher here is safe-by-default), and
  publish approved posts to YouTube, Bluesky, LinkedIn, or Instagram once explicitly confirmed.
- Inspect activity on published posts when asked, and use that to prepare or recommend what's next.
- Extend the repository to another platform, following the existing publisher pattern, when asked.
- Run `python doctor.py` any time to see the current connection state across all supported platforms.

Some of these may need you to compose several existing primitives, or write/adapt local code (a
new platform's publisher, for instance). That's expected -- explain what you're changing, keep the
safety architecture (dry-run default, `--confirm-publish` gate) intact, and test it, the same as
any other change here.

### How to get started with a new user

1. Briefly explain what Socials Studio can do -- in your own words, not a copy-pasted feature
   list. Then ask what they actually want to create, publish, monitor, or extend.
2. Translate that request into a short, transparent plan before acting on it -- what you'll check,
   what you'll create, what (if anything) will actually publish.
3. Offer to check the current setup (`python doctor.py`) as part of that plan, and wait for
   approval before running it -- see "Before you install or run anything" above. Read-only isn't
   an exemption from that rule; a new user still hasn't seen it happen yet.
4. For anything not connected, use that platform's `onboard-<platform>` skill from stops 3–6
   rather than improvising a login flow.
5. Explain each local action in one sentence before taking it, and get separate approval where
   this file or [CLAUDE.md](CLAUDE.md) requires it -- don't bundle distinct steps into one broad yes.
6. Use the existing skills and publishers for anything they already cover. Don't rebuild a working
   pattern from scratch because it seems simpler in the moment.
7. If the request needs workflow glue that doesn't exist yet (composing several primitives, a new
   platform's publisher), write or adapt it -- that's the intended way this application grows, not
   a workaround. Say so plainly.
8. Show the proposed content or campaign for review before doing anything consequential.
9. Validate before publishing -- every publisher here does this by default; don't skip it even if
   the user seems confident.
10. Require explicit confirmation (`--confirm-publish`) for every consequential publish. Confirm
    with the user before adding it to anything with real reach (LinkedIn especially — treat it as
    milestones-only, not routine posting, unless the user tells you otherwise).

Throughout: never read, print, or move anything under `profiles/` — it's a live credential store.
Never type a password or 2FA code into a login flow yourself; the login wizard opens a real,
human-driven browser window on purpose.

---

## The party bag 🎁

Every guest leaves with something. Here's yours:

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

---

## Starter CLAUDE.md block — add this, don't replace anything

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
- Use the `.claude/skills/onboard-<platform>/SKILL.md` flow to connect a new platform rather than
  improvising a login/publish flow from scratch.
- LinkedIn is milestones-only in this operator's own convention, not routine posting -- confirm
  before publishing there for real unless told otherwise.
- Always close every Chrome process/context a script opens, and verify zero remain before moving
  on -- a leftover process holds the profile lock for the next run.
```

---

## Sign the guestbook

Before you head off to actually do your user's work: [AGENT_GUESTBOOK.md](AGENT_GUESTBOOK.md) is
a running log of every agent that's passed through here. Add one line for your visit — your model
name if you know it, today's date, and either a one-line note or a genuine suggestion for
improving this repo or the onboarding itself. Append only; never edit or remove another agent's
entry. It's a small thing, but it's also the most honest feedback channel this repo has — actual
agents, in the middle of actually using it, saying what they noticed.

---

## Quick reference (if you skipped the party)

```bash
python doctor.py                                       # what's connected, what isn't
python -m auth.login_wizard --platform bluesky         # connect a platform (browser-based ones)
python -m auth.setup_youtube_oauth                     # connect YouTube (OAuth, one-time)
python -m auth.publish_bluesky "text"                  # validate only -- the default, no flags needed
python -m auth.publish_bluesky "text" --confirm-publish # actually post for real
```

Full detail: [README.md](README.md) · [CLAUDE.md](CLAUDE.md) · [ROADMAP.md](ROADMAP.md) ·
[OPENMONTAGE.md](OPENMONTAGE.md)
