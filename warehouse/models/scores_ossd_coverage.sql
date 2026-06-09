-- Model: scores.ossd_coverage
-- Dataset: currentai.scores
-- Table: currentai.scores.ossd_coverage
-- Kind: FULL (daily cron)
--
-- Per-org oss-directory match rates.
-- Surfaces best candidates for adding to oss-directory.

WITH goodai_deduped AS (
  SELECT LOWER(repo) AS repo, CAST(stars AS BIGINT) AS stars,
    ROW_NUMBER() OVER (PARTITION BY LOWER(repo) ORDER BY updated_at DESC NULLS LAST) AS _rn
  FROM currentai.catalog.goodailist_repos
),
repo_orgs AS (
  SELECT
    SPLIT_PART(repo, '/', 1) AS org,
    repo,
    is_in_oss_directory,
    project_slug
  FROM currentai.entities.repos
),
org_stats AS (
  SELECT
    org,
    COUNT(*) AS total_repos,
    COUNT(CASE WHEN is_in_oss_directory THEN 1 END) AS matched_repos,
    COUNT(CASE WHEN NOT is_in_oss_directory THEN 1 END) AS unmatched_repos
  FROM repo_orgs
  GROUP BY org
),
unmatched_stars AS (
  SELECT
    SPLIT_PART(r.repo, '/', 1) AS org,
    SUM(g.stars) AS total_stars_unmatched,
    MAX_BY(r.repo, g.stars) AS top_unmatched_repo
  FROM currentai.entities.repos r
  JOIN goodai_deduped g ON g.repo = r.repo AND g._rn = 1
  WHERE NOT r.is_in_oss_directory
  GROUP BY SPLIT_PART(r.repo, '/', 1)
),
existing AS (
  SELECT DISTINCT
    SPLIT_PART(repo, '/', 1) AS org,
    project_slug AS existing_project
  FROM repo_orgs
  WHERE is_in_oss_directory
)
SELECT
  o.org,
  o.total_repos,
  o.matched_repos,
  o.unmatched_repos,
  COALESCE(us.total_stars_unmatched, 0) AS total_stars_unmatched,
  CASE WHEN o.matched_repos > 0 THEN 'partial_match' ELSE 'new_org' END AS opportunity_type,
  us.top_unmatched_repo,
  e.existing_project
FROM org_stats o
LEFT JOIN unmatched_stars us ON o.org = us.org
LEFT JOIN existing e ON o.org = e.org
WHERE o.unmatched_repos > 0
ORDER BY o.unmatched_repos DESC
