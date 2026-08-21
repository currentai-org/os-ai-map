-- ────── PLATFORM MIRROR (read-only) ──────
-- A snapshot of a model that runs on the OSO platform to build one of the gap map's
-- tables. The platform is the source of truth; nothing deploys from this copy, and
-- editing it here changes nothing. See README.md and manifest.yaml in this folder.

-- currentai.signal_huggingface.product_adoption
-- Adoption band per PRODUCT for the map's Hugging Face artifacts.
--
-- Separate from hub_state on purpose. hub_state is a fetcher: it holds a secret,
-- calls the Hub once per artifact, and its grain is the artifact. Banding is pure
-- derivation over it plus the registry, so keeping it here means a rubric change
-- re-bands without re-fetching 174 Hub endpoints, and the fetcher stays a fetcher.
--
-- Two things this exists to get right, neither of which hub_state can:
--
--   * GRAIN. `signal_routing.yaml` declares `sum_across_artifacts: true` for
--     adoption, because the map's unit is the family rather than a repo. 107
--     model artifacts belong to 55 products, so banding per artifact would score
--     nearly half of them on a single SKU.
--   * SCALE. The band comes from currentai.registry.adoption_bands keyed on the
--     product's declared TYPE, so a dataset is read on the dataset scale. That
--     matters: no dataset artifact in this corpus exceeds 10M monthly downloads,
--     so on the software/model scale level 5 is unreachable for the whole type.
--
-- Route order follows signal_routing.yaml: huggingface_model outranks
-- huggingface_dataset, and the first kind a product actually has wins. The sum is
-- taken WITHIN the winning kind rather than across both, so a product shipping
-- both a model and its training corpus is not credited with the corpus twice.
WITH typed AS (
  SELECT
    h.product_slug,
    p.type AS product_type,
    h.artifact_kind,
    h.downloads_30d
  FROM currentai.signal_huggingface.hub_state h
  JOIN currentai.registry.products p
    ON p.slug = h.product_slug
  -- A failed fetch is not a zero. Excluding it keeps a transient 429 from banding
  -- a product at 1 rather than leaving it unbanded.
  WHERE h.http_status = 200
    AND h.downloads_30d IS NOT NULL
),
per_kind AS (
  SELECT
    product_slug,
    product_type,
    artifact_kind,
    SUM(downloads_30d) AS downloads_30d_family,
    COUNT(*) AS artifacts_counted
  FROM typed
  GROUP BY product_slug, product_type, artifact_kind
),
routed AS (
  SELECT
    per_kind.*,
    ROW_NUMBER() OVER (
      PARTITION BY product_slug
      ORDER BY CASE artifact_kind WHEN 'huggingface_model' THEN 0 ELSE 1 END
    ) AS route_rank
  FROM per_kind
),
winning AS (
  SELECT * FROM routed WHERE route_rank = 1
),
-- The highest band whose exclusive lower bound the family total clears. A type with
-- no declared bands contributes no row, so the level stays NULL rather than
-- borrowing another type's scale. The floor band is -1, so a family total of zero
-- still bands at 1 rather than falling out entirely.
banded AS (
  SELECT
    w.product_slug,
    CAST(MAX(b.level) AS INTEGER) AS adoption_level
  FROM winning w
  JOIN currentai.registry.adoption_bands b
    ON b.product_type = w.product_type
   AND w.downloads_30d_family > b.above
  GROUP BY w.product_slug
)
SELECT
  w.product_slug,
  w.product_type,
  w.artifact_kind AS route,
  w.artifacts_counted,
  w.downloads_30d_family,
  bd.adoption_level
FROM winning w
LEFT JOIN banded bd
  ON bd.product_slug = w.product_slug
