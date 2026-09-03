# Promote a preliminary category to published

## Use this when
A category exists as a **preliminary** taxonomy entry with a signal-only seed roster in
`sources/registry/<slug>.yaml`, and the job is to turn those candidates into fully researched head
products and publish the category into the map.

Neighboring doors: [`edit-category.md`](edit-category.md) creates the category and owns its record;
[`add-product.md`](add-product.md) is one product added to a category that already exists;
[`refresh-category.md`](refresh-category.md) re-verifies a category that is already published.
This workflow is the middle passage between the first and the last, and it is a long one - roughly
a day per twenty-five candidates.

## Inputs you need
- The category slug, its **boundary** (what it includes and, more usefully, what it excludes), and
  the neighboring categories whose products it must not duplicate.
- A seed roster in `sources/registry/<slug>.yaml`, or a discovery source to build one from.
- A working `GITHUB_TOKEN`. See the note under Validation: the unauthenticated API ceiling is 60
  requests an hour and this workflow needs three to four per candidate.

## Files this changes
Per promoted product, five concerns:
1. `sources/products/<slug>.yaml` and 2. `sources/scores/<slug>.yaml` - the records.
3. `sources/categories/<cat>.yaml` - the head roster, in display order.
4. `sources/organizations/<org>.yaml` - the org roster, created if the org is new.
5. `sources/registry/<cat>.yaml` - the row comes **out**.

Plus, once per category: the category's `strapline`, its `scoring_recipe.derived_from` counts, and
`sources/taxonomy.yaml` when the status flips. A product moved in from another category also
touches that category's roster and its own capability band.

## Procedure

1. **Triage every seeded row before believing any of it.** A registry row is a candidate, not a
   decision, and its fields are a discovery source's guess. Measured on the `compilers` and
   `storage` seeds: one repository had moved (`quic/aimet` redirects to `qualcomm/aimet`) and five
   of fifty `org` fields named the wrong organization, including one that named a different company
   outright. Fetch each repo's API record and confirm the canonical `full_name`, that it is neither
   archived nor a fork, and that the row names a distinct product rather than a release, a
   submodule, or a rename of something already on the map.

2. **Apply the boundary, and record every rejection.** A row that fails the boundary does not
   belong to the category at any tier, so it is removed rather than parked in the registry - and
   the reason goes in the category's `comments`, because "why is X not here" is the question a
   reader asks next. Reject shapes worth knowing: a product whose own README leads with a different
   product kind (`litert` leads "Google's on-device runtime" and the boundary excluded complete
   runtimes); a dormant thin wrapper superseded by something already on the roster (`torch2trt`, no
   commit in two years, against `nvidia-model-optimizer`); a paper's reference implementation whose
   production successor is on the roster (`llm-awq` against `llm-compressor`); a general-purpose
   system that added one feature in the category's direction (`redis`, `tidb`).

3. **Replace what you reject** with a candidate that meets the boundary, verified the same way. Do
   not pad to a number: the point of the count is that the category is representative, and a forced
   add is worse than a shorter roster.

4. **Decide cross-category moves explicitly, before scoring.** If the category's direct peers sit
   in another published category, the map has two ladders banding the same kind of product and the
   bands cannot be compared. Either move them here and reband them against this category's matrix,
   or state a boundary that genuinely excludes them. Documenting the tension is not a resolution.
   Qdrant, Milvus and Pinecone moved into `storage` on exactly this reasoning; a move is cheap when
   the products form a self-contained comparison cluster (nothing outside them pointed in) and
   expensive when they do not.

5. **Write the records.** [`add-product.md`](add-product.md) governs each one; read it, because the
   traps are per product and this workflow does not restate them. Two that bite hardest at batch
   scale:
   - **Read the LICENSE body, never the label.** Five of the fifty candidates reported
     `NOASSERTION` on a verbatim BSD or MIT text behind a vendor copyright line, and one reported
     no license at all because it follows the REUSE convention with no root LICENSE file.
   - **A same-named registry package is not the product.** See the identification trap in
     [`../reference/adoption.md`](../reference/adoption.md): ten of `storage`'s products have a
     PyPI package matching their name and in none of them is it the product. `check_artifacts`
     cannot catch the client case.

6. **Author the capability matrix once, for the whole category, and check its distribution.** This
   is the judgment-heavy part and the axis has no shared formula. Write the rung definitions into
   the category's `scoring_recipe.note`, name a top anchor, and record every other band against a
   peer with `relative_to` and `relation` so `check_capability` can check the arithmetic rather
   than trusting a sentence. Then count the products per rung - see "Writing the rungs" in
   [`../reference/capability.md`](../reference/capability.md), which is the rule this step exists
   to point at.

7. **Expect the ladder to abstain on something, and let it.** A license the shared tier does not
   name maps to no tier and the formula abstains; record the product in `scoring_recipe.deferred`
   with a substantive reason and move on. Two of fifty landed there, both because the `osi` tier
   lists names literally and had never been asked to name `BSD-2-Clause` or `PostgreSQL`. Extending
   a shared tier reaches every category that inherits it, so it is a maintainer's ruling and not
   part of a promotion - and `check_recipe` will report the deferral stale the moment the ruling
   lands, which is how it closes.

8. **Publish only when the conditions hold.** Flip `sources/taxonomy.yaml` to `status: published`
   when the category has an evidence-based strapline, at least ten fully scored head products,
   coherent capability anchors, and no unresolved identity or boundary dispute on the roster. The
   long-tail `counts.scored` follows automatically at serialize time - nothing to re-sync. If a
   condition fails, leave the category preliminary and say in the PR exactly what blocks it.

**Head products in a preliminary category are normal, not an error.** That is the state this whole
workflow passes through, and `validate` allows it deliberately. While a category is preliminary its
products are absent from every public index - categories, `n_total`, the organization roster, the
alias redirects and the long-tail sample - and `build/validate.published_products` is the single
owner of that visibility. Anything new the payload emits derives from it.

## Validation
```bash
uv run python -m build.validate            # must print 0 error(s)
uv run python -m build.check_recipe        # the ladder accepts every recorded score
uv run python -m build.check_rubric        # per-category reproduction, deferrals itemized
uv run python -m build.check_verification  # producible pairs, digests, the dated-claim invariant
uv run python -m build.check_capability    # the anchor arithmetic and same-category rule
uv run python -m build.check_adoption      # every band against its declared instrument
uv run python -m build.check_instrument    # the instrument a band claims exists for it
uv run python -m build.check_artifacts     # artifacts still resolve; --live also checks PyPI
uv run python -m build.serialize_registry --check
uv run python -m build.serialize_rubric --check
uv run pytest -q
```

**Budget the GitHub API.** Unauthenticated it is 60 requests an hour, and verifying one candidate
costs three to four (repo record, license, README, sometimes a tree listing), so a
twenty-five-product category exceeds the ceiling twice over. A stale token is worse than none: it
fails as a silent 401, which reads as *every repository is dead*, and that is what a first pass over
fifty live repos reported before the token was checked.

Preview only, never commit: `build/notebook_data.json`, `notebooks/ai-stack-map.py` (bot-owned).

## Expected PR contents
The five files per product, the category record, and `sources/taxonomy.yaml`. In the description:
the final count, every rejection and replacement with its reason, the capability rung definitions
and anchors, and anything still deferred or resting on weak evidence. No census is pinned in a test
any more. The PR's review sheet from `build.check_corpus_diff` states the stage, gap, and tier delta
per category; a stage move must be intended and carried by the `stage-move` label.

## Stop and escalate when
- The category has **no `scoring_recipe`**, or its evidence is prose the ladder cannot read →
  `build-rubric`.
- A promotion would need a **shared rubric change** - a license tier, a new dimension → defer the
  product, report it, and leave the ruling to a maintainer.
- A candidate's **identity cannot be settled** against primary sources → leave it in the registry
  rather than promoting a guess.

## Relevant reference material
[`../reference/identity.md`](../reference/identity.md) ·
[`../reference/openness.md`](../reference/openness.md) ·
[`../reference/adoption.md`](../reference/adoption.md) ·
[`../reference/capability.md`](../reference/capability.md) ·
[`../reference/product-copy.md`](../reference/product-copy.md) ·
[`../reference/evidence-and-freshness.md`](../reference/evidence-and-freshness.md)
