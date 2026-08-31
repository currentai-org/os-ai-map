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
5. `sources/snapshots/long_tail.json` — the dedup counts, regenerated (gated by `validate`).

`CONTRIBUTING.md` historically listed only the first four. The fifth is real.

**A sixth, when the product starts life as a discovered candidate.** If a row for this slug
exists in `sources/registry/<cat>.yaml` — put there by
[`discover-candidates.md`](discover-candidates.md) — that row **comes out** in the same PR. A
slug may live in exactly one tier, so adding the head product without removing the tail row
fails `validate` with `tail slug '<slug>' already exists as a head product`. Check before you
start:

```bash
grep -rn "slug: <slug>" sources/registry/
```

`promote-category` does the same removal for a whole roster, but it applies only to
*preliminary* categories. A candidate discovered in an already-published category has no other
workflow that clears its row, so this is the only place it happens.

## Procedure
1. **Pick the slug.** Kebab-case, and it names the **tier the vendor sells**, not a version or
   size — see [`../reference/identity.md`](../reference/identity.md). Slugs are immutable.
2. **Write the product file.** For a brand-new file, `yaml.safe_dump(..., sort_keys=False,
   allow_unicode=True)` is fine. Declare artifacts as typed top-level arrays of `{url: ...}`;
   `docs/schemas/product.schema.json` is the authoritative key list.
3. **Verify against PRIMARY sources.** Never assert a 2025+ release from memory; confirm it
   against the vendor HF org / blog / registry. If it cannot be confirmed, mark it SKIP rather
   than guess. Read the LICENSE **body** for the OSI call (a custom copyright line makes a
   genuine MIT/Apache repo report `NOASSERTION`). Two shapes worth knowing before you hunt: a
   repository following the **REUSE convention** carries no root LICENSE at all - the texts sit in
   `LICENSES/*.txt` with a `REUSE.toml` declaring which covers what, and the API reports no license
   rather than `NOASSERTION` (`arm-compute-library`). And a **split license** states its own split
   in the body: `elasticsearch` names a default triple license and carves out `x-pack`,
   `meilisearch` reads `MIT AND BUSL-1.1` and names an Enterprise Edition. Those are `core-gated`
   evidence, not just a license question.
4. **Write the score.** Record the openness evidence in `openness.components` and let the
   category's `scoring_recipe` decide the `(score, class)` — do not hand-assign unless the
   category defers the product. Every non-null openness/capability value needs a `sources`
   entry. Adoption may be left for the warehouse to band from artifacts. See
   [`../reference/openness.md`](../reference/openness.md), [`../reference/adoption.md`](../reference/adoption.md),
   [`../reference/capability.md`](../reference/capability.md).
5. **Attest the spine, if the batch places bands by comparison.** A capability band placed
   against a peer records `relative_to` + `relation`, and the peer will almost always have been
   confirmed before this product existed. Do not drop the comparison into prose, and do not
   re-date the peer's whole axis to get around it. Pick the two or three peers the batch compares
   against, `uv run python -m build.fetch_source <the discriminating URL>` on each, read the body,
   confirm the feature or scale claim separating the peer from the new products still reads as
   its `value` says, and write a `comparison` block per edge. One fetch serves every edge against
   that peer. The peer's own `last_verified` stays where it is — unless the read covered every
   source its capability axis cites, in which case it has been re-derived and may be dated.
   `uv run python -m build.check_refetch --product <peer>` first is cheap triage: where everything
   reproduces, the peer's recorded values are known unchanged and the read is a formality.
6. **Update both rosters** (category and org), and the org file if the org is new. A slug
   appears in exactly one of each. **If the product came from a registry row, delete that row
   now** — see the sixth file above. If it was the last row in the file, leave `products: []`
   rather than deleting the file: the file pairs with a category, not with its contents.
7. **For a batch,** generate the files with a small script (dump for new files, and a helper
   that inserts `- <slug>` lines under existing `products:` blocks so their formatting is
   preserved). Never load-modify-dump an existing corpus file. Re-check the two hand-authored
   things a batch disturbs: category straplines and `sources/snapshots/long_tail.json`.

## Validation
```bash
uv run python -m build.validate            # must print 0 error(s)
uv run python -m build.check_recipe        # the ladder accepts the new score
uv run python -m build.check_verification  # producible pair; invariant if you dated it
uv run python -m build.check_capability    # the comparisons and their attestations hold
```
Preview only, never commit: `build/notebook_data.json`, `notebooks/ai-stack-map.py` (bot-owned).

## Expected PR contents
The five files above — six when a discovered candidate's registry row comes out — and nothing
generated. A one-line note per product on the evidence that settled its openness score.

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
