# Runbook: getting every score auditable

Executable plan for reaching the state where every score can be re-derived from evidence, and
the failure modes this project has actually hit are prevented by a mechanism rather than by
remembering.

> **Read `docs/guides/verification.md` first.** It is normative: what `last_verified` means,
> who may write one, the `establishes` invariant, and the gate table. This runbook is only
> the order of operations and the commands.

**Definition of done.** Not "every axis has a date." It is:

1. Every axis claiming a confirmation satisfies the invariant — every recorded dimension has
   an establishing source re-read on or after the claimed date. Gated.
2. Every score/class pair is producible by its category's rubric. Gated.
3. `check_rubric` reproduces 16/16 categories, and the warehouse agrees per product. Gated.
4. Every date traces to a fetch with a status and a digest. Gated.
5. The remaining gaps are enumerated in `deferred` with reasons, not silently absent.

A date on every axis is the *by-product*. Chasing coverage first is how the field got
corrupted twice already.

---

## Phase 0 — Build the gates, before any volume work

Do this first. Everything after it is bulk edits to `sources/scores/`, and gates written
afterwards would be gates written to fit whatever the bulk edits happened to produce.

> **0.1 to 0.4 have landed.** `build/check_verification.py` runs in `validate.yml`, and all
> three gates pass. Two things went differently from what is written below and are worth
> knowing before following it:
>
> - **G3 caught 17 impossible pairs, not 2.** `vellum` and `whylabs` were the known ones;
>   `tensorrt-llm` made a third `4 / open_source`, five products were `2 / open_core`, and
>   nine carried a score of 3, which the software ladder cannot emit at all. All were fixed
>   as score corrections. `docs/guides/verification.md` has the three groups and the
>   reasoning; the ladder was not touched.
> - **The G2 exemption list is empty.** All 6 dated axes qualified for it, and none of them
>   satisfied G1 either, because the 2026-07-28 pass on the model flagships re-read only the
>   dataset endpoint. Re-fetching the 23 cited sources was 23 requests and it turned up two
>   defects the exemption would have hidden. Exempting stays the cheaper move and the
>   mechanism is still there; it is not the better move when the set is small.
>
> **0.5 (G6) has NOT landed.** It is the one Phase 0 item still open.

### 0.1 Schema: `establishes`, `http_status`, `content_sha256`

Add all three to `docs/schemas/score.schema.json` under `definitions.source`, **all
optional**. `establishes` is an array whose items must be dimension names declared by some
recipe — validate that cross-file in `build/validate.py`, or a typo'd dimension name silently
establishes nothing.

```bash
uv run python -m build.validate        # 0 errors, nothing populated yet
uv run pytest -q
```

### 0.2 `build/components.py` — the only supported components editor

Extract the block-safe rewriter: locate the `  components:` block including folded
continuation lines, rebuild it, re-parse the file, and assert both the new value and that
every other field is byte-identical. Port the callers.

Test it against a file whose `components` folds across three lines. A single-line regex
passes such a test only by accident, which is why the test matters more than the helper.

### 0.3 The three free gates

Put all three in `build/check_verification.py`, one command, wired into `validate.yml` next
to the existing test step.

- **G1, the invariant.** For each axis carrying `last_verified: D`: every dimension the score
  records has ≥1 source with `establishes` naming it and `accessed >= D`. Scope: axes with a
  date only.
- **G2, digest present.** Same scope: every establishing source has `http_status` and
  `content_sha256`. Exempt dates predating this runbook by listing them explicitly, so the
  exemption is visible and shrinks.
- **G3, producible pair.** For every scored product in a category with a recipe, `(score,
  class)` must equal the outcome of some rule in that recipe. Full scope, immediately.

```bash
uv run python -m build.check_verification          # expect G3 to FAIL first run
```

G3 will fail on `vellum` and `whylabs` (`4 / open_source`) and possibly others. **Fix those
scores before landing the gate**; each is a real error, and one of the two recorded values is
wrong in each case. Resolve by reading the product, not by adjusting the rubric to admit the
pair.

### 0.4 The nonce-forcing query helper

One place that builds warehouse queries and appends `-- cache-bust <uuid4>`. Warehouse
results cache on query text, so a fixed verification query returns its first answer forever;
this has already caused a tool to report success against pre-materialization data. Port
`apply_scores.fetch_computed` and any verification script onto it.

### 0.5 G6 — the release assertion

`build/publish_registry.py` (or the runbook step around it) asserts, for every UDM it depends
on, that `latestRevision.revisionNumber == latestRelease.revision.revisionNumber`.

A run materializes the latest **released** revision. Creating a revision changes nothing
until `createDataModelRelease` points at it, and the symptom is "my change had no effect"
rather than an error — three runs were spent on that, concluding a column drop had broken
materialization when the new SQL had never executed. See `docs/runbooks/deploy-udms.md`.

**Exit criteria for Phase 0:** `check_verification` passes, `validate.yml` runs it, the
components helper has the folded-scalar test, and G3's catches are fixed as score
corrections.

---

## Phase 1 — Finish the recipes: 16/16 categories, 470/470 products

111 products, four categories. Do this before Phase 2 or the SQL generalization gets done
twice.

| category | n | type | notes |
|---|---|---|---|
| `benchmark_eval_data` | 27 | dataset | one new ladder covers both dataset categories |
| `training_synthetic_datasets` | 38 | dataset | |
| `edge_hardware` | 20 | hardware | own ladder; version-in-identity applies |
| `safeguards` | 26 | **mixed** 9 model + 17 software | do last, changes the machinery |

Method per category, the one proven on `deployment` and the nine software categories:

```bash
# 1. Survey what is actually recorded before designing anything.
#    Software components turned out to be prose with 213 distinct keys; the model
#    categories were structured. Do not assume which you have.
uv run python -m build.check_rubric --category <slug>

# 2. Derive each dimension from the recorded prose WITHOUT looking at the score, apply
#    the ladder, compare. Agreement is corroboration; normalize only those.
# 3. Hold the rest in `deferred` with a real reason (>40 chars; a test enforces it).
# 4. Verify.
uv run python -m build.check_rubric && uv run python -m build.validate && uv run pytest -q
```

Two rules learned the hard way:

- **Never trust a regex classification.** A first pass got 3 of deployment's 27 wrong:
  `sandbox-runtime` says "no managed/**proprietary** tier", `openpcc` calls its commercial
  service "**separate**", `webcontainers` publishes a repo but no runtime source. Most
  gated-sounding words in this corpus sit inside negations. Use the regex to triage, read to
  decide.
- **Use `build/components.py`.** See 0.2.

`safeguards` is the interesting one: being the only mixed-type category, `extends` must become
per-product-type rather than per-category. That forces extracting the model ladder to
`sources/rubrics/model.yaml`, which finishes the de-duplication that
`sources/rubrics/software.yaml` started.

**Exit criteria:** `check_rubric` reports 16/16 `[OK]`, every deferral carries a reason, no
category's stage or gaps moved (diff the serialized output before and after).

---

## Phase 2 — Generalize the scoring SQL, once ✅ done 2026-08-05

Landed as two models. `docs/guides/verification.md` step 2 carries the full account; this is
the operational half.

`currentai.scores.openness_computed` resolved `weights`, `data`, `code` and `license` by name,
so 13 of 16 categories produced no rows. It now reads
`currentai.registry.category_dimensions`, the ladder's own declaration. **470 rows, 384
scored, zero divergence from `check_rubric`.**

What shipped:

1. **Dimension-generic resolution**, in a new `currentai.scores.openness_facts` — one row per
   (product, category, declared dimension), which is also the audit chain's dimension link.
   The split was forced: one query hit 174 Trino stages against a ceiling of 150.
2. **`dims_recorded` and `all_recorded_dims_from_dataset`**, the denominator Phase 3 needs.
3. **`category_deferrals`**, plus `category_dimensions`. Deferred products keep a row, carry
   the recorded reason, and are never walked through the rules.

### The refresh order, which is not optional

Nothing here carries a cron, so a publish is only the first half of a refresh. Getting this
wrong looks exactly like a code bug: the first run of the generalized SQL reported three
categories missing entirely, and the cause was `product_evidence` sitting three recipes stale
— from before the slug collapse in #121, so it still held 47 orchestration products against
the repo's 36.

```bash
# 1. push the declarations, and wait for the static models to materialize
uv run python -m build.serialize_rubric && uv run python -m build.publish_registry

# 2. refresh the user models IN ORDER, waiting for each: they do not cascade
#    evidence.product_evidence -> scores.openness_facts -> scores.openness_computed

# 3. revision -> RELEASE -> run, for a model whose SQL changed. The middle step is the
#    one that gets forgotten, and a run without it executes the previous release.
uv run python tools/deploy_udm.py --dataset scores --model openness_facts \
    --sql udms/scores_openness_facts.sql

# 4. prove it
uv run python -m build.check_parity
```

### G5 — the parity gate

`build/check_parity.py` compares `check_rubric`'s local verdict against
`currentai.scores.openness_computed` for every product, and fails on any divergence. It runs
daily in `.github/workflows/parity.yml`.

This is the mechanism for the failure mode that bit four times in one day — `check_rubric` and
the SQL mirror each other's logic by hand and drift silently. Every one of those four was
caught by per-product comparison and none by a local check, and the gate's first run caught a
fifth: `license:none` resolving to a tier through check_rubric's definitional fallback and to
nothing at all through the warehouse's lookup table.

It is not in `registry.yml`, on purpose. Chained onto a publish it would compare fresh rules
against the un-recomputed warehouse of step 2 above and fail for a reason that is not a drift.
Move it there when those three models carry crons.

**Exit criteria:** all 16 categories score in the warehouse, `check_parity` passes, and the
deferral count in `category_deferrals` matches the repo's.

---

## Phase 3 — The automated pass, ~400 axes

Adoption and capability only, and only where every recorded dimension is signal-derived
(needs Phase 2's column). The date is the signal fetch date; the establishing source is the
signal's URL, with the digest captured at fetch time.

No reading and no judgment, which is why it can run unattended — and exactly why it must be
fenced to those axes. Openness is excluded permanently: `data` is research-only in
`signal_routing.yaml`, the GitHub code route is `settles_dimension: false`, and software
`core_gated` needs a pricing page.

```bash
uv run python -m build.check_verification    # G1/G2 now cover ~400 more axes
uv run python -m build.check_freshness       # coverage should jump
```

**Exit criteria:** every axis it touched satisfies G1 and G2, and `check_freshness` reports
them as `verified` rather than `commit`.

---

## Phase 4 — The re-read pass, ~1099 URLs

Everything else, all of openness included. **Fold the 174 held-back products in rather than clearing
them first** — reading a product's sources to settle `core-gated` *is* the re-check that earns
its date. Two passes means the same pages fetched twice, on scores about to change.

Per axis, the unit of work:

1. Fetch each cited URL; record `http_status`, `content_sha256`, and a `shows` extract that
   actually appears in the body.
2. Re-derive each recorded dimension and attribute it: `establishes: [...]`.
3. If a value moved, that is the valuable output — fix the score and say why in `note`.
4. Stamp `last_verified` only once every recorded dimension has an establishing source.

Batch by category so `check_rubric` gives a clean signal per batch, and run
`check_verification` after each batch rather than at the end.

**On agent execution.** This is 1099 fetches and it is the step most exposed to
rubber-stamping — an agent that "confirms" without reading would reproduce #108's failure at
fifty times the scale while looking legitimate. Three things make that not work: G1 requires
the `accessed` bump on every dimension, G2 requires a digest that only fetching produces, and
G4 re-fetches a sample and compares. Do not relax any of the three to make a batch finish.

**Expect scores to move.** The RWKV correction in #105 came out of a pass like this. Movement
is the return on the work, not a problem with it — `apply_scores --check` exits non-zero on a
moved score deliberately.

**Exit criteria:** every one of the 1386 real claims either carries a confirmed
`last_verified` or sits in `deferred` with a reason. Zero silently absent.

---

## Phase 5 — Close the ratchet

```bash
uv run python -m build.check_freshness --max-age-days 90     # tune, then gate
```

Add G4 (sampled re-fetch) as a weekly scheduled workflow, reporting drift rather than hard
failing, since pages legitimately change. Turn `--max-age-days` into a CI gate once coverage
makes it fail on genuine staleness rather than on backlog. Drop the G2 exemption list.

**Exit criteria:** the five definition-of-done conditions hold, and each is enforced by
something that runs without being remembered.

---

## Standing hazards

Every one of these has happened. They are not hypotheticals.

| hazard | tell | guard |
|---|---|---|
| Derived date sold as a confirmation | any aggregate of `accessed` reaching `last_verified` | `tests/test_apply_scores.py`; G1 validates, never derives |
| Stale warehouse read | identical query text returning a pre-materialization answer | the nonce helper (0.4) |
| Unreleased revision | "my SQL change had no effect", no error | G6 (0.5) |
| Repo/warehouse drift | local reproduces, warehouse abstains | G5 (Phase 2) |
| Folded-scalar corruption | a components value with a key spliced mid-string | `build/components.py` (0.2) |
| Partial coverage overstating openness | most-restrictive over a subset of SKUs | already in the SQL: `skus_mapped = skus_reachable AND tiers_seen <= 1` |
| Bot-owned files in a PR | `generated-files-guard` fails | edit `sources/` only; the bot regenerates on merge |
| British spelling | `licence`, `penalised`, `labelled` | American English everywhere, including identifiers |

## Related

- `docs/guides/verification.md` — normative: the invariant, the gates, who may write a date
- `docs/guides/freshness.md` — normative: what `last_verified` means
- `docs/runbooks/deploy-udms.md` — revision → release → run
- `AGENTS.md` — the layer-2 loop and the evidence grading rule
