-- Model: events.github_events
-- Dataset: currentai.events
-- Table: currentai.events.github_events
-- Kind: FULL (daily cron)
--
-- Pre-filtered GitHub Archive events for repos in our catalog.
-- Name-based join (Trino can't hash-join on source_id within 15GB).
-- Outputs current repo name from entities.repos.
-- 12-month rolling window.
--
-- Known limitation: events under a pre-rename repo name won't match.
-- Improves as oss_directory coverage grows (entities.repos tracks
-- current names; renamed repos get re-resolved on next catalog refresh).

WITH repo_ids AS (
  SELECT
    repo,
    github_id,
    LOWER(SPLIT_PART(repo, '/', 1)) AS owner,
    LOWER(SPLIT_PART(repo, '/', 2)) AS name
  FROM currentai.entities.repos
)
SELECT
  r.github_id,
  r.repo,
  ev.event_type,
  ev.time
FROM repo_ids r
JOIN oso.int_events__github_unified ev
  ON LOWER(ev.to_artifact_namespace) = r.owner
  AND LOWER(ev.to_artifact_name) = r.name
WHERE ev.time >= CURRENT_DATE - INTERVAL '365' DAY
