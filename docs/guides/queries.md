# CurrentAI Queries Guide

## Dataset layout

5 datasets, all using three-part names: `currentai.<dataset>.<table>`

| Dataset | Type | Key tables |
|---------|------|------------|
| `catalog` | Static CSV | `goodailist_repos`, `model_benchmarks`, `model_repos`, `osai_gap_map` |
| `entities` | UDM | `repos`, `projects`, `packages`, `models` |
| `events` | UDM | `github_events` |
| `metrics` | UDM | `daily` |
| `scores` | UDM | `repos_summary`, `taxonomy`, `dependency_graph`, `fragility`, `project_summary`, `ossd_coverage` |

`oso.*` tables are public and can be queried with any valid key.

## Starting points

**For notebook queries:** use `scores.repos_summary` (15K rows, pre-computed snapshot):
```sql
SELECT * FROM currentai.scores.repos_summary WHERE country = 'France' ORDER BY stars DESC
```

**For project-level data:** use `scores.project_summary`:
```sql
SELECT * FROM currentai.scores.project_summary ORDER BY total_stars DESC LIMIT 20
```

**For time-series:** use `metrics.daily` (long format):
```sql
SELECT day, value FROM currentai.metrics.daily
WHERE repo = 'pytorch/pytorch' AND metric = 'stars'
ORDER BY day
```

**For raw events:** use `events.github_events`:
```sql
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

```sql
-- Repo → project
SELECT r.repo, r.project_slug, p.display_name, p.location
FROM currentai.entities.repos r
LEFT JOIN currentai.entities.projects p ON r.project_slug = p.project_slug

-- Project → taxonomy (OSAI layers)
SELECT t.project_slug, t.osai_layer, t.osai_subcategory, t.gap_score
FROM currentai.scores.taxonomy t
WHERE t.project_slug = 'pytorch'

-- Project → packages
SELECT p.package_source, p.package_name, p.url
FROM currentai.entities.packages p
WHERE p.project_slug = 'pytorch'

-- Project → models
SELECT m.model_id, m.url, m.benchmark_avg
FROM currentai.entities.models m
WHERE m.project_slug = 'pytorch'

-- Monthly dev counts by category (from metrics.daily)
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

- `scores.repos_summary` and `entities.repos` are already deduped by `LOWER(repo)`. No `ROW_NUMBER()` needed.
- `catalog.goodailist_repos` can contain duplicates; deduplicate by `LOWER(repo)` when querying it directly.
- Always `LOWER()` repo names when joining across sources.
- Bound exploratory queries with `LIMIT` and/or date windows.

## Gap semantics

- [`docs/catalog-gaps.md`](../catalog-gaps.md) = coverage/ingestion backlog (missing orgs/repos).
- `scores.ossd_coverage` = per-org oss-directory match rates.
- `catalog.osai_gap_map` = maturity gap framework once data is present.

## Pointers

- Inventory + schedules: [`warehouse/models/README.md`](../../warehouse/models/README.md)
- Coverage backlog: [`docs/catalog-gaps.md`](../catalog-gaps.md)
- Compatibility router: [`docs/analysis-router.md`](../analysis-router.md)
