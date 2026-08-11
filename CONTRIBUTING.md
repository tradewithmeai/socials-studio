# Contributing

This is an early public beta maintained by one person. Contributions are welcome, but please open
an issue before a large PR so we don't cross wires on direction. Participation in this project is
governed by the [Code of Conduct](CODE_OF_CONDUCT.md).

## Reporting

- **Something broke** -> Bug report template.
- **Want a platform/feature added** -> Feature request template.
- **You ran this on your own setup** -> Beta test report template (pass or fail, both useful).
- **Broader feedback, ideas, "does this even make sense as a product"** -> GitHub Discussions.

## Development setup

```bash
git clone https://github.com/tradewithmeai/socials-studio.git
cd socials-studio
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1   |   Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
python -m playwright install chrome
```

`profiles/` (saved login sessions) is gitignored -- never commit it. Never commit `.env` files,
tokens, or anything under a directory a `.gitignore` rule excludes; if you're not sure whether
something is sensitive, ask in the PR rather than pushing it.

## Running the tests

```bash
pytest
```

The test suite (`tests/`) never launches a real browser, calls a live platform API, or needs
credentials -- it's safe to run freely, and CI runs it on every push and PR (see
`.github/workflows/ci.yml`). If you're adding a new publisher or changing safety-gate behavior in
an existing one, add or update tests alongside the code -- see `tests/test_publish_safety.py` and
`tests/test_publishers_safe_defaults.py` for the existing pattern.

## Code style

Match what's already there: small, direct, commented only where the *why* isn't obvious from the
code itself. Browser-automation selectors are best-effort against live platform UIs by nature --
if you fix a broken selector, leave a one-line comment noting the date and what changed, the way
the rest of the codebase does. This project inherited that convention from the private automation
project it grew out of, where that log became genuinely load-bearing over time.

Every publisher is safe by default -- see `auth/publish_safety.py`. If you're adding a new
platform's publish flow, use `should_publish()` from that module for the confirm-publish gate
rather than reimplementing the dry-run logic; match the existing pattern otherwise: real Chrome
(not bundled Chromium), safe defaults, and be upfront in your PR about whether you actually ran it
against a live account.

## Pull requests

- Keep them focused -- one platform/fix/feature per PR.
- If you're touching a live-platform-facing flow (login or publish), say in the PR description
  whether you actually ran it against a live account or only reviewed/dry-ran it. That distinction
  matters a lot for a project like this.
- If your change touches CLI flags, safety behavior, or scopes for any publisher, update the
  corresponding test file and the relevant `.claude/skills/onboard-*` doc in the same PR -- this
  project has been bitten before by docs and code drifting apart.
