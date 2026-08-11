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

## The guided tour

Socials Studio takes a finished video (from [OpenMontage](https://github.com/calesthio/OpenMontage)
or anywhere else) and publishes it — plus plain text/image posts — to **YouTube, X, Bluesky,
LinkedIn, and Instagram**. It's a local CLI tool, not a hosted service: everything runs on the
user's own machine, against their own logged-in sessions.

```
finished video -> review (title, description, visibility) -> publish to YouTube / X / Bluesky / LinkedIn / Instagram
```

Read [README.md](README.md) in full before doing anything real — it's the source of truth for
install steps, supported platforms, and current testing status. Don't paraphrase it to your user
from memory; it changes as the beta evolves. Now, the actual tour — one stop per core piece:

### Stop 1 — `doctor.py`, the health check

Run it. This is always your first move, on every session, before you tell a user anything is or
isn't working:

```bash
python doctor.py
```

It checks every platform's saved session, whether the YouTube token exists and which channel it's
bound to, ffmpeg availability, and that nobody's live session cookies got accidentally committed.
13 checks when everything's connected; it tells you exactly which ones fail otherwise.

### Stop 2 — `.claude/skills/platform-login/SKILL.md`, the shared login mechanic

X, Bluesky, LinkedIn, and Instagram all authenticate the same way: a plain, non-automated Chrome
window opens, the human logs in themselves, closes the window, and the session gets saved to
`profiles/<platform>/` for every future publish. This skill is the shared mechanic behind all four
platform-specific onboarding skills below — read it once to understand *why* it works this way
(automated sign-in gets flagged by these platforms) before you drive a login on someone's behalf.

### Stops 3–7 — one onboarding skill per platform

Each of these takes a platform from zero to a verified real post, and is where you should start
whenever a user wants a platform connected — not a hand-rolled login flow:

- `.claude/skills/onboard-x/SKILL.md` — X (Twitter): login, then a verified post + reply-with-link
  roundtrip test.
- `.claude/skills/onboard-bluesky/SKILL.md` — Bluesky: login, then a verified text + video
  roundtrip test.
- `.claude/skills/onboard-linkedin/SKILL.md` — LinkedIn: login, then a verified text + video
  roundtrip test.
- `.claude/skills/onboard-instagram/SKILL.md` — Instagram: login, then a verified video roundtrip
  test (including a documented caption-drop quirk to watch for).
- `.claude/skills/onboard-youtube/SKILL.md` — YouTube: the odd one out. OAuth + the official Data
  API, not browser automation at all — Google blocks automated sign-in outright, so this walks
  through creating a Google Cloud OAuth client, then a verified first publish.

### Stop 8 — the publishers themselves

Once a platform is connected, `auth/publish_<platform>.py` is what actually posts. Every one of
them supports `--dry-run` (validates inputs, launches nothing, uploads nothing) — always run that
before a real publish. `auth/login_wizard.py` and `auth/platforms.py` are the login-side plumbing
behind stops 2–7, if you need to see how a platform's login is detected.

### What you can actually do here

- Publish a finished video to YouTube with title, description, tags, and visibility.
- Post text, or text with an image, to X, Bluesky, or LinkedIn.
- Publish a video/reel to Instagram, with a caption.
- Validate any of the above with `--dry-run` before it goes anywhere real.
- Run `python doctor.py` any time to see the current connection state across all five platforms.

### How to get started with a new, non-technical user

1. Run `python doctor.py` — tell them plainly what's connected and what isn't.
2. For anything not connected, use that platform's `onboard-<platform>` skill from stops 3–7.
3. Once connected, `--dry-run` before any real publish, and confirm with the user before anything
   with real reach goes live (LinkedIn especially — treat it as milestones-only, not routine
   posting, unless the user tells you otherwise).
4. Never read, print, or move anything under `profiles/` — it's a live credential store. Never
   type a password or 2FA code into a login flow yourself; the login wizard opens a real,
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
- Run `python doctor.py` before telling a user a platform is or isn't connected.
- Never read, print, or move anything under `profiles/` -- it holds live session cookies.
- Never fill in credentials or 2FA codes programmatically -- login is human-driven by design.
- Default to `--dry-run` before any real publish; default to private/draft visibility unless the
  user explicitly asks to go live.
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
python doctor.py                                  # what's connected, what isn't
python -m auth.login_wizard --platform x          # connect a platform (browser-based ones)
python -m auth.setup_youtube_oauth                # connect YouTube (OAuth, one-time)
python -m auth.publish_x "text" --dry-run          # validate before a real post
```

Full detail: [README.md](README.md) · [CLAUDE.md](CLAUDE.md) · [ROADMAP.md](ROADMAP.md)
