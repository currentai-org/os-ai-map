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
| `openness.class` | categorical | An OSI / Model Openness Framework (MOF) label: `open_source`, `open_weights`, `open_core`, `source_available`, `restricted`, `gated`, `documented_only`, `closed`, `open`. |
| `openness.score` | integer 0–5 | A graded openness score with a `components` breakdown (models: `weights / data / code / checkpoints / license`; software: OSI-class license tests; datasets: access / license / documentation). |

Both are assigned by hand against MOF/OSI, with a required primary `sources:` entry for
every non-null value. There is **no deterministic formula** in the repo that computes the
score from inputs. (The `add-product` skill references a per-category `scoring_recipe`, but
that optional field is currently not populated on any category — scoring is editorial
judgment documented in `components`/`note`.)

## Why the raw score is not comparable across categories

The 0–5 score is graded relative to what's achievable *within a product type*, so the same
number means different things in different categories. A quick cross-tab of `score | class`
across all score files shows the overlap:

| score | classes that appear at this score |
|-------|-----------------------------------|
| 5 | `open_source`, `open` |
| 4 | `open_core`, `open_source`, `open_weights`, `open`, `gated` |
| 3 | `open_weights`, `open_core`, `source_available` |
| 2 | `restricted`, `open_core`, `source_available`, `gated` |
| 1 | `closed` |
| 0 | `closed` |

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
