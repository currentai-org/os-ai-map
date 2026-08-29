-- Model: entities.models
-- Dataset: currentai.entities
-- Table: currentai.entities.models
-- Kind: FULL (daily cron)
--
-- HF models linked to repos and projects via catalog.model_repos,
-- enriched with benchmarks and foundation model family.

WITH model_repo_links AS (
  SELECT
    mr.model_id,
    'https://huggingface.co/' || mr.model_id AS url,
    mr.author,
    LOWER(mr.github_repo) AS repo,
    mr.base_model_id,
    mr.pipeline_tag,
    mr.library_name,
    CAST(mr.downloads AS BIGINT) AS downloads,
    CAST(mr.likes AS INTEGER) AS likes
  FROM currentai.catalog.model_repos mr
),
foundation AS (
  SELECT LOWER(github_repo) AS repo, model_family
  FROM currentai.catalog.foundation_model_repos
),
benchmarks AS (
  SELECT model_id, CAST(average AS DOUBLE) AS benchmark_avg, architecture
  FROM currentai.catalog.model_benchmarks
),
repo_projects AS (
  SELECT repo, COALESCE(project_slug, repo) AS project_slug
  FROM currentai.entities.repos
)
SELECT
  m.model_id,
  m.url,
  m.author,
  m.repo,
  rp.project_slug,
  m.base_model_id,
  m.pipeline_tag,
  m.library_name,
  m.downloads,
  m.likes,
  f.model_family,
  b.benchmark_avg,
  b.architecture
FROM model_repo_links m
LEFT JOIN repo_projects rp ON m.repo = rp.repo
LEFT JOIN foundation f ON m.repo = f.repo
LEFT JOIN benchmarks b ON m.model_id = b.model_id
