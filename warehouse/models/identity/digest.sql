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
-- evidence_kinds and last_evidence_change are NOT read from currentai.identity.candidates.
-- candidates.evidence_kinds tried to aggregate membership_edges' method vocabulary, but
-- membership_edges' name_match evidence itself reads currentai.identity.candidates -- a genuine
-- cycle in the model DAG (candidates -> membership_edges -> candidates), so the platform can
-- never resolve it and candidates.evidence_kinds is deployed as a permanently empty array. This
-- model breaks the cycle on the read side: it aggregates the method vocabulary itself, straight
-- from the three edge tables it already joins (membership_edges, equivalence_edges, org_edges),
-- in the `candidate_evidence` CTE below -- no read of currentai.identity.digest's own prior
-- output either, so no model in this dataset reads its own prior materialization.
-- last_evidence_change is the MAX of whatever per-edge timestamp this model can reach (today:
-- only currentai.identity.artifact_nodes.last_observed_at, reachable for membership items via
-- the same fold-join used for candidate_key -- equivalence and org items have no edge-reachable
-- timestamp today), falling back to the candidate's own last_evidence_change (computed in
-- identity_candidates.sql from first_seen and the resolution_ledger, which is NOT part of this
-- cycle) when nothing edge-side is reachable.
--
-- sweep_week = sweep_week_start = DATE_TRUNC('week', CURRENT_DATE) AS DATE. This model runs
-- weekly (Sunday 05:30 UTC, see docs/operations/deploy-models.md), so each run's CURRENT_DATE
-- lands in exactly one week.
--
-- NOTE for a future revision: identity_artifact_identity_edges.sql now carries a `candidate_tier`
-- column (revision 3, deployed 2026-09-03), so a future version of this model can join it
-- consistently with the other two edge tables. It is not read here yet.
--
-- state:
--   parked      evidence_kinds = ARRAY['name_match'] (the weakest signal -- no other evidence has
--               ever attached to this candidate) AND last_evidence_change is more than 7 days
--               old AND first_seen is less than 56 days old. Held back from the review queue.
--   resurfaced  name-match-only, but EITHER first_seen >= 56 days ago (resurfaced_reason =
--               'age') OR last_evidence_change is within the last 7 days (resurfaced_reason =
--               'evidence_changed'). Competes for the same 25 weekly slots as `active`.
--   active      not name-match-only (or has no candidate context to test); ranked alongside
--               `resurfaced` items and capped at 25 rows per sweep_week.
--   pool        an active- or resurfaced-eligible item that ranked beyond the top 25 this week;
--               overflow, not reviewed this sweep. resurfaced_reason is NULL for a pool row even
--               if it was resurfaced-eligible pre-cap -- it did not actually resurface this week.
-- Ranking is GLOBAL; presentation is separate (reviewer ruling, 2026-09-04). The old key led
-- with `CASE relation WHEN 'equivalence' THEN 0 ELSE 1 END`, which handed all 25 slots to
-- equivalence items and starved every blast_radius = 3 membership item -- the only items that
-- can move a score -- behind them. Relation is now the fourth key, not the first, so the cap
-- selects the 25 most important items in the whole sweep regardless of relation:
--   1. blast_radius DESC              (3 = a ruling moves a score)
--   2. resurfacing urgency DESC       (resurfaced/evidence_changed, then resurfaced/age, then
--                                      plain active -- something that changed outranks something
--                                      that merely aged, which outranks something new)
--   3. first_seen ASC                 (older first -- an item starved for weeks wins the tie)
--   4. relation priority              (equivalence, membership, org, artifact_identity)
--   5. confidence DESC
-- `tiebreak` (downloads + stars) is no longer a ranking key; it stays as an output column
-- because build/identity_digest.py orders WITHIN a rendered section by it.
-- Cap: ROW_NUMBER() OVER (PARTITION BY sweep_week ORDER BY <the five keys above>) among state IN
-- ('active', 'resurfaced')-eligible rows; rank <= 25 keeps its state, rank > 25 becomes 'pool'.
-- That row number is exposed as the `rank` column (INTEGER, 1 = most important) so a renderer
-- can group by relation for display and still show, or re-sort by, the global standing. A parked
-- row never competed for a slot, so its `rank` is NULL; a `pool` row carries its real rank,
-- which is > 25 by definition. Output is ordered by the same key.
--
-- Output casts: explicit CAST on every output column (DATE sweep_week, VARCHAR strings, DOUBLE
-- confidence, ARRAY(VARCHAR) method/evidence/penalties/options, INTEGER blast_radius, BIGINT
-- tiebreak, INTEGER rank), matching the deploy pass's fix on the first four models. Date
-- arithmetic uses DATE_ADD('day', -N, sweep_week), not the `date - INTERVAL 'N' DAY` operator
-- form, and the result is cast to TIMESTAMP(6) before comparing against
-- first_seen/last_evidence_change (both TIMESTAMP(6)).

WITH sweep AS (
  SELECT CAST(DATE_TRUNC('week', CURRENT_DATE) AS DATE) AS sweep_week
),

-- Method vocabulary and reachable evidence timestamp per candidate_key, aggregated straight from
-- the three edge tables (no read of currentai.identity.candidates.evidence_kinds, which is a
-- permanently empty array -- see the header note above on why). This is the cycle-free
-- replacement for the aggregation candidates.sql used to do.
membership_evidence AS (
  SELECT
    n.artifact_kind || ':' || n.artifact_key AS candidate_key,
    meth AS method,
    n.last_observed_at AS evidence_ts
  FROM currentai.identity.membership_edges m
  JOIN currentai.identity.artifact_nodes n
    ON n.artifact_kind = m.artifact_kind AND CONTAINS(n.also_seen_as, m.artifact_id)
  CROSS JOIN UNNEST(m.method) AS t(meth)
),

equivalence_evidence AS (
  SELECT
    e.candidate_key,
    meth AS method,
    CAST(NULL AS TIMESTAMP(6)) AS evidence_ts
  FROM currentai.identity.equivalence_edges e
  CROSS JOIN UNNEST(e.method) AS t(meth)
),

org_evidence AS (
  SELECT
    o.candidate_key,
    meth AS method,
    CAST(NULL AS TIMESTAMP(6)) AS evidence_ts
  FROM currentai.identity.org_edges o
  CROSS JOIN UNNEST(o.method) AS t(meth)
),

candidate_evidence AS (
  SELECT
    candidate_key,
    CAST(ARRAY_SORT(ARRAY_DISTINCT(ARRAY_AGG(method))) AS ARRAY(VARCHAR)) AS evidence_kinds,
    MAX(evidence_ts) AS max_edge_ts
  FROM (
    SELECT * FROM membership_evidence
    UNION ALL
    SELECT * FROM equivalence_evidence
    UNION ALL
    SELECT * FROM org_evidence
  )
  GROUP BY candidate_key
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
    COALESCE(c.first_seen, DATE '1970-01-01') AS first_seen,
    COALESCE(c.last_evidence_change, TIMESTAMP '1970-01-01') AS candidate_last_evidence_change
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
    COALESCE(c.first_seen, DATE '1970-01-01') AS first_seen,
    COALESCE(c.last_evidence_change, TIMESTAMP '1970-01-01') AS candidate_last_evidence_change
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
    COALESCE(c.first_seen, DATE '1970-01-01') AS first_seen,
    COALESCE(c.last_evidence_change, TIMESTAMP '1970-01-01') AS candidate_last_evidence_change
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
    CAST(COALESCE(ce.max_edge_ts, ci.candidate_last_evidence_change) AS TIMESTAMP(6))
      AS last_evidence_change,
    COALESCE(ce.evidence_kinds, ci.method) AS evidence_kinds
  FROM current_items ci
  CROSS JOIN sweep s
  LEFT JOIN candidate_evidence ce ON ce.candidate_key = ci.candidate_key
),

-- week_ago / eight_weeks_ago via DATE_ADD (not the `date - INTERVAL` operator form) and cast to
-- TIMESTAMP(6) so they compare cleanly against last_evidence_change/first_seen (both TIMESTAMP(6)
-- throughout this dataset).
thresholds AS (
  SELECT
    *,
    (evidence_kinds = ARRAY['name_match']) AS is_name_match_only,
    CAST(DATE_ADD('day', -7, sweep_week) AS TIMESTAMP(6)) AS week_ago,
    CAST(DATE_ADD('day', -56, sweep_week) AS TIMESTAMP(6)) AS eight_weeks_ago
  FROM scored
),

pre_state AS (
  SELECT
    *,
    CASE
      WHEN NOT is_name_match_only THEN 'active_candidate'
      WHEN first_seen <= eight_weeks_ago THEN 'resurfaced_age'
      WHEN last_evidence_change >= week_ago THEN 'resurfaced_evidence'
      ELSE 'parked'
    END AS pre_state_label
  FROM thresholds
),

-- Global ranking. Relation is the FOURTH key, not the first -- see the header on why the old
-- relation-first key starved every blast_radius = 3 membership item. The two ordering CASEs are
-- factored out here so the window function, the exposed `rank` column and the final ORDER BY
-- cannot drift apart.
priorities AS (
  SELECT
    *,
    CASE pre_state_label
      WHEN 'resurfaced_evidence' THEN 0
      WHEN 'resurfaced_age' THEN 1
      ELSE 2
    END AS urgency_rank,
    CASE relation
      WHEN 'equivalence' THEN 0
      WHEN 'membership' THEN 1
      WHEN 'org' THEN 2
      ELSE 3
    END AS relation_rank
  FROM pre_state
),

ranked AS (
  SELECT
    *,
    CASE
      WHEN pre_state_label <> 'parked' THEN
        ROW_NUMBER() OVER (
          PARTITION BY sweep_week
          ORDER BY
            blast_radius DESC,
            urgency_rank,
            first_seen ASC,
            relation_rank,
            confidence DESC
        )
    END AS eligible_rank
  FROM priorities
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
      WHEN eligible_rank <= 25 AND pre_state_label = 'active_candidate' THEN 'active'
      WHEN eligible_rank <= 25 THEN 'resurfaced'
      ELSE 'pool'
    END AS VARCHAR
  ) AS state,
  CAST(
    CASE
      WHEN eligible_rank <= 25 AND pre_state_label = 'resurfaced_age' THEN 'age'
      WHEN eligible_rank <= 25 AND pre_state_label = 'resurfaced_evidence' THEN 'evidence_changed'
      ELSE CAST(NULL AS VARCHAR)
    END AS VARCHAR
  ) AS resurfaced_reason,
  -- Global standing, 1 = most important. NULL for a parked row, which never competed for a
  -- slot; > 25 for a pool row. Exposed so a renderer can group by relation for display without
  -- losing the ranking the cap was actually decided on.
  CAST(eligible_rank AS INTEGER) AS "rank"
FROM ranked
ORDER BY
  blast_radius DESC,
  urgency_rank,
  first_seen ASC,
  relation_rank,
  confidence DESC
