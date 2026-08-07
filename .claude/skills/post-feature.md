# Feature-Piece Post Skill (detailed, CTA-driven)

A **writing** skill for the bigger posts: project announcements, tester-recruitment, milestones. Longer
and more structured than the off-the-cuff skill. Produces copy (and a video brief where relevant), then
hands to the platform skills to publish. Complements the platform skills.

**Platforms:** Instagram, Twitter, Bluesky, YouTube — and **LinkedIn IS allowed here** (feature pieces
are announcements/milestones, which is the one thing LinkedIn should get). Video optional and, because
Project Bright has no audio yet, **any video must work silently** (on-screen text carries it).

The planned feature campaigns already live in `campaigns/<project>/plan.md` — this skill is how you
write/execute them.

---

## When to use which skill

- **Off-the-cuff** (`post-offthecuff.md`): "here's a wild thing that happened today", short, Bluesky+Twitter.
- **Feature piece** (this): "here's a project — come test it", detailed, clear CTA, all platforms + LinkedIn.

## Structure

```
<Hook — concrete, specific; a number or a vivid one-liner about the project>

<2–4 lines: what it is + what makes it interesting, in plain language>

<The ask — ONE clear CTA: play / apply / try it / read the report>
<link>
<optional: how to give feedback / where the community is>
#relevant #tags
```

## Rules

1. **One clear CTA.** Feature pieces exist to recruit testers/users — end on a single ask, not three.
2. **Lead with a concrete specific**, not "Excited to announce…". Name brands/models (reach).
3. **Tailor per platform** — don't fan identical copy everywhere. Long caption for IG/LinkedIn; tighter
   for Bluesky/Twitter (respect ≤280 / ≤300). Provide each variant.
4. **Video = silent.** On-screen text/captions must carry the story; never rely on voiceover.
5. **Made-with-Project-Bright videos double as a live test of Project Bright** — lean into that when true.
6. **Honesty in the pitch.** Real state of the project (e.g. "early but playable", "no audio yet").
7. **Sign-off:** show the user final copy AND the rendered video before any publish. Never infer go.

## Workflow

1. Open the project's `campaigns/<project>/plan.md` — it has goal, audience, draft copy, video brief.
2. Fill any `[NEED FROM YOU]` gaps (URLs, CTA route) with the user.
3. Write per-platform copy variants + finalise the (silent) video brief.
4. If a video is needed: produce it (Project Bright, or Remotion) — publish the quick Bluesky/Twitter
   text while it renders, drop the video posts (YouTube/IG) when ready.
5. Show the user copy + video for explicit sign-off, then hand to the platform skills to publish.
6. Log to `post_schedule.json`; capture organic engagers via `engagers.py`.
