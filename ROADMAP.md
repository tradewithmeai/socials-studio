# Roadmap

This is a public beta. Direction here is driven by real feedback, not a fixed spec -- see
[CONTRIBUTING.md](CONTRIBUTING.md) for how to weigh in. Substantive feedback will be considered as
this develops; that's not a promise every request gets built.

## Now (v0.1.0-beta.2)

- Login wizard: X, Bluesky, LinkedIn, Instagram.
- Publish: YouTube, X, Bluesky, LinkedIn, Instagram.
- Safe-by-default: every publisher validates only unless `--confirm-publish` is explicitly
  passed; `--dry-run` remains available as an explicit way to request the same thing.

## Not available yet (the two genuine gaps)

These are the only capabilities that are actually missing today, not just unpackaged:

- **Live streaming.**
- **Unattended or scheduled automated publishing**, as a packaged, supported workflow. Claude Code
  can already prepare and execute a multi-post, multi-platform campaign in one session with your
  review and explicit `--confirm-publish` at each consequential step -- what's missing is
  publication that continues without you reviewing and authorising it through that gate. See
  [README.md](README.md#what-isnt-available-yet).

## In progress: guided installers (v0.1.0-beta.3)

Windows, macOS, and Linux installers so a user with a Claude subscription but no GitHub, Git, or
Python experience can get set up -- see `installer/` and the README's [Get started](README.md#get-started)
section. The Windows installer is built and reviewed but not yet run end-to-end by a second
person; macOS and Linux are built by CI but **not yet verified on real hardware** -- see the
README's Testing status before relying on either.

## Next, roughly in order

- Package proven agent-led workflows (see the two gaps above, once a working pattern exists) into
  dedicated, tested skills -- more discoverable and repeatable, not a new capability boundary.
- Evaluate migrating X, Bluesky, LinkedIn, and/or Instagram from browser automation to their
  official publishing APIs (X's API v2, Bluesky's `createPost`, LinkedIn's Posts API, Instagram's
  Content Publishing API) -- each exists and is documented; what's unevaluated is the access requirements
  (developer app review, account type requirements, rate limits) and feature-coverage tradeoff
  against what the current browser-driven publishers do. See [SECURITY.md](SECURITY.md) for the
  risk rationale behind considering this at all.
- An MCP server exposing these primitives as structured, typed tools -- a discoverability and
  ergonomics improvement for agents/interfaces that work better with tool calls than shell
  commands, not something that newly unlocks agent-driven use (Claude Code already operates this
  repository conversationally today).
- Multi-agent support beyond Claude Code: OpenCode and Codex are the two firm targets; a couple
  more slots open after that.
- A possible future OpenMontage `tools/publishers/` adapter file, contributed as an ordinary
  third-party pull request (not an official integration or partnership) -- this repo remains the
  standalone engine either way, and doesn't exist as an adapter yet.

## Not planned right now

- Its own hosted service / SaaS layer. This is a local tool you run yourself, on your own logged-in
  session, on your own machine.
