# Deploy the scoring-trace tables

Maintainer runbook (OSO write access). Publishes the three repository-owned scoring-trace tables
— `currentai.evaluation.axis_facts`, `evaluation.axis_rule_matches`, and `evaluation.axis_results`
(`build/axis_scoring_trace.py`). An editor session does not run this: it builds and tests the
candidates in-repo; only a maintainer materializes them.

The three tables are the ADR-001 repository-owned evaluator's published trace of the openness
ladder. They key on `declaration_version_id` and carry **no** `release_id` and **no**
`observation_snapshot_id` (§4.4): a deterministic evaluation of the declarations does not depend on
any measurement. Like `registry.axis_assessments` and the Phase-3 evaluation tables, they are **not**
UDMs — a platform SQL model cannot compute `declaration_version_id`, which encodes the repository
git SHA and the `sources/` content digest the warehouse has no access to. They are cut by the
builder, at a commit, from the working tree.

## 1. Preconditions

- The commit you are publishing from is on `main` and the worktree is clean. The builder derives
  `declaration_version_id` from `HEAD` + the working tree and refuses a dirty tree (a dirty tree
  yields an id no commit reproduces); pass `--allow-dirty` only for a throwaway diagnostic.
- `OSO_API_KEY` and `OSO_ORG_ID` are set. `OSO_DATASET` defaults to `evaluation` — these tables
  live in the same dataset as the Phase-3 adoption evaluation tables, which already created it.

## 2. Build the candidate CSVs

Validate first (builds in memory, writes nothing, fails on a dirty tree or a recipe error):

```bash
uv run python -m build.axis_scoring_trace --check
```

Then write the upload artifacts:

```bash
uv run python -m build.axis_scoring_trace --out build/evaluation
```

This reads the recorded `sources/scores/`, the resolved rubrics, and the published roster
(`build_payload`), replays the openness ladder once per product, and writes
`build/evaluation/axis_facts.csv`, `axis_rule_matches.csv`, and `axis_results.csv`. That directory
is git-ignored — the CSVs are upload artifacts, not repository state. Sanity-check the reported
summary against the goldens in `tests/test_axis_scoring_trace.py` (over the current corpus: 522
results — 517 scored and all reproducing the recorded score, 5 deferred — 2284 facts, 2734 rule
matches). Every scored `axis_results` row must have `reproduces_recorded = true`; a `false` there
means the evaluator disagrees with a recorded score, which is a `check_rubric` failure to resolve
before publishing, never something to deploy around.

## 3. Publish

The three tables are static models in the `evaluation` dataset. They use the same publish mechanics
as the Phase-3 evaluation tables (`resolve_dataset` → `resolve_static_models` → upload URL → `PUT`
the CSV → `createStaticModelRunRequest`, requested **one model at a time and awaited in turn** so
two runs never race to create the dataset's Trino schema, then wait for each run to reach terminal
`SUCCESS` and read the deployed row count/schema back via `pyoso` before trusting it). They are
**not** wired into any automatic table set, precisely because they are cut at a commit rather than
on every merge; a maintainer publishes them explicitly. Wiring a dedicated publisher (mirroring
`build/publish_evaluation.py`, with the same validate-before-mutation and SUCCESS-gated archive) is
the natural follow-up once this deploy becomes routine.

Record the `dataset_id`, each static-model id, and the `declaration_version_id` you published from
in the deploy note.

## 4. Reconcile the inventory with reality

Once the tables exist on the platform:

- In `warehouse/assets.yaml`, move each of `evaluation.axis_facts`, `evaluation.axis_results`, and
  `evaluation.axis_rule_matches` from `status: staged` / `materialized: false` to `active` /
  `materialized: true`, record the `dataset_id`, and update `verified_at`.
- Regenerate the derived DAG and counts with `build/assets.py` (the `staged_assets` count marker
  moves), and update `docs/architecture/current-state-dag.md` and the counts in
  `docs/architecture/data-architecture.md`.
- Update the Phase-6 row in `docs/architecture/migration-status.md`.

## The `evaluator_version` cutover is a SEPARATE, gated step — do not fold it into this deploy

Landing this evaluator is what eventually replaces the declared sentinel
`v0-no-repo-evaluator` in `build/declaration_version.EVALUATOR_VERSION` with a real evaluator
version. **This deploy does not do that**, and neither did the work that built these tables.

The reason is impact, not caution. `evaluator_version` is folded into every
`declaration_version_id`, so replacing the sentinel re-keys **every** `declaration_version_id`
corpus-wide — including tables that were deployed against the sentinel and key on it:

- `evaluation.product_adoption_measurements` and `evaluation.adoption_reconciliation` (Phase 3,
  deployed 2026-08-25), and
- `registry.axis_assessments` (staged), and
- these three scoring-trace tables themselves.

Every row of all of them carries a `declaration_version_id` computed with the sentinel today. The
day the sentinel is replaced, all of those ids change together, and any published trace or
reconciliation cut before the flip no longer shares an id with one cut after it. So the flip is its
own reviewed change: bump `EVALUATOR_VERSION`, regenerate and republish every declaration-keyed
table in one coordinated pass, and record the id transition. Do it deliberately, not as a
side effect of shipping the trace.

## Note on the current state

Nothing consumes these tables yet — they are the queryable trace the Phase-7 retirement of the
duplicate warehouse openness chain (`scores.openness_facts`, `scores.openness_computed`) will lean
on, once dual-running shows complete agreement over multiple releases (ADR-001). Publishing them
wires the shape into the platform ahead of that retirement; it changes no existing consumer, so
there is no gate to enable and no rollback consumer to break.
