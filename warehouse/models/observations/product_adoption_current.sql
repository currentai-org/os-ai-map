-- currentai.observations.product_adoption_current
--
-- The current-state slice of adoption observations: the latest valid, artifact-level
-- measurement per artifact-observation identity, normalized across every machine adoption
-- source into one shape. Repo-authored (authority: repo); it deploys FROM this copy once the
-- observations namespace exists on the platform (data-architecture.md §4.3) — it is NOT a
-- platform mirror.
--
-- Grain: one row per
--   (product_slug, artifact_kind, artifact_id, channel, metric_type, measurement_window_days)
--
-- ARTIFACT-LEVEL and BAND-FREE, on purpose (§4.3):
--   * No level, reach, or instrument_type. A band is a judgment about a measurement and an
--     instrument is a scoring concept; both belong to `evaluation`, assigned there by the
--     compiled routes of §4.1 (registry.adoption_routes). This table carries only the raw
--     fact: `metric_type` (what was measured) and `raw_value`.
--   * No route precedence. The `pypi > huggingface > stars` ordering is a routing decision;
--     it lives in registry.adoption_routes and is applied in evaluation.product_adoption_measurements,
--     never here. This table holds ALL valid observations across channels; it does not pick a
--     winner and does not exclude one channel because another measured the product.
--   * Product-level aggregation (summing a family's artifacts to one figure) is also an
--     evaluation concern. This is per artifact.
--
-- Run binding is blocked on #355. The platform exposes no row-level run id in the fetcher
-- tables, so `source_run_id` is NULL here and is NOT reconstructed from timestamps. A downstream
-- consequence, enforced by reconciliation (evaluation.adoption_reconciliation), not by this
-- table: an execution `SUCCESS` with no row-to-run binding reconciles to `source_unavailable`,
-- never to agreement. This table makes no completeness claim; it only records the current value.
--
-- "Latest valid" is an explicit ordering, never an unordered MAX() that could splice fields from
-- different rows (§4.3). Each source is already current-state (one row per artifact at its latest
-- fetch), so the row_number() is defensive de-duplication rather than a real history collapse;
-- when the incremental history table (observations.product_adoption, Phase 2B / #352) lands, this
-- model is replaced by a view over it with the same schema and the same tie-break.
--
-- Sources normalized (the deployed machine adoption routes of signal_routing.yaml; the
-- hand-authored active_users / reported_traction routes have no machine table and are not here):
--   signal_github.artifact_state            channel github        metric stars      (no window)
--   signal_huggingface.artifact_state       channel huggingface   metric downloads  (30-day)
--   signal_pypi.package_downloads           channel pypi          metric downloads  (30-day)
--   signal_semanticscholar.paper_citations  channel other/arxiv   metric citations  (no window)
-- signal_packages.downloads (the merged-registry successor, #314) is deliberately NOT read yet:
-- it is staged and deployed nowhere. It replaces the pypi channel here once it deploys.

WITH observations AS (
  -- GitHub stars, per declared repo. artifact_kind 'github' matches registry.product_artifacts.
  SELECT
    product_slug,
    'github'                                       AS channel,
    'github'                                       AS artifact_kind,
    repo                                           AS artifact_id,
    'stars'                                        AS metric_type,
    CAST(stargazers_count AS BIGINT)               AS raw_value,
    'stars'                                        AS unit,
    CAST(NULL AS INTEGER)                          AS measurement_window_days,
    CAST(fetched_at AS TIMESTAMP)                  AS observed_at,
    'signal_github'                                AS source_dataset,
    'currentai.signal_github.artifact_state'       AS source_table
  FROM currentai.signal_github.artifact_state
  WHERE http_status = 200 AND stargazers_count IS NOT NULL

  UNION ALL

  -- Hugging Face 30-day downloads, per artifact (model or dataset).
  SELECT
    product_slug,
    'huggingface'                                  AS channel,
    artifact_kind,
    artifact_id,
    'downloads'                                    AS metric_type,
    CAST(downloads_30d AS BIGINT)                  AS raw_value,
    'downloads'                                    AS unit,
    30                                             AS measurement_window_days,
    CAST(fetched_at AS TIMESTAMP)                  AS observed_at,
    'signal_huggingface'                           AS source_dataset,
    'currentai.signal_huggingface.artifact_state'  AS source_table
  FROM currentai.signal_huggingface.artifact_state
  WHERE http_status = 200 AND downloads_30d IS NOT NULL

  UNION ALL

  -- PyPI 30-day downloads, per package. observed_at is the last day of download data in the
  -- window (the fetcher windows counts rather than stamping a fetch time).
  SELECT
    product_slug,
    'pypi'                                         AS channel,
    'pypi'                                         AS artifact_kind,
    package                                        AS artifact_id,
    'downloads'                                    AS metric_type,
    CAST(downloads_30d AS BIGINT)                  AS raw_value,
    'downloads'                                    AS unit,
    30                                             AS measurement_window_days,
    CAST(last_day_seen AS TIMESTAMP)               AS observed_at,
    'signal_pypi'                                  AS source_dataset,
    'currentai.signal_pypi.package_downloads'      AS source_table
  FROM currentai.signal_pypi.package_downloads
  WHERE downloads_30d IS NOT NULL

  UNION ALL

  -- Semantic Scholar citations, per arxiv paper. channel is 'other' (§4.3 fixes the channel
  -- vocabulary to github|huggingface|pypi|npm|crates|other); the arxiv identity is carried by
  -- artifact_kind='arxiv' and artifact_id.
  SELECT
    product_slug,
    'other'                                              AS channel,
    'arxiv'                                               AS artifact_kind,
    arxiv_id                                              AS artifact_id,
    'citations'                                           AS metric_type,
    CAST(citation_count AS BIGINT)                        AS raw_value,
    'citations'                                           AS unit,
    CAST(NULL AS INTEGER)                                 AS measurement_window_days,
    CAST(fetched_at AS TIMESTAMP)                         AS observed_at,
    'signal_semanticscholar'                              AS source_dataset,
    'currentai.signal_semanticscholar.paper_citations'    AS source_table
  FROM currentai.signal_semanticscholar.paper_citations
  WHERE found = true AND citation_count IS NOT NULL
),

ranked AS (
  SELECT
    o.*,
    -- Deterministic id over the observation grain. captured/ingest time is excluded so an
    -- unchanged observation keeps its id across refreshes.
    lower(to_hex(sha256(to_utf8(concat_ws(
      '|', product_slug, artifact_kind, artifact_id, channel, metric_type,
      COALESCE(CAST(measurement_window_days AS VARCHAR), ''),
      CAST(observed_at AS VARCHAR)
    ))))) AS observation_id,
    ROW_NUMBER() OVER (
      PARTITION BY product_slug, artifact_kind, artifact_id, channel, metric_type, measurement_window_days
      ORDER BY observed_at DESC, source_table, artifact_id
    ) AS rn
  FROM observations o
)

SELECT
  r.observation_id,
  r.product_slug,
  p.type                                    AS product_type,
  r.artifact_kind,
  r.artifact_id,
  r.channel,
  r.metric_type,
  r.raw_value,
  r.unit,
  r.measurement_window_days,
  r.observed_at,
  CAST(current_timestamp AS TIMESTAMP)      AS ingested_at,
  r.source_dataset,
  r.source_table,
  CAST(NULL AS VARCHAR)                     AS source_run_id,             -- blocked on #355
  CAST(NULL AS VARCHAR)                     AS source_record_id,
  true                                      AS is_valid,                 -- only valid rows are selected
  CAST(NULL AS VARCHAR)                     AS supersedes_observation_id -- no history until Phase 2B
FROM ranked r
LEFT JOIN currentai.registry.products p ON p.slug = r.product_slug
WHERE r.rn = 1
