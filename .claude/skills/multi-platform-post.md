# Multi-Platform Post Skill (one topic → tailored across platforms)

The **orchestration** skill: take ONE story and split it across the platforms — decide **which to use
and which to leave out**, then give each its own **hook, angle, and voice**. Same facts, five different
posts. It sits above the platform skills (mechanics) and the post-type skills (off-the-cuff / feature).

Goal: "one topic, up to five platforms; the system knows which channels fit, the hook for each, and it
carries the operator's personality — each platform slightly different." Proven on the Fable-5 campaign
(worked example at the bottom).

---

## The operator's voice (bake this in)

- **Geeky-tech + tabloid sensation** (the sensation filter): lead with the shocking-but-true angle, a
  real number/figure, and named brands/models (@AnthropicAI, Fable 5, Opus, OpenCode, DeepSeek…).
- **Dry wit**, and on the loud channels, **aggressive "no shame."** Real figures and named people.
- **Opinion is fine; fabrication is not.** Sensational framing of TRUE facts. Mark hot-takes as opinion,
  don't assert unverified causal/political claims as fact.
- **Piggyback trends only when ON-TOPIC.** Do NOT hijack unrelated wars/tragedies/hashtags for reach —
  it reads as spam, gets reported/ratio'd, and burns the brand. On-topic trend/figure piggybacking (the
  actual people/companies in the story) is the win.
- 🚨 **On Twitter, never START the text with an @-mention** — X classifies it as a reply, so it skips
  the Posts tab and only reaches people following BOTH accounts. Self-defeating on exactly the
  piggyback posts where mentions matter most. Reorder (`Just shipped by @OpenAI: …`) or use a leading
  dot (`.@OpenAI …`). Full detail in `twitter.md`.

## Platform register — the "which bar are you walking into" model

| Platform | Register | Use it for | Voice / hook | Media |
|---|---|---|---|---|
| **Twitter/X** | Kick the door in | spicy hot-takes, political/sensational angle, news-jacking the real players | Aggressive, dense, **inline hashtags**, @-tag the targets, piggyback on-topic figures, meme energy 🏴‍☠️. Lead with the punch. | meme/image great; short video |
| **Bluesky** | The wine bar (dev, serious, "clever") | the same story minus the rage — the *insight/hypocrisy* | **Dry, clever, dense**, hashtags OK (contra local convention), shows the actual issue, geek-sensational, **no shock, no politics/Trump** | text-first |
| **LinkedIn** | The credible hub / report | milestones, announcements, the substantive write-up | Professional, measured, the **anchor other socials link back to**. No memes, no aggression. | text or the report; no spice |
| **Instagram** | The visual | reels / image / meme | Short, visual; caption carries it (silent video — no audio yet). Not text-only spicy takes. | image/meme or reel |
| **YouTube** | The explainer | the deep-dive **follow-up** once a post catches | Longer video explainer (16:9) or vertical Short for dailies. Capitalise on a hit: turn a Twitter storm into a YT explainer. | video required |

## Selection logic — which to use, which to leave out

Decide by **topic type × media on hand**:
- **Off-the-cuff / short / spicy** → Twitter + Bluesky (skip LinkedIn/IG/YT).
- **Feature / announcement / milestone / tester-recruitment** → all five incl. LinkedIn.
- **Political / aggressive angle** → Twitter (full aggression + meme), Bluesky (dry, de-politicised),
  LinkedIn (credible/professional only), IG (visual only), YouTube (explainer as a follow-up if it lands).
- **Media gate:** text-only → TW/BS/LinkedIn; image/meme → TW/IG (+BS reply); video → IG/YT/all.
- **LinkedIn is milestones-only** — never the daily/spicy stuff.

### ⚠️ When the user gives loose scope ("all platforms", "all platforms apart from X") — ENUMERATE, don't assume

**Mistake made 2026-08-01/02:** user said "all platforms apart from linkedin" for a SPLITFIRE promo. The
assistant silently read that as Twitter+Bluesky+Instagram and never mentioned YouTube — but the account's
"all platforms" set is five (YT/TW/BS/IG/LinkedIn), and this was a video post where YouTube fit was a real
open question (12s clip, wrong aspect for a proper YT video). The gap surfaced an hour later as user
confusion over whether/how the clip should reach YouTube, and a second round of back-and-forth to recover
intent for a LinkedIn video that could no longer be attached to the (already-published, text-only) LinkedIn
post from earlier that day.

**Fix: whenever scope is given as "all platforms" or "all except <n>", say the full platform list back
before drafting** — e.g. "That's YouTube, Twitter, Bluesky, Instagram (skipping LinkedIn) — right?" Do this
even when it feels obvious. It costs one line and catches exactly this kind of silent scope-narrowing before
copy gets drafted, agents get dispatched, or (as here) a platform that needed its own decision (does this
media even fit YouTube?) gets skipped without ever being raised.

## 🔗 Tracked short links — worth setting up if you link to your own pages

*Optional. If you don't have redirect infrastructure, post normal links and skip this section.*

**Don't post the same bare URL everywhere.** Give each platform its own redirect slug pointing at
the same destination, with the platform baked into both the path and the UTM parameters:

```
yourdomain.com/go/<service>-<platform>   →  302  →  the real page + ?utm_source=<platform>&…
```

Suggested platform keys: `li` LinkedIn · `x` X · `bs` Bluesky · `ig` Instagram (bio) · `yt` YouTube
description. So `shop-x` on X and `shop-li` on LinkedIn both land on the same page.

**Why bother:** two independent tracking layers for very little work. The redirect can be logged
server-side (timestamp, slug, referrer), and the UTMs are picked up by the analytics on the landing
page — so you learn both *which platform produced the click* and *what that visitor did next*.
Neither is available from a shared bare URL, because most platforms strip or obscure the referrer.

**Instagram especially.** IG clicks report as direct with no referrer, so without a tagged bio link
they are simply invisible. IG also allows only one bio link at a time and it can only be changed by
hand in the app — treat that slot as a deliberate choice.

**Rules:**
- Keep slugs **stable public IDs**, with destinations re-pointable from one config file. A campaign
  can then change where a link goes without breaking every post that already shipped.
- Use a **302, not a 301** — a 301 gets cached by the browser, so you lose both the click log and the
  ability to re-point it later.
- **Still one link per post on X and Bluesky.** The short link *is* that link; a second URL hijacks
  the unfurl card.
- **Not every link needs a slug.** An external article, someone else's site, a raw YouTube URL — leave
  those alone. The rule is: pointing at something *you own* → use a tracked slug.

## Funnel + cross-promo

- Pick ONE **hub** per campaign (the substantive destination): the LinkedIn report, or the website for a
  product launch. Every other platform's post **points back to the hub**.
- **Cross-promo "click & subscribe" reply:** after posting, reply to the TW/BS post with the hub link
  (and/or links to the other socials). Outward-facing → needs the operator's go.
- Sequence: **post the hub first**, grab its URL, then drop it into the other posts.

## Workflow

1. Get the story + the real facts/numbers (from the excitement feed, a commit, a report).
2. Choose platforms via the selection logic. Note which you're leaving out and why.
3. Write each variant in that platform's register (use the post-type skills for length/format; write to
   the limit; count before posting).
4. Show the operator ALL variants + any media for explicit sign-off (never infer go).
5. Post the hub first → link the rest → optional cross-promo replies → log IDs → record engagers.

**If a post FAILS, start FRESH — don't fight the wedged state.** Reload the page / open a new composer
and retry clean (poking a stuck composer only degrades it: stale refs, stuck alt/discard dialogs,
typeahead). **Cap at ~2 clean attempts**, then change approach — prep the composer and hand the final
click to the user, go text-only, or attach media by hand. Don't grind 5+ times. (See twitter.md: image
tweets specifically must be finished by hand in the current X UI.)

---

## Worked example — "First AI Censorship?" (Fable 5 vs Opus, 2026-07-03)

One topic (Fable 5's dual-use safeguard swapped it out of a security review of the operator's own app),
split five ways, hub = the LinkedIn report:

- **LinkedIn (hub):** measured write-up — the tie on findings, then the operational twist, ending on
  "when guardrails can't tell a defender from an attacker, they stop the fix — who does that serve?"
  Everything links here.
- **Twitter (door-kick + meme):** *"@AnthropicAI's Mythos: #banned abroad on 'national security' 🏴‍☠️
  then crawls back tail-between-legs. I go to security-sweep my OWN app — it reverts to Opus 'for safety.'
  First AI #censorship, brought to you by #Trump. More coming 🏴‍☠️ [hub] @YourHandle"* + the wrestling
  tag-team meme. On-topic piggyback (@AnthropicAI, #Trump, OpenAI). **Left OUT the unrelated war
  hashtag** — hijacking a live war for reach backfires.
- **Bluesky (wine bar):** *"'Safety' on Anthropic's Fable is now so robust it won't let me audit my OWN
  app — it taps out and hands the job to the older, unrestricted model. A dual-use filter that can't tell
  a defender from an attacker doesn't block misuse. It blocks the fix. Govt broke our toys again.
  #AISafety #infosec"* Dry, no Trump, hub link in the reply.
- **Instagram:** the meme image.
- **YouTube:** an explainer — held as the **follow-up** to run if the posts catch.

The lesson to reuse: **same facts, five voices, hub-and-spoke, personality throughout, and the discipline
to leave the wrong angle (or platform) out.**
