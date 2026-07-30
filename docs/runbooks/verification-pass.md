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

## Phase 2 — Generalize the scoring SQL, once

`currentai.scores.openness_computed` resolves `weights`, `data`, `code` and `license` by name
in hardcoded UNION branches, so the ten software categories do not score in the warehouse at
all today. It must read the dimensions each recipe DECLARES, as `build/check_rubric.py` now
does.

Three things ship together:

1. **Dimension-generic resolution**, driven by `category_scoring_rules.condition_key`.
2. **A per-axis "every RECORDED dimension is dataset-grade" column.** `dims_relied_on` counts
   only what the winning rule reads, which is the wrong denominator — the rule requires every
   dimension the score *records*. Without this, Phase 3 cannot legitimately write a date.
3. **A `category_deferrals` table.** `deferred` lives only in the repo, so the warehouse does
   not know which ~180 products are held back. With no `otherwise` rule in the software
   ladder they currently fall out of an INNER JOIN — safe, but silent.

Deploy per `docs/runbooks/deploy-udms.md`, and note the release step:

```bash
# revision -> RELEASE -> run. The middle step is the one that gets forgotten.
uv run python -m build.serialize_rubric && uv run python -m build.publish_registry
# then create the revision, create the release, then trigger the run
```

### G5 — the parity gate

Add `build/check_parity.py`: for every scored product, compare `check_rubric`'s local result
against `currentai.scores.openness_computed` and fail on any divergence. Run it in
`registry.yml` after the publish step.

This is the mechanism for the failure mode that bit four times in one day — `check_rubric`
and the SQL mirror each other's logic by hand and drift silently. Every one of those four was
caught by per-product comparison and none by a local check. Automate the thing that worked.

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

Everything else, all of openness included. **Fold the ~180 deferrals in rather than clearing
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
