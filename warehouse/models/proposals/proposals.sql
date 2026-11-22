-- ────── PLATFORM MIRROR (read-only) ──────
-- A snapshot of a model that runs on the OSO platform to build one of the gap map's
-- tables. The platform is the source of truth; nothing deploys from this copy, and
-- editing it here changes nothing. See README.md and manifest.yaml in this folder.

-- currentai.proposals.proposals
-- Input to os-ai-map's proposals bridge (build/proposals.py): one row per proposal, one
-- UNION ALL branch per producer. Empty until the first producer exists. Kept FULL, never
-- incremental: a producer's rows go when the producer is fixed or disabled.

SELECT
  CAST(NULL AS varchar)   AS proposal_id,
  CAST(NULL AS varchar)   AS kind,
  CAST(NULL AS varchar)   AS product_slug,
  CAST(NULL AS varchar)   AS axis,
  CAST(NULL AS date)      AS observed_at,
  CAST(NULL AS varchar)   AS producer_model,
  CAST(NULL AS varchar)   AS producer_revision,
  CAST(NULL AS varchar)   AS evidence,
  CAST(NULL AS timestamp) AS created_at
FROM (VALUES 1) AS t(x)
WHERE false
