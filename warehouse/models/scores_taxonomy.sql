-- Model: scores.taxonomy
-- Dataset: currentai.scores
-- Table: currentai.scores.taxonomy
-- Kind: FULL (daily cron)
--
-- Maps projects into the OSAI editorial layer structure via
-- hand-curated bridge tables. A project can appear in multiple
-- subcategories. Falls back to category-level bridge when no
-- subcategory match exists.

WITH subcat_bridge AS (
  SELECT
    osai_layer,
    osai_subcategory,
    TRIM(goodai_sub) AS goodai_subcategory
  FROM currentai.catalog.osai_subcategory_mapping
  CROSS JOIN UNNEST(SPLIT(goodai_subcategories, ',')) AS t(goodai_sub)
),
cat_bridge AS (
  SELECT osai_layer, goodai_category
  FROM currentai.catalog.taxonomy_crosswalk
),
gap AS (
  SELECT
    layer, subcategory, subcategory_id,
    CAST(overall_score AS DOUBLE) AS gap_score,
    parity_verdict
  FROM currentai.catalog.osai_gap_map
  WHERE subcategory_id IS NOT NULL AND subcategory_id != ''
),
repo_subcats AS (
  SELECT DISTINCT
    COALESCE(r.project_slug, r.repo) AS project_slug,
    sb.osai_layer,
    sb.osai_subcategory,
    'subcategory_bridge' AS mapping_source
  FROM currentai.entities.repos r
  INNER JOIN subcat_bridge sb ON r.subcategory = sb.goodai_subcategory
),
repo_cats AS (
  SELECT DISTINCT
    COALESCE(r.project_slug, r.repo) AS project_slug,
    g.layer AS osai_layer,
    g.subcategory AS osai_subcategory,
    'category_bridge' AS mapping_source
  FROM currentai.entities.repos r
  INNER JOIN cat_bridge cb ON r.category = cb.goodai_category
  INNER JOIN gap g ON cb.osai_layer = g.layer
  WHERE NOT EXISTS (
    SELECT 1 FROM repo_subcats rs
    WHERE rs.project_slug = COALESCE(r.project_slug, r.repo)
  )
),
all_mappings AS (
  SELECT * FROM repo_subcats
  UNION ALL
  SELECT * FROM repo_cats
)
SELECT
  m.project_slug,
  m.osai_layer,
  m.osai_subcategory,
  g.subcategory_id AS osai_subcategory_id,
  g.gap_score,
  g.parity_verdict,
  m.mapping_source
FROM all_mappings m
INNER JOIN gap g
  ON m.osai_layer = g.layer
  AND m.osai_subcategory = g.subcategory
