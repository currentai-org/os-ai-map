-- currentai.metrics.daily
-- Normalized daily activity metrics per repo. Long format: repo x day x metric -> value.
--
-- SOURCES (changed 2026-08-16):
--   * Event metrics (stars/forks/commits/pull_requests/issues_opened) come from
--     currentai.events.github_events, which is now DAILY AGGREGATED. We therefore
--     SUM(event_count) rather than COUNT(*).
--   * Contributor bands (contributors/full_time/part_time) are now derived from
--     oso.github_events.github_events_last_365_days, the published marketplace
--     feed, replacing the internal oso warehouse pair
--     oso.int_opendevdata__repositories_with_repo_id +
--     oso.stg_opendevdata__repo_developer_28d_activities.
--
-- CONTRIBUTOR DEFINITION: for each (repo, day), a developer counts if they had a
-- COMMIT_CODE event on that repo in the trailing 28 days ending that day.
-- full_time = active on >= 10 distinct days in that window, part_time = 1..9.
-- This reproduces the old l28_days banding, but the identity is the GitHub actor
-- (username) rather than opendevdata's resolved developer, which attributes the
-- same commits to fewer distinct people. Measured on 2026-01-15 the bands move
-- contributors 39,792 -> 34,518, full_time 7,938 -> 6,075, part_time 31,854 ->
-- 28,443. Counts from 2026-08-16 onward are on this new basis and are NOT
-- directly comparable with values computed before that date.
--
-- COVERAGE: contributor bands remain a trailing 365-day window, exactly as the
-- previous opendevdata version was. Event metrics still start 2024-06-01 via the
-- frozen history snapshot unioned into events.github_events. COMMIT_CODE in the
-- marketplace feed is verified stable across the 2025-10-08 upstream break
-- (~3.1M/day rising to ~3.9M/day), unlike the PR/issue/star types.
WITH event_counts AS (
  SELECT
    repo,
    github_id,
    CAST(time AS DATE) AS day,
    event_type,
    SUM(event_count) AS cnt
  FROM currentai.events.github_events
  GROUP BY repo, github_id, CAST(time AS DATE), event_type
),
roster AS (
  SELECT repo, github_id FROM currentai.entities.repos
),
activity AS (
  SELECT
    r.repo,
    r.github_id,
    g.username,
    g.date
  FROM roster r
  JOIN oso.github_events.github_events_last_365_days g
    ON LOWER(g.repo) = r.repo
  WHERE g.event_type = 'COMMIT_CODE'
    AND g.username IS NOT NULL
),
calendar AS (
  SELECT DISTINCT date AS day FROM oso.github_events.github_events_last_365_days
),
dev_window AS (
  SELECT
    a.repo,
    a.github_id,
    c.day,
    a.username,
    COUNT(DISTINCT a.date) AS l28_days
  FROM activity a
  JOIN calendar c
    ON a.date <= c.day
   AND a.date > c.day - INTERVAL '28' DAY
  GROUP BY a.repo, a.github_id, c.day, a.username
),
contrib AS (
  SELECT
    repo,
    github_id,
    day,
    COUNT(*) AS contributors,
    COUNT(CASE WHEN l28_days >= 10 THEN 1 END) AS full_time,
    COUNT(CASE WHEN l28_days BETWEEN 1 AND 9 THEN 1 END) AS part_time
  FROM dev_window
  GROUP BY repo, github_id, day
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
