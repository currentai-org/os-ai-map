-- ────── PLATFORM MIRROR (read-only) ──────
-- A snapshot of a model that runs on the OSO platform to build one of the gap map's
-- tables. The platform is the source of truth; nothing deploys from this copy, and
-- editing it here changes nothing. See README.md and manifest.yaml in this folder.

-- currentai.identity.candidates
--
-- Grain: one row per candidate_key (the resolved set's primary artifact -- i.e. an
-- currentai.identity.artifact_nodes row with no declared spelling at all, best_tier = 'pool').
-- candidate_key = <artifact_kind> || ':' || <artifact_key> (the folded comparison form of
-- artifact_id, see build/identity.py::fold_for_proposal). The kind prefix is required so that
-- candidate_key is globally unique across artifact kinds -- two different kinds can fold to the
-- same bare string (e.g. a homepage host and a PyPI name) -- and so every downstream reader
-- (equivalence_edges, org_edges, digest) can recover artifact_kind from candidate_key alone.
-- `artifact_key` (unprefixed) is kept as its own column for kind-scoped joins and for readers
-- that already have artifact_kind in hand.
--
-- Inputs: currentai.identity.artifact_nodes, filtered to best_tier = 'pool' (nodes minus
-- anything declared in currentai.registry.product_artifacts or currentai.registry.tail_products
-- -- a node with ANY declared spelling has best_tier head/tail and is excluded here).
-- currentai.signal_openrouter.models is read only to enrich `source` for a huggingface_model
-- candidate that is ALSO listed on OpenRouter under the same id; it never creates a candidate
-- row of its own -- OpenRouter's `provider_model` is not a first-class artifact kind in
-- build/identity.py (see the header of identity_artifact_nodes.sql).
--
-- first_seen / last_evidence_change / evidence_kinds: added so identity_digest.sql can derive
-- park/resurface state without reading its own prior output (no model may read its own prior
-- materialization). first_seen is the earliest observation of the artifact across its node
-- inputs (currentai.identity.artifact_nodes.last_observed_at is itself a MAX over fetched_at /
-- source_updated_at, so it is reused directly rather than re-deriving a MIN here -- there is no
-- earlier per-fetch timestamp exposed at the node grain to MIN over). last_evidence_change is the
-- latest of: the node's last_observed_at, and the resolution_ledger's decided_on for any ruling
-- naming this candidate (a ledger ruling is evidence of a state change even when it does not
-- itself become a digest item).
--
-- evidence_kinds is DELIBERATELY EMPTY here. It was originally the distinct method vocabulary
-- seen for this candidate_key across the three edge tables (membership, equivalence, org), but
-- currentai.identity.membership_edges reads currentai.identity.candidates (for its name-match
-- evidence), so reading membership_edges back from this model is a genuine circular dependency in
-- the model DAG -- not a staleness question the platform can schedule around. The cycle is broken
-- HERE, on the upstream side, because the only consumer of evidence_kinds is
-- identity_digest.sql, which already joins all three edge tables and can aggregate the method
-- vocabulary itself with no cycle. The column stays in the schema as an empty ARRAY(VARCHAR) so
-- the digest's park/resurface test (evidence_kinds = ARRAY['name_match']) needs no schema change
-- when it is moved there. Until the digest does that aggregation, park/resurface eligibility will
-- read as "no evidence yet" for every candidate.
--
-- TODO verify on deploy: whether currentai.signal_openrouter.models.model_id namespaces line up
-- with currentai.signal_hfhub.model_universe.hf_id closely enough for a raw equality join to be
-- useful; sampled rows on 2026-09-03 suggest OpenRouter's `<provider>/<slug>` ids do not
-- generally match Hub `<namespace>/<repo>` ids, so this join may contribute few or zero rows
-- today -- it is left in as a documented no-harm enrichment, not load-bearing for the grain.

WITH pool_nodes AS (
  SELECT
    artifact_kind,
    artifact_key,
    artifact_kind || ':' || artifact_key AS candidate_key,
    artifact_id,
    best_tier,
    downloads_30d,
    likes,
    stars,
    last_observed_at
  FROM currentai.identity.artifact_nodes
  WHERE best_tier = 'pool'
),

openrouter_seen AS (
  SELECT DISTINCT LOWER(model_id) AS candidate_key_lower
  FROM currentai.signal_openrouter.models
),

-- one row per candidate_key naming every ledger ruling that mentions it, folded the same way
-- artifact_nodes/candidates fold artifact_id -- duplicated here for the same reason
-- identity_equivalence_edges.sql duplicates it: Trino has no shared macro.
ledger_evidence_change AS (
  SELECT
    artifact_kind || ':' ||
      CASE
        WHEN artifact_kind IN ('github', 'huggingface_model', 'huggingface_dataset')
          THEN LOWER(artifact_id)
        WHEN artifact_kind IN ('pypi', 'crates')
          THEN REGEXP_REPLACE(LOWER(artifact_id), '[-_.]+', '-')
        -- homepage folds the WHOLE canonical URL, path included -- the fold must stay
        -- byte-identical to identity_artifact_nodes.sql's `keyed` CTE, or a ledger ruling
        -- naming a homepage would key to a candidate that does not exist. Inert today
        -- (resolution_ledger carries only github rows, verified 2026-09-04).
        WHEN artifact_kind = 'homepage'
          THEN LOWER(artifact_id)
        ELSE LOWER(artifact_id)
      END AS candidate_key,
    MAX(CAST(decided_on AS TIMESTAMP(6))) AS last_ruling_at
  FROM currentai.registry.resolution_ledger
  GROUP BY 1
)

SELECT
  CAST(p.candidate_key AS VARCHAR) AS candidate_key,
  CAST(p.artifact_kind AS VARCHAR) AS artifact_kind,
  CAST(p.artifact_key AS VARCHAR) AS artifact_key,
  CAST(p.artifact_id AS VARCHAR) AS artifact_id,
  CAST(
    CASE p.artifact_kind
      WHEN 'huggingface_model' THEN 'signal_hfhub.model_universe'
      WHEN 'github' THEN 'signal_goodailist.repo_catalog'
      ELSE 'unknown'
    END ||
      (CASE WHEN o.candidate_key_lower IS NOT NULL THEN '+signal_openrouter.models' ELSE '' END)
    AS VARCHAR) AS source,
  CAST(p.last_observed_at AS TIMESTAMP(6)) AS first_seen,
  CAST(GREATEST(
    p.last_observed_at,
    COALESCE(lec.last_ruling_at, p.last_observed_at)
  ) AS TIMESTAMP(6)) AS last_evidence_change,
  -- always empty: see the header note on the membership_edges <-> candidates cycle
  CAST(ARRAY[] AS ARRAY(VARCHAR)) AS evidence_kinds,
  p.downloads_30d,
  p.stars
FROM pool_nodes p
LEFT JOIN openrouter_seen o
  ON p.artifact_kind = 'huggingface_model' AND LOWER(p.artifact_key) = o.candidate_key_lower
LEFT JOIN ledger_evidence_change lec ON lec.candidate_key = p.candidate_key
