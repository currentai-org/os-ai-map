# Product Info Guide

The style, format, and tone of a product's **prose** fields — `description` and
`comments` — and the procedure for keeping them current.

> This guide governs the two hand-authored strings in `sources/products/<slug>.yaml`.
> It is the prose companion to the scoring machinery, which is a different thing: how a
> *score* earns a `last_verified` date, its evidence, and its gates live in
> `docs/guides/verification.md` and `docs/guides/freshness.md`, and this guide never
> overrides them. When a rule here changes, change the guide first and make the reviewer
> (and the `verify-product` skill) follow.

Both fields are reader-facing. `serialize.py` emits `description` into the payload as
`description` and `comments` as `version_note`; both render in the notebook. So neither is
a scratchpad — they are published copy.

## Scope, and what this is NOT

In scope: the free-text prose an editor writes by hand — `description` and `comments` —
plus the two label fields around them (`display_name`, and how they relate to `name`).

Out of scope, and deliberately: **anything a score records.** `openness`, `adoption`,
`capability`, their `sources[]`, and `last_verified` live in
`sources/scores/<slug>.yaml`, are governed by `verification.md`/`freshness.md`, and are
partly machine-written (`build/apply_scores.py`). Do not encode a score judgment in the
prose (see "Keep judgments on the axes" below), and do not treat the `comments`
verification line as a freshness date — the two are related in spirit and separate in
mechanism (see "Provenance vs. `last_verified`").

## The fields at a glance

| field | schema | what it is | audience |
|---|---|---|---|
| `name` | required, kebab-case | the slug/identity; see `add-product` | machine |
| `display_name` | required | the human label | reader |
| `description` | string | what the product IS and DOES, neutral | reader (payload `description`) |
| `comments` | string | footnote: how the entry was verified, and any judgment call behind it | reader (payload `version_note`) |

Both prose fields are optional in the schema, but in practice every product carries a
`description` and almost every one carries `comments`. Write both.

## `description` — what it is and does

**Purpose.** Tell a reader what the product is and what it does, in the neutral register
of a catalog entry. It is not a pitch and not a review.

**`description` is the load-bearing field.** Everything a reader needs about the product
belongs here: what it is, what it does, what distinguishes it, and who builds or stewards
it. `comments` is a footnote about *how we know*, not a second place to put product facts —
see "The division of labor" below. When a fact could sit in either, it goes here.

**Format.**
- **Length: 2–4 sentences, ~35–70 words.** The corpus median is 3 sentences / 55 words;
  treat 1 sentence as too thin for a scored product and 6 as too long. A long tail entry
  may be a single clause.
- **Lead with the product doing something**, not with its vendor. Good: "Accelerate is a
  Hugging Face PyTorch library that lets users run raw PyTorch training scripts across
  CPUs, multi-GPU, and TPU…". Who builds it belongs in the description, but usually in a
  closing clause rather than the opening one, unless the org is load-bearing for identity
  (e.g. "NVIDIA's content-safety classifier").
- **Vary the sentence openings.** Three sentences in a row beginning "It …" reads as a
  generated list. Recast one around its real subject ("A graph compiler optimizes…",
  "Modular develops and distributes it").
- **Present tense, third person, declarative.** No second person ("you can"), no imperative.
- **First mention uses the display name**, then a natural short form.
- **Spell out an acronym once** if the category reader would not know it.

**Content — include:**
- The product's *kind* (library / model / protocol / dataset / board) and its one-line job.
- What distinguishes it from the obvious neighbor, factually ("Where MCP connects agents
  to tools, A2A connects agents to other agents").
- Concrete, checkable specifics: parameter class, modality, what it bundles, what standard
  it implements.

**Content — exclude:**
- **Marketing cadence.** No "powerful", "cutting-edge", "seamless", "revolutionary",
  "blazing-fast". Borrow the register named in `docs/methodology.md`: *precise, defined,
  measured, forthright about limitations.*
- **Unsourced superlatives and rankings** ("the best", "the leading", "the de facto
  standard") unless they are a plain, checkable fact stated as one.
- **Point-in-time facts** — star counts, download/install/pull counts, contributor and
  commit counts, "fastest-growing", and the product's current version number. See
  "Volatile facts" below; they go stale the day they are written and prose has no
  freshness gate to catch it.
- **Curator rationale** — why the map includes the product. See below.

### Curator rationale is not description content

A description describes. A clause explaining why the map picked something up — "Picked when
hardware is constrained", "Chosen because it is the only OSI-licensed option in the category" —
is a note about our selection rather than about the product, and it reads as a recommendation
in a field that is meant to be a catalog entry.

It is also where the content this guide already bans has collected. Surveying the corpus on
2026-08-08, every hardcoded star count in a product carrying such a clause sat inside the
clause, as did nearly every superlative, while the descriptive half of the same field was
clean. Removing the clause is mostly a deletion, not a rewrite.

Find them with:

```
\b(picked|chosen|included|selected)\s+(because|when|by|for|as|if)\b
```

Rewrite in this order:

1. **Salvage the facts trapped inside.** The clause often carries the most concrete thing in
   the entry — "powers the Hugging Face Open LLM Leaderboard", "the execution layer behind
   Vercel Open Agents", "Anyscale's founders created Ray at UC Berkeley's RISELab in 2019".
   Those are product facts. Move them into the description proper.
2. **Drop counts, funding and superlatives.** Banned elsewhere in this guide already, so no
   judgment call is involved.
3. **Delete the recommendation framing.** What is left of "Picked when hardware is
   constrained" after steps 1 and 2 is our opinion, and it goes.

If a selection judgment genuinely needs recording — a product admitted on a borderline reading,
say — it is a footnote about *our reading*, so it belongs in `comments` under the rules below.

## `comments` — verification details and methodology footnotes

**Purpose.** How we know what the entry says, and anything a reader or the next editor
needs about the *treatment* rather than the product. In practice: the verification line,
plus the occasional footnote about a judgment call or an evidence gap.

### The division of labor

`description` is load-bearing; `comments` is a footnote. The test is the subject of the
sentence:

| the sentence is about… | field |
|---|---|
| the product — what it is, does, runs on, who builds it | `description` |
| our reading of it — what was checked, what was ambiguous, what a score followed | `comments` |

Both fields render in the same product detail panel, one directly above the other. A fact
stated twice is read twice, so the split is not cosmetic. Before writing a clause in
`comments`, check it is not already in `description`; if it belongs to the product, move it
rather than repeat it.

Footnotes that earn their place:
- an evidence gap — "no tagged releases, so this is verified against the repository head"
- a judgment call the score rests on — "the repository source and usage terms carry
  different licenses; the openness score follows the usage terms"
- something in a source that would mislead the next reader — "the LICENSE file also bundles
  third-party code under separate terms"

**Format.** Up to ~45 words, and no lower bound. Most products need only the verification
line, and one line is a complete entry. Do not pad, and do not invent a footnote to fill
the field.

**Do not state the license here.** It is a scored field — see "Scored fields" below.

### The verification line — canonical form

The corpus carries this idiom 227 ways ("Verified live June 2026", "verified live on HF
June 2026", "Verified live 2026-06-22 via primary sources", …). Standardize on:

```
Verified <YYYY-MM-DD> via <source>.
```

- **ISO date**, matching the `accessed:` format in score files. A month-year ("June 2026")
  is acceptable only when the exact day is genuinely unknown; prefer the full date.
- **`<source>` names the document you read, not the method you used.** `GitHub`, `PyPI`,
  `the LICENSE body`, `the HF model card`, `the AWS Neuron documentation`, `Groq's LPU
  architecture blog` are all good. This list is **illustrative, not closed** — name the
  source specifically enough that the next editor can open the same page. Where several
  sources were needed, name them.
- **Never name a method.** `web search`, `research`, and the bare `primary sources` describe
  how you looked rather than what settled it, and leave the next editor nothing to re-open.
  If a search led you to a vendor page, the vendor page is the source.
- Capital "V". One line, at the end of `comments`.

Examples:
- `Verified 2026-06-22 via GitHub and the LICENSE body.`
- `No tagged releases, so this is verified against the repository head. Verified 2026-06-22 via GitHub.`
- `The base weights are gated, so openness was read from the model card rather than a download. Verified 2026-06-14 via the HF model card.`

## Global rules

1. **American English everywhere** — `license` not `licence`, `penalized`, `labeled`,
   `behavior`. This is a standing hazard in `verification-pass.md` and applies to prose
   too, not just identifiers.
2. **No marketing cadence.** Same register as the methodology copy.
3. **Never assert from memory.** Any factual claim — version, release date, license,
   what it bundles — is confirmed against a PRIMARY source before it is written. A
   plausible claim that does not survive a check is not written. (This is the same rule
   `add-product` step 7 states for adding.)
4. **Keep judgments on the axes.** Adoption and openness are scored, sourced fields. An
   *openness verdict* ("truly open") and the **license it rests on** belong in the score
   file, where they carry evidence. See "Scored fields" below.
5. **Do not embed volatile facts** — counts, current version numbers, or corporate events.
   See below.

## How far to verify a claim

A prose refresh runs *inside* the score re-read — one pass per product, described in
`docs/runbooks/verification-pass.md` Phase 4. The same repository, model card and vendor docs
are opened once and both halves are written from what they show. So prose carries no separate
research budget, and the only question left is what to do with the claims that sit outside the
score's evidence.

| claim class | policy |
|---|---|
| what the product is and does | **verify** — the score re-read establishes it anyway |
| comparative positioning ("Where MCP …, A2A …") | **verify** — the same pages settle it |
| superlative or unsourced ranking | **delete** — already against this guide |
| corporate event (acquired / raised / IPO) | **omit** unless identity-bearing |
| curator rationale ("Picked when …") | **remove from `description`** |

Three of the five resolve to delete or omit rather than research, which is most of the reason
the prose half adds little to the cost of a re-read. A claim that the sources opened for the
score do not settle, and that none of the rules above disposes of, comes **out** of the prose.
It is never left in unverified on the grounds that it was already there.

This is also why the coupling matters. A prose pass run on its own does not open primary
sources, and the result is a provenance line naming a method — `Verified 2026-08-08 via web
search` — which is precisely what the canonical form below forbids.

## Scored fields — don't restate them

The license is the clearest case, and the one this guide used to get backwards. It is not
merely descriptive: it *is* the openness score's basis, recorded in
`sources/scores/<slug>.yaml` as `openness.components` — either the legacy flat string
(`license:Apache-2.0(OSI);…`) or the structured mapping the corpus is migrating to, always
read via `components_of` rather than assumed to be either shape — with `sources[].accessed`
behind it and the invariant and the digest requirement in front of it.

Restating it in `comments` creates a second copy with none of that. The two then drift in
one direction only: a relicense flows correctly through `verification.md`, the score
updates, and the prose is quietly left wrong with nothing to catch it. That is the same
"liability with no owner" the volatile-facts rule names, made worse by the copy *looking*
authoritative.

It also buys the reader nothing. `build/serialize.py` emits the `openness` dict into the
payload, flattening `components` back to a string via `components_string` whichever shape
the score file carries, and the front end already renders `openness.components` in the
product detail panel — in larger type than the prose `version_note` directly above it. The
license is on screen either way; only one copy carries evidence.

So: **read the LICENSE body, and do not write it into prose.** Reading it stays essential —
the GitHub classifier lies (a custom copyright line makes a genuine MIT/Apache repo report
`NOASSERTION`), and the OSI / not-OSI call is exactly what the score turns on. But when the
body disagrees with the recorded score, that is a **score** finding: stop and follow
`verification.md`. Do not reconcile it by editing the product file.

The same applies to any other scored dimension. Adoption, capability, and the openness
class are axes with evidence; prose describes what the product is and lets them carry the
judgment.

## Volatile facts — link, don't embed

Prose carries no freshness mechanism. `last_verified` gates *scores*, not `description`
text, so any fact in prose that a later event can invalidate is a liability with no owner.

**The test: would a future release make this sentence wrong?** If yes, it is volatile and
does not belong in prose. If a future release would instead be a *different product entry*,
or if there will be no future release, the fact is durable and can stay.

### Counts

A star count, download count, or contributor count is stale the moment it is written. A
hardcoded "24K GitHub stars" or "~4.8k stars, actively maintained" fails the test. Do not
write it.

The actuals already have two homes, and neither is the prose:

- **The artifact URLs are the live link.** A product's `github`/`pypi`/`huggingface_*`
  entries point at the page that shows the current number. A reader who wants the count
  follows the link; a tool reads it from the source.
- **Adoption is a computed axis.** Magnitude of use is scored on the `adoption` axis from
  those artifacts by the warehouse (`docs/methodology.md`: "real usage, not stars"), which
  is where the number belongs *with* a date and a signal type.

What prose may still say is the **durable, qualitative** shape of adoption when it is a
structural fact rather than a number — "the distributed-training backbone for other Hugging
Face libraries", "hosted by the Linux Foundation". Prefer even these sparingly, and never
as a stand-in for a count. If a number matters, it is an `adoption` score, not a sentence.

> Forward direction: as the notebook renders live/computed counts from the linked artifacts
> and the `adoption` axis, prose should carry none. Treat every metric you would type as a
> link you should rely on instead.

### Current version and release date

A "latest version" clause fails the same test for the same reason: the next release makes
it wrong, and nothing in the repo will notice. `v0.26.0 released 2026-07-25` and
`Latest stable v1.2.1 ...; 1.3.0 release candidates in progress` are both promises the map
cannot keep across several hundred products. The `github`/`pypi`/`huggingface_*` links
already point at the page showing the current release. Do not restate it.

Three cases are **durable** and stay:

1. **The version is the entry's identity.** For a named model release — `Apertus family
   (8B + 70B), released 2 Sep 2025` — the date is a historical fact about *this* product,
   and the next release is a different entry (or a different rung; see
   `docs/reference/identity.md`). Keep it.
2. **There will be no future release.** `Latest release v3.3.7 (2025-12-19). Repo archived
   2026-03-21 and placed in maintenance mode` is durable precisely because the project
   stopped. Keep it — an archived project's last release is a lifecycle fact.
3. **A statement of absence.** `Created 6 May 2026; no tagged releases (built from source)`
   describes how the project ships, not where it currently is.

### Corporate events

An acquisition, a funding round, or an IPO fails the same test. It is true on the day it is
written, the next event makes it incomplete rather than wrong, and nothing in the repo is
watching. **Omit it by default.**

The exception is when the event is *identity-bearing* — it establishes who ships the product
now, and a reader who did not know it would go looking for the wrong vendor. `Predibase, now
part of Rubrik` earns its clause on those grounds. `Raised a $50M Series B in 2025` does not,
and neither does an acquisition recounted as company history. Funding in particular is a
proxy for traction, which is what the `adoption` axis is for.

The tell for the volatile case is a word like "latest", "current", or "as of". A tier
product states this outright — see `claude-sonnet`: *"Anthropic ships a new Sonnet roughly
every few months, so a versioned entry goes stale faster than it can be reviewed; the slug
is stable."* That reasoning generalizes; it is why the rule exists.

Where a version genuinely bears on a *score* — a relicense at v2, weights pulled in a
later release — it is score evidence with a `sources[].accessed` date, not a prose clause.

## Provenance vs. `last_verified`

These look alike and are not the same, and conflating them is the exact error
`freshness.md` exists to prevent. Keep them straight:

- The **`comments` verification line** is *editorial provenance for the prose* in the
  product file. It says "an editor last confirmed these descriptive facts on this day." It
  is not gated, not machine-read for freshness, and carries no per-dimension evidence.
- **`last_verified`** lives in the *score* file, per axis, and is a confirmation that a
  *score* is still correct, re-derivable from `sources[].establishes`, and gated by the
  invariant and the digest requirement. Only a person writes it, and only per the rules in
  `verification.md`.

Writing the `comments` line **does not** earn a `last_verified`, and updating a product's
prose is not a score re-check. If a prose re-read turns up a fact that moves a *score* (a
relicense, weights pulled, a dataset gated), that is a score change: stop, and follow
`verification.md` — do not edit the score from the product file.

## Updating a product — procedure

Use this to refresh an existing product's prose (the `verify-product` skill automates it):

1. **Open the primary source(s)** the product points at — its `github`/`huggingface_*`/
   `pypi` URLs, and the vendor blog or registry. Never refresh from memory or a secondary
   summary.
2. **Re-derive the checkable facts**: what it bundles/does, ownership/hosting, lifecycle
   state. Read the LICENSE body and the current release too — not to write them into prose,
   but to confirm the project is alive and that neither has moved a score. A version goes in
   only under one of the three durable cases above; a license does not go in at all.
3. **Rewrite `description`** to the format above if anything material changed, keeping it
   neutral and within the length band. Leave it alone if nothing moved. Strip a curator
   rationale clause and a corporate event wherever you find one, salvaging any product fact
   inside first; both are edits worth making on their own, with nothing else moving.
4. **Update `comments`**: strip any stale count, "latest version" clause, or license
   restatement, and move any surviving *product* fact into `description`. Keep only
   footnotes about the reading itself. Set the verification line to today's date and the
   document you read.
5. **If a fact moves a score**, do not touch the score file here — record it and hand off
   to the `verification.md` flow.
6. **Validate:** `uv run python -m build.validate` prints `0 error(s)`. Preview only; do
   not commit `build/notebook_data.json` or `notebooks/ai-stack-map.py` (bot-owned).

## Checklist

- [ ] `description`: 2–4 sentences, ~35–70 words, leads with the product doing something,
      present tense, neutral register.
- [ ] No marketing words; no unsourced superlatives; judgments left on the axes. Watch
      "high-performance" and "high-throughput" — say what the product does instead.
- [ ] No three consecutive sentences opening "It …".
- [ ] No hardcoded star/download/contributor counts — rely on the artifact links and the
      `adoption` axis instead.
- [ ] No "latest/current version" clause, unless it is identity, terminal, or an absence.
- [ ] No curator rationale — no "Picked when …" / "Chosen because …" clause in `description`.
- [ ] No funding round, acquisition, or IPO, unless it says who ships the product now.
- [ ] No license restatement — it is `openness.components` in the score file (string or
      structured mapping, read via `components_of`, edited only via `build/components.py`).
- [ ] `comments` says nothing `description` already says — no product facts, footnotes only.
- [ ] Verification line in canonical form: `Verified <YYYY-MM-DD> via <source>.`
- [ ] `<source>` names a document someone could reopen, never a method ("web search").
- [ ] American English throughout.
- [ ] Every factual claim confirmed against a primary source, not memory.
- [ ] `uv run python -m build.validate` → `0 error(s)`.

## Related

- `skills/verify-product/SKILL.md` — the procedure above, as an agent-runnable skill
- `skills/add-product/SKILL.md` — creating a product (step 7 is the same primary-source rule)
- `docs/guides/verification.md` — normative: how a *score* earns `last_verified`
- `docs/guides/freshness.md` — normative: what `last_verified` means
- `docs/methodology.md` — the register these fields borrow ("no marketing cadence")
- `docs/schemas/product.schema.json` — the field definitions
