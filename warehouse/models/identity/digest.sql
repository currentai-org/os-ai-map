-- ────── PLATFORM MIRROR (read-only) ──────
-- A snapshot of a model that runs on the OSO platform to build one of the gap map's
-- tables. The platform is the source of truth; nothing deploys from this copy, and
-- editing it here changes nothing. See README.md and manifest.yaml in this folder.

-- currentai.identity.digest
--
-- Grain: one row per (sweep_week, item_id). item_id identifies a single reviewable claim drawn
-- from the three edge tables:
--   'membership:<artifact_kind>:<artifact_id>-><product_tier>:<product_slug>'
--   'equivalence:<candidate_key>-><product_tier>:<product_slug>'
--   'org:<candidate_key>-><org_slug>'
-- The relation prefix is load-bearing, not decoration: without it a membership item and an
-- equivalence item over the same artifact and product produce byte-identical item_ids, because
-- artifact_id and artifact_key are the same string for an already-lowercase repo. That collided
-- on 33 item_ids live (2026-09-04) and broke the stated grain.
-- Declared edges (method = ['declared'] or ['resolution_ledger']) are NOT reviewable claims -- a
-- human already wrote them down -- so this model excludes any item whose method set is entirely
-- made of those authoritative sources; it carries only the edges that still need a human look.
-- 'product_alias' is NOT on that list (reviewer ruling, 2026-09-04). It was, until the previous
-- pass capped it at 0.9 in identity_equivalence_edges.sql: the alias -> product half of the
-- mapping is declared by a curator, but the alias -> node half is a namespace-blind name match,
-- so `tiny-random/phi-4` earns the same alias edge as `microsoft/phi-4`. An edge that is not
-- scored as certain is a reviewable claim, so alias-only items now compete for the weekly cap
-- like any other; being alias-evidenced makes an item `active`-eligible (it is not
-- name-match-only), never parked.
--
-- Tier scope: identity_equivalence_edges.sql and identity_org_edges.sql now compute over
-- currentai.identity.artifact_nodes -- ALL tiers (head, tail, pool), not just undeclared pool
-- candidates -- per the reviewer ruling that the replay eval needs to compare edges against
-- artifacts humans already declared, not only against the undeclared pool. Both tables carry the
-- source artifact's tier as `candidate_tier`. This model still reviews pool-tier items only: a
-- head/tail artifact's equivalence or org relation is already established by the registry
-- declaration that put it in that tier, so it is not a reviewable claim here. `equivalence_items`
-- and `org_items` below both filter `candidate_tier = 'pool'`.
--
-- Shape follows the design's digest schema exactly: item_id, relation, sweep_week,
-- candidate_key, left and right as canonical (kind, id) pairs, confidence, method, evidence[],
-- penalties[], proposed_action, blast_radius, tiebreak, options, default_if_ignored.
--   relation      'membership' | 'equivalence' | 'org', matching item_kind above.
--   candidate_key <artifact_kind>:<artifact_key> of the artifact side (see identity_candidates.sql).
--   left          ROW(kind, id) for the artifact side: kind = artifact_kind, id = the declared
--                 artifact_id for membership items (artifact_identity_edges' grain), or the
--                 unprefixed folded artifact_key for equivalence/org items (those edge tables
--                 carry no declared spelling, only candidate_key).
--   right         ROW(kind, id) for the other side: ('product', product_slug) for membership and
--                 equivalence, ('org', org_slug) for org.
--   evidence      Per-item evidence strings, each `<url> | <excerpt>` -- a link a reviewer can
--                 open and a phrase saying what it says. The union of the contributing edges'
--                 own `evidence` arrays, distinct and sorted. Until 2026-09-04 this column was
--                 method[] verbatim, which told a reviewer the NAME of the inference and nothing
--                 they could check; the three edge tables now each emit a real evidence array
--                 (see their headers for the per-source shapes) and this model relays it.
--                 `method` is unchanged and still carries the method-name vocabulary.
--   proposed_action 'confirm_<relation>_edge' -- the single action this item's evidence points
--                 toward; `options` (below) is what a reviewer can actually choose.
--   options       ['confirm', 'reject', 'park'] for every relation today. No relation-specific
--                 vocabulary (e.g. a distinct 'mark_sku_of' for equivalence) is defined by the
--                 design brief, so this model does not invent one.
--   default_if_ignored always the literal 'no edge' -- an unreviewed item never gets promoted to
--                 an edge by default.
--
-- blast_radius (INTEGER, categorical, per reviewer ruling -- NOT downloads + stars):
--   3  the item is a membership edge, scoring_bearing = TRUE, product_tier = 'head'
--      (a ruling here would move a score or a band).
--   2  the item is an equivalence edge onto a head-tier product, OR the underlying candidate's
--      downloads_30d >= 1000, OR its stars >= 1000 (a promotion decision -- could move a stage).
--   1  otherwise.
-- tiebreak (BIGINT) = COALESCE(downloads_30d, 0) + COALESCE(stars, 0) on the underlying
--   artifact/candidate. BIGINT, not INTEGER (changed 2026-09-04). Both inputs are BIGINT columns
--   on currentai.identity.candidates and the sum is a raw download count: the live maximum is
--   246,135,287, already 11% of the INT32 range, so a corpus one order of magnitude larger turns
--   the cast into a hard run failure rather than a degraded value. It is no longer a ranking key
--   in this model (see the ranking note below) -- build/identity_digest.py still orders WITHIN a
--   rendered section by it.
--
-- Candidate context: downloads_30d, stars and first_seen are read from
-- currentai.identity.candidates by candidate_key -- for membership items, candidate_key is
-- derived by folding the artifact via currentai.identity.artifact_nodes (the same fold CASE
-- duplicated across this dataset; see identity_artifact_nodes.sql's `keyed` CTE).
--
-- NO FETCH TIMESTAMP FEEDS ANY STATE DECISION IN THIS MODEL (reviewer ruling, 2026-09-04).
-- currentai.identity.artifact_nodes.last_observed_at is a FETCH time -- the weekly run rewrites
-- it on every pass -- so deriving an evidence-change time from it made every row look changed
-- this week: `parked` became unreachable, all 25 review slots went to name-match-only items
-- labelled `resurfaced_evidence`, and every alias item sat in `pool`. That is the freshness rule
-- the repo already states (docs/guides/freshness.md): an evidence time is when the evidence was
-- confirmed, never when a fetcher last looked. Two consequences here:
--   * `last_evidence_change` is the resolution_ledger `decided_on` of a ruling naming this
--     candidate (the `ledger_change` CTE below, folded to candidate_key exactly as
--     identity_candidates.sql folds it), and NULL when no such ruling exists. It is NOT read from
--     currentai.identity.candidates.last_evidence_change, which is
--     GREATEST(node.last_observed_at, ledger) and so carries the fetch time inside it.
--   * name-match-only is decided from the ITEM's own `method` array, not from an aggregate over
--     the candidate. There is no candidate-level evidence-kind aggregation in this model any more
--     (currentai.identity.candidates.evidence_kinds is a permanently empty array -- it tried to
--     aggregate membership_edges' method vocabulary, but membership_edges reads
--     currentai.identity.candidates for its name_match evidence, a genuine cycle in the model
--     DAG). Per-item `method` answers the same question for a review decision -- what does THIS
--     claim rest on -- without the cycle, without the UNNEST-and-regroup over three edge tables,
--     and without any timestamp.
-- DEFERRED: the `evidence_changed` resurfacing reason. It needs an evidence-history table (per
-- (candidate_key, method) first-seen/last-confirmed rows) that does not exist; nothing reachable
-- today dates a piece of evidence rather than a fetch. Until it exists the only resurfacing
-- reason is 'age', and `resurfaced_reason` is NULL for every other row. Do not reinstate
-- 'evidence_changed' from a fetch column.
--
-- sweep_week = sweep_week_start = DATE_TRUNC('week', CURRENT_DATE) AS DATE. This model runs
-- weekly (Sunday 05:30 UTC, see docs/operations/deploy-models.md), so each run's CURRENT_DATE
-- lands in exactly one week.
--
-- NOTE for a future revision: identity_artifact_identity_edges.sql now carries a `candidate_tier`
-- column (revision 3, deployed 2026-09-03), so a future version of this model can join it
-- consistently with the other two edge tables. It is not read here yet.
--
-- state (no timestamp in this logic is a fetch time -- see the ruling above):
--   name_match_only  every element of the item's own `method` array is 'name_match'. The weakest
--               signal there is: a repo or Hub id whose name segment happens to equal a product
--               slug, with nothing else pointing at it. An item carrying any other method
--               (product_alias, model_family, org_handle, hf_namespace, homepage_domain,
--               resolution_ledger alongside another source) is NOT name-match-only.
--   parked      name_match_only AND first_seen >= sweep_week_start - 56 days. Recently discovered
--               and resting on a name collision alone: held out of the review queue, never
--               ranked, `rank` NULL.
--   resurfaced  name_match_only AND first_seen < sweep_week_start - 56 days, resurfaced_reason
--               'age'. It has sat in the pool for eight weeks or more, so it gets a look.
--               Competes for the same 25 weekly slots as `active`.
--   active      NOT name_match_only. Alias, model-family, handle, hf-namespace and ledger-backed
--               evidence all qualify. Ranked alongside `resurfaced` and capped at 25.
--   pool        an active- or resurfaced-eligible item that did not make the 25-slot cap this
--               week; overflow, not reviewed this sweep, `rank` NULL and resurfaced_reason NULL
--               (it did not actually resurface this week).
-- Ranking is GLOBAL; presentation is separate (reviewer ruling, 2026-09-04). The key, in order:
--   1. blast_radius DESC              (3 = a ruling moves a score)
--   2. urgency                        (resurfaced/age first, then plain active -- something that
--                                      has waited eight weeks outranks something new)
--   3. first_seen ASC                 (older first -- an item starved for weeks wins the tie)
--   4. relation priority              (equivalence, membership, org, artifact_identity)
--   5. confidence DESC
-- `tiebreak` (downloads + stars) is not a ranking key; it stays as an output column because
-- build/identity_digest.py orders WITHIN a rendered section by it.
--
-- Cap: 25 items per sweep_week, filled with a PER-RELATION RESERVATION (reviewer ruling,
-- 2026-09-04) rather than purely globally. A purely global cap let one relation and one evidence
-- class monopolize the whole queue -- the week the ranking went global, all 25 slots went to
-- membership items and the equivalence and org sections rendered zero. So:
--   1. the top 5 eligible items of EACH relation by the key above are taken first (fewer if a
--      relation has fewer than 5 eligible items -- there is no padding and no relation is owed a
--      slot it cannot fill), then
--   2. the remaining slots are filled by global order from what is left.
-- With three live relations the reservation claims at most 15 of the 25 slots, so global standing
-- still decides the majority of the queue. `rank` is the item's final position in the selected
-- set, 1..25, ordered by the global key -- NOT the pre-cap global order. A row outside the cap
-- (`pool`) and a `parked` row both get `rank` NULL: neither is being reviewed this week, and a
-- rank on an unreviewed row invited exactly the "rank means selected" misreading. Output is
-- ordered by the global key, parked rows last.
--
-- Output casts: explicit CAST on every output column (DATE sweep_week, VARCHAR strings, DOUBLE
-- confidence, ARRAY(VARCHAR) method/evidence/penalties/options, INTEGER blast_radius, BIGINT
-- tiebreak, INTEGER rank), matching the deploy pass's fix on the first four models. Date
-- arithmetic uses DATE_ADD('day', -N, sweep_week), not the `date - INTERVAL 'N' DAY` operator
-- form, and the result is cast to TIMESTAMP(6) before comparing against first_seen (TIMESTAMP(6)
-- throughout this dataset).

WITH sweep AS (
  SELECT CAST(DATE_TRUNC('week', CURRENT_DATE) AS DATE) AS sweep_week
),

-- The only evidence-DATED source this model can reach: a resolution_ledger ruling naming the
-- candidate. decided_on is the day a human decided, which is what an evidence time means. Folded
-- to candidate_key with the same CASE identity_candidates.sql and identity_equivalence_edges.sql
-- use (Trino has no shared macro, so it is intentionally duplicated, not re-derived
-- differently). MAX(CAST(decided_on AS TIMESTAMP(6))) matches identity_candidates.sql: decided_on
-- is a text column, every live value parses, and a malformed one should fail loudly rather than
-- become a silent NULL.
-- No fetch column appears here, and none may be added: see the header ruling.
ledger_change AS (
  SELECT
    artifact_kind || ':' ||
      CASE
        WHEN artifact_kind IN ('pypi', 'crates')
          THEN REGEXP_REPLACE(LOWER(artifact_id), '[-_.]+', '-')
        ELSE LOWER(artifact_id)
      END AS candidate_key,
    MAX(CAST(decided_on AS TIMESTAMP(6))) AS last_ruling_at
  FROM currentai.registry.resolution_ledger
  GROUP BY 1
),

membership_items AS (
  SELECT
    'membership' AS relation,
    -- The 'membership:' prefix is load-bearing, not decoration. Without it a membership item and
    -- an equivalence item over the same artifact and product produce byte-identical item_ids
    -- (artifact_id and artifact_key are the same string for an already-lowercase repo), which
    -- breaks this model's stated (sweep_week, item_id) grain -- 33 collisions live on 2026-09-04.
    'membership:' || m.artifact_kind || ':' || m.artifact_id || '->' || m.product_tier || ':'
      || m.product_slug AS item_id,
    n.artifact_kind || ':' || n.artifact_key AS candidate_key,
    CAST(ROW(m.artifact_kind, m.artifact_id) AS ROW(kind VARCHAR, id VARCHAR)) AS left_pair,
    CAST(ROW('product', m.product_slug) AS ROW(kind VARCHAR, id VARCHAR)) AS right_pair,
    m.confidence,
    m.method,
    CAST(ARRAY_SORT(ARRAY_DISTINCT(m.evidence)) AS ARRAY(VARCHAR)) AS evidence,
    m.penalties,
    'confirm_membership_edge' AS proposed_action,
    (m.scoring_bearing AND m.product_tier = 'head') AS is_blast_3,
    (m.product_tier = 'head') AS product_is_head,
    c.downloads_30d,
    c.stars,
    COALESCE(c.first_seen, DATE '1970-01-01') AS first_seen
  FROM currentai.identity.membership_edges m
  LEFT JOIN currentai.identity.artifact_nodes n
    ON n.artifact_kind = m.artifact_kind AND n.artifact_id = m.artifact_id
  LEFT JOIN currentai.identity.candidates c
    ON c.candidate_key = n.artifact_kind || ':' || n.artifact_key
  WHERE NOT (CARDINALITY(m.method) = 1 AND m.method[1] IN ('declared'))
),

equivalence_items AS (
  SELECT
    'equivalence' AS relation,
    'equivalence:' || e.candidate_key || '->' || e.product_tier || ':' || e.product_slug AS item_id,
    e.candidate_key,
    CAST(
      ROW(
        e.artifact_kind,
        COALESCE(c.artifact_key, SUBSTR(e.candidate_key, LENGTH(e.artifact_kind) + 2))
      ) AS ROW(kind VARCHAR, id VARCHAR)
    ) AS left_pair,
    CAST(ROW('product', e.product_slug) AS ROW(kind VARCHAR, id VARCHAR)) AS right_pair,
    e.confidence,
    e.method,
    CAST(ARRAY_SORT(ARRAY_DISTINCT(e.evidence)) AS ARRAY(VARCHAR)) AS evidence,
    e.penalties,
    'confirm_equivalence_edge' AS proposed_action,
    FALSE AS is_blast_3,
    (e.product_tier = 'head') AS product_is_head,
    c.downloads_30d,
    c.stars,
    COALESCE(c.first_seen, DATE '1970-01-01') AS first_seen
  FROM currentai.identity.equivalence_edges e
  LEFT JOIN currentai.identity.candidates c ON c.candidate_key = e.candidate_key
  -- 'product_alias' is deliberately NOT excluded here (reviewer ruling 2026-09-04): it is capped
  -- at 0.9, so it is not an authoritative declaration. See the header.
  WHERE e.candidate_tier = 'pool'
    AND NOT (
      CARDINALITY(e.method) = 1
      AND e.method[1] IN ('resolution_ledger')
    )
),

org_items AS (
  SELECT
    'org' AS relation,
    'org:' || o.candidate_key || '->' || o.org_slug AS item_id,
    o.candidate_key,
    CAST(
      ROW(
        o.artifact_kind,
        COALESCE(c.artifact_key, SUBSTR(o.candidate_key, LENGTH(o.artifact_kind) + 2))
      ) AS ROW(kind VARCHAR, id VARCHAR)
    ) AS left_pair,
    CAST(ROW('org', o.org_slug) AS ROW(kind VARCHAR, id VARCHAR)) AS right_pair,
    o.confidence,
    o.method,
    CAST(ARRAY_SORT(ARRAY_DISTINCT(o.evidence)) AS ARRAY(VARCHAR)) AS evidence,
    o.penalties,
    'confirm_org_edge' AS proposed_action,
    FALSE AS is_blast_3,
    FALSE AS product_is_head,
    c.downloads_30d,
    c.stars,
    COALESCE(c.first_seen, DATE '1970-01-01') AS first_seen
  -- org_edges has no 1.0 authoritative source in this plan (0.85/0.80/0.75 only), so the only
  -- filter here is the pool-tier restriction.
  FROM currentai.identity.org_edges o
  LEFT JOIN currentai.identity.candidates c ON c.candidate_key = o.candidate_key
  WHERE o.candidate_tier = 'pool'
),

current_items AS (
  SELECT * FROM membership_items
  UNION ALL
  SELECT * FROM equivalence_items
  UNION ALL
  SELECT * FROM org_items
),

scored AS (
  SELECT
    s.sweep_week,
    ci.relation,
    ci.item_id,
    ci.candidate_key,
    ci.left_pair,
    ci.right_pair,
    ci.confidence,
    ci.method,
    ci.evidence,
    ci.penalties,
    ci.proposed_action,
    CASE
      WHEN ci.is_blast_3 THEN 3
      WHEN (ci.relation = 'equivalence' AND ci.product_is_head)
        OR COALESCE(ci.downloads_30d, 0) >= 1000
        OR COALESCE(ci.stars, 0) >= 1000
        THEN 2
      ELSE 1
    END AS blast_radius,
    -- BIGINT, not INTEGER: the live max is already 11% of the INT32 range. See the header.
    CAST(COALESCE(ci.downloads_30d, 0) + COALESCE(ci.stars, 0) AS BIGINT) AS tiebreak,
    CAST(ARRAY['confirm', 'reject', 'park'] AS ARRAY(VARCHAR)) AS options,
    CAST('no edge' AS VARCHAR) AS default_if_ignored,
    CAST(ci.first_seen AS TIMESTAMP(6)) AS first_seen,
    -- Evidence time, not fetch time: the ledger ruling that named this candidate, or NULL when
    -- no ruling names it. See the header ruling -- do not COALESCE a fetch column in here.
    CAST(lc.last_ruling_at AS TIMESTAMP(6)) AS last_evidence_change
  FROM current_items ci
  CROSS JOIN sweep s
  LEFT JOIN ledger_change lc ON lc.candidate_key = ci.candidate_key
),

-- eight_weeks_ago via DATE_ADD (not the `date - INTERVAL` operator form) and cast to TIMESTAMP(6)
-- so it compares cleanly against first_seen, which is TIMESTAMP(6) throughout this dataset.
-- name-match-only is read off the item's OWN method array: every element is 'name_match'. FILTER
-- rather than `method = ARRAY['name_match']` so an item that somehow carries the same method
-- twice still reads as name-match-only, and the CARDINALITY > 0 guard keeps an item with an empty
-- method array (none live -- checked) out of the parked branch instead of into it.
thresholds AS (
  SELECT
    *,
    (
      CARDINALITY(method) > 0
      AND CARDINALITY(FILTER(method, m -> m <> 'name_match')) = 0
    ) AS is_name_match_only,
    CAST(DATE_ADD('day', -56, sweep_week) AS TIMESTAMP(6)) AS eight_weeks_ago
  FROM scored
),

pre_state AS (
  SELECT
    *,
    CASE
      WHEN NOT is_name_match_only THEN 'active_candidate'
      WHEN first_seen < eight_weeks_ago THEN 'resurfaced_age'
      ELSE 'parked'
    END AS pre_state_label
  FROM thresholds
),

-- Global ranking. Relation is the FOURTH key, not the first -- see the header on why the old
-- relation-first key starved every blast_radius = 3 membership item. The ordering CASEs are
-- factored out here so the window functions, the exposed `rank` column and the final ORDER BY
-- cannot drift apart. `parked_last` keeps parked rows out of the way of every ROW_NUMBER below
-- without a WHERE (they still have to appear in the output).
priorities AS (
  SELECT
    *,
    CASE WHEN pre_state_label = 'parked' THEN 1 ELSE 0 END AS parked_last,
    CASE pre_state_label
      WHEN 'resurfaced_age' THEN 0
      ELSE 1
    END AS urgency_rank,
    CASE relation
      WHEN 'equivalence' THEN 0
      WHEN 'membership' THEN 1
      WHEN 'org' THEN 2
      ELSE 3
    END AS relation_rank
  FROM pre_state
),

-- Two orderings over the eligible rows, on the identical key: the global standing, and the
-- standing within the row's own relation. The second is what the per-relation reservation reads.
orders AS (
  SELECT
    *,
    CASE
      WHEN pre_state_label <> 'parked' THEN
        ROW_NUMBER() OVER (
          PARTITION BY sweep_week
          ORDER BY
            parked_last,
            blast_radius DESC,
            urgency_rank,
            first_seen ASC,
            relation_rank,
            confidence DESC
        )
    END AS global_order,
    CASE
      WHEN pre_state_label <> 'parked' THEN
        ROW_NUMBER() OVER (
          PARTITION BY sweep_week, relation
          ORDER BY
            parked_last,
            blast_radius DESC,
            urgency_rank,
            first_seen ASC,
            relation_rank,
            confidence DESC
        )
    END AS relation_order
  FROM priorities
),

-- The cap, with the per-relation reservation. Each relation's top 5 eligible items are claimed
-- first (a relation with fewer than 5 claims fewer -- nothing is padded), and the rest of the 25
-- goes to global order. `slot_order <= 25` is therefore the selected set; it is NOT the item's
-- rank, because the reservation deliberately jumps items ahead of their global standing.
selection AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY sweep_week
      ORDER BY
        CASE WHEN global_order IS NULL THEN 1 ELSE 0 END,
        CASE WHEN relation_order <= 5 THEN 0 ELSE 1 END,
        global_order
    ) AS slot_order
  FROM orders
),

-- `rank` is the selected item's 1..25 position in GLOBAL order, so a reserved item that was
-- promoted into the cap still shows its true standing. The PARTITION BY on the selected flag is
-- what restarts the numbering at 1 inside the cap; rows outside it get NULL.
ranked AS (
  SELECT
    *,
    CASE
      WHEN global_order IS NOT NULL AND slot_order <= 25 THEN
        ROW_NUMBER() OVER (
          PARTITION BY
            sweep_week,
            CASE WHEN global_order IS NOT NULL AND slot_order <= 25 THEN 1 ELSE 0 END
          ORDER BY global_order
        )
    END AS final_rank
  FROM selection
)

SELECT
  CAST(sweep_week AS DATE) AS sweep_week,
  CAST(relation AS VARCHAR) AS relation,
  CAST(item_id AS VARCHAR) AS item_id,
  CAST(candidate_key AS VARCHAR) AS candidate_key,
  left_pair AS "left",
  right_pair AS "right",
  CAST(confidence AS DOUBLE) AS confidence,
  CAST(method AS ARRAY(VARCHAR)) AS method,
  CAST(evidence AS ARRAY(VARCHAR)) AS evidence,
  CAST(penalties AS ARRAY(VARCHAR)) AS penalties,
  CAST(proposed_action AS VARCHAR) AS proposed_action,
  CAST(blast_radius AS INTEGER) AS blast_radius,
  CAST(tiebreak AS BIGINT) AS tiebreak,
  options,
  default_if_ignored,
  first_seen,
  last_evidence_change,
  CAST(
    CASE
      WHEN pre_state_label = 'parked' THEN 'parked'
      WHEN final_rank IS NULL THEN 'pool'
      WHEN pre_state_label = 'resurfaced_age' THEN 'resurfaced'
      ELSE 'active'
    END AS VARCHAR
  ) AS state,
  -- 'age' is the only reason today: 'evidence_changed' is deferred until an evidence-history
  -- table exists (see the header). NULL on every row that is not a resurfaced item inside the cap.
  CAST(
    CASE
      WHEN final_rank IS NOT NULL AND pre_state_label = 'resurfaced_age' THEN 'age'
      ELSE CAST(NULL AS VARCHAR)
    END AS VARCHAR
  ) AS resurfaced_reason,
  -- Final position in this week's 25, 1 = most important, in global order. NULL for a parked row
  -- (never competed) and for a pool row (competed, missed the cap) -- neither is being reviewed
  -- this week, and a rank on an unreviewed row reads as if it were.
  CAST(final_rank AS INTEGER) AS "rank"
FROM ranked
ORDER BY
  parked_last,
  blast_radius DESC,
  urgency_rank,
  first_seen ASC,
  relation_rank,
  confidence DESC
