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
| `comments` | string | provenance: license, version, release date, and the verification line | reader (payload `version_note`) |

Both prose fields are optional in the schema, but in practice every product carries a
`description` and almost every one carries `comments`. Write both.

## `description` — what it is and does

**Purpose.** Tell a reader what the product is and what it does, in the neutral register
of a catalog entry. It is not a pitch and not a review.

**Format.**
- **Length: 2–4 sentences, ~35–70 words.** The corpus median is 3 sentences / 55 words;
  treat 1 sentence as too thin for a scored product and 6 as too long. A long tail entry
  may be a single clause.
- **Lead with the product doing something**, not with its vendor or its license. Good:
  "Accelerate is a Hugging Face PyTorch library that lets users run raw PyTorch training
  scripts across CPUs, multi-GPU, and TPU…". The org and license belong in `comments`, not
  in the first sentence, unless the org name is genuinely load-bearing for identity (e.g.
  "NVIDIA's content-safety classifier").
- **Present tense, third person, declarative.** No second person ("you can"), no imperative.
- **First mention uses the display name**, then a natural short form.
- **Spell out an acronym once** if the category reader would not know it.

**Content — include:**
- The product's *kind* (library / model / protocol / dataset / board) and its one-line job.
- What distinguishes it from the obvious neighbour, factually ("Where MCP connects agents
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

## `comments` — provenance and notes

**Purpose.** The provenance notes a reader or the next editor needs but that are not the
product's description: identity and aliases, ownership and hosting, gating caveats,
lifecycle state (archived, superseded), and the verification line.

**Format.** One compact paragraph, up to ~45 words. Semicolon- or period-separated clauses
are both fine. Order, loosely: identity/aka → ownership/hosting → caveats → verification
line.

There is no lower bound. With the license and the current version both out, a product whose
durable provenance is just "who maintains it" gets one clause and the verification line, and
that is a complete entry. Do not pad to reach a length.

**Do not state the license here.** It is a scored field — see "Scored fields" below.

### The verification line — canonical form

The corpus carries this idiom 227 ways ("Verified live June 2026", "verified live on HF
June 2026", "Verified live 2026-06-22 via primary sources", …). Standardize on:

```
Verified <YYYY-MM-DD> via <source>.
```

- **ISO date**, matching the `accessed:` format in score files. A month-year ("June 2026")
  is acceptable only when the exact day is genuinely unknown; prefer the full date.
- **`<source>`** names what was read: `primary sources`, `HF model card`, `GitHub`,
  `PyPI`, `vendor docs`, `LICENSE body`. Name the host when one source settled it.
- Capital "V". One line, at the end of `comments`.

Examples:
- `Hosted by the Linux Foundation; originated at UC Berkeley. Verified 2026-06-22 via GitHub.`
- `Adapter weights public on HF, base gated by Meta. Verified 2026-06-14 via HF model card.`

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
5. **Do not embed volatile facts** — counts or current version numbers. See below.

## Scored fields — don't restate them

The license is the clearest case, and the one this guide used to get backwards. It is not
merely descriptive: it *is* the openness score's basis, recorded in
`sources/scores/<slug>.yaml` as `openness.components` (`license:Apache-2.0(OSI);…`) with
`sources[].accessed` behind it and the G1/G2 gates in front of it.

Restating it in `comments` creates a second copy with none of that. The two then drift in
one direction only: a relicense flows correctly through `verification.md`, the score
updates, and the prose is quietly left wrong with nothing to catch it. That is the same
"liability with no owner" the volatile-facts rule names, made worse by the copy *looking*
authoritative.

It also buys the reader nothing. `build/serialize.py` emits the whole `openness` dict into
the payload, and the front end already renders `openness.components` in the product detail
panel — in larger type than the prose `version_note` directly above it. The license is on
screen either way; only one copy carries evidence.

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
   `slug_aliases.yaml`). Keep it.
2. **There will be no future release.** `Latest release v3.3.7 (2025-12-19). Repo archived
   2026-03-21 and placed in maintenance mode` is durable precisely because the project
   stopped. Keep it — an archived project's last release is a lifecycle fact.
3. **A statement of absence.** `Created 6 May 2026; no tagged releases (built from source)`
   describes how the project ships, not where it currently is.

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
  *score* is still correct, re-derivable from `sources[].establishes`, and gated (G1/G2).
  Only a person writes it, and only per the rules in `verification.md`.

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
   neutral and within the length band. Leave it alone if nothing moved.
4. **Update `comments`**: correct the ownership, hosting, and caveat clauses; strip any
   stale count, "latest version" clause, or license restatement; then set the verification
   line to today's date and the source you read.
5. **If a fact moves a score**, do not touch the score file here — record it and hand off
   to the `verification.md` flow.
6. **Validate:** `uv run python -m build.validate` prints `0 error(s)`. Preview only; do
   not commit `build/notebook_data.json` or `notebooks/ai-stack-map.py` (bot-owned).

## Checklist

- [ ] `description`: 2–4 sentences, ~35–70 words, leads with the product doing something,
      present tense, neutral register.
- [ ] No marketing words; no unsourced superlatives; judgments left on the axes.
- [ ] No hardcoded star/download/contributor counts — rely on the artifact links and the
      `adoption` axis instead.
- [ ] No "latest/current version" clause, unless it is identity, terminal, or an absence.
- [ ] No license restatement — it is `openness.components` in the score file.
- [ ] `comments`: identity/aka; ownership/hosting; caveats; lifecycle state.
- [ ] Verification line in canonical form: `Verified <YYYY-MM-DD> via <source>.`
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
