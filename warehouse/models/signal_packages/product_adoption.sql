-- ────── PLATFORM MIRROR (read-only) ──────
-- A snapshot of a model that runs on the OSO platform to build one of the gap map's
-- tables. The platform is the source of truth; nothing deploys from this copy, and
-- editing it here changes nothing. See README.md and manifest.yaml in this folder.

-- currentai.signal_packages.product_adoption
-- One usage_volume band per product, summed across every package registry it ships through.
-- Grain: one row per product declaring at least one package artifact.
--
-- The unit forces the summation. sources/rubrics/software.yaml declares the software /
-- usage_volume unit as "package downloads in the trailing 30 days, summed across declared
-- artifacts", and npm, PyPI and crates.io all publish that same quantity on that same window.
-- So a product's band is one number over all of its package artifacts. `beeai` is the live
-- case: it declares an npm package and a PyPI package, and a per-registry band would give one
-- product two levels over two partial figures with nothing to say which one the map means.
--
-- `artifact_kind` cannot be a column here, for the same reason: one row may be built from two
-- registries. What replaces it is `kinds_counted`, a comma-joined list of the kinds that
-- actually contributed, so a level 5 built from npm plus PyPI is distinguishable from one built
-- on PyPI alone without re-deriving it. Comma-joined rather than an array because every other
-- multi-value column this repo publishes is (signal_github.repo_state.topics), and a VARCHAR
-- survives a CSV round trip into a notebook unchanged.
--
-- Scope: the PACKAGE channel of usage_volume only. currentai.signal_huggingface.product_adoption
-- bands Hub downloads and currentai.signal_github.product_adoption bands stars. Unifying all
-- three into a single adoption authority is issue #169's question, not this model's.
--
-- Two rules it exists to enforce:
--
--   * The thresholds are READ, never written here. They are declared per product type in
--     sources/rubrics/<type>.yaml, published to currentai.registry.adoption_bands, and joined
--     below on (product_type, signal_type). Issue #173 records what the alternative cost:
--     signal_pypi carried them as a hardcoded CASE applying the software scale to every type,
--     under which level 5 is unreachable for a dataset entirely, and nothing in the repo could
--     see it. A type with no declared band gets adoption_level NULL rather than another type's
--     scale, which is what hardware's empty band list is for.
--     The join also filters signal_type, which signal_pypi's does not: adoption_bands holds
--     three instruments' scales and only usage_volume belongs to a download count.
--   * Partial coverage abstains. If a declared package artifact produced no figure -- it 404s,
--     or the fetch has not reached it yet -- the sum is short by an unknown amount, so the band
--     is NULL and abstain_reason says which. A sum over some of a product's channels is the
--     under-coverage error in docs/guides/adoption.md, and it is worse than no number because
--     it carries a level.
--   * A non-primary artifact is excluded from the sum, never from the table. Where a declared
--     package is not how the product ships, sources/products/*.yaml says so per artifact with
--     `not_primary_channel` and a reason, and this model leaves it out of the figure it bands.
--     `hexabot`'s npm entry is an embeddable widget rather than the self-hosted platform, and
--     `yomo`'s crate is a Rust SDK for a Go binary; both products then have no primary package
--     channel at all and fall through to the stars instrument legitimately, rather than being
--     held at a hand-set level nothing could check. Their downloads are still computed and
--     still visible in signal_packages.downloads. This is the mechanism behind the
--     minority-channel ruling that also covers gvisor, ollama, promptfoo and opencompass.
--
-- A computed band is an observation, never a score. Nothing here writes back into sources/.

WITH measured AS (
  SELECT
    product_slug,
    product_type,
    artifact_kind,
    package,
    downloads_30d,
    downloads_prev_30d,
    days_observed,
    window_start,
    last_day_seen,
    missing_from_registry,
    not_primary_channel,
    -- An artifact is eligible for the summed figure only if it is how the product ships. The
    -- artifact stays declared and its downloads stay published per artifact; this is the one
    -- place the exclusion applies.
    not_primary_channel IS NULL AS is_primary
  FROM currentai.signal_packages.downloads
),

rolled AS (
  SELECT
    product_slug,
    product_type,
    COUNT(*) AS artifacts_declared,
    COUNT_IF(is_primary) AS artifacts_primary,
    COUNT_IF(NOT is_primary) AS artifacts_excluded,
    COUNT(CASE WHEN is_primary THEN downloads_30d END) AS artifacts_counted,
    COUNT_IF(is_primary AND missing_from_registry) AS artifacts_missing,
    ARRAY_JOIN(
      ARRAY_AGG(DISTINCT CASE WHEN is_primary AND downloads_30d IS NOT NULL THEN artifact_kind END
                ORDER BY CASE WHEN is_primary AND downloads_30d IS NOT NULL THEN artifact_kind END),
      ','
    ) AS kinds_counted,
    ARRAY_JOIN(
      ARRAY_AGG(DISTINCT CASE WHEN NOT is_primary THEN artifact_kind END
                ORDER BY CASE WHEN NOT is_primary THEN artifact_kind END),
      ','
    ) AS kinds_excluded,
    SUM(CASE WHEN is_primary THEN downloads_30d END) AS downloads_30d,
    SUM(CASE WHEN is_primary THEN downloads_prev_30d END) AS downloads_prev_30d,
    MIN(CASE WHEN is_primary THEN days_observed END) AS days_observed,
    -- The oldest window bounds what the sum is a sum of. Taking the newest would date the
    -- claim later than the data supports, and the legs are anchored per registry.
    MIN(CASE WHEN is_primary THEN window_start END) AS window_start,
    MIN(CASE WHEN is_primary THEN last_day_seen END) AS last_day_seen
  FROM measured
  GROUP BY product_slug, product_type
),

complete AS (
  SELECT
    product_slug,
    product_type,
    artifacts_declared,
    artifacts_primary,
    artifacts_excluded,
    artifacts_counted,
    artifacts_missing,
    kinds_counted,
    kinds_excluded,
    downloads_30d,
    downloads_prev_30d,
    days_observed,
    window_start,
    last_day_seen,
    -- Completeness is measured against the PRIMARY artifacts, not against everything declared.
    -- A product whose only package artifact is a non-primary channel has zero countable
    -- artifacts, which is a different state from having one that 404s and from having one
    -- nothing has fetched yet; all three are false here and abstain_reason below says which.
    artifacts_counted = artifacts_primary AND artifacts_primary > 0 AS is_complete
  FROM rolled
),

-- Every band the summed figure clears, then the highest of them. The completeness test rides on
-- the join, so an incomplete product matches no band rather than banding on a short sum.
banded AS (
  SELECT
    c.product_slug,
    CAST(MAX(b.level) AS INTEGER) AS adoption_level,
    MAX_BY(b.reach, b.level) AS reach,
    MAX_BY(b.unit, b.level) AS unit
  FROM complete c
  JOIN currentai.registry.adoption_bands b
    ON b.product_type = c.product_type
    AND b.signal_type = 'usage_volume'
    AND c.downloads_30d > b.above
  WHERE c.is_complete
  GROUP BY c.product_slug
)

SELECT
  c.product_slug,
  c.product_type,
  c.kinds_counted,
  c.kinds_excluded,
  c.artifacts_declared,
  c.artifacts_primary,
  c.artifacts_excluded,
  c.artifacts_counted,
  c.artifacts_missing,
  CASE WHEN c.is_complete THEN c.downloads_30d END AS downloads_30d,
  CASE WHEN c.is_complete THEN c.downloads_prev_30d END AS downloads_prev_30d,
  c.days_observed,
  c.window_start,
  c.last_day_seen,
  b.adoption_level,
  b.reach,
  b.unit,
  c.is_complete,
  -- Ordered most specific first, and the first two arms are the distinction that matters: an
  -- artifact excluded as a minority channel is a curator's declared judgment, an artifact that
  -- 404s is a broken declaration, and reading either as the other loses the finding.
  CASE
    WHEN c.artifacts_primary = 0
      THEN 'no primary package channel: all ' || CAST(c.artifacts_excluded AS VARCHAR)
        || ' declared package artifacts (' || c.kinds_excluded
        || ') are marked not_primary_channel, so the product ships another way'
    WHEN c.artifacts_counted = 0 AND c.artifacts_missing > 0
      THEN 'every primary package artifact was looked for and not found'
    WHEN c.artifacts_counted = 0
      THEN 'no signal row yet for any primary package artifact'
    WHEN NOT c.is_complete
      THEN 'partial coverage: ' || CAST(c.artifacts_counted AS VARCHAR) || ' of '
        || CAST(c.artifacts_primary AS VARCHAR) || ' primary package artifacts counted'
    WHEN b.adoption_level IS NULL
      THEN 'no usage_volume band declared for product type ' || c.product_type
  END AS abstain_reason,
  CURRENT_TIMESTAMP AS computed_at
FROM complete c
LEFT JOIN banded b ON b.product_slug = c.product_slug
