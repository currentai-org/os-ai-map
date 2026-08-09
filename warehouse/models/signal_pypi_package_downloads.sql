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
--
-- The adoption bands are NOT defined here. They were, until 2026-08-09, as a
-- hardcoded CASE that applied one scale to every product type - which is the
-- repo/warehouse split check_parity exists to catch, one axis over, and it was
-- wrong for datasets: no dataset artifact in the corpus exceeds 10M monthly
-- downloads, so level 5 was unreachable for the whole type. They now come from
-- currentai.registry.adoption_bands, declared per product type in
-- sources/rubrics/<type>.yaml and pushed by CI.
--
-- A type with no bands declared gets a NULL level rather than another type's
-- scale. `hardware` is deliberately in that state - a board has no download
-- count - and the abstention is the same rule signal_routing.yaml states for
-- sources: abstain rather than substitute.
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
),
measured AS (
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
    w.package IS NULL AS missing_from_pypi
  FROM roster r
  CROSS JOIN bounds b
  LEFT JOIN windowed w
    ON LOWER(r.package) = LOWER(w.package)
),
-- The highest band whose exclusive lower bound the figure clears. A type absent
-- from the table contributes no row, so the LEFT JOIN leaves the level NULL.
banded AS (
  SELECT
    m.product_slug,
    m.package,
    MAX(b.level) AS adoption_level
  FROM measured m
  JOIN currentai.registry.adoption_bands b
    ON b.product_type = m.product_type
   AND m.downloads_30d > b.above
  WHERE m.downloads_30d IS NOT NULL
  GROUP BY m.product_slug, m.package
)
SELECT
  m.product_slug,
  m.product_type,
  m.package,
  m.downloads_30d,
  m.downloads_7d,
  m.days_observed,
  m.countries_seen,
  m.first_day_seen,
  m.last_day_seen,
  m.window_start,
  bd.adoption_level,
  m.missing_from_pypi
FROM measured m
LEFT JOIN banded bd
  ON bd.product_slug = m.product_slug
 AND bd.package = m.package
