# Socials Studio v0.1.0-beta.2

Socials Studio is a **local-first, agentic social media publishing application**, operated
through [Claude Code](https://claude.com/claude-code). Clone the repository, run `claude`, and
describe what you want -- an idea, a campaign brief, or finished media. Claude creates
platform-specific posts, coordinates them into a multi-platform campaign, reviews the result with
you, and publishes approved posts once you explicitly confirm.

## Supported platforms

**YouTube, X (Twitter), Bluesky, LinkedIn, and Instagram.**

- YouTube publishes through the official Data API via OAuth -- no browser automation at all,
  since Google blocks automated sign-in outright.
- X, Bluesky, LinkedIn, and Instagram each publish through a saved, human-created browser session
  -- you log in yourself, once, in a real Chrome window; Claude never touches credentials.

## What it does

- Creates a single platform-specific post, or coordinates a whole multi-platform campaign from
  one idea or one piece of media.
- Works with [OpenMontage](https://github.com/calesthio/OpenMontage)-rendered video and reads its
  script/brief/render-report artifacts to ground the copy it writes -- and works exactly the same
  way with a finished video from anywhere else, or with no video at all. Socials Studio is an
  independent project, not affiliated with, maintained by, or endorsed by OpenMontage.
- Validates every post by default and touches no browser, API, or network call to a platform
  until you explicitly pass `--confirm-publish`.

## What isn't included yet

- Live streaming.
- Unattended or scheduled automated publishing, as a packaged workflow -- Claude can already run
  a full multi-post campaign in one session with your review and confirmation at each
  consequential step; what's missing is publication that continues without that review.

## A note on reliability

X, Bluesky, LinkedIn, and Instagram publish through browser automation against real, live
platform UIs, not official APIs -- when one of those platforms changes its interface, the
matching publisher may need maintenance. YouTube's official Data API path doesn't carry this
risk.

## License and testing

Open source under the [MIT License](LICENSE). This beta has been developed and tested with
Claude Code; other coding agents, operating systems, and configurations haven't been validated
yet -- reports from real use are welcome either way, pass or fail.

See [CHANGELOG.md](CHANGELOG.md) for the complete, detailed change history.
