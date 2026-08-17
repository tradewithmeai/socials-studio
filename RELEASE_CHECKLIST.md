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
6. Confirm X (Twitter) is listed consistently as a supported platform, not stale "not supported"
   language reappearing from an old branch or draft:
   `grep -rniE "\bx\b|twitter" README.md docs/index.html ROADMAP.md AGENTS.md CLAUDE.md .github/ISSUE_TEMPLATE/`
   and confirm every hit either lists X alongside the other supported platforms or is unrelated
   noise (e.g. CSS `overflow-x`, the `twitter:card` meta tag standard) -- flag anything that still
   says X isn't supported.
7. Update `CHANGELOG.md`'s `(unreleased)` heading to the real release date.
8. Update the version string in `README.md`'s beta line and `ROADMAP.md`'s `## Now` heading if
   they don't already match the version being tagged.
9. Confirm `RELEASE_NOTES.md` names all five supported platforms individually and contains
   neither `TikTok` nor any claim that this is a CLI-only tool:
   ```bash
   for platform in "YouTube" "X (Twitter)" "Bluesky" "LinkedIn" "Instagram"; do
     grep -Fq "$platform" RELEASE_NOTES.md || echo "MISSING: $platform"
   done
   ```
   should print nothing (no output means every platform was found), and
   `grep -i "tiktok\|CLI-only\|CLI only\|command-line tool\b" RELEASE_NOTES.md` should print
   nothing.

## Tagging and publishing

Run these only after the maintainer has reviewed and approved the diff:

```bash
git tag -a v0.1.0-beta.2 -m "v0.1.0-beta.2"
git push origin v0.1.0-beta.2
gh release create v0.1.0-beta.2 --title "Socials Studio v0.1.0-beta.2" --notes-file RELEASE_NOTES.md --prerelease
```

`gh release create` now points `--notes-file` at `RELEASE_NOTES.md` -- the short, curated
summary meant for a release body -- rather than the entire `CHANGELOG.md`, which stays linked
from the release notes for anyone who wants the full detail. `--prerelease` matches how
`v0.1.0-beta.1` is marked; keep it for every beta tag until this leaves beta.

## After publishing

1. Update `docs/index.html`'s "Get the public beta" link from the releases listing to the
   specific new tag: `https://github.com/tradewithmeai/socials-studio/releases/tag/v0.1.0-beta.2`.
2. Commit and push that link change.
3. Confirm the live GitHub Pages site (`https://tradewithmeai.github.io/socials-studio/`) reflects
   the change within a few minutes of the push.
4. Post/announce wherever makes sense -- this step is manual and outside this repo's scope.
