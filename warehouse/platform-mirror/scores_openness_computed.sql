-- ────── PLATFORM MIRROR (read-only) ──────
-- A snapshot of a model that runs on the OSO platform to build one of the gap map's
-- tables. The platform is the source of truth; nothing deploys from this copy, and
-- editing it here changes nothing. See README.md and manifest.yaml in this folder.

-- currentai.scores.openness_computed
-- Layer-2 stage 2b: walk the ordered rules over the resolved facts.
--
-- This is build/check_rubric.py:apply_formula ported onto the warehouse. The rules
-- are NOT written here. They arrive from currentai.registry.category_scoring_rules,
-- which CI pushes from each category's `scoring_recipe`, so editing a threshold in
-- the repo re-scores without touching this model. That is the whole point of the
-- split: the repo declares, OSO computes.
--
-- Grain: one row per (product_slug, category_slug).
--
-- Reads currentai.scores.openness_facts and the rule tables, never the evidence store or the
-- raw signals. Resolution - which grade wins, how a license becomes a tier - lives in the
-- facts model, and the isolation is enforced by the dependency graph rather than by
-- convention, so this model cannot quietly reach past it.
--
-- ## No dimension is named in this file
--
-- It used to resolve `weights`, `data`, `code` and `license` in hardcoded UNION branches.
-- That was written when two model categories had a rubric, and it meant the ten software
-- categories, the two dataset categories and the hardware category produced no rows at all:
-- their rules test `source`, `core_gated`, `availability`, `answers`, `documentation`,
-- `schematics` and `toolchain`, no branch built those facts, so nothing matched and - with no
-- `otherwise` rung in those ladders - every product fell out of the join. 74 of 470 rows, and
-- the repo a week ahead of the warehouse.
--
-- Facts now arrive keyed by whatever the ladder declares, and a rule's `condition_key` joins
-- straight onto `fact_key`. A seventeenth category scores here the day its recipe lands.
--
-- ## The rule walk is per ladder VARIANT, not per category
--
-- `rule_index` is unique only within (category_slug, product_type), because a category whose
-- products do not all climb the same ladder emits one rule set per type - `safeguards` holds
-- guardrail models and guardrail software. Every join to the rule tables therefore carries
-- the governing variant, which each facts row names. Joining on the category alone
-- interleaves two ladders' numbering, and MIN(rule_index) then picks a rung from whichever
-- ladder happened to number it lowest.
--
-- ## What reproducing the hand-authored scores does and does not prove
--
-- It proves the rubric faithfully describes how the category was scored. It does
-- NOT show the scores are right: the document-grade evidence it reads was parsed
-- out of the same files the scores live in, so agreement is a fidelity check on the
-- formula, not a validation of the facts.
--
-- ## An unmapped license tier does not fall through, but it only stops the rungs that ask
--
-- check_rubric REPORTS an unmapped license rather than scoring it, and so does this:
-- the score comes out null with a reason. Letting it reach the `otherwise` rule
-- would silently record every unrecognized license as 3/open_weights.
--
-- The guard fires only for ladders that ASK about a license, which is the allowance
-- check_rubric gained for hardware. `sources/rubrics/hardware.yaml` scores design, toolchain
-- and availability and declares no `license_tier`; none of the 20 edge products records a
-- license. Applied unconditionally the guard nulls all 20 scores, and the repo would report
-- the category fully reproduced while the warehouse published nothing. The facts model emits
-- a `license_tier` row only where there is a tier vocabulary, so the presence of that fact
-- key is the test - no second lookup, and no way for the two to disagree.
--
-- That allowance was still too coarse, and it was the last shape of parity drift on this
-- axis (10 of the 13 divergences standing on 2026-08-12). `asks_license` is true whenever the
-- LADDER declares a tier vocabulary anywhere, so a product the ladder settles on a
-- source-only rung was nulled because some OTHER rung, further down and never reached, turns
-- on a license. `apify` records `source:partial` and a license of `mixed`; the software
-- ladder decides `source:partial` at 2/source_available on the source dimension alone, and
-- the license it could not map was never going to be consulted. Same for `deepseek-chat` and
-- `meta-ai` on `source:closed`, and seven more across three categories.
--
-- check_rubric fixed this in `walk_formula` (PR #203): resolve a tier only where a rung
-- actually tests one. The mirror is the `blocked` CTE below, and it is deliberately a
-- POSITION comparison rather than a condition on the winner. In Python the walk returns at
-- the first rung it can neither evaluate nor skip - a rung whose non-license conditions all
-- match, that tests `license_tier`, with no tier resolved - and that return happens BEFORE
-- any later rung, `otherwise` included, is ever seen. So the test here is whether such a
-- rung sits at a lower `rule_index` than the winning one.
--
-- ## Why an `otherwise` winner is not itself tier-checked
--
-- Because `walk_formula` does not check one either: it returns an `otherwise` result the
-- moment it reaches that rule, consulting no tier. The protection the old guard provided -
-- an unmapped license must not silently score 3/open_weights through `otherwise` - survives
-- intact, but it now lives one step earlier. To REACH `otherwise` in a ladder that turns on
-- a license, the walk must first pass every license rung above it, and any such rung whose
-- other conditions match is exactly what `blocked` catches. `dify` is the worked example:
-- it records `source:public`, which reaches the `competition_restricted` rung, so its
-- unmapped vendor license blocks there and it stays deferred rather than falling through.
--
-- Tier-checking the `otherwise` winner directly would be the stricter-looking choice and the
-- wrong one. It re-nulls every product whose ladder has a license rung it never reached,
-- which is the bug above wearing a narrower hat.
--
-- Note that `deps` below still expands an `otherwise` win to ALL condition keys. That is a
-- separate and still-correct claim - about which facts the score RESTS on for the
-- verification counts - and it is not the guard. The two were never the same question.
--
-- ## An abstention is a row, not an absence
--
-- Every non-deferred product reaching the facts model gets a row here, even when no rule
-- fires. A ladder with no `otherwise` is saying it does not decide some products - the
-- software ladders do this on purpose, because whether the published source is the whole
-- product is recorded for about two thirds of products and an `otherwise` would score the
-- rest on an absence. Those products used to vanish from this model, which reads as "not in
-- the map" rather than "the rubric abstained". Now the score is null and `scoring_note` says
-- which of the two happened.
--
-- ## A deferral is the repo refusing, and it is not the same as an abstention
--
-- `scoring_recipe.deferred` names products a category has declared its ladder does not decide.
-- Those products get a row here with a null score and the recorded reason, and the rule walk
-- never runs for them - `winning_rule_index` is null too, because a rung this model was told
-- not to apply is not an explanation of anything. All 470 products are therefore present, and
-- the 86 unscored ones say why in `scoring_note` rather than by being absent.
--
-- Keeping them out of the walk is a correctness fix, not tidiness. `sources/rubrics/model.yaml`
-- ends in `otherwise: {score: 3, class: open_weights}`, so before the flag existed `safeguards`
-- published a computed score for nine guardrail models the repo had explicitly declined to
-- stand behind, and seven of the nine disagreed with the recorded value.
--
-- The two causes stay distinguishable in `scoring_note`, which matters: a deferral is a
-- curation decision with an owner and a reason, while an abstention is the ladder reporting
-- that this product's recorded evidence does not reach any rung.
--
-- ## This model computes no freshness date, on purpose
--
-- It used to emit `freshness_floor`, the MIN accessed date across the evidence the winning
-- rule depends on. That column is gone. It was an aggregate of access dates, which is the one
-- thing docs/guides/freshness.md rules out as a freshness measure: opening a URL is a weaker
-- claim than confirming a conclusion, and no aggregation upgrades it. Having the column
-- invited exactly one use - writing it back into sources/scores as last_verified - and that
-- is what #108 did.
--
-- `last_checked` stays. It is the MAX accessed over admitted evidence and it answers a real
-- question: when did this pipeline last see any of this. It is a diagnostic, never written to
-- a file, and build/apply_scores.py no longer writes any date at all.
--
-- Nothing here stamps CURRENT_DATE either: a recompute must never make stale evidence look
-- freshly checked.
--
-- What IS new is the denominator a freshness claim would need. `dims_relied_on` counts the
-- facts the winning RULE reads, and a rule can win on the license alone while `data` and
-- `code` sit unconfirmed, so it can never support a whole-axis claim. `dims_recorded` counts
-- every declared dimension this product actually records, and
-- `all_recorded_dims_from_dataset` is the test docs/guides/verification.md step 2 asks for.
-- For openness it is expected to be false almost everywhere - `data` has no dataset route at
-- all - and that is the honest answer rather than a gap.
--
-- Operational note for whoever revises this next: a run materializes the latest RELEASED
-- revision, not the latest revision. Creating a revision changes nothing until
-- createDataModelRelease points at it. Three runs were spent concluding that dropping a
-- column had broken materialization, when the runs were still executing the previous release
-- and the new SQL had never executed at all.
WITH facts AS (
  SELECT * FROM currentai.scores.openness_facts
),
rules AS (
  SELECT category_slug, product_type, rule_index, is_otherwise, condition_key, condition_value,
         then_score, then_class
  FROM currentai.registry.category_scoring_rules
),

-- The roster and the wide fact view, in one aggregation ----------------------
-- Both come off the same grain, and computing them separately would mean two scans of the
-- facts table. This query is the second half of a model that had to be split at Trino's
-- 150-stage ceiling, so the same discipline applies here.
axis AS (
  SELECT
    product_slug,
    category_slug,
    MAX(product_type) AS product_type,
    MAX(ladder_product_type) AS ladder_type,
    BOOL_OR(is_deferred) AS is_deferred,
    MAX(deferral_reason) AS deferral_reason,
    ARRAY_JOIN(
      ARRAY_AGG(fact_key || '=' || COALESCE(NULLIF(fact_value, ''), '?') ORDER BY fact_key)
        FILTER (WHERE fact_key IS NOT NULL),
      '; '
    ) AS dimension_values,
    MAX(CASE WHEN fact_key = 'license_tier' THEN fact_value END) AS license_tier,
    MAX(CASE WHEN fact_key = 'license_tier' THEN fact_grade END) AS license_tier_grade,
    MAX(CASE WHEN fact_key = 'license_tier' THEN fact_input END) AS license_name,
    -- Whether this ladder asks about a license at all. The facts model emits the key only
    -- where a tier vocabulary exists, so this is the tier-free allowance, read rather than
    -- re-derived.
    BOOL_OR(fact_key = 'license_tier') AS asks_license,
    ARRAY_JOIN(ARRAY_AGG(fact_note ORDER BY fact_key) FILTER (WHERE fact_note IS NOT NULL), ' ')
      AS abstention_notes,
    COUNT(fact_key) AS dims_declared,
    COUNT_IF(is_recorded) AS dims_recorded,
    COUNT_IF(is_recorded AND fact_grade = 'dataset') AS dims_recorded_from_dataset
  FROM facts
  GROUP BY product_slug, category_slug
),

-- Walk the ordered rules, first match wins ----------------------------------
rule_size AS (
  SELECT category_slug, product_type, rule_index, COUNT(*) AS conditions_required
  FROM rules WHERE NOT is_otherwise
  GROUP BY category_slug, product_type, rule_index
),
rule_hits AS (
  SELECT
    f.product_slug,
    f.category_slug,
    f.ladder_product_type AS ladder_type,
    r.rule_index,
    COUNT(*) AS conditions_met
  FROM facts f
  JOIN rules r
    ON r.category_slug = f.category_slug
   AND r.product_type = f.ladder_product_type
   AND r.condition_key = f.fact_key
   AND r.condition_value = f.fact_value
  WHERE NOT r.is_otherwise
    AND NOT f.is_deferred
  GROUP BY f.product_slug, f.category_slug, f.ladder_product_type, r.rule_index
),
otherwise_rule AS (
  SELECT category_slug, product_type, MIN(rule_index) AS rule_index
  FROM rules WHERE is_otherwise
  GROUP BY category_slug, product_type
),
candidates AS (
  SELECT h.product_slug, h.category_slug, h.ladder_type, h.rule_index
  FROM rule_hits h
  JOIN rule_size s
    ON s.category_slug = h.category_slug
   AND s.product_type = h.ladder_type
   AND s.rule_index = h.rule_index
  WHERE h.conditions_met = s.conditions_required
  UNION ALL
  -- `otherwise` is a candidate for every product, and MIN below decides. Taking the
  -- minimum over conditional matches AND the otherwise index is what makes this
  -- faithful to apply_formula's ordered walk, in which any rule declared after an
  -- `otherwise` is unreachable.
  SELECT a.product_slug, a.category_slug, a.ladder_type, o.rule_index
  FROM axis a
  JOIN otherwise_rule o
    ON o.category_slug = a.category_slug
   AND o.product_type = a.ladder_type
  WHERE NOT a.is_deferred
),
winner AS (
  SELECT product_slug, category_slug, ladder_type, MIN(rule_index) AS rule_index
  FROM candidates
  GROUP BY product_slug, category_slug, ladder_type
),

-- The rungs a missing license tier actually stops --------------------------
-- `walk_formula`'s `blocked` return, ported. A rung blocks when it tests `license_tier`,
-- no tier resolved, and every OTHER condition it carries matches - meaning the walk has
-- arrived at a rung it can neither satisfy nor rule out, and first-match-wins forbids
-- stepping over it.
--
-- `other_conditions` counts a rung's non-license conditions; `conditions_met` from
-- `rule_hits` counts what this product matched. Those two can be compared directly here
-- because the license condition cannot contribute to `conditions_met` when no tier
-- resolved: the facts row carries a null `fact_value` and the equality join in `rule_hits`
-- drops it. A rung testing the license and nothing else has `other_conditions = 0` and
-- blocks unconditionally, which is right - there is nothing about it left to evaluate.
license_rules AS (
  SELECT category_slug, product_type, rule_index,
         COUNT_IF(condition_key <> 'license_tier') AS other_conditions
  FROM rules
  WHERE NOT is_otherwise
  GROUP BY category_slug, product_type, rule_index
  HAVING COUNT_IF(condition_key = 'license_tier') > 0
),
blocked AS (
  SELECT a.product_slug, a.category_slug, MIN(lr.rule_index) AS rule_index
  FROM axis a
  JOIN license_rules lr
    ON lr.category_slug = a.category_slug
   AND lr.product_type = a.ladder_type
  LEFT JOIN rule_hits h
    ON h.product_slug = a.product_slug
   AND h.category_slug = a.category_slug
   AND h.ladder_type = a.ladder_type
   AND h.rule_index = lr.rule_index
  WHERE NOT a.is_deferred
    AND a.asks_license
    AND COALESCE(NULLIF(a.license_tier, ''), NULL) IS NULL
    AND COALESCE(h.conditions_met, 0) = lr.other_conditions
  GROUP BY a.product_slug, a.category_slug
),
outcome AS (
  -- Every condition row of a rule carries the same then_score / then_class, so any
  -- aggregate picks it out.
  SELECT category_slug, product_type, rule_index,
         MAX(then_score) AS score, MAX(then_class) AS class
  FROM rules
  GROUP BY category_slug, product_type, rule_index
),

-- Which facts the winning rule actually rests on -----------------------------
deps AS (
  SELECT w.product_slug, w.category_slug, r.condition_key AS fact_key
  FROM winner w
  JOIN rules r
    ON r.category_slug = w.category_slug
   AND r.product_type = w.ladder_type
   AND r.rule_index = w.rule_index
  WHERE NOT r.is_otherwise
  UNION
  -- Reaching `otherwise` means every earlier rule was tested and failed, so the
  -- score rests on all of the facts, not on none of them.
  SELECT w.product_slug, w.category_slug, k.condition_key
  FROM winner w
  JOIN rules ro
    ON ro.category_slug = w.category_slug
   AND ro.product_type = w.ladder_type
   AND ro.rule_index = w.rule_index
   AND ro.is_otherwise
  JOIN (
    SELECT DISTINCT category_slug, product_type, condition_key
    FROM rules WHERE NOT is_otherwise
  ) k
    ON k.category_slug = w.category_slug
   AND k.product_type = w.ladder_type
),
verification AS (
  SELECT
    d.product_slug,
    d.category_slug,
    COUNT(*) AS dims_relied_on,
    COUNT_IF(f.fact_admitted) AS dims_sourced,
    COUNT_IF(f.fact_grade = 'dataset') AS dims_from_dataset,
    -- A CHECK EVENT: the last time this pipeline read any admitted evidence. Diagnostic
    -- only. The matching MIN used to be emitted as `freshness_floor` and is gone; see the
    -- header. Two dates that differ only in aggregate invite being mistaken for each
    -- other, and one of them has no legitimate consumer.
    MAX(CASE WHEN f.fact_admitted THEN f.fact_accessed END) AS newest_admitted_accessed,
    ARRAY_JOIN(
      ARRAY_AGG(d.fact_key ORDER BY d.fact_key) FILTER (WHERE NOT f.fact_admitted), ', '
    ) AS unsourced_dimensions
  FROM deps d
  JOIN facts f
    ON f.product_slug = d.product_slug
   AND f.category_slug = d.category_slug
   AND f.fact_key = d.fact_key
  GROUP BY d.product_slug, d.category_slug
)

SELECT
  a.product_slug,
  a.category_slug,
  a.product_type,
  -- Which ladder variant governed. '*' for the fifteen uniform categories, the product's own
  -- type where a category mixes them, null where none covers it.
  a.ladder_type AS ladder_product_type,
  a.is_deferred,
  CASE
    WHEN a.is_deferred OR a.ladder_type IS NULL THEN CAST(NULL AS BIGINT)
    -- The blocked rung is checked before the winner, and against its POSITION: a rung the
    -- walk could not evaluate only counts if the walk would have reached it first.
    WHEN b.rule_index IS NOT NULL AND (w.rule_index IS NULL OR b.rule_index < w.rule_index)
      THEN CAST(NULL AS BIGINT)
    WHEN w.rule_index IS NULL THEN CAST(NULL AS BIGINT)
    ELSE o.score
  END AS openness_score,
  CASE
    WHEN a.is_deferred OR a.ladder_type IS NULL THEN CAST(NULL AS VARCHAR)
    WHEN b.rule_index IS NOT NULL AND (w.rule_index IS NULL OR b.rule_index < w.rule_index)
      THEN CAST(NULL AS VARCHAR)
    WHEN w.rule_index IS NULL THEN CAST(NULL AS VARCHAR)
    ELSE o.class
  END AS openness_class,
  a.dimension_values,
  a.license_tier,
  a.license_tier_grade,
  w.rule_index AS winning_rule_index,
  v.dims_relied_on,
  v.dims_sourced,
  v.dims_from_dataset,
  a.dims_recorded,
  a.dims_recorded_from_dataset,
  a.dims_declared,
  -- The precondition for any tool that wants to write a date. False whenever a single
  -- recorded dimension rests on someone's reading of prose, which for openness is nearly
  -- always: `data` has no dataset route by declaration, not by omission.
  a.dims_recorded > 0 AND a.dims_recorded_from_dataset = a.dims_recorded
    AS all_recorded_dims_from_dataset,
  v.unsourced_dimensions,
  -- The CHECK EVENT, and the only date that belongs in sources/scores. The most recent
  -- date on which any admitted evidence behind this score was actually read - a document
  -- source's `accessed`, or a signal's fetch. Traceable by construction, because every
  -- contributing row carries its own source_url and date in the evidence store.
  v.newest_admitted_accessed AS last_checked,
  CASE
    WHEN a.is_deferred
      THEN 'the category defers this product: '
           || COALESCE(NULLIF(a.deferral_reason, ''), 'no reason recorded')
    WHEN a.ladder_type IS NULL
      THEN 'no ladder in this category covers product type '
           || COALESCE(NULLIF(a.product_type, ''), '<unrecorded>')
    -- Blocked outranks "no rule matched", mirroring check_rubric's `check_category`, which
    -- tests `blocked_on_tier` before it tests an empty result. The two are different
    -- findings with different owners: an unreadable license is a curation prompt, while an
    -- unmatched ladder is a rubric gap.
    WHEN b.rule_index IS NOT NULL AND (w.rule_index IS NULL OR b.rule_index < w.rule_index)
      THEN 'license ' || COALESCE('''' || a.license_name || '''', '<unrecorded>')
           || ' maps to no declared tier, and rule ' || CAST(b.rule_index AS VARCHAR)
           || ' - which the ladder reaches - tests one, so the rubric cannot score it'
    WHEN w.rule_index IS NULL
      THEN 'the recipe does not decide this product: no rule matched and it declares no '
           || 'otherwise [' || COALESCE(a.dimension_values, 'no evidence recorded') || ']'
    ELSE NULLIF(a.abstention_notes, '')
  END AS scoring_note
FROM axis a
LEFT JOIN winner w
  ON w.product_slug = a.product_slug AND w.category_slug = a.category_slug
LEFT JOIN blocked b
  ON b.product_slug = a.product_slug AND b.category_slug = a.category_slug
LEFT JOIN outcome o
  ON o.category_slug = w.category_slug
 AND o.product_type = w.ladder_type
 AND o.rule_index = w.rule_index
LEFT JOIN verification v
  ON v.product_slug = a.product_slug AND v.category_slug = a.category_slug
ORDER BY a.product_slug
