-- ────── PLATFORM MIRROR (read-only) ──────
-- A snapshot of a model that runs on the OSO platform to build one of the gap map's
-- tables. The platform is the source of truth; nothing deploys from this copy, and
-- editing it here changes nothing. See README.md and manifest.yaml in this folder.

-- currentai.language_representation.classification
-- Contract table, method version 1 (os-ai-map docs/reference/language-classification.md).
-- One row per ISO 639-3 code in scope. Reads classification_src, which writes related_to, flags and
-- provenance as JSON text because Python models write flat columns only.
SELECT
  iso639_3,
  macrolanguage,
  CAST(json_parse(related_to) AS array(varchar)) AS related_to,
  CAST(json_parse(flags) AS array(varchar)) AS flags,
  written_best,
  written_worst,
  written_state,
  representation_class,
  representation_class_best,
  representation_class_worst,
  status_best,
  status_worst,
  status_state,
  recognized,
  speakers_low,
  speakers_high,
  speakers_state,
  official,
  many_speakers,
  large_written_material,
  scholarly_works,
  endangerment,
  descriptive_status,
  transform(
    CAST(json_parse(provenance) AS array(row(measure varchar, source varchar, source_version varchar,
                                             retrieved_at varchar, content_sha256 varchar))),
    p -> CAST(ROW(p.measure, p.source, p.source_version, CAST(p.retrieved_at AS timestamp(6)), p.content_sha256)
              AS row(measure varchar, source varchar, source_version varchar, retrieved_at timestamp(6),
                     content_sha256 varchar))
  ) AS provenance,
  code_table_version,
  method_version,
  CAST(computed_at AS timestamp(6)) AS computed_at
FROM currentai.language_representation.classification_src
