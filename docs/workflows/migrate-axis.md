# Migrate an axis

Change the **structure or meaning** of openness, adoption, or capability across the whole
corpus — for example splitting `basis` from `basis_detail`, normalizing adoption instruments,
or restructuring `openness.components`. This is a **deliberately low-freedom workflow**. It
requires a deterministic migration script and **prohibits ad-hoc hand edits across hundreds of
YAML files**. If you find yourself editing product files one at a time, stop: that is how the
corpus gets silently corrupted, and it is what this workflow exists to prevent.

## Use this when
The change is to what an axis *records or means*, not to one product's value (that is
[`update-product.md`](update-product.md)) and not to one category's weights or ladder
([`edit-category.md`](edit-category.md) / `build-rubric`).

## Inputs you need
- A clear statement of the **old contract and the new contract** for the axis.
- Agreement that the change is worth a corpus-wide migration — this touches every score file.

## The impact checklist — all ten, in order
A migration is not done until every one is addressed. Skipping any of these is how a
half-migration ships that looks complete until something downstream breaks.

1. **Define the old and new contract.** Write down, precisely, the field shapes before and after
   and the mapping between them. This is the spec the script implements and the reviewer checks.
2. **Update the score schema.** `docs/schemas/score.schema.json` (and any sibling), so `validate`
   describes the new shape.
3. **Write a deterministic corpus migration.** One script, using `build/components.py`'s
   block-safe helpers (`set_field`, `put_field`, `set_document_field`) — never a hand edit and
   never a `yaml.load`/`dump` round-trip, which rewraps every string in every file. The script
   must be idempotent and re-runnable.
4. **Update the validators and checkers.** Every `build/check_*.py` that reads the axis, plus
   `build/validate.py`'s cross-file rules. The producible-pair, invariant, and axis-specific
   gates must understand the new shape.
5. **Update serialization and the payload contract.** `build/serialize.py`,
   `build/serialize_rubric.py`, and `render.py` if the shape reaches the notebook.
   `check_payload` must still pass.
6. **Update the registry tables and OSO model inputs.** `build/serialize_registry.py` and the
   warehouse SQL that reads the axis — see [`../operations/deploy-models.md`](../operations/deploy-models.md).
   A schema change the warehouse does not know about breaks `check_parity`.
7. **Assess front-end compatibility.** `aipotluck.org` consumes `notebook_data.json`. Confirm
   whether the payload shape it reads changed; if so, that is a coordinated change, not a
   silent one.
8. **Update reference docs and examples.** The relevant `docs/reference/*.md`, so no doc teaches
   the old shape.
9. **Run old-versus-new distribution comparisons.** Show that the migration moved what it was
   supposed to and nothing else — a per-axis before/after of the value distribution, so an
   unintended reshaping is visible.
10. **Define removal or compatibility rules for the old representation.** A shadow field (like
    `openness.raw` during the components migration) or an explicit deletion, with the gate that
    enforces the end state.

## Files this changes
The schema, one or more `build/` modules, the migration script, `docs/reference/*`, and — through
the script only — every affected `sources/scores/*.yaml`. Warehouse SQL is a maintainer follow-up.

## Validation
```bash
uv run python -m build.validate            # 0 error(s) under the new schema
uv run python -m build.check_verification
uv run python -m build.check_payload
uv run python -m pytest tests/ -q
```
Plus the distribution comparison from step 9, and (maintainer) `check_parity` once the warehouse
side is deployed.

## Expected PR contents
The contract spec, the schema change, the migration script, the checker/serializer updates, the
doc updates, and the before/after distribution evidence. The bulk YAML diff is the script's
output, not hand work — reviewers check the script and the distributions, not 472 files.

## Stop and escalate when
- The change is really **one category's ladder** → `build-rubric` skill, not a migration.
- The warehouse or front-end contract must change in lockstep → coordinate the deploy
  ([`../operations/deploy-models.md`](../operations/deploy-models.md)) rather than shipping the
  repo half alone.

## Relevant reference material
[`../reference/evidence-and-freshness.md`](../reference/evidence-and-freshness.md) ·
[`../reference/openness.md`](../reference/openness.md) ·
[`../reference/adoption.md`](../reference/adoption.md) ·
[`../reference/capability.md`](../reference/capability.md) ·
`docs/schemas/score.schema.json`
