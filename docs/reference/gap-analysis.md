# Gap Analysis

Gap analysis assigns every stack-map category two derived attributes, computed
deterministically from the scores of the products in that category:

- a **Maturity Stage** (`0`–`5`) — how far the category's *open* ecosystem has progressed
  toward parity with the best available option, and
- a **set of gaps** — what is missing for it to advance.

"Maturity" names the category-level stage and nothing else. The per-product number that used to
share the word is the **overall score** (see below); the two were never a roll-up of each other,
and one word for both is what made the old `maturity` gap ambiguous.

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

## Overall score, and what the 4.5 bar actually means

Each product gets a single **overall score** on a 1–5 scale from a per-category linear blend of
its two graded axes, normalized by the weight sum so it stays on the 1–5 scale for any weights:

```
score = (weights.adopt · adoption + weights.cap · capability) / (weights.adopt + weights.cap)
```

Where a product's capability has no defensible basis it may be null, in which case the product
is graded on adoption alone. A fully-open product reaches the top **Leading** tier when its
score clears 4.5.

**The bar is worth stating plainly, because it has never been written down.** Both grades are
whole numbers from 1 to 5, so clearing 4.5 always takes **a 5 on at least one axis.** A product
graded 4 and 4 — strong on both counts — lands at exactly 4.0 and does not qualify, and that 4/4
group is the largest single one on the map. Whether the second axis can be a 4 or must also be a
5 depends on the category's weights: with an even split a 5 and a 4 average to 4.5, but where one
axis is weighted more heavily a 5 on the lighter axis needs a 5 on the heavier one too. That is
the right bar for a map that already curates the most prominent products in each category; a
lower one would put almost everything at the top.

### Score tiers

The same two boundaries name the product-level tiers, emitted per product as `tier`:

| Tier | Score | Meaning |
|---|---|---|
| **Leading** | score ≥ 4.5 | overall score in this band, over the product's available measured axes |
| **Strong** | 4.0 ≤ score < 4.5 | overall score in this band; a product graded 4 and 4 lands here |
| *(none)* | score < 4.0 | — |

Each band names the overall score computed from the product's *available measured axes* — it is
not a claim about both. Where both axes are measured they are whole numbers 1–5, so reaching 4.5
always needs a 5 on at least one axis (with the partner axis's required grade set by the category
weights); a product graded on adoption alone is banded on that score without asserting a
capability grade it does not have.

Tiers are derived from the score alone, across every openness bucket, because they describe the
*product*. The legacy `mature` flag is the same 4.5 bar gated on the fully-`open` bucket — that
is, `tier == "leading" and openness.bucket == "open"` — because only fully-open products advance
a category's stage. A closed product can therefore be Leading and not mature; that is the
intended reading, not a contradiction.

**Leading and depth say different things on purpose.** Leading is about one product being best
in class. The `depth` gap below is about a category not having enough of them.

### Field names

The per-product score ships under two keys during the migration: **`overall_score`** (current)
and **`maturity`** (retained for one release so the front end and the warehouse can move over
before it is removed). Same value, including the null. New consumers read `overall_score`.

The boolean `mature` is likewise legacy, kept for one release. Its replacement is not a single
field but a pair a consumer already has: `mature` is exactly `tier == "leading" and
openness.bucket == "open"`. The migration mapping is therefore:

| Legacy field | Replacement |
|---|---|
| `maturity` | `overall_score` |
| `mature` | `tier == "leading"` **and** `openness.bucket == "open"` |

### The two nulls are not symmetric, and one of them is not an abstention

Worth stating plainly, because the code makes them look alike and they behave oppositely:

- **Null adoption abstains.** `_maturity_score` returns `None`, and `_stage_and_gaps` drops the
  product — "we can't judge what we can't measure, so they neither advance nor depress the
  category's stage." Measured 2026-08-13: 20 products, 19 of them `closed`, which the open-only
  counting rule already excluded. The abstention is real and costs nothing.
- **Null capability does not abstain.** It falls through to adoption alone, which silently
  reweights maturity from a blend to a single axis rather than declining to score. The product
  keeps counting toward the stage.

That fallback is right for the case it was written for. 21 of the 26 null-capability products
are in `benchmark_eval_data`, where downloads plausibly *are* the quality signal — a corpus
everyone evaluates against is, by that fact, a good corpus.

**Every other category inherits it by accident.** `model-context-protocol` is the clearest
live case: adoption 5, capability null, `open_source`, so its overall score computes to 5.0 and
it counts as a Leading fully-open product on one axis while a reader assumes two.

**A correction, because this guide got the stakes wrong on first writing.** It claimed that
`agent_tools_protocols`'s stage rested on that null, on the reasoning that one Leading fully-open
product is the entire `stage >= 4` threshold. The rule is real but the inference was not
checked against the category: it has **seven** Leading fully-open products, not one — MCP, `fastmcp`,
`qdrant`, `mcp-python-sdk`, `mcp-typescript-sdk`, `docling`, `markitdown` — and six of them
reach 4.5 from a real adoption *and* a real capability score with no null in the arithmetic.
Seven clears `_STAGE5_MIN_MATURE = 4`, so the category is **stage 5**, and deleting MCP
entirely leaves six and changes nothing. The methodological defect is unaffected; the claim
that a stage depended on it was wrong, and was caught by re-deriving it against
`build/serialize.py` rather than reasoning from the threshold.

So the open question is whether "graded on adoption alone" should be a **per-category
declaration**, like `disclosure` below, rather than a global fallback. It is deliberately not
settled here: it is to be resolved during the `agent_tools_protocols` verification pass, when
`model-context-protocol` gets a real capability score and the question stops being hypothetical.

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

The headline finding for `training_synthetic_datasets` is a **monoculture**: every Leading
fully-open corpus today is filtered Common-Crawl English web text (FineWeb-Edu, DCLM, Dolma 3).
The multilingual, preference, and reasoning roles lag well behind — capable corpora exist
(FineWeb-2, MADLAD-400, Aya, UltraFeedback) but none clears the Leading bar — so the category's
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

| Stage | Name | Definition | Triggers when |
|------:|------|------------|---------------|
| **5** | Mature Open Ecosystem | Multiple fully open products have reached the category's leading tier, creating a deep and competitive open ecosystem. | `L >= 4` |
| **4** | Competitive Open Ecosystem | At least one fully open product has reached the category's leading tier, but the open field is still thin. | `1 <= L <= 3` |
| **3** | Viable Alternatives | Fully open options are genuinely viable, but none has reached the category's leading tier. | `L = 0`, `B >= 3.5` |
| **2** | Emerging Alternatives | Fully open products are becoming credible options, but remain meaningfully behind the category's strongest options. | `L = 0`, `3.0 <= B < 3.5` |
| **1** | Open Experiments | Fully open products are absent or remain far behind the category's strongest options. | `L = 0`, `B < 3.0` |
| **0** | Void | The category is still nascent overall, with no leading products and no meaningful fully open options. | `L = 0`, `B < 2.0`, and nothing anywhere reaches the Leading tier |

The **Definition** column is quoted verbatim from `_STAGE_DESC` in `build/serialize.py` and is
what ships in the payload. **Triggers when** is the mechanism, which the payload never carries:
`L` is the number of fully-open products at or above the Leading bar, and `B` is the best
fully-open overall score (`0` when the category has no scored fully-open product at all).
Rules are evaluated top down, so Stages 5 and 4 are decided on count alone before any score
band is considered.

The exact count and score cutoffs that separate the stages are policy parameters (below),
chosen so the ladder discriminates rather than bunching categories at one rung.

## Gaps

Gaps are a **set** (zero or more) per category, so a category can carry more than one. They are
derived from the same metrics as the stage:

- **`void`** — No usable fully open option exists at all.
- **`capability`** — Fully open products exist, but they lack the capabilities needed to compete with the category's strongest options.
- **`adoption`** — Fully open products have not reached the adoption of the category's strongest options.
- **`depth`** — Fully open products have reached the category's leading tier, but there are too few to create a deep and resilient open ecosystem.
- **`openness`** — Products have reached the category's leading tier, but none of them is fully open.
- **`disclosure`** — Closed products rely on data or training recipes that are not disclosed, limiting visibility into how they are built and how they compare with fully open products.

Those six sentences are quoted verbatim from `_GAP_DESC` in `build/serialize.py`: they are
the text the payload carries and the text a reader sees in the site legend and the category
drawer. Edit them in one place and copy across. Everything else in this document — which
rung each gap fires on, the thresholds behind it, whether it is derived or declared — is the
mechanism, and is deliberately absent from the payload.

A fully mature ecosystem carries no gaps — with one exception: `disclosure` can still be
flagged at Stage 5, because it describes the closed frontier's silence, not a shortfall of the
open ecosystem.

### How they are assigned

| Stage | Gaps |
|---|---|
| 5 | none (except a declared `disclosure`) |
| 4 | `depth` |
| 1–3 | `capability` and/or `adoption` (or neither), plus `openness` where it applies |
| 0 | `void` |

**`depth` fires at Stage 4 only.** Stage 4 means a category has proven Leading open options but
not enough for redundancy, so the shortfall is genuinely count rather than quality. Defining
depth as "no Leading open product at all" would extend it over the weaker categories and
rebuild the problem this taxonomy replaced: the old `maturity` gap fired in 12 of 16 categories
and so distinguished between none of them. Below Stage 4 the stage number already says no
Leading open option exists, and `capability` and `adoption` say why.

**At Stages 1–3 the drivers are read off the best fully-open product** — the one with the
highest overall score. Its capability is a `capability` gap when it falls below the capability
cutoff, its adoption is an `adoption` gap when it falls below the adoption cutoff, and **both
fire where both apply.** There is no longer a rule emitting a single diagnostic per category.
That rule checked openness first, which is why `capability` was unreachable and never once
appeared: `edge_hardware`'s only fully-open board is genuinely underpowered, and the category
reported an openness gap instead, so nobody reading the map could see it.

**A category at Stages 1–3 can carry no driver gap, and that is allowed.** If both measured axes
clear their cutoffs and the blend still misses 4.5, neither driver fires and the category carries
only whatever `openness` applies — possibly nothing. The stage number already says the category
has not reached the leading-product threshold; inventing an adoption or capability shortfall where
the axis clears its cutoff would be a knowingly false label. Exactly one category is in this state:
`benchmark_eval_data`, whose fully-open benchmarks are adoption 4 with a **null capability**, so
the blend is adoption alone and tops out at 4.0 — adoption is not short, capability is simply
unmeasured. The fix is to score capability for evaluation sets — the axis is already applied to 4
of that category's 27 products — which is filed separately. If unmeasured axes become common
enough to name, add a gap for that state deliberately rather than reusing an inaccurate one.

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
open-source), with only weak fully-open options behind them: it has no Leading *fully-open*
product, so it sits low on the ladder (Viable / Emerging) and carries a **capability** gap,
an **adoption** gap, or both, depending on which axes hold the best fully-open option back; and
because capable, adopted options do exist but aren't fully open, it also carries an **openness**
gap. Contrast a category with one strong, widely-used open-source library and nothing behind it:
Stage 4, a **depth** gap, nothing wrong with the library itself. Contrast again with several
such libraries: Stage 5, no gaps.

## Policy parameters

The thresholds are deliberate, tunable choices rather than fixed law. They live as named
constants at the top of the gap-analysis block in `build/serialize.py`:

- the **Leading** score threshold (the 4.5 bar, retained as the legacy `mature` bar),
- the **Strong** tier boundary,
- the count of Leading fully-open products required for **Stage 5**,
- the best-fully-open score bands that separate **Stages 1–3**,
- the raw capability and adoption cutoffs that decide which drivers fire at Stages 1–3.

Adjusting them shifts how demanding each rung is; they should be reviewed when the scoring
rubric or the curation density changes materially.

## Where it lives

- **Computed** in `build/serialize.py` (`_stage_and_gaps`), from the per-product scores in
  `sources/scores/` and the per-category `weights` in `sources/categories/`.
- **Emitted** into `build/notebook_data.json` per category (`stage`, `gaps`). The
  plain-language definitions of every stage, gap and score tier ship in the payload's top-level
  `descriptions` block (`descriptions.stages`, `descriptions.gaps`, `descriptions.tiers`, plus
  the neutral per-category one-liner in `descriptions.categories`), so a consumer can render a
  legend without re-deriving this document. Each product also carries its openness
  `bucket` (`open` / `open-ish` / `closed`) alongside the raw `class`, its `overall_score`
  (and, for one more release, the same number as `maturity`), and its `tier`.
- **Displayed** in the published notebook as a maturity-ladder table (each category placed on
  its stage). The per-category gap set is carried in the payload for downstream consumers
  rather than shown inline.

For the current assignments, read the live notebook payload — they are regenerated on every
build and are intentionally not duplicated here.
