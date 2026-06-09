-- Model: scores.investment_ranking
-- Dataset: currentai.scores
-- Table: currentai.scores.investment_ranking
-- Kind: FULL (daily cron)
--
-- Composite investment ranking per OSAI subcategory:
-- gap urgency x dependency centrality x fragility risk.

WITH gap AS (
  SELECT
    layer, subcategory, subcategory_id,
    CAST(overall_score AS DOUBLE) AS overall_score,
    maturity, parity_verdict
  FROM currentai.catalog.osai_gap_map
  WHERE subcategory_id IS NOT NULL AND subcategory_id != ''
),
subcat_map_raw AS (
  SELECT
    osai_layer, osai_subcategory,
    TRIM(goodai_sub) AS goodai_subcategory
  FROM currentai.catalog.osai_subcategory_mapping
  CROSS JOIN UNNEST(SPLIT(goodai_subcategories, ',')) AS t(goodai_sub)
),
repo_fragility AS (
  SELECT
    r.repo,
    r.subcategory AS goodai_subcategory,
    f.total_dependents,
    f.fragility_score
  FROM currentai.entities.repos r
  LEFT JOIN currentai.scores.fragility f ON r.repo = f.repo
  WHERE r.subcategory IS NOT NULL AND r.subcategory != ''
),
subcat_deps AS (
  SELECT
    sm.osai_layer,
    sm.osai_subcategory,
    MAX(rf.total_dependents) AS max_dependents,
    MAX(rf.fragility_score) AS max_fragility,
    MAX_BY(rf.repo, COALESCE(rf.total_dependents, 0)) AS top_repo,
    COUNT(DISTINCT rf.repo) AS repo_count
  FROM subcat_map_raw sm
  INNER JOIN repo_fragility rf ON sm.goodai_subcategory = rf.goodai_subcategory
  GROUP BY sm.osai_layer, sm.osai_subcategory
),
max_vals AS (
  SELECT
    MAX(max_dependents) AS global_max_deps,
    MAX(max_fragility) AS global_max_frag
  FROM subcat_deps
)
SELECT
  g.layer,
  g.subcategory,
  g.parity_verdict,
  ROUND((5.0 - g.overall_score) / 4.0 * 100, 1) AS gap_urgency,
  sd.top_repo,
  sd.repo_count,
  ROUND(COALESCE(CAST(sd.max_dependents AS DOUBLE), 0)
    / GREATEST(mv.global_max_deps, 1) * 100, 1) AS dep_centrality,
  sd.max_fragility,
  ROUND(COALESCE(sd.max_fragility, 0)
    / GREATEST(mv.global_max_frag, 1) * 100, 1) AS fragility_risk,
  ROUND(
    (
      (5.0 - g.overall_score) / 4.0 * 100
      + COALESCE(CAST(sd.max_dependents AS DOUBLE), 0) / GREATEST(mv.global_max_deps, 1) * 100
      + (5.0 - g.overall_score) / 4.0 * 100
      + COALESCE(sd.max_fragility, 0) / GREATEST(mv.global_max_frag, 1) * 100
    ) / 4.0,
    1
  ) AS composite_score
FROM gap g
LEFT JOIN subcat_deps sd
  ON g.layer = sd.osai_layer AND g.subcategory = sd.osai_subcategory
CROSS JOIN max_vals mv
ORDER BY composite_score DESC
