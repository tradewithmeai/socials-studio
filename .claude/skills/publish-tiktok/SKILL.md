---
name: publish-tiktok
description: Prepare, validate, review and publish a video to an already-authorized TikTok account. Use when the user wants to draft, review or upload a TikTok video -- not for first-time OAuth setup (see onboard-tiktok) and not for diagnosing a failed/uncertain publish (see troubleshoot-publishing).
---

# Publish to TikTok

## When to use it

Drafting, reviewing, or uploading a TikTok video to an already-authorized account. Not for
first-time OAuth setup (`onboard-tiktok`) or diagnosing a failed/uncertain publish
(`troubleshoot-publishing`).

## Instructions

```bash
python -m auth.publish_tiktok path/to/video.mp4 --title "..."                  # validates only (default)

python -m auth.publish_tiktok path/to/video.mp4 --title "..." --confirm-publish
```

Requires `python -m auth.setup_tiktok_oauth` to have already been run.

Visibility flags map to TikTok's actual `privacy_level` values: `private` (default) ->
`SELF_ONLY`, `followers` -> `FOLLOWER_OF_CREATOR`, `friends` -> `MUTUAL_FOLLOW_FRIENDS`, `public`
-> `PUBLIC_TO_EVERYONE`. Other flags: `--disable-duet`, `--disable-stitch`, `--disable-comment`,
and `--is-aigc` (TikTok's required disclosure for AI-generated content).

## The unaudited-app reality -- read this before telling a user a post is "live"

Every new TikTok app starts unaudited. Until TikTok's own review team audits and approves it,
**every post is forced to private/self-only regardless of the `--visibility` requested** -- the
API accepts `public` without erroring, then silently downgrades it. This tool prints that reminder
(`UNAUDITED_APP_NOTICE`) on every real-publish attempt and includes it in every dry-run result too
-- do not tell a user their video is publicly live without independently confirming the account
has passed audit.

**The sanctioned workaround**, straight from TikTok's own Content Sharing Guidelines
(https://developers.tiktok.com/doc/content-sharing-guidelines): the account owner can make a
specific post public by hand, afterward, in the TikTok app -- first set the *account* to public
(if it isn't already), then open that *post* and change its own privacy to "Everyone." This is
documented, sanctioned behavior, not a workaround of TikTok's rules -- it's just a manual,
per-post step until the app passes audit. Tell the user this plainly rather than letting them
assume the post is stuck private forever.

## Guardrails

- A real upload requires `--confirm-publish`; without it, this only validates (same shared gate,
  `auth.publish_safety.should_publish`, as every other publisher here).
- `--visibility` defaults to `private`. Only mention `--visibility public` once the user
  understands it is still forced private pre-audit -- see above.
- `--title` is capped at 2,200 UTF-16 code units (TikTok's documented limit) and this tool now
  actually enforces it before publishing -- an over-length title is rejected up front, not only
  by the real API after the video has already uploaded.
- **This tool does not check a creator's own account restrictions before publishing.** A creator
  with e.g. comments disabled globally may reject the default `disable_comment=False` at the API
  level -- see the module docstring's "Known, disclosed gap" section. Confirm this together on a
  live account before assuming every combination of flags will be accepted.
- **Never make multiple real (`--confirm-publish`) attempts back-to-back, even to debug the same
  failure.** Confirmed live 2026-08-18: a burst of real publish attempts against a brand-new
  unaudited developer app was followed by the connected TikTok account being reset entirely (new
  username, zero followers/posts/friends, asked to redo birthdate/photo/bio, no warning email).
  TikTok has not officially confirmed the cause, but the timing matches known anti-abuse
  enforcement and there is no known fix once it happens -- prevention only. Space real attempts
  minutes apart; use `python -m auth.publish_tiktok --check-status <publish_id>` (read-only) to
  check an uncertain result instead of publishing again; and stop to ask the user rather than
  retrying live if a real publish fails or looks wrong. See `onboard-tiktok`'s known failures for
  the full incident.

## Known failures and recovery

- **Post "succeeds" (a `publish_id` comes back) but is invisible to anyone but the account
  owner**: expected pre-audit behavior, not a bug -- see the unaudited-app section above. Confirm
  with the user whether they want the manual per-post public-visibility fix.
- **Upload fails partway through a chunk**: `MIN_CHUNK_SIZE`/`MAX_CHUNK_SIZE` in
  `auth/publish_tiktok.py` (5 MiB / 64 MiB) are confirmed against TikTok's real Media Transfer
  Guide, not guessed -- but chunked upload of a video over 64 MiB has not itself been exercised
  live yet (only the single-chunk, under-64-MiB path has). Treat the first large-video upload as
  still-unverified for that specific path.
- **A publish "succeeds" (a `publish_id` comes back) but the video never appears**: the result's
  own `"status"` field distinguishes this now -- `"published"` means TikTok's status check
  reported `PUBLISH_COMPLETE`, `"processing"` means it hadn't finished yet as of that check (use
  `--check-status` to follow up), and a terminal `FAILED` status raises an error with TikTok's own
  `fail_reason` instead of silently returning either of those. Don't trust a bare `publish_id`
  alone as proof of success.
- **Token expired and refresh fails**: `profiles/tiktok/client_secret.json` must still exist (not
  just `token.json`) for a refresh to succeed -- see `onboard-tiktok`'s known failures.
- **The connected TikTok account gets reset/wiped after several real publish attempts in a short
  window**: see the guardrail above -- do not retry a real publish to "debug" an uncertain TikTok
  result, use `--check-status` or stop and ask instead.
- If a publish fails, looks uncertain, or you suspect a duplicate, use `troubleshoot-publishing`
  rather than retrying blind.
- This integration follows TikTok's publicly documented Content Posting API and has now been
  exercised against a live account (chunking and the unaudited-account privacy requirement were
  both confirmed and fixed live 2026-08-17), but rapid real-publish testing has since caused an
  account reset (above) -- treat any further real run as high-stakes and throttled, not routine.