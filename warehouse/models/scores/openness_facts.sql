-- ────── PLATFORM MIRROR (read-only) ──────
-- A snapshot of a model that runs on the OSO platform to build one of the gap map's
-- tables. The platform is the source of truth; nothing deploys from this copy, and
-- editing it here changes nothing. See README.md and manifest.yaml in this folder.

-- currentai.scores.openness_facts
-- Layer-2 stage 2a: one authoritative fact per dimension a ladder declares.
--
-- Grain: one row per (product_slug, category_slug, fact_key), including declared dimensions
-- the product records NOTHING for - those carry a null value, which is the point. A missing
-- row would be indistinguishable from a dimension nobody asked about, and the difference
-- between "unanswered" and "not asked" is what a freshness claim turns on.
--
-- ## Why this is its own model
--
-- It was one query with `openness_computed` until 2026-08-05. Generalizing off the
-- hardcoded model dimensions took it to 174 Trino stages against a ceiling of 150, because
-- the resolution CTEs are referenced several times each by the rule walk and Trino replans
-- the subtree per reference. Splitting materializes the facts once.
--
-- The split earns its keep beyond the stage count. docs/guides/verification.md describes the
-- audit chain as score <- rule <- dimension values <- evidence <- source, and the third link
-- had no table: `openness_computed` resolved dimensions inside itself and published only the
-- score. This is that link, queryable, so "which fact did this score rest on, at what grade"
-- is a select rather than a re-derivation.
--
-- ## What resolution means here
--
-- Two grades arrive from the evidence store and one has to win.
--
--   * A dataset-grade route reports per SKU and a family of SKUs can disagree, so those rows
--     are aggregated before they become a fact. Where the admitted SKUs agree, dataset wins:
--     a field lookup beats someone's reading of prose. Where they disagree, this abstains and
--     the recorded components decide, with the reason in `fact_note`.
--   * `license_tier` is the one derived fact. A license is recorded as one or more NAMES and
--     a rule tests a tier, so each name is normalized and mapped through the ladder's own
--     examples before anything can read it, and the most restrictive of them governs. Every
--     part must map or the whole value abstains - see `license_fact`. Ladders that turn on no
--     license at all - hardware scores design, toolchain and availability - get no
--     `license_tier` row, and that absence is how `openness_computed` knows not to demand one.
--
-- Nothing in this file names a dimension. The vocabulary comes from
-- currentai.registry.category_dimensions, which is the ladder's own declaration, so a
-- seventeenth category resolves here the day its recipe lands.
--
-- ## Deferrals are marked, not dropped
--
-- `scoring_recipe.deferred` names products a category has declared its ladder does not
-- decide - 86 of the 470 today. They stay in this table carrying `is_deferred` and the
-- recorded reason, because dropping them would make the openness tables cover 384 products
-- and answer "why not this one" with silence. The refusal is data.
--
-- What must not happen is a score. `openness_computed` refuses to walk the rules for a
-- deferred product, and the flag has to travel with the facts for it to be able to:
-- suppressing a product's document rows in the repo does not suppress the hub rows the signal
-- route writes for the same product, so the evidence store has two inlets and a deferred
-- product arrives here regardless. Until the flag existed, `safeguards` published a computed
-- score for nine guardrail models the repo had explicitly declined to stand behind - the
-- model ladder ends in `otherwise: {score: 3}` - and seven of the nine disagreed with the
-- recorded value.
WITH dims AS (
  SELECT category_slug, product_type, dimension
  FROM currentai.registry.category_dimensions
),
variants AS (
  SELECT DISTINCT category_slug, product_type FROM dims
),
-- One row per (category, ladder variant, example license), which the registry table itself
-- does not guarantee. `proprietary` is both a declared example and one of the definitional
-- tokens, and the two dataset ladders each list apache-2.0, mit and odc-by twice: 17 example
-- licenses across 13 ladders arrive as two or three rows.
--
-- It never mattered while the license was one row per product, because every aggregate
-- downstream absorbed the duplicate. It matters now that the document side COUNTS parts to
-- decide whether they all mapped - one part matching two rows would read as two parts, and
-- the count would go into `fact_note` and into the reassembled name.
--
-- Least restrictive wins a genuine disagreement, because that is what
-- `check_rubric._tier_of` does: it returns the FIRST tier whose examples contain the name,
-- and declaration order is restrictiveness ascending. No duplicate pair disagrees today -
-- all 17 resolve to a single tier - so this collapses rows without changing an answer. The
-- rule is written down anyway, because the day one pair does disagree is the day the two
-- implementations would silently answer differently.
tiers AS (
  SELECT
    category_slug,
    product_type,
    example_license,
    MIN_BY(tier, tier_rank) AS tier,
    MIN(tier_rank) AS tier_rank
  FROM (
    SELECT category_slug, product_type, tier, tier_rank,
           LOWER(TRIM(example_license)) AS example_license
    FROM currentai.registry.category_license_tiers
  )
  GROUP BY category_slug, product_type, example_license
),
ladder_tiers AS (
  SELECT category_slug, product_type, COUNT(*) AS tier_rows
  FROM tiers
  GROUP BY category_slug, product_type
),
ev AS (
  SELECT * FROM currentai.evidence.product_evidence
),

-- Roster, and which ladder governs each product ------------------------------
-- `product_type` on the registry tables is '*' when one ladder covers every type and the
-- product's own type when a category mixes them, mirroring build/rubrics.py:recipe_for. It
-- has to be resolved here rather than downstream, because `rule_index` is unique only within
-- (category_slug, product_type) and the tier examples are per variant too: `safeguards`
-- holds guardrail models on a five-tier ladder and guardrail software on a three-tier one.
--
-- The roster is the registry's, not the evidence store's. It used to be
-- `SELECT DISTINCT product_slug, category_slug FROM product_evidence`, which silently made
-- coverage conditional on evidence existing: serialize_rubric emits no document rows for a
-- deferred product, so 36 of the 86 deferrals - the ones with no Hub or GitHub artifact to
-- generate a dataset row either - were absent rather than unscored. Every product a scored
-- category claims belongs here, whether or not anything is known about it.
roster AS (
  SELECT
    pc.product_slug,
    pc.category_slug,
    COALESCE(p.type, '') AS product_type,
    d.product_slug IS NOT NULL AS is_deferred,
    d.because AS deferral_reason
  FROM currentai.registry.product_categories pc
  JOIN (
    SELECT DISTINCT category_slug FROM currentai.registry.category_scoring_rules
  ) scored
    ON scored.category_slug = pc.category_slug
  LEFT JOIN currentai.registry.products p
    ON p.slug = pc.product_slug
  LEFT JOIN currentai.registry.category_deferrals d
    ON d.product_slug = pc.product_slug
   AND d.category_slug = pc.category_slug
),
governing AS (
  SELECT
    r.product_slug,
    r.category_slug,
    r.product_type,
    r.is_deferred,
    r.deferral_reason,
    -- A '*' variant wins outright; otherwise the one matching this product's type. Null
    -- means no ladder in the category covers this type, which check_rubric reports as a
    -- problem. Here it produces a single row with a null fact_key, so the product stays
    -- visible downstream instead of disappearing.
    COALESCE(
      MAX(CASE WHEN v.product_type = '*' THEN '*' END),
      MAX(CASE WHEN v.product_type = r.product_type THEN v.product_type END)
    ) AS ladder_type
  FROM roster r
  LEFT JOIN variants v
    ON v.category_slug = r.category_slug
  GROUP BY r.product_slug, r.category_slug, r.product_type, r.is_deferred, r.deferral_reason
),

-- Every fact key the governing ladder asks about -----------------------------
declared AS (
  SELECT category_slug, product_type, dimension AS fact_key FROM dims
  UNION ALL
  -- The derived one, present only where there is a tier vocabulary to derive against.
  SELECT category_slug, product_type, 'license_tier' FROM ladder_tiers
),

-- One pass over the evidence store, per declared dimension -------------------
-- Both grades resolved in a single aggregation rather than two CTEs and a full outer join,
-- which is again the stage count.
--
-- The join to `dims` is what keeps traceability rows out. serialize_rubric emits the
-- resolved value under the DIMENSION name and every other recorded key under its own name,
-- so `finetuned_chat`'s data answer arrives as `data` while the raw `post-training-data` row
-- rides along for provenance. Both are document grade and only one is a fact.
--
-- `settles_dimension` on the dataset side replaces a hardcoded exclusion of `code`. The
-- GitHub route reports that a repo exists and is alive, which informs the code dimension
-- without answering it, and signal_routing.yaml is where that is declared. Reading the flag
-- rather than naming the dimension means a future corroborating route is handled correctly
-- on the day it lands instead of quietly outvoting a document.
dim_facts AS (
  SELECT
    g.product_slug,
    g.category_slug,
    e.dimension AS fact_key,
    -- One document row per grain by construction. The aggregate is defensive: a second row
    -- would otherwise multiply this product through every downstream join.
    MAX(CASE WHEN e.grade = 'document' THEN e.value END) AS doc_value,
    BOOL_OR(e.grade = 'document' AND e.admitted) AS doc_admitted,
    MAX(CASE WHEN e.grade = 'document' THEN e.source_accessed END) AS doc_accessed,
    COUNT_IF(e.grade = 'dataset' AND e.settles_dimension AND e.admitted) AS skus_admitted,
    COUNT(DISTINCT CASE
      WHEN e.grade = 'dataset' AND e.settles_dimension AND e.admitted THEN e.value END
    ) AS values_seen,
    MAX(CASE
      WHEN e.grade = 'dataset' AND e.settles_dimension AND e.admitted THEN e.value END
    ) AS ds_value,
    MIN(CASE
      WHEN e.grade = 'dataset' AND e.settles_dimension AND e.admitted THEN e.source_accessed END
    ) AS ds_accessed
  FROM ev e
  JOIN governing g
    ON g.product_slug = e.product_slug
   AND g.category_slug = e.category_slug
  JOIN dims d
    ON d.category_slug = e.category_slug
   AND d.product_type = g.ladder_type
   AND d.dimension = e.dimension
  GROUP BY g.product_slug, g.category_slug, e.dimension
),

-- The license, which is an input rather than a dimension ---------------------
-- One row per recorded PART. A license can be several licenses - `zed` ships an editor
-- under GPL-3.0-or-later, a collab server under AGPL-3.0 and GPUI under Apache-2.0 - and
-- the tier is the most restrictive of them. The parts arrive already separated, one
-- evidence row each carrying its `part_index`, so nothing here splits a string.
--
-- That is a change of principle rather than of technique. This model used to receive the
-- whole clause and cut the last `+`-segment out of it when the word 'model' appeared,
-- while build/serialize_rubric.py published a value already truncated at the first `(`.
-- Between them, `zed`'s three licenses reached the warehouse as one and
-- `redpajama-data-v2`'s two arrived joined into a name no tier declares. Both sides were
-- inferring the count of licenses from punctuation, and they inferred differently: three
-- of the last standing parity divergences were exactly that.
--
-- The curator records the count. `culturax` writes `follows mC4 + OSCAR-2301 terms` as ONE
-- part, because neither operand is a license, and no rule here could have told that from a
-- genuine compound. That is why the pre-check this replaces had to exist, and why it does
-- not need to any more.
license_rows AS (
  SELECT
    g.product_slug,
    g.category_slug,
    g.ladder_type,
    e.grade,
    e.admitted,
    e.source_reachable,
    e.source_accessed,
    e.part_index,
    CASE
      -- Mirrors build/check_rubric.py:normalize_license, and both forms are named in
      -- the recipe's `normalization` list. A `code ` or `model ` prefix says which
      -- artifact the license covers, not which license it is; the 'assumed-' prefix marks
      -- confidence, not a different license. Dataset rows arrive from the hub route
      -- already resolved to a canonical name, so they skip this.
      --
      -- The 'code MIT + model X' rule the old CASE implemented - keep the last segment,
      -- the model license governs - is gone, and is now a consequence rather than a
      -- special case: both parts resolve and the most restrictive wins. In every recorded
      -- instance the weights license IS the restrictive half, and where it would not be,
      -- the old rule was wrong anyway. A permissive weights license does not buy back a
      -- restrictive code license.
      WHEN e.grade = 'document' THEN TRIM(REGEXP_REPLACE(
        REGEXP_REPLACE(e.value, '(?i)^\s*(code|model)\s+', ''),
        '(?i)^assumed-', ''))
      ELSE TRIM(e.value)
    END AS license_clean
  FROM ev e
  JOIN governing g
    ON g.product_slug = e.product_slug
   AND g.category_slug = e.category_slug
  WHERE e.dimension = 'license'
),
-- Then the recorded-name alias, which is the third step of normalize_license and
-- the one that cannot be expressed as a regex. The hub path already joins
-- license_aliases for the slug a source publishes; this is the same table for the
-- name a human typed, under source = 'recorded'.
--
-- Applied AFTER the regex steps, matching the order in check_rubric, so the alias
-- table does not have to enumerate an `assumed-` variant of every license.
--
-- Left out, `glm-4` and `NVIDIA-Nemotron-Open-Model-License` map to no tier and the
-- score comes out null, while check_rubric resolves both and reports the category fully
-- reproduced. The two disagreeing is worse than either being wrong, because the local
-- checker is what CI gates on and the warehouse is what anyone querying the map sees.
license_named AS (
  SELECT
    l.product_slug,
    l.category_slug,
    l.ladder_type,
    l.grade,
    l.admitted,
    l.source_reachable,
    l.source_accessed,
    l.part_index,
    COALESCE(a.license_name, l.license_clean) AS license_name
  FROM license_rows l
  LEFT JOIN currentai.registry.license_aliases a
    ON a.source = 'recorded'
   AND l.grade = 'document'
   AND LOWER(a.license_slug) = LOWER(l.license_clean)
),
license_tiered AS (
  SELECT
    n.product_slug,
    n.category_slug,
    n.grade,
    n.admitted,
    n.source_reachable,
    n.source_accessed,
    n.part_index,
    n.license_name,
    t.tier,
    t.tier_rank
  FROM license_named n
  LEFT JOIN tiers t
    ON t.category_slug = n.category_slug
   AND t.product_type = n.ladder_type
   AND t.example_license = LOWER(n.license_name)
),

-- Grade precedence, and why partial coverage cannot be trusted ---------------
-- Dataset grade governs a family-level aggregate ONLY when every reachable SKU yielded a
-- mapped tier.
--
-- Measured on qwen-2-5: Qwen2.5-72B reports its license as `other` and Qwen2.5-7B as
-- apache-2.0. Taking the max over only the SKUs that answered resolves the family to `osi`
-- and moves it from 2/restricted to 3/open_weights, on the strength of the SKU that is not
-- the restrictive one. max(restrictiveness) over a subset can only fall, so partial coverage
-- always biases toward permissive. It overstates openness, which is the worst direction for
-- this map to be wrong in.
--
-- A second way partial trust fails, found 2026-07-29 when release-level products were
-- collapsed into vendor tiers. A tier declares every release's repos, so `gemma` carries
-- Gemma 2, 3 and 4: four SKUs report the Gemma License and two report Apache-2.0, and
-- most-restrictive across all six published the family as `restricted` when Gemma 4 had
-- relicensed. Same for `hermes`, whose Llama-based and Apache-based builds substitute for
-- each other. Most-restrictive is only sound across SKUs a user cannot substitute away from;
-- across releases and interchangeable bases it erases relicensing. So when the mapped SKUs
-- disagree, the dataset route abstains and the recorded components decide.
--
-- Every other dataset route is held to agreement but not to coverage, and the difference is
-- not an oversight. `license_tier` is an aggregate over SKUs - most restrictive wins - so a
-- SKU we failed to reach can change the answer. The weights route is a claim about
-- existence: one downloadable SKU makes the family's weights downloadable, and a SKU we
-- missed could only have added openness. An unreachable SKU is fatal to the first and
-- harmless to the second; disagreement among SKUs that DID answer is fatal to both.
--
-- ## The document side is now an aggregate too, over PARTS rather than SKUs
--
-- Same shape, same reason, one level down. A recorded license has one or more parts and
-- `check_rubric.license_tier` resolves every one of them: if any part maps to no tier the
-- whole value abstains, and otherwise the most restrictive governs. Skipping a part it
-- could not map would be the partial-coverage error again - an unmapped part can only ever
-- be MORE restrictive than the tier the mapped parts reached, so ignoring it overstates
-- openness. `doc_parts` and `doc_parts_mapped` are that test; `doc_most_restrictive` is the
-- MAX over tier rank, which is the ladder's own declaration order ascending.
license_fact AS (
  SELECT
    product_slug,
    category_slug,
    COUNT_IF(grade = 'dataset' AND source_reachable) AS skus_reachable,
    COUNT_IF(grade = 'dataset' AND source_reachable AND admitted AND tier IS NOT NULL)
      AS skus_mapped,
    COUNT(DISTINCT CASE
      WHEN grade = 'dataset' AND admitted AND tier IS NOT NULL THEN tier END
    ) AS tiers_seen,
    -- COALESCE to -1 stops an unmapped SKU winning the max, and -2 keeps document rows out
    -- of the family aggregate entirely. If nothing mapped, the winning value is null anyway
    -- and the coverage test below rejects the family.
    MAX_BY(
      CASE WHEN grade = 'dataset' THEN tier END,
      CASE WHEN grade = 'dataset' THEN COALESCE(tier_rank, -1) ELSE -2 END
    ) AS most_restrictive_tier,
    MIN(CASE
      WHEN grade = 'dataset' AND admitted AND tier IS NOT NULL THEN source_accessed END
    ) AS ds_accessed,
    COUNT_IF(grade = 'document') AS doc_parts,
    COUNT_IF(grade = 'document' AND tier IS NOT NULL) AS doc_parts_mapped,
    -- Same -1 / -2 convention as the SKU aggregate above: an unmapped part cannot win the
    -- max, and dataset rows are kept out of the document one entirely.
    MAX_BY(
      CASE WHEN grade = 'document' THEN tier END,
      CASE WHEN grade = 'document' THEN COALESCE(tier_rank, -1) ELSE -2 END
    ) AS doc_most_restrictive,
    -- The recorded license reassembled in the order it was written, which is what
    -- `part_index` is carried this far for. It is what gets printed when no tier resolves,
    -- and reading 'GPL-3.0-or-later + AGPL-3.0 + Apache-2.0' is how someone sees which of
    -- the three the ladder has not been told about.
    ARRAY_JOIN(
      ARRAY_AGG(license_name ORDER BY part_index) FILTER (WHERE grade = 'document'), ' + '
    ) AS doc_license_name,
    BOOL_OR(grade = 'document' AND admitted) AS doc_admitted,
    MAX(CASE WHEN grade = 'document' THEN source_accessed END) AS doc_accessed
  FROM license_tiered
  GROUP BY product_slug, category_slug
),
-- The two verdicts, named once rather than spelled out at each of the five places that
-- used to repeat the coverage test.
license_resolved AS (
  SELECT
    *,
    (skus_reachable > 0 AND skus_mapped = skus_reachable AND tiers_seen <= 1)
      AS dataset_governs,
    CASE WHEN doc_parts > 0 AND doc_parts_mapped = doc_parts THEN doc_most_restrictive END
      AS doc_tier
  FROM license_fact
),

-- One authoritative fact per key ---------------------------------------------
resolved AS (
  SELECT
    g.product_slug,
    g.category_slug,
    'license_tier' AS fact_key,
    CASE WHEN f.dataset_governs THEN f.most_restrictive_tier ELSE f.doc_tier END AS fact_value,
    CASE WHEN f.dataset_governs THEN 'dataset' ELSE 'document' END AS fact_grade,
    CASE WHEN f.dataset_governs THEN true ELSE COALESCE(f.doc_admitted, false) END
      AS fact_admitted,
    CASE WHEN f.dataset_governs THEN f.ds_accessed ELSE f.doc_accessed END AS fact_accessed,
    -- The license as it was named before the tier lookup, so an unmapped one can be read off
    -- this table instead of reconstructed. check_rubric prints exactly this in its finding.
    -- All of it, for a compound: the part that failed to map is the one worth seeing, and it
    -- is not always the first.
    f.doc_license_name AS fact_input,
    CASE
      WHEN f.dataset_governs THEN CAST(NULL AS VARCHAR)
      WHEN f.tiers_seen > 1
        THEN 'dataset abstained on the family: its ' || CAST(f.skus_mapped AS VARCHAR)
             || ' mapped SKUs span ' || CAST(f.tiers_seen AS VARCHAR)
             || ' license tiers, so most-restrictive is a judgment about which releases '
             || 'substitute for each other rather than a lookup. Deferred to the recorded '
             || 'components.'
      WHEN f.skus_reachable > 0 AND f.skus_mapped < f.skus_reachable
        THEN 'dataset abstained on the family: ' || CAST(f.skus_mapped AS VARCHAR) || ' of '
             || CAST(f.skus_reachable AS VARCHAR)
             || ' reachable SKUs mapped to a tier, so most-restrictive is not computable'
      -- A partly-mapped recorded license. Distinct from mapping nothing, which is a plain
      -- "the rubric has not been told about this license" and is reported downstream by
      -- `openness_computed` off `fact_input`. This one names a rubric gap that a glance at
      -- the reassembled license would not: two of three parts resolved.
      WHEN f.doc_parts > f.doc_parts_mapped AND f.doc_parts_mapped > 0
        THEN 'the recorded license abstained: ' || CAST(f.doc_parts_mapped AS VARCHAR)
             || ' of its ' || CAST(f.doc_parts AS VARCHAR)
             || ' parts map to a tier, and an unmapped part can only be more restrictive '
             || 'than the ones that did, so most-restrictive would overstate openness.'
      ELSE CAST(NULL AS VARCHAR)
    END AS fact_note
  FROM governing g
  JOIN ladder_tiers lt
    ON lt.category_slug = g.category_slug
   AND lt.product_type = g.ladder_type
  LEFT JOIN license_resolved f
    ON f.product_slug = g.product_slug AND f.category_slug = g.category_slug

  UNION ALL

  SELECT
    product_slug,
    category_slug,
    fact_key,
    CASE WHEN values_seen = 1 THEN ds_value ELSE doc_value END,
    CASE WHEN values_seen = 1 THEN 'dataset' ELSE 'document' END,
    CASE WHEN values_seen = 1 THEN true ELSE COALESCE(doc_admitted, false) END,
    CASE WHEN values_seen = 1 THEN ds_accessed ELSE doc_accessed END,
    CAST(NULL AS VARCHAR),
    CASE
      WHEN values_seen > 1
        THEN 'dataset abstained on ' || fact_key || ': its '
             || CAST(skus_admitted AS VARCHAR) || ' admitted SKUs report '
             || CAST(values_seen AS VARCHAR)
             || ' different values, so the family has no single machine-readable answer. '
             || 'Deferred to the recorded components.'
      ELSE CAST(NULL AS VARCHAR)
    END
  FROM dim_facts
)

SELECT
  g.product_slug,
  g.category_slug,
  g.product_type,
  g.ladder_type AS ladder_product_type,
  g.is_deferred,
  g.deferral_reason,
  d.fact_key,
  r.fact_value,
  r.fact_grade,
  r.fact_admitted,
  r.fact_accessed,
  r.fact_input,
  r.fact_note,
  -- The distinction the null value cannot carry on its own: this ladder asked, and this
  -- product has an answer. `dims_recorded` downstream is a sum over this column.
  r.fact_value IS NOT NULL AND r.fact_value <> '' AS is_recorded
FROM governing g
LEFT JOIN declared d
  ON d.category_slug = g.category_slug
 AND d.product_type = g.ladder_type
LEFT JOIN resolved r
  ON r.product_slug = g.product_slug
 AND r.category_slug = g.category_slug
 AND r.fact_key = d.fact_key
ORDER BY g.product_slug, g.category_slug, d.fact_key
