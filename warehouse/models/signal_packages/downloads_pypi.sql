-- ────── PLATFORM MIRROR (read-only) ──────
-- A snapshot of a model that runs on the OSO platform to build one of the gap map's
-- tables. The platform is the source of truth; nothing deploys from this copy, and
-- editing it here changes nothing. See README.md and manifest.yaml in this folder.

-- currentai.signal_packages.downloads_pypi
-- The PyPI leg of currentai.signal_packages.downloads: windowed download volume for the pypi
-- artifacts the map declares. Grain: one row per (artifact_kind, package), where package is
-- the name exactly as oso.pypi_downloads.daily_downloads_by_package spells it.
--
-- Split out of downloads because that model read every package on PyPI at day grain and
-- aggregated all of them before joining to a roster of a few hundred, and on 2026-10-25 the
-- HashAggregationOperator hit the 15GB per-node limit. Here the source is restricted to the
-- roster's pypi packages BEFORE any per-package aggregation.
--
-- The roster filter is case-insensitive, matching downloads' LOWER(w.package) = LOWER(r.package)
-- join. It filters rows, it does not rename them: the group key stays the package as PyPI spells
-- it, so a name that appears in more than one case still yields one row per spelling, exactly as
-- before the split.
--
-- The anchor (last_day) is MAX(day) over the FULL PyPI table, not the filtered one: the window
-- is anchored on the registry's own latest day, never on the roster's. There is deliberately no
-- day filter on the history, because days_of_history and first_day_seen report the full history
-- the table retains.

WITH roster_packages AS (
  SELECT DISTINCT LOWER(artifact_id) AS package_key
  FROM currentai.registry.product_artifacts
  WHERE artifact_kind = 'pypi'
),

anchor AS (
  SELECT MAX(day) AS last_day
  FROM oso.pypi_downloads.daily_downloads_by_package
),

history AS (
  SELECT
    package,
    day,
    downloads,
    -- BIGINT, as the old union with the npm/crates leg's CAST(NULL AS BIGINT) made it.
    CAST(country_count AS BIGINT) AS country_count
  FROM oso.pypi_downloads.daily_downloads_by_package
  WHERE LOWER(package) IN (SELECT package_key FROM roster_packages)
)

SELECT
  CAST('pypi' AS VARCHAR) AS artifact_kind,
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
CROSS JOIN anchor a
GROUP BY h.package, a.last_day
