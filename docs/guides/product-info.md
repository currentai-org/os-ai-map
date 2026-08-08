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
- **Point-in-time metrics** — star counts, download/install/pull counts, contributor and
  commit counts, "fastest-growing". See "Volatile metrics" below; they go stale the day
  they are written and prose has no freshness gate to catch it.

## `comments` — provenance and notes

**Purpose.** The scoring/provenance notes a reader or the next editor needs but that are
not the product's description: license (with OSI/OSI-not call), version and release date,
ownership/hosting nuance, gating caveats, and the verification line.

**Format.** One compact paragraph, ~15–45 words (corpus median ~30). Semicolon- or
period-separated clauses are both fine. Order, loosely: identity/aka → license → version
& date → caveats → verification line.

**Always state the license explicitly, and flag the non-obvious call**, because the
license is what the openness score turns on and the classifier lies (see
`add-product` and `openness-spectrum.md`): "Llama 2 Community License (not OSI)",
"Gemma license is not OSI", "BSL 1.1 → source_available", "LICENSE file is the standard,
unmodified Apache 2.0 text."

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
- `Apache 2.0 (unmodified LICENSE body). v1.9.3 released 2026-05-29. Verified 2026-06-22 via GitHub.`
- `Llama 2 Community License (not OSI); adapter weights public on HF, base gated by Meta. Verified 2026-06-14 via HF model card.`

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
   *openness verdict* ("truly open") belongs in the score file, where it carries evidence,
   not in prose. When in doubt, describe what the product is and let the axis carry the
   judgment.
5. **Do not embed volatile metrics** — see below.

## Volatile metrics — link, don't embed

A star count, download count, or contributor count is stale the moment it is written, and
prose carries no freshness mechanism — `last_verified` gates *scores*, not `description`
text. So a hardcoded "24K GitHub stars" or "~4.8k stars, actively maintained" is a
liability with no owner. Do not write it.

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
2. **Re-derive the checkable facts**: current version and release date, license (read the
   LICENSE body, not the GitHub classifier), what it bundles/does, ownership/hosting.
3. **Rewrite `description`** to the format above if anything material changed, keeping it
   neutral and within the length band. Leave it alone if nothing moved.
4. **Update `comments`**: correct the license/version/date clauses, then set the
   verification line to today's date and the source you read.
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
- [ ] `comments`: license stated with the OSI call; version + release date; caveats.
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
