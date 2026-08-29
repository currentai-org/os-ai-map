-- Daily-aggregated GitHub events for the Open Source AI Map roster.
--
-- SOURCE: oso.github_events.github_events_last_365_days, the PUBLISHED OSO
-- marketplace dataset. This model has no dependency on any internal oso
-- warehouse model (the int_/stg_/_v0 namespace).
--
-- GRAIN: DAILY AGGREGATED, not one row per event. Columns are
-- (github_id, repo, event_type, time, event_count) where `time` is midnight of
-- the day. Consumers must SUM(event_count), never COUNT(*). `time` is kept as a
-- TIMESTAMP so date_trunc() and range filters written against the old per-event
-- column keep working.
--
-- WINDOW: ROLLING 365 DAYS, and deliberately so as of 2026-08-16.
-- History before that window is NOT retained. The previous frozen snapshot
-- (events.github_events_history, covering 2024-06-01 .. 2025-08-01) was removed
-- to eliminate the last reference to oso.int_events__github_unified. Because the
-- marketplace feed only ever exposes the trailing 365 days, that older history
-- cannot be re-created from any available source. Anything needing a multi-year
-- roster series must use commit data (see currentai.metrics.daily 'commits', or
-- the opendevdata-backed series) rather than this table.
--
-- UPSTREAM DATA QUALITY (verified 2026-08-16): the marketplace feed carries the
-- same 2025-10-08 degradation as the internal model it replaced, because it is
-- derived from the same upstream and reproduces it to the row:
--   * PULL_REQUEST_MERGED is entirely absent for Nov 2025 and ~23% of expected
--     for Oct 2025.
--   * Ecosystem-wide PULL_REQUEST_OPENED decays ~141k/day (Aug 2025) ->
--     ~104k (Dec-Feb) -> ~50k (May 2026) -> ~15k (Jun) -> ~4k (Jul).
--   * COMMIT_CODE is unaffected and stable (~3.1M/day rising to ~3.9M/day).
-- Any PR- or issue-based trend crossing 2025-10-08 needs an ecosystem control.
WITH repo_ids AS (
  SELECT repo, github_id
  FROM currentai.entities.repos
)
SELECT
  r.github_id,
  r.repo,
  g.event_type,
  CAST(g.date AS TIMESTAMP) AS time,
  CAST(SUM(g.event_count) AS BIGINT) AS event_count
FROM repo_ids r
JOIN oso.github_events.github_events_last_365_days g
  ON LOWER(g.repo) = r.repo
GROUP BY r.github_id, r.repo, g.event_type, g.date
