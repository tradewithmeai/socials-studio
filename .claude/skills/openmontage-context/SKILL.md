---
name: openmontage-context
description: Read an OpenMontage project's own artifacts (script, brief, render report) before writing publish copy for its video, so captions/descriptions are grounded in the video's actual content, tone and audience instead of guessed from the filename. Use whenever drafting or suggesting copy for a video that came from OpenMontage.
---

# OpenMontage context

## When to use it

Whenever drafting or suggesting publish copy for a video that came from OpenMontage. Not needed
for a video from any other source.

## Instructions

An OpenMontage project lives at `<OpenMontage repo>/projects/<project-name>/`. If not already
pointed at a specific project, ask the user which one, or find the project whose
`renders/final.mp4` matches the video in question. Read whatever of the following actually exists
-- different pipelines produce different artifact shapes, so this isn't a fixed schema:

1. **`project.json`** -- title and `pipeline_type`, for fast orientation.
2. **`artifacts/script.json`** -- the ground truth of what the video says: `title`,
   `total_duration_seconds`, `voice_performance.performance_intent`/`pacing_profile`/
   `energy_curve` for tone and delivery, and `sections[].label`/`sections[].text` for the actual
   narration.
3. **`artifacts/brief.json`** or **`artifacts/research_brief.json`** (whichever exists) --
   `hook`, `core_message`, `cta`, `tone`, `target_audience`, `key_points`, or a `research_summary`/
   `landscape` for research-first pipelines.
4. **`artifacts/render_report.json`** -- the real output specs (`outputs[].duration_seconds`,
   `resolution`, `fps`, `platform_target`) -- check this against the platform you're about to
   publish to (e.g. a 16:9 explainer aimed at `platform_target: "youtube"` needs cropping or
   re-export before it fits a vertical-first platform).

Write copy that echoes the video's actual hook, tone, and audience from these files, rather than
inventing framing from scratch or guessing from the filename.

## Guardrails

Read-only: this skill never touches credentials, browser sessions, or the publish path.

## Known failures and recovery

If the artifacts are missing, thin, or ambiguous, ask the user rather than guess -- or, if
OpenMontage's own Claude instance is running locally in that repo, ask it directly.
