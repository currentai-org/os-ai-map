# CLAUDE.md

Entry point for agent sessions in `os-ai-map`. Read this, then the one workflow your task maps
to. `docs/README.md` is the human version of the same routing; `AGENTS.md` is the repo map
(directory layout, the 30 `build/` modules, the data model, the editor/maintainer boundary).

## Route to a workflow first

Find your task, open its workflow doc, and follow it. The skills are thin wrappers that point at
these same docs and add agent orchestration — they are registered under `.claude/skills/`, so
the Skill tool should list them; if it does not, read `skills/<name>/SKILL.md` directly. Either
way, **do not improvise a procedure a workflow already carries.**

| Your task | Workflow | Skill |
|---|---|---|
| Add a product | `docs/workflows/add-product.md` | `add-product` |
| Change an existing product (identity, prose, a score, rosters, retirement) | `docs/workflows/update-product.md` | `update-product` |
| Create or edit a category | `docs/workflows/edit-category.md` | `edit-category` |
| Re-verify a whole category | `docs/workflows/refresh-category.md` | `refresh-category` |
| Change an axis's schema or meaning, corpus-wide | `docs/workflows/migrate-axis.md` | `migrate-axis` |

`update-product` is a router — if you are unsure which door, start there. Advanced skills
(`build-rubric`, `add-data-source`, `refresh-all-categories`, `pyoso-analyst`) are off the
primary path. The rules each workflow relies on live once under `docs/reference/`.

Nothing above touches the warehouse. Warehouse writes — UDM revisions, static-model reloads,
notebook publishes — are maintainer steps under `docs/operations/`, and an editor session does
not do them.

## Writing YAML: one policy, three cases

Normative:

1. **A new file** — `yaml.safe_dump(..., sort_keys=False, allow_unicode=True)`. Fine, there is no
   existing formatting to destroy.
2. **An existing corpus file** — use `build/components.py` for `openness.components`, and surgical
   single-field edits (`set_document_field`) for everything else.
3. **Never load-modify-dump a file in `sources/`.** The corpus prose is hand-wrapped; a round-trip
   through PyYAML rewraps every string and buries the one change you meant. A hand-rolled line
   splice is not the fallback either — it shipped a 7-product defect, which is why
   `set_document_field` exists.

After any `components` edit, regenerate `raw` or CI fails.

## Traps worth knowing before you start

- **Adding a product touches five files**, not four: product, score, category roster, org roster,
  and `sources/snapshots/long_tail.json` (gated in `validate.py`).
- **Every schema sets `additionalProperties: false`.** An invented field fails `validate` rather
  than being ignored — there is no `litmus` field on a category.
- **Counts written in prose drift.** Regenerate a number before repeating it; `check_recipe`,
  `check_freshness` and `sweep_status` print the live ones.
- **`notebooks/ai-stack-map.py` and `build/notebook_data.json` are bot-owned.** Preview locally,
  leave them out of the commit; CI blocks hand edits.
- **The scoring-chain SQL is not in this repo.** It lives on the OSO platform, and its deploy
  script and `.sql` sit one directory up in `currentai-org/{tools,udms}/`, not under version
  control. See `docs/operations/deploy-models.md`.
- **The chain does not run on a schedule.** Its crons were set at the model-revision layer; the
  platform schedules from the dataset, and zero scheduled runs have ever fired. Treat every
  scoring-chain recompute as manual, and check run history before believing a freshness claim.

## Conventions

- `uv` for everything Python. `uv run python -m build.<module>`; every module takes `--help`.
- Trino SQL for warehouse work.
- American English. No AI tells in commits, PRs, or prose.
- Category slugs are `underscore_form`; product and org slugs are `kebab-case`.
