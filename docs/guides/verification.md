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
| G5 | repo and warehouse drifting apart | per-product differential after every publish | network, per publish |
| G6 | a UDM revision that was never released | assert latest revision == latest release | network, per publish |

**They ratchet rather than switch on.** G1 and G2 apply only to axes that carry a
`last_verified`, which is 6 today and grows as the re-read pass proceeds. So the gate covers
exactly what has been done, never blocks progress, and never permits a regression on ground
already taken. A big-bang gate over all 1386 axes would fail on day one and get switched
off, which is how gates die.

G3, G5 and G6 apply in full immediately — nothing has to be populated first. G3 already has
a known catch: `vellum` and `whylabs` are recorded `4 / open_source`, a pair no ladder here
can produce.

### Two shared utilities, so the mechanism cannot be bypassed

- **`build/components.py`** — the only supported way to edit a `components` field. The
  block-safe rewriter with the reparse assertion, extracted. 21 of deployment's 27 files
  fold that scalar across lines, so any hand-rolled `^  components: (.*)$` substitution
  splices keys mid-string and corrupts the value silently. A shared helper means the next
  script cannot re-invent that.
- **A query helper that forces a cache-busting nonce.** Warehouse results cache on query
  TEXT, so a fixed verification query returns its first answer forever and a tool reading
  through that cache reports success against stale data. It has already happened. The nonce
  belongs in the helper, not in each caller's discipline.

## Why openness can never be fully automated

By design, not for want of coverage. Of the recorded openness dimensions only `license` and
`weights` have a dataset route. `signal_routing.yaml` declares `data` research-only, and the
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
| distinct source URLs behind all of it | 1099 (450 cited more than once) |

Every real claim already cites a source. The work is not finding evidence; it is re-reading
what is cited. And the re-read surface is 1099 fetches, not 1386, because sources are shared.

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

### 1. Finish the recipes — 16/16 categories, 470/470 products

111 products across four categories still have no `scoring_recipe`:

| category | n | product type |
|---|---|---|
| `benchmark_eval_data` | 27 | dataset |
| `training_synthetic_datasets` | 38 | dataset |
| `edge_hardware` | 20 | hardware |
| `safeguards` | 26 | **mixed** — 9 model, 17 software |

**Do this before step 2.** Step 2 generalizes the scoring SQL off its hardcoded model
dimensions, and that generalization should be driven by the complete dimension vocabulary.
Generalize it now for software alone and it gets redone when `dataset` and `hardware` arrive
with dimensions of their own.

Two of the four are cheap: one dataset ladder covers 65 products, hardware is 20 products.
`safeguards` is the one that changes the machinery — it is the only mixed-type category, so
`extends` has to become per-product-type rather than per-category. That in turn forces the
other half of the ladder extraction: pulling the model ladder out to
`sources/rubrics/model.yaml` so `safeguards` can reference both it and `software.yaml`.

### 2. Generalize the scoring SQL, once

`currentai.scores.openness_computed` resolves `weights`, `data`, `code` and `license` by
name in hardcoded UNION branches, so the ten software categories do not score in the
warehouse at all today. It needs to read the dimensions each recipe DECLARES, exactly as
`build/check_rubric.py` now does.

Two things ride along:

- **A per-axis "every recorded dimension is dataset-grade" column.** `dims_relied_on` counts
  only what the winning rule reads, which is the wrong denominator — `freshness.md` requires
  every dimension the score *records*. Without this column no tool can ever legitimately
  write `last_verified`, so it is the precondition for step 3.
- **A `category_deferrals` table.** `deferred` currently lives only in the repo, so the
  warehouse does not know which products a category has held back. There are ~180 of them
  now. With no `otherwise` rule in the software ladder they fall out of the model's INNER
  JOIN rather than being scored wrongly — the safe direction, but silent.

### 3. The automated freshness pass — roughly 400 axes

Adoption and capability, restricted to axes where every recorded dimension is signal-derived.
The date is the signal fetch date. No reading and no judgment, which is exactly why it can
run unattended and why it must be fenced to those axes only.

### 4. The re-read pass — roughly 1099 URLs

Everything else, all of openness included. **Fold the deferral backlog into this pass rather
than clearing it first.** Reading a product's sources to determine `core-gated` *is* the
re-check that earns its `last_verified`; done as two passes it is the same pages fetched
twice, and it re-verifies scores that are about to change.

That backlog is currently ~180 products: 59 whose prose does not settle their dimensions, 11
where the ladder and the recorded score disagree, plus the model-category gaps.

**Expect scores to move.** Verification is not a formality: the RWKV correction in #105 came
out of a pass like this, and the 11 ladder conflicts already say some recorded scores are
wrong — `vellum` and `whylabs` are recorded `4 / open_source`, which is not a pair any ladder
here can produce. `apply_scores --check` exits non-zero on a moved score for this reason.

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
