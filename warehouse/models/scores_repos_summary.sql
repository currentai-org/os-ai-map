-- Model: scores.repos_summary
-- Dataset: currentai.scores
-- Table: currentai.scores.repos_summary
-- Kind: FULL (daily cron)
--
-- Per-repo snapshot: catalog metadata + aggregated metrics.
-- Replaces the old ai_repo_activity UDM as the single source
-- of truth for notebook repo-level queries. ~15K rows.

WITH goodai AS (
  SELECT
    LOWER(repo) AS repo,
    category,
    TRIM(SPLIT_PART(subcat, ',', 1)) AS subcategory,
    CAST(stars AS BIGINT) AS stars,
    CAST(star_7d AS BIGINT) AS star_7d,
    CAST(contributors AS BIGINT) AS contributors,
    language,
    country,
    description,
    ROW_NUMBER() OVER (
      PARTITION BY LOWER(repo)
      ORDER BY updated_at DESC NULLS LAST
    ) AS _rn
  FROM currentai.catalog.goodailist_repos
),
deduped AS (
  SELECT repo, category, subcategory, stars, star_7d, contributors,
         language, country, description
  FROM goodai WHERE _rn = 1
),
activity_90d AS (
  SELECT
    repo,
    SUM(CASE WHEN metric = 'stars' THEN value ELSE 0 END) AS stars_90d,
    SUM(CASE WHEN metric = 'forks' THEN value ELSE 0 END) AS forks_90d,
    SUM(CASE WHEN metric = 'commits' THEN value ELSE 0 END) AS commits_90d
  FROM currentai.metrics.daily
  WHERE day >= CURRENT_DATE - INTERVAL '90' DAY
    AND metric IN ('stars', 'forks', 'commits')
  GROUP BY repo
),
latest_contributors AS (
  SELECT
    repo,
    MAX(CASE WHEN metric = 'contributors' THEN CAST(value AS INTEGER) END) AS total_contributors,
    MAX(CASE WHEN metric = 'full_time' THEN CAST(value AS INTEGER) END) AS full_time,
    MAX(CASE WHEN metric = 'part_time' THEN CAST(value AS INTEGER) END) AS part_time
  FROM currentai.metrics.daily
  WHERE metric IN ('contributors', 'full_time', 'part_time')
    AND day = (SELECT MAX(day) FROM currentai.metrics.daily WHERE metric = 'contributors')
  GROUP BY repo
)
SELECT
  d.repo,
  d.category,
  d.subcategory,
  d.stars,
  d.star_7d,
  d.contributors,
  d.language,
  d.country,
  d.description,
  COALESCE(a.stars_90d, 0) AS stars_90d,
  COALESCE(a.forks_90d, 0) AS forks_90d,
  COALESCE(a.commits_90d, 0) AS commits_90d,
  COALESCE(lc.total_contributors, 0) AS total_contributors,
  COALESCE(lc.full_time, 0) AS full_time,
  COALESCE(lc.part_time, 0) AS part_time
FROM deduped d
LEFT JOIN activity_90d a ON d.repo = a.repo
LEFT JOIN latest_contributors lc ON d.repo = lc.repo
