# Changelog

All notable changes to this repository are recorded here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
What a MAJOR, MINOR, or PATCH bump means for a data-and-schema repo is spelled out in
`skills/publish-release/SKILL.md`; the `publish-release` skill cuts each release.

Record a change under `## [Unreleased]`, in the same PR that makes it, only when it is
**notable and user-facing** — a new or removed product, category, or data source; a schema or
scoring change; a new skill or workflow. Routine maintenance stays out: bot regenerations,
dependency bumps, internal refactors, and day-to-day evidence refreshes that do not move a
published score. Put each entry under the matching heading (Added, Changed, Deprecated,
Removed, Fixed, Security), one line, newest first, in plain past tense, with the PR linked.

## [Unreleased]

### Added

- `mirror.code_unchanged_from` in `warehouse/dependencies.yaml`: a marker letting a mirror contract
  record a platform revision that was minted over byte-identical code (a cron cleared, a
  description added), which the coherence gate would otherwise forbid forever. Accepted only when
  the marker names the revision committed at the merge base, the revision strictly advances, the
  mirrored bytes are unchanged and `synced_at` does not regress; setting it alongside changed bytes
  is itself a violation, so the next genuine resync deletes the line.
  `currentai.scores.openness_facts` (7 → 9),
  `currentai.scores.openness_computed` (15 → 17) and `currentai.signal_github.artifact_state`
  (2 → 3) now record the deployed revision (#365).

- `build/propose_org_handles.py`, which proposes `huggingface` org handles from the namespaces of
  already declared Hugging Face artifacts, grouped by org and checked for aggregator accounts and
  ownership conflicts, for review as a GitHub issue rather than seeded silently (#365).
- A weekly mirror-drift sentinel (`mirror-drift.yml`, Monday 08:30 UTC): every `mirror:` contract
  in `warehouse/dependencies.yaml` is compared against the platform's latest revision, and a red
  run is picked up by `report-failure.yml`, which opens or comments on the `sentinel` issue.
  Reports revision, hash, code, metadata-only and missing-model findings separately, and exits 2
  rather than passing whenever the platform cannot be read at all. A newer platform revision over
  byte-identical code is `metadata-only` and exits 0; a hash change at an unchanged revision
  number stays drift however well the code matches. Closes
  the gap where the repo's own gates stay green while the platform releases past a mirror; the
  first runs found eight of seventeen contracts behind. "Mirror resync" in
  `docs/operations/deploy-models.md` is the runbook (#365).
- `build/publish_neon.py` loads the serialized registry tables into Neon (Postgres) as the
  `gapmap` schema, so the front end can read the declarations at request time instead of going
  through the warehouse. It runs in `registry.yml` on every push to `main`, one step after the
  OSO publish, and requires the `NEON_DATABASE_URL` secret. The load is atomic: rows go into
  `gapmap_staging` and the cutover is three schema renames in one transaction, so a reader
  mid-request sees the whole old schema or the whole new one. A `gapmap.publish_runs` row
  records the commit, the declaration version and the per-table row counts of each load (#365).

- An explicit `reclaimed-as-dependency` transition in the externalization receipt, so a table that
  an in-scope governed asset starts reading again moves from externalized back into the governed
  dependency graph as a recorded event instead of an edited record. The disposition history is
  append-only (in-scope → externalized → reclaimed-as-dependency) and gated: the reclaim must name
  the prior entry, an in-repo reader that genuinely reads the table, and a dependency contract with
  a mirror block (#365).

### Fixed

- `homepage` artifact identity now keys on the full canonical URL (host and path), not the bare
  domain — two products sharing one company's domain at different paths are no longer treated as
  a collision. A shared domain is corroborating evidence of ownership, never proof of identity;
  it never establishes equivalence between two candidates and never suppresses a second one.
  `registry.tail_products` homepage rows now carry that full URL in `artifact_id` (#365).

### Added

- A weekly digest issue of low-confidence identity items (`identity-digest.yml`, Monday
  09:00 UTC): membership, equivalence, and org edges the identity graph could not auto-emit,
  capped at 25 a week, each with a pre-filled ledger entry ready to paste into
  `sources/resolution_ledger.yaml` once decided (#365).
- The digest renderer now reads the table's own `rank` and never re-sorts: items render in
  `currentai.identity.digest`'s rank order, grouped by relation for reading but each carrying
  its global rank, with a "Top 5 this week" summary at the top; `evidence` renders as linked
  bullets instead of bare method names, parked items collapse to a per-relation count, and the
  scorecard gets a fourth line breaking the ranked set down by relation (#365).
- Organization platform handles (`sources/org_handles.yaml`) and model release-name families
  (`sources/model_families.yaml`), published as `registry.org_handles` and
  `registry.model_families` — declared identity evidence for who owns which account and which
  release names bridge to which tier-level product (#474).
- Per-product `overall_score` and `tier` (`leading` for score ≥ 4.5, `strong` for
  4.0 ≤ score < 4.5, else `null`) fields, a `depth` category gap that fires at Stage 4, and a
  `descriptions.tiers` legend in the payload (#87, #318).
- `build/identity_eval.py`: replay eval that scores the `currentai.identity.*` edge tables
  against prior human decisions (the resolution ledger, declared artifacts, org rosters, and
  a known-negatives set), with precision/recall floors — checked only once a relation has at
  least 20 truth items — on the four relations automation is planned for, and two rules
  pinned as tests rather than metrics: a name-match edge never auto-emits (checked against
  `method` as an array, matching the deployed SQL) and a scoring-bearing membership edge
  never auto-emits regardless of confidence. Truth is built from DECLARED (head/tail)
  artifacts only, so `equivalence`, `org` and `artifact_identity` — sourced from every tier,
  head/tail/pool — split on their `candidate_tier` column: precision/recall are computed over
  the declared slice truth covers, and `n_emitted_at_threshold`/the review digest are
  computed over the pool slice automation would actually act on. Scheduled weekly as
  `identity-eval.yml`, which runs a fixture on every PR and
  `--from-warehouse --allow-unprovisioned` on schedule — the flag skips cleanly (exit 0) only
  on a genuine missing-table error (matched against Trino's own live wording, verified against
  `currentai.identity.equivalence_edges` while undeployed: a live `--from-warehouse` run now
  exits 0 as intended) while the identity dataset is undeployed, exits 2 on any other failure
  (auth, timeout, a missing column, an unrecognized `candidate_tier`/`product_tier` value),
  and refuses to run at all once `warehouse/assets.yaml` marks the dataset deployed (#365).

### Changed

- Dropped `--allow-unprovisioned` from the `identity-eval` and `identity-digest` workflows now
  that the identity dataset is deployed and contracted. Both modules refuse the flag once a
  `currentai.identity.*` contract with a `mirror` block exists, so a missing table is a real
  failure again rather than a green skip (#365).
- Split the labour between stage and gap text: a stage says where a category stands, a gap says
  what it needs. They render together in the category drawer, and written in one mood they
  restated each other — `depth` fires if and only if the stage is 4, so both sentences carried
  the same fact (#87, #321).
- Took the record's own scoring history out of score notes - "RE-BANDED 2026-08-14", "Class
  corrected from open_core on 2026-07-30", "LEVEL CORRECTED 3 -> 2". The reasoning behind each
  correction stays, in the present tense; the chronology goes to git, which already holds it with
  the diff and digests that produced it. A note may no longer state a date at all, enforced by
  `test_no_note_states_a_date_unless_it_is_a_product_fact` against a reviewed allowlist of 26 axes
  whose dates are facts about the product rather than about the reading (#322, #323).
- Rewrote the stage and gap definitions the payload carries — the text rendered in the site
  legend and category drawer. Stage 4 and the `depth` gap no longer define each other, the
  `adoption` gap no longer defines itself by its own threshold, and the `disclosure` gap no longer
  ships a repo path to the public payload. `docs/reference/gap-analysis.md` and
  `docs/methodology.md` now quote these definitions verbatim, with thresholds and assignment rules
  kept alongside rather than restated, and a test enforces the match (#87, #320).
- Split the `maturity` category gap into `depth` (Stage 4) and its `capability`/`adoption`
  drivers, which now fire together wherever both apply, and redefined the `adoption` gap
  independent of capability (#87, #318).
- `registry.tail_products` now includes homepage-bearing tail rows, previously silently dropped
  even though they validated (+27 rows; every one is a tail product that already declares
  another artifact kind, none homepage-only) (#472).
- Consolidated GitHub/PyPI/npm/crates/arXiv/Hugging Face artifact-identity canonicalization,
  previously duplicated and drifted across three modules, into one (#472).
- Brought all seven deployed `currentai.identity.*` models under repo governance (ADR-003):
  read-only mirrors under `warehouse/models/identity/`, plus dependency contracts pinning each
  model id, released revision and file hash, so `build/identity_eval.py`'s and
  `build/identity_digest.py`'s inputs are versioned, hashed and reviewable. Mirrored the three
  pool feeds (`signal_hfhub.model_universe`, `signal_openrouter.models`,
  `signal_goodailist.repo_catalog`) the same way, since the dependency gate requires a mirror
  for every `currentai.*` input a governed reader reaches (#365).
- Recorded `currentai.signal_goodailist.repo_catalog`'s return to the dependency graph as a
  `reclaimed-as-dependency` event in `warehouse/audits/externalization.json`: the identity
  graph's `artifact_nodes` model reads it, so it is contracted again while the original
  externalization entry stays byte-identical as history (#365).

### Deprecated

- The per-product `maturity` and `mature` keys, dual-published for one release so consumers can
  migrate before removal. Replacements: `maturity` → `overall_score`; `mature` →
  `tier == "leading"` and `openness.bucket == "open"` (#87, #318).

### Removed

- The `maturity` gap type (#87, #318).

### Fixed

- `registry.product_artifacts`'s `crates` `artifact_id` now serializes the bare crate name
  instead of the full crates.io URL (one row: `yomo`) (#472).
- The resolution ledger now keys a `product_membership` ruling on the product it names
  (`resolves_to`), not on the artifact alone. One package can legitimately be `member_of` one
  product's measurement and `not_member_of` another's — the loader used to raise
  `DuplicateResolution` on that legitimate case. `registry.resolution_ledger`'s grain moves to
  one row per `(artifact_kind, artifact_id, relation, resolves_to)` to match (#365).

## [0.2.0] - 2026-08-16

Grew and re-verified the corpus end to end, on top of a new evidence-based scoring pipeline.

### Added

- **One new category** (Dataset Processing Tools) and **85 products** — a net gain of 14
  after consolidation — bringing the map to **472 products across 16 categories** and 257
  organizations.
- **Scoring ladders:** a shared openness ladder for software across ten categories, shared
  ladders for datasets and hardware, per-product-type variants, and a single license scale
  used everywhere (#126, #129, #131, #137, #139).
- **An adoption measure** with per-product-type bands, declared scales, and readings backed
  by real usage signals (#171, #175, #176, #224, #227).
- **Evidence-based scoring:** openness scores are now computed from recorded evidence
  instead of being hand-authored — a machine-readable scoring rubric, an evidence store,
  and computed scores brought back into the repo for review (#98, #101, #102, #103, #108).
- **Automated verification checks** for verification-date support, source attribution and
  digests, sampled refetch reproducibility, and score reproduction from the declared rubrics
  (#127, #128, #134, #136, #148).
- **Structured openness and license records,** converted across the whole corpus, with each
  license part recorded as its own piece of evidence (#185, #186, #191–#198, #216, #217).
- **A routing table** naming the authoritative source for each scoring dimension (#103),
  and freshness reporting behind a 30-day refresh window (#102, #162, #267).
- **Artifact tooling:** an arXiv artifact type, a tool that proposes candidate artifacts,
  and a check that declared artifacts resolve to what they claim (#100, #104, #165, #170).
- **Skills:** `refresh-category` and `refresh-all-categories` to drive the re-verification
  pass (#158).

### Changed

- **Re-verified all 472 products** against named, reopenable evidence, preferring primary
  sources where available — 385 product records and their scores updated — and edited all 15
  existing categories.
- **Made product descriptions neutral** rather than marketing copy, under one standard for
  the description and comments fields (#147, #222).
- **Consolidated closed-model point releases** into the tier the vendor sells and fixed each
  product's identifier so it stays stable; alternate names now live on the records they
  identify (#114, #121, #157).
- **Reorganized the docs** into five task-based workflows over a shared reference layer, with
  a check that keeps them consistent and a skill registry (#269, #271, #274).
- **Added a read-only copy** of the scoring and signal models that run on the OSO platform,
  so they can be read from this repo (#272).

### Removed

- **Retired or consolidated 71 product entries** — collapsing point releases into vendor
  tiers and dropping projects that were renamed or shut down.
- Replaced the frozen GoodAI List CSV with a live data feed, and removed warehouse CSV files
  that nothing used (#110, #309).
- Removed an openness class the schema forbids, obsolete prose-cleanup tooling, historical
  snapshots, and dead build code (#178, #179, #306, #310).

### Fixed

- Corrected score, license, and adoption records against reachable evidence across the
  corpus (#204, #215, #226, #255, #260).
- Dated each score file from its last content change, not its last file touch (#190).
- Stopped the score-import step from overwriting the "last verified" date through a stale
  cache, and reverted the dates it had written (#115, #124).
- Reconciled the verification tracking file and restored nine deferred items (#301).

## [0.1.0] - 2026-07-01

Initial release: the first full snapshot of the AI Stack Map corpus, at the start of July —
**458 products across 15 categories**, from **249 organizations**, each scored on openness,
adoption, and capability. Tagged at commit `2e9d6eb`.

[unreleased]: https://github.com/currentai-org/os-ai-map/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/currentai-org/os-ai-map/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/currentai-org/os-ai-map/releases/tag/v0.1.0
