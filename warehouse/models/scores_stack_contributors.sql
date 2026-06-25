-- currentai.scores.stack_contributors
-- Distinct GitHub code contributors to the curated AI Stack Map products, with the
-- stack-map taxonomy (category / layer / openness) bridged in via currentai.catalog.stack_map.
-- Grain: one row per (developer, repo). Window: trailing 365 days of COMMIT_CODE.
-- Bots are excluded. The repo->taxonomy bridge is regenerated from sources/ (the OSO
-- entities catalog does not carry stack-map categories).

WITH commits AS (
  SELECT
    e.from_artifact_id AS developer_id,
    e.from_artifact_name AS developer_login,
    LOWER(e.to_artifact_namespace || '/' || e.to_artifact_name) AS repo,
    COUNT(*) AS commits_12mo,
    MAX(e.time) AS last_commit
  FROM oso.int_events__github_unified e
  WHERE e.event_type = 'COMMIT_CODE'
    AND e.time >= CURRENT_DATE - INTERVAL '365' DAY
    AND LOWER(e.to_artifact_namespace || '/' || e.to_artifact_name) IN (SELECT repo FROM currentai.catalog.stack_map)
    AND e.from_artifact_name IS NOT NULL
    AND NOT (
      LOWER(e.from_artifact_name) LIKE '%[bot]%'
      OR LOWER(e.from_artifact_name) LIKE '%-bot'
      OR LOWER(e.from_artifact_name) LIKE 'bot-%'
      OR LOWER(e.from_artifact_name) IN ('github-actions','dependabot','renovate','renovate-bot','mergify','copybara')
    )
  GROUP BY 1, 2, 3
)
SELECT
  c.developer_id,
  c.developer_login,
  c.repo,
  m.product_slug,
  m.product_name,
  m.org,
  m.category,
  m.layer,
  m.openness_class,
  m.openness_bucket,
  c.commits_12mo,
  c.last_commit
FROM commits c
JOIN currentai.catalog.stack_map m ON c.repo = m.repo
