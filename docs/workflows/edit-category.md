# Edit a category

## Use this when
You are creating a category, or changing an existing one's definition, strapline, axis
weights, or product roster. For giving a category its openness ladder (`scoring_recipe`),
escalate to the `build-rubric` skill — that is its own craft. For turning a preliminary category's
seed roster into published head products, use [`promote-category.md`](promote-category.md). For
re-verifying every product in a category, use [`refresh-category.md`](refresh-category.md).

## Inputs you need
- The category **slug** (`underscore_form`), and for a new one, its `display_name` and where it
  sits in the taxonomy.
- What you are changing: `description`, `strapline`, `weights.{adopt,cap}`, or the roster.

## Files this changes
- `sources/categories/<slug>.yaml` — the category record.
- `sources/taxonomy.yaml` — only when **creating** a category (assign it to an arc) or regrouping.
- `sources/registry/<slug>.yaml` — optional signal-only seed roster for a preliminary category.

There is **no `litmus` field**. `category.schema.json` sets `additionalProperties: false`, so
inventing one fails `validate`. The membership boundary test — why a borderline product sits
here and not next door — is prose: put it in the category's `comments`, and in the product's own
`comments` for the specific call.

## Procedure
1. **Open** `sources/categories/<slug>.yaml` (or create it). Edit surgically — never
   load-modify-dump the file.
2. **Editable fields:** `display_name`, `description`, `strapline`, `weights.{adopt,cap}`,
   `comments`, and the `products:` roster. `name` is the slug; do not rename it after creation.
3. **Roster:** to add a product it must already have `sources/products/<slug>.yaml` and
   `sources/scores/<slug>.yaml` (use [`add-product.md`](add-product.md) first), then append its
   slug. A slug appears in exactly one category roster. Order equals display order; reorder by
   moving slugs.
4. **Creating a category:** also add it to an arc in `sources/taxonomy.yaml`, or `validate`
   fails with "must appear in exactly one taxonomy arc". New categories normally start as
   `{name: <slug>, status: preliminary}`. They need a definition, weights, and scoring recipe,
   but no strapline or head products yet, and are excluded from the public scored payload.
   Historical scalar entries are published categories. The arc is the Columbia openness layer;
   see [`../reference/identity.md`](../reference/identity.md) and the taxonomy schema.
5. **Seed roster:** discovery candidates belong in `sources/registry/<slug>.yaml`, not in the
   full `products:` roster. Registry rows carry stable identity and artifact IDs but no editorial
   scores. A slug or artifact may not duplicate a head product or another tail row.
6. **Publication:** change the taxonomy entry to `status: published` only after the category has
   a strapline and at least ten promoted, fully scored head products. Validation enforces both, and
   holds every category to the same contract whichever taxonomy spelling it uses — a scalar entry
   means published and owes a description, weights, a ladder, a strapline and ten products.
   Researching a seed roster into those products is its own job: see
   [`promote-category.md`](promote-category.md).
7. **Regrouping / reordering across arcs** happens in `sources/taxonomy.yaml` only — a category
   file no longer carries `arc` or cross-category `order`.

## Validation
```bash
uv run python -m build.validate            # must print 0 error(s)
```
Then serialize and render locally to preview; do not commit the generated notebook or payload.

## Expected PR contents
The category file, plus `taxonomy.yaml` if you created or regrouped a category, and an optional
per-category registry seed. If you touched the head roster, the added products' files belong in
the same PR.

## Stop and escalate when
- The category needs a **`scoring_recipe`** or its `components` values are prose rather than
  controlled tokens → escalate to the `build-rubric` skill.
- You are changing what an **axis means** rather than one category's weights → that is
  [`migrate-axis.md`](migrate-axis.md).

## Relevant reference material
[`../reference/identity.md`](../reference/identity.md) ·
[`../reference/openness.md`](../reference/openness.md) ·
`docs/schemas/category.schema.json` · `docs/schemas/taxonomy.schema.json`
