# Plan: the `evaluator_version` cutover (Phase 6 → the sentinel is retired)

**Status: PLAN FOR REVIEW. No platform mutation is authorized by this document.** The three
decisions the cutover turned on (D1–D3) are now **settled** (below); execution remains unauthorized
until the §0 prerequisite code fixes, durable archive persistence, and the cross-cutover checks are
in place.

## What the cutover is

`build/declaration_version.py:111` pins `EVALUATOR_VERSION = "v0-no-repo-evaluator"` — a sentinel
recording "scores are curator-recorded, not machine-derived." Phase 6 landed the repository-owned
evaluator (the `evaluation.axis_*` scoring trace, deployed 2026-08-27). Retiring the sentinel —
replacing it with a real evaluator version — is what this plan covers.

`declaration_version_id = f(source_git_sha, source_content_digest, evaluator_version)`
(`build/declaration_version.py`). `evaluator_version` is folded into **every**
`declaration_version_id`, and the id is **table-independent** — it depends only on the commit, the
declaration content, and the evaluator version, not on which table carries it. So bumping
`EVALUATOR_VERSION` re-keys every declaration-keyed table at once, and **rebuilding all candidates
from one commit collapses them to a single new id** (§3, §7).

## Settled decisions

- **D1 — the new value and bump policy.** `evaluator_version = "v1-repo-openness-evaluator"`.
  - **Bump** when evaluator *code* can change any canonical scoring-trace output for identical
    declarations — a normalized fact, license resolution, a rule outcome, a disposition, or a final
    score.
  - **Do not bump** for rubric or source changes: those already move `source_content_digest`.
  - **Do not bump** for behavior-preserving refactors *proven* by corpus-wide canonical equivalence.
  - **No date-based versions** — `source_git_sha` already carries chronology; the evaluator version
    names a behavior generation, not a time.
- **D2 — preserve the observation snapshot.** Rebuild the two adoption candidates from the same
  frozen Phase-2 baseline, holding `observation_snapshot_id = 9bd4d93a6fc6…`. See §4 for the precise
  reason this matters (and what it does *not* do).
- **D3 — leave `registry.axis_assessments` staged; exclude it from this cutover.** It has **no live
  identity to re-key**. Including it would widen the cutover, require standing up a new publisher,
  and deploy an unconsumed table. Note that "all tables share one id" is only a **cutover-moment
  invariant**, not a durable property: any later refresh of any table from a newer commit mints
  another declaration generation, because `source_git_sha` is part of the id. So its eventual first
  deployment is handled independently, whenever it happens, and simply inherits the evaluator version
  in force then.

## 1. The declaration-keyed surface: 6 in the architecture, 5 in this cutover, 1 excluded

Derived from `warehouse/assets.yaml` (every asset whose `grain` names `declaration_version_id`), not
hand-listed:

**Six declaration-keyed assets in the architecture:**

| Asset | Dataset | Publisher | In this cutover? |
|---|---|---|---|
| `evaluation.product_adoption_measurements` | `evaluation` | `build/publish_evaluation.py` | ✅ deployed |
| `evaluation.adoption_reconciliation` | `evaluation` | `build/publish_evaluation.py` | ✅ deployed |
| `evaluation.axis_facts` | `evaluation` | `build/publish_scoring_trace.py` | ✅ deployed |
| `evaluation.axis_rule_matches` | `evaluation` | `build/publish_scoring_trace.py` | ✅ deployed |
| `evaluation.axis_results` | `evaluation` | `build/publish_scoring_trace.py` | ✅ deployed |
| `registry.axis_assessments` | `registry` | (none yet) | ❌ **staged, excluded (D3)** |

**Five currently deployed** (`status: active` / `materialized: true`) are the cutover set. **One
staged** asset is explicitly excluded — it has no live table to re-key.

**Runtime completeness assertion:** re-derive the declaration-keyed set at execution time and require
the cutover to cover **every `active`/`materialized` declaration-keyed asset** — no more, no fewer.
It must *not* force `staged` assets into service; a staged asset that is somehow marked
active/materialized without being in the cutover set is the failure this catches, and a
still-staged asset is simply outside the set. Cover the live surface completely, or do not run.

## 2. The current live generations (the real "old" IDs — not one global value)

Read live via `pyoso` on 2026-08-27:

| Table(s) | Live `declaration_version_id` | Cut at commit |
|---|---|---|
| `product_adoption_measurements`, `adoption_reconciliation` | `232015a76ecc…` | `f012d85` |
| `axis_facts`, `axis_rule_matches`, `axis_results` | `eb828b57b14d…` | `980250b` |

There are **two** live generations, because the eval tables and the trace tables were deployed from
different commits. The rollback and transition map treat these as distinct old IDs (§7, §9).
`registry.axis_assessments` has no live id (staged) and does not appear.

## 3. One clean cutover commit

All candidates are built from a **single `main` commit** whose only material change is the
`EVALUATOR_VERSION` bump (plus this plan and the §0 prerequisite fixes), over a **clean worktree**.
Because the id is commit- and evaluator-scoped and **table-independent**, one commit + one new
`evaluator_version` yields **one** new `declaration_version_id` shared by every table in the cutover
set. `observation_snapshot_id` does **not** enter `declaration_version_id`, so preserving the
snapshot (D2) is not what makes the id shared — the single commit and single evaluator version are.
What preserving the snapshot buys is separate and is covered in §4.

## 4. What preserving the observation snapshot actually does (D2)

`product_adoption_measurements` and `adoption_reconciliation` also key on `observation_snapshot_id`
(currently `9bd4d93a6fc6`); the trace tables do not, and `observation_snapshot_id` is **not** part of
`declaration_version_id`. Preserving the snapshot therefore does not affect the shared id. What it
does is hold the adoption **content** fixed: rebuilt from the same frozen baseline, the two adoption
tables' rows are identical to what is deployed except for the identity columns — which is exactly
what the semantic no-change invariant in §8 verifies. Refreshing from live
`observations.product_adoption_current` would change adoption content in the same deploy and defeat
that invariant, making the id transition impossible to attribute to the evaluator bump alone.

## 5. Handling the non-atomic interval

Static models replace in place and are published sequentially, so mid-cutover some tables carry the
new id and some the old. There is no release-scoped materialization yet (`releases.*` does not exist;
atomicity is transitional per `migration-status.md`). Mitigations:

- **Low blast radius today.** Nothing consumes these tables cross-generation on the platform: the
  Phase-4 gate is disabled and the Phase-7 retirement has not begun, so no live query joins an
  old-id table to a new-id table. The window is real but currently harms no consumer.
- **One session, fail-fast.** Run the whole cutover in a single maintainer session; each publisher
  already polls each run group to terminal `SUCCESS` and exits non-zero on the first failure, so a
  partial cutover stops loudly rather than silently half-swapping.
- **Announced window**, and a **post-swap invariant check** (§8, §10): after all deploys, assert
  every deployed declaration-keyed table carries the *same* new id; a straggler means the swap did
  not complete.

## 6. Deployment order

From the cutover commit, after a full dry-run of both publishers:

1. **Scoring trace** — `build/publish_scoring_trace.py` (`axis_facts`, `axis_rule_matches`,
   `axis_results`).
2. **Adoption evaluation** — `build/publish_evaluation.py` (`product_adoption_measurements`, then
   `adoption_reconciliation`, the order the publisher already uses because reconciliation reads
   measurements as candidate rows in-repo).

**Deploy: trace → adoption.** Order is not forced by platform reads (the tables are independent
static models); the most self-contained set (the trace) swaps first. Each publisher is serialized
and SUCCESS-gated internally. `registry.axis_assessments` is not in this sequence (D3).

## 7. Old → new declaration-ID transition map

The new id is not knowable until `EVALUATOR_VERSION` is bumped and the commit is made; the procedure
captures it. `SELECT DISTINCT declaration_version_id` per table **before** (done above) and
**after**; both old generations must map to the single `<new>` id, and no table may retain an old id.

| Old generation | Tables | New id |
|---|---|---|
| `232015a76ecc…` | measurements, reconciliation | `<new>` (computed at the cutover commit) |
| `eb828b57b14d…` | axis_facts, axis_rule_matches, axis_results | `<new>` |

## 8. Pre-flight invariants: counts, schemas, single identity, and semantic no-change

Before any upload, build every candidate at the cutover commit and assert:

- **Row counts** match the builders: adoption 377 / 522 (from the preserved baseline); trace 2,284 /
  2,734 / 522.
- **Schemas** equal each builder's `COLUMNS` (the publishers already gate this per file).
- **Per-file authority** — `publish_scoring_trace` canonical-equivalence and `publish_evaluation`
  `validate_candidates` already prove each file is exactly its builder's output at HEAD.
- **Single-identity invariant.** Every candidate across both publishers shares **one**
  `declaration_version_id` and one `source_git_sha` (on the tables that carry it). This proves the
  single-commit build produced a single generation. Implemented as
  `build.cutover_preflight.single_identity_problems` (§0.2).
- **Semantic no-change invariant (the important one).** The cutover must change **identity only** —
  not facts, rule matches, scores, routes, statuses, or reconciliation results. For each of the five
  live tables, project out the fields expected to change — `declaration_version_id`, `source_git_sha`
  where present, and any explicitly non-content build/deployment timestamp (`evaluated_at` on
  `adoption_reconciliation`; the per-table set is `cutover_preflight.NON_CONTENT_COLUMNS`, re-affirmed
  at execution time) — and require the **new candidate rows to equal the currently-deployed rows
  canonically** (order-independent multiset, tolerating the loader's all-null-column drop). Any
  difference outside the projected-out columns fails the cutover: it would mean the evaluator bump is
  smuggling a content change, which D1's bump policy forbids without its own justified generation.
  Implemented as `build.cutover_preflight.semantic_no_change_problems` (§0.2); the deployed rows come
  from an offline CSV export (`--deployed-dir`) or a read-only `pyoso` read (`--live`).
- **Hashes** — record the sha256 of every uploaded CSV in the deploy note (the publishers archive
  these in each receipt).

## 9. Rollback — reverse-order, by archived bytes (with real gaps to close first)

Rollback re-uploads the **previous generation's archived bytes** in reverse deploy order —
**adoption → trace** — restoring the old ids: `publish_* --rollback <artifact_id>` (it verifies the
archived bytes' hashes and reconstructs provenance before re-uploading). Both §0.1 gaps are now
closed (content-addressed archive; provenance-gated rollback).

**Durable persistence** — the local archives under `build/evaluation/…deployments/` are git-ignored
and per-session ephemeral, so `build/release_persistence.py` gives rollback bytes a durable home.
The executable per-deploy sequence is **stage → Release → publish → record**:

```bash
# 1. stage: persist the content-addressed artifact locally, network-free; prints <artifact_id>
uv run python -m build.publish_scoring_trace --stage-artifact --dir build/evaluation \
    --archive-root build/evaluation/scoring-trace-deployments
# 2. Release: push the artifact to a durable GitHub Release (draft -> verify -> publish)
uv run python -m build.release_persistence persist --publisher scoring-trace \
    --archive-root build/evaluation/scoring-trace-deployments --artifact-id <artifact_id>
# 3. publish: the OSO deploy of the EXACT released artifact (uploads, runs, verifies) — --deploy-artifact
#    binds the OSO publish to the staged/Released id, never re-reading (and re-hashing) --dir
uv run python -m build.publish_scoring_trace --deploy-artifact <artifact_id> \
    --archive-root build/evaluation/scoring-trace-deployments
# 4. record: write the durable append-only occurrence file for the reconciliation PR to commit
uv run python -m build.release_persistence record-occurrence --publisher scoring-trace \
    --archive-root build/evaluation/scoring-trace-deployments
```

`restore` recovers an artifact from its Release into a fresh container before a rollback
(`release_persistence restore --publisher … --artifact-id …`): it downloads and FULLY validates the
bytes in a temp dir first — safe extraction, content-addressing to the requested id, `SHA256SUMS`
agreement with the extracted CSVs, the publisher's exact filename set, and receipt provenance
recomputed from the bytes — and only then rebuilds `artifacts/<artifact_id>/` atomically, so a forged
receipt or tampered `SHA256SUMS` leaves no artifact directory at all.

**Persist both currently-live generations before the cutover** — but heed the byte-fidelity warning:
the trace generation `eb828b57b14d` can be reproduced exactly by rebuilding at `980250b`; the
evaluation generation `232015a76ecc` **cannot** — rebuilding at `f012d85` regenerates `evaluated_at`,
so the bytes differ. Recover the original evaluation archive if it still exists, or export the
currently-deployed rows and **verify logical equivalence explicitly**; do NOT label regenerated bytes
as the original `232015a76ecc` artifact (a different byte-set is a different `artifact_id` by design).

## 10. Post-deploy verification and lockstep reconciliation

After the swap, in one reconciliation PR (mirroring the Unit-2 reconciliation):

- `pyoso` read-back of every table: row counts and schemas unchanged from the candidates.
- Assert the single shared new `declaration_version_id` across all deployed declaration-keyed tables
  in the cutover set (the §8 single-identity invariant, now against the platform).
- Update `assets.yaml` (`verified_at`, note the new declaration generation), `migration-status.md`
  (record the §7 transition table; mark the sentinel retired), `data-architecture.md` §4.5 and the
  "Versioning identities" section (`evaluator_version` is now `v1-repo-openness-evaluator`, with the
  D1 bump policy), and any `where-scores-live` / DAG counts the change touches.

## §0 — prerequisite code fixes (no platform write; land and review before execution)

1. **Archive-root / deployment-occurrence.** Rework the archive mechanism in **both**
   `build/publish_evaluation.py` and `build/publish_scoring_trace.py` so it:
   - separates the read `--dir` (where candidates are read) from a fixed `--archive-root` (where the
     durable archive lives);
   - stores immutable content archives keyed by content/deployment identity;
   - records each successful deployment **or rollback** as a distinct **append-only occurrence**;
   - determines the current and prior live states from those **occurrences**, not from directory
     modification times;
   - **never nests** an archive when publishing from archived bytes;
   - applies consistently across the evaluation and scoring-trace publishers.
   Tests only; no platform mutation.
2. **Cross-cutover identity + semantic no-change checks** (§8) — **implemented** in
   `build/cutover_preflight.py` (tests only, no platform write): `single_identity_problems` asserts
   all candidates across both publishers share one `declaration_version_id` + `source_git_sha`, and
   `semantic_no_change_problems` asserts each live table's candidate equals the deployed rows
   canonically once the per-table non-content columns are projected out. Run offline as
   `uv run python -m build.cutover_preflight --dir build/evaluation` (single identity), adding
   `--deployed-dir <export>` or `--live` for the semantic check.

(There is deliberately **no** `registry.axis_assessments` publisher item here — D3 excludes it from
the cutover; its eventual first deployment is a separate, independent step.)

Each of these is a normal reviewed code PR with tests, containing no platform mutation. The evaluator
cutover itself stays unauthorized until §0.1, §0.2, and durable archive persistence (§9) are all in
place.
