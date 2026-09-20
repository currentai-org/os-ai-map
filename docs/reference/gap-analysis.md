# Gap Analysis

Gap analysis assigns every stack-map category two derived attributes, computed
deterministically from the scores of the products in that category:

- a **Maturity Stage** (`0`–`5`) — how far the category's *open* ecosystem has progressed
  toward parity with the best available option, and
- a **set of gaps** — what is missing for it to advance.

"Maturity" names the category-level stage and nothing else. The per-product number is the
**overall score** (see below), and the two are not a roll-up of each other. One word for both is
what makes a `maturity` gap ambiguous, which is why neither carries it.

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
is graded on adoption alone. A fully-open product reaches the top **category-leading** tier when its
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
| **Category-leading** | score ≥ 4.5 | overall score in this band, over the product's available measured axes |
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
a category's stage. A closed product can therefore be category-leading and not mature; that is the
intended reading, not a contradiction.

**Category-leading and resiliency say different things on purpose.** Category-leading is about one product being best
in class. The `resiliency` gap below is about a category not having enough of them.

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
  category's stage." Measured 2026-09-20: 39 products, 38 of them `closed` and one
  `source_available`, every one of which the open-only counting rule already excluded. The
  abstention is real and costs nothing.
- **Null capability does not abstain.** It falls through to adoption alone, which reweights
  maturity from a blend to a single axis rather than declining to score. The product keeps
  counting toward the stage. It has a second effect worth stating because the code does not:
  a null **suppresses the PER-PRODUCT capability driver gap**. That reading fires when the best
  fully-open product's capability is below the cutoff, and a null is not below anything — it is
  not comparable at all — so it cannot fire.

  It does **not** suppress the category-level reading. When neither per-product driver fires,
  `_stage_and_gaps` falls through to `_unreached_axes` over every fully-open product, and that can
  still name `capability`: it asks whether any fully-open product has topped the axis, which a
  null in the best product does not answer either way. So the null closes one of the two readings,
  not both, and a category whose best fully-open product abstains usually still carries a gap —
  `compilers` and `dataset_processing_tools` both report `adoption` from the per-product read.

  A genuinely empty gap set at Stages 1-3 therefore needs the category-level reading to be silent
  too, which happens only when an axis is unrecorded across the whole fully-open population or has
  been topped somewhere in it. That is narrow and no category is in it today;
  `benchmark_eval_data` is the category that reaches it whenever its capability recipe is live
  rather than abstaining. The shape is general, which is why it is documented rather than left to
  be rediscovered.

That fallback is right for the case it was written for. Most null-capability products
are in `benchmark_eval_data`, where downloads plausibly *are* the quality signal — a corpus
everyone evaluates against is, by that fact, a good corpus.

**It reaches every other category too.** `model-context-protocol` is the clearest live case:
adoption 5, capability null, `open_source`, so its overall score computes to 5.0 and it counts as
a category-leading fully-open product on one axis where a reader might assume two.

`agent_protocols` shows what that looks like at category scale. Six fully-open products sit at
4.5 or above — `model-context-protocol`, `ag-ui`, `mcp-apps`, `mcp-python-sdk`,
`mcp-typescript-sdk` and `fastmcp`. Three carry a real capability score; three reach 5.0 on
adoption with capability null. Six clears `_STAGE5_MIN_MATURE = 4` with room, so the category is
**stage 5** and no single product carries it: drop any one and five remain. A category-leading
fully-open product is not by itself a stage, and reading the threshold without reading the
roster will suggest otherwise.

**Both effects are the settled behavior, and neither is a bug.** A category whose best
fully-open product abstains on capability is graded on adoption alone: the product is NOT dropped
from the stage computation the way a null adoption drops it, and the empty gap set is not marked.
The reasoning is that these categories genuinely lack a capability signal worth grading on, so
adoption alone is the honest reading rather than a fallback that happens to be reachable.
`benchmark_eval_data` is the standing example: a capability recipe was written for its corpora,
tested, and rejected, and the category returned to abstaining.

Grading on adoption alone is therefore a **convention of this methodology**, not a per-category
declaration and not a flag a reader sees. It follows from the axis being null, which is itself a
recorded editorial judgment carrying its own reasoning in the score file. Two consequences a
reader of the map should know:

- an overall score built from adoption alone is on the same 1-5 scale as one built from both
  axes, and `overall_score` itself carries no marker of which. The payload does not hide the
  difference — the product's `capability` block is emitted with `score: null` beside a non-null
  `adoption.level`, so a consumer can tell — but nothing in the blended number says so, and
  nothing in the category's stage or gaps does either;
- a category can sit at Stages 1-3 with no gaps named. That is not by itself evidence of an
  ungraded shortfall: the paragraph below on the two gapless states describes a second route to
  it, where both axes have been topped but never in the same product. Which one a category is in
  is answered by reading its products, not by the empty set.

Adoption-only grading is not a per-category declaration like `disclosure`, and does not become
one: it follows from the axis being null, which is already recorded per product.

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

The headline finding for `training_synthetic_datasets` is a **monoculture**: every category-leading
fully-open corpus today is filtered Common-Crawl English web text (FineWeb-Edu, DCLM, Dolma 3).
The multilingual, preference, and reasoning roles lag well behind — capable corpora exist
(FineWeb-2, MADLAD-400, Aya, UltraFeedback) but none clears the category-leading bar — so the category's
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
also distinguishes resiliency from a single standout (see Stage 5).

This is consequential but bounded: counting open-weights as fully open would move only a few
categories, all in the model layer (measured 2026-09-20: `base_pretrained` 3→5,
`finetuned_chat` 3→4, `edge_hardware` 3→4, `scientific_ai_models` 1→3), and would leave every
infrastructure and tooling verdict unchanged.

## Stages

| Stage | Name | Definition | Triggers when |
|------:|------|------------|---------------|
| **5** | Mature Open Ecosystem | Several fully open products lead the category, so no single project carries it. | `L >= 4` |
| **4** | Competitive Open Ecosystem | A small number of fully open products lead the category. | `1 <= L <= 3` |
| **3** | Viable Alternatives | Fully open options are proven in real use, but none leads the category. | `L = 0`, `B >= 3.5` |
| **2** | Emerging Alternatives | Fully open products are becoming credible, but remain limited in adoption or capability. | `L = 0`, `3.0 <= B < 3.5` |
| **1** | Open Experiments | Fully open products are absent or remain substantially limited in adoption, capability, or both. | `L = 0`, `B < 3.0`, and (`B >= 2.0` or `M`) |
| **0** | Void | The category is still nascent overall, with no category-leading products and no meaningful fully open options. | `L = 0`, `B < 2.0`, and not `M` |

The **Definition** column is quoted verbatim from `_STAGE_DESC` in `build/serialize.py` and is
what ships in the payload. **Triggers when** is the mechanism, which the payload never carries:

- **`L`** — how many fully-open products score at or above the category-leading bar (4.5).
- **`B`** — the best overall score among fully-open products, or `0` where the category has
  no scored fully-open product at all.
- **`M`** — whether *any* product, in any openness bucket, reaches the category-leading bar. Only
  Stages 1 and 0 consult it, and it is what separates them: a category whose open options are
  all feeble is Stage 1 rather than Void when a category-leading closed or open-ish product exists,
  because Void means the whole category is nascent, not merely its open side.

The conditions above are mutually exclusive, so the table can be read in any order. The code
evaluates them 5, 4, 0, 1, 2, 3 and relies on earlier branches to narrow the later ones; the
extra clause on Stage 1 is what that ordering does implicitly.

The exact count and score cutoffs that separate the stages are policy parameters (below),
chosen so the ladder discriminates rather than bunching categories at one rung.

## Gaps

Gaps are a **set** (zero or more) per category, so a category can carry more than one. They are
derived from the same metrics as the stage:

- **`void`** — Needs a usable fully open option at all.
- **`capability`** — Needs a more capable fully open option.
- **`adoption`** — Needs broader adoption of its fully open options.
- **`resiliency`** — Needs more fully open products at the leading tier to be resilient.
- **`openness`** — Needs its category-leading products to be fully open.
- **`disclosure`** — Needs the closed alternatives to disclose their data and training recipes.

Those six sentences are quoted verbatim from `_GAP_DESC` in `build/serialize.py`: they are
the text the payload carries and the text a reader sees in the site legend and the category
drawer. Edit them in one place and copy across.

They are written as needs on purpose. Stage text and gap text render together in the category
drawer, and a **stage says where the category stands** while a **gap says what it needs** — in
one mood they restate each other, because `resiliency` fires if and only if the stage is 4, and the
Stage 3–5 sentences and the `openness` gap otherwise circle the same tier fact. Each gap still
has to read on its own, because the legend shows gap text with no stage beside it.

Everything else in this document — which rung each gap fires on, the thresholds behind it,
whether it is derived or declared — is the mechanism, and is deliberately absent from the
payload.

A fully mature ecosystem carries no gaps — with one exception: `disclosure` can still be
flagged at Stage 5, because it describes the closed frontier's silence, not a shortfall of the
open ecosystem.

### How they are assigned

| Stage | Gaps |
|---|---|
| 5 | none (except a declared `disclosure`) |
| 4 | `resiliency` |
| 1–3 | `capability` and/or `adoption` (or neither), plus `openness` where it applies |
| 0 | `void` |

**`resiliency` fires at Stage 4 only.** Stage 4 means a category has proven category-leading open options but
not enough for redundancy, so the shortfall is genuinely count rather than quality. Defining
resiliency as "no category-leading open product at all" would extend it over the weaker categories
and rebuild the problem this taxonomy exists to avoid: a gap that fires in three quarters of the
map distinguishes between none of it. Below Stage 4 the stage number already says no
category-leading open option exists, and `capability` and `adoption` say why.

**At Stages 1–3 the drivers are read off the best fully-open product** — the one with the
highest overall score. Its capability is a `capability` gap when it falls below the capability
cutoff, its adoption is an `adoption` gap when it falls below the adoption cutoff, and **both
fire where both apply.** No rule emits a single diagnostic per category, because a rule that
emits one has to pick, and picking openness first makes `capability` unreachable:
`edge_hardware`'s only fully-open board is genuinely underpowered, and a category reporting an
openness gap instead leaves nobody reading the map able to see it.

**A driver gap says its axis is short for the category, and that is true in two ways.** The
per-product reading above is the first: the best fully-open product is below the axis cutoff. The
second fires only when the first is silent — **no fully-open product in the category has reached
the top of that axis at all.**

The second clause exists because the first could leave a category saying nothing. The cutoffs are
4 and the maturity bar is 4.5, so a product must reach 5 on an axis to be mature, and one sitting
at exactly 4 and 4 clears both cutoffs while missing the bar. Measured 2026-09-20, 33 fully-open
products across 13 categories sit there. Where such a product is its category's best, the category reported a stage
and no gaps, and a reader was told nothing about what was missing. `compilers` is the case: its
best fully-open option is `coremltools` at 4/4, while `apache-tvm`, `iree` and `xla` reach
capability 5 and, across 44 products, **nothing reaches adoption 5**. The capability exists in the
open and has not been adopted, so the category reports `adoption`.

Both readings are the same gap type rather than two, because both answer the question a reader is
actually asking — which axis is holding this category back — and a seventh chip would buy
precision at the cost of a vocabulary nobody asked to learn.

**Two states still carry no driver gap, deliberately.** An axis that **no** fully-open product
records is unmeasured rather than deficient, and is never named: a category graded on adoption
alone must not be told it has a capability shortfall. A null on the *best* fully-open product alone
is NOT this state — it silences the per-product reading and leaves the category-level one intact, so
a capability gap can still fire from a peer that recorded the axis. See the null-capability rule
above. And a category that has topped both axes,
but never in the same product, reports nothing — the parts exist and nobody has assembled them,
which is a real state this vocabulary cannot yet name. Measured 2026-09-20 it holds in
`agent_protocols`, `agent_tools_connectors`, `finetuning_code`, `inference_code`, `storage` and
`training_synthetic_datasets`, and none of them reaches this branch: all but one are at Stage 4 or
5, and in `agent_tools_connectors` the per-product reading fires first, so the category-level
question is never asked.

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
open-source), with only weak fully-open options behind them: it has no category-leading *fully-open*
product, so it sits low on the ladder (Viable / Emerging) and carries a **capability** gap,
an **adoption** gap, or both, depending on which axes hold the best fully-open option back; and
because capable, adopted options do exist but aren't fully open, it also carries an **openness**
gap. Contrast a category with one strong, widely-used open-source library and nothing behind it:
Stage 4, a **resiliency** gap, nothing wrong with the library itself. Contrast again with several
such libraries: Stage 5, no gaps.

## Policy parameters

The thresholds are deliberate, tunable choices rather than fixed law. They live as named
constants at the top of the gap-analysis block in `build/serialize.py`:

- the **category-leading** score threshold (the 4.5 bar, retained as the legacy `mature` bar),
- the **Strong** tier boundary,
- the count of category-leading fully-open products required for **Stage 5**,
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
