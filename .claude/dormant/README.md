# Dormant material

Files here are **not deleted, not advertised, and not auto-discovered** as Claude Code skills.
They're kept out of `.claude/skills/` specifically so they stay out of skill discovery.

## What's here now

X (Twitter) is a supported platform again -- see `.claude/skills/onboard-x/SKILL.md`,
`.claude/skills/publish-x/SKILL.md`, and the X-specific rows in
`.claude/skills/troubleshoot-publishing/SKILL.md` for the current, active, code-verified guidance.
The X-specific material that used to live here (`onboard-x/SKILL.md`, `twitter.md`,
`x-troubleshooting-symptoms.md`) has been folded into those active skills and removed from this
directory, so there is only one version of any given piece of X guidance and it can't go stale
against `auth/publish_x.py` unnoticed.

What remains dormant is the old **content-strategy playbooks**, which treat X as a co-equal
default platform alongside Bluesky/LinkedIn/Instagram/YouTube as part of a specific posting
rotation:

- `multi-platform-post.md`, `post-feature.md`, `post-offthecuff.md`, `post-quick.md` -- content
  strategy playbooks built around a particular multi-platform rotation strategy, not general X
  mechanics. They're left dormant deliberately: reactivating them would mean either imposing that
  specific strategy on every user or rebuilding them against the current simplified skill format,
  neither of which is part of reinstating X support itself. Revisit these on their own merits if
  that content strategy is wanted later.

## What was NOT moved

`auth/publish_x.py`, `auth/platforms.py`, `auth/login_wizard.py` -- untouched throughout; X was
never removed from the code, only from the advertised/discoverable documentation surface, and that
documentation gap is now closed.
