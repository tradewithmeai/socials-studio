# Quick Post Skill — user drops an image + a campaign; you own the rest

The lightest posting flow. The user pastes a screenshot/image (often mid-work, e.g. during a
running-story campaign) and says some variant of **"post this"** — usually naming or implying a
campaign. From that moment YOU are responsible for the whole post: file it, write it, publish it, log it.

## The contract
- **Input:** an image (+ its `D:\Documents\Screenshots\...` source path shown in the message) and a
  campaign (named, or obvious from context — e.g. the running campaign of the day).
- **You do everything else.** Don't ask for copy; write it. Only come back if something is genuinely
  ambiguous (wrong campaign guess would be embarrassing, or the image contradicts the story).

## Procedure
1. **Stage the image** into the campaign: copy the source file to
   `campaigns/<slug>/media/<NN-beat>/<short-name>.png` (uploads only work from inside the project dir).
2. **Write the copy** with the off-the-cuff skill's rules (`post-offthecuff.md`): sensational-but-true
   lead, name brands/models, one number, write to the limit. Platforms default **Twitter + Bluesky**
   (the running-story channels) unless the campaign says otherwise. If it's a running-story campaign,
   carry the story spine (clock/time-elapsed for challenge days, "still going" energy).
3. **Pre-flight char counts** (TW ≤280 weighted, EACH url = 23, emoji = 2; BS ≤300 literal).
4. **Record it** as a post file in `campaigns/<slug>/posts/<NN>-<slug>.md` (front-matter: id, status,
   platforms, media map; body: the per-platform copy). The campaign folder is the source of truth.
5. **Publish** (or delegate to a publishing subagent so the main session keeps working — give the
   subagent the exact text, image ABSOLUTE paths, and the platform skill files to read):
   - **Bluesky:** fully automated (text → attach media → wait for processing → publish → verify rkey
     via the public API).
   - **Twitter image posts: PREP ONLY** — fill composer + attach image, verify Post enabled, then hand
     the final click to the user (the alt-text reminder wedges automated image tweets — verified).
6. **Log**: update the campaign's beats table / post status; capture post ids in the post file or
   `post_schedule.json` if it's a tracked series.

## Authorization model
The user's "post this" (with the image, naming the campaign/day) IS the go for that post — this skill
exists so they don't have to review routine beat copy mid-flow. BUT: show the copy in your reply as you
publish (so they can veto fast), and drop back to full sign-off for anything outward-facing beyond the
routine beat (replies to other accounts, political/spicy angles, client content, anything irreversible
beyond a deletable post).

## Gotchas
- Don't reuse stats/screenshots across contexts — check the image actually belongs to this campaign's
  story (2026-07-07: a 20X usage screenshot was from a DIFFERENT run than the game build — it became a
  separate post rather than a comment on the build thread).
- One image = one beat. A second image in the same message may be a different beat (ask the story, not
  the user: does it advance the same thread or start a parallel one?).
- Running-story campaigns: number the beats (`00-teaser`, `01-progress`, ...) so the story reads in order.
