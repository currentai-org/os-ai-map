-- ────── PLATFORM MIRROR (read-only) ──────
-- A snapshot of a model that runs on the OSO platform to build one of the gap map's
-- tables. The platform is the source of truth; nothing deploys from this copy, and
-- editing it here changes nothing. See README.md and manifest.yaml in this folder.

-- currentai.evidence.product_evidence
-- Graded, traceable evidence behind each openness dimension, per product.
--
-- Sits between the two layer-2 stages: research writes evidence, scoring reads it
-- and applies the category's rules. Every row records how the value can be arrived
-- at again, because re-derivability - not authorship - is what makes it checkable.
-- The first pass of sources/scores was itself agent-authored, so a column saying
-- whether a human or a model wrote it would grade the wrong thing.
--
--   grade = 'dataset'   a named field in a machine-readable source. Re-derived by
--                       running a query. Carries source_table and source_column.
--   grade = 'document'  a URL whose content asserts the value. Re-derived by
--                       reading it. Carries when it was read.
--
-- `dataset` is preferred wherever it can answer, because a document is an
-- interpretation of prose and a dataset field is a lookup. RWKV is why: its
-- data-openness 5 rested on a paper's claim of a 3.1T open corpus, and what
-- corrected it to 4 was the Hub showing the published repos hold a component index
-- and previews. Choosing between the two is stage 2's job, not this model's - this
-- one records what each source says and whether it says anything usable.
--
-- Grain: one row per (product_slug, category_slug, dimension, grade, artifact_id,
-- part_index). artifact_id is null for document rows and names the SKU for dataset rows,
-- because a family ships several SKUs and they routinely disagree. That disagreement is
-- the whole reason stage 2 needs a family-level rule rather than a per-row one.
--
-- `part_index` is the same observation one level down, on the document side. A recorded
-- license can be SEVERAL licenses - `zed` ships an editor, a collab server and a UI
-- framework under three - and build/serialize_rubric.py publishes one row per part, in the
-- order the record writes them. Every other dimension answers once and pins the index at 0.
--
-- It is a grain column, not a payload one, and it exists because the alternative was
-- splitting a string in Trino. The repo owns how a recorded value is parsed; when the
-- warehouse re-derived the parts from punctuation the two disagreed, and three products
-- scored differently on either side of the bridge for it.
--
-- Four limits, surfaced as columns rather than buried:
--
--   * `attribution` - document sources are recorded per AXIS in sources/scores,
--     never per dimension, so a document row cannot name the single URL behind it.
--     Picking one would invent an attribution the files do not contain. The
--     evidence-store design wants per-dimension sources; today's files lack them.
--   * `admitted` - a row citing nothing specific is still emitted, carrying its
--     reason, so unsourced assertions become a queryable work list instead of
--     passing for provenance. 111 of the 253 source rows behind the base models say
--     only 'flagship phase-C verification source'.
--   * `source_reachable` is held apart from `admitted` deliberately. "The artifact
--     responded" and "the artifact answered the question" are different facts, and
--     stage 2's family rule needs the first: it must know how many SKUs it should
--     have heard from before deciding whether partial coverage is safe to act on.
--     Null for document rows, which are never fetched.
--   * `settles_dimension` - the GitHub route establishes that code exists and is
--     alive, not that it is a full training pipeline. It informs `code` and must not
--     decide it, per signal_routing.yaml. Its values are deliberately outside the
--     rubric's code enum so they cannot be mistaken for an answer.
--   * Abstention values come from currentai.registry.evidence_abstentions rather
--     than being written here, so sources/signal_routing.yaml stays the single
--     declaration. A rule implemented in two places drifts.
--
-- Openness only. Adoption bands and the capability anchor route differently, and
-- the capability anchor is still unbridged, so neither is part of this pilot.
WITH abstain AS (
  SELECT source, column_name, LOWER(abstain_value) AS abstain_value
  FROM currentai.registry.evidence_abstentions
),

-- Only categories with a machine-readable rubric can be scored, so only their
-- products need evidence. Today that is base_pretrained alone.
roster AS (
  SELECT DISTINCT pc.product_slug, pc.category_slug
  FROM currentai.registry.product_categories pc
  JOIN (
    SELECT DISTINCT category_slug FROM currentai.registry.category_scoring_rules
  ) scored ON scored.category_slug = pc.category_slug
),

-- Document grade -------------------------------------------------------------
-- Values parsed from the `components` string by build/serialize_rubric.py. Parsing
-- stays in the repo because build/check_rubric.py already owns and tests it, and a
-- second copy here would drift from the first.
axis_sources AS (
  SELECT
    product_slug,
    category_slug,
    axis,
    COUNT(*) AS sources_total,
    COUNT_IF(admitted) AS sources_admitted,
    MAX(CASE WHEN admitted THEN NULLIF(source_accessed, '') END) AS last_admitted
  FROM currentai.registry.product_score_sources
  GROUP BY product_slug, category_slug, axis
),
document AS (
  SELECT
    e.product_slug,
    e.category_slug,
    e.dimension,
    CAST(e.part_index AS BIGINT) AS part_index,
    e.value,
    NULLIF(e.value_detail, '') AS value_detail,
    'document' AS grade,
    'axis' AS attribution,
    CAST(NULL AS VARCHAR) AS artifact_id,
    CAST(NULL AS VARCHAR) AS source_url,
    CAST(NULL AS VARCHAR) AS source_table,
    CAST(NULL AS VARCHAR) AS source_column,
    TRY_CAST(s.last_admitted AS DATE) AS source_accessed,
    COALESCE(s.sources_admitted, 0) > 0 AS admitted,
    -- Never fetched, so reachability does not apply. Not `false`, which would read
    -- as "we tried and it was down".
    CAST(NULL AS BOOLEAN) AS source_reachable,
    CASE
      WHEN COALESCE(s.sources_admitted, 0) > 0 THEN CAST(NULL AS VARCHAR)
      ELSE 'openness axis cites nothing specific: '
           || CAST(COALESCE(s.sources_total, 0) AS VARCHAR)
           || ' source(s) recorded, 0 admissible'
    END AS reject_reason,
    true AS settles_dimension
  FROM currentai.registry.product_openness_evidence e
  LEFT JOIN axis_sources s
    ON s.product_slug = e.product_slug
   AND s.category_slug = e.category_slug
   AND s.axis = 'openness'
),

-- Dataset grade: Hugging Face ------------------------------------------------
hub AS (
  SELECT
    r.product_slug,
    r.category_slug,
    h.artifact_id,
    h.license,
    h.is_gated,
    h.gated_mode,
    h.is_private,
    h.is_disabled,
    h.used_storage_bytes,
    h.http_status,
    CAST(h.fetched_at AS DATE) AS fetched_on
  FROM currentai.signal_huggingface.hub_state h
  JOIN roster r ON r.product_slug = h.product_slug
  WHERE h.artifact_kind = 'huggingface_model'
),
hub_license AS (
  SELECT
    b.product_slug,
    b.category_slug,
    'license' AS dimension,
    -- A hub SKU reports one license, so the part index is 0 by construction. It is not
    -- null: a null would read as "this row has no position" and the abstain COUNT on the
    -- document side turns on rows being countable.
    CAST(0 AS BIGINT) AS part_index,
    -- The alias is load-bearing. The Hub publishes a slug (`gemma`, `llama3.1`)
    -- and the rubric's tier examples use license names, so without the map a
    -- present, use-restricting license reads as absent - which is the direction
    -- that overstates openness.
    a.license_name AS value,
    'hub slug: ' || COALESCE(b.license, '<null>') AS value_detail,
    'dataset' AS grade,
    'artifact' AS attribution,
    b.artifact_id,
    'https://huggingface.co/' || b.artifact_id AS source_url,
    'currentai.signal_huggingface.hub_state' AS source_table,
    'license' AS source_column,
    b.fetched_on AS source_accessed,
    (
      b.http_status = 200
      AND b.license IS NOT NULL
      AND ab.abstain_value IS NULL
      AND a.license_name IS NOT NULL
    ) AS admitted,
    (b.http_status = 200) AS source_reachable,
    CASE
      WHEN b.http_status <> 200
        THEN 'declared artifact does not resolve (HTTP ' || CAST(b.http_status AS VARCHAR) || ')'
      WHEN b.license IS NULL THEN 'hub records no license for this SKU'
      WHEN ab.abstain_value IS NOT NULL
        THEN 'hub license ' || b.license || ' is an escape hatch, not a license'
      WHEN a.license_name IS NULL
        THEN 'no alias declared for hub license slug ' || b.license
      ELSE CAST(NULL AS VARCHAR)
    END AS reject_reason,
    true AS settles_dimension
  FROM hub b
  LEFT JOIN currentai.registry.license_aliases a
    ON a.source = 'huggingface'
   AND LOWER(a.license_slug) = LOWER(b.license)
  -- Joined on the ROUTE's source name rather than a bare 'huggingface', so an
  -- abstention declared for model licenses cannot be read as applying to dataset
  -- licenses. Both are declared in signal_routing.yaml, on their own routes.
  LEFT JOIN abstain ab
    ON ab.source = 'huggingface_model'
   AND ab.column_name = 'license'
   AND ab.abstain_value = LOWER(b.license)
),
hub_weights AS (
  SELECT
    b.product_slug,
    b.category_slug,
    'weights' AS dimension,
    CAST(0 AS BIGINT) AS part_index,
    -- Only ever 'open' or nothing. A private or disabled repo is NOT evidence the
    -- weights are closed: the model may be distributed off the Hub entirely, which
    -- signal_routing.yaml calls out as unroutable and leaves to research.
    CASE
      WHEN b.http_status = 200
       AND NOT COALESCE(b.is_private, false)
       AND NOT COALESCE(b.is_disabled, false)
       AND COALESCE(b.used_storage_bytes, 0) > 0
      THEN 'open'
      ELSE CAST(NULL AS VARCHAR)
    END AS value,
    -- Gating is recorded here rather than closing the dimension. A click-through
    -- gate is not the same thing as withheld weights.
    CONCAT(
      CASE WHEN COALESCE(b.is_gated, false)
        THEN 'gated (' || COALESCE(b.gated_mode, 'unspecified') || ')' ELSE 'ungated' END,
      ', ',
      CAST(ROUND(COALESCE(b.used_storage_bytes, 0) / 1e9, 1) AS VARCHAR), ' GB on the Hub'
    ) AS value_detail,
    'dataset' AS grade,
    'artifact' AS attribution,
    b.artifact_id,
    'https://huggingface.co/' || b.artifact_id AS source_url,
    'currentai.signal_huggingface.hub_state' AS source_table,
    'is_private, is_disabled, used_storage_bytes' AS source_column,
    b.fetched_on AS source_accessed,
    (
      b.http_status = 200
      AND NOT COALESCE(b.is_private, false)
      AND NOT COALESCE(b.is_disabled, false)
      AND COALESCE(b.used_storage_bytes, 0) > 0
    ) AS admitted,
    (b.http_status = 200) AS source_reachable,
    CASE
      WHEN b.http_status <> 200
        THEN 'declared artifact does not resolve (HTTP ' || CAST(b.http_status AS VARCHAR) || ')'
      WHEN COALESCE(b.is_private, false) THEN 'hub repo is private'
      WHEN COALESCE(b.is_disabled, false) THEN 'hub repo is disabled'
      WHEN COALESCE(b.used_storage_bytes, 0) = 0 THEN 'hub repo carries no files'
      ELSE CAST(NULL AS VARCHAR)
    END AS reject_reason,
    true AS settles_dimension
  FROM hub b
),

-- Dataset grade: GitHub ------------------------------------------------------
-- Presence and liveness only. Whether the code is a full pretraining pipeline or
-- inference utilities is a judgment no API makes, so this route informs `code`
-- without settling it. The values are deliberately NOT in the rubric's code enum
-- (open / partial / closed) so they cannot be read as an answer by mistake.
repo_code AS (
  SELECT
    r.product_slug,
    r.category_slug,
    'code' AS dimension,
    CAST(0 AS BIGINT) AS part_index,
    CASE
      WHEN g.http_status <> 200 THEN CAST(NULL AS VARCHAR)
      WHEN COALESCE(g.is_archived, false) THEN 'repo-archived'
      ELSE 'repo-present'
    END AS value,
    'last pushed ' || COALESCE(CAST(CAST(g.pushed_at AS DATE) AS VARCHAR), 'unknown') AS value_detail,
    'dataset' AS grade,
    'artifact' AS attribution,
    g.repo AS artifact_id,
    g.html_url AS source_url,
    'currentai.signal_github.repo_state' AS source_table,
    'is_archived, pushed_at' AS source_column,
    CAST(g.fetched_at AS DATE) AS source_accessed,
    (g.http_status = 200) AS admitted,
    (g.http_status = 200) AS source_reachable,
    CASE
      WHEN g.http_status <> 200
        THEN 'declared repo does not resolve (HTTP ' || CAST(g.http_status AS VARCHAR) || ')'
      ELSE CAST(NULL AS VARCHAR)
    END AS reject_reason,
    -- The load-bearing false. Everything else about this row is corroboration.
    false AS settles_dimension
  FROM currentai.signal_github.repo_state g
  JOIN roster r ON r.product_slug = g.product_slug
)

SELECT
  product_slug,
  category_slug,
  dimension,
  part_index,
  value,
  value_detail,
  grade,
  attribution,
  artifact_id,
  source_url,
  source_table,
  source_column,
  source_accessed,
  admitted,
  source_reachable,
  reject_reason,
  settles_dimension
FROM (
  SELECT * FROM document
  UNION ALL SELECT * FROM hub_license
  UNION ALL SELECT * FROM hub_weights
  UNION ALL SELECT * FROM repo_code
)
ORDER BY product_slug, dimension, grade, artifact_id, part_index
