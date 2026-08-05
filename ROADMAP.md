# Roadmap

This is a public beta. Direction here is driven by real feedback, not a fixed spec -- see
[CONTRIBUTING.md](CONTRIBUTING.md) for how to weigh in. Substantive feedback will be considered as
this develops; that's not a promise every request gets built.

## Now (v0.1.0-beta.1)

- Login wizard: TikTok, Instagram, YouTube, X.
- Publish: YouTube, TikTok, Instagram, X.
- Safe-by-default: `--dry-run` on publish, private/draft default where supported.

## Next, roughly in order

- Publish support for Bluesky.
- An MCP server wrapping login + publish as proper agent tools, so this isn't CLI-only.
- Multi-agent support beyond Claude Code: OpenCode and Codex are the two firm targets; a couple
  more slots open after that.
- A possible future OpenMontage `tools/publishers/` adapter file, contributed as an ordinary
  third-party pull request (not an official integration or partnership) -- this repo remains the
  standalone engine either way, and doesn't exist as an adapter yet.

## Not planned right now

- Its own hosted service / SaaS layer. This is a local tool you run yourself, on your own logged-in
  session, on your own machine.
