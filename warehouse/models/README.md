# Models

Data models deployed to the `currentai` org on the OSO data warehouse, organized into 5 datasets.

## Dataset Layout

```
catalog (STATIC_MODEL)     — CSV reference data, manually refreshed
entities (USER_MODEL)      — resolved identities: repos, projects, packages, models
events (USER_MODEL)        — pre-filtered event logs (GitHub Archive)
metrics (USER_MODEL)       — normalized daily activity per repo
scores (USER_MODEL)        — interpretive: taxonomy, dependencies, fragility, rankings
```

## Catalog (Static Model)

CSV-based reference data uploaded via scripts. Source CSVs live in `warehouse/catalog/`.

| Table | Source CSV | Records | Description |
|-------|-----------|---------|-------------|
| `currentai.catalog.goodailist_repos` | `warehouse/catalog/goodailist/repos.csv` | ~15K | Primary repo catalog with categories, stars, contributors |
| `currentai.catalog.model_benchmarks` | `warehouse/catalog/huggingface/model_benchmarks.csv` | ~4.5K | Open LLM Leaderboard v2 scores |
| `currentai.catalog.model_repos` | `warehouse/catalog/huggingface/model_repos.csv` | ~6.3K | HF model → GitHub repo links |
| `currentai.catalog.foundation_model_repos` | `warehouse/catalog/huggingface/foundation_model_repos.csv` | ~72 | Curated foundation model families → canonical repos |
| `currentai.catalog.pypi_downloads` | `warehouse/catalog/pypi/pypi_downloads.csv` (gitignored) | ~1.6M | PyPI daily downloads by package × country, 39 AI packages |

## Entities (User Defined Models)

Resolved identities and relationships. `entities.repos` is the foundation — everything chains off it.

| Table | SQL | Schedule | Rows | Description |
|-------|-----|----------|------|-------------|
| `currentai.entities.repos` | [entities_repos.sql](entities_repos.sql) | Daily 6am | ~15K | Deduped repo catalog + oss_directory IDs and project resolution |
| `currentai.entities.projects` | [entities_projects.sql](entities_projects.sql) | Daily 6am | ~14K | OSO projects where matched, standalone repos otherwise |
| `currentai.entities.packages` | [entities_packages.sql](entities_packages.sql) | Daily 6am | ~2.8K | Published packages linked to repos via `package_owners_v0` |
| `currentai.entities.models` | [entities_models.sql](entities_models.sql) | Daily 6am | ~6.4K | HF models with repo links, benchmarks, foundation model family |

## Events (User Defined Models)

Pre-filtered event logs scoped to our catalog repos.

| Table | SQL | Schedule | Rows | Description |
|-------|-----|----------|------|-------------|
| `currentai.events.github_events` | [events_github_events.sql](events_github_events.sql) | Daily 5am | ~24M | GitHub Archive events for catalog repos, 12-month rolling window |

## Metrics (User Defined Models)

Normalized time-series activity.

| Table | SQL | Schedule | Rows | Description |
|-------|-----|----------|------|-------------|
| `currentai.metrics.daily` | [metrics_daily.sql](metrics_daily.sql) | Daily 6am | ~5M | Long format: repo × day × metric → value (8 metric types) |

Metric types: `stars`, `forks`, `commits`, `pull_requests`, `issues_opened`, `contributors`, `full_time`, `part_time`

## Scores (User Defined Models)

Interpretive layer — taxonomy, dependencies, fragility, rankings, summaries.

The OSAI/Raffi v2 taxonomy layer (scores.taxonomy, scores.investment_ranking) was removed in favor of the sources/categories model.

| Table | SQL | Schedule | Rows | Description |
|-------|-----|----------|------|-------------|
| `currentai.scores.dependency_graph` | [scores_dependency_graph.sql](scores_dependency_graph.sql) | Daily 6am | ~26K | Transitive AI→AI deps (direct + depth-2) |
| `currentai.scores.fragility` | [scores_fragility.sql](scores_fragility.sql) | Daily 6am | ~600 | Dependency reach × maintainer capacity |
| `currentai.scores.project_summary` | [scores_project_summary.sql](scores_project_summary.sql) | Daily 7am | ~14K | Rolled-up snapshot per project |
| `currentai.scores.repos_summary` | [scores_repos_summary.sql](scores_repos_summary.sql) | Daily 7am | ~15K | Per-repo snapshot: catalog metadata + 90-day activity + contributors |
| `currentai.scores.ossd_coverage` | [scores_ossd_coverage.sql](scores_ossd_coverage.sql) | Daily 6am | ~10K | Per-org oss-directory match rates |

## Subscribed External Datasets

| Dataset | Tables | Source |
|---------|--------|--------|
| `oss_directory` | `oso.oss_directory.projects`, `.repositories`, `.collections`, `.artifacts_by_project`, `.projects_by_collection` | OSO public marketplace |

## Querying

All tables use three-part names: `currentai.<dataset>.<table>`

```sql
-- Entities
SELECT * FROM currentai.entities.repos LIMIT 10
SELECT * FROM currentai.entities.projects WHERE project_slug = 'pytorch'

-- Events
SELECT event_type, COUNT(*) FROM currentai.events.github_events WHERE repo = 'pytorch/pytorch' GROUP BY event_type

-- Metrics (long format)
SELECT metric, SUM(value) FROM currentai.metrics.daily WHERE repo = 'pytorch/pytorch' GROUP BY metric

-- Scores
SELECT * FROM currentai.scores.repos_summary WHERE country = 'France' ORDER BY stars DESC LIMIT 20
SELECT * FROM currentai.scores.project_summary ORDER BY total_stars DESC LIMIT 10
```

## Refreshing

```bash
# Refresh catalog CSVs:
uv run python warehouse/ingest/fetch_goodailist.py          # then upload via MCP
uv run python warehouse/ingest/fetch_model_benchmarks.py    # then upload via MCP

# UDMs refresh on their daily cron schedule, or trigger manually via MCP:
# createUserModelRunRequest with the dataset ID
```

## DAG

```
catalog (static CSVs)  +  oso.oss_directory.*
         ↓                        ↓
    entities (repos → projects, packages, models)
         ↓
    events (github_events ← oso.int_events__github_unified)
         ↓
    metrics (daily ← events.github_events + OpenDevData)
         ↓
    scores (dependency_graph, fragility, project_summary, repos_summary, ossd_coverage)
```
