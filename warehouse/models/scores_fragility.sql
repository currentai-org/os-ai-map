-- Model: scores.fragility
-- Dataset: currentai.scores
-- Table: currentai.scores.fragility
-- Kind: FULL (daily cron)
--
-- Dependency reach x maintainer capacity.
-- Uses latest contributor counts from metrics.daily,
-- falls back to GoodAI contributor count.

WITH goodai_deduped AS (
  SELECT
    LOWER(repo) AS repo,
    CAST(stars AS BIGINT) AS total_stars,
    CAST(contributors AS BIGINT) AS goodai_contributors,
    ROW_NUMBER() OVER (
      PARTITION BY LOWER(repo)
      ORDER BY updated_at DESC NULLS LAST
    ) AS _rn
  FROM currentai.catalog.goodailist_repos
),
latest_day AS (
  SELECT MAX(day) AS max_day
  FROM currentai.metrics.daily
  WHERE metric = 'contributors'
),
latest_contributors AS (
  SELECT repo, CAST(value AS INTEGER) AS contributors
  FROM currentai.metrics.daily, latest_day
  WHERE metric = 'contributors' AND day = max_day
),
latest_ft AS (
  SELECT repo, CAST(value AS INTEGER) AS full_time
  FROM currentai.metrics.daily, latest_day
  WHERE metric = 'full_time' AND day = max_day
),
latest_pt AS (
  SELECT repo, CAST(value AS INTEGER) AS part_time
  FROM currentai.metrics.daily, latest_day
  WHERE metric = 'part_time' AND day = max_day
),
dep_counts AS (
  SELECT
    dependency_repo AS repo,
    COUNT(*) AS total_dependents,
    COUNT(CASE WHEN min_depth = 1 THEN 1 END) AS direct_dependents,
    COUNT(CASE WHEN min_depth = 2 THEN 1 END) AS transitive_dependents
  FROM currentai.scores.dependency_graph
  GROUP BY dependency_repo
)
SELECT
  r.repo,
  r.category,
  g.total_stars,
  COALESCE(ft.full_time, 0) AS full_time,
  COALESCE(pt.part_time, 0) AS part_time,
  CAST(CASE
    WHEN COALESCE(lc.contributors, 0) > 0 THEN lc.contributors
    ELSE g.goodai_contributors
  END AS INTEGER) AS total_contributors,
  d.direct_dependents,
  d.transitive_dependents,
  d.total_dependents,
  ROUND(CAST(d.transitive_dependents AS DOUBLE) / d.total_dependents, 3) AS transitive_ratio,
  ROUND(
    CAST(d.total_dependents AS DOUBLE)
    / GREATEST(
        CAST(CASE
          WHEN COALESCE(lc.contributors, 0) > 0 THEN lc.contributors
          ELSE g.goodai_contributors
        END AS DOUBLE),
        1.0
      ),
    2
  ) AS fragility_score
FROM dep_counts d
INNER JOIN currentai.entities.repos r ON d.repo = r.repo
INNER JOIN goodai_deduped g ON r.repo = g.repo AND g._rn = 1
LEFT JOIN latest_contributors lc ON r.repo = lc.repo
LEFT JOIN latest_ft ft ON r.repo = ft.repo
LEFT JOIN latest_pt pt ON r.repo = pt.repo
ORDER BY d.total_dependents DESC
