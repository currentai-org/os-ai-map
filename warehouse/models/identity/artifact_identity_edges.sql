-- ────── PLATFORM MIRROR (read-only) ──────
-- A snapshot of a model that runs on the OSO platform to build one of the gap map's
-- tables. The platform is the source of truth; nothing deploys from this copy, and
-- editing it here changes nothing. See README.md and manifest.yaml in this folder.

-- currentai.identity.artifact_identity_edges
--
-- Grain: one row per (artifact_kind, artifact_id_a, artifact_id_b), with artifact_id_a <
-- artifact_id_b (raw string order on the DECLARED spelling, not the folded artifact_key --
-- see build/identity.py's docstring on why declared spelling is kept). An edge says "these two
-- declared spellings name the same underlying artifact"; it is deliberately NOT the same
-- question identity_equivalence_edges answers ("this artifact belongs to this product").
--
-- candidate_tier: the LOWER-ranked (worse) tier of the two spellings, rank head=1 < tail=2 <
-- pool=3 -- pool if either side is pool, else tail if either is tail, else head. Looked up by
-- finding each spelling's own node in currentai.identity.artifact_nodes (CONTAINS(also_seen_as,
-- spelling)), not the pair's shared node -- for a fold_pairs row both spellings share one node
-- (so this is trivially that node's best_tier), but a gh_redirects row can pair spellings from
-- TWO different nodes (repo and resolved_repo can fold to different artifact_keys). A spelling
-- with no matching node at all (confirmed live: a redirect's resolved_repo can be untracked --
-- not declared, not in the pool feed) defaults to 'pool', the lowest-priority tier, since an
-- untracked spelling carries no stronger claim than the pool.
--
-- Confidence: GREATEST(evidence...) - SUM(penalties), clamped with
-- GREATEST(0, LEAST(1, ...)); `penalties` is ARRAY(VARCHAR) (a penalty reason per applied
-- penalty, matching the eval's contract on all four edge tables); no penalty source is defined
-- for this model today so it is always the empty array, kept as a column so a future penalty
-- source needs no schema change.
--
-- Evidence sources:
--   1.0  fold-collapse (non-homepage kinds) -- two distinct declared spellings that fold to the
--        same artifact_key in currentai.identity.artifact_nodes.also_seen_as (structural:
--        casing/punctuation only, never a different underlying repo).
--   0.5  fold-collapse between two homepage spellings (capped) -- for artifact_kind = 'homepage',
--        artifact_key is the full canonical URL lowercased (host lowercased, `www.` stripped,
--        path kept, no trailing slash -- see identity_artifact_nodes.sql's header, corrected
--        2026-09-04; it used to fold to the bare host). Two spellings that fold together are
--        therefore the same URL up to case, not merely the same domain, and two products at
--        `acme.com/a` and `acme.com/b` now correctly never pair here at all. Per reviewer
--        ruling a homepage pair stays weak corroborating evidence: capped at 0.5, method
--        'homepage_domain' (never 'fold_collapse'), so it can never alone cross the 0.99/1.0
--        thresholds or suppress a second candidate. It has no other evidence source to combine
--        with in THIS table (github_redirect only ever applies to artifact_kind = 'github'), so
--        the "+0.1 on top of other evidence, clamped to 1" stacking rule never triggers here in
--        practice; it is documented for readers who add a second homepage-kind evidence source
--        later.
--   0.9  GitHub redirect -- currentai.signal_github.artifact_state (a dependency contract) marks
--        resolved_via_redirect = TRUE with a resolved_repo distinct from the declared repo. Below
--        1.0 because it is inferred from an HTTP redirect, not a human ruling in the resolution
--        ledger (that ruling, when it exists, lands in identity_equivalence_edges instead, since
--        it is a product-equivalence verdict, not an artifact-pair fact).
--
-- registry.product_aliases (listed as an input in the design table) is NOT used here: its
-- `alias` column is an alternate PRODUCT slug, not a second artifact identifier, so it carries
-- no artifact-pair evidence at this grain. An alias-driven artifact equivalence, if one is ever
-- declared, belongs in identity_equivalence_edges (candidate_key -> product_slug), not here.

WITH fold_pairs AS (
  SELECT
    n.artifact_kind,
    a.spelling AS artifact_id_a,
    b.spelling AS artifact_id_b,
    CASE WHEN n.artifact_kind = 'homepage' THEN 0.5 ELSE 1.0 END AS evidence,
    CASE WHEN n.artifact_kind = 'homepage' THEN 'homepage_domain' ELSE 'fold_collapse' END AS method
  FROM currentai.identity.artifact_nodes n
  CROSS JOIN UNNEST(n.also_seen_as) AS a(spelling)
  CROSS JOIN UNNEST(n.also_seen_as) AS b(spelling)
  WHERE a.spelling < b.spelling
),

gh_redirects AS (
  SELECT
    'github' AS artifact_kind,
    LEAST(repo, resolved_repo) AS artifact_id_a,
    GREATEST(repo, resolved_repo) AS artifact_id_b,
    0.9 AS evidence,
    'github_redirect' AS method
  FROM currentai.signal_github.artifact_state
  WHERE resolved_via_redirect = TRUE
    AND resolved_repo IS NOT NULL
    AND resolved_repo <> repo
),

combined AS (
  SELECT * FROM fold_pairs
  UNION ALL
  SELECT * FROM gh_redirects
),

tiered AS (
  SELECT
    c.*,
    COALESCE(na.best_tier, 'pool') AS tier_a,
    COALESCE(nb.best_tier, 'pool') AS tier_b
  FROM combined c
  LEFT JOIN currentai.identity.artifact_nodes na
    ON na.artifact_kind = c.artifact_kind AND CONTAINS(na.also_seen_as, c.artifact_id_a)
  LEFT JOIN currentai.identity.artifact_nodes nb
    ON nb.artifact_kind = c.artifact_kind AND CONTAINS(nb.also_seen_as, c.artifact_id_b)
)

SELECT
  CAST(artifact_kind AS VARCHAR) AS artifact_kind,
  CAST(artifact_id_a AS VARCHAR) AS artifact_id_a,
  CAST(artifact_id_b AS VARCHAR) AS artifact_id_b,
  CAST(
    CASE
      WHEN 'pool' IN (MAX(tier_a), MAX(tier_b)) THEN 'pool'
      WHEN 'tail' IN (MAX(tier_a), MAX(tier_b)) THEN 'tail'
      ELSE 'head'
    END AS VARCHAR
  ) AS candidate_tier,
  CAST(GREATEST(0, LEAST(1, MAX(evidence) - 0)) AS DOUBLE) AS confidence,
  ARRAY_SORT(ARRAY_DISTINCT(ARRAY_AGG(method))) AS method,
  CAST(ARRAY[] AS ARRAY(VARCHAR)) AS penalties
FROM tiered
GROUP BY artifact_kind, artifact_id_a, artifact_id_b
