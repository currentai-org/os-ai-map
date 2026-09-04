-- ────── PLATFORM MIRROR (read-only) ──────
-- A snapshot of a model that runs on the OSO platform to build one of the gap map's
-- tables. The platform is the source of truth; nothing deploys from this copy, and
-- editing it here changes nothing. See README.md and manifest.yaml in this folder.

-- currentai.identity.membership_edges
--
-- Grain: one row per (artifact_kind, artifact_id, product_tier, product_slug).
--
-- Confidence: GREATEST(evidence...) - SUM(penalties), clamped with GREATEST(0, LEAST(1, ...)).
-- `penalties` is ARRAY(VARCHAR) (a penalty reason per applied penalty, matching the eval's
-- contract on all four edge tables); no penalty source is defined for this model today, so it is
-- always the empty array and the confidence formula's penalty_sum term is 0.
--
-- Evidence sources (per the design and the corrected plan for this pass):
--   1.0  declared -- currentai.registry.product_artifacts (product_tier=head) and
--        currentai.registry.tail_products (product_tier=tail): the product declares this exact
--        artifact.
--   0.5  name match (a CEILING, never higher) -- a currentai.identity.candidates row whose
--        artifact-local name (the part after the owner/namespace for github and
--        huggingface_model) normalizes to the same string as a currentai.registry.products slug.
--        Backlinks from build/propose_artifacts.py's declared_repo are NOT available in SQL
--        today (design table row for this model), so this model emits ONLY the declared 1.0
--        edges and the name-match 0.5 edges -- nothing else -- in this plan.
--
-- scoring_bearing: TRUE iff currentai.registry.adoption_routes declares a route for this
-- artifact_kind (i.e. some evaluation route actually reads this kind of artifact for adoption).
-- Spot check from the deploy brief: a PyPI-declared product should read TRUE (pypi has a route),
-- a homepage-declared product should read FALSE (homepage has no adoption route).
--
-- evidence (ARRAY(VARCHAR), added 2026-09-04 per reviewer ruling): one `<url> | <excerpt>`
-- string per contributing evidence item, NOT a repeat of the method-name vocabulary. A reviewer
-- reading the digest needs a link they can open and a phrase saying what it says; a method label
-- ('declared', 'name_match') tells them neither. Shapes emitted by this model:
--   declared (head)  <repo>/sources/products/<product_slug>.yaml | declared <kind> artifact
--   declared (tail)  <repo>/sources/registry/<category_slug>.yaml | declared <kind> artifact
--   name_match       <artifact url> | name segment equals product slug
-- where <repo> is https://github.com/currentai-org/os-ai-map/blob/main.
-- The tail form deviates from the ruling's single example (which names sources/products/) on
-- purpose: a tail product is not declared in sources/products/ at all -- it is a row inside
-- sources/registry/<category>.yaml (build/serialize_registry.py emits tail_products from
-- exactly that file, and carries category_slug for it). Pointing a reviewer at a URL that 404s
-- would be worse than a slightly different string.
-- Artifact URLs are built per kind, matching build/serialize_registry.py's own artifact_url
-- construction byte for byte (github, huggingface model/dataset, pypi with its trailing slash,
-- npm, crates, arxiv, homepage). registry.product_artifacts and registry.tail_products both
-- carry an `artifact_url` column, but the CASE is used instead so every evidence string in this
-- dataset is built the same way -- equivalence_edges and org_edges read artifact_nodes, which
-- has no url column at all.
--
-- TODO verify on deploy: the name-normalization rule below (lowercase, non [a-z0-9] runs
-- collapsed to a single '-', trimmed) is a reasonable guess at "the same product name", not a
-- rule taken from an existing module; tighten or replace once real name-match false positives
-- are observed.

WITH declared_head AS (
  SELECT
    artifact_kind,
    artifact_id,
    'head' AS product_tier,
    product_slug,
    1.0 AS confidence,
    'declared' AS method,
    'https://github.com/currentai-org/os-ai-map/blob/main/sources/products/'
      || product_slug || '.yaml | declared ' || artifact_kind || ' artifact' AS evidence_item
  FROM currentai.registry.product_artifacts
),

declared_tail AS (
  SELECT
    artifact_kind,
    artifact_id,
    'tail' AS product_tier,
    slug AS product_slug,
    1.0 AS confidence,
    'declared' AS method,
    -- sources/registry/<category>.yaml, not sources/products/<slug>.yaml: a tail product is a
    -- row inside its category's registry file and has no file of its own. See the header.
    'https://github.com/currentai-org/os-ai-map/blob/main/sources/registry/'
      || category_slug || '.yaml | declared ' || artifact_kind || ' artifact' AS evidence_item
  FROM currentai.registry.tail_products
),

products_tier AS (
  SELECT product_slug AS slug, 1 AS tier_rank, 'head' AS product_tier
  FROM currentai.registry.product_artifacts
  GROUP BY product_slug

  UNION ALL

  SELECT slug, 2 AS tier_rank, 'tail' AS product_tier
  FROM currentai.registry.tail_products
  GROUP BY slug
),

products_tier_ranked AS (
  SELECT slug, product_tier
  FROM (
    SELECT
      slug,
      product_tier,
      ROW_NUMBER() OVER (PARTITION BY slug ORDER BY tier_rank) AS rn
    FROM products_tier
  )
  WHERE rn = 1
),

candidate_names AS (
  SELECT
    artifact_kind,
    artifact_id,
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
    ) AS normalized_name,
    -- Per-kind artifact URL, identical in construction to build/serialize_registry.py's
    -- artifact_url. See the header on why the CASE is used rather than a registry column.
    CASE artifact_kind
      WHEN 'github' THEN 'https://github.com/' || artifact_id
      WHEN 'huggingface_model' THEN 'https://huggingface.co/' || artifact_id
      WHEN 'huggingface_dataset' THEN 'https://huggingface.co/datasets/' || artifact_id
      WHEN 'pypi' THEN 'https://pypi.org/project/' || artifact_id || '/'
      WHEN 'npm' THEN 'https://www.npmjs.com/package/' || artifact_id
      WHEN 'crates' THEN 'https://crates.io/crates/' || artifact_id
      WHEN 'arxiv' THEN 'https://arxiv.org/abs/' || artifact_id
      WHEN 'homepage' THEN 'https://' || artifact_id
      ELSE artifact_id
    END AS artifact_url
  FROM currentai.identity.candidates
),

name_match AS (
  SELECT
    c.artifact_kind,
    c.artifact_id,
    pt.product_tier,
    p.slug AS product_slug,
    0.5 AS confidence,
    'name_match' AS method,
    c.artifact_url || ' | name segment equals product slug' AS evidence_item
  FROM candidate_names c
  JOIN currentai.registry.products p
    ON c.normalized_name = LOWER(p.slug)
  JOIN products_tier_ranked pt
    ON pt.slug = p.slug
),

combined AS (
  SELECT * FROM declared_head
  UNION ALL
  SELECT * FROM declared_tail
  UNION ALL
  SELECT * FROM name_match
),

route_kinds AS (
  -- The NULL artifact_kind is filtered deliberately, not defensively: registry.adoption_routes
  -- carries a route row with a NULL artifact_kind, and a NULL inside an IN list makes
  -- `x IN (...)` evaluate to NULL rather than FALSE for any non-matching x -- which would make
  -- scoring_bearing NULL (not FALSE) for every unrouted kind, homepage included.
  SELECT DISTINCT artifact_kind
  FROM currentai.registry.adoption_routes
  WHERE artifact_kind IS NOT NULL
)

SELECT
  CAST(m.artifact_kind AS VARCHAR) AS artifact_kind,
  CAST(m.artifact_id AS VARCHAR) AS artifact_id,
  CAST(m.product_tier AS VARCHAR) AS product_tier,
  CAST(m.product_slug AS VARCHAR) AS product_slug,
  CAST(GREATEST(0, LEAST(1, MAX(m.confidence) - 0)) AS DOUBLE) AS confidence,
  ARRAY_SORT(ARRAY_DISTINCT(ARRAY_AGG(m.method))) AS method,
  CAST(ARRAY_SORT(ARRAY_DISTINCT(ARRAY_AGG(m.evidence_item))) AS ARRAY(VARCHAR)) AS evidence,
  CAST(ARRAY[] AS ARRAY(VARCHAR)) AS penalties,
  CAST(m.artifact_kind IN (SELECT artifact_kind FROM route_kinds) AS BOOLEAN) AS scoring_bearing
FROM combined m
GROUP BY m.artifact_kind, m.artifact_id, m.product_tier, m.product_slug
