# Release checklist

Steps to actually ship a tagged release. Nothing here should be run automatically or by an
agent without the maintainer's explicit go-ahead for each step -- tagging and publishing a
release are one-way, public actions.

## Before tagging

1. `git status --short` -- confirm the working tree is clean and every intended change is
   committed on the release branch.
2. Run the full test suite: `pytest` (or `python -m pytest`). All tests must pass.
3. Compile-check every Python file: `python -m compileall -q auth doctor.py tests`. No output
   means no syntax errors.
4. Confirm no `profiles/` contents, cached credentials, or browser artifacts are staged:
   `git status --short | grep -i profiles` should print nothing; `python doctor.py` should report
   "Session data is not committed."
5. Search for stale version references: `grep -rn "beta\.1" --include="*.md" --include="*.html" .`
   and confirm every hit is either historical (CHANGELOG's own beta.1 section) or intentional.
6. Search for reintroduced public claims that X is supported:
   `grep -rniE "\bx\b|twitter" README.md docs/index.html ROADMAP.md AGENTS.md CLAUDE.md .github/ISSUE_TEMPLATE/`
   and confirm every hit is either the intentional "not supported" disclosure or unrelated noise
   (e.g. CSS `overflow-x`, the `twitter:card` meta tag standard).
7. Update `CHANGELOG.md`'s `(unreleased)` heading to the real release date.
8. Update the version string in `README.md`'s beta line and `ROADMAP.md`'s `## Now` heading if
   they don't already match the version being tagged.

## Tagging and publishing

Run these only after the maintainer has reviewed and approved the diff:

```bash
git tag -a v0.1.0-beta.2 -m "v0.1.0-beta.2"
git push origin v0.1.0-beta.2
gh release create v0.1.0-beta.2 --title "Socials Studio v0.1.0-beta.2" --notes-file CHANGELOG.md
```

(`gh release create` with `--notes-file` will include the whole changelog file; trim to just the
new section first if that's not what you want in the release body.)

## After publishing

1. Update `docs/index.html`'s "Get the public beta" link from the releases listing to the
   specific new tag: `https://github.com/tradewithmeai/socials-studio/releases/tag/v0.1.0-beta.2`.
2. Commit and push that link change.
3. Confirm the live GitHub Pages site (`https://tradewithmeai.github.io/socials-studio/`) reflects
   the change within a few minutes of the push.
4. Post/announce wherever makes sense -- this step is manual and outside this repo's scope.
