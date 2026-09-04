-- ────── PLATFORM MIRROR (read-only) ──────
-- A snapshot of a model that runs on the OSO platform to build one of the gap map's
-- tables. The platform is the source of truth; nothing deploys from this copy, and
-- editing it here changes nothing. See README.md and manifest.yaml in this folder.

-- currentai.identity.artifact_nodes
--
-- Grain: one row per (artifact_kind, artifact_key). `artifact_key` is the FOLDED comparison
-- form -- see build/identity.py::fold_for_proposal, which this SQL mirrors exactly:
--   github, huggingface_model, huggingface_dataset  -> LOWER(x)
--   pypi, crates                                    -> REGEXP_REPLACE(LOWER(x), '[-_.]+', '-')
--   homepage                                        -> LOWER(x)
-- A homepage artifact_id is the FULL canonical URL as the repo publishes it -- scheme-less,
-- host lowercased, leading `www.` stripped, PATH KEPT as declared, no trailing slash (see
-- build/identity.py::_homepage_canonical). Its fold is that whole string lowercased
-- (fold_for_proposal's `homepage -> c.lower()`), NOT the bare host: two distinct products at
-- `acme.com/a` and `acme.com/b` are legitimately different homepage artifacts, and collapsing
-- them onto the host made every homepage key disagree with the repo's truth key. Verified
-- 2026-09-04 against the 27 declared homepage rows in currentai.registry.tail_products
-- (currentai.registry.product_artifacts declares none): every published id is already
-- scheme-less with no `www.` prefix, so LOWER() alone reproduces fold_for_proposal exactly.
-- Anything downstream that needs the bare HOST extracts it from the key itself
-- (identity_org_edges.sql does; do not reintroduce a host-only fold here to serve it).
-- `artifact_id` keeps the DECLARED spelling (never folded): identity.py's own docstring is
-- explicit that the declared spelling must survive because downstream joins against externally
-- sourced signal tables (GitHub's own casing, PyPI's own package name) are on raw equality.
-- Where more than one declared spelling folds to the same artifact_key, one representative
-- artifact_id is kept -- chosen by tier priority (head, then tail, then pool) and then
-- alphabetically -- and every distinct spelling seen is kept in `also_seen_as` so
-- identity_artifact_identity_edges can emit the fold-collapse pairs.
--
-- Inputs:
--   currentai.registry.product_artifacts   (tier=head; every row is a declared artifact)
--   currentai.registry.tail_products       (tier=tail; every row is a declared artifact)
--   currentai.signal_hfhub.model_universe  (kind=huggingface_model, tier=pool; undeclared hub models)
--   currentai.signal_goodailist.repo_catalog (kind=github, tier=pool; undeclared GitHub repos)
-- currentai.signal_openrouter.models is NOT a node source here (it names `provider_model`
-- identifiers on OpenRouter's own namespace, not a first-class artifact kind in build/identity.py
-- -- design table row for identity.artifact_nodes lists it as "as provider_model evidence only,
-- not a node kind"); it is read by identity_candidates.sql instead.
--
-- Verified on deploy (2026-09-03, ListTablesForDataset): signal_hfhub.model_universe
-- (hf_id, downloads_30d BIGINT, likes BIGINT, fetched_at TIMESTAMP) and
-- signal_goodailist.repo_catalog (repo, stars BIGINT, source_updated_at TIMESTAMP) match the
-- columns read below; no drift.

WITH declared AS (
  SELECT
    artifact_kind,
    artifact_id,
    1 AS tier_rank,
    'head' AS tier,
    product_slug AS declared_by
  FROM currentai.registry.product_artifacts

  UNION ALL

  SELECT
    artifact_kind,
    artifact_id,
    2 AS tier_rank,
    'tail' AS tier,
    slug AS declared_by
  FROM currentai.registry.tail_products
),

hub AS (
  SELECT
    'huggingface_model' AS artifact_kind,
    hf_id AS artifact_id,
    3 AS tier_rank,
    'pool' AS tier,
    CAST(NULL AS VARCHAR) AS declared_by,
    downloads_30d,
    likes,
    CAST(NULL AS BIGINT) AS stars,
    CAST(fetched_at AS TIMESTAMP(6)) AS observed_at
  FROM currentai.signal_hfhub.model_universe
),

gh AS (
  SELECT
    'github' AS artifact_kind,
    repo AS artifact_id,
    3 AS tier_rank,
    'pool' AS tier,
    CAST(NULL AS VARCHAR) AS declared_by,
    CAST(NULL AS BIGINT) AS downloads_30d,
    CAST(NULL AS BIGINT) AS likes,
    stars,
    CAST(source_updated_at AS TIMESTAMP(6)) AS observed_at
  FROM currentai.signal_goodailist.repo_catalog
),

unioned AS (
  SELECT
    artifact_kind, artifact_id, tier_rank, tier, declared_by,
    CAST(NULL AS BIGINT) AS downloads_30d,
    CAST(NULL AS BIGINT) AS likes,
    CAST(NULL AS BIGINT) AS stars,
    CAST(NULL AS TIMESTAMP(6)) AS observed_at
  FROM declared

  UNION ALL

  SELECT artifact_kind, artifact_id, tier_rank, tier, declared_by,
         downloads_30d, likes, stars, observed_at
  FROM hub

  UNION ALL

  SELECT artifact_kind, artifact_id, tier_rank, tier, declared_by,
         downloads_30d, likes, stars, observed_at
  FROM gh
),

keyed AS (
  SELECT
    *,
    CASE
      WHEN artifact_kind IN ('github', 'huggingface_model', 'huggingface_dataset')
        THEN LOWER(artifact_id)
      WHEN artifact_kind IN ('pypi', 'crates')
        THEN REGEXP_REPLACE(LOWER(artifact_id), '[-_.]+', '-')
      -- homepage folds the WHOLE canonical URL, path included -- see the header. The declared
      -- id already arrives scheme-less and `www.`-free, so LOWER() is the whole fold.
      WHEN artifact_kind = 'homepage'
        THEN LOWER(artifact_id)
      ELSE LOWER(artifact_id)
    END AS artifact_key
  FROM unioned
)

SELECT
  CAST(artifact_kind AS VARCHAR) AS artifact_kind,
  CAST(artifact_key AS VARCHAR) AS artifact_key,
  -- representative declared spelling: lowest tier_rank (head < tail < pool), then alphabetical.
  -- Trino has no WITHIN GROUP for array_agg -- the sort goes inside the aggregate's arg list.
  CAST(ARRAY_AGG(artifact_id ORDER BY tier_rank, artifact_id)[1] AS VARCHAR) AS artifact_id,
  CAST(CASE MIN(tier_rank)
    WHEN 1 THEN 'head'
    WHEN 2 THEN 'tail'
    ELSE 'pool'
  END AS VARCHAR) AS best_tier,
  ARRAY_SORT(ARRAY_DISTINCT(ARRAY_AGG(artifact_id))) AS also_seen_as,
  ARRAY_DISTINCT(ARRAY_AGG(declared_by) FILTER (WHERE declared_by IS NOT NULL)) AS declared_by,
  MAX(downloads_30d) AS downloads_30d,
  MAX(likes) AS likes,
  MAX(stars) AS stars,
  MAX(observed_at) AS last_observed_at
FROM keyed
GROUP BY artifact_kind, artifact_key
