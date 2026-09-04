# ADR-003: Repository scope boundary — govern the Gap Map, not the OSO org

**Status:** **Accepted; fully implemented (steps 2–6), 2026-08-29.** This document is the plan; it
has now landed in full. The mechanism (steps 2–4) — the `role` field on governed assets,
`warehouse/dependencies.yaml`, the root-scoped DAG, and the anti-reintroduction gates — is merged,
and the externalization (steps 5–6) is complete: the 28 externalized assets (24 long-tail
pipelines + 4 questionable gap_map tables) were removed from this repo's inventory and publisher and
**frozen under platform ownership** — disposition `frozen-without-producer`, recorded per asset in
`warehouse/audits/externalization.json` (archived source hashes, platform IDs, consumers at removal).
That is the no-orphan disposition, **not** a verified ownership transfer to a named destination repo:
**no OSO table was deleted** — each deployed table is retained and frozen at its last publish, its
repo producer removed, and its consumers still resolve against it. The governed inventory is now 42
governed assets + 18 dependency contracts; the `long_tail` population is retired and the backlog is
empty, kept so by the gates.
**Supersedes:** the scope *basis* of ADR-002 and `data-architecture.md` §11.3 (the transitive-closure
membership rule). ADR-002's provenance test (`registry` vs `catalog`) stands; its assumption that every
misfiled `catalog` table must be *migrated into repo ownership* does not.

## Context — the root cause

Inventory membership is currently triggered by:

```text
exists on OSO  OR  is read by any repository notebook
    → inventory membership (assets.yaml)
    → migration / lifecycle / retirement obligations
    → main DAG membership
```

Three implementation choices make that boundary inevitable: `assets.yaml` is defined as "one entry per
platform table"; `build.assets` scans every model, build module, workflow **and standalone notebook** as
a graph root; and the DAG renders every inventoried asset. So the repository models *the OSO
organization's warehouse* rather than *the data system governing the Open Source AI Gap Map*.

The ownership test is wrong: **a live OSO notebook reading a table does not make that table part of Gap
Map governance.** The symptom, from the current inventory (dated reading, 2026-08-29):

- <!-- observed:2026-08-29 -->73 total assets, of which only <!-- observed:2026-08-29 -->28 are on the
  Gap Map release path (`release_path: true`).
- <!-- observed:2026-08-29 -->24 carry `population: long_tail` — the entire `entities`, `events`,
  `metrics` and analytical `scores` pipelines plus catalog reference inputs. They power the standalone
  `long-tail-explorer` / `oss-ai-trends` notebooks and other platform work, **not** the governed map.

That is why the migration keeps generating namespace moves, schedules, compatibility states, audit
receipts and retirement obligations: the complexity is produced by the repository's boundary, not by the
Gap Map. Recent `registry.foundation_model_repos` work (#397/#400) is a concrete instance — a
`population: long_tail`, `release_path: false` table that exists only to feed `entities.models` became a
registry *publication* responsibility. It should not have.

## Decision — the boundary rule

The repository tracks two different kinds of thing, in two different files:

**Governed assets** (`warehouse/assets.yaml`) — things the repository *owns*. An entry is a governed
asset only if it is one of:

1. **A curated declaration or published table directly powering the Gap Map** (a governed output).
2. **Repo-owned computation implementing or auditing Gap Map scoring / adoption / openness semantics.**
4. **A temporary compatibility object for (1) or (2)** with a defined exit (a named `replacement` and a
   retirement trigger).

**Dependency contracts** (`warehouse/dependencies.yaml`) — things the repository *depends on but does
not own*:

3. **A direct OSO input required by a (1)/(2) asset** — recorded as a contract (purpose, grain,
   freshness, verified revision or content hash, `owner: oso`). **A dependency contract is never a
   governed asset and never appears in `assets.yaml`.**

Everything else — a table that merely exists on OSO, or is read only by standalone notebooks or other
platform products — is **out of scope** in both files. It keeps living on OSO and is discoverable
through OSO's own UI. The repository assigns it no migration status and takes no retirement obligation
for it. (The one exception: a category-3 dependency the repo actually reads may keep a **read-only
mirror file** of the platform model's definition, so the dependency chain stays inspectable and its
provenance is gated — a mirror is provenance, not ownership, and confers no governance. An out-of-scope
table gets no such mirror.)

Population and release-path follow from this, not the reverse: **every governed asset carries
`population: gap_map`; only governed outputs additionally require `release_path: true`.** (The
`population: long_tail` value is retired as a *governed* population — see the gates.)

## Repository roles (a new `role` field on governed assets)

Every governed asset declares a `role`, so membership is asserted, not inferred from a graph:

| role | meaning | must be |
|---|---|---|
| `governed-output` | a **published Gap Map artifact whose schema and publication lifecycle are owned here** — regardless of whether its rows come exclusively from `sources/` (so the `evaluation.*` release-path publications, derived partly from `observations`, qualify) | `release_path: true`; `authority: repo` |
| `repo-computation` | repo-**owned** SQL/Python implementing or auditing map semantics | has a model file; `authority: repo`. A `mirror:` block proves provenance, not ownership, so a platform-authored mirror is **not** a repo-computation — it is a dependency contract |
| `governed-data` | a repo-**owned** data or control artifact that is not a computation — the frozen adoption baseline (bytes, not a query) and the `source_runs` control snapshot | `authority: repo`; not `release_path`; no model file |
| `compatibility-shim` | temporary shim for a (1)/(2) asset (named to avoid collision with the lifecycle `status: compatibility`); may be a platform mirror, since a shim is transitional by definition | carries `replacement` |

External dependencies are **not** governed assets and carry no `role` — they live in the manifest below. Because a mirror is provenance and not ownership, the seven platform-authored mirrors the repo reads — the openness chain (`evidence.product_evidence`, `scores.openness_facts`, `scores.openness_computed`) and the signal ingestion (`signal_github`/`signal_huggingface`.`artifact_state`, `signal_pypi.package_downloads`, `signal_semanticscholar.paper_citations`) — are **dependency contracts**, not governed assets (implemented 2026-08-29).

## External dependency manifest — `warehouse/dependencies.yaml`

Category-3 OSO inputs are recorded as **contracts**, not owned models. Proposed schema (per entry):

```yaml
- table: currentai.signal_github.artifact_state   # or an oso.* upstream
  purpose: adoption_and_evidence                  # why a (1)/(2) asset needs it
  expected_grain: one row per (artifact_kind, artifact_id)
  freshness_requirement: <= 8 days
  required_by:                                     # the named repo computation(s) that read it
    - warehouse/models/observations/product_adoption_current.sql
  # Provenance anchor — exactly one of:
  verified_revision: <integer platform revision number, == the mirror block's revision>   # currentai.* mirror, OR
  # content_contract_sha256: <hash> + verified_at: <date>   # for an oso.* upstream with no revision
  owner: oso                                      # NOT this repo
```

`verified_revision` is used where the dependency is a `currentai.*` platform model with a revision; the
repo keeps its read-only `mirror` **file** (claimed by the contract) and the gate recomputes the file's
`local_sha256`, so a silent edit is caught. An `oso.*` upstream that has no model revision instead
records a `content_contract_sha256` — the fingerprint of the agreed schema (table + grain + TYPED
`expected_columns`, each `{name, type, nullable}`; names alone are insufficient) — plus a `verified_at`
date, and the gate recomputes it. A dependency entry confers **no** migration status, retirement policy,
or namespace-cleanup obligation; a `currentai.*` mirror the repo will retire (the openness chain, #384)
carries a `retirement_context` recording that the repo drives the retirement without owning the model.
Implemented 2026-08-29.

## The DAG becomes root-scoped

The primary dependency graph is generated by **reachability from explicit map roots** (`sources/` →
`registry`/`evaluation` `governed-output`s and their `repo-computation`), **not** by enumerating every
asset. Standalone notebooks (`long-tail-explorer`, `oss-ai-trends`, `pypi-geo-trends`) **do not create
core DAG nodes**. Three separate views replace the single all-asset graph:

1. **Map governance** — `sources/` → `registry`/`evaluation` outputs.
2. **Runtime dependencies** — OSO inputs (from `dependencies.yaml`) → map computation.
3. **Compatibility / retirement appendix** — shims and their exits.

## Anti-reintroduction gates (implemented 2026-08-29)

Executable invariants over `assets.yaml` **and** `dependencies.yaml` together — so the manifest
cannot itself grow into a new organization-wide inventory. Implemented in `build/assets.py`
(`role_violations`, `dependency_violations`, `notebook_root_violations`) and asserted in
`tests/test_assets_inventory.py` + `tests/test_scope_gates.py`; see `data-architecture.md` §11.5.
Gate 6 is enforced against the governed set (assets carrying a `role`): `gap_map` is the only
governed population, so no `long_tail` asset can appear; the 28 externalized tables are recorded in
the reproducible externalization receipt, and the role/scope gates keep any of them — or any other
peripheral table — from re-entering the governed inventory.

1. **Governed-output ⇔ release_path.** A `governed-output` asset must be `release_path: true`, and a
   `release_path: true` asset must be a `governed-output`.
2. **Every external table a repo computation reads appears in `dependencies.yaml` exactly once** — a
   platform-authored input is a dependency contract, not a governed asset; the only exception is a
   `compatibility-shim`, which is a governed asset by design.
3. **A dependency cannot also appear in `assets.yaml`** (and a governed asset cannot appear in
   `dependencies.yaml`) — the two files are disjoint.
4. **Every dependency is referenced by at least one named repo computation** (`required_by`), and
   **no dependency is referenced only by a standalone notebook or an external platform product.**
   `required_by` is recorded and mechanically re-derived from the repo-computation reads, and the gate
   fails if the two disagree — so an unused or notebook-only dependency cannot linger.
5. **A standalone-notebook read never confers membership** in either file: the DAG reachability roots
   exclude notebooks that are not themselves map publications.
6. **`population: long_tail` is retired as a *governed* population.** Every governed asset is
   `population: gap_map`. The repo's legitimate tail-candidate registry (`registry.tail_products`,
   curator-promoted) is distinct from the OSO long-tail analytics pipeline; both currently say "long
   tail", which obscures ownership — the analytics pipeline externalizes, the tail-candidate registry
   stays and is not `long_tail`.

## Classification of the peripheral assets (for freeze under platform ownership, not deletion)

**Do not delete working OSO tables.** Freeze each deployed table under platform ownership at its last
publish (`frozen-without-producer`) — or, where a destination reproduces it, point consumers there —
then remove them from this repo's inventory and publisher. This is the no-orphan disposition, not a
verified ownership transfer to a named destination repo.

### The 24 `long_tail` assets → externalize

| Group | Assets | Disposition |
|---|---|---|
| Discovery pipeline | `entities.{repos,models,packages,projects}`, `signal_goodailist.repo_catalog`, `catalog.goodailist_repos` | Externalize. Feeds `long-tail-explorer`, not the canonical map. |
| Activity pipeline | `events.github_events`, `metrics.daily` | Externalize. Feeds `oss-ai-trends` + platform products. |
| Analytical scores | `scores.{dependency_graph,fragility,ossd_coverage,project_summary,repos_summary,investment_ranking,taxonomy}` | Externalize. Platform analytics; none is `release_path`. |
| Catalog reference | `catalog.{country_populations,model_benchmarks,model_repos,pypi_downloads,osai_gap_map,osai_subcategory_mapping,taxonomy_crosswalk}` | Externalize or record as a dependency **only** where a (1)/(2) asset provably reads it. |
| Recently over-scoped | `registry.foundation_model_repos` + `catalog.foundation_model_repos` | Externalize with the discovery pipeline it feeds. **This partly unwinds #397/#400** — noted honestly; the registry publication was created under the old boundary and should not persist under this one. |

Per-asset ownership confirmation happens in the execution PR (step 5); a `long_tail` asset that a
`governed-output` or `repo-computation` provably reads becomes a category-3 dependency contract instead
of leaving entirely.

### The 4 questionable `gap_map` assets → resolve individually

None currently participates in the canonical map pipeline (all `release_path: false`):

| Asset | Finding | Proposed |
|---|---|---|
| `catalog.stack_map` | Repo bridge read by `scores.stack_contributors` + the `long-tail-explorer` notebook — neither is the canonical map. | Externalize (it serves the long-tail explorer). **This retires the `stack_map → registry.stack_map` transition** that was otherwise Phase 5's last unit. |
| `scores.stack_contributors` | Repo analytical model, no in-repo reader, no reviewed platform consumer. | Externalize. |
| `signal_artificialanalysis.model_evaluations` | No consumer at all (no repo, no platform, no notebook). | Drop from governed scope; record as a dependency only if a map use emerges. |
| `signal_lmarena.text_leaderboard` | Read only by `ai_demand_curve.model_capability_current` (an out-of-scope platform product). | Externalize. |

Each keeps the rule: **gain a named Gap Map use, or leave the governed inventory.**

## Execution sequence (all steps landed 2026-08-29)

1. **Plan (#404):** the boundary rule, the role taxonomy, the `dependencies.yaml` spec, the
   root-scoped-DAG design, the anti-reintroduction-gate design, and the classification above. Amended the
   charter (`CLAUDE.md`).
2. Add the `role` field to governed assets and create `warehouse/dependencies.yaml`.
3. Root-scope the DAG generator and split the three views.
4. Add the anti-reintroduction gates.
5. Externalize the 24 (freeze under platform ownership, `frozen-without-producer`; remove from
   inventory + publisher; **no OSO deletion**).
6. Resolve the 4 individually.

### No-orphan precondition for step 5

One rule, not a checklist (everything here is the same account, so a "responsible owner" field carries
no signal): **do not leave a consumed table with no producer and no data.** Concretely, before removing
a source from this repo's inventory and publisher, confirm both:

- the deployed OSO table still exists (never deleted as part of cleanup), and
- every consumer that still reads it — in this repo or on the platform — still resolves.

If a destination reproduces the table, point consumers there; if not, the deployed table simply freezes
at its last publish, which is acceptable for the curated reference tables here **only while their
consumers keep resolving**. `registry.foundation_model_repos` was called out as the case that must not
be shortcut — its deployed table keeps serving `entities.models` — and steps 5–6 resolve it explicitly
rather than by shortcut. Its sole consumer, `entities.models`, is **itself** one of the externalized
tables: it too is frozen under platform ownership (`frozen-without-producer`, in the same receipt). So
this is a **frozen consumer reading a frozen producer** — both deployed tables retained on the platform
at their last publish, neither with a repository producer, both out of this repo's governance. The
no-orphan rule holds because the data is retained (the table is frozen, not deleted) and the consumer
still resolves against it; there is no repo-side staleness because neither table is regenerated here.
**This ADR authorizes that frozen dependency explicitly, accepting its staleness and availability
risk:** `registry.foundation_model_repos` and `entities.models` are static at their last platform
publish, and the platform maintainer owns keeping them live or retiring the pair together — the
repository no longer does. This is why the `#397`/`#400` registry publication is unwound by freezing the
deployed table, not by reversing the platform deployment. (Had the consumer been a *live governed*
asset, the producer would have had to stay produced until that reader was repointed; it is not, so it
does not.)

The Phase-5 platform migration those runbooks described (`osai_subcategory_mapping`/`taxonomy_crosswalk`
→ registry, `stack_map` → registry, and any `entities`/`events`/`metrics`/analytical-`scores`
consolidation) was never executed: steps 5–6 externalized those tables instead, so the moves are moot
and their runbooks stay superseded.

## Consequences

- The governed inventory shrinks to the Gap Map's actual data system (curated declarations, published
  outputs, the openness/adoption computation and its real OSO dependencies, plus compatibility shims).
- Parts of ADR-002 are superseded: catalog reference tables it routed *into* `registry` are instead
  **externalized**, because ownership follows the scope rule, not the provenance shape.
- Recent `foundation_model_repos` work (#397/#400) is unwound **by freezing the deployed table, not by
  reversing the platform deployment** (see the no-orphan precondition): its repo producer/publisher are
  removed and the deployed `registry.foundation_model_repos` keeps serving `entities.models` frozen at
  its last publish (disposition `frozen-without-producer`). The honest cost of having migrated under the
  old boundary — a freeze, not a completed ownership transfer.
- The agent stops generating cross-org consistency work, because the boundary no longer pulls unrelated
  OSO assets into repository governance.

## Addendum — reclaiming a dependency (2026-09-04)

An externalized table can come back. It becomes a legitimate category-3 input again when an in-scope
governed asset starts reading it. The boundary rule is unchanged: what
qualifies the table is a named repo computation that reads it, exactly as for any other dependency
contract. Nothing here weakens a gate or creates an exception for a particular table.

The transition is recorded, not erased. `warehouse/audits/externalization.json` stays append-only, so
the disposition history reads **in-scope → externalized (`frozen-without-producer` or `transferred`)
→ `reclaimed-as-dependency`**: the original entry in `assets` is left byte-identical, and a `reclaims`
record is appended alongside it carrying `table`, `prior_disposition`, `prior_date`,
`new_disposition`, `date`, `reason`, and `governed_reader` — the in-repo file that now reads the
table.

`reclaimed-as-dependency` means the table is **still platform-owned and still not deployed from this
repo**, and is once again inside the repo's governed dependency graph. Its representation is a
`warehouse/dependencies.yaml` contract with a mirror block, which is provenance, not ownership. A
reclaimed table never becomes a governed asset; `assets.yaml` and the receipt's `assets` list are
both untouched by a reclaim.

`build.assets.reclaim_violations()` enforces it. A reclaim record is valid only if the table has a
prior externalization entry with the stated disposition and date, `governed_reader` exists in the
tree and genuinely reads the table (re-derived with the same scanner as the rest of the graph), and a
contract with a mirror block exists for it. The converse is also a hard error: a contract for a table
the receipt externalized, with no reclaim record, means the externalization was undone silently. The
reproduction check then treats a reclaimed table as still in the **historical** removed set — that
set never shrinks — while `still_external_count` records the population currently outside the graph,
so the shrink is written down rather than inferred.

Two limits keep a reclaim from being a general amnesty:

- **Only a frozen table is reclaimable.** `prior_disposition` must be `frozen-without-producer`. A
  `transferred` table is owned by its named destination repository, so a contract for it would have
  to declare `owner: oso` falsely and its mirror would anchor to a model that repo now owns.
  Reclaiming a transferred table needs a ruling; until there is one the gate fails closed.
- **A reclaim re-admits only the files its own contract claims.** The archived-file and
  producer checks are relaxed for the contract's declared mirror paths and nothing else, so a
  fetcher, a data file, or a second model deriving the same table stays a violation. Those mirror
  paths are then content-bound by the existing mirror integrity check.
