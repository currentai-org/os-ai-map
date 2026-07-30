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
| `openness.class` | categorical | An OSI / Model Openness Framework (MOF) label. In use today, by frequency: `open_source`, `closed`, `open`, `open_weights`, `open_core`, `source_available`, `documented`, `gated`, `restricted`, `open_toolchain`, `open_hardware`. `documented_only` is also defined in the vocabulary but no product currently carries it. [`openness-class-map.json`](../openness-class-map.json) is the authoritative list. |
| `openness.score` | integer 0–5 | A graded openness score with a `components` breakdown (models: `weights / data / code / checkpoints / license`; software: OSI-class license tests; datasets: access / license / documentation). |

Every non-null value needs a primary `sources:` entry. Both fields were originally assigned
by hand against MOF/OSI, and that history is why `components`/`note` read as editorial prose.

**A deterministic formula now exists for most of the map.** 13 of the 16 categories declare a
`scoring_recipe` that names an ordered rule list over dimension values, and
`build/check_rubric.py` replays it against each product's recorded `components` to check that
the recorded score is the one the rules produce. Most recipes `extend` a shared ladder in
[`sources/rubrics/`](../../sources/rubrics/) rather than restating one: `software.yaml` covers
eleven categories, `model.yaml` the fine-tuned and guardrail models. A category holding more
than one kind of product maps `extends` per product type.

Three caveats, because "a formula exists" is easy to over-read:

- **The remaining three categories have no recipe yet** — `benchmark_eval_data`,
  `training_synthetic_datasets` and `edge_hardware`, 85 products. Their scores are still
  editorial only.
- **A recipe reproducing a score does not validate it.** It shows the rules describe how the
  category was scored. The document-grade evidence the checker reads was parsed out of the
  same files the scores live in, so agreement is a fidelity check on the formula, not on the
  facts.
- **A category can hold products back.** `scoring_recipe.deferred` lists products the rules do
  not decide, usually because a dimension is not recorded in a form the ladder can read. There
  are 89 such products across 10 categories, and `safeguards` currently defers all 26 of its
  own. Deferred products publish no openness evidence to the warehouse.

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

Regenerated 2026-07-30. The overlap is narrower than it was: #128's verification gate G3 found
17 pairs no rule in any recipe could emit and corrected them, which is why `open_core` and
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
| `documented_only` | Documented only | 1 |
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
- **closed** = `restricted` / `documented_only` / `closed` / `documented`

## Caveats — these are editorial choices

The mapping is the analysts' judgment, not a law of nature. Two things to know before you
lean on it:

- **The gradient and the bucket don't perfectly align.** `source_available`, `restricted`,
  and `gated` all share gradient = 2, but bucket differently: `source_available` and `gated`
  are *open-ish* while `restricted` is *closed*. If your visualization shows both a fine
  gradient and a coarse bucket, expect them to disagree at the 2-fill band.
- **Some distinctions collapse.** `open_source` and `open` both map to 5; `documented_only`
  and `closed` both map to 1. That's intentional for the map but may be too coarse depending
  on what you're showing.

If you want a different lens than the published map, you're free to define one — just do it
deliberately and note where it diverges from this table.
