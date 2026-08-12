# X-specific troubleshooting symptoms (relocated from post-troubleshooting.md)

Moved here, not deleted, when X (Twitter) was confirmed not to be a supported platform in
v0.1.0-beta.2 -- see `.claude/dormant/README.md` for the general reasoning. These were previously
"Symptom D1" and "Symptom K" in `.claude/skills/post-troubleshooting.md`; that file keeps its
other symptom numbering as-is (D2/D3 etc.) rather than renumbering around the gap.

## Symptom D1 — clicked Post, page moved on, nothing posted (X's alt-text reminder)

| # | Cause | Tell | Fix |
|---|---|---|---|
| D1 | **X's alt-text reminder blocked the submit** | "Don't forget to make your image accessible" | `publish_x.py` handles this by filling in a description. If it recurs, the dialog's buttons changed |

## Symptom K — the post reached almost nobody (X)

Check whether the text **begins with `@handle`**. X classifies that as a *reply*: it skips the Posts
tab and only reaches people following both accounts. Reorder the sentence. This is a reach failure,
not a posting failure, so nothing will look wrong.
