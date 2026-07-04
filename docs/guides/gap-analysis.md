# Gap Analysis

Gap analysis assigns every stack-map category two derived attributes, computed
deterministically from the scores of the products in that category:

- a **maturity stage** (`0`–`5`) — how far the category's *open* ecosystem has progressed
  toward parity with the best available option, and
- a **set of gaps** — what is missing for it to advance.

Both are recomputed from source on every build, so they never drift from the underlying
product scores. They are emitted per category into `build/notebook_data.json` as
`stage` (`{num, name}`) and `gaps` (a list, possibly empty), alongside `layer`, and the
published notebook renders them as a stage badge with gap chips.

Stages and gaps are assigned at the **category** level. Placing individual products on the
ladder, or splitting a category into sub-bands, is a possible later refinement; it does not
change the model below.

## The model

A category's open ecosystem climbs a ladder from **Void** (no usable open option) to a
**Mature Open Ecosystem** (several open options are strong, widely used, and redundant). The
stage is the rung it currently occupies. The gaps name what is keeping it off the next rung.

Openness is treated as an axis **orthogonal** to maturity: a category can have strong,
widely-adopted options that simply aren't *fully* open (e.g. open-weights rather than
open-source). That situation is the **openness gap** — the distinction the map exists to
surface — and it is reported independently of how mature the ecosystem is otherwise.

## Inputs (per product)

- **Openness bucket** — `openness.class` collapsed to `open` / `open-ish` / `closed` via the
  canonical map in [`openness-class-map.json`](../openness-class-map.json). "Fully open" means
  the `open` bucket; "open-ish" is partial openness (e.g. open-weights, source-available).
- **Adoption** — `adoption.level` (1–5).
- **Capability** — `capability.score` (1–5; for a dataset this is its *training value under
  frontier-style evaluation* — how good the models built on it are on standard, largely English
  and benchmark-driven evals — from ablations and downstream-model evidence. It does not capture
  consent, licensing, documentation, or language coverage; a low score means "not the current
  pick for that objective," not "low quality." May be null where no defensible basis exists yet).
- **Per-category weights** — `weights.adopt` and `weights.cap`, so each category blends the two
  axes according to what matters most for that part of the stack.

## Maturity score and the "mature" bar

Each product gets a single **maturity score** on a 1–5 scale from a per-category linear blend,
normalized by the weight sum so it stays on the 1–5 scale for any weights:

```
score = (weights.adopt · adoption + weights.cap · capability) / (weights.adopt + weights.cap)
```

Where a product's capability has no defensible basis it may be null, in which case the product
is graded on adoption alone. A product is **mature** when its score clears a high threshold (a
near-best-on-both-axes bar). The bar is intentionally demanding: because the map curates the
most prominent products in each category, a low bar would call almost everything mature.

## Dataset categories

Datasets are scored on both axes like everything else, but each axis is read specifically for a
corpus. Adoption is verified download volume, graded against corpus-specific bands one order of
magnitude below the package bands (see the *Training-corpus bands* section of `CONTRIBUTING.md`):
a multi-terabyte corpus is pulled per training run, not per CI job, so package-scale download
floors would make maturity unreachable. Capability is the corpus's *training value* — how good
the models built on it are — from controlled ablations and downstream-model evidence, which is
also where documented reuse counts (crediting it to adoption too would double-count the same
signal). Benchmark datasets keep the standard adoption bands, because small evaluation sets are
pulled by harnesses on every run and their download counts behave like packages.

The headline finding for `training_synthetic_datasets` is a **monoculture**: every mature
fully-open corpus today is filtered Common-Crawl English web text (FineWeb-Edu, DCLM, Dolma 3).
The multilingual, preference, and reasoning roles lag well behind — capable corpora exist
(FineWeb-2, MADLAD-400, Aya, UltraFeedback) but none clears the maturity bar — so the category's
Stage 4 reflects English web pretraining specifically, not a broadly mature open data ecosystem.
This is partly a property of the category mixing roles — pretraining corpora, SFT mixtures, and
preference sets are graded against different yardsticks (knowledge benchmarks versus
instruction-following or preference wins), so capability is read per role and cross-role
comparison within the category is looser than in the single-purpose categories.

Training data is also where the `disclosure` gap is declared (see *Declaring the disclosure gap*
below): the open corpora are real and shared, but the frontier's proprietary and licensed data
and its exact mixing recipe stay invisible, and that asymmetry is the finding worth surfacing.

## Counting rule: open-only

Only **fully-open** products count toward a category's maturity and stage. Open-ish products do
not advance the stage — they are used solely to detect the openness gap. The rationale: the
ladder measures **fully-open-pipeline maturity** — the health of the genuinely-open ecosystem —
and crediting partially-open products to it would blur exactly the open-source-vs-open-weights
line the map is built to expose. Open-weights models therefore never advance a stage. Counting
also distinguishes depth from a single standout (see Stage 5).

This is consequential but bounded: counting open-weights as fully open would move only three
categories, all in the model layer (`base_pretrained` 3→5, `finetuned_chat` 2→3,
`edge_hardware` 3→4), and would leave every infrastructure and tooling verdict unchanged.

## Stages

| Stage | Name | Condition |
|------:|------|-----------|
| **5** | Mature Open Ecosystem | enough mature fully-open products to be redundant/resilient |
| **4** | Competitive Open Ecosystem | at least one mature fully-open product, but not yet enough for depth |
| **3** | Viable Alternatives | no mature fully-open product, but the best fully-open option is strong |
| **2** | Emerging Alternatives | no mature fully-open product; the best fully-open option is promising but limited |
| **1** | Open Experiments | fully-open options exist but are weak on both axes |
| **0** | Void | no usable open option exists (and nothing is mature anywhere) |

The exact count and score cutoffs that separate the stages are policy parameters (below),
chosen so the ladder discriminates rather than bunching categories at one rung.

## Gaps

Gaps are a **set** (zero or more) per category, so a category can carry more than one. They are
derived from the same metrics as the stage:

- **`void`** — no usable open option at all.
- **`capability`** — the best fully-open option isn't capable enough to be useful.
- **`adoption`** — a capable fully-open option exists but is under-adopted.
- **`maturity`** — open options exist and at least one may be mature, but the ecosystem lacks
  the depth/redundancy of a mature ecosystem (too few mature fully-open products).
- **`openness`** — capable, adopted options exist, but the mature ones are not fully open
  (open-ish or closed). This is the orthogonal flag; it can co-occur with the others.
- **`disclosure`** — the open products are real and widely used, but the closed frontier's own
  equivalent is undisclosed: labs publish neither their proprietary and licensed data nor their
  exact recipe. The gap is the invisibility of the frontier's data, not the absence of open
  data. Unlike the other gaps it is **declared per category**, not inferred (see below), and it
  can appear at **any** stage, including Stage 5.

A fully mature ecosystem carries no gaps — with one exception: `disclosure` can still be
flagged at Stage 5, because it describes the closed frontier's silence, not a shortfall of the
open ecosystem.

### Declaring the disclosure gap

`disclosure` is set with `disclosure_gap: true` in the category file, not derived from the
product scores. It is an editorial judgment about the *closed* world, which the open products'
scores cannot express, so making it explicit keeps it from silently toggling when the roster
changes. Set it where the open products are inputs whose closed-frontier equivalent (proprietary
data, licensed corpora, the exact mixing recipe) is structurally undisclosed — training data is
the clear case. Do **not** set it where the open products are the shared public standard the
frontier reports against: open evaluation benchmarks, for instance, are what closed models are
measured on in public, so there is no comparable invisibility and `benchmark_eval_data` leaves
the flag unset.

The set is **extensible**: new gap types (for example *maintenance* or *bus-factor* risk, once
those signals are tracked) can be added without changing the staging logic — they are simply
additional flags computed per category.

## Worked example (illustrative)

A hypothetical category whose strongest, most-adopted products are all open-*weights* (not
open-source), with only weak fully-open options behind them: it has no mature *fully-open*
product, so it sits low on the ladder (Viable / Emerging) and carries a **maturity** gap; and
because capable, adopted options do exist but aren't fully open, it also carries an
**openness** gap. Contrast a category with several strong, widely-used open-source libraries:
multiple mature fully-open products → Stage 5, no gaps.

## Policy parameters

The thresholds are deliberate, tunable choices rather than fixed law. They live as named
constants at the top of the gap-analysis block in `build/serialize.py`:

- the **mature** score threshold,
- the count of mature fully-open products required for **Stage 5**,
- the best-fully-open score bands that separate **Stages 1–3**,
- the raw capability cutoff that splits a `capability` gap from an `adoption` gap.

Adjusting them shifts how demanding each rung is; they should be reviewed when the scoring
rubric or the curation density changes materially.

## Where it lives

- **Computed** in `build/serialize.py` (`_stage_and_gaps`), from the per-product scores in
  `sources/scores/` and the per-category `weights` in `sources/categories/`.
- **Emitted** into `build/notebook_data.json` per category (`stage`, `gaps`). The
  plain-language definitions of every stage and gap ship in the payload's top-level
  `descriptions` block (`descriptions.stages`, `descriptions.gaps`, plus the neutral
  per-category one-liner in `descriptions.categories`), so a consumer can render a
  legend without re-deriving this document. Each product also carries its openness
  `bucket` (`open` / `open-ish` / `closed`) alongside the raw `class`.
- **Displayed** in the published notebook as a maturity-ladder table (each category placed on
  its stage). The per-category gap set is carried in the payload for downstream consumers
  rather than shown inline.

For the current assignments, read the live notebook payload — they are regenerated on every
build and are intentionally not duplicated here.
