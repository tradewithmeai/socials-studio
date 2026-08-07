# Video Pipeline Skill — operate the campaign filesystem + video bridge

How to run the near-automated studio without re-reading the code. Load this, then use the commands.

## Mental model

- **socials-studio (here)** = marketing brain: campaign planning, platform knowledge, copy, publishing.
- **project-bright** = production: renders the videos. Separate repo. Talks ONLY via two JSON contracts.
- **The loop:** plan in a campaign folder → request multi-output videos → project-bright renders →
  deliveries route back into the campaign folder → publish.

## The pieces (what each owns)

| Thing | What it is |
|---|---|
| `campaigns/<slug>/` | **source of truth** per campaign — `campaign.md` + `posts/<post>.md` + `media/` |
| `campaign.py` | the campaign manager (status / new / show / index / request) |
| `platform_profiles/*.json` | per-platform video-design rules (youtube/instagram/tiktok); the canonical matrix |
| `campaign_packs/<id>/` | reusable brand/intro-outro + marketing defaults; a campaign references one |
| `request_video.py` | emits a **`video_production_request_v1` (v2)** into project-bright (`outputs[]`) |
| `ingest_handoffs.py` | routes delivered `finished_video_publish_v1` media INTO the campaign folder |

## The operating commands (the whole surface)

```bash
# PLAN
py campaign.py new <slug>                 # scaffold campaigns/<slug>/ (campaign.md + posts/01-example.md)
#   then edit campaign.md (status/goal/cta/pack) and posts/<NN>-<slug>.md:
#   per-platform copy (## Copy — <platform>), ## Build guide (shot list), ## Voiceover notes,
#   and the front-matter outputs[] (which platform cuts this post needs).

# SEE WHAT'S READY vs MISSING (copy / build guide / VO / media per post)
py campaign.py status [slug]
py campaign.py show <slug>

# REQUEST the videos (emits the post's outputs[] to project-bright; --dry-run to preview)
py campaign.py request <slug> <post>      # e.g. py campaign.py request yourgov 01-mp-votes

# INGEST deliveries (routes each delivered variant into campaigns/<slug>/media/<post>/<output_id>.mp4
# and updates the post's media map; also refreshes POST_QUEUE.md's BRIDGE block)
py ingest_handoffs.py                      # add --list to route without touching POST_QUEUE

# REGENERATE the cross-campaign index
py campaign.py index                       # writes CAMPAIGNS.md

# NEWS FEED — ingest the day's story feed, decide, draft into the ai-top5 campaign
py news_feed.py [--dry-run]               # https://solvx.uk/api/social-posts.json -> decisions
#   rank->treatment (off-the-cuff/hold/skip), category->platforms, entities->names_to_drop; all 5
#   decisions logged in campaigns/ai-top5/editions/<date>.json; off-the-cuff stories become draft
#   posts (same edition date as the day's video = siblings). Then: write copy, sign-off, publish.

# PROFILES / PACKS (rarely needed — they're referenced, not edited per post)
py platform_profiles.py list | show <id> | validate | new <id>
py campaign_packs.py list | show <id> | validate | new <id>
```

**Publishing** is unchanged: use the platform skills (`twitter.md`/`bluesky.md`/`instagram.md`/
`linkedin.md`/`youtube.md`) with the campaign's media (`campaigns/<slug>/media/<post>/<output_id>.mp4`)
and copy (from `posts/<post>.md`), then log IDs to `post_schedule.json`. Always sign-off first.

## Key facts (so you don't re-derive them)

- **Request v2 = `outputs[]`.** Each output: `output_id`, `role` (hero|spoke|equal), `platform_profile`,
  `platforms[]`, `aspect`, `duration`, `edit.style`. One request → many platform-specific cuts (e.g. a
  long **yt-hero** 16:9 + a snappy **ig-spoke** 9:16 that `promotes` it).
- **`edit.style` ∈ `{full-show, hook-first}`** (the committed enum). Anything else warns and
  project-bright falls back to full-show. New styles are added by agreement.
- **`_profile`** (the resolved platform profile) is injected into each output — project-bright reads it
  off the wire as the render geometry. `platform_profiles/*.json` is the single source; don't duplicate.
- **Delivery threads back** via `request_id` (→ the post) + `output_id` (→ the exact output). `ingest`
  prefers these; falls back to aspect inference (16:9 → yt-hero/YT-TW-BS-LI, 9:16 → ig-spoke/IG-TikTok).
- **Copy lives ONCE** in `posts/<post>.md`. **Media** is gitignored under `campaigns/<slug>/media/`.
- **project-bright authors per-output VO** (a spoke is NOT a trim of the hero); our `## Voiceover notes`
  is campaign-level guidance only. Optional per-output `edit.vo_hint` steers intent.
- Contract accepted 2026-07-06 (`docs/OUTPUTS_CONTRACT_PROPOSAL.md`): full-show renders now, the
  hook-first teaser cut is staged (**AI Top 5 first**, then YourGov).

## Gotchas
- `campaign.py request` needs the campaign's marketing frame (goal + a key_message/angle) — it builds
  those from `campaign.md`; make sure `goal` and `name`/`cta` are set.
- Readiness treats template hints / `(fill in)` / single-line parentheticals as MISSING.
- YAML front-matter round-trips to block style on write (harmless).
- POST_QUEUE/RESERVE are becoming generated views; `CAMPAIGNS.md` is already generated (don't hand-edit).
