# Verification Guide

How a score earns a `last_verified` date, and the plan for getting one onto every axis.

> Companion to `docs/guides/freshness.md`, which defines what `last_verified` *means*.
> This guide covers who may write one and how. Both are normative. When either changes,
> change the guide first and make the code follow.

## How an axis earns its date

**An axis earns `last_verified` when someone re-read its cited sources and re-derived its
value.** Not when a tool aggregated dates. Not when a value was copied forward.

Three consequences, and no other reading is intended:

1. **A re-check must be evidence-producing.** It records what was read and what that
   source showed, the way `sources[].shows` already does. A date that cannot be traced to
   a fresh observation is indistinguishable from a rubber stamp, and we have twice shipped
   the rubber stamp by accident (#108, #115).
2. **An agent re-reading a cited URL is a confirmation. The pipeline reading recorded
   values is not.** This is the distinction the whole plan below rests on, so it is worth
   stating precisely. When an agent fetches `https://…/model-card` and re-derives that the
   license is Apache-2.0, something outside the repo was consulted and the conclusion was
   re-established. When `apply_scores` reads `license:Apache-2.0` out of
   `sources/scores/foo.yaml`, computes on it, and writes a date back, the repo has been
   read to itself and nothing was confirmed.

   Who performed the re-check is not the test — re-derivability is. The first pass of
   `sources/scores/` was agent-authored, so authorship never established trust here and
   does not now. See the grading rule in `AGENTS.md`.
3. **A re-check that changes nothing still earns the date.** Confirming a value is
   unchanged is the normal outcome and the main point. Only recording the ones that moved
   would make the field a change log rather than a freshness measure.

### What may never write it

No tool that computes over already-recorded values. `build/apply_scores.py` writes
`openness.score` and `openness.class` and deliberately writes no date at all; the reasoning
is in its module docstring and in the divergence history in `freshness.md`.

## The audit chain, and where it currently breaks

For a score to be auditable, a reader must be able to walk it back to something outside the
repo:

```
score  <-  the rule that fired      (category scoring_recipe)
       <-  the dimension values     (openness.components)
       <-  the evidence             (openness.sources[].shows)
       <-  a source                 (openness.sources[].url)
```

Three of those four links hold today. **The third does not.** `sources` is a flat list per
axis, so nothing records WHICH source establishes WHICH dimension. Measured on 2026-07-30:
324 of 470 openness axes cite exactly one source, asserted to establish `weights`, `data`,
`code` and `license` together. A reader cannot check that, and neither can a tool.

That is the gap that makes a re-check unfalsifiable, and closing it is what makes everything
below possible.

### `establishes`: per-dimension attribution

A source item gains an optional list naming the dimensions it settles:

```yaml
sources:
- url: https://huggingface.co/org/model
  shows: Apache-2.0 in the model card; safetensors weights downloadable
  accessed: '2026-07-30'
  establishes: [license, weights]
- url: https://github.com/org/model
  shows: pretraining configs and data-prep scripts in the repo
  accessed: '2026-07-30'
  establishes: [code, data]
```

Optional and forward-populated, so existing data is not retroactively invalid. The re-check
tooling writes it; the gates below apply only to axes that claim a confirmation.

### The invariant that makes a rubber stamp fail

> **`last_verified: D` is valid only if, for every dimension the score records, at least one
> source that `establishes` that dimension has `accessed >= D`.**

This is the mechanism, not a convention. Claiming a confirmation you did not perform now
requires also back-dating the `accessed` field of every dimension's source — and those are
what the content check below verifies.

**This validates a claimed date. It never derives one.** The distinction is the whole point
and it is easy to erode: someone will eventually notice that the invariant mentions
`accessed` and "simplify" it into `last_verified = max(accessed)`, which is #115 exactly.
Deriving the date asserts a confirmation nobody made; validating it rejects a confirmation
nobody could have made. `freshness.md` forbids the first and requires the second.

Note the aggregation direction, which is also load-bearing: the check is over EVERY recorded
dimension, so the binding constraint is the *least* recently re-read one. `max(accessed)`
across an axis would pass an axis where one dimension was re-read today and three were last
seen in June.

### Catching fabrication rather than just inconsistency

The invariant catches unsupported dates. It cannot catch a source that never said what
`shows` claims, or a URL that never existed. For that, the re-check tool records what it
actually fetched:

```yaml
- url: https://…
  accessed: '2026-07-30'
  http_status: 200
  content_sha256: 3f9a…          # of the fetched body at accessed time
```

A digest makes two later audits possible: a URL that 404s at re-check time was either never
real or has rotted, and a changed digest tells you the page moved under a claim that still
cites it. Neither is a hard failure on its own — pages legitimately change — but both are
reasons to re-check, and a *missing* digest on a newly claimed confirmation is a hard
failure, because it means the tool did not fetch anything.

## The gates, and why they ratchet

Every failure mode this project has actually hit gets a mechanism, not a note. Cheap ones
gate every PR; ones needing the network run periodically.

| # | failure mode | mechanism | cost |
|---|---|---|---|
| G1 | a confirmation with no supporting evidence | the invariant above | free |
| G2 | a claimed date with no fetch digest | required on axes claiming a confirmation | free |
| G3 | an impossible score/class pair | the pair must be producible by some rule in the recipe | free |
| G4 | fabricated or rotted sources | sampled re-fetch, digest and `shows` token match | network, weekly |
| G5 | repo and warehouse drifting apart | `build/check_parity.py`, a per-product differential | network, daily |
| G6 | a UDM revision that was never released | assert latest revision == latest release | network, per publish |

**They ratchet rather than switch on.** G1 and G2 apply only to axes that carry a
`last_verified`, which is 6 today and grows as the re-read pass proceeds. So the gate covers
exactly what has been done, never blocks progress, and never permits a regression on ground
already taken. A big-bang gate over all 1386 axes would fail on day one and get switched
off, which is how gates die.

G3, G5 and G6 apply in full immediately — nothing has to be populated first.

G5 runs on its own weekly schedule rather than inside the publish job, and that placement is
deliberate rather than a stopgap in disguise. Publishing pushes and materializes the static
models; the three user models that read them recompute on Monday at 03:00, 04:00 and 05:00 UTC,
upstream first, and G5 grades the result at 06:00. Chained onto a publish instead, the gate would
compare fresh rules against a warehouse that has not recomputed and fail for a reason that is
not a drift.

**The gate's schedule has to match the chain's.** A daily gate over a weekly chain fails every
day between a merge and the following Monday, always saying "the warehouse has not caught up",
which is not what a parity gate is for and is how a gate earns its way into being ignored. If
you want a check sooner, refresh the three models and run `check_parity` by hand.

The crons bound how stale the warehouse gets; they do not make a publish arrive any faster, so a
Tuesday merge is scored the following Monday. Move G5 into `registry.yml` on the day
`publish_registry` triggers those three runs and waits for them.

G3 found 17 impossible pairs on its first run, not the two that were known. `vellum`,
`whylabs` and `tensorrt-llm` were recorded `4 / open_source`, a pair no rule emits because
4 is `open_core`; five more were `2 / open_core`, which no rule emits either; and nine
carried a score of 3, which the software ladder cannot produce **at all**, its rungs being
1, 2, 4 and 5. All 17 were corrected by reading the products, in three groups:

- `2 / open_core` → `2 / source_available`. The class was wrong. `open_core` in this ladder
  means an OSI core with functionality withheld for a paid tier; these five have an open
  periphery around a closed engine, which is `source: partial`.
- score 3 → 2. The score was wrong. Every one of the nine is "you can read it and not run
  it freely" — a non-OSI restrictive license over public source, or a client standing in
  for a closed service — which the ladder scores at 2.
- `4 / open_source` → `5 / open_source`. The score was wrong. Each of the three publishes
  the whole self-hostable product under an OSI license with nothing withheld. The 4s
  encoded maturity or scepticism about the vendor's marketing, both of which belong on the
  adoption and capability axes and were already recorded there.

Worth noting what G3 caught that `check_rubric` could not: 16 of the 17 were sitting in a
category's `deferred` block, which excludes a product from reproduction. G3 ignores the
evidence and asks only whether the pair exists in the ladder, so deferring cannot hide it.

### Two shared utilities, so the mechanism cannot be bypassed

- **`build/components.py`** — the only supported way to edit a `components` field. The
  block-safe rewriter with the reparse assertion. 277 of the 470 score files fold that
  scalar across lines, 57 of them across three or more, so any hand-rolled
  `^  components: (.*)$` substitution splices keys mid-string and corrupts the value
  silently. A shared helper means the next script cannot re-invent that. Generic over the
  field, so a score correction and a components edit are the same operation with the same
  assertion behind them.
- **`build/warehouse.py`** — the only supported way to read the warehouse, and it forces a
  cache-busting nonce. Results cache on query TEXT, so a fixed verification query returns
  its first answer forever and a tool reading through that cache reports success against
  stale data. It has already happened. `query()` has no parameter to switch the nonce off.

## Why openness can never be fully automated

By design, not for want of coverage. `all_recorded_dims_from_dataset` in
`currentai.scores.openness_computed` is the column that says so per axis, and it is false
almost everywhere. Of the recorded openness dimensions only `license` and `weights` have a
dataset route. `signal_routing.yaml` declares `data` research-only, and the
GitHub code route carries `settles_dimension: false` because a live repo establishes neither
a full training pipeline nor an ungated core. For software categories, `core_gated` needs a
pricing page read.

So every openness axis needs at least one read, permanently. Adoption and capability are
different in kind and can be automated — see the table below.

## Current state, 2026-07-30

| | count |
|---|---|
| axes total (470 products × 3) | 1410 |
| deliberately null — capability on datasets and a wire protocol, not claims | 24 |
| **real claims to verify** | **1386** |
| of those, citing at least one source URL | 1386 |
| carrying a real `last_verified` | 6 (once #124 lands; 26 before it, 19 of them tool-written) |
| of those 6, satisfying G1 and G2 | 6, after the Phase 0 re-read |
| distinct source URLs behind all of it | 1099 (450 cited more than once) |

Every real claim already cites a source. The work is not finding evidence; it is re-reading
what is cited. And the re-read surface is 1099 fetches, not 1386, because sources are shared.

**None of the 6 satisfied G1 as first written**, which is worth recording because it is the
clearest evidence that the invariant does something. `establishes` did not exist when those
dates were set, and beyond that the 2026-07-28 pass on the four model flagships re-read only
the dataset endpoint: `apertus`, `olmo`, `pythia` and `lucie-7b` all claimed a whole-axis
confirmation while citing 2026-06 reads for weights, code, checkpoints and license. Refetching
the 23 cited sources cleared it and turned up two things an exemption would have hidden — a
Lucie source URL that had never resolved as cited (missing the `/datasets/` segment, so the
Hub answered 401), and an `rwkv` `weights:open` claim with no source behind it at all.

### What automation can and cannot earn, per axis

| axis | axes | all sources signal-backed | can a fetch earn the date? |
|---|---|---|---|
| adoption | 470 | 204 (+68 partial) | **Yes** — the score IS a banded signal, so re-fetching re-derives it |
| capability | 446 | 198 (+55 partial) | **Yes where a benchmark row exists**; feature and internal-eval judgments need a read |
| openness | 470 | 272 (+86 partial) | **Never fully** — see above |

"Signal-backed" means every source the axis cites is on a host a fetcher already re-derives
automatically: the HF hub, GitHub, PyPI, LMArena, Artificial Analysis, OpenRouter.

## The plan, in order

The order matters more than usual here, because two of the steps get cheaper by waiting and
one gets done twice if rushed.

### 1. Finish the recipes — 16/16 categories ✅ **done 2026-08-01**

All sixteen categories carry a `scoring_recipe`. The last three landed as PRs #131, #135 and
#137, and `safeguards` was corrected from 0/26 to 21/26 in #138 and #139.

Four shared ladders now exist — `software` (ten categories), `model` (two), `dataset` (two)
and `hardware` (one) — plus `base_pretrained`'s own. `build/check_recipe.py` gates the
structure of every one of them on every PR, and `skills/build-rubric/SKILL.md` is the
procedure for the next one.

Two things this step turned out to depend on, neither of which the plan anticipated:

- **A category can only be laddered if its `components` VALUES are controlled tokens.**
  `check_rubric` matches `head(value)` against a declared enum, so a category recording
  sentences cannot be read at all. `edge_hardware` had the tidiest key coverage of the three
  and 71% prose values, which is why it went last and needed a normalization pass first. Key
  coverage is not readiness; measuring the prose share is now step 0 of the guide.
- **"One dataset ladder covers both dataset categories" was optimistic.** Applied unchanged to
  `benchmark_eval_data` the ladder reproduced 0 of 27, because that category spells the card
  key `datasheet` and because a benchmark may not be published at all — an internal eval suite
  or a held-out test set — which `gate` had no rung for. The shared ladder widened rather than
  forking, and `training_synthetic_datasets` came through identical.

**This had to precede step 2**, and still does for anyone re-reading the order: step 2
generalizes the scoring SQL off its hardcoded model dimensions, and that generalization is
driven by the complete dimension vocabulary. Doing it before `dataset` and `hardware` existed
would have meant doing it twice.

`safeguards` is no longer on this list, and it is why `extends` now accepts two forms. It
holds 9 products typed `model` and 17 typed `software`, so a single shared ladder could not
cover it. `scoring_recipe.extends` can now be a mapping of product type to ladder name —
`safeguards` declares `model: model, software: software` — resolved per product by the
`type:` field in `sources/products/<slug>.yaml`, through `build/rubrics.py`'s
`resolve_recipe_variants` and `recipe_for`. That forced the other half of the extraction
too: the fine-tuned model ladder moved out of `finetuned_chat.yaml` into a shared
`sources/rubrics/model.yaml`, so `safeguards` could reference it alongside `software.yaml`.

The machinery landed; the scores did not. `safeguards` reproduces none of its 26 products.
All 26 sit in the category's `deferred` block: a license resolving to the wrong tier,
evidence recorded under a key the ladder does not read, a couple of judgment calls on which
SKU governs a bundled guard model. Correcting those 26 is what remains, through curation
rather than more machinery.

### 2. Generalize the scoring SQL, once ✅ **done 2026-08-05**

`currentai.scores.openness_computed` resolved `weights`, `data`, `code` and `license` by name
in hardcoded UNION branches, so 13 of the 16 categories produced no rows at all: their rules
test `source`, `core_gated`, `availability`, `answers`, `documentation`, `schematics` and
`toolchain`, nothing built those facts, and with no `otherwise` rung in those ladders every
product fell out of the join. 74 rows of a possible 470.

It now reads the dimensions each ladder DECLARES, from a new
`currentai.registry.category_dimensions`, so a seventeenth category scores in the warehouse
the day its recipe lands. **470 rows, 384 scored, and `check_parity` reports zero divergence
from `check_rubric` on every one of them.**

What it took, beyond the generic resolution:

- **A split into two models.** Generalizing took the query to 174 Trino stages against a
  ceiling of 150, because the resolution CTEs are read several times each by the rule walk
  and Trino replans the subtree per reference. `currentai.scores.openness_facts` now holds one
  row per (product, category, declared dimension) and `openness_computed` walks the rules over
  it. That is also the audit chain's third link, which this guide describes and which had no
  table: "which fact did this score rest on, at what grade" is now a select.
- **The rule join carries the product type.** `rule_index` is unique only within
  `(category_slug, product_type)`, so `safeguards` — guardrail models on one ladder, guardrail
  software on another — was the category where joining on the slug alone interleaves two
  ladders' numbering.
- **The tier-free allowance.** The unmapped-license guard now fires only for ladders that ask
  about a license. `sources/rubrics/hardware.yaml` declares no `license_tier` and none of the
  20 edge products records one, so applied unconditionally the guard nulls all 20.
- **`dims_recorded` and `all_recorded_dims_from_dataset`.** `dims_relied_on` counts only what
  the winning rule reads, which is the wrong denominator — this guide requires every dimension
  the score *records*. The new columns are the precondition for step 3, and for openness the
  boolean is false almost everywhere, which is the honest answer rather than a gap.
- **A `category_deferrals` table.** `deferred` lived only in the repo, so the warehouse did
  not know which products a category had held back. Deferred products now carry a row with a
  null score and the recorded reason, and the rule walk is skipped for them.

  This was a correctness fix, not observability. `sources/rubrics/model.yaml` ends in
  `otherwise: {score: 3, class: open_weights}`, so a deferred product on the model ladder was
  scored rather than dropped: `safeguards` published a computed openness for nine guardrail
  models the repo had explicitly declined to stand behind, and seven of the nine disagreed
  with the published value.

Three things this step turned up that the plan did not anticipate:

- **The evidence model was three recipes stale.** `currentai.evidence.product_evidence` last
  materialized before the dataset, hardware and safeguards recipes landed — and before the
  slug collapse in #121, so it still held 47 orchestration products where the repo has 36.
  None of these models carries a cron, so "the repo is ahead of the warehouse" had a second
  cause underneath the SQL. Crons are step 5 of the plan in `layer2-status`; until then a
  publish is only half a refresh.
- **The roster cannot come from the evidence store.** It was
  `SELECT DISTINCT product_slug, category_slug FROM product_evidence`, which quietly made
  coverage conditional on evidence existing: `serialize_rubric` emits no document rows for a
  deferred product, so 36 of the 86 deferrals — the ones with no Hub or GitHub artifact to
  generate a dataset row either — were absent rather than unscored. It is now
  `product_categories`, which is what a category claims.
- **`license:none` resolved two ways.** `check_rubric` maps `none`, `closed` and `proprietary`
  to a tier NAMED `proprietary` whether or not the ladder declares one; the warehouse joins a
  real lookup table and found no row, so three internal-eval benchmarks scored locally and
  came back null. The dataset ladder's `unstated` tier already means exactly this, so the
  three tokens are now declared there rather than left to a fallback. Precisely the shape of
  drift `check_parity` exists to catch, and it was caught by the first run of it.

### 3. The automated freshness pass — roughly 400 axes

Adoption and capability, restricted to axes where every recorded dimension is signal-derived.
The date is the signal fetch date. No reading and no judgment, which is exactly why it can
run unattended and why it must be fenced to those axes only.

### 4. The re-read pass — roughly 1099 URLs

Everything else, all of openness included. **Fold the deferral backlog into this pass rather
than clearing it first.** Reading a product's sources to determine `core-gated` *is* the
re-check that earns its `last_verified`; done as two passes it is the same pages fetched
twice, and it re-verifies scores that are about to change.

That backlog is currently the 86 declared deferrals. Every category has a recipe now, and
`safeguards` — which used to contribute all 26 of its products here — is down to 5. The
composition is roughly: products whose prose does not settle a dimension the ladder reads,
products whose recorded license maps to no tier, and a handful where the ladder and the
recorded score genuinely disagree (`jina-reader`, `openhands`, `maple-ai`, `privatemode`, all
producible pairs, so G3 passes them and only `check_rubric` objects).

Regenerate the number rather than trusting it — `check_recipe` prints per-category counts, and
the figure has moved several times in a week.

**Expect scores to move.** Verification is not a formality: the RWKV correction in #105 came
out of a pass like this, and G3's first run moved 17 openness scores or classes before the
gate could land at all. `apply_scores --check` exits non-zero on a moved score for this
reason.

### 5. Turn on the age gate

`build/check_freshness.py --max-age-days` becomes a CI gate. This is the entire point of
having the field: a category whose oldest axis is 50 days old is a category to go and look
at. Gating earlier would only fail on the pre-automation backlog rather than on genuine
staleness.

## Related

- `docs/runbooks/verification-pass.md` — the executable plan: gate order, commands, exit
  criteria per phase, and the standing-hazards table
- `docs/guides/freshness.md` — what `last_verified` means, and the two divergences already
  closed
- `docs/guides/openness-spectrum.md` — the openness ladders themselves
- `sources/rubrics/` — shared ladders; `build/rubrics.py` for how `extends` resolves (#126)
- `AGENTS.md` — the layer-2 loop and the evidence grading rule
