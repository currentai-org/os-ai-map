# Design: os-ai-map as a community hub

**Date**: 2026-06-10
**Status**: Approved
**Owner**: Carl

## Goal

Turn os-ai-map into a maintainable community resource for tracking the Open Source AI
Stack while preserving everything that already works: the curated four-concern registry
in `sources/`, the deterministic validate/serialize/render pipeline, the warehouse
models, the reference marimo notebook, and the editor skills.

## Decisions (settled)

| Question | Decision |
|---|---|
| Where does recurring automation live? | GitHub Actions: weekly fetcher crons + on-merge regeneration, committing via a bot. Warehouse static-model loads and notebook publish remain maintainer-MCP runbook steps. |
| How do community members contribute? | Direct YAML PRs for capable contributors, plus structured GitHub issue forms for everyone else; maintainers (or the add-product skill) convert issues to PRs. CI validates everything. |
| Where do indexer-discovered candidates land? | A committed queue file (`sources/queue/uncategorized.yaml`) updated by a weekly bot PR; curators triage in-repo. |
| Licensing | MIT for the whole repo (code + data). Decided 2026-06-11. |

## Architecture: three loops

All three loops anchor on the curated `sources/` tree.

1. **Human loop (PRs)**: contributors edit `sources/` YAML; CI validates; curators merge.
2. **Machine loop (weekly)**: Actions run fetchers, refresh `warehouse/catalog/` CSVs,
   and surface new uncategorized candidates into a committed queue for curator review.
3. **Build loop (on merge)**: Actions regenerate `build/notebook_data.json`, the
   notebook, and flat export tables. Generated artifacts are bot-owned, never
   hand-committed.

## Phase 0: Hygiene and launch prep (one PR)

- Delete one-time v2-to-v3 migration tooling: `build/convert.py`, `build/orgs.py`,
  `build/_make_registry_fixture.py`, `build/_registry_artifacts.json`,
  `tests/test_convert_roundtrip.py`, `tests/test_orgs.py`. Git history preserves them.
- Fix stale docs: `warehouse/models/README.md` references `data/` and `scripts/` paths
  that are actually `warehouse/catalog/` and `warehouse/ingest/`.
- Repo metadata: push `main` to `currentai-org/os-ai-map` (currently empty), update the
  GitHub description to reflect data + models (the app lives in `ecosystem-mapping`),
  add `.DS_Store` to `.gitignore`.
- License: MIT (decided 2026-06-11; LICENSE committed).
- **Full dataset refresh dry-run** (done 2026-06-10): every fetcher run end-to-end;
  refreshed `warehouse/catalog/` CSVs to be committed with this phase. Bugs found and
  fixed during the dry-run:
  - All six fetchers wrote to `warehouse/data/` (pre-migration path); now point at
    `warehouse/catalog/`.
  - `fetch_github_ai_repos.py` used `Path` without importing it (pre-existing crash).
  - `datasets` package used by `fetch_model_benchmarks.py` but undeclared; added to
    `pyproject.toml`.
  - Stale warehouse table names (`currentai.goodailist_repos.repos`,
    `currentai.ai_repo_activity.ai_repo_activity`) fixed to
    `currentai.catalog.goodailist_repos` / `currentai.entities.repos`.
  - Required secrets for the Phase 2 workflow: `OSO_API_KEY`, `HF_TOKEN`,
    `GITHUB_TOKEN`. Without `HF_TOKEN` the model link scan silently degrades
    (742 links -> 7) instead of failing; treat missing tokens as hard errors in CI.
  - Build loop verified idempotent: validate 0 errors, serialize 285 products, render
    byte-identical notebook, 18 tests pass, marimo check clean.

## Phase 1: Community scaffolding

- **CI on every PR** (`.github/workflows/validate.yml`): `uv sync`, `build.validate`
  (must print 0 errors), `pytest`, dry-run `serialize`. This is the trust backbone that
  makes community YAML edits safe to merge.
- **CONTRIBUTING.md**: plain-markdown recipes mirroring the skills (add a product, edit
  a category, update a score) so humans without Claude Code have a first-class path.
  Includes the data-model cheat sheet and slug rules.
- **Issue forms**: `suggest-a-product.yml` (name, org, category, artifact URLs, why it
  matters), `report-an-error.yml`, `propose-a-category.yml`.
- **PR template** with the validate checklist; **CODEOWNERS** routing
  `sources/categories/*` to category curators as that roster grows.
- **Generated-artifact policy**: `build/notebook_data.json` and
  `notebooks/ai-stack-map.py` become bot-owned. A `regenerate.yml` workflow on push to
  `main` re-runs serialize + render and commits the diff as a bot. CI fails PRs that
  hand-edit generated files. The `generated:` date becomes the workflow run date
  instead of a hardcoded constant.

## Phase 2: Scheduled data refresh

- **Weekly cron workflow** runs `warehouse/ingest/fetch_*.py` per the `refresh:`
  cadence declared in `warehouse/sources.yaml`, opening a bot PR that updates
  `warehouse/catalog/` CSVs. A maintainer merges; merge is the human checkpoint.
- **Dry-run learnings to bake into the workflow** (2026-06-10):
  - `fetch_github_orgs.py` scans ~10K owners against a 5,000/hr GitHub limit; it is
    resumable (skips owners already in `orgs.csv`) but needs either rate-limit-aware
    pacing (sleep until reset) or two scheduled passes per refresh.
  - Open LLM Leaderboard v2 is frozen upstream (refresh returns byte-identical data);
    capability scoring needs a successor benchmark source. Track as an open item.
  - `warehouse/catalog/github-orgs/orgs.csv` and
    `warehouse/catalog/goodailist/forked_ai_repos.csv` are produced by fetchers but
    not yet registered as warehouse static models; register or consciously exclude
    them in `warehouse/sources.yaml`.
- **Warehouse load stays a runbook step** (static-model upload + UDM trigger via MCP)
  with a noted follow-up to automate once an API-token path exists.
- Catalog CSV size: keep in git for now; revisit LFS/Releases if any single source
  crosses ~50MB (goodailist is ~20MB today).

## Phase 3: Indexer and uncategorized queue

- **New `build/queue.py`**: cross-references fetched catalogs (GoodAI List, Hugging
  Face, GitHub; PyPI/NPM later) against artifacts already claimed in
  `sources/products/`, scores candidates by adoption signal, and writes
  `sources/queue/uncategorized.yaml` (slug, evidence, suggested category) via the
  weekly bot PR.
- **Dismissals file** (`sources/queue/dismissed.yaml`, one reason per slug) so rejected
  candidates never resurface.
- **Retire the frozen fixtures**: `build/_frozen_long_tail.json` and
  `build/uncategorized.json` are replaced by a long-tail artifact derived from the live
  queue, making the notebook's long-tail section real instead of a snapshot.
- **Triage flow**: a curator promotes a candidate with the add-product recipe/skill or
  dismisses it with a reason. The queue doubles as a "what's new in open AI" feed.
- Fold what is still relevant from `docs/catalog-gaps.md` into the queue, then delete it.

## Phase 4: Power-data exports

- **New `build/export.py`**: emits flat, analyst-friendly tables regenerated by the
  on-merge workflow:
  - `exports/products.csv` (+ parquet): one row per product with org, category, arc,
    and all three scores joined.
  - `exports/registry.json`: the stable machine-readable master file for data apps.
- **Publish the registry to the warehouse** as a static model
  (`currentai.catalog.stack_map_products`) so the curated layer is queryable next to
  the activity metrics.

## Phase 5: Docs and ongoing quality

- **README rewrite** for a community audience: what the AI Stack Map is, the three
  loops, a contribution quick-start, architecture diagram.
- **Score-staleness report**: weekly job flags scores whose `accessed:` dates are older
  than 6 months, appended to the queue PR as a standing re-verification worklist.
- Skills stay in sync with CONTRIBUTING: skills are the agent path, CONTRIBUTING is the
  human path, same invariants.

## Deletions and deprecations

| Artifact | Action | Phase |
|---|---|---|
| `build/convert.py`, `build/orgs.py`, `build/_make_registry_fixture.py`, `build/_registry_artifacts.json` | Delete | 0 |
| `tests/test_convert_roundtrip.py`, `tests/test_orgs.py` | Delete | 0 |
| `warehouse/models/README.md` stale paths | Fix | 0 |
| `docs/catalog-gaps.md` | Fold into queue, then delete | 3 |
| `build/_frozen_long_tail.json`, `build/uncategorized.json` | Replace with derived queue artifact | 3 |
| Hand-committed `notebook_data.json` / notebook | Become bot-generated | 1 |

## Milestones

- **Phases 0-1**: the "ready to show off" milestone — safe to accept PRs.
- **Phases 2-3**: self-sustaining — data refreshes and candidate discovery run weekly.
- **Phases 4-5**: a data product — exports power external notebooks and apps.

## Open items

- **OSO write automation**: automating static-model upload and notebook publish from
  Actions depends on an API-token path; until then these remain maintainer runbooks.
- **Benchmark successor**: Open LLM Leaderboard v2 is frozen upstream; pick a successor
  capability source (e.g. LMArena, HELM, or per-category benchmarks).

## Error handling and testing

- CI validation is the primary error gate: schema + cross-file invariants on every PR.
- Bot PRs (fetcher refresh, queue updates) are never auto-merged; a maintainer merge is
  the human checkpoint.
- Existing pytest suite continues to cover build helpers; new modules (`queue.py`,
  `export.py`) ship with unit tests over fixture inputs.
- The regenerate workflow is idempotent: re-running on the same `sources/` tree
  produces an identical payload (already proven by the serializer round-trip work).
