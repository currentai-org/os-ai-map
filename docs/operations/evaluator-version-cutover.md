# Plan: the `evaluator_version` cutover (Phase 6 → the sentinel is retired)

**Status: PLAN FOR REVIEW. No platform mutation is authorized by this document.** It resolves the
open questions the cutover raises and proposes an exact procedure; execution is a separate,
explicitly-authorized step once this plan and its two open decisions are approved.

## What the cutover is

`build/declaration_version.py:111` pins `EVALUATOR_VERSION = "v0-no-repo-evaluator"` — a sentinel
recording "scores are curator-recorded, not machine-derived." Phase 6 landed the
repository-owned evaluator (the `evaluation.axis_*` scoring trace, deployed 2026-08-27). Retiring
the sentinel — replacing it with a real evaluator version — is what this plan covers.

`declaration_version_id = f(source_git_sha, source_content_digest, evaluator_version)`
(`build/declaration_version.py`). `evaluator_version` is folded into **every**
`declaration_version_id`, and the id is **table-independent** — it depends only on the commit, the
declaration content, and the evaluator version, not on which table carries it. So bumping
`EVALUATOR_VERSION` re-keys every declaration-keyed table at once, and **rebuilding all candidates
from one commit collapses them to a single new id** (see §3, §7).

## 1. The complete derived inventory of declaration-keyed tables

Derived from `warehouse/assets.yaml` (every asset whose `grain` names `declaration_version_id`), not
hand-listed — this is checkable and must be re-derived at execution time, not trusted from here:

| Asset | Dataset | Publisher | State today |
|---|---|---|---|
| `evaluation.product_adoption_measurements` | `evaluation` | `build/publish_evaluation.py` | active, deployed |
| `evaluation.adoption_reconciliation` | `evaluation` | `build/publish_evaluation.py` | active, deployed |
| `evaluation.axis_facts` | `evaluation` | `build/publish_scoring_trace.py` | active, deployed |
| `evaluation.axis_rule_matches` | `evaluation` | `build/publish_scoring_trace.py` | active, deployed |
| `evaluation.axis_results` | `evaluation` | `build/publish_scoring_trace.py` | active, deployed |
| `registry.axis_assessments` | `registry` | `build/publish_axis_assessments`* (runbook `deploy-axis-assessments.md`) | **staged**, not deployed |

\* `registry.axis_assessments` has no dedicated publisher yet (its runbook still describes the
mechanics); it also keys on `declaration_version_id`. It is **staged** — no live table — so it is
**not** part of the live atomic swap. Decision D3 below: deploy it in the same cutover (so the whole
declaration-keyed surface shares one id from day one) or leave it staged and let it inherit the new
evaluator whenever it first deploys. Recommended: deploy it in the same pass, for one coherent
generation.

An execution-time assertion must re-run this derivation and fail if any declaration-keyed asset is
absent from the cutover set — the cutover must cover the surface completely, or not run.

## 2. The current live generations (the real "old" IDs — not one global value)

Read live via `pyoso` on 2026-08-27:

| Table(s) | Live `declaration_version_id` | Cut at commit |
|---|---|---|
| `product_adoption_measurements`, `adoption_reconciliation` | `232015a76ecc…` | `f012d85` |
| `axis_facts`, `axis_rule_matches`, `axis_results` | `eb828b57b14d…` | `980250b` |
| `registry.axis_assessments` | — (staged, no live table) | — |

There are **two** live generations, because the eval tables and the trace tables were deployed from
different commits. Any rollback or transition map must treat these as distinct old IDs (§7, §9).

## 3. One clean cutover commit

All candidates are built from a **single `main` commit** whose only material change is the
`EVALUATOR_VERSION` bump (plus this plan and any prerequisite code fix from §0), over a **clean
worktree**. Because the id is commit- and evaluator-scoped and table-independent, one commit + one
new `evaluator_version` yields **one** new `declaration_version_id` shared by every table (given the
snapshot decision in §4 holds the observation inputs fixed). This single id is the atomicity anchor
and the cross-table invariant checked in §8.

## 4. Adoption tables: preserve the observation snapshot, do not refresh it

`product_adoption_measurements` and `adoption_reconciliation` also key on `observation_snapshot_id`
(currently `9bd4d93a6fc6`); the trace tables do not. **Recommendation: preserve** — rebuild the two
adoption candidates from the same frozen Phase-2 baseline, so the cutover changes only
`evaluator_version` (and `source_git_sha`), never the observation content. Refreshing from live
`observations.product_adoption_current` would fold a data change into the same deploy and make the
id transition impossible to attribute cleanly to the evaluator bump. **This is open decision D2** —
confirm preserve, or state the deliberate reason to refresh and record the new snapshot id.

## 5. Handling the non-atomic interval

Static models replace in place and are published sequentially, so mid-cutover some tables carry the
new id and some the old. There is no release-scoped materialization yet (`releases.*` does not
exist; atomicity is transitional per `migration-status.md`). Mitigations:

- **Low blast radius today.** Nothing consumes these tables cross-generation on the platform: the
  Phase-4 gate is disabled and the Phase-7 retirement has not begun, so no live query joins an
  old-id table to a new-id table. The window is real but currently harms no consumer.
- **One session, fail-fast.** Run the whole cutover in a single maintainer session; each publisher
  already polls each run group to terminal `SUCCESS` and exits non-zero on the first failure, so a
  partial cutover stops loudly rather than silently half-swapping.
- **Announced window.** Record the start/end and that mixed generations are expected in between.
- **Post-swap invariant check** (§8, §10): after all deploys, assert every deployed declaration-keyed
  table carries the *same* new id; a straggler means the swap did not complete.

## 6. Exact deployment order

From the cutover commit, after a full dry-run of every publisher:

1. **`registry.axis_assessments`** (only if D3 = deploy it) — registry dataset.
2. **Scoring trace** — `build/publish_scoring_trace.py` (`axis_facts`, `axis_rule_matches`,
   `axis_results`).
3. **Adoption evaluation** — `build/publish_evaluation.py` (`product_adoption_measurements`, then
   `adoption_reconciliation`, the order the publisher already uses because reconciliation reads
   measurements as candidate rows in-repo).

Order is not forced by platform reads (the tables are independent static models), so it is chosen for
legibility and so the most self-contained set (the trace) swaps first. Each publisher is serialized
and SUCCESS-gated internally.

## 7. Old → new declaration-ID transition map

The new id is not knowable until `EVALUATOR_VERSION` is chosen and the commit is made; the procedure
captures it. The transition to record in the deploy note:

| Old generation | Tables | New id |
|---|---|---|
| `232015a76ecc…` | measurements, reconciliation | `<new>` (computed at the cutover commit) |
| `eb828b57b14d…` | axis_facts, axis_rule_matches, axis_results | `<new>` |
| — (staged) | registry.axis_assessments | `<new>` (if D3 = deploy) |

Capture `SELECT DISTINCT declaration_version_id` per table **before** (done above) and **after**;
both old generations must map to the single `<new>` id, and no table may retain an old id.

## 8. Pre-flight: counts, schemas, hashes, cross-table invariants

Before any upload, build every candidate at the cutover commit and assert:

- **Row counts** match the builders: adoption 377 / 522 (from the preserved baseline); trace 2,284 /
  2,734 / 522; `registry.axis_assessments` its builder's count if D3.
- **Schemas** equal each builder's `COLUMNS` (the publishers already gate this per file).
- **Per-file authority** — `publish_scoring_trace` canonical-equivalence and `publish_evaluation`
  `validate_candidates` already prove each file is exactly its builder's output at HEAD.
- **NEW cross-cutover invariant** — every candidate across all three publishers shares **one**
  `declaration_version_id` and one `source_git_sha`. This is the check that the single-commit build
  actually produced a single generation. It does not exist yet and must be added (a small script or
  test run at execution time), because each publisher only validates its own files today.
- **Hashes** — record the sha256 of every uploaded CSV in the deploy note (the publishers already
  archive these in each receipt).

## 9. Rollback — reverse-order, by archived bytes (with a real gap to close first)

Rollback re-uploads the **previous generation's archived bytes** in reverse deploy order
(adoption → trace → registry), restoring the old ids. Each publisher archives the exact bytes it
uploaded. **Two gaps must be closed before this is dependable for the cutover:**

- **§0 archive-root bug** (below) — re-publishing from an archive via `--dir` currently nests a new
  archive and does not update the canonical archive root.
- **Archive persistence.** Archives live under `build/evaluation/…deployments/` and
  `build/registry/…`, which are **git-ignored and per-session ephemeral**. In a fresh container the
  prior archives do not exist, so rollback-by-bytes only works within the same session that deployed
  — or from archives deliberately preserved. The cutover procedure must **retain the pre-cutover
  archives** (the two current generations) and the cutover session's own archives somewhere durable,
  or download the deployed bytes before overwriting them. This must be decided and wired before
  execution; it is a genuine hole in the rollback story, not a formality.

## 10. Post-deploy verification and lockstep reconciliation

After the swap, in one reconciliation PR (mirroring the Unit-2 reconciliation):

- `pyoso` read-back of every table: row counts and schemas unchanged from the candidates.
- Assert the single shared new `declaration_version_id` across all deployed declaration-keyed tables
  (the §8 invariant, now against the platform).
- Update `assets.yaml` (`verified_at`, and note the new declaration generation), `migration-status.md`
  (record the id transition table from §7; mark the sentinel retired), `data-architecture.md` §4.5
  and the "Versioning identities" section (`evaluator_version` is now a real value, with the bump
  policy from D1), and any `where-scores-live` / DAG counts the change touches.

## Open decisions for the maintainer (blockers on execution)

- **D1 — the new `evaluator_version` value and bump policy.** Proposal: a monotonic string
  `"v1-openness-<yyyymm>"` (e.g. `v1-openness-202608`) or a bare `"v1"`, with the policy: **bump when
  the evaluator's scoring logic can change a result** — `build/check_rubric.py`'s ladder walk,
  license resolution, or recipe interpretation — and *not* for unrelated code. Recorded in a short
  note beside the constant, and each bump is its own cutover. Alternative considered: embed a hash of
  the evaluator modules (auto-bumps, but noisy and opaque). **Maintainer picks the value and policy.**
- **D2 — preserve vs refresh the observation snapshot** (§4). Recommended: preserve `9bd4d93a6fc6`.
- **D3 — include `registry.axis_assessments`** in the cutover (§1). Recommended: yes, so the whole
  declaration-keyed surface shares one generation; it needs its publisher wired first (§0).

## §0 — prerequisite code fixes (no platform write; land before execution)

1. **Archive-root / deployment-occurrence** (already flagged in `publish_scoring_trace.py` and
   shared with `publish_evaluation.py`): decouple the archive root from the read `--dir`. The archive
   must always be written to (and `latest_archive` read from) a fixed canonical root, so
   re-publishing a prior archive via `--dir` neither nests a new archive nor leaves the system
   claiming the superseded deployment is the latest live state. Add tests: publishing from an archive
   directory writes to the canonical root (or records a rollback occurrence there), and never inside
   the read directory.
2. **Cross-cutover identity invariant** (§8): a small checkable step asserting all candidates across
   the three publishers share one `declaration_version_id` + `source_git_sha`.
3. **(If D3)** a dedicated `registry.axis_assessments` publisher mirroring the others, or a
   documented manual path, before it can join the cutover.

Each of these is a normal reviewed code PR with tests, containing no platform mutation.
