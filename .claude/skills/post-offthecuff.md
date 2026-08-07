# Off-the-Cuff Post Skill (short, snappy, sensational)

A **writing** skill: turns one exciting story (usually a GitHub commit/finding) into a short, snappy
post. It does NOT publish — it produces the copy, then you hand it to the platform skill
(`twitter.md` / `bluesky.md`) to post. Complements the platform skills; it's the *what to say*, they're
the *how to post*.

**Platforms (for now):** Bluesky + Twitter ONLY. Text-only is fine (no image required). Not Instagram
(needs media), not LinkedIn (milestones only — use the feature-piece skill for those).

---

## The one job

Take a genuinely interesting thing that happened and write a post someone would actually stop to read.
Short. Direct. One idea. Out the same day it happened — "off the cuff", not laboured.

## Non-negotiable rules

1. **Lead with the sensational — but TRUE — line.** The shocking fact goes FIRST, not the setup.
   - ✅ "Gemini invented 38 seconds of video that never existed."
   - ❌ "While building my video app, I noticed a timestamp issue…"
   Sensational framing of a real fact. **Never fabricate** — the drama must be true. (See the
   "tabloid geek" filter: pick/frame like an editor who loves deep tech AND front-page sensation.)
2. **Name the brands and models.** "Gemini", "Claude Code", "gpt-5.4-mini", "Remotion" — not "an AI".
   Real names boost algorithmic reach and reader interest.
3. **Lead with a concrete number** where there is one (38 seconds, 2m23s vs 1m45s, 138 views).
   Sensation + brand + number = the strongest hook.
4. **Write to the limit — don't draft long then trim.** Twitter ≤ 280 chars, Bluesky ≤ 300. Compose
   AT the target length; make the most of it. Verify the count before handing off.
5. **No markdown.** Asterisks/underscores render literally on both platforms — don't use `*bold*`.
6. **One idea, snappy.** 3 short blocks max: hook → the substance in a line or two → a one-line
   takeaway (or light CTA).
7. **Hashtags (rule set 2026-07-07): at least the main 2, `#buildinpublic` FIRST, then your choice of
   1–2 brand/model tags** (e.g. `#Fable5 #Claude #Cowork #AI #Gemini`). Twitter lives and dies on
   hashtags — a bare post is a missed reach opportunity. Budget for them in the char count.

## Shape

```
<SENSATIONAL TRUE HOOK — the shocking fact, brand + number if possible>

<1–2 lines: what actually happened / the context that makes it land>

<one-line takeaway or lesson>
#buildinpublic
```

## Worked example

Source: Gemini hallucinated a clip's timeline (143s reported on a 105s clip) while building Project
Bright; fixed with signal detection.

> Gemini invented 38 seconds of video that never existed.
>
> I asked it to cut the dead gaps from a clip for Project Bright, my AI video app. It swore the footage
> ran to 2m23s. The real clip is 1m45s.
>
> LLMs reason about content, not time.
> #buildinpublic

(249 chars — fits both platforms, leads with sensation + brand, keeps the numbers.)

## Workflow

1. **Get the story.** Later: read the top-rated item from the GitHub excitement API (see
   `services/github-excitement-feed/SPEC.md`). For now: pick the most headline-worthy commit from the
   day's `git log` across the projects.
2. **Write** per the rules above. Produce Bluesky + Twitter copy (usually identical; only differ if the
   count forces it).
3. **Verify char counts** (Twitter ≤280, Bluesky ≤300).
4. **Show the user the final copy for explicit sign-off.** Never publish on inference.
5. On go, hand to `twitter.md` + `bluesky.md` to post; log to `post_schedule.json`; record any organic
   replies via `engagers.py`.
