# Socials Studio for OpenMontage users

Socials Studio is an independent community project. **It is not affiliated with, maintained by,
or endorsed by [OpenMontage](https://github.com/calesthio/OpenMontage).** This guide explains how
the two fit together in practice -- see [README.md](README.md) for everything else about Socials
Studio itself.

## What Socials Studio adds after a render

[OpenMontage](https://github.com/calesthio/OpenMontage) renders the video. That's where its job
ends and Socials Studio's begins -- and it's more than a fixed review-then-publish step. Ask
Claude Code to turn an OpenMontage render into a whole campaign: platform-specific posts for
several destinations, coordinated with each other, reviewed with you, and published once you've
explicitly confirmed. Claude can also request media from OpenMontage (or another available
agentic video application) as part of preparing that campaign in the first place, not only
consume a render that already exists. The single-video, single-post path (review the title,
description, and visibility, validate, publish) is still there when that's all you want.

## The current workflow: file-based compatibility

Socials Studio has no dependency on OpenMontage's code and doesn't call into it. It works with a
finished video file from OpenMontage the exact same way it works with a finished video file from
anywhere else -- point it at the file, review the details, publish. There is no live handoff, no
shared process, no API between the two projects today.

## Safe validate-first example

Every publisher validates by default and touches nothing -- no browser, no API call -- until you
explicitly confirm:

```bash
# Validates only. This is the default even with no flags at all.
python -m auth.publish_youtube path/to/openmontage-render.mp4 --title "My video"

# Only this actually uploads:
python -m auth.publish_youtube path/to/openmontage-render.mp4 --title "My video" \
    --description "..." --visibility private \
    --not-made-for-kids --acknowledge-upload-terms --confirm-publish
```

See [README.md's Publishing safety section](README.md#publishing-safety) for why this is the
default everywhere, not just for YouTube.

## Using OpenMontage's own context to write better copy

OpenMontage's pipeline writes plain JSON artifacts alongside a render -- the script that was
actually used, the intended tone and audience, the real output resolution and duration. If you're
using Claude Code, the `openmontage-context` skill
(`.claude/skills/openmontage-context/SKILL.md`) reads whatever of that is actually present for a
given project, in roughly this order of usefulness:

- `project.json` -- title and pipeline type, for fast orientation.
- `artifacts/script.json` -- the ground truth of what the video actually says: the narration
  section by section, and the intended delivery style (`voice_performance`).
- `artifacts/brief.json` or `artifacts/research_brief.json` (whichever exists) -- the hook, core
  message, tone, and target audience behind the video, where present.
- `artifacts/render_report.json` -- the real, final output specs (duration, resolution,
  `platform_target`), worth checking against whatever you're about to publish it as.

**This is deliberately not a fixed schema.** Different OpenMontage pipelines produce different
artifact shapes -- an animated-explainer project looks different from a custom one -- and
OpenMontage doesn't guarantee any of these files exist for a given project. The skill reads what's
actually there and uses what's useful, rather than requiring a specific structure. The result:
copy that echoes the video's real hook and tone, instead of being guessed from the filename.

## Supported publishing destinations

YouTube, Bluesky, LinkedIn, and Instagram -- see
[README.md's Supported platforms table](README.md#supported-platforms) for exactly what each one
supports (text, image, video) and how authentication works for it.

## Current limitations

- No live integration between the two projects' code -- this is file-based compatibility, reviewed
  and confirmed through Claude Code each time, not an unattended pipeline that goes from an
  OpenMontage render straight to a live publish with no human in the loop. That's a deliberate
  safety property, not a missing feature -- see README.md's
  ["what isn't available yet"](README.md#what-isnt-available-yet) for the two genuine gaps.
- The `openmontage-context` skill only helps if you're using Claude Code and the OpenMontage
  project's artifacts are present and findable; it degrades gracefully (asks, or works from just
  the video file) when they aren't.
- Bluesky, LinkedIn, and Instagram publish via browser automation against your own logged-in
  session, not an official API -- see [SECURITY.md](SECURITY.md) for the risk tradeoffs of that
  approach and why it's what this project does today.
- This project has not been accepted, merged, or endorsed by OpenMontage in any way. Any future
  relationship is described below, and doesn't exist yet.

## A possible future adapter -- not built, not proposed yet

[ROADMAP.md](ROADMAP.md) tracks the idea of a future OpenMontage `tools/publishers/` adapter file,
contributed as an ordinary third-party pull request -- not an official integration or partnership.
Socials Studio remains the standalone engine either way, whether or not that adapter is ever
built or accepted. Nothing described in this section exists today.

## Links

- [OpenMontage on GitHub](https://github.com/calesthio/OpenMontage)
- [Socials Studio on GitHub](https://github.com/tradewithmeai/socials-studio)
- [Socials Studio README](README.md)
- [Socials Studio ROADMAP](ROADMAP.md)
