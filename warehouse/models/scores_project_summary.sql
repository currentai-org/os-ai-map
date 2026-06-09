-- Model: scores.project_summary
-- Dataset: currentai.scores
-- Table: currentai.scores.project_summary
-- Kind: FULL (daily cron)
--
-- Rolled-up snapshot per project for website cards.
-- Aggregates stars, contributors, packages, models,
-- dependents, fragility, benchmarks, and gap scores.

WITH proj AS (
  SELECT project_slug, display_name, repo_count
  FROM currentai.entities.projects
),
goodai_deduped AS (
  SELECT LOWER(repo) AS repo, CAST(stars AS BIGINT) AS stars,
    ROW_NUMBER() OVER (PARTITION BY LOWER(repo) ORDER BY updated_at DESC NULLS LAST) AS _rn
  FROM currentai.catalog.goodailist_repos
),
star_totals AS (
  SELECT
    COALESCE(r.project_slug, r.repo) AS project_slug,
    SUM(g.stars) AS total_stars
  FROM currentai.entities.repos r
  JOIN goodai_deduped g ON g.repo = r.repo AND g._rn = 1
  GROUP BY COALESCE(r.project_slug, r.repo)
),
recent_metrics AS (
  SELECT
    COALESCE(r.project_slug, r.repo) AS project_slug,
    SUM(CASE WHEN m.metric = 'stars' AND m.day >= CURRENT_DATE - INTERVAL '28' DAY THEN m.value ELSE 0 END) AS stars_28d,
    MAX(CASE WHEN m.metric = 'contributors' THEN m.value ELSE 0 END) AS contributors_28d,
    MAX(CASE WHEN m.metric = 'full_time' THEN m.value ELSE 0 END) AS full_time_28d
  FROM currentai.entities.repos r
  LEFT JOIN currentai.metrics.daily m ON r.repo = m.repo
  GROUP BY COALESCE(r.project_slug, r.repo)
),
pkg_counts AS (
  SELECT project_slug, COUNT(*) AS package_count
  FROM currentai.entities.packages
  WHERE project_slug IS NOT NULL
  GROUP BY project_slug
),
model_counts AS (
  SELECT project_slug, COUNT(*) AS model_count,
    MAX(benchmark_avg) AS best_benchmark_avg
  FROM currentai.entities.models
  WHERE project_slug IS NOT NULL
  GROUP BY project_slug
),
frag AS (
  SELECT
    COALESCE(r.project_slug, f.repo) AS project_slug,
    MAX(f.direct_dependents) AS direct_dependents,
    MAX(f.total_dependents) AS total_dependents,
    MAX(f.fragility_score) AS max_fragility_score
  FROM currentai.scores.fragility f
  JOIN currentai.entities.repos r ON f.repo = r.repo
  GROUP BY COALESCE(r.project_slug, f.repo)
),
tax AS (
  SELECT project_slug, MIN(gap_score) AS primary_gap_score
  FROM currentai.scores.taxonomy
  GROUP BY project_slug
),
inv AS (
  SELECT
    t.project_slug,
    MAX(ir.composite_score) AS investment_priority
  FROM currentai.scores.taxonomy t
  JOIN currentai.scores.investment_ranking ir
    ON t.osai_layer = ir.layer AND t.osai_subcategory = ir.subcategory
  GROUP BY t.project_slug
)
SELECT
  p.project_slug,
  p.display_name,
  COALESCE(st.total_stars, 0) AS total_stars,
  CAST(COALESCE(rm.stars_28d, 0) AS BIGINT) AS stars_28d,
  CAST(COALESCE(rm.contributors_28d, 0) AS INTEGER) AS contributors_28d,
  CAST(COALESCE(rm.full_time_28d, 0) AS INTEGER) AS full_time_28d,
  p.repo_count,
  COALESCE(pk.package_count, 0) AS package_count,
  COALESCE(mc.model_count, 0) AS model_count,
  COALESCE(fr.direct_dependents, 0) AS direct_dependents,
  COALESCE(fr.total_dependents, 0) AS total_dependents,
  COALESCE(fr.max_fragility_score, 0.0) AS max_fragility_score,
  mc.best_benchmark_avg,
  tx.primary_gap_score,
  inv.investment_priority
FROM proj p
LEFT JOIN star_totals st ON p.project_slug = st.project_slug
LEFT JOIN recent_metrics rm ON p.project_slug = rm.project_slug
LEFT JOIN pkg_counts pk ON p.project_slug = pk.project_slug
LEFT JOIN model_counts mc ON p.project_slug = mc.project_slug
LEFT JOIN frag fr ON p.project_slug = fr.project_slug
LEFT JOIN tax tx ON p.project_slug = tx.project_slug
LEFT JOIN inv ON p.project_slug = inv.project_slug
