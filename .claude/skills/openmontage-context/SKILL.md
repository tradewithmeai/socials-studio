---
name: openmontage-context
description: Read an OpenMontage project's own artifacts (script, brief, render report) before writing publish copy for its video, so captions/descriptions are grounded in the video's actual content, tone and audience instead of guessed from the filename. Use whenever drafting or suggesting copy for a video that came from OpenMontage.
---

# OpenMontage context

See [OPENMONTAGE.md](../../../OPENMONTAGE.md) at the repo root for the human-facing version of
this same guidance, including the independent-project relationship between the two repos, if a
user asks about that rather than just wanting copy written.

OpenMontage renders a video through a pipeline of stages, and each stage writes a plain JSON
artifact -- so the video's actual script, intended tone, target audience, and even its real
duration and resolution are all sitting on disk next to the render, not something you need to
infer from the video itself or the filename. This skill is just: read those files before you
write copy, so what you write matches what the video actually is.

This is deliberately lightweight -- not a parser, not a schema validator. Different OpenMontage
pipelines produce slightly different artifact shapes (an `animated-explainer` project looks
different from a custom one); read what's there and use what's useful, rather than expecting a
fixed structure.

## Finding the project

An OpenMontage project lives at `<OpenMontage repo>/projects/<project-name>/`. If you're not
already pointed at a specific project folder, ask the user which one, or look for a project
whose `renders/final.mp4` matches the video they're asking about.

## What to read, in order of usefulness

1. **`project.json`** -- title and `pipeline_type`. Fast orientation, nothing more.

2. **`artifacts/script.json`** -- the ground truth of what the video actually says. This is the
   most reliable file here because it's not a proposal or an option that might have been
   rejected -- it's what got rendered. Pull:
   - `title`, `total_duration_seconds`
   - `voice_performance.performance_intent`, `pacing_profile`, `energy_curve` -- the intended
     tone and delivery style, in the pipeline's own words
   - `sections[].label` and `sections[].text` -- the actual narration, section by section

3. **`artifacts/brief.json`** or **`artifacts/research_brief.json`** (whichever exists --
   pipelines vary) -- the positioning behind the video, where present:
   - `hook`, `core_message`, `cta`, `tone`, `target_audience`, `key_points`
   - Research-first pipelines may instead have a `research_summary` and a `landscape` of
     existing content instead of these fields -- that's fine, use whatever's actually there.

4. **`artifacts/render_report.json`** -- the real, final output: `outputs[].duration_seconds`,
   `resolution`, `fps`, `platform_target`, and the render's own file `path`. Worth checking this
   against whatever you're about to publish it as -- e.g. a 90-second 16:9 explainer aimed at
   `platform_target: "youtube"` is a straightforward YouTube upload, but flag it before treating
   the same file as a good fit for a vertical-first platform without cropping or re-export.

## Using it

Once you've read these, write platform copy that echoes the video's actual hook, tone, and
audience rather than inventing new framing from scratch. A caption for Bluesky should sound like
it came from the same voice as `performance_intent`; a description shouldn't claim an audience or
angle the `brief`/`research_brief` didn't set out to reach.

If the artifacts are ambiguous, thin, or you're genuinely unsure what a project is going for, and
OpenMontage's own Claude instance is running locally in that repo, it's reasonable to just ask it
directly rather than guess from partial files -- it has the full working context this skill only
gives you a snapshot of.
