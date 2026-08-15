# Add a product

## Use this when
A product belongs on the map and does not exist yet. If the product is already present and
you want to change it, use [`update-product.md`](update-product.md) instead.

## Inputs you need
- The **category** it belongs to (exactly one) and the **organization** that makes it.
- Its **product type** (`software`, `model`, `dataset`, `hardware`).
- Its open **artifacts**: GitHub / PyPI / npm / crates / HuggingFace model or dataset / arXiv URLs.
- Enough **primary-source evidence** to score openness, and to say what it is.

## Files this changes
Five, and all in the same PR:
1. `sources/products/<slug>.yaml` — the product record.
2. `sources/scores/<slug>.yaml` — its three-axis score.
3. `sources/categories/<cat>.yaml` — append the slug to the roster.
4. `sources/organizations/<org>.yaml` — append the slug to the roster (create the org file if new).
5. `build/_frozen_long_tail.json` — the dedup counts, regenerated (gated by `validate`).

`CONTRIBUTING.md` historically listed only the first four. The fifth is real.

## Procedure
1. **Pick the slug.** Kebab-case, and it names the **tier the vendor sells**, not a version or
   size — see [`../reference/identity.md`](../reference/identity.md). Slugs are immutable.
2. **Write the product file.** For a brand-new file, `yaml.safe_dump(..., sort_keys=False,
   allow_unicode=True)` is fine. Declare artifacts as typed top-level arrays of `{url: ...}`;
   `docs/schemas/product.schema.json` is the authoritative key list.
3. **Verify against PRIMARY sources.** Never assert a 2025+ release from memory; confirm it
   against the vendor HF org / blog / registry. If it cannot be confirmed, mark it SKIP rather
   than guess. Read the LICENSE **body** for the OSI call (a custom copyright line makes a
   genuine MIT/Apache repo report `NOASSERTION`).
4. **Write the score.** Record the openness evidence in `openness.components` and let the
   category's `scoring_recipe` decide the `(score, class)` — do not hand-assign unless the
   category defers the product. Every non-null openness/capability value needs a `sources`
   entry. Adoption may be left for the warehouse to band from artifacts. See
   [`../reference/openness.md`](../reference/openness.md), [`../reference/adoption.md`](../reference/adoption.md),
   [`../reference/capability.md`](../reference/capability.md).
5. **Update both rosters** (category and org), and the org file if the org is new. A slug
   appears in exactly one of each.
6. **For a batch,** generate the files with a small script (dump for new files, and a helper
   that inserts `- <slug>` lines under existing `products:` blocks so their formatting is
   preserved). Never load-modify-dump an existing corpus file. Re-check the two hand-authored
   things a batch disturbs: category straplines and `_frozen_long_tail.json`.

## Validation
```bash
uv run python -m build.validate            # must print 0 error(s)
uv run python -m build.check_recipe        # the ladder accepts the new score
uv run python -m build.check_verification  # producible pair; invariant if you dated it
```
Preview only, never commit: `build/notebook_data.json`, `notebooks/ai-stack-map.py` (bot-owned).

## Expected PR contents
The five files above, nothing generated. A one-line note per product on the evidence that
settled its openness score.

## Stop and escalate when
- The product needs a **new category** → do [`edit-category.md`](edit-category.md) first (and a
  new category also needs a slug added to `sources/taxonomy.yaml`).
- Its category has **no `scoring_recipe`**, or its openness evidence is prose the ladder cannot
  read → escalate to the `build-rubric` skill; do not normalize a vocabulary inline.
- A release **cannot be confirmed** against any primary source → SKIP it, do not guess.

## Relevant reference material
[`../reference/identity.md`](../reference/identity.md) ·
[`../reference/openness.md`](../reference/openness.md) ·
[`../reference/adoption.md`](../reference/adoption.md) ·
[`../reference/capability.md`](../reference/capability.md) ·
[`../reference/product-copy.md`](../reference/product-copy.md) ·
[`../reference/evidence-and-freshness.md`](../reference/evidence-and-freshness.md)
