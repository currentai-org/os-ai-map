# AGENTS.md

This file provides guidance to coding agents and assistants when working in this repository.

## Project Overview

`os-ai-map` is the public data + modeling home behind the AI Stack Map. It holds curated
YAML (`sources/`), warehouse SQL and fetchers (`warehouse/`), a deterministic build
pipeline (`build/`), and the published notebook (`notebooks/`).

There is no front-end in this repo. The website lives in the `aipotluck.org` monorepo
(`currentai-org/aipotluck.org`), which *consumes* this data and does not regenerate it.
The older `os-ai-visualization` repo is retired; it still receives bot data-sync PRs, so
activity there is not a signal of real work.

## Directory map

```
sources/               Curated YAML: organizations, categories, head products, scores, tail registry
sources/taxonomy.yaml  Arc grouping + cross-category display order
sources/allowlists/    Draining allowlists. undigested_sources.txt grandfathers the sources
                       cited before the digest discipline; anything NOT listed must carry a
                       content_sha256, and a line that stops describing an undigested source
                       fails, so the list cannot rot into a permanent exemption.
sources/snapshots/     Hand-frozen inputs to the build. long_tail.json carries the dedup
                       counts and is the fifth file a product add touches (gated by validate).
sources/verification_queue.yaml  Axes deliberately held: a value whose evidence contradicts
                       it carries no date and sits here with a reason instead.
sources/signal_routing.yaml  Which machine signal is authoritative per dimension, and
                       which values mean "this source has no answer" (abstain_values)
sources/evidence_policy.yaml  When an observation is admissible as evidence
sources/rubrics/       Shared scoring ladders. A category inherits one with
                       `scoring_recipe: {extends: <name>}` rather than copying it;
                       or, for a category whose products don't all climb the same
                       ladder, `{extends: {<product type>: <name>, ...}}` (safeguards
                       is the example). build/rubrics.py resolves either form.
                       license-to-tier lives here, because whether AGPL is `osi` is
                       a fact about AGPL, not about one category.
warehouse/platform-mirror/  Read-only COPY of the models that run on the OSO platform to
                       build the gap map's data (evidence, openness scores, signals), with a
                       provenance manifest. Source of truth is the platform; nothing deploys from here.
warehouse/models/      SQL for the legacy entities/events/metrics/scores layer (in-repo)
warehouse/ingest/      Python fetchers that write CSVs to warehouse/catalog/
warehouse/catalog/     Raw external CSVs (HF model catalog, benchmarks, stack-map bridge)
warehouse/sources.yaml Manifest: each external source declares EITHER a fetcher
                       (writes a CSV) or an ingested_by (a UDM reads it directly)
build/                 Python pipeline, see below
notebooks/             Generated ai-stack-map.py and standalone companion notebooks (pypi-geo-trends, oss-ai-trends, long-tail-explorer)
docs/methodology.md    Canonical methodology copy, rendered into the notebook (a build input)
docs/README.md         Task router: which workflow/skill for which change
docs/workflows/        Task-oriented how-to, one per contributor intent
docs/reference/        Concepts + normative rules (openness, adoption, capability,
                       identity, evidence-and-freshness, gap-analysis, queries, notebook-design)
docs/operations/       Maintainer deploy/publish runbooks
docs/schemas/          JSON Schemas for the source files (four concerns + taxonomy)
skills/                Agent skills for common editor workflows
tests/                 pytest suite for build helpers and serializer behavior
```

### What is in `build/`

This section maps the stages; it is not an inventory. An earlier version claimed to be
complete, named a count, and was wrong within a fortnight.

Every module carries a docstring explaining why it exists, and that docstring is the
authority. **The ones that are CLIs answer `uv run python -m build.<module> --help`** — the
pipeline stages, the gates, the proposers, `sweep_status`, `fetch_source`, `product_prose`.
The shared helpers are code APIs rather than commands and answer nothing: `vocabulary`,
`rubrics`, `warehouse`, `components`, `freshness_payload`. Read their docstrings.

```
Notebook build     validate -> serialize -> render, plus freshness_payload and update_readme.
                   sources/ in, build/notebook_data.json and notebooks/ai-stack-map.py out.

Config bridge out  serialize_registry, serialize_rubric, publish_registry.
                   Identity and rubric tables, pushed to OSO as static models.

Scores back in     apply_scores. Reads computed openness score and class from OSO and writes
                   nothing else. The ONLY inbound data path, and it writes no dates.

Editing library    components, the only supported way to edit openness.components in place.
                   Never load-modify-dump a corpus file.

Gates              check_*, one module per question. Four families:
                     scoring    check_rubric, check_recipe, check_capability, check_adoption,
                                check_instrument, check_components
                     evidence   check_verification, check_freshness, check_refetch
                     payload    check_payload, check_retirement, check_parity
                     coverage   check_routing, check_artifacts
                   `check_verification` runs several sub-gates and its exit covers all of
                   them. A line a gate prints but does not exit on is marked `~` with a
                   written reason; anything else printed is a failure.

Shared helpers     vocabulary (the one owner of any vocabulary two modules need), rubrics,
                   warehouse (the only supported way to read OSO), fetch_source,
                   product_prose, sweep_status.

Proposers          propose_arxiv, propose_artifacts.
```

Proposers deliberately **print rather than write**. Matching artifacts by name measured 2
correct in 10 on this data, and a wrong artifact attaches another project's license and
downloads to a product, which is indistinguishable from a real score until someone checks.

### One fact, one owner

The rule that cost this repo four defects in a fortnight, none of which failed loudly:

> **A vocabulary with a declarative owner is derived from it, never copied.** Where a literal
> genuinely differs from its source, write the difference down and test it, so it stays a
> decision instead of becoming drift.

Each of the four reported success over a *narrower* question than the one it claimed to
answer — five sources checked where the table declared seven, a date validated by shape so
`2026-99-99` passed. `build/vocabulary.py` owns the derivations;
`tests/test_vocabulary_siblings.py` enforces them by AST and by calling the code, never by
matching source text. `docs/reference/sibling-invariants.md` has the case-by-case record,
including the copies that are deliberately kept and why.

## Data model

The curated source set is four full-record YAML concerns in `sources/`, a compact tail
registry, plus the single `sources/taxonomy.yaml` manifest:

- **organizations**: one file per org (`name`=slug, `display_name`, `type`, `homepage`,
  optional `github` typed-url array and `comments` string). Owns the `products:` roster: a list of product slugs that belong to this org. A product
  slug must appear in exactly one org roster (validated).
- **categories**: one file per stack-map category (`name`=slug, `display_name`). Owns the
  ordered product roster (`products:` array). Order equals display order. One product
  appears in exactly one category. Category files no longer carry `arc` or cross-category
  `order`. Optional `comments` string for curator notes.
- **products**: one file per product. `name` is the slug (kebab-case); `display_name` is
  the human label. Products do NOT carry an `org:` field; org membership is declared in
  the org file. No `flags` field; flag-style judgments are left to analyst downstream
  business logic. Open artifacts are declared as typed top-level arrays of `{url: ...}`
  objects: `github`, `npm`, `pypi`, `crates`, `go`, `huggingface_model`,
  `huggingface_dataset`, `arxiv`. Only keys with entries are included; `product.schema.json`
  is the authoritative list. Four further optional keys are not artifacts and are documented
  in the schema: `aliases`, `lineage`, `version_in_identity`, `artifact_exceptions`. Optional
  `comments` is a free-text string for provenance and scoring notes (version, license, last
  release date).
- **scores**: one file per product (same slug) with `openness`, `adoption`, `capability`.
  Every non-null score value requires a `sources:` citation entry.
- **registry**: one file per category with compact signal-only tail products. Each row owns
  a stable slug, display name, product type, organization slug, and addressable artifact IDs.
  Tail rows carry no editorial scores and need no organization file; they are exported to
  OSO but excluded from the public scored map until promoted to the full records above.
- **taxonomy.yaml**: owns arc grouping + cross-category display order. The three arcs
  ARE the Columbia openness-ontology layers (`product_ux`, `model_components`,
  `infrastructure`); each arc declares its `layer` slug and an ordered category list.
  `serialize.py` derives order, the display `arc`, and the machine `layer` from here, so
  a category's layer is never a separate hand-maintained field -- it is whichever arc the
  category sits in. A mapping entry may also declare `status: preliminary | published`;
  historical scalar entries mean published. Preliminary categories are registry-visible but
  omitted from the notebook payload. Validate enforces that every category appears in exactly
  one arc and that every arc declares a valid layer.

Category slugs are underscore form (`base_pretrained`). Product and org slugs are
hyphenated kebab-case (`llama-3-1`).

## Build pipeline

```bash
uv run python -m build.validate        # validate sources/ (must print "0 error(s)")
uv run python -m build.serialize       # sources/ -> build/notebook_data.json
uv run python -m build.render          # -> notebooks/ai-stack-map.py
uv run marimo export html notebooks/ai-stack-map.py -o /tmp/preview.html
```

Serialize/render locally for preview only. Do not commit `build/notebook_data.json` or
`notebooks/ai-stack-map.py`: a bot regenerates them on merge to main, and CI blocks PRs
that hand-edit them.

### Layer-2: scores computed from evidence, not authored

The repo declares; OSO computes; a PR brings the result back for review. The test of this
working is not "is the data fresh" — it is **did a score change without anyone hand-writing
it?**

```bash
# Out: rubric and recorded evidence -> registry static models on OSO
uv run python -m build.serialize_rubric --check    # CI gate
uv run python -m build.serialize_rubric && uv run python -m build.publish_registry

# In: computed scores -> sources/scores/
uv run python -m build.apply_scores --check        # exits non-zero if a score moved
uv run python -m build.apply_scores
```

Between those two halves sit three warehouse models, all plain Trino SQL:
`currentai.evidence.product_evidence` (graded observations),
`currentai.scores.openness_facts` (one resolved fact per dimension a ladder declares) and
`currentai.scores.openness_computed` (the ordered-rule walk from `check_rubric.py`).
Their SQL lives outside this repo, with the maintainer's UDM sources.

None of the three carries a cron, so publishing the registry is only half a refresh: the
user models recompute when something asks them to, in that order. `check_parity` is what
tells you whether what the warehouse published still matches what the repo computes, and it
is a per-product comparison because every drift this project has shipped was invisible to a
count.

Three rules worth knowing before editing any of it:

- **Evidence is graded by re-derivability, never by author.** `dataset` means a named field
  in a machine-readable source; `document` means a URL whose content asserts the value. The
  first pass of `sources/scores/` was agent-authored, so who wrote a value says nothing
  about whether anyone can check it.
- **Declare a rule once.** Abstention values live on the route in `signal_routing.yaml`,
  admission policy in `evidence_policy.yaml`, the formula in the category's
  `scoring_recipe`. The warehouse hardcodes none of them; it reads them across the bridge.
- **`apply_scores` writes no date at all.** It writes `openness.score` and
  `openness.class`, and that is the whole list. `last_verified` means a person or an agent
  re-read the cited sources and re-derived the value; this pipeline reads values back out of
  `sources/scores/`, which confirms nothing. Two releases taught it to write the field from
  an aggregate of `sources[].accessed` anyway — #108 the MIN, #115 the MAX — and between
  them they put a derived date on 19 of the 26 axes that carried one. **Do not reintroduce
  it**, under any aggregation or column name; `tests/test_apply_scores.py` asserts the
  absence. The rule is in `docs/reference/evidence-and-freshness.md`, who may write it in
  `docs/reference/evidence-and-freshness.md`.

`notebooks/pypi-geo-trends.py`, `notebooks/oss-ai-trends.py`, and `notebooks/long-tail-explorer.py`
are **fully standalone**: no build-pipeline coupling, no generated payload. Each queries
`currentai.*` warehouse tables live via `pyoso`, so the bot never touches them. They share the
AI Stack Map design system; when editing, keep them aligned with `docs/reference/notebook-design.md`
(Noto Serif / Plus Jakarta Sans / DM Mono, the navy + salmon-ramp palette, sharp corners). These
mirror notebooks also published on the OSO platform.

## Prefer a UDM over a committed CSV

When adding an external source, the default is a UDM that reads it directly, not a
fetcher that commits a CSV. A committed mirror of a live source can only be staler than
the source, and nothing makes the drift visible.

The GoodAI List was ingested as a CSV and is the cautionary case: by the time it was
retired, the frozen copy still listed 300 repos the site had delisted (169 of them over
1,000 stars) while missing 2,056 it had added. It is now
`currentai.signal_goodailist.repo_catalog`, on a daily cron. Reserve the fetcher route
for sources needing credentials or shaping a UDM cannot do, or for genuinely fixed
reference data.

## Writing to `sources/`

One policy, three cases. Normative:

1. **A new file** — `yaml.safe_dump(..., sort_keys=False, allow_unicode=True)`. Fine; there is
   no existing formatting to destroy.
2. **An existing corpus file** — `build/components.py` for `openness.components`, and surgical
   single-field edits (`set_document_field`) for everything else.
3. **Never load-modify-dump a file in `sources/`.** The corpus prose is hand-wrapped; a
   round-trip through PyYAML rewraps every string and buries the one change you meant. A
   hand-rolled line splice is not the fallback either — it shipped a 7-product defect, which is
   why `set_document_field` exists.

After any `components` edit, regenerate `raw` or CI fails.

### Traps worth knowing before you start

- **Adding a product touches five files**, not four: product, score, category roster, org
  roster, and `sources/snapshots/long_tail.json` (gated in `validate.py`).
- **Every schema sets `additionalProperties: false`.** An invented field fails `validate`
  rather than being ignored — there is no `litmus` field on a category.
- **Counts written in prose drift.** Regenerate a number before repeating it; `check_recipe`,
  `check_freshness` and `sweep_status` print the live ones.
- **`notebooks/ai-stack-map.py` and `build/notebook_data.json` are bot-owned.** Preview
  locally, leave them out of the commit; CI blocks hand edits.
- **The scoring-chain SQL is not in this repo.** It lives on the OSO platform, and its deploy
  script and `.sql` sit one directory up in `currentai-org/{tools,udms}/`, not under version
  control. See `docs/operations/deploy-models.md`.
- **The chain runs weekly, and that is verified rather than declared.** Dataset-level crons:
  `evidence` Monday 03:00 UTC, `scores` 04:00, with `parity` grading at 06:00. A scheduled run
  was observed firing on 2026-08-19, so this is an observation and not a cron field. It was NOT
  running before that date — the crons had been set at the model-revision layer, which is a
  throttle rather than a sweep. Treat every
  scoring-chain recompute as manual, and check run history before believing a freshness claim.
- **A real-corpus test asserts an invariant, or derives its count. Never a census.** Six tests here
  have now failed because the work succeeded rather than because anything broke;
  `tests/test_sweep_status.py` tells that story in its own docstring, and its `== 16` categories and
  `== 472` products became the sixth on 2026-08-18. Both are now derived from the published
  categories. Where a census IS pinned deliberately - `test_check_parity`'s computed/deferred split,
  `test_serialize_rubric`'s per-category row counts - the comment beside it says what moves the
  number, so whoever updates it next knows whether they are recording a change or hiding one.

## Editor posture (read-only on the warehouse)

Editors (curators, analysts) work only in `sources/`, `docs/`, and `notebooks/`. They
open PRs. They do not:

- Run MCP tools.
- Upload or revise UDMs or static models.
- Push to main directly.

All warehouse write operations are maintainer steps. See `docs/operations/`.

## Skills and workflows

`docs/README.md` is the task router. Each editor skill is a thin wrapper that points at one
workflow document under `docs/workflows/` and adds agent-specific orchestration; the rules live
once in `docs/reference/`, not in the skill. Skills are registered under `.claude/skills/` so a
Claude Code session discovers them by name; if yours does not list them, read
`skills/<name>/SKILL.md` directly.

**Six primary editor skills** (the contributor front door):

| Skill | When to use | Workflow |
|-------|------------|----------|
| `add-product` | Add a new product | `docs/workflows/add-product.md` |
| `update-product` | Change an existing product (identity, prose, a score, rosters, retirement) | `docs/workflows/update-product.md` |
| `edit-category` | Create a category, or change its definition/weights/roster | `docs/workflows/edit-category.md` |
| `promote-category` | Turn a preliminary category's seed roster into published head products | `docs/workflows/promote-category.md` |
| `refresh-category` | Re-verify a whole category, scores and prose, to the PR | `docs/workflows/refresh-category.md` |
| `migrate-axis` | Change an axis's schema or meaning corpus-wide (script-only) | `docs/workflows/migrate-axis.md` |

**Advanced / internal skills** (off the primary path): `build-rubric` (derive a category's
openness ladder), `add-data-source` (register a fetcher), `refresh-all-categories` (drive the
whole-corpus sweep), `pyoso-analyst` (read-only warehouse analysis), `publish-release` (cut a
versioned release + changelog; maintainer).

Invoke the relevant skill before doing editor work. Skills enforce the read-only boundary and
walk through validation + preview steps.

## Maintainer operations

After a PR merges, a maintainer (OSO MCP write access) may need to:

- `docs/operations/deploy-models.md`: revise, release, and run the warehouse models — and the
  truth about the scoring-chain schedule (declared but not firing; recompute is manual).
- `docs/operations/refresh-data.md`: run fetchers and reload static models.
- `docs/operations/publish-map.md`: serialize, render, upload, and publish the live notebook to
  `/currentai/ai-stack-map` (id `7b29bf47`).

For the score-verification procedure itself, see `docs/workflows/refresh-category.md` and the
normative `docs/reference/evidence-and-freshness.md`.

## Environment

- `OSO_API_KEY` loaded automatically via `direnv` (place in `.env`, which is gitignored).
- See `.env.example` for the required variable.
- OSO MCP connects via HTTP to `https://mcp.oso.xyz/mcp` with a Bearer token in `.mcp.json`
  (maintainer only; the file is gitignored).

## Common references

- Query conventions: `docs/reference/queries.md`
- Notebook style: `docs/reference/notebook-design.md`
- Methodology copy (rendered into the notebook): `docs/methodology.md`
- Openness scoring: `docs/reference/openness.md`
- Gap analysis (stages + gaps): `docs/reference/gap-analysis.md`
- Coverage backlog: tracked in GitHub issues
- Warehouse models this repo maintains: `warehouse/models/README.md`
