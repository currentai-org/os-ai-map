-- ────── PLATFORM MIRROR (read-only) ──────
-- A snapshot of a model that runs on the OSO platform to build one of the gap map's
-- tables. The platform is the source of truth; nothing deploys from this copy, and
-- editing it here changes nothing. See README.md and manifest.yaml in this folder.

-- currentai.signal_github.product_adoption
-- Stars-derived adoption band per PRODUCT, for products with no better signal.
--
-- Separate from repo_state for the same reason product_adoption is separate from
-- hub_state: repo_state is a fetcher at repo grain holding a token, this is pure
-- derivation at product grain. A rubric change re-bands without re-fetching.
--
-- THIS IS THE LAST RESORT ROUTE. signal_routing.yaml orders adoption
-- huggingface_model -> huggingface_dataset -> pypi -> stars, first artifact the
-- product has wins, and stars are marked "last resort, and explicitly last"
-- because they measure attention rather than use. So a product already banded on
-- a download signal is excluded here rather than published twice with two
-- different levels.
--
-- The scale is the stars scale from registry.adoption_bands, filtered to
-- signal_type = 'stars_fallback'. It is declared once on the route in
-- signal_routing.yaml, is type-independent, and is CAPPED AT 3 - a star count can
-- never claim the top two levels however large. Joining this table without
-- filtering on signal_type would band stars against the download scale.
WITH already_measured AS (
  SELECT product_slug FROM currentai.signal_pypi.package_downloads
  WHERE adoption_level IS NOT NULL
  UNION
  SELECT product_slug FROM currentai.signal_huggingface.product_adoption
  WHERE adoption_level IS NOT NULL
),
stars AS (
  SELECT
    g.product_slug,
    p.type AS product_type,
    -- Summed across the product's repos, for the same reason downloads are summed
    -- across its artifacts: the map's unit is the product, not the repository.
    SUM(g.stargazers_count) AS stars,
    COUNT(*) AS repos_counted
  FROM currentai.signal_github.repo_state g
  JOIN currentai.registry.products p
    ON p.slug = g.product_slug
  -- A failed fetch is not zero stars.
  WHERE g.http_status = 200
    AND g.stargazers_count IS NOT NULL
    AND g.product_slug NOT IN (SELECT product_slug FROM already_measured)
  GROUP BY g.product_slug, p.type
),
banded AS (
  SELECT
    s.product_slug,
    CAST(MAX(b.level) AS INTEGER) AS adoption_level
  FROM stars s
  JOIN currentai.registry.adoption_bands b
    ON b.signal_type = 'stars_fallback'
   AND s.stars > b.above
  GROUP BY s.product_slug
)
SELECT
  s.product_slug,
  s.product_type,
  s.repos_counted,
  s.stars,
  bd.adoption_level
FROM stars s
LEFT JOIN banded bd
  ON bd.product_slug = s.product_slug
