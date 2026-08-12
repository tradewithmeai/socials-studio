# Roadmap

This is a public beta. Direction here is driven by real feedback, not a fixed spec -- see
[CONTRIBUTING.md](CONTRIBUTING.md) for how to weigh in. Substantive feedback will be considered as
this develops; that's not a promise every request gets built.

## Now (v0.1.0-beta.2)

- Login wizard: Bluesky, LinkedIn, Instagram.
- Publish: YouTube, Bluesky, LinkedIn, Instagram.
- Safe-by-default: every publisher validates only unless `--confirm-publish` is explicitly
  passed; `--dry-run` remains available as an explicit way to request the same thing.
- X (Twitter) is not presented as a supported platform in this release -- see
  [CHANGELOG.md](CHANGELOG.md). The implementation (`auth/publish_x.py`) is untouched and
  functional; its future is undecided.

## Next, roughly in order

- Evaluate migrating Bluesky, LinkedIn, and/or Instagram from browser automation to their
  official publishing APIs (Bluesky's `createPost`, LinkedIn's Posts API, Instagram's Content
  Publishing API) -- each exists and is documented; what's unevaluated is the access requirements
  (developer app review, account type requirements, rate limits) and feature-coverage tradeoff
  against what the current browser-driven publishers do. See [SECURITY.md](SECURITY.md) for the
  risk rationale behind considering this at all.
- An MCP server wrapping login + publish as proper agent tools, so this isn't CLI-only.
- Multi-agent support beyond Claude Code: OpenCode and Codex are the two firm targets; a couple
  more slots open after that.
- A possible future OpenMontage `tools/publishers/` adapter file, contributed as an ordinary
  third-party pull request (not an official integration or partnership) -- this repo remains the
  standalone engine either way, and doesn't exist as an adapter yet.

## Not planned right now

- Its own hosted service / SaaS layer. This is a local tool you run yourself, on your own logged-in
  session, on your own machine.
