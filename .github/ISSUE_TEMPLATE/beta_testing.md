---
name: Beta test report
about: You ran this on your own setup -- tell us what happened, pass or fail
title: "[beta] "
labels: beta-testing
---

This is a public beta. Reports on **any** outcome (worked or didn't) are useful — this template
is for structured pass/fail reports, separate from bug reports for something clearly broken.

**Configuration**
- OS:
- Python version:
- Coding agent (Claude Code / OpenCode / Codex / other):
- Platform tested (YouTube / X / Bluesky / LinkedIn / Instagram):
- Video source (OpenMontage-rendered / other):

**What you ran**
- [ ] Installation (`pip install -r requirements.txt`, `playwright install chrome`) -- worked?
- [ ] `python -m auth.login_wizard --platform ...` -- authentication worked?
- [ ] `python -m auth.publish_youtube ... --dry-run`
- [ ] `python -m auth.publish_youtube ...` (live) -- YouTube publication succeeded?
- [ ] Something else:

**Outcome**
Did it work end to end? Where (if anywhere) did it break or behave unexpectedly? If you tested
with OpenMontage-rendered output specifically, say so and note anything that behaved differently
from a non-OpenMontage file.

**Was anything in the docs unclear or wrong for your setup?**

**What would make this genuinely useful for your actual workflow?**
