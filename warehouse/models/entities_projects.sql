-- Model: entities.projects
-- Dataset: currentai.entities
-- Table: currentai.entities.projects
-- Kind: FULL (daily cron)
--
-- Slim identity table. OSO projects where matched, standalone
-- repo-as-project otherwise. Categories, languages, collections
-- are many-to-many — derive via joins to entities.repos.

WITH goodai_deduped AS (
  SELECT
    LOWER(repo) AS repo,
    CAST(stars AS BIGINT) AS stars,
    country,
    ROW_NUMBER() OVER (
      PARTITION BY LOWER(repo)
      ORDER BY updated_at DESC NULLS LAST
    ) AS _rn
  FROM currentai.catalog.goodailist_repos
),
ossd_projects AS (
  SELECT
    r.project_slug,
    p.display_name,
    MIN(SPLIT_PART(r.repo, '/', 1)) AS org,
    MAX(r.description) AS description,
    COUNT(*) AS repo_count,
    SUM(g.stars) AS total_stars,
    'oss_directory' AS source
  FROM currentai.entities.repos r
  JOIN goodai_deduped g ON g.repo = r.repo AND g._rn = 1
  JOIN oso.oss_directory.projects p ON r.project_slug = p.project_name
  WHERE r.is_in_oss_directory
  GROUP BY r.project_slug, p.display_name
),
standalone AS (
  SELECT
    r.repo AS project_slug,
    SPLIT_PART(r.repo, '/', 2) AS display_name,
    SPLIT_PART(r.repo, '/', 1) AS org,
    r.description,
    1 AS repo_count,
    g.stars AS total_stars,
    'goodai_standalone' AS source
  FROM currentai.entities.repos r
  JOIN goodai_deduped g ON g.repo = r.repo AND g._rn = 1
  WHERE NOT r.is_in_oss_directory
),
all_projects AS (
  SELECT * FROM ossd_projects
  UNION ALL
  SELECT * FROM standalone
),
project_locations AS (
  SELECT
    COALESCE(r.project_slug, r.repo) AS project_slug,
    g.country AS location,
    ROW_NUMBER() OVER (
      PARTITION BY COALESCE(r.project_slug, r.repo)
      ORDER BY COUNT(*) DESC
    ) AS _rn
  FROM currentai.entities.repos r
  JOIN goodai_deduped g ON g.repo = r.repo AND g._rn = 1
  WHERE g.country IS NOT NULL AND g.country != ''
  GROUP BY COALESCE(r.project_slug, r.repo), g.country
)
SELECT
  p.project_slug,
  p.display_name,
  p.org,
  p.description,
  l.location,
  p.repo_count,
  p.total_stars,
  p.source
FROM all_projects p
LEFT JOIN project_locations l
  ON p.project_slug = l.project_slug AND l._rn = 1
