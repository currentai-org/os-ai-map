-- Model: scores.dependency_graph
-- Dataset: currentai.scores
-- Table: currentai.scores.dependency_graph
-- Kind: FULL (daily cron)
--
-- Transitive dependency graph between AI repos.
-- Direct + depth-2 edges with category metadata.

WITH goodai_deduped AS (
  SELECT
    LOWER(repo) AS repo,
    CAST(stars AS DOUBLE) AS stars,
    ROW_NUMBER() OVER (
      PARTITION BY LOWER(repo)
      ORDER BY updated_at DESC NULLS LAST
    ) AS _rn
  FROM currentai.signal_goodailist.repo_catalog
),
ai_repos AS (
  SELECT
    r.repo,
    r.category,
    g.stars
  FROM currentai.entities.repos r
  JOIN goodai_deduped g ON g.repo = r.repo AND g._rn = 1
),
ai_ns AS (SELECT DISTINCT SPLIT_PART(repo, '/', 1) AS ns FROM ai_repos),
direct AS (
  SELECT DISTINCT
    d.dependent_artifact_namespace || '/' || d.dependent_artifact_name AS src,
    d.package_owner_artifact_namespace || '/' || d.package_owner_artifact_name AS dst
  FROM oso.int_code_dependencies d
  -- The namespace semi-joins are load-bearing for memory, not just tidiness.
  --
  -- oso.int_code_dependencies is one row per (dependent repo, PACKAGE), so a single
  -- repo-to-repo edge repeats once per package the owner publishes: every edge into
  -- lodash/lodash appears hundreds of times. The DISTINCT below therefore aggregates
  -- an enormous input down to ~12k rows, and joining only on the concatenated
  -- `namespace || '/' || name` gives the connector nothing it can push down, so the
  -- whole table reaches the aggregation. That is a 14.5GB hash aggregation against a
  -- 15GB per-node limit -- it had been passing only by a margin, and growing the
  -- roster ~11% (retiring the frozen CSV for the live signal) pushed it over.
  --
  -- Filtering on the bare namespace first is selective enough for Trino to apply it
  -- as a dynamic filter at scan time, so the aggregation sees a fraction of the rows.
  -- Same output, 12,425 edges either way.
  INNER JOIN ai_ns n1 ON d.dependent_artifact_namespace = n1.ns
  INNER JOIN ai_ns n2 ON d.package_owner_artifact_namespace = n2.ns
  INNER JOIN ai_repos a1
    ON d.dependent_artifact_namespace || '/' || d.dependent_artifact_name = a1.repo
  INNER JOIN ai_repos a2
    ON d.package_owner_artifact_namespace || '/' || d.package_owner_artifact_name = a2.repo
  WHERE d.dependent_artifact_namespace || '/' || d.dependent_artifact_name
     != d.package_owner_artifact_namespace || '/' || d.package_owner_artifact_name
),
-- Depth-2 pairs are deduped once, by the GROUP BY below, rather than by a DISTINCT
-- here and again afterwards. This is a tidiness win and a modest memory saving, and
-- explicitly NOT what fixed the out-of-memory failure: merging these two
-- aggregations was tried on its own and the model still exceeded the 15GB limit.
-- The namespace pre-filter above is the load-bearing change. Do not remove it on the
-- assumption that this one covers it.
edges AS (
  SELECT src, dst, 1 AS depth FROM direct
  UNION ALL
  SELECT a.src, b.dst, 2 AS depth
  FROM direct a
  INNER JOIN direct b ON a.dst = b.src
  WHERE a.src != b.dst
),
deduped AS (
  SELECT src, dst, MIN(depth) AS min_depth
  FROM edges GROUP BY src, dst
)
SELECT
  e.src AS dependent_repo,
  a1.category AS dependent_category,
  e.dst AS dependency_repo,
  a2.category AS dependency_category,
  e.min_depth,
  a1.stars AS dependent_stars,
  a2.stars AS dependency_stars
FROM deduped e
INNER JOIN ai_repos a1 ON e.src = a1.repo
INNER JOIN ai_repos a2 ON e.dst = a2.repo
