---
name: onboard-tiktok
description: Set up TikTok publishing for Socials Studio from scratch (developer app registration through a verified first post). Use when the user wants to connect, set up, or onboard TikTok, or a TikTok publish fails because no token exists yet.
---

# TikTok onboarding

## When to use it

Connecting TikTok for the first time, or a publish fails because no token exists yet. Not for
routine publishing once connected (`publish-tiktok`) or diagnosing a failed/uncertain publish
(`troubleshoot-publishing`).

## Before you start: set expectations

TikTok blocks automated sign-in the same way X/Instagram/LinkedIn/YouTube do, so this is OAuth +
the official Content Posting API, not a Chrome login wizard. More importantly: **every new TikTok
app starts "unaudited."** Until TikTok's own review team audits and approves the app, every post
made through it is forced to private/self-only visibility, no matter what this tool requests.
Tell the user this up front, before they invest time setting up a developer app — the honest
framing is "this can post right away, but only you will see it until TikTok audits the app; making
a specific post public afterward is a manual step in the TikTok app itself" (see
`publish-tiktok`'s guardrails for exactly how). Audit review takes days to weeks and is a TikTok
compliance review, not something this tool can speed up or bypass.

**Do not repeat real (`--confirm-publish`) publish attempts back-to-back.** Confirmed live
2026-08-18: several real publish attempts against a brand-new unaudited developer app, made in
quick succession while debugging an unrelated issue, was followed by the connected TikTok account
being reset entirely — new/changed username, zero followers/posts/friends, asked to redo
birthdate/photo/bio, with no warning or notification email beforehand. TikTok has not confirmed
this diagnosis and there is no official statement tying the two together, but the timing and
pattern match known anti-bot/anti-abuse enforcement, and there is no other explanation on hand.
There is no known recovery once it happens. Treat this as a hard rule, not a suggestion: space out
real TikTok publish attempts by minutes, not seconds; use `python -m auth.publish_tiktok
--check-status <publish_id>` (read-only, does not touch the publish endpoint) to check on an
uncertain result instead of publishing again; and if a real publish fails or looks wrong, stop and
ask the user before trying another real publish rather than iterating live against the API.

## Instructions

1. One-time TikTok for Developers setup (the user does this themselves, in their own browser,
   logged into their own TikTok account):
   - Register an app at https://developers.tiktok.com/.
   - Add the **Content Posting API** product to the app and request the `video.publish` scope.
   - Add a **Login Kit** redirect URI: an absolute HTTPS URL on a domain the user already
     controls (e.g. `https://their-domain.example/tiktok-callback`). It does not need any
     server-side code — it just needs to exist so the browser lands somewhere real after
     approving access, instead of a broken-page error. TikTok requires this be registered in the
     app's Login Kit configuration before it's accepted; it cannot be a bare `localhost` URL like
     Google's desktop OAuth flow allows.
   - Note the app's **Client Key** and **Client Secret** from its Basic Information page.
2. Save those three values as JSON at `profiles/tiktok/client_secret.json` (create the folder if
   needed):
   ```json
   {
     "client_key": "...",
     "client_secret": "...",
     "redirect_uri": "https://their-domain.example/tiktok-callback"
   }
   ```
3. Run setup:
   ```bash
   python -m auth.setup_tiktok_oauth
   ```
   Opens the user's real, non-automated default browser to TikTok's own authorization screen —
   they approve it themselves. TikTok then redirects to the registered redirect_uri with a `code`
   in the address bar; the user copies that **full URL** and pastes it back into the terminal
   when prompted. On success, writes `profiles/tiktok/token.json`.
4. Verify before a real publish:
   ```bash
   python -m auth.publish_tiktok <video.mp4> --title "..." --dry-run
   ```
   Check for `"token_found": true`, and read the unaudited-app note in the result — it's there on
   every dry run too, not just real attempts.
5. First real publish — requires `--confirm-publish`. Visibility defaults to `--visibility
   private` regardless; only mention `--visibility public` once the user understands it will
   still be forced private until the app is audited (see `publish-tiktok`).

## Guardrails

- Never fill in TikTok credentials or approve the consent screen programmatically — the
  authorization page is always completed by the user, in their real, non-automated browser.
- Never read, print, or surface `profiles/tiktok/token.json` or `client_secret.json` contents.
- Set expectations about the unaudited-app restriction BEFORE the user spends time on developer
  app registration, not after their first post turns out invisible to everyone but them.
- Never make multiple real (`--confirm-publish`) publish attempts in quick succession on an
  unaudited app — see the account-reset incident above. Prefer `--check-status` or a longer wait
  over another real publish when a result is uncertain.

## Known failures and recovery

- **Redirect lands on an error/broken page**: the redirect_uri in `client_secret.json` must
  match, character-for-character, what's registered in the app's Login Kit configuration.
  Mismatches are a common first-run failure.
- **Pasted URL rejected ("state" mismatch)**: the user pasted a URL from a stale/previous attempt
  rather than the one from the run currently waiting for input. Re-run the command fresh.
- **Token exchange or refresh fails**: `profiles/tiktok/client_secret.json` is also needed to
  refresh an expired access token later, not just for the initial exchange — if it's moved or
  deleted, refreshing fails even with a valid `refresh_token` on file.
- **Everything "succeeds" but nobody but the user can see the post**: this is the unaudited-app
  behavior working as documented, not a bug — see `publish-tiktok`'s guardrails for the manual
  per-post fix.
- **The account itself gets reset (new username, zero followers/posts/friends, asked to redo
  birthdate/photo/bio) after a burst of real publish attempts**: confirmed live 2026-08-18,
  believed (not officially confirmed by TikTok) to be its anti-abuse system reacting to rapid
  repeated Content Posting API calls on a brand-new unaudited app. There is no known fix or
  recovery for the account once this happens — prevention is the only lever: throttle real
  publish attempts to minutes apart, use `--check-status` instead of re-publishing to check an
  uncertain result, and stop to ask the user rather than retrying live against the API.
- This integration follows TikTok's publicly documented Content Posting API and OAuth flow and has
  now been exercised against a live developer app (chunking and the unaudited-account privacy
  requirement were both confirmed and fixed live 2026-08-17) — but real publishing has since caused
  an account reset (above) and has not been re-verified end-to-end since. Treat any further real
  run with the throttling guardrail above, and report back anything that doesn't match this skill.