## What this changes

<!-- One or two sentences. What problem does this solve, or what feature does it add? -->

## Did you run this against a live account?

<!-- Say explicitly whether you actually ran this against a real platform account, or only
     reviewed/dry-ran it. This matters a lot for a project like this -- see CONTRIBUTING.md. -->

- [ ] Ran against a live account (which platform: ____)
- [ ] Reviewed / dry-ran only, not tested live
- [ ] Not applicable (docs-only, tests-only, etc.)

## Checklist

- [ ] `pytest` passes locally
- [ ] `python -m compileall -q auth doctor.py tests` reports no errors
- [ ] If this touches CLI flags, safety behavior, or scopes for any publisher: updated the
      corresponding test file and the relevant `.claude/skills/onboard-*` doc
- [ ] If this adds a new platform's publish flow: uses `auth.publish_safety.should_publish` for
      the confirm-publish gate, matches the existing safe-by-default pattern
- [ ] Nothing under `profiles/`, no `.env` files, no tokens or client secrets are staged
      (`git status --short` reviewed before pushing)

## Anything else worth knowing?

<!-- Edge cases, follow-up work, things you're unsure about. -->
