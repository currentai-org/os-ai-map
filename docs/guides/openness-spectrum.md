# Openness Spectrum Guide

How openness is scored, why the raw score isn't comparable across categories, and
which field to use when you want to place a product on an openness spectrum.

> This is the data-consumer / query reference. For the reader-facing methodology
> narrative published in the notebook, see [`docs/methodology.md`](../methodology.md).
> Keep the two consistent when the openness model changes.

## TL;DR

- **`openness.class` is the cross-category normalizer.** Use it to position a product
  on a spectrum.
- **`openness.score` (0–5) is NOT comparable across categories.** It's a within-type
  grade. Treat it as a detail, not a spectrum coordinate.
- A machine-readable mapping lives in [`docs/openness-class-map.json`](../openness-class-map.json).
  It is derived from `build/render.py` (the published notebook), so reusing it keeps any
  new visualization consistent with the live map.

## The two openness fields

Each `sources/scores/<slug>.yaml` carries two separate, analyst-assigned openness fields:

| Field | Type | What it is |
|-------|------|------------|
| `openness.class` | categorical | An OSI / Model Openness Framework (MOF) label. In use today, by frequency: `open_source`, `closed`, `open`, `open_weights`, `open_core`, `source_available`, `documented`, `gated`, `restricted`, `open_toolchain`, `open_hardware`. [`openness-class-map.json`](../openness-class-map.json) is the authoritative list. |
| `openness.score` | integer 0–5 | A graded openness score with a `components` breakdown (models: `weights / data / code / checkpoints / license`; software: OSI-class license tests; datasets: access / license / documentation). |

Every non-null value needs a primary `sources:` entry. Both fields were originally assigned
by hand against MOF/OSI, and that history is why `components`/`note` read as editorial prose.

**A deterministic formula now exists for most of the map.** All 16 categories declare a
`scoring_recipe` that names an ordered rule list over dimension values, and
`build/check_rubric.py` replays it against each product's recorded `components` to check that
the recorded score is the one the rules produce. Most recipes `extend` a shared ladder in
[`sources/rubrics/`](../../sources/rubrics/) rather than restating one: `software.yaml` covers
eleven categories, `model.yaml` the fine-tuned and guardrail models. A category holding more
than one kind of product maps `extends` per product type.

Three caveats, because "a formula exists" is easy to over-read:

- **A recipe covers a category, not every product in it.** All sixteen categories carry one as
  of 2026-08-01, but 81 products are declared in a `deferred:` block, meaning the category has
  said the ladder does not decide them. Those scores remain editorial. `check_recipe` prints
  the per-category split and fails if a product abstains without being declared.
- **A recipe reproducing a score does not validate it.** It shows the rules describe how the
  category was scored. The document-grade evidence the checker reads was parsed out of the
  same files the scores live in, so agreement is a fidelity check on the formula, not on the
  facts.
- **A category can hold products back.** `scoring_recipe.deferred` lists products the rules do
  not decide, usually because a dimension is not recorded in a form the ladder can read. There
  are 81 such products across 13 categories, and `safeguards` defers 5 of its 26. Deferred
  products publish no openness evidence to the warehouse.

So openness is part computed and part editorial, and which one you are looking at depends on
the category and the product. `docs/guides/verification.md` tracks the work to close that gap.

## Why the raw score is not comparable across categories

The 0–5 score is graded relative to what's achievable *within a product type*, so the same
number means different things in different categories. A quick cross-tab of `score | class`
across all score files shows the overlap:

| score | classes that appear at this score |
|-------|-----------------------------------|
| 5 | `open_source`, `open`, `open_hardware` |
| 4 | `open_core`, `open_weights`, `open`, `gated`, `open_toolchain` |
| 3 | `open_weights`, `open`, `documented`, `gated` |
| 2 | `restricted`, `source_available`, `gated` |
| 1 | `closed` |
| 0 | `closed` |

Regenerated 2026-07-30. The overlap is narrower than it was: the producible-pair check added in
#128 found 17 pairs no rule in any recipe could emit, and correcting them is why `open_core` and
`source_available` no longer appear at 3 and `open_core` no longer appears at 2. If you are
reading this table long after that date, regenerate it rather than trusting it — the check is
a few lines over `sources/scores/*.yaml`.

A pretrained model at **2** is genuinely restricted/gated, because the model gradient is
compressed (open weights typically land around 3, and you only reach 5 with a fully open
pipeline like Pythia or OLMo). A deployment tool at **2** sits somewhere else entirely.
**Don't compare the numbers directly across categories.**

## The normalization (use this for a spectrum)

`build/render.py` already collapses the model / software / dataset class vocabularies onto
one gradient and into a three-bucket verdict. Both are captured in
[`openness-class-map.json`](../openness-class-map.json).

**Class → 0–5 gradient** (`OPEN` dict in `render.py`) — the normalized, cross-category
spectrum coordinate:

| class | label | gradient |
|-------|-------|----------|
| `open_source` | Open source | 5 |
| `open` | Open data | 5 |
| `open_core` | Open core | 4 |
| `open_weights` | Open weights | 3 |
| `source_available` | Source available | 2 |
| `restricted` | Restricted | 2 |
| `gated` | Gated | 2 |
| `closed` | Closed | 1 |
| `open_hardware` | Open hardware | 5 |
| `open_toolchain` | Open toolchain | 3 |
| `documented` | Documented | 2 |

The last three are the **hardware** openness vocabulary (product `type: hardware`):
open schematics + toolchain = `open_hardware`; proprietary silicon but open SDK/datasheets +
retail-available = `open_toolchain`; datasheets public but proprietary design / firmware blobs =
`documented`; NDA/private-sale = `restricted` (shared with the model vocabulary).

**Class → three-bucket verdict** (`vbucket()` in `render.py`) — the coarse spectrum:

- **open** = `open_source` / `open` / `open_core` / `open_hardware`
- **open-ish** = `open_weights` / `source_available` / `gated` / `open_toolchain`
- **closed** = `restricted` / `closed` / `documented`

## The license scale

One scale across every product type. It is a **cap on the score, not the score**: the license
sets the ceiling, and the artifact dimensions decide where below it a product lands. Every
ladder checks `weights: closed` or `source: closed` before any license rung, so an OSI license
on something nobody can run is still a 1.

| cap | test | tier names |
|---|---|---|
| **5** | OSI-approved, or open by the Open Definition for data | `osi`, `open_data` |
| **4** | not OSI-approved, but no cap on who may use it or at what scale — attribution, naming, conduct | `permissive_non_osi` |
| **3** | commercial use permitted but bounded — a MAU ceiling, a revenue ceiling, an acceptable-use policy | `use_bounded` |
| **2** | commercial use prohibited or reserved to the vendor, though source or weights are published | `commercial_forbidden`, `competition_restricted`, `noncommercial` |
| **1** | nothing published to license | `proprietary`, `unstated` |

**The 3/2 boundary asks one question: does the license permit commercial use at all?** That is
what separates Meta's 700M-MAU clause and AI21's $50M-revenue clause — which bind almost
nobody — from CC-BY-NC and Mistral's Non-Production License, which bind everyone. It is also
where MOF draws its own line: Class III, its entry point, requires components usable
"including for commercial and educational purposes".

The tier names still differ per ladder, because a corpus and a codebase carry different
license families. The **caps** are what is universal.

### What it changed, and why it was needed

Before the scale, the same license family was scored two ways. `Llama-3.1-Community` was
`3/open_weights` on `llama-guard` in `safeguards` and `2/restricted` on `llama-instruct` in
`finetuned_chat`. `CC-BY-NC` capped `command-r` at 2 while `CC-BY-NC-SA` left `personahub` at
5. Ten products carry a bounded commercial license; six were recorded 2 and four were recorded
3.

Applying the scale on 2026-08-01 moved seven scores: six from `2/restricted` to
`3/open_weights` (`llama`, `codellama`, `llama-instruct`, `tulu`, `jamba-large`, `codegemma`)
and `personahub` from `5/open` to `2/restricted`. Four products deferred in `safeguards`
resolved without being touched, because they were already recorded where the scale puts them.

Two things worth knowing about the shape of it:

- **A full open recipe does not lift a capped license.** `tulu` releases its post-training
  data, code and RLVR recipe under Apache-2.0 and still scores 3, because the license rung
  fires ahead of the data and code rungs. The recipe is credited where it lives —
  `tulu-3-sft-mixture` is 5/open in `training_synthetic_datasets`, and the same recipe produces
  `olmo-3-instruct` at 5/open_source on an open base.
- **`restricted` joined the dataset class vocabulary** for this. Datasets were the only product
  type with no word between `open` and `gated`, which is exactly how a non-commercial corpus
  came to sit in the `open` bucket.

## How the buckets relate to MOF and OSAID

The Model Openness Framework and the OSI's Open Source AI Definition are both **binary**.
MOF says so directly: openness "has always been a binary decision in the open-source
movement", and it warns the reader not to read its Class I/II/III as a gradient — those
classes measure how *complete* a release is, once it has already passed the license test.
OSAID requires the freedom to use a system "for any purpose", so a field-of-use or commercial
restriction disqualifies. Under MOF, a release under OpenRAIL, a Llama community license or
AI2 ImpACT is *source-available*, not open.

This map is a 0–5 score, which is a different instrument. The 2024 Columbia Convening
catalogs three families of approach — gradient, score, and binary — and adopts none; the
score family is the one the map belongs to.

The two stay compatible through one rule:

> **The `open` bucket requires a license that is open by an external standard** — OSI
> approval for code and weights, the Open Definition for data. The score may subdivide the
> region below that line as finely as it likes, and nothing below it enters the `open`
> bucket.

So MOF's binary line sits between the `open` bucket and the `open-ish` bucket, exactly where
MOF puts it, and our 4/3/2/1 subdivide what MOF treats as one undifferentiated
"source-available" bucket. `render.py` calls this the "strict OSI/MOF cut".
`tests/test_openness_buckets.py` enforces it against every ladder, and it is a live check
rather than a comment: `software.yaml` carried two rungs emitting `open_core` and
`open_source` from its `permissive_non_osi` tier, and they went unnoticed because that tier's
`examples` list is empty so the rungs could never fire.

### Two places the map deliberately departs from MOF

Both are choices, not oversights, and neither moves the binary line.

- **We are stricter than MOF Class III.** Class III is MOF's entry point and needs
  architecture, final weights, and light documentation including a *data card* — not the
  data. So an Apache-2.0 open-weights model with a good card and closed training data is
  fully open under MOF and scores **3/`open_weights`** here. Do not read our 5 as Class I or
  our 3 as failing MOF. We are tighter than Class III on training data and looser than
  Class I, which additionally wants the research paper, intermediate checkpoints and
  training logs — none of which we score.
- **We rank acceptable-use policies above commercial caps; MOF ranks neither.** MOF excludes
  a release that implements "restrictions or acceptable uses" outright. We put an
  attribution-or-conduct license at 4 and a 700M-MAU commercial cap at 3, on the reasoning
  settled in issue #117: a prohibition on illegal or military use caps neither commerce nor
  reach, and collapsing it into the same bucket as a revenue ceiling discards information the
  map exists to surface. Both still sit below the `open` bucket, so the outcome agrees with
  MOF even where the reasoning does not.

### Where the boundary is currently weakest

The **dataset** vocabulary has no middle. Its classes are `open`, `gated`, `restricted`
and `closed`, and `open` is the only word above `gated`, so every corpus classed `open` sits
in that bucket — 51 products today, including one at 3 and six at 4. A model at 4
is `open_weights` and open-ish; a corpus at 4 is `open`. `the-pile` (license deferring to
per-subset terms, Books3 withdrawn) and `stack-edu` (deferring to The Stack v2's gated terms)
are counted as open on that basis. Closing it means giving the vocabulary a middle class and
re-scoring, so the two rungs involved sit in `KNOWN_VIOLATIONS` in the bucket test with the
reasoning attached, and the test fails if that list stops being accurate in either direction.

**Hardware has no license gate at all.** `hardware.yaml` scores design, toolchain and
availability rather than a source license, by design, and `open_hardware` sits at 5 in the
`open` bucket. The analogue that keeps the rule honest is OSHWA certification plus design
files under a license permitting reuse, which is what `beagley-ai` has. That analogue should
be written into the ladder when `edge_hardware` gets a recipe rather than left implicit.

## Caveats — these are editorial choices

The mapping is the analysts' judgment, not a law of nature. Two things to know before you
lean on it:

- **The gradient and the bucket don't perfectly align.** `source_available`, `restricted`,
  and `gated` all share gradient = 2, but bucket differently: `source_available` and `gated`
  are *open-ish* while `restricted` is *closed*. If your visualization shows both a fine
  gradient and a coarse bucket, expect them to disagree at the 2-fill band.
- **Some distinctions collapse.** `open_source` and `open` both map to 5; `documented`
  and `closed` both sit in the closed bucket. That's intentional for the map but may be too
  coarse depending on what you're showing.

If you want a different lens than the published map, you're free to define one — just do it
deliberately and note where it diverges from this table.
