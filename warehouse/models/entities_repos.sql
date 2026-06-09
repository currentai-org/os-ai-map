-- Model: entities.repos
-- Dataset: currentai.entities
-- Table: currentai.entities.repos
-- Kind: FULL (daily cron)
--
-- Foundation table: deduped GoodAI repo catalog enriched with
-- oss_directory stable IDs and project resolution.
-- Every downstream model chains off this.

WITH goodai AS (
  SELECT
    LOWER(repo) AS repo,
    category,
    TRIM(SPLIT_PART(subcat, ',', 1)) AS subcategory,
    language,
    country,
    description,
    CAST(created_at AS DATE) AS created_at,
    ROW_NUMBER() OVER (
      PARTITION BY LOWER(repo)
      ORDER BY updated_at DESC NULLS LAST
    ) AS _rn
  FROM currentai.catalog.goodailist_repos
),
deduped AS (
  SELECT repo, category, subcategory, language, country,
         description, created_at
  FROM goodai WHERE _rn = 1
),
ossd_match AS (
  SELECT
    LOWER(a.artifact_namespace || '/' || a.artifact_name) AS repo,
    a.project_name AS project_slug
  FROM oso.oss_directory.artifacts_by_project a
  WHERE a.artifact_source = 'GITHUB'
),
ossd_repos AS (
  SELECT
    LOWER(name_with_owner) AS repo,
    CAST(id AS BIGINT) AS github_id,
    node_id,
    license_spdx_id AS license
  FROM oso.oss_directory.repositories
)
SELECT
  d.repo,
  'https://github.com/' || d.repo AS url,
  r.github_id,
  r.node_id,
  m.project_slug,
  d.category,
  d.subcategory,
  d.language,
  d.country,
  d.description,
  COALESCE(r.license, '') AS license,
  d.created_at,
  m.project_slug IS NOT NULL AS is_in_oss_directory
FROM deduped d
LEFT JOIN ossd_match m ON d.repo = m.repo
LEFT JOIN ossd_repos r ON d.repo = r.repo
