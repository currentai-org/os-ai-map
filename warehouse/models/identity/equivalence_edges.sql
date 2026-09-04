-- ────── PLATFORM MIRROR (read-only) ──────
-- A snapshot of a model that runs on the OSO platform to build one of the gap map's
-- tables. The platform is the source of truth; nothing deploys from this copy, and
-- editing it here changes nothing. See README.md and manifest.yaml in this folder.

-- currentai.identity.equivalence_edges
--
-- Grain: one row per (candidate_key, product_tier, product_slug). candidate_key =
-- <artifact_kind> || ':' || <folded artifact_key> (build/identity.py::fold_for_proposal).
--
-- Sourced from currentai.identity.artifact_nodes (`all_nodes` below), which spans ALL tiers
-- (head, tail, pool) -- NOT currentai.identity.candidates, which is pool-only. Per reviewer
-- ruling: the replay eval compares edges against what humans already declared, so this model
-- must be able to emit an equivalence edge onto a head- or tail-tier artifact too, not just an
-- undeclared pool one. `candidate_tier` (the node's `best_tier`: head/tail/pool) is carried as
-- its own explicit output column so a downstream reader can filter back down to pool-only
-- (currentai.identity.digest does exactly that -- see its header).
--
-- The resolution_ledger evidence path is the one exception that does NOT read `all_nodes`
-- directly: a ledger ruling can name an artifact that is not in today's live node fetch (a
-- historical or since-archived candidate), so its candidate_key is still computed independently
-- via the fold CASE (the same rule as identity_artifact_nodes.sql's `keyed` CTE -- Trino has no
-- shared macro, so it is intentionally duplicated, not re-derived differently), and its
-- candidate_tier is looked up against `all_nodes` with a `'pool'` fallback when the artifact is
-- not found live (matching the tier a since-archived pool candidate almost always had).
-- `artifact_kind` is carried as its own explicit column (not just embedded in candidate_key) per
-- the schema ruling that every edge table names its artifact kind directly.
--
-- Confidence: GREATEST(evidence...) - SUM(penalties), clamped with GREATEST(0, LEAST(1, ...)).
-- `penalties` is ARRAY(VARCHAR); no penalty source is defined for this model today, so it is
-- always the empty array.
--
-- Evidence sources:
--   1.0  resolution ledger -- currentai.registry.resolution_ledger, verdict IN
--        ('existing_product', 'sku_of'). `relation` absent means product_equivalence per the
--        ledger schema (docs/schemas/resolution_ledger.schema.json); relation =
--        'product_membership' rulings (member_of / not_member_of) answer a different question
--        and are excluded here.
--   0.9  declared alias -- currentai.registry.product_aliases. Its `alias` column is a bare
--        product-name-shaped string with no artifact_kind of its own (confirmed live: columns
--        are alias, product_slug only), so it cannot be turned into a candidate_key on its own.
--        Matched against the candidate's NAME segment (`candidate_names.normalized_name`), the
--        same side the model-family patterns match, NOT against artifact_key: an alias is shaped
--        like `serde-json` while artifact_key for the dominant kinds is `<namespace>/<name>`, so
--        the artifact_key comparison this CTE used until 2026-09-04 matched NOTHING and the
--        source was inert (0 rows). Both sides are folded the same way -- lowercased,
--        non-alphanumeric runs collapsed to `-`, leading/trailing `-` trimmed -- which subsumes
--        fold_for_proposal's `[-_.]+ -> -` rule for every alias shape in the live vocabulary.
--        Restricted to the Hub and package kinds (huggingface_model, huggingface_dataset, pypi,
--        crates, npm) and NOT github: a GitHub repo name is frequently not the product name
--        (`ggerganov/llama.cpp`, `vllm-project/vllm`), so matching an alias against it invents
--        equivalences the vocabulary never declared.
--        Capped at 0.9, not the 1.0 a declared alias would otherwise carry. The alias->product
--        half of the mapping IS declared by a curator, but the alias->NODE half is inferred by
--        name, and the spot check on the 46 rows it now emits shows that inference is not
--        certain: the alias matches the name segment regardless of namespace, so
--        `tiny-random/phi-4` (a random-weights test stub, not phi-4 at all) earns the same edge
--        as `microsoft/phi-4`. 0.9 keeps a declared alias ahead of a model-family match (0.8)
--        and behind a resolution_ledger ruling (1.0), which is the true ordering of how much
--        human judgment stands behind each.
--   0.8  model family -- currentai.registry.model_families, `pattern` matched via LIKE with the
--        glob `*` turned into SQL `%` (ESCAPE '\', and any literal `%` in the pattern escaped
--        first so it is not itself read as a wildcard). Where several pattern rows match the same
--        candidate, only the row with the greatest LENGTH(pattern) is kept (longest match wins).
--        Matched against the candidate's NAME segment (`candidate_names.normalized_name`: the part
--        after the first `/`, lowercased, non-alphanumerics folded to `-`), NOT against
--        artifact_key. artifact_key for a Hub artifact is `<namespace>/<name>` (verified live
--        2026-09-04: e.g. `meta-llama/llama-guard-3-8b`), so a family pattern like `llama-guard-*`
--        would match nothing at all against artifact_key -- the family vocabulary names model
--        LINES, not namespaced repo ids. Restricted to huggingface_model / huggingface_dataset:
--        the patterns describe model families, and matching them against GitHub repo names would
--        fire `llama-*` on `ggerganov/llama.cpp` (normalized `llama-cpp`) and attach a 0.8
--        equivalence edge onto the wrong product.
--   0.5  name match (a CEILING, never higher) -- same normalization rule as
--        identity_membership_edges.sql's candidate_names CTE.
--
-- Homepage-domain evidence: per reviewer ruling, a shared homepage domain is weak corroborating
-- evidence for PRODUCT equivalence too -- capped at 0.5, method 'homepage_domain', and able to
-- add at most +0.1 on top of other evidence for the same (candidate_key, product_tier,
-- product_slug), clamped to 1, rather than following the plain MAX(evidence) formula. This model
-- has no such evidence source today: currentai.registry.products carries no homepage column, and
-- currentai.registry.product_artifacts has zero artifact_kind = 'homepage' rows live (checked
-- 2026-09-03), so there is nothing to match a homepage-kind candidate's domain against at the
-- product grain (org-level domain matching is identity_org_edges.sql's homepage_evidence, which
-- answers a different question -- who owns it, not which product it equals). If a product-level
-- homepage source is added, its evidence must be wired through the capped/stacked rule above,
-- not the plain MAX(evidence) - penalty_sum formula used for the other four sources.
--
-- Verified live 2026-09-04: currentai.registry.model_families exists with 26 rows and exactly the
-- brief's columns (pattern, product_slug, note, decided_in). currentai.registry.resolution_ledger
-- has NO `product` column (its columns are artifact_kind, artifact_id, relation, verdict,
-- boundary, decided_in, decided_on, note, resolves_to), so the product slug is read straight from
-- `resolves_to`, which is populated on every existing_product / sku_of row.
--
-- Output casts: explicit CAST on every output column (VARCHAR strings, DOUBLE confidence,
-- ARRAY(VARCHAR) method/penalties), matching the deploy pass's fix on the first four models --
-- the confidence literals (1.0/0.9/0.8/0.5) are Trino DECIMAL, not DOUBLE, so `GREATEST(0, LEAST(1,
-- MAX(confidence) - 0))` would otherwise leave the column typed DECIMAL and liable to drift
-- against the other edge tables' DOUBLE confidence.

WITH all_nodes AS (
  SELECT
    artifact_kind,
    artifact_key,
    artifact_kind || ':' || artifact_key AS candidate_key,
    best_tier AS candidate_tier,
    artifact_id
  FROM currentai.identity.artifact_nodes
),

ledger_key AS (
  SELECT
    verdict,
    resolves_to AS product_slug,
    artifact_kind,
    artifact_kind || ':' ||
      CASE
        WHEN artifact_kind IN ('github', 'huggingface_model', 'huggingface_dataset')
          THEN LOWER(artifact_id)
        WHEN artifact_kind IN ('pypi', 'crates')
          THEN REGEXP_REPLACE(LOWER(artifact_id), '[-_.]+', '-')
        WHEN artifact_kind = 'homepage'
          THEN REGEXP_REPLACE(
                 REGEXP_EXTRACT(LOWER(artifact_id), '^(?:[a-z]+://)?([^/]+)', 1),
                 '^www\.', ''
               )
        ELSE LOWER(artifact_id)
      END AS candidate_key
  FROM currentai.registry.resolution_ledger
  WHERE verdict IN ('existing_product', 'sku_of')
    AND (relation IS NULL OR relation = 'product_equivalence')
),

-- Head tier is currentai.registry.products, NOT the distinct product_slug of
-- currentai.registry.product_artifacts. Head-ness is a declaration, and a head product is under
-- no obligation to declare artifacts: 121 of the 615 products have zero product_artifacts rows
-- (verified live 2026-09-04), and the two rosters are disjoint from tail_products (0 overlap).
-- Deriving head from product_artifacts silently dropped every evidence row pointing at one of
-- those 121 -- including the resolution_ledger ruling a2aproject/a2a -> agent2agent-protocol,
-- which is exactly the kind of hand-made ruling this model exists to honor.
products_tier_ranked AS (
  SELECT slug, product_tier
  FROM (
    SELECT
      slug,
      product_tier,
      ROW_NUMBER() OVER (PARTITION BY slug ORDER BY tier_rank) AS rn
    FROM (
      SELECT slug, 1 AS tier_rank, 'head' AS product_tier
      FROM currentai.registry.products
      UNION ALL
      SELECT slug, 2 AS tier_rank, 'tail' AS product_tier
      FROM currentai.registry.tail_products
      GROUP BY slug
    )
  )
  WHERE rn = 1
),

ledger_evidence AS (
  SELECT
    lk.candidate_key,
    lk.artifact_kind,
    COALESCE(n.candidate_tier, 'pool') AS candidate_tier,
    pt.product_tier,
    lk.product_slug,
    1.0 AS confidence,
    'resolution_ledger' AS method
  FROM ledger_key lk
  LEFT JOIN all_nodes n
    ON n.candidate_key = lk.candidate_key AND n.artifact_kind = lk.artifact_kind
  JOIN products_tier_ranked pt ON pt.slug = lk.product_slug
),

candidate_names AS (
  SELECT
    candidate_key,
    artifact_kind,
    candidate_tier,
    LOWER(
      TRIM(BOTH '-' FROM REGEXP_REPLACE(
        CASE
          WHEN artifact_kind IN ('github', 'huggingface_model', 'huggingface_dataset')
               AND STRPOS(artifact_id, '/') > 0
            THEN SUBSTR(artifact_id, STRPOS(artifact_id, '/') + 1)
          ELSE artifact_id
        END,
        '[^a-zA-Z0-9]+', '-'
      ))
    ) AS normalized_name
  FROM all_nodes
),

-- product_aliases carries no artifact_kind of its own (confirmed live: alias, product_slug only),
-- so an alias fires only when it matches a live node's NAME segment, and inherits that node's
-- artifact_kind/candidate_key/candidate_tier. Matched against candidate_names.normalized_name,
-- not artifact_key -- see the header: an alias is `serde-json`-shaped and artifact_key is
-- `<namespace>/<name>`, so the artifact_key form matched nothing at all. The alias is folded with
-- the same rule as normalized_name so the two sides are comparable. Restricted to the Hub and
-- package kinds; github is excluded because a repo name is often not the product name.
alias_evidence AS (
  SELECT
    cn.candidate_key,
    cn.artifact_kind,
    cn.candidate_tier,
    pt.product_tier,
    pa.product_slug,
    0.9 AS confidence,
    'product_alias' AS method
  FROM currentai.registry.product_aliases pa
  JOIN candidate_names cn
    ON cn.normalized_name =
       LOWER(TRIM(BOTH '-' FROM REGEXP_REPLACE(pa.alias, '[^a-zA-Z0-9]+', '-')))
  JOIN products_tier_ranked pt ON pt.slug = pa.product_slug
  WHERE cn.artifact_kind IN (
    'huggingface_model', 'huggingface_dataset', 'pypi', 'crates', 'npm'
  )
),

-- longest pattern wins where several currentai.registry.model_families rows match one candidate.
-- Matched against normalized_name (the name segment), not artifact_key -- see the header.
-- The glob `*` is turned into SQL `%`; a literal `%` in a pattern is escaped first so it is not
-- itself read as a wildcard, with a single-character ESCAPE.
family_matches AS (
  SELECT
    cn.candidate_key,
    cn.artifact_kind,
    cn.candidate_tier,
    mf.product_slug,
    mf.pattern,
    ROW_NUMBER() OVER (
      PARTITION BY cn.candidate_key
      ORDER BY LENGTH(mf.pattern) DESC
    ) AS pattern_rank
  FROM candidate_names cn
  JOIN currentai.registry.model_families mf
    ON cn.normalized_name LIKE
         REPLACE(REPLACE(mf.pattern, '%', '\%'), '*', '%') ESCAPE '\'
  WHERE cn.artifact_kind IN ('huggingface_model', 'huggingface_dataset')
),

family_evidence AS (
  SELECT
    candidate_key,
    artifact_kind,
    candidate_tier,
    product_slug,
    0.8 AS confidence,
    'model_family' AS method
  FROM family_matches
  WHERE pattern_rank = 1
),

name_evidence AS (
  SELECT
    cn.candidate_key,
    cn.artifact_kind,
    cn.candidate_tier,
    pt.product_tier,
    p.slug AS product_slug,
    0.5 AS confidence,
    'name_match' AS method
  FROM candidate_names cn
  JOIN currentai.registry.products p ON cn.normalized_name = LOWER(p.slug)
  JOIN products_tier_ranked pt ON pt.slug = p.slug
),

combined AS (
  SELECT candidate_key, artifact_kind, candidate_tier, product_tier, product_slug, confidence, method
  FROM ledger_evidence
  UNION ALL
  SELECT candidate_key, artifact_kind, candidate_tier, product_tier, product_slug, confidence, method
  FROM alias_evidence
  UNION ALL
  SELECT fe.candidate_key, fe.artifact_kind, fe.candidate_tier, pt.product_tier, fe.product_slug, fe.confidence, fe.method
  FROM family_evidence fe
  JOIN products_tier_ranked pt ON pt.slug = fe.product_slug
  UNION ALL
  SELECT candidate_key, artifact_kind, candidate_tier, product_tier, product_slug, confidence, method
  FROM name_evidence
)

SELECT
  CAST(candidate_key AS VARCHAR) AS candidate_key,
  CAST(artifact_kind AS VARCHAR) AS artifact_kind,
  CAST(MAX(candidate_tier) AS VARCHAR) AS candidate_tier,
  CAST(product_tier AS VARCHAR) AS product_tier,
  CAST(product_slug AS VARCHAR) AS product_slug,
  CAST(GREATEST(0, LEAST(1, MAX(confidence) - 0)) AS DOUBLE) AS confidence,
  CAST(ARRAY_SORT(ARRAY_DISTINCT(ARRAY_AGG(method))) AS ARRAY(VARCHAR)) AS method,
  CAST(ARRAY[] AS ARRAY(VARCHAR)) AS penalties
FROM combined
GROUP BY candidate_key, artifact_kind, product_tier, product_slug
