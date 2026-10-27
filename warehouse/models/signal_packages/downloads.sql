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
-- declared artifacts" -- so a band on one artifact of a product that ships several is a band on
-- part of the product. The band moves one grain up, to
-- currentai.signal_packages.product_adoption.
--
-- Where each leg's history comes from:
--   * pypi   -- oso.pypi_downloads.daily_downloads_by_package, the marketplace dataset holding
--              every package on PyPI at day grain. Nothing to fetch. NOTE it retains only about
--              103 days (2026-06-01 to 2026-09-11 as measured 2026-09-13), so days_of_history is
--              far shorter on this leg than on npm's.
--   * npm    -- currentai.signal_packages.downloads_daily, which fetches 18 months of
--              daily history per package, because no global npm dataset exists.
--   * crates -- the same daily table. crates.io serves 90 days and will not page further back.
--
-- The windowing itself lives in two feeder models, which this model unions:
--   * currentai.signal_packages.downloads_pypi     -- the pypi leg, restricted to the roster's
--              pypi packages BEFORE aggregation. Windowing every package on PyPI and then joining
--              to the roster ran out of memory on 2026-10-25 (HashAggregationOperator at the
--              15GB per-node limit); that is why the legs are split.
--   * currentai.signal_packages.downloads_registry -- the npm and crates legs.
-- Each feeder emits its own anchor as last_day, so anchors below is derived from them.
--
-- The 30-day window is anchored per registry on that registry's own latest day, not on
-- CURRENT_DATE and not on the package's own latest day. Per registry, because the PyPI feed lags
-- npm by about a day (2026-09-11 against 2026-09-12 on 2026-09-13) and a shared anchor would
-- silently drop days from the slower leg. Never per package, because then an abandoned package
-- would anchor its window on its own last day of life and read as healthy.
--
-- Counts are raw installer requests everywhere: CI jobs, mirrors and container builds
-- included. Volume, not unique users.
--
-- latest_version / latest_upload_at (#709) come from currentai.signal_packages.package_metadata
-- and are filled for pypi rows only; npm and crates stay null until that model fetches them.
-- They are what build/check_channel_authority.py --warehouse reads for its version-lag leg.
-- Homebrew rows are deliberately NOT here even though package_metadata carries them: an install
-- is its own metric with its own bands, and this table is download volume.

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

-- Every windowed (kind, package) the three registries can offer, in one shape.
-- downloads_prev_30d is the 30 days before the current window. This is what tells a step change
-- that has held for months from a collapse that happened this week, which two point reads cannot:
-- it is the lmdeploy case in issue #163, where 165K -> 50K turned out to be one step in May.
windowed AS (
  SELECT
    artifact_kind,
    package,
    last_day,
    downloads_30d,
    downloads_7d,
    downloads_prev_30d,
    days_observed,
    days_of_history,
    max_country_count,
    first_day_seen,
    last_day_seen
  FROM currentai.signal_packages.downloads_pypi

  UNION ALL

  SELECT
    artifact_kind,
    package,
    last_day,
    downloads_30d,
    downloads_7d,
    downloads_prev_30d,
    days_observed,
    days_of_history,
    max_country_count,
    first_day_seen,
    last_day_seen
  FROM currentai.signal_packages.downloads_registry
),

-- One anchor per registry: every feeder row of a kind carries the same last_day.
anchors AS (
  SELECT
    artifact_kind,
    MAX(last_day) AS last_day
  FROM windowed
  GROUP BY artifact_kind
),

-- One row per (kind, package): package_metadata is at product grain, so a package two
-- products declare would otherwise double every row it joins.
metadata AS (
  SELECT
    artifact_kind,
    LOWER(package) AS package_key,
    MAX(latest_version) AS latest_version,
    MAX(latest_upload_at) AS latest_upload_at
  FROM currentai.signal_packages.package_metadata
  WHERE artifact_kind IN ('pypi', 'npm', 'crates')
  GROUP BY artifact_kind, LOWER(package)
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
  r.not_primary_channel,
  m.latest_version,
  m.latest_upload_at
FROM roster r
LEFT JOIN anchors a ON a.artifact_kind = r.artifact_kind
LEFT JOIN windowed w
  ON w.artifact_kind = r.artifact_kind
  AND LOWER(w.package) = LOWER(r.package)
LEFT JOIN fetch_status s
  ON s.artifact_kind = r.artifact_kind
  AND s.package = r.package
LEFT JOIN metadata m
  ON m.artifact_kind = r.artifact_kind
  AND m.package_key = LOWER(r.package)
