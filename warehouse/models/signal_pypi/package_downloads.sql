-- ────── PLATFORM MIRROR (read-only) ──────
-- A snapshot of a model that runs on the OSO platform to build one of the gap map's
-- tables. The platform is the source of truth; nothing deploys from this copy, and
-- editing it here changes nothing. See README.md and manifest.yaml in this folder.

-- currentai.signal_pypi.package_downloads
-- Monthly PyPI download volume for the map's declared pypi artifacts.
--
-- Roster from currentai.registry.product_artifacts (the CI-pushed declaration),
-- joined to the oso.pypi_downloads marketplace dataset. SQL rather than Python:
-- there is no fetch and no secret here, so this needs neither the Python sandbox
-- nor the flaky UDM host.
--
-- Grain: one row per (product_slug, package).
--
-- Two honest limits, both inherited from the source and surfaced as columns
-- rather than buried:
--   * Counts are raw installer requests. They include CI jobs, mirrors and other
--     automated traffic, so they are volume, not unique users. `downloads_30d` is
--     the adoption input; it is not a user count.
--   * History is short. `days_observed` and `window_start` make the window
--     explicit so a partial window is visible instead of reading as a decline.
WITH bounds AS (
  SELECT MAX(day) AS last_day FROM oso.pypi_downloads.daily_downloads_by_package
),
roster AS (
  SELECT DISTINCT
    product_slug,
    product_type,
    artifact_id AS package
  FROM currentai.registry.product_artifacts
  WHERE artifact_kind = 'pypi'
),
windowed AS (
  SELECT
    d.package,
    SUM(CASE WHEN d.day > b.last_day - INTERVAL '30' DAY THEN d.downloads ELSE 0 END) AS downloads_30d,
    SUM(CASE WHEN d.day > b.last_day - INTERVAL '7' DAY THEN d.downloads ELSE 0 END) AS downloads_7d,
    COUNT(DISTINCT CASE WHEN d.day > b.last_day - INTERVAL '30' DAY THEN d.day END) AS days_observed,
    MAX(d.country_count) AS max_country_count,
    MIN(d.day) AS first_day_seen,
    MAX(d.day) AS last_day_seen
  FROM oso.pypi_downloads.daily_downloads_by_package d
  CROSS JOIN bounds b
  GROUP BY d.package
)
SELECT
  r.product_slug,
  r.product_type,
  r.package,
  w.downloads_30d,
  w.downloads_7d,
  w.days_observed,
  w.max_country_count AS countries_seen,
  w.first_day_seen,
  w.last_day_seen,
  CAST(b.last_day - INTERVAL '30' DAY AS DATE) AS window_start,
  -- Adoption band on the map's own scale, so the level is derived here rather
  -- than re-derived by every consumer. The level-5 floor is >10M monthly.
  CASE
    WHEN w.downloads_30d IS NULL THEN NULL
    WHEN w.downloads_30d > 10000000 THEN 5
    WHEN w.downloads_30d > 1000000 THEN 4
    WHEN w.downloads_30d > 100000 THEN 3
    WHEN w.downloads_30d > 10000 THEN 2
    ELSE 1
  END AS adoption_level,
  -- A roster package absent from PyPI entirely is a data-quality signal, not a zero.
  w.package IS NULL AS missing_from_pypi
FROM roster r
CROSS JOIN bounds b
LEFT JOIN windowed w
  ON LOWER(r.package) = LOWER(w.package)
