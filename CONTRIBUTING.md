# Contributing

This is an early public beta maintained by one person. Contributions are welcome, but please open
an issue before a large PR so we don't cross wires on direction.

## Reporting

- **Something broke** -> Bug report template.
- **Want a platform/feature added** -> Feature request template.
- **You ran this on your own setup** -> Beta test report template (pass or fail, both useful).
- **Broader feedback, ideas, "does this even make sense as a product"** -> GitHub Discussions.

## Development setup

```bash
git clone https://github.com/tradewithmeai/socials-studio.git
cd socials-studio
pip install -r requirements.txt
python -m playwright install chrome
```

`profiles/` (saved login sessions) is gitignored -- never commit it. Never commit `.env` files,
tokens, or anything under a directory a `.gitignore` rule excludes; if you're not sure whether
something is sensitive, ask in the PR rather than pushing it.

## Code style

Match what's already there: small, direct, commented only where the *why* isn't obvious from the
code itself. Browser-automation selectors are best-effort against live platform UIs by nature --
if you fix a broken selector, leave a one-line comment noting the date and what changed, the way
the rest of the codebase does. This project inherited that convention from the private automation
project it grew out of, where that log became genuinely load-bearing over time.

## Pull requests

- Keep them focused -- one platform/fix/feature per PR.
- If you're touching a live-platform-facing flow (login or publish), say in the PR description
  whether you actually ran it against a live account or only reviewed/dry-ran it. That distinction
  matters a lot for a project like this.
