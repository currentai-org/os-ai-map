-- Model: metrics.daily
-- Dataset: currentai.metrics
-- Table: currentai.metrics.daily
-- Kind: FULL (daily cron)
--
-- Normalized daily activity metrics per repo, 12-month rolling window.
-- Long format: one row per repo × day × metric.
-- GitHub event metrics from events.github_events,
-- contributor metrics from OpenDevData.

WITH event_counts AS (
  SELECT
    repo,
    github_id,
    CAST(time AS DATE) AS day,
    event_type,
    COUNT(*) AS cnt
  FROM currentai.events.github_events
  GROUP BY repo, github_id, CAST(time AS DATE), event_type
),
contrib AS (
  SELECT
    r.repo,
    r.github_id,
    CAST(rda.day AS DATE) AS day,
    COUNT(DISTINCT rda.canonical_developer_id) AS contributors,
    COUNT(DISTINCT CASE WHEN rda.l28_days >= 10 THEN rda.canonical_developer_id END) AS full_time,
    COUNT(DISTINCT CASE WHEN rda.l28_days BETWEEN 1 AND 9 THEN rda.canonical_developer_id END) AS part_time
  FROM currentai.entities.repos r
  JOIN oso.int_opendevdata__repositories_with_repo_id rid
    ON LOWER(rid.repo_name) = r.repo
  JOIN oso.stg_opendevdata__repo_developer_28d_activities rda
    ON rda.repo_id = rid.opendevdata_id
  WHERE rda.day >= CURRENT_DATE - INTERVAL '365' DAY
  GROUP BY r.repo, r.github_id, CAST(rda.day AS DATE)
)
SELECT repo, github_id, day, 'stars' AS metric, CAST(cnt AS DOUBLE) AS value
FROM event_counts WHERE event_type = 'STARRED'
UNION ALL
SELECT repo, github_id, day, 'forks', CAST(cnt AS DOUBLE)
FROM event_counts WHERE event_type = 'FORKED'
UNION ALL
SELECT repo, github_id, day, 'commits', CAST(cnt AS DOUBLE)
FROM event_counts WHERE event_type = 'COMMIT_CODE'
UNION ALL
SELECT repo, github_id, day, 'pull_requests', CAST(cnt AS DOUBLE)
FROM event_counts WHERE event_type = 'PULL_REQUEST_OPENED'
UNION ALL
SELECT repo, github_id, day, 'issues_opened', CAST(cnt AS DOUBLE)
FROM event_counts WHERE event_type = 'ISSUE_OPENED'
UNION ALL
SELECT repo, github_id, day, 'contributors', CAST(contributors AS DOUBLE)
FROM contrib WHERE contributors > 0
UNION ALL
SELECT repo, github_id, day, 'full_time', CAST(full_time AS DOUBLE)
FROM contrib WHERE full_time > 0
UNION ALL
SELECT repo, github_id, day, 'part_time', CAST(part_time AS DOUBLE)
FROM contrib WHERE part_time > 0
