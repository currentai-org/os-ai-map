-- ────── PLATFORM MIRROR (read-only) ──────
-- A snapshot of a model that runs on the OSO platform to build one of the gap map's
-- tables. The platform is the source of truth; nothing deploys from this copy, and
-- editing it here changes nothing. See README.md and manifest.yaml in this folder.

-- currentai.language_representation.measurements
-- Contract table, method version 1 (os-ai-map docs/reference/language-classification.md).
-- One row per (iso639_3, measure, source, source_version, source_label). Reads measurements_src,
-- which writes label_population as JSON text because Python models write flat columns only.
SELECT
  iso639_3,
  measure,
  source,
  source_version,
  source_label,
  value_low,
  value_high,
  state,
  CAST(json_parse(label_population) AS array(varchar)) AS label_population,
  relation,
  mapping_basis,
  source_url,
  CAST(retrieved_at AS timestamp(6)) AS retrieved_at,
  content_sha256
FROM currentai.language_representation.measurements_src
