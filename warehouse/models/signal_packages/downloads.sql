-- ────── PLATFORM MIRROR (read-only) ──────
-- A snapshot of a model that runs on the OSO platform to build one of the gap map's
-- tables. The platform is the source of truth; nothing deploys from this copy, and
-- editing it here changes nothing. See README.md and manifest.yaml in this folder.

-- currentai.signal_packages.downloads
-- Windowed download volume for every package artifact the map declares, across all three
-- registries. Grain: one row per (product_slug, artifact_kind, package).
--
-- Registry-neutral successor to currentai.signal_pypi.package_downloads. Same column names
-- wherever the meaning is the same, so a reader comparing the two does not have to translate,
-- with two differences that the neutrality forces:
--
--   * `artifact_kind` is new, carrying the registry's own vocabulary (pypi / npm / crates).
--     It is the discriminator sources/signal_routing.yaml filters each route on, exactly as
--     it already filters currentai.signal_huggingface.hub_state into its model and dataset
--     routes.
--   * `missing_from_pypi` becomes `missing_from_registry`, because in a neutral table the old
--     name would be false for two thirds of the rows. It means the same thing: the artifact
--     was looked for and not found, which is not the same as not looked for yet.
--
-- `adoption_level` is deliberately NOT here, and that is the substantive change rather than a
-- rename. signal_pypi banded per package, and the software / usage_volume unit in
-- sources/rubrics/software.yaml is "package downloads in the trailing 30 days, summed across
-- declared artifacts" — so a band on one artifact of a product that ships several is a band on
-- part of the product. The band moves one grain up, to
-- currentai.signal_packages.product_adoption.
--
-- Where each leg's history comes from:
--   * pypi   — oso.pypi_downloads.daily_downloads_by_package, the marketplace dataset holding
--              every package on PyPI at day grain. Nothing to fetch.
--   * npm    — currentai.signal_packages.downloads_daily, which fetches 18 months of
--              daily history per package, because no global npm dataset exists.
--   * crates — the same daily table. crates.io serves 90 days and will not page further back.
--
-- The 30-day window is anchored per registry on that registry's own latest day, not on
-- CURRENT_DATE and not on the package's own latest day. Per registry, because PyPI's feed lags
-- about six days behind npm's and a shared anchor would silently drop days from the slower
-- leg. Never per package, because then an abandoned package would anchor its window on its own
-- last day of life and read as healthy.
--
-- Counts are raw installer requests everywhere: CI jobs, mirrors and container builds
-- included. Volume, not unique users.

WITH roster AS (
  SELECT DISTINCT
    product_slug,
    product_type,
    artifact_kind,
    artifact_id AS package,
    -- Why this artifact is not how the product ships, declared per artifact in
    -- sources/products/*.yaml. Kept as the reason rather than reduced to a flag, because the
    -- reason is what makes the exclusion reviewable. The download figure is still computed and
    -- still published here; product_adoption is what leaves it out of the banded sum.
    NULLIF(not_primary_channel, '') AS not_primary_channel
  FROM currentai.registry.product_artifacts
  WHERE artifact_kind IN ('pypi', 'npm', 'crates')
),

-- Every day of history the three registries can offer, in one shape.
history AS (
  SELECT
    'pypi' AS artifact_kind,
    package,
    day,
    downloads,
    country_count
  FROM oso.pypi_downloads.daily_downloads_by_package

  UNION ALL

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
),

windowed AS (
  SELECT
    h.artifact_kind,
    h.package,
    SUM(CASE WHEN h.day > a.last_day - INTERVAL '30' DAY THEN h.downloads ELSE 0 END) AS downloads_30d,
    SUM(CASE WHEN h.day > a.last_day - INTERVAL '7' DAY THEN h.downloads ELSE 0 END) AS downloads_7d,
    -- The 30 days before the current window. This is what tells a step change that has held
    -- for months from a collapse that happened this week, which two point reads cannot: it is
    -- the lmdeploy case in issue #163, where 165K -> 50K turned out to be one step in May.
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
  GROUP BY h.artifact_kind, h.package
),

-- What the fetch itself reported, per artifact. A 404 is a row in the daily table carrying a
-- null day, so it survives to here and becomes missing_from_registry below.
fetch_status AS (
  SELECT
    artifact_kind,
    package,
    MAX(http_status) AS http_status
  FROM currentai.signal_packages.downloads_daily
  GROUP BY artifact_kind, package
)

SELECT
  r.product_slug,
  r.product_type,
  r.artifact_kind,
  r.package,
  w.downloads_30d,
  w.downloads_7d,
  w.downloads_prev_30d,
  w.days_observed,
  w.days_of_history,
  w.max_country_count AS countries_seen,
  w.first_day_seen,
  w.last_day_seen,
  CAST(a.last_day - INTERVAL '30' DAY AS DATE) AS window_start,
  -- Looked for and not found. A declared artifact the fetch has not reached yet has no status
  -- and no window either, so it reads as unmeasured rather than as gone.
  w.package IS NULL AND (r.artifact_kind = 'pypi' OR s.http_status IS NOT NULL) AS missing_from_registry,
  s.http_status,
  r.not_primary_channel
FROM roster r
LEFT JOIN anchors a ON a.artifact_kind = r.artifact_kind
LEFT JOIN windowed w
  ON w.artifact_kind = r.artifact_kind
  AND LOWER(w.package) = LOWER(r.package)
LEFT JOIN fetch_status s
  ON s.artifact_kind = r.artifact_kind
  AND s.package = r.package
