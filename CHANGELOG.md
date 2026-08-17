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

- Per-product `overall_score` and `tier` (`leading` for score ≥ 4.5, `strong` for
  4.0 ≤ score < 4.5, else `null`) fields, a `depth` category gap that fires at Stage 4, and a
  `descriptions.tiers` legend in the payload (#87, #318).

### Changed

- Rewrote the stage and gap definitions the payload carries — the text rendered in the site
  legend and category drawer. Stage 4 and the `depth` gap no longer define each other, the
  `adoption` gap no longer defines itself by its own threshold, and the `disclosure` gap no longer
  ships a repo path to the public payload. `docs/reference/gap-analysis.md` and
  `docs/methodology.md` now quote these definitions verbatim, with thresholds and assignment rules
  kept alongside rather than restated, and a test enforces the match (#87, #320).
- Split the `maturity` category gap into `depth` (Stage 4) and its `capability`/`adoption`
  drivers, which now fire together wherever both apply, and redefined the `adoption` gap
  independent of capability (#87, #318).

### Deprecated

- The per-product `maturity` and `mature` keys, dual-published for one release so consumers can
  migrate before removal. Replacements: `maturity` → `overall_score`; `mature` →
  `tier == "leading"` and `openness.bucket == "open"` (#87, #318).

### Removed

- The `maturity` gap type (#87, #318).

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
