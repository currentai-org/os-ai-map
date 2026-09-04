-- ────── PLATFORM MIRROR (read-only) ──────
-- A snapshot of a model that runs on the OSO platform to build one of the gap map's
-- tables. The platform is the source of truth; nothing deploys from this copy, and
-- editing it here changes nothing. See README.md and manifest.yaml in this folder.

-- currentai.identity.org_edges
--
-- Grain: one row per (candidate_key, org_slug). Only onto orgs that already exist --
-- every evidence source below joins to currentai.registry.organizations, so a candidate can
-- never manufacture a new org here.
--
-- Sourced from currentai.identity.artifact_nodes (`all_nodes` below), which spans ALL tiers
-- (head, tail, pool) -- NOT currentai.identity.candidates, which is pool-only. Per reviewer
-- ruling: the replay eval compares edges against what humans already declared, so this model
-- must be able to emit an org edge onto a head- or tail-tier artifact too, not just an undeclared
-- pool one. `candidate_tier` (the node's `best_tier`: head/tail/pool) is carried as its own
-- explicit output column so a downstream reader can filter back down to pool-only
-- (currentai.identity.digest does exactly that -- see its header). candidate_key =
-- <artifact_kind> || ':' || <artifact_key>; `artifact_kind` is also carried as its own explicit
-- column per the schema ruling that every edge table names its artifact kind directly.
--
-- Confidence: GREATEST(evidence...) - SUM(penalties), clamped with GREATEST(0, LEAST(1, ...)).
-- `penalties` is ARRAY(VARCHAR); no penalty source is defined for this model today, so it is
-- always the empty array.
--
-- Evidence sources:
--   0.85 org handle -- currentai.registry.org_handles (platform, handle, org_slug): the
--        candidate's owner/namespace segment matches a registered handle for that platform.
--        org_handles.platform does NOT use the artifact_kind vocabulary (verified live
--        2026-09-04: the distinct set is github 220, homepage_domain 257, huggingface 2 -- 479
--        rows). It is coarser on the Hub side and differently spelled on the homepage side, so
--        the join goes through the `handle_platform_map` CTE below rather than a bare
--        `platform = artifact_kind` equality, which would have matched only the github rows and
--        silently dropped the other 259. The homepage row shape also differs in WHAT is compared:
--        a homepage_domain handle is a bare domain, so it is matched against the HOST of the
--        candidate's artifact_key, not against owner_handle, which is NULL for a homepage
--        artifact and would have matched nothing. It also differs in HOW: a homepage handle
--        matches its own subdomains too (see the host-matching note below).
--   0.80 HF namespace -- a huggingface_model/huggingface_dataset candidate's namespace segment
--        (the part before the first `/`) matches an org's slug directly, with no registered
--        handle in org_handles. Lower confidence than an explicit handle because it is a bare
--        slug-equality guess, not a curated mapping.
--   0.75 homepage domain -- a homepage candidate's host matches the host of an org's
--        currentai.registry.organizations.homepage. This 0.75 stands uncapped -- unlike the
--        weak-corroboration cap applied to homepage-domain evidence in
--        identity_artifact_identity_edges.sql and identity_equivalence_edges.sql, org ownership
--        is exactly the relation a shared domain is good evidence for.
--
-- Host matching, both homepage paths (fixed 2026-09-04 -- both emitted ZERO rows before):
--   1. The host is extracted from artifact_key rather than used raw:
--      REGEXP_EXTRACT(artifact_key, '^([^/]+)', 1) with a leading `www.` stripped. Homepage
--      artifact_id is moving to the full canonical URL (host lowercased, `www.` stripped, path
--      kept, no trailing slash) in a parallel repo change, so `example.com/product` will fold to
--      a key with a path segment in it. Today's 27 homepage keys are still bare hosts, so the
--      extraction is a no-op on live data -- it exists so the model does not silently go to zero
--      the week the repo change lands.
--   2. A candidate host matches an org domain when it EQUALS it or is a SUBDOMAIN of it
--      (`host LIKE '%.' || domain`). Exact equality alone is why both paths were inert: none of
--      the 27 homepage nodes is a bare registered org domain, but three are subdomains of one --
--      `rocm.docs.amd.com` (amd), `developer.nvidia.com` (nvidia),
--      `developers.llamaindex.ai` (llamaindex). LIKE is safe without an ESCAPE clause here
--      because a hostname cannot contain `%` or `_`.
--   3. On the organizations.homepage path only, an org host claimed by MORE THAN ONE org is
--      dropped (`unambiguous_org_hosts` below). 7 hosts are shared live, and they are shared
--      because they are code-hosting platforms, not company domains: 11 orgs give `github.com`
--      as their homepage and 3 give `huggingface.co`. Without the filter a single homepage
--      candidate under such a host would fan out to every one of those orgs at 0.75.
--      org_handles needs no such filter -- its 257 homepage_domain handles are unambiguous
--      (0 handles map to more than one org_slug, verified live).
--   Both homepage paths land on the SAME three candidates today, so those rows carry
--   method ['homepage_domain', 'org_handle'] and confidence 0.85 (the MAX), not 0.75. The two
--   paths are kept separate anyway: they read different tables and either can grow on its own.
--
-- Verified live 2026-09-04: currentai.registry.org_handles exists with 479 rows and exactly the
-- brief's columns (platform, handle, org_slug). Its `platform` vocabulary is coarser than
-- artifact_kind -- 'huggingface' covers both HF kinds and 'homepage_domain' is the homepage
-- spelling -- so `handle_platform_map` below carries the mapping, exactly the case the original
-- TODO on this line anticipated.
--
-- evidence (ARRAY(VARCHAR), added 2026-09-04 per reviewer ruling): one `<url> | <excerpt>`
-- string per contributing evidence item, NOT a repeat of the method-name vocabulary. Shapes:
--   org_handle (github)      https://github.com/<handle> | org_handles: <org> github <handle>
--   org_handle (huggingface) https://huggingface.co/<handle> | org_handles: <org> huggingface <handle>
--   org_handle (homepage)    https://<handle> | org_handles: <org> homepage_domain <handle>
--   hf_namespace              https://huggingface.co/<ns> | namespace matches org <org> huggingface handle
--   homepage_domain          https://<candidate host> | host matches org <org> homepage_domain handle
-- The homepage_domain excerpt is the ruling's wording verbatim even though this path reads
-- registry.organizations.homepage rather than org_handles -- the two homepage paths land on the
-- same three candidates today and a reviewer sees both strings on one row.
--
-- Output casts: explicit CAST on every output column (VARCHAR strings, DOUBLE confidence,
-- ARRAY(VARCHAR) method/penalties), matching the deploy pass's fix on the first four models --
-- the confidence literals (0.85/0.80/0.75) are Trino DECIMAL, not DOUBLE, so
-- `GREATEST(0, LEAST(1, MAX(evidence) - 0))` would otherwise leave the column typed DECIMAL.

WITH all_nodes AS (
  SELECT
    artifact_kind,
    artifact_key,
    artifact_kind || ':' || artifact_key AS candidate_key,
    best_tier AS candidate_tier,
    artifact_id
  FROM currentai.identity.artifact_nodes
),

candidate_owner AS (
  SELECT
    candidate_key,
    artifact_kind,
    candidate_tier,
    artifact_key,
    artifact_id,
    CASE
      WHEN artifact_kind IN ('github', 'huggingface_model', 'huggingface_dataset')
           AND STRPOS(artifact_id, '/') > 0
        THEN LOWER(SUBSTR(artifact_id, 1, STRPOS(artifact_id, '/') - 1))
      ELSE NULL
    END AS owner_handle,
    -- What an org_handles row is compared against, per platform: the owner/namespace segment for
    -- github and the two Hub kinds, the bare host for homepage (a homepage artifact has no owner
    -- segment at all). The host is EXTRACTED from artifact_key up to the first `/` rather than
    -- used raw, so a canonical-URL key like `example.com/product` still yields `example.com`.
    CASE
      WHEN artifact_kind = 'homepage'
        THEN REGEXP_REPLACE(REGEXP_EXTRACT(artifact_key, '^([^/]+)', 1), '^www\.', '')
      WHEN artifact_kind IN ('github', 'huggingface_model', 'huggingface_dataset')
           AND STRPOS(artifact_id, '/') > 0
        THEN LOWER(SUBSTR(artifact_id, 1, STRPOS(artifact_id, '/') - 1))
      ELSE NULL
    END AS handle_token
  FROM all_nodes
),

-- org_handles.platform -> artifact_kind. Read live, not assumed: platform is
-- {github, huggingface, homepage_domain}, artifact_kind is
-- {github, huggingface_model, huggingface_dataset, homepage, pypi, crates, npm, arxiv}.
handle_platform_map AS (
  SELECT * FROM (
    VALUES
      ('github', 'github'),
      ('huggingface', 'huggingface_model'),
      ('huggingface', 'huggingface_dataset'),
      ('homepage_domain', 'homepage')
  ) AS t (platform, artifact_kind)
),

-- The URL an org_handles row itself points at, per platform: a github account page, a Hub
-- namespace page, or the bare domain as an https URL.
handle_urls AS (
  SELECT * FROM (
    VALUES
      ('github', 'https://github.com/'),
      ('huggingface', 'https://huggingface.co/'),
      ('homepage_domain', 'https://')
  ) AS t (platform, url_prefix)
),

handle_evidence AS (
  SELECT
    co.candidate_key,
    co.artifact_kind,
    co.candidate_tier,
    oh.org_slug,
    0.85 AS evidence,
    'org_handle' AS method,
    hu.url_prefix || LOWER(oh.handle) || ' | org_handles: ' || oh.org_slug || ' '
      || oh.platform || ' ' || LOWER(oh.handle) AS evidence_item
  FROM candidate_owner co
  JOIN handle_platform_map hpm ON hpm.artifact_kind = co.artifact_kind
  JOIN currentai.registry.org_handles oh
    ON oh.platform = hpm.platform
   AND LOWER(oh.handle) = co.handle_token
  JOIN handle_urls hu ON hu.platform = oh.platform
  JOIN currentai.registry.organizations o ON o.slug = oh.org_slug
),

-- Subdomain half of the org-handle path, homepage only: `rocm.docs.amd.com` is the amd handle
-- `amd.com` one level down. Split out from handle_evidence rather than folded into its join
-- condition so the github/Hub path stays a plain equi-join. Strictly the subdomain case
-- (`%.` || handle), so it can never duplicate a handle_evidence row.
homepage_handle_evidence AS (
  SELECT
    co.candidate_key,
    co.artifact_kind,
    co.candidate_tier,
    oh.org_slug,
    0.85 AS evidence,
    'org_handle' AS method,
    'https://' || LOWER(oh.handle) || ' | org_handles: ' || oh.org_slug
      || ' homepage_domain ' || LOWER(oh.handle) AS evidence_item
  FROM candidate_owner co
  JOIN currentai.registry.org_handles oh
    ON oh.platform = 'homepage_domain'
   AND co.handle_token LIKE '%.' || LOWER(oh.handle)
  JOIN currentai.registry.organizations o ON o.slug = oh.org_slug
  WHERE co.artifact_kind = 'homepage'
),

hf_namespace_evidence AS (
  SELECT
    co.candidate_key,
    co.artifact_kind,
    co.candidate_tier,
    o.slug AS org_slug,
    0.80 AS evidence,
    'hf_namespace' AS method,
    'https://huggingface.co/' || co.owner_handle || ' | namespace matches org ' || o.slug
      || ' huggingface handle' AS evidence_item
  FROM candidate_owner co
  JOIN currentai.registry.organizations o ON LOWER(o.slug) = co.owner_handle
  WHERE co.artifact_kind IN ('huggingface_model', 'huggingface_dataset')
),

-- currentai.registry.organizations.homepage, folded to a bare host the same way the candidate
-- side is. A host claimed by more than one org is dropped: those are code-hosting platforms
-- (github.com on 11 orgs, huggingface.co on 3), not company domains, and matching one would fan a
-- single candidate out to every org sharing it.
org_hosts AS (
  SELECT
    o.slug,
    REGEXP_REPLACE(
      REGEXP_EXTRACT(LOWER(o.homepage), '^(?:[a-z]+://)?([^/]+)', 1),
      '^www\.', ''
    ) AS org_host
  FROM currentai.registry.organizations o
  WHERE o.homepage IS NOT NULL
),

unambiguous_org_hosts AS (
  SELECT org_host, MAX(slug) AS slug
  FROM org_hosts
  WHERE org_host IS NOT NULL
  GROUP BY org_host
  HAVING COUNT(DISTINCT slug) = 1
),

homepage_evidence AS (
  SELECT
    co.candidate_key,
    co.artifact_kind,
    co.candidate_tier,
    h.slug AS org_slug,
    0.75 AS evidence,
    'homepage_domain' AS method,
    'https://' || co.handle_token || ' | host matches org ' || h.slug
      || ' homepage_domain handle' AS evidence_item
  FROM candidate_owner co
  JOIN unambiguous_org_hosts h
    ON co.handle_token = h.org_host
    OR co.handle_token LIKE '%.' || h.org_host
  WHERE co.artifact_kind = 'homepage'
),

combined AS (
  SELECT * FROM handle_evidence
  UNION ALL
  SELECT * FROM homepage_handle_evidence
  UNION ALL
  SELECT * FROM hf_namespace_evidence
  UNION ALL
  SELECT * FROM homepage_evidence
)

SELECT
  CAST(candidate_key AS VARCHAR) AS candidate_key,
  CAST(artifact_kind AS VARCHAR) AS artifact_kind,
  CAST(MAX(candidate_tier) AS VARCHAR) AS candidate_tier,
  CAST(org_slug AS VARCHAR) AS org_slug,
  CAST(GREATEST(0, LEAST(1, MAX(evidence) - 0)) AS DOUBLE) AS confidence,
  CAST(ARRAY_SORT(ARRAY_DISTINCT(ARRAY_AGG(method))) AS ARRAY(VARCHAR)) AS method,
  CAST(ARRAY_SORT(ARRAY_DISTINCT(ARRAY_AGG(evidence_item))) AS ARRAY(VARCHAR)) AS evidence,
  CAST(ARRAY[] AS ARRAY(VARCHAR)) AS penalties
FROM combined
GROUP BY candidate_key, artifact_kind, org_slug
