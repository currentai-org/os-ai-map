-- ────── PLATFORM MIRROR (read-only) ──────
-- A snapshot of a model that runs on the OSO platform to build one of the gap map's
-- tables. The platform is the source of truth; nothing deploys from this copy, and
-- editing it here changes nothing. See README.md and manifest.yaml in this folder.

-- currentai.signal_packages.downloads_registry
-- The npm and crates legs of currentai.signal_packages.downloads: windowed download volume from
-- currentai.signal_packages.downloads_daily, which fetches both registries for the declared
-- artifacts. Grain: one row per (artifact_kind, package).
--
-- Split out of downloads alongside downloads_pypi. This leg was never the memory problem (the
-- daily table holds only declared artifacts), but it lives in its own feeder so downloads is a
-- plain union of legs.
--
-- The window is anchored per artifact_kind on that kind's own MAX(day), never on a shared day:
-- the feeds do not run through the same day, and a shared anchor would silently drop days from
-- the slower leg. A failed fetch is a row with a null day in downloads_daily; it is excluded
-- here, and downloads reads it back from downloads_daily as http_status.

WITH history AS (
  SELECT
    artifact_kind,
    package,
    day,
    downloads,
    CAST(NULL AS BIGINT) AS country_count
  FROM currentai.signal_packages.downloads_daily
  WHERE day IS NOT NULL
    AND downloads IS NOT NULL
),

anchors AS (
  SELECT
    artifact_kind,
    MAX(day) AS last_day
  FROM history
  GROUP BY artifact_kind
)

SELECT
  h.artifact_kind,
  h.package,
  a.last_day,
  SUM(CASE WHEN h.day > a.last_day - INTERVAL '30' DAY THEN h.downloads ELSE 0 END) AS downloads_30d,
  SUM(CASE WHEN h.day > a.last_day - INTERVAL '7' DAY THEN h.downloads ELSE 0 END) AS downloads_7d,
  SUM(CASE
    WHEN h.day > a.last_day - INTERVAL '60' DAY AND h.day <= a.last_day - INTERVAL '30' DAY
    THEN h.downloads ELSE 0 END) AS downloads_prev_30d,
  COUNT(DISTINCT CASE WHEN h.day > a.last_day - INTERVAL '30' DAY THEN h.day END) AS days_observed,
  COUNT(DISTINCT h.day) AS days_of_history,
  MAX(h.country_count) AS max_country_count,
  MIN(h.day) AS first_day_seen,
  MAX(h.day) AS last_day_seen
FROM history h
JOIN anchors a ON a.artifact_kind = h.artifact_kind
GROUP BY h.artifact_kind, h.package, a.last_day
