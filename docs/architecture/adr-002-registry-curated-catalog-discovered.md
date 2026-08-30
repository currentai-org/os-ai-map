# ADR-002: `registry` is curated, `catalog` is discovered

**Status:** Accepted 2026-08-20. **Scope basis superseded by
[ADR-003](adr-003-repository-scope-boundary.md) (2026-08-29).**

> The `registry` vs `catalog` provenance distinction below still stands. What ADR-003 supersedes is
> this ADR's assumption that misfiled `catalog` tables should be *migrated into repo `registry`
> ownership*: those tables model the OSO organization, not the Gap Map's data system, so ADR-003
> **externalized** them (frozen under platform ownership) instead. Read the "belongs in registry" /
> "moves into catalog" / "two populations" passages below as the pre-ADR-003 plan, not current
> intent.

**Context:** `data-architecture.md` AD-3, section 10

## Decision

Both names are used, and they mean different things.

- **`registry`** holds curated, authoritative declarations compiled from `sources/`.
- **`catalog`** holds externally discovered inventory that has not necessarily been accepted
  into the map.

The test is provenance of row existence:

> If a curator controls whether the row exists, it belongs in `registry`. If a collector
> discovers the row, it belongs in `catalog`.

Measurements belong in neither. They belong in a source-specific `signal_*` dataset or in
`observations`.

## Why the test is provenance, not storage

The distinction is not static-versus-computed. `currentai.registry` and `currentai.catalog`
are both `STATIC_MODEL` datasets today, so that axis separates nothing. `registry` is
CI-pushed from `sources/` on every merge to main; `catalog` is uploaded by hand or by a
fetcher.

Nor is it curated-versus-machine-generated. An agent may generate a candidate at scale and
it stays discovery until a person accepts it. Acceptance is the curator act, and acceptance
is what `registry` records.

## What fails the test today

Audited 2026-08-20 against the live org. `currentai.catalog` holds ten tables, not the five
its README documents, and four are misfiled by this ADR's own test:

| Table | Verdict |
|---|---|
| `model_benchmarks` | Correctly `catalog`. Externally discovered leaderboard scores. |
| `model_repos` | Correctly `catalog`. Externally discovered mapping. |
| `country_populations` | Correctly `catalog`. External reference lookup. |
| `goodailist_repos` | Superseded by `signal_goodailist.repo_catalog`. Documented as retired; the table is live and the `ai-safety-incidents` notebook still reads it. |
| `osai_gap_map` | External third-party map. Its `maturity`, `parity_verdict` and `overall_score` columns read as Gap Map outputs and must be renamed to say whose map it is. No consumer found. |
| `osai_subcategory_mapping` | Curated crosswalk. Belongs in `registry`. No consumer found. |
| `taxonomy_crosswalk` | Curated crosswalk. Belongs in `registry`. No consumer found. |
| `pypi_downloads` | A measurement, 1.6M rows of daily downloads by package and country. Belongs in `observations`. |
| `foundation_model_repos` | The README calls it curated. A curator controls these rows, so it belongs in `registry`. |
| `stack_map` | Derived from `sources/` by `warehouse/models/catalog/stack_map.py`. A repo-derived bridge presented as external inventory. Belongs in `registry`. |

`registry.tail_products` passes the test and stays where it is. Tail rows are promoted or
rejected by a curator, and both are curator acts. Its platform table is absent only because
the last push had no rows — `build/publish_registry.py` records it as "94 bytes of header on
a push where every tail row was promoted or rejected".

## Consequences

The long-tail chain moves into `catalog` rather than needing a sixth namespace.
`entities.repos`, `.projects`, `.packages` and `.models` are discovered from the goodailist
roster; `long-tail-explorer` describes them as "the discovery set not yet scored in the gap
map", which is this ADR's definition of catalog restated.

Two populations then share the namespaces: roughly 522 curated products and roughly 24,600
discovered artifacts. That is intended. What keeps the gates coherent is that release gates
key on the declared `population` and `release_path`, never on the namespace.

Nothing in this ADR authorizes a deletion. Every reclassification above is recorded in
`warehouse/assets.yaml` as a `target_namespace` and executed in a later phase, with
consumers migrated first.
