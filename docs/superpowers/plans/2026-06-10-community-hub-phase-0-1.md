# Community Hub Phases 0-1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make os-ai-map safe and welcoming for community PRs: clean out migration debris, commit the verified dataset refresh, add CI validation, contributor docs, issue forms, and the bot-owned generated-artifact loop.

**Architecture:** The curated `sources/` tree stays the single source of truth. PR CI (`validate.yml`) enforces schema + cross-file invariants and blocks hand-edits to generated files; a `regenerate.yml` workflow on `main` re-serializes and re-renders the notebook as a bot. Contributor docs (CONTRIBUTING.md + issue forms) mirror the existing Claude Code skills for humans without agents.

**Tech Stack:** Python 3.12 + uv, pytest, jsonschema, marimo, GitHub Actions (`astral-sh/setup-uv`).

**Spec:** `docs/superpowers/specs/2026-06-10-community-hub-design.md`

**Pre-existing working-tree state this plan commits in Task 1:** fetcher path/table/import fixes, `datasets` dep, refreshed `warehouse/catalog/` CSVs, `.gitignore` additions, the spec doc. A background top-up of `warehouse/catalog/github-orgs/orgs.csv` may land mid-execution; commit it whenever it appears (see Task 10).

---

### Task 1: Commit the dry-run work already in the working tree

The dataset-refresh dry-run (2026-06-10) left verified changes uncommitted. Commit them as four logical commits so history stays reviewable.

**Files:**
- Commit (existing modifications/untracked): `docs/superpowers/specs/`, `warehouse/ingest/*.py`, `pyproject.toml`, `uv.lock`, `warehouse/catalog/**`, `.gitignore`

- [ ] **Step 1: Confirm clean baseline of what's changing**

Run: `git status --short`
Expected: modified `.gitignore`, `pyproject.toml`, `uv.lock`, `.claude/skills/pyoso-analyst/SKILL.md`, 6 files under `warehouse/ingest/`, ~10 CSV/JSON files under `warehouse/catalog/`, untracked `docs/superpowers/` and `warehouse/catalog/goodailist/forked_ai_repos.csv` and `warehouse/catalog/github-orgs/`.

- [ ] **Step 2: Commit the spec**

```bash
git add docs/superpowers/specs/2026-06-10-community-hub-design.md
git commit -m "docs: add community hub design spec"
```

- [ ] **Step 3: Commit the fetcher fixes**

```bash
git add warehouse/ingest/ pyproject.toml uv.lock .claude/skills/pyoso-analyst/SKILL.md
git commit -m "fix(ingest): repair fetchers found broken in refresh dry-run

- output paths: warehouse/data/ (pre-migration) -> warehouse/catalog/
- fetch_github_ai_repos: missing pathlib import (pre-existing crash)
- stale table names: currentai.goodailist_repos.repos and
  currentai.ai_repo_activity -> currentai.catalog.goodailist_repos /
  currentai.entities.repos (verified against live warehouse)
- declare datasets dep used by fetch_model_benchmarks"
```

- [ ] **Step 4: Commit the refreshed catalog**

```bash
git add warehouse/catalog/
git commit -m "chore(catalog): refresh all external datasets (2026-06-10 dry-run)

goodailist 16185 repos; HF 2061 tracked models + 662 datasets + top-1000;
benchmarks 4576 rows / 742 repo links; incidents refreshed; new outputs:
github-orgs/orgs.csv (7581 owners, partial pending rate-limit top-up),
goodailist/forked_ai_repos.csv"
```

- [ ] **Step 5: Commit gitignore hygiene**

First append `.DS_Store` (with trailing newline) to `.gitignore` so it reads:

```
.env
.venv/
__pycache__/
warehouse/catalog/pypi_downloads.csv
__marimo__/
.marimo.toml
.mcp.json
.DS_Store
```

```bash
git add .gitignore
git commit -m "chore: gitignore .mcp.json and .DS_Store"
```

---

### Task 2: Delete one-time migration tooling, replace round-trip test with a self-contained serialize test

`build/convert.py` (and helpers) were the one-time v2→v3 migration. `tests/test_convert_roundtrip.py` reads an absolute path inside `insights-private` — it can never pass for a community contributor. Replace it with a fixture-based test of `build_payload` so serializer behavior stays covered.

**Files:**
- Delete: `build/convert.py`, `build/orgs.py`, `build/_make_registry_fixture.py`, `build/_registry_artifacts.json`, `tests/test_convert_roundtrip.py`, `tests/test_orgs.py`
- Create: `tests/test_serialize.py`
- Keep: `build/slugs.py` + `tests/test_slugs.py` (slug rules are used by contributor docs and the future queue indexer)

- [ ] **Step 1: Write the failing test**

Create `tests/test_serialize.py`:

```python
from build.serialize import build_payload


def _sources():
    return {
        "organizations": {"meta": {"name": "meta", "display_name": "Meta",
                                   "type": "unknown", "products": ["llama-4"]}},
        "taxonomy": {"arcs": [{"name": "Models", "categories": ["base_pretrained"]}]},
        "categories": {
            "base_pretrained": {"name": "base_pretrained",
                                "display_name": "Base / pretrained models",
                                "products": ["llama-4"], "comments": ""}
        },
        "products": {"llama-4": {"name": "llama-4", "display_name": "Llama 4",
                                 "type": "model", "description": "desc",
                                 "comments": "note text"}},
        "scores": {"llama-4": {"product": "llama-4",
                               "openness": {"score": 2, "class": "restricted"},
                               "adoption": {"level": 4, "signal_type": "usage_volume"},
                               "capability": {"score": None, "basis": "n/a"}}},
    }


def test_build_payload_shape_and_order():
    payload = build_payload(_sources(), frozen_long_tail={"counts": {}, "top": []},
                            generated="2026-06-10")
    assert payload["order"] == ["base_pretrained"]
    assert payload["n_total"] == 1
    assert payload["generated"] == "2026-06-10"
    cat = payload["categories"]["base_pretrained"]
    assert cat["label"] == "Base / pretrained models"
    assert cat["arc"] == "Models"
    row = cat["products"][0]
    assert row["product"] == "Llama 4"
    assert row["org"] == "Meta"
    # comments field is carried under the legacy payload key version_note
    assert row["version_note"] == "note text"


def test_unknown_org_renders_empty_string():
    s = _sources()
    s["organizations"] = {"unknown": {"name": "unknown", "display_name": "Unknown",
                                      "type": "unknown", "products": ["llama-4"]}}
    payload = build_payload(s, frozen_long_tail={}, generated="2026-06-10")
    assert payload["categories"]["base_pretrained"]["products"][0]["org"] == ""
```

- [ ] **Step 2: Run the new test (should pass immediately — it pins existing behavior)**

Run: `uv run pytest tests/test_serialize.py -v`
Expected: 2 passed. (This is a characterization test of existing code; if either fails, the test's expectation is wrong — fix the test against actual `build_payload` output, do not change `serialize.py`.)

- [ ] **Step 3: Delete the migration tooling**

```bash
git rm build/convert.py build/orgs.py build/_make_registry_fixture.py \
       build/_registry_artifacts.json tests/test_convert_roundtrip.py tests/test_orgs.py
```

- [ ] **Step 4: Verify nothing references the deleted modules**

Run: `grep -rn "convert\|build.orgs\|_registry_artifacts\|_make_registry" build/ tests/ docs/ .claude/ README.md CLAUDE.md --include="*.py" --include="*.md" | grep -v superpowers | grep -v "_frozen"`
Expected: no output (mentions inside `docs/superpowers/` plan/spec are fine).

- [ ] **Step 5: Run full suite + build loop**

Run: `uv run pytest -q && uv run python -m build.validate && uv run python -m build.serialize && uv run python build/render.py`
Expected: all tests pass (still 18: two deleted, two added), `0 error(s)`, `wrote build/notebook_data.json (285 products)`, notebook written. `git status` should show NO change to `build/notebook_data.json` or `notebooks/ai-stack-map.py` (idempotent).

- [ ] **Step 6: Commit**

```bash
git add -A build/ tests/
git commit -m "chore(build): remove one-time v2->v3 migration tooling

convert.py + helpers did their job. test_convert_roundtrip depended on an
absolute insights-private path; replaced with self-contained
tests/test_serialize.py characterization tests."
```

---

### Task 3: Fix stale paths in warehouse/models/README.md

The README references `data/` and `scripts/` paths from before the repo migration; actual locations are `warehouse/catalog/` and `warehouse/ingest/`.

**Files:**
- Modify: `warehouse/models/README.md`

- [ ] **Step 1: Apply the path fixes**

In `warehouse/models/README.md`:
1. Line ~17: `Source CSVs live in `data/`.` → `Source CSVs live in `warehouse/catalog/`.`
2. In the Catalog table, replace every `data/...` source path with `warehouse/catalog/...` (e.g. `data/goodailist/repos.csv` → `warehouse/catalog/goodailist/repos.csv`; same for `model_benchmarks.csv`, `model_repos.csv`, `foundation_model_repos.csv`, `pypi_downloads.csv`).
3. In the Refreshing section, replace:

```bash
uv run scripts/fetch_goodailist.py          # then upload via MCP
uv run scripts/fetch_model_benchmarks.py    # then upload via MCP
```

with:

```bash
uv run python warehouse/ingest/fetch_goodailist.py          # then upload via MCP
uv run python warehouse/ingest/fetch_model_benchmarks.py    # then upload via MCP
```

Also fix the same `scripts/` usage strings inside fetcher docstrings:
- `warehouse/ingest/fetch_model_benchmarks.py` docstring: `uv run scripts/fetch_model_benchmarks.py` → `uv run python warehouse/ingest/fetch_model_benchmarks.py` (both usage lines), and its `Outputs:` lines `data/huggingface/...` → `warehouse/catalog/huggingface/...`
- `warehouse/ingest/fetch_github_orgs.py` docstring: `uv run scripts/fetch_github_orgs.py` → `uv run python warehouse/ingest/fetch_github_orgs.py` (both lines)

- [ ] **Step 2: Verify no stale references remain**

Run: `grep -rn "uv run scripts\|data/goodailist\|data/huggingface\|data/pypi" warehouse/ docs/ README.md | grep -v superpowers | grep -v catalog-gaps`
Expected: no output.

- [ ] **Step 3: Commit**

```bash
git add warehouse/
git commit -m "docs(warehouse): fix pre-migration data/ and scripts/ paths"
```

---

### Task 4: Parameterize the serialize `generated` date

`build/serialize.py` hardcodes `generated="2026-06-04"`. The regenerate workflow needs the run date; local runs default to today.

**Files:**
- Modify: `build/serialize.py:35` (signature default) and the `__main__` block
- Test: `tests/test_serialize.py` (already covers `generated` passthrough from Task 2)

- [ ] **Step 1: Change the signature default and CLI**

In `build/serialize.py`, change the function signature:

```python
def build_payload(sources: dict, frozen_long_tail: dict, generated: str | None = None) -> dict:
```

and at the top of the function body add:

```python
    if generated is None:
        generated = date.today().isoformat()
```

Add `from datetime import date` to the imports. Replace the `__main__` block with:

```python
if __name__ == "__main__":
    import argparse
    from build.validate import load_sources
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=None,
                        help="value for the payload 'generated' field (default: today)")
    args = parser.parse_args()
    sources = load_sources(ROOT)
    frozen = json.load(open(ROOT / "build" / "_frozen_long_tail.json"))
    payload = build_payload(sources, frozen, generated=args.date)
    (ROOT / "build" / "notebook_data.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"wrote build/notebook_data.json ({payload['n_total']} products)")
```

- [ ] **Step 2: Run tests**

Run: `uv run pytest -q`
Expected: all pass (test_serialize passes explicit `generated=`, unaffected by the new default).

- [ ] **Step 3: Verify CLI override keeps today's repo state stable**

Run: `uv run python -m build.serialize --date 2026-06-04 && git status --short build/`
Expected: prints `wrote build/notebook_data.json (285 products)`; `git status` clean (byte-identical with the pinned date).

- [ ] **Step 4: Commit**

```bash
git add build/serialize.py
git commit -m "feat(build): serialize --date flag; generated defaults to today"
```

---

### Task 5: PR validation workflow

**Files:**
- Create: `.github/workflows/validate.yml`

- [ ] **Step 1: Create the workflow**

```yaml
name: validate

on:
  pull_request:
  push:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true
      - name: Install dependencies
        run: uv sync --locked
      - name: Validate sources (schema + cross-file invariants)
        run: uv run python -m build.validate
      - name: Run tests
        run: uv run pytest -q
      - name: Serialize dry-run
        run: uv run python -m build.serialize --date ci-dry-run

  generated-files-guard:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request' && github.actor != 'github-actions[bot]'
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Fail if PR hand-edits bot-owned generated files
        run: |
          git fetch origin "${{ github.base_ref }}"
          CHANGED=$(git diff --name-only "origin/${{ github.base_ref }}...HEAD" \
            | grep -E '^(build/notebook_data\.json|notebooks/ai-stack-map\.py)$' || true)
          if [ -n "$CHANGED" ]; then
            echo "::error::build/notebook_data.json and notebooks/ai-stack-map.py are regenerated by a bot on merge. Remove them from this PR (edit sources/ only)."
            exit 1
          fi
```

- [ ] **Step 2: Sanity-check the workflow YAML parses**

Run: `uv run python -c "import yaml; yaml.safe_load(open('.github/workflows/validate.yml')); print('ok')"`
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/validate.yml
git commit -m "feat(ci): validate sources, tests, and generated-file guard on PRs"
```

---

### Task 6: Regenerate workflow (bot-owned artifacts)

On push to `main` that touches `sources/`, regenerate `build/notebook_data.json` + `notebooks/ai-stack-map.py` and commit as the Actions bot. Pushes made with `GITHUB_TOKEN` do not retrigger workflows, so no loop guard is needed beyond the actor check in Task 5.

**Files:**
- Create: `.github/workflows/regenerate.yml`

- [ ] **Step 1: Create the workflow**

```yaml
name: regenerate

on:
  push:
    branches: [main]
    paths:
      - "sources/**"
      - "build/serialize.py"
      - "build/render.py"
      - "build/_frozen_long_tail.json"

permissions:
  contents: write

jobs:
  regenerate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true
      - name: Install dependencies
        run: uv sync --locked
      - name: Validate
        run: uv run python -m build.validate
      - name: Serialize (generated = run date)
        run: uv run python -m build.serialize --date "$(date -u +%F)"
      - name: Render notebook
        run: uv run python build/render.py
      - name: Notebook structure check
        run: uv run marimo check notebooks/ai-stack-map.py
      - name: Commit regenerated artifacts
        run: |
          if git diff --quiet build/notebook_data.json notebooks/ai-stack-map.py; then
            echo "No changes to generated artifacts."
            exit 0
          fi
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add build/notebook_data.json notebooks/ai-stack-map.py
          git commit -m "chore(build): regenerate notebook data + notebook [bot]"
          git push
```

- [ ] **Step 2: Sanity-check the workflow YAML parses**

Run: `uv run python -c "import yaml; yaml.safe_load(open('.github/workflows/regenerate.yml')); print('ok')"`
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/regenerate.yml
git commit -m "feat(ci): regenerate bot-owned notebook artifacts on merge to main"
```

---

### Task 7: CONTRIBUTING.md

The human-path mirror of the Claude Code skills. Every invariant stated here is enforced by `build/validate.py`, so the doc can promise that CI catches mistakes.

**Files:**
- Create: `CONTRIBUTING.md`

- [ ] **Step 1: Create CONTRIBUTING.md**

```markdown
# Contributing to os-ai-map

Thanks for helping map the open source AI stack. All curation happens through
pull requests editing the YAML files in `sources/`. CI validates every PR, so
you can't break anything that a maintainer won't catch.

> **License note:** a code + data license is being finalized. Until it lands,
> contributions are accepted under the project's forthcoming terms.

## Quick start

```bash
uv sync
uv run python -m build.validate   # must print "0 error(s)"
```

No API keys are needed to edit sources or run validation.

## The data model in one minute

One YAML file per record, four concerns plus one manifest:

| Path | What it holds |
|------|---------------|
| `sources/products/<slug>.yaml` | The product: `name` (slug), `display_name`, `type`, `description`, typed artifact URL arrays, optional `comments` |
| `sources/scores/<slug>.yaml` | Openness / adoption / capability scores. Every non-null value needs a `sources:` citation |
| `sources/organizations/<slug>.yaml` | The org, plus the `products:` roster it owns |
| `sources/categories/<slug>.yaml` | The category, plus its **ordered** `products:` roster (order = display order) |
| `sources/taxonomy.yaml` | Arc grouping and cross-category display order |

Invariants (validated in CI):
- A product appears in **exactly one** category roster and **exactly one** org roster.
- Every product has a matching score file (same slug).
- Slugs: products and orgs are kebab-case (`llama-3-1`); categories are
  underscore form (`base_pretrained`).

## Recipe: add a product

1. **Pick the slug**: kebab-case of the product name (`OLMo 2` → `olmo-2`). If
   taken, suffix the org slug (`command-r-cohere`), then a numeric suffix.
2. **Create `sources/products/<slug>.yaml`**:

   ```yaml
   name: <slug>
   display_name: <Display Name>
   type: model | software | dataset
   description: <one paragraph: what it is, why it matters>
   github:
   - url: https://github.com/org/repo
   huggingface_model:
   - url: https://huggingface.co/org/model
   comments: ''
   ```

   Artifact keys (include only the ones that exist): `github`, `npm`, `pypi`,
   `crates`, `go`, `huggingface_model`, `huggingface_dataset`. Do **not** add an
   `org:` field — org membership lives in the org file.
3. **Create `sources/scores/<slug>.yaml`** (see scoring rubric below). If you
   can't score an axis yet, use `score: null` with a `basis`/`note` explaining
   why — but openness is usually determinable from the license.
4. **Add the slug to one category roster** in `sources/categories/<category>.yaml`,
   at the position where it should display.
5. **Add the slug to one org roster** in `sources/organizations/<org>.yaml`.
   If the org doesn't exist, create it:

   ```yaml
   name: <org-slug>
   display_name: <Org Name>
   type: unknown
   homepage: https://example.com
   products:
   - <slug>
   ```
6. **Validate**: `uv run python -m build.validate` → `0 error(s)`.
7. Open a PR. Don't touch `build/notebook_data.json` or
   `notebooks/ai-stack-map.py` — a bot regenerates those on merge.

## Recipe: edit a category

Category files own the roster and its order. To add/remove/reorder products,
edit the `products:` array. To move a product between categories, remove it
from one roster and add it to the other (it must end up in exactly one).
Arc grouping and cross-category order live in `sources/taxonomy.yaml`.

## Scoring rubric (summary)

Each score file has three axes. **Every non-null value needs at least one
`sources:` citation** (`url`, `shows`, `accessed`).

- **openness** (`score:` 1-5, `class:` depends on type):
  - models: `open_source`, `open_weights`, `restricted`, `closed`
  - software: `open_source`, `source_available`, `open_core`, `closed`
  - datasets: `open`, `gated`, `documented_only`, `closed`
- **adoption** (`level:` 1-5, `signal_type:` one of `active_users`,
  `usage_volume`, `reported_traction`, `stars_fallback`, `unknown`): real usage
  (downloads, active users, deployments) beats stars. `stars_fallback` can
  never justify a level above 3 (enforced by validation).
- **capability** (`score:` 1-5, `basis:` e.g. `benchmark:MLPerf`): benchmark or
  comparative evidence; `null` with a reason if no defensible basis exists.

Look at `sources/scores/vllm.yaml` for a complete worked example.

## Suggesting without writing YAML

Open an issue instead — there are structured forms for **suggest a product**,
**report an error**, and **propose a category**. A maintainer (or an agent)
turns accepted suggestions into PRs.

## For agent-assisted editing

If you use Claude Code, the repo ships skills that automate these recipes:
`add-product`, `curate-category`, `add-data-source`, `pyoso-analyst`. See
`CLAUDE.md`.
```

- [ ] **Step 2: Verify the recipes match the validator**

Run: `uv run python -m build.validate`
Expected: `0 error(s)` (no source change in this task; this confirms the doc's quick-start command works as written).

- [ ] **Step 3: Commit**

```bash
git add CONTRIBUTING.md
git commit -m "docs: add CONTRIBUTING with human-path curation recipes"
```

---

### Task 8: Issue forms

**Files:**
- Create: `.github/ISSUE_TEMPLATE/config.yml`
- Create: `.github/ISSUE_TEMPLATE/suggest-a-product.yml`
- Create: `.github/ISSUE_TEMPLATE/report-an-error.yml`
- Create: `.github/ISSUE_TEMPLATE/propose-a-category.yml`

- [ ] **Step 1: Create config.yml**

```yaml
blank_issues_enabled: true
contact_links:
  - name: AI Stack Map (live notebook)
    url: https://www.oso.xyz/currentai/ai-stack-map
    about: See the published map this repo powers.
```

- [ ] **Step 2: Create suggest-a-product.yml**

```yaml
name: Suggest a product
description: Propose a product for the AI Stack Map (no YAML required)
title: "[product] <name>"
labels: ["product-suggestion"]
body:
  - type: input
    id: product_name
    attributes:
      label: Product name
      placeholder: e.g. OLMo 2
    validations:
      required: true
  - type: input
    id: org
    attributes:
      label: Organization / maintainer
      placeholder: e.g. Allen Institute for AI
    validations:
      required: true
  - type: dropdown
    id: category
    attributes:
      label: Suggested category
      options:
        - Base / pretrained models (base_pretrained)
        - Fine-tuned / chat models (finetuned_chat)
        - Inference code (inference_code)
        - Fine-tuning code (finetuning_code)
        - Evaluation code (evaluation_code)
        - Benchmarks & eval data (benchmark_eval_data)
        - Orchestration & agents (orchestration_agents)
        - UI / API (ui_api)
        - Telemetry & observability (telemetry_observability)
        - Agent tools & protocols (agent_tools_protocols)
        - Deployment (deployment)
        - Not sure
    validations:
      required: true
  - type: textarea
    id: artifacts
    attributes:
      label: Open artifact URLs
      description: GitHub repo, Hugging Face model/dataset, PyPI/npm/crates/Go package links — one per line.
      placeholder: |
        https://github.com/allenai/OLMo
        https://huggingface.co/allenai/OLMo-2-1124-13B
    validations:
      required: true
  - type: textarea
    id: why
    attributes:
      label: Why it belongs on the map
      description: Adoption signals, license, what makes it notable.
    validations:
      required: true
```

- [ ] **Step 3: Create report-an-error.yml**

```yaml
name: Report an error
description: Wrong score, stale description, bad link, or misplaced product
title: "[error] <product or category>"
labels: ["data-error"]
body:
  - type: input
    id: record
    attributes:
      label: Which record?
      description: Product, org, or category name (or the sources/ file path).
      placeholder: e.g. sources/scores/vllm.yaml
    validations:
      required: true
  - type: textarea
    id: what
    attributes:
      label: What's wrong?
    validations:
      required: true
  - type: textarea
    id: evidence
    attributes:
      label: Evidence
      description: Links that show the correct information.
    validations:
      required: true
```

- [ ] **Step 4: Create propose-a-category.yml**

```yaml
name: Propose a category
description: Suggest a new stack-map category or a change to the taxonomy
title: "[category] <name>"
labels: ["category-proposal"]
body:
  - type: input
    id: name
    attributes:
      label: Proposed category name
    validations:
      required: true
  - type: textarea
    id: definition
    attributes:
      label: Definition and litmus test
      description: What belongs in this category, and what's the one-line test for membership?
    validations:
      required: true
  - type: textarea
    id: examples
    attributes:
      label: 5+ example products
      description: A category needs enough products to be worth a row on the map.
    validations:
      required: true
  - type: textarea
    id: overlap
    attributes:
      label: Overlap check
      description: Which existing categories could these products fit into, and why is a new one better?
    validations:
      required: true
```

- [ ] **Step 5: Validate all four parse as YAML**

Run: `uv run python -c "import yaml,glob; [yaml.safe_load(open(f)) for f in glob.glob('.github/ISSUE_TEMPLATE/*.yml')]; print('ok')"`
Expected: `ok`

- [ ] **Step 6: Commit**

```bash
git add .github/ISSUE_TEMPLATE/
git commit -m "feat(community): issue forms for product, error, and category suggestions"
```

---

### Task 9: PR template, CODEOWNERS, README contributing section

**Files:**
- Create: `.github/pull_request_template.md`
- Create: `.github/CODEOWNERS`
- Modify: `README.md`

- [ ] **Step 1: Create the PR template**

```markdown
## What

<!-- One or two sentences: what does this PR add or change? -->

## Checklist

- [ ] `uv run python -m build.validate` prints `0 error(s)`
- [ ] New/changed scores cite sources (`url`, `shows`, `accessed`)
- [ ] I did not edit `build/notebook_data.json` or `notebooks/ai-stack-map.py`
      (a bot regenerates them on merge)
- [ ] Product appears in exactly one category roster and one org roster
```

- [ ] **Step 2: Create CODEOWNERS**

```
# Default: maintainers review everything.
* @ccerv1

# Category rosters get curator owners as the curator roster grows, e.g.:
# /sources/categories/inference_code.yaml @some-curator
```

- [ ] **Step 3: Add a Contributing section to README.md**

Insert after the intro block (before `## Data model: four concerns plus one manifest`):

```markdown
## Contributing

Community curation happens through pull requests and issue forms. Read
[CONTRIBUTING.md](CONTRIBUTING.md) for the data model and step-by-step recipes,
or open a [product suggestion](../../issues/new?template=suggest-a-product.yml)
if you'd rather not write YAML. Every PR is validated by CI.
```

- [ ] **Step 4: Commit**

```bash
git add .github/pull_request_template.md .github/CODEOWNERS README.md
git commit -m "feat(community): PR template, CODEOWNERS, README contributing section"
```

---

### Task 10: Final verification and launch checklist

**Files:** none created; verification + maintainer actions.

- [ ] **Step 1: Commit the github-orgs top-up if it has landed**

The background rerun of `fetch_github_orgs.py` (post rate-limit reset) updates `warehouse/catalog/github-orgs/orgs.csv`. If `git status` shows it modified:

```bash
git add warehouse/catalog/github-orgs/orgs.csv
git commit -m "chore(catalog): top up github-orgs after rate-limit reset"
```

- [ ] **Step 2: Full local verification**

Run: `uv run pytest -q && uv run python -m build.validate && uv run python -m build.serialize --date 2026-06-04 && uv run python build/render.py && uv run marimo check notebooks/ai-stack-map.py && git status --short`
Expected: tests pass, `0 error(s)`, regeneration leaves the tree clean.

- [ ] **Step 3: STOP — confirm launch actions with Carl before executing**

These are outward-facing and irreversible-ish; get explicit confirmation:

```bash
# Push this branch as main (repo currently has no main):
git push origin HEAD:main

# Update the repo description:
gh repo edit currentai-org/os-ai-map \
  --description "Curated data and models behind the Open Source AI Stack Map" \
  --homepage "https://www.oso.xyz/currentai/ai-stack-map"
```

After pushing, verify the `validate` workflow runs green on a trivial test PR, and that branch protection on `main` (require PR + passing checks) is configured in repo settings (manual, maintainer).

- [ ] **Step 4: Report**

Summarize: commits made, CI status, what remains for Phase 2 (weekly refresh workflow with `OSO_API_KEY`/`HF_TOKEN`/`GITHUB_TOKEN` secrets, rate-limit-aware github_orgs) and Phase 3 (queue indexer).
```
