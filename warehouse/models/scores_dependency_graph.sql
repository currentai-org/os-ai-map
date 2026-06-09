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
  FROM currentai.catalog.goodailist_repos
),
ai_repos AS (
  SELECT
    r.repo,
    r.category,
    g.stars
  FROM currentai.entities.repos r
  JOIN goodai_deduped g ON g.repo = r.repo AND g._rn = 1
),
direct AS (
  SELECT DISTINCT
    d.dependent_artifact_namespace || '/' || d.dependent_artifact_name AS src,
    d.package_owner_artifact_namespace || '/' || d.package_owner_artifact_name AS dst
  FROM oso.int_code_dependencies d
  INNER JOIN ai_repos a1
    ON d.dependent_artifact_namespace || '/' || d.dependent_artifact_name = a1.repo
  INNER JOIN ai_repos a2
    ON d.package_owner_artifact_namespace || '/' || d.package_owner_artifact_name = a2.repo
  WHERE d.dependent_artifact_namespace || '/' || d.dependent_artifact_name
     != d.package_owner_artifact_namespace || '/' || d.package_owner_artifact_name
),
depth2 AS (
  SELECT DISTINCT a.src, b.dst
  FROM direct a
  INNER JOIN direct b ON a.dst = b.src
  WHERE a.src != b.dst
),
combined AS (
  SELECT src, dst, 1 AS depth FROM direct
  UNION ALL
  SELECT src, dst, 2 AS depth FROM depth2
),
deduped AS (
  SELECT src, dst, MIN(depth) AS min_depth
  FROM combined GROUP BY src, dst
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
