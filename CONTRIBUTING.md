# Contributing to os-ai-map

Thanks for helping map the open source AI stack. All curation happens through
pull requests editing the YAML files in `sources/`. CI validates every PR, so
you can't break anything that a maintainer won't catch.

This project is [MIT licensed](LICENSE); contributions are accepted under the
same terms.

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

Machine-readable JSON Schemas for all five file types live in `docs/schemas/`.

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
   type: model | software | dataset | hardware
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
3. **Create `sources/scores/<slug>.yaml`** (see scoring rubric below). The file
   starts with `product: <slug>`; openness requires both `score` and `class`,
   and capability requires `score` and `basis`. If you can't score an axis yet,
   use `score: null` with a `basis`/`note` explaining why — but openness is
   usually determinable from the license.
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

The category also carries two bits of editorial text: `description` (a neutral
one-liner — *what the category is*) and `strapline` (the *finding* — what the map
concludes about its open/closed gap). Both flow into the build, so edit them here
rather than in the notebook; `description` is also emitted into the payload's
top-level `descriptions.categories` legend.

## Scoring rubric (summary)

Each score file has three axes. **Every non-null value needs at least one
`sources:` citation** (`url`, `shows`, `accessed`).

- **openness** (`score:` 0-5, `class:` depends on type):
  - models: `open_source`, `open_weights`, `restricted`, `closed`
  - software: `open_source`, `source_available`, `open_core`, `closed`
  - datasets: `open`, `gated`, `documented_only`, `closed`
  - hardware: `open_hardware`, `open_toolchain`, `documented`, `restricted`, `closed`
- **adoption** (`level:` 1-5, `signal_type:` one of `active_users`,
  `usage_volume`, `reported_traction`, `documented_reuse`, `stars_fallback`,
  `unknown`): real usage (downloads, active users, deployments) beats stars.
  `stars_fallback` can never justify a level above 3 (enforced by validation).
  `documented_reuse` is for training corpora whose decisive signal is documented
  use by downstream models (see the training-corpus bands below).
- **capability** (`score:` 1-5, `basis:` e.g. `benchmark:MLPerf`): benchmark or
  comparative evidence; `null` with a reason if no defensible basis exists.

### Adoption level bands

The `adoption.level` is graded against monthly usage volume — package-registry
downloads (PyPI, npm), Hugging Face downloads, or equivalent active-user / request
counts. Use the band the product's verified monthly volume falls into:

| Level | Monthly usage volume | Reading |
|------:|----------------------|---------|
| **5** | **> 10M / mo** | Ecosystem standard — the default choice for its job (e.g. PyTorch, LangChain, MLflow, Ray). |
| **4** | 1M – 10M / mo | Widely adopted; a leading option in its category (e.g. vLLM, TRL, Diffusers). |
| **3** | 100k – 1M / mo | Real, non-trivial usage; established but not dominant. |
| **2** | 10k – 100k / mo | Emerging; a meaningful user base but still niche. |
| **1** | < 10k / mo | Early / experimental; little verified usage. |

Notes on applying the bands:

- **Use real usage, not popularity.** Downloads, active users, deployments, and
  request volume are the basis. **GitHub stars are a weak last-resort signal and
  never raise adoption above level 3** (`signal_type: stars_fallback`, enforced by
  validation).
- **Ecosystem-standard status can stand in for a clean count.** A few infrastructure
  tools have no single download figure but are unambiguously the default in their
  category (e.g. a C/C++ engine, a managed platform). These may sit at level 4–5 on
  documented ecosystem-standard status with `signal_type: reported_traction`; say so
  in the `note`.
- **Borderline cases.** When volume sits right at a band edge (e.g. ~10–13M/mo at the
  level-5 floor), lean on whether the product is genuinely the ecosystem default before
  promoting, and record the reasoning in the `note`.
- The `reach` field is a free-text label for the same figure (e.g. `'>10M'`,
  `1M-10M`); keep it consistent with the chosen level.

Look at `sources/scores/vllm.yaml` for a complete worked example.

#### Training-corpus bands

Download volume for a multi-terabyte corpus is not comparable to a package: a
corpus is pulled a handful of times per training run, not on every CI job. Products
in the `training_synthetic_datasets` category are therefore graded one order of
magnitude below the standard bands:

| Level | Monthly HF downloads | Reading |
|------:|----------------------|---------|
| **5** | **> 1M / mo** | Ecosystem-standard corpus — a default choice for building models. |
| **4** | 100k – 1M / mo | Widely used; a leading corpus in its niche. |
| **3** | 10k – 100k / mo | Established, real usage. |
| **2** | 1k – 10k / mo | Emerging; a meaningful user base but still niche. |
| **1** | < 1k / mo | Early / experimental; little verified usage. |

These bands do **not** apply to `benchmark_eval_data`: benchmark sets are small
files pulled by evaluation harnesses on every run, so their download counts behave
like package downloads and the standard bands fit.

**Documented reuse.** Raw downloads still under-measure a corpus that model builders
mirror once and reuse forever. A corpus verifiably documented (model cards, technical
reports) as a training-data component of **three or more notable independent model
families** may sit **one level above** its volume band — never more than one. Use
`signal_type: documented_reuse`, name the model families in the `note`, and cite the
documenting reports in `sources`.

## Suggesting without writing YAML

Open an issue instead — there are structured forms for **suggest a product**,
**report an error**, and **propose a category**. A maintainer (or an agent)
turns accepted suggestions into PRs.

## For agent-assisted editing

If you use a coding agent, the repo ships skills that automate these recipes:
`add-product`, `curate-category`, `add-data-source`, `pyoso-analyst`. See
`AGENTS.md` and `skills/`.
