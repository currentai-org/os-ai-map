# ADR-003: Repository scope boundary — govern the Gap Map, not the OSO org

**Status:** **Accepted — implementation pending**, 2026-08-29. This is a **plan only**: no asset is
moved, removed, or reclassified by this document; it sets the boundary and sequences the execution into
later reviewed PRs. **Accepting the ADR does not lift the Phase-5 freeze** — the freeze holds until the
mechanism PRs (the `role` field, `dependencies.yaml`, the root-scoped DAG, and the anti-reintroduction
gates; steps 2–4 below) are merged. The old Phase-5 runbooks are **superseded, not re-enabled**.
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
through OSO's own UI. The repository does not mirror it, assign it a migration status, or take
retirement obligations for it.

Population and release-path follow from this, not the reverse: **every governed asset carries
`population: gap_map`; only governed outputs additionally require `release_path: true`.** (The
`population: long_tail` value is retired as a *governed* population — see the gates.)

## Repository roles (a new `role` field on governed assets)

Every governed asset declares a `role`, so membership is asserted, not inferred from a graph:

| role | meaning | must be |
|---|---|---|
| `governed-output` | a **published Gap Map artifact whose schema and publication lifecycle are owned here** — regardless of whether its rows come exclusively from `sources/` (so the `evaluation.*` release-path publications, derived partly from `observations`, qualify) | `release_path: true` |
| `repo-computation` | repo-owned SQL/Python implementing or auditing map semantics | has a repo file; `authority: repo` |
| `compatibility-shim` | temporary shim for a (1)/(2) asset (named to avoid collision with the lifecycle `status: compatibility`) | carries `replacement` + a retirement trigger |

External dependencies are **not** governed assets and carry no `role` — they live in the manifest below.

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
  verified_revision: <platform revision hash>     # for a currentai.* USER_MODEL with a revision, OR
  # content_contract_sha256: <hash> + verified_at: <date>   # for an oso.* upstream with no revision
  owner: oso                                      # NOT this repo
```

`verified_revision` is used where the dependency is a `currentai.*` model with a platform revision; an
`oso.*` upstream that has no model revision instead records a `content_contract_sha256` (a hash of the
agreed schema/content contract) plus a `verified_at` date. A dependency entry confers **no** migration
status, retirement policy, source mirror, or namespace-cleanup obligation. It records what a governed
asset needs and lets a gate check the contract (grain/freshness) without claiming ownership of the
model's deployment. The manifest is created and populated in the execution PR (step 2 below); this ADR
specifies it and does not add the file.

## The DAG becomes root-scoped

The primary dependency graph is generated by **reachability from explicit map roots** (`sources/` →
`registry`/`evaluation` `governed-output`s and their `repo-computation`), **not** by enumerating every
asset. Standalone notebooks (`long-tail-explorer`, `oss-ai-trends`, `pypi-geo-trends`) **do not create
core DAG nodes**. Three separate views replace the single all-asset graph:

1. **Map governance** — `sources/` → `registry`/`evaluation` outputs.
2. **Runtime dependencies** — OSO inputs (from `dependencies.yaml`) → map computation.
3. **Compatibility / retirement appendix** — shims and their exits.

## Anti-reintroduction gates (proposed; added in the execution PR, not here)

These are executable invariants over `assets.yaml` **and** `dependencies.yaml` together — so the
manifest cannot itself grow into a new organization-wide inventory:

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

## Classification of the peripheral assets (for ownership transfer, not deletion)

**Do not delete working OSO tables.** Transfer their code/data ownership to the appropriate platform
repository, then remove them from this repo's inventory and publisher.

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

## Execution sequence (later PRs — frozen until this boundary lands)

1. **This PR (plan only):** the boundary rule, the role taxonomy, the `dependencies.yaml` spec, the
   root-scoped-DAG design, the anti-reintroduction-gate design, and the classification above. Amends the
   charter (`CLAUDE.md`) and marks Phase 5 migration frozen.
2. Add the `role` field to governed assets and create `warehouse/dependencies.yaml`.
3. Root-scope the DAG generator and split the three views.
4. Add the anti-reintroduction gates.
5. Externalize the 24 (ownership transfer to the platform repo; remove from inventory + publisher; **no
   OSO deletion**).
6. Resolve the 4 individually.

### Ownership-handoff precondition for step 5 (no orphaning)

Before any peripheral source is removed from this repo's inventory **and publisher**, a verified
ownership handoff must exist and be recorded:

- destination repository and path;
- responsible owner;
- the merged transfer commit / PR;
- a working deploy or publication path in the destination;
- proof that existing OSO consumers of the table remain functional after the handoff.

This is not optional bookkeeping: for `registry.foundation_model_repos`, removing it from *this*
publisher before another owner can reproduce it would **orphan the live input to `entities.models`**.
The recent `#397`/`#400` work is unwound by **transferring ownership**, never by reversing the platform
deployment — the deployed table keeps serving its readers until the destination reproduces it.

All Phase-5 platform migration (`osai_subcategory_mapping`/`taxonomy_crosswalk` → registry, `stack_map`
→ registry, and any `entities`/`events`/`metrics`/analytical-`scores` consolidation) is **held** until
the mechanism (steps 2–4) is merged. **Accepting this ADR does not lift the freeze.**

## Consequences

- The governed inventory shrinks to the Gap Map's actual data system (curated declarations, published
  outputs, the openness/adoption computation and its real OSO dependencies, plus compatibility shims).
- Parts of ADR-002 are superseded: catalog reference tables it routed *into* `registry` are instead
  **externalized**, because ownership follows the scope rule, not the provenance shape.
- Recent `foundation_model_repos` work (#397/#400) is unwound **through ownership transfer, not by
  reversing the platform deployment** (see the handoff precondition): the deployed table keeps serving
  `entities.models` until a destination owner reproduces it. The honest cost of having migrated under
  the old boundary.
- The agent stops generating cross-org consistency work, because the boundary no longer pulls unrelated
  OSO assets into repository governance.
