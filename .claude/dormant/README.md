# Dormant material

Files here are **not deleted, not advertised, and not auto-discovered** as Claude Code skills.
They're moved out of `.claude/skills/` specifically so they stop appearing in skill discovery and
stop being offered to an agent as something this beta currently supports.

## Why these specific files

For `v0.1.0-beta.2`, X (Twitter) is not presented as a supported platform in this release (see the
project's own README and ROADMAP for why). `auth/publish_x.py` and the underlying login machinery
in `auth/platforms.py` / `auth/login_wizard.py` are untouched and still fully functional -- this is
a documentation-and-discovery change, not a code removal. If X support is reinstated in a future
release, moving these files back to `.claude/skills/` (and re-adding the references removed from
`AGENTS.md`, `README.md`, etc.) is the whole job.

- `onboard-x/SKILL.md` -- the X-specific setup-from-scratch flow (login through a verified post).
- `twitter.md` -- X-specific publishing notes (character-limit weighting, alt-text handling, reply
  demotion, etc.), written for an agent driving `auth/publish_x.py`.
- `multi-platform-post.md`, `post-feature.md`, `post-offthecuff.md`, `post-quick.md` -- content
  strategy playbooks that treat X as a co-equal default platform alongside Bluesky/LinkedIn/
  Instagram/YouTube. These were already unreferenced by any currently-discoverable skill before
  this move (confirmed by search); moving them here doesn't break any live cross-reference from an
  active skill. They may contain internal links to each other or to `twitter.md` that go stale now
  that everything's in one flat directory -- that's expected and low-stakes, since nothing outside
  this folder points to them.
- `x-troubleshooting-symptoms.md` -- two X-specific rows ("Symptom D1" and "Symptom K") relocated
  out of `.claude/skills/post-troubleshooting.md`, which otherwise stayed in place (see below).
  Confirmed unreferenced elsewhere by number before moving.

## What was NOT moved

- `post-troubleshooting.md` and `.claude/skills/bluesky.md` stayed in `.claude/skills/` because
  they're actively referenced by `onboard-instagram` and `onboard-bluesky` respectively, for
  content that has nothing to do with X. Their X-specific passages were relocated or edited in
  place instead of moving the whole file -- `post-troubleshooting.md`'s X-only symptom rows moved
  to `x-troubleshooting-symptoms.md` above, and its one mixed-platform row (character limits) had
  only its X-specific clause trimmed, keeping the Bluesky/LinkedIn parts intact. `bluesky.md`'s one
  X-comparison sentence was reworded rather than removed outright, since the sentence's actual
  content (hashtag usage on Bluesky) is about Bluesky, not X.
- `auth/publish_x.py`, `auth/platforms.py`, `auth/login_wizard.py` -- untouched by design; see
  above.
