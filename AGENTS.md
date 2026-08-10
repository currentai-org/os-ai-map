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
sources/               Curated YAML: organizations, categories, products, scores
sources/taxonomy.yaml  Arc grouping + cross-category display order
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
warehouse/models/      UDM SQL (entities, events, metrics, scores)
warehouse/ingest/      Python fetchers that write CSVs to warehouse/catalog/
warehouse/catalog/     Raw external CSVs (HF benchmarks, incidents, GitHub orgs)
warehouse/sources.yaml Manifest: each external source declares EITHER a fetcher
                       (writes a CSV) or an ingested_by (a UDM reads it directly)
build/                 Python pipeline, see below
notebooks/             Generated ai-stack-map.py and standalone companion notebooks (pypi-geo-trends, oss-ai-trends, long-tail-explorer)
docs/methodology.md    Canonical methodology copy, rendered into the notebook (a build input)
docs/guides/           Query conventions, notebook style, freshness and verification
docs/runbooks/         Maintainer deploy runbooks
docs/schemas/          JSON Schemas for the source files (four concerns + taxonomy)
skills/                Agent skills for common editor workflows
tests/                 pytest suite for build helpers and serializer behavior
```

### What is in `build/`

Every module is a CLI with a docstring that explains why it exists; run any of them with
`--help`. Grouped by what they are for:

```
Notebook build      validate.py      sources/ schema + cross-file invariants
                    serialize.py     sources/ -> build/notebook_data.json
                    render.py        notebook_data.json -> notebooks/ai-stack-map.py
                    update_readme.py syncs the README stat badges

Config bridge out   serialize_registry.py  identity: what exists
                    serialize_rubric.py    each category's rubric + recorded evidence
                    publish_registry.py    pushes both table sets to OSO as static models

Scores back in      apply_scores.py   reads computed scores from OSO, writes
                                      openness.score and openness.class into
                                      sources/scores/ and nothing else. The ONLY
                                      inbound data path. It writes no dates -- see
                                      docs/guides/verification.md.

Checkers (CI)       check_rubric.py    does the rubric reproduce the hand-authored scores
                    check_routing.py   which dimensions have a usable machine signal
                    check_freshness.py how stale is each axis

Proposers           propose_arxiv.py     candidate arXiv ids, verified live
                    propose_artifacts.py candidate artifacts, verified live
```

Proposers deliberately **print rather than write**. Matching artifacts by name measured 2
correct in 10 on this data, and a wrong artifact attaches another project's license and
downloads to a product, which is indistinguishable from a real score until someone checks.

## Data model

The curated source set is four per-record YAML concerns in `sources/` plus the single
`sources/taxonomy.yaml` manifest:

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
  `huggingface_dataset`. Only keys with entries are included. Optional `comments` is a
  free-text string for provenance and scoring notes (version, license, last release date).
- **scores**: one file per product (same slug) with `openness`, `adoption`, `capability`.
  Every non-null score value requires a `sources:` citation entry.
- **taxonomy.yaml**: owns arc grouping + cross-category display order. The three arcs
  ARE the Columbia openness-ontology layers (`product_ux`, `model_components`,
  `infrastructure`); each arc declares its `layer` slug and an ordered category list.
  `serialize.py` derives order, the display `arc`, and the machine `layer` from here, so
  a category's layer is never a separate hand-maintained field -- it is whichever arc the
  category sits in. Validate enforces that every category appears in exactly one arc and
  that every arc declares a valid layer.

Category slugs are underscore form (`base_pretrained`). Product and org slugs are
hyphenated kebab-case (`llama-3-1`).

## Build pipeline

```bash
uv run python -m build.validate        # validate sources/ (must print "0 error(s)")
uv run python -m build.serialize       # sources/ -> build/notebook_data.json
uv run python build/render.py          # -> notebooks/ai-stack-map.py
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
  absence. The rule is in `docs/guides/freshness.md`, who may write it in
  `docs/guides/verification.md`.

`notebooks/pypi-geo-trends.py`, `notebooks/oss-ai-trends.py`, and `notebooks/long-tail-explorer.py`
are **fully standalone**: no build-pipeline coupling, no generated payload. Each queries
`currentai.*` warehouse tables live via `pyoso`, so the bot never touches them. They share the
AI Stack Map design system; when editing, keep them aligned with `docs/guides/notebook-design.md`
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

## Editor posture (read-only on the warehouse)

Editors (curators, analysts) work only in `sources/`, `docs/`, and `notebooks/`. They
open PRs. They do not:

- Run MCP tools.
- Upload or revise UDMs or static models.
- Push to main directly.

All warehouse write operations are maintainer steps. See `docs/runbooks/`.

## Skills

Editor skills live in `skills/`. They compose: the sweep drives a category, a category
drives its products, and a product's prose has its own procedure.

| Skill | When to use |
|-------|------------|
| `curate-category` | Edit category definition, weights, litmus, or product roster |
| `add-product` | Add a new product (scaffolds product + score YAML, updates roster) |
| `build-rubric` | Derive a category's openness ladder, or extend a shared one to it |
| `verify-product` | Refresh one product's `description` and `comments` against its sources |
| `refresh-category` | Re-verify a whole category: scores and prose together, to the PR |
| `refresh-all-categories` | Drive the sweep — report progress, pick the next category |
| `add-data-source` | Register a new external data source and add a fetcher |
| `pyoso-analyst` | Query `currentai.*` tables via `pyoso` (read-only analysis) |

Invoke the relevant skill before doing editor work. Skills enforce the read-only boundary
and walk through validation + preview steps.

## Maintainer runbooks

After a PR merges, a maintainer (OSO MCP write access) may need to:

- `docs/runbooks/verification-pass.md`: the plan for getting every score auditable --
  gates first, then coverage, then the re-read pass. Start here for score-verification
  work; it names the failure modes each step is guarding against.
- `docs/runbooks/deploy-udms.md`: revise, release, and run UDM SQL changes.
- `docs/runbooks/refresh-data.md`: run fetchers and reload static models.
- `docs/runbooks/publish-notebook.md`: serialize, render, upload, and publish the live
  notebook to `/currentai/ai-stack-map` (id `7b29bf47`).

## Environment

- `OSO_API_KEY` loaded automatically via `direnv` (place in `.env`, which is gitignored).
- See `.env.example` for the required variable.
- OSO MCP connects via HTTP to `localhost:8000/mcp` with a Bearer token in `.mcp.json`
  (maintainer only).

## Common references

- Query conventions: `docs/guides/queries.md`
- Notebook style: `docs/guides/notebook-design.md`
- Methodology copy (rendered into the notebook): `docs/methodology.md`
- Openness scoring: `docs/guides/openness-spectrum.md`
- Gap analysis (stages + gaps): `docs/guides/gap-analysis.md`
- Coverage backlog: tracked in GitHub issues
- Warehouse models this repo maintains: `warehouse/models/README.md`
