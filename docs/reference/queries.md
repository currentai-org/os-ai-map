# CurrentAI Queries Guide

## Dataset layout

The `currentai` warehouse uses three-part names: `currentai.<dataset>.<table>`. `warehouse/assets.yaml`
inventories only the tables this repo **governs** — the `registry`, `observations` and `evaluation`
datasets plus the governed `signal_*` collectors and compatibility shims. The read-only `signal_*`
mirrors of platform-owned models are **not** governed; they are dependency contracts in
`warehouse/dependencies.yaml`. `docs/architecture/data-architecture.md` documents both.

The datasets below (`catalog`, `signal_goodailist`, `entities`, `events`, `metrics`, `scores`) were
**externalized under ADR-003**: they model the OSO organization, not the Gap Map's data system, so they
are frozen under platform ownership and are no longer repo-maintained. They still exist on the platform
and can be queried, but treat them as OSO tables, not repo-governed assets. The worked examples further
down that read them are historical.

| Dataset | Type | Key tables | Scope |
|---------|------|------------|-------|
| `registry` | Static/UDM | `product_scores`, `product_artifacts`, `adoption_routes`, … | **Governed (repo)** |
| `observations` | UDM | `product_adoption_current` | **Governed (repo)** |
| `evaluation` | Static | `product_adoption_measurements`, `adoption_reconciliation`, `axis_*` | **Governed (repo)** |
| `catalog` / `entities` / `events` / `metrics` / `scores` / `signal_goodailist` | UDM/CSV | — | Externalized (frozen, platform-owned) |

`oso.*` tables are public and can be queried with any valid key.

## Worked examples (externalized datasets)

Every example below reads a dataset ADR-003 externalized. They still run. What they return
stopped advancing at that table's last publish, so a result set that looks current is not,
and nothing in the query itself says so. Each example carries the warning as a SQL comment,
which is the only part of this page that survives a copy into your client.

For a table this repo still maintains, start at `registry`, `observations` or `evaluation`.

**Repo-level snapshot,** `scores.repos_summary`:
```sql
-- FROZEN (ADR-003): scores.repos_summary has no producer in this repo and stopped
-- advancing at its last publish. Results are historical.
SELECT * FROM currentai.scores.repos_summary WHERE country = 'France' ORDER BY stars DESC
```

**Project-level data,** `scores.project_summary`:
```sql
-- FROZEN (ADR-003): historical, no longer refreshed.
SELECT * FROM currentai.scores.project_summary ORDER BY total_stars DESC LIMIT 20
```

**Time-series,** `metrics.daily` (long format). The series ends at the freeze date, so do not
read its last point as today:
```sql
-- FROZEN (ADR-003): the series stops at the last publish, it does not run to today.
SELECT day, value FROM currentai.metrics.daily
WHERE repo = 'pytorch/pytorch' AND metric = 'stars'
ORDER BY day
```

**Raw events,** `events.github_events`:
```sql
-- FROZEN (ADR-003): no events after the last publish, so counts are a closed window.
SELECT event_type, COUNT(*) FROM currentai.events.github_events
WHERE repo = 'pytorch/pytorch' GROUP BY event_type
```

## SQL dialect (Trino)

- `CAST(x AS VARCHAR)` not `SAFE_CAST`
- `DATE_TRUNC('month', dt)` not `DATE_TRUNC(dt, MONTH)`
- `COALESCE` not `IFNULL`
- `CURRENT_DATE - INTERVAL '30' DAY` for date math
- `ARRAY_AGG` / `ARRAY_JOIN` not `STRING_AGG`

## Join patterns

The `entities`, `metrics` and `scores` joins below all read externalized tables. They are
kept because the join shapes are still the right ones, not because the data is current.

```sql
-- FROZEN (ADR-003): every entities/metrics/scores table in this block is frozen at its
-- last publish. The join shapes hold; the rows do not advance.

-- Repo → project
SELECT r.repo, r.project_slug, p.display_name, p.location
FROM currentai.entities.repos r
LEFT JOIN currentai.entities.projects p ON r.project_slug = p.project_slug

-- Project → packages
SELECT p.package_source, p.package_name, p.url
FROM currentai.entities.packages p
WHERE p.project_slug = 'pytorch'

-- Project → models
SELECT m.model_id, m.url, m.benchmark_avg
FROM currentai.entities.models m
WHERE m.project_slug = 'pytorch'

-- Monthly dev counts by category (from metrics.daily). The last month is the freeze
-- month, not the current one.
SELECT r.category, DATE_TRUNC('month', m.day) AS month,
  MAX(CASE WHEN m.metric = 'contributors' THEN CAST(m.value AS INTEGER) END) AS devs
FROM currentai.metrics.daily m
JOIN currentai.scores.repos_summary r ON m.repo = r.repo
WHERE m.metric = 'contributors'
GROUP BY r.category, DATE_TRUNC('month', m.day)

-- Ossinsight collection membership (via oss_directory)
SELECT pc.collection_name, c.display_name, COUNT(*) AS repos
FROM oso.oss_directory.projects_by_collection pc
JOIN oso.oss_directory.collections c ON pc.collection_id = c.collection_id
JOIN oso.oss_directory.artifacts_by_project a ON pc.project_id = a.project_id
WHERE pc.collection_name LIKE 'ossinsight-%' AND a.artifact_source = 'GITHUB'
GROUP BY pc.collection_name, c.display_name
```

## Join and dedupe caveats

- `scores.repos_summary` and `entities.repos` (both frozen) are already deduped by `LOWER(repo)`. No `ROW_NUMBER()` needed.
- `signal_goodailist.repo_catalog` is the GoodAI roster. It replaces the retired
  `catalog.goodailist_repos` static model; deduplicate by `LOWER(repo)` when querying it
  directly.
- Always `LOWER()` repo names when joining across sources.
- Bound exploratory queries with `LIMIT` and/or date windows.

## Gap semantics

- Coverage/ingestion gaps (missing orgs/repos) are tracked in GitHub issues.
- `scores.ossd_coverage` = per-org oss-directory match rates, frozen at its last publish.

## Pointers

- Inventory + schedules: [`warehouse/assets.yaml`](../../warehouse/assets.yaml) and [data architecture §11](../architecture/data-architecture.md)
- Coverage backlog: tracked in GitHub issues
