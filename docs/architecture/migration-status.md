# Migration status

The ADR-003 repository-scope migration is **complete** (2026-08-30). This file now records only the
remaining blocked or deferred follow-on work — each tracked as a GitHub issue — plus the one
transitional runtime state (release atomicity) that a later phase resolves. The normative contract
lives in `data-architecture.md` and `adr-003-repository-scope-boundary.md`.

## Migration phases (done)

| Phase | Outcome |
|---|---|
| 0 — architecture record and inventory | Merged (#345). |
| 0b — deployed-model audit | Merged (#347); all deployed model definitions read, receipt at `warehouse/audits/platform_models.json`. |
| 1 — schedule normalization | Applied (#349), verified 2026-08-23 (every in-scope dataset fired a `SCHEDULED` run on its UTC cron). |
| 2 / 2A — normalized adoption observations + routing | Merged (#351, #356). `observations.product_adoption_current` deployed 2026-08-24 with the declared-identity guard; the §18 baseline frozen at `warehouse/data/observations/product_adoption_baseline.parquet`. |
| 3 — reconciliation report | Deployed (#368). `evaluation.product_adoption_measurements` and `evaluation.adoption_reconciliation` published, keyed on `declaration_version_id` + `observation_snapshot_id`. |
| 5 — scope reset (catalog split / long-tail) | **Externalized under ADR-003** (#404 → #405 → #406 → #407). The peripheral OSO pipelines were frozen under platform ownership and removed from this repo; receipt at `warehouse/audits/externalization.json`. `population: long_tail` retired; the governed inventory is the Gap Map's own data system. |
| 6 — repository-owned scoring trace | Deployed 2026-08-27; cutover prerequisites merged (#387, #388, #389). The `evaluator_version` cutover itself is a gated follow-on (below). |

The versioning identities these phases depend on — `declaration_version_id`
(`build/declaration_version.py`) and `observation_snapshot_id` (`build/observation_snapshot.py`) —
are implemented and specified in `data-architecture.md` §4.5.

## Remaining follow-on work

None of these blocks normal curation (adding or refreshing products and categories). Each is a
platform- or release-integrity improvement, tracked as an issue.

| Work | Status | Issue |
|---|---|---|
| Incremental adoption history (append-only `observations.product_adoption`) | Blocked on OSO incremental-model support | #352 |
| Authoritative row-to-run binding (`observations.source_runs`) | Blocked on OSO run-manifest emission (mechanism may come from Kariba OSO-4705) | #355 |
| Phase 4 — blocking adoption-agreement gate | Blocked on #355; every measured reconciliation row is `source_unavailable` (the accepted interim state, §18), so the gate is deliberately disabled | #410 |
| Phase 6 — `evaluator_version` cutover from the `v0-no-repo-evaluator` sentinel | Planned; prerequisites merged; pending explicit authorization | #411 |
| Phase 7 — retire the duplicate warehouse openness computation | Waits on multi-release dual-run agreement of the repo-owned trace (ADR-001) | #384 |
| Phase 8 — release manifests (`releases.*`, atomic materialization) | Not started; resolves the atomicity state below and binds `release_id` into the evaluation tables | #412 |

The five deployed `evaluation` tables (`product_adoption_measurements`, `adoption_reconciliation`,
`axis_facts`, `axis_rule_matches`, `axis_results`) are pre-positioned replacements whose reviewed
consumers are the Phase-4 gate (#410) and the Phase-7 openness retirement (#384) — "nothing uses it
yet", not deletion candidates. The retirement-candidate list is derived by `build/assets.py`
(`retirement_candidates()` / `no_reviewed_consumers()`) and reviewed under §17, never acted on
automatically; the open retirement review is #348.

## Assets with no reviewed consumer

Derived by `build/assets.py` (`no_reviewed_consumers()`) and drift-checked against this table.
Each is a **deployed** asset whose reviewed consumer belongs to a later phase — "nothing uses it
yet", not a deletion candidate (§17). `external` stays `unknown`, so this is weaker than "no
consumer".

| Asset | Reviewed consumer it awaits |
|---|---|
| `evaluation.product_adoption_measurements` | The Phase-4 blocking gate (#410), held on row-to-run binding (#355). |
| `evaluation.adoption_reconciliation` | The Phase-4 blocking gate (#410); the report is the deliverable, gating on it awaits #355. |
| `evaluation.axis_facts` | The Phase-7 openness-computation retirement (#384), gated on multi-release dual-run agreement. |
| `evaluation.axis_rule_matches` | The Phase-7 openness-computation retirement (#384). |
| `evaluation.axis_results` | The Phase-7 openness-computation retirement (#384); carries `reproduces_recorded`, the ADR-001 dual-run agreement. |

## Atomicity: which state is in force

**Transitional, until Phase 8 (#412).** Verified 2026-08-20: static models carry no version or
revision list and `registry.product_scores` reports `createdAt == updatedAt`, so each publish
replaces in place — there is no native release-scoped materialization. Per `data-architecture.md`
§12.2, `releases.*` does not exist yet; `registry.product_scores`, `build/notebook_data.json` and
the published notebooks are replace-in-place and **NOT atomic**. The definition-of-done clause
"joining current public tables cannot mix releases silently" is met for release-aware consumers and
**UNMET for compatibility consumers** until Phase 8 lands.
