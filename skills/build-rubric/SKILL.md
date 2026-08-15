---
name: build-rubric
description: Use when a category needs a `scoring_recipe` — deriving an openness ladder from the scores a category already carries, or extending a shared ladder to a new category, in os-ai-map.
---

# Build a Rubric

A `scoring_recipe` is a machine-readable openness ladder: the dimensions a category asks
about, the license tiers it recognizes, and an ordered formula that turns recorded evidence
into a `(score, class)` pair. It lets `check_rubric` re-derive every score in the category from
the evidence, which is the difference between a score that is documented and a score that is
checkable.

Ladders live in `sources/rubrics/<name>.yaml` when shared, and inline under
`scoring_recipe.openness` in a category file when they are not. A category opts in with
`scoring_recipe: {extends: <name>}`, or `{extends: {model: model, software: software}}` where
its roster mixes product types.

## The one rule above the others

**Reproduction rate is a diagnostic, never a target.**

A ladder tuned until it reproduces every recorded score is a curve fit to the data it was
supposed to check. It looks rigorous and is worth less than nothing, because it retires a
check while appearing to pass it.

- Finding a real mismatch and *lowering* the reproduction rate is a good day's work.
- `safeguards` reproduced 0 of 26 and that was the correct outcome at the time: the mismatches
  were the finding. It is 21/26 now, and the way it got there is the more useful lesson —
  sixteen of the seventeen fixes were transcription, not curation. The evidence was in the
  files under keys the ladders do not read. Check for that before assuming a low rate means
  research is owed.
- Never add a rung whose only justification is that one product needs it.
- Never edit a score to make a ladder reproduce. **You do not edit `sources/scores/` at all** —
  see Boundaries.

`check_recipe` therefore asserts nothing about the rate in either direction.

## Step 0 — check the category can be laddered at all

Do this before anything else. It is a few lines and it has twice been the difference between
a day's work and a wasted one.

`check_rubric` resolves a dimension by taking `head(value)` — everything before the first `(`
or `,` — and testing it against the dimension's declared enum. That works when values are
controlled tokens with an optional parenthetical, which is how most of the map was curated.
It cannot work when values are sentences. Count them:

```python
# prose share of components values, for one category
from build.check_rubric import components_of, head
vals = [v for openness in category_openness for v in components_of(openness).values()]
prose = sum(1 for v in vals if len(head(v).split()) > 1)
```

Reference points measured 2026-07-31: `base_pretrained` 0% prose, `training_synthetic_datasets`
2%, `benchmark_eval_data` 15%, `safeguards` 19%, `deployment` 25%, **`edge_hardware` 71% with
no product recording a license at all**.

`edge_hardware` was chosen first precisely because 18 of its 20 products record the same five
keys. Key coverage is not readiness. Its values are prose in the two keys that decide the
score, so no ladder can read it, and the correct move was to stop and propose a normalization
rather than build an alias map around it — see
`plans/reports/2026-07-31-edge-hardware-derivation.md` (local, not in this repo) for the worked
case.

If the values are prose: **stop and write a proposal.** A per-value alias map is the tempting
alternative and it is the curve fit relocated from the formula into the value map — a license
name is a closed external vocabulary where each entry is a fact, but prose is authored per
product, so an alias list needs an entry per product and the next product invents a new
phrasing.

## The derivation, nine steps

1. **Inventory the prose.** Dump every `components` key and value across the category with
   counts. This reveals the questions already being answered and where the spelling drift is.
   `software.yaml`'s header records about forty phrasings behind two dimensions.
2. **Cluster into candidate dimensions.** Name the small number of questions the prose is
   actually answering. Two for software, three for a dataset, three or four for a model.
   Read the `note:` field on the boundary products — the reasoning that distinguishes a 4 from
   a 5 is usually there rather than in `components`.
3. **Name controlled values, and absorb spelling drift with `reads:`.** Never rewrite a score
   file to match a key you chose. `redistributability` and `redistributable` become one
   dimension with two `reads`.

   **`reads:` absorbs drift in the KEY only — never in the value, and never in the polarity.**
   It selects a key and takes its value, so it cannot invert one. `gated: false`,
   `ungated: yes` and `access: ungated` are one fact three ways. The way out is to make every
   *positive* spelling a distinct token, test only those in the formula, and let every spelling
   of "no gate" fall through to the rungs below.
4. **Build `license_tier` with declaration order = restrictiveness ascending.** `tier_rank` is
   emitted from that order, so the order is load-bearing rather than cosmetic. List spelling
   variants literally: whether AGPL is OSI is a fact, and a fact is cheaper to look up than a
   regex is to get right.
5. **Write the formula: ordered, first match wins, `because` on every rung.** The `because` is
   the reviewable artifact — what a human reads where a machine cannot judge. `check_recipe`
   requires it.

   **Require positive evidence for the top rung.** If a rung fires on the *absence* of bad
   evidence, a product that recorded nothing scores full marks. `dataset.yaml`'s top rung tests
   `documentation` for exactly this reason: its gate rungs fire on positive gate tokens, so a
   product with no gate key is *unrecorded*, not ungated.
6. **Decide `otherwise` deliberately and record the decision.** `software.yaml` has none on
   purpose — a third of its products do not record `core-gated`, and an `otherwise` would
   publish a score for every one of them. `model.yaml` has one, landing on the category's
   center of gravity. A judgment per ladder, never a default. An `otherwise` must not land in
   the `open` bucket, or unrecorded evidence counts as open.
7. **Run `check_rubric`. Every non-reproducing product gets a real per-product deferral reason,
   or goes in the report.** Never a score edit. The reason must say what is actually wrong with
   that product. Read two existing `deferred:` blocks before writing yours.
8. **Record `machine_signal` per dimension.** What a fetcher could settle later, and what will
   always need a human read. Required even when the answer is `none`: "nobody has thought about
   it" and "this needs a human forever" are different facts, and the automation roadmap depends
   on telling them apart.
9. **Verify against one category before sharing a ladder.** Prove it on one roster, record the
   counts in that category's `derived_from`, and only then let a second category `extend` it.
   `software.yaml` was verified against `deployment` 27/27 before ten categories inherited it.

## Two rules about rungs and dimensions

They pull in opposite directions and both matter.

**A declared dimension with no rung is legitimate.** `blobs`, `retail` and `datasheets` in the
hardware draft; `checkpoints` in `base_pretrained`. Declare it, give it a `machine_signal`, and
say in a comment that it discriminates nothing yet. Omitting it turns every product recording
it into a vocabulary-drift warning.

**A rung with no product is not.** A rule that cannot fire is where a later edit hides. #133 is
what happens when this is ignored: two rungs in `software.yaml` handed a non-OSI license an
`open`-bucket class, and nothing noticed for weeks because the tier's `examples` list was empty
so the rungs could never fire. Assigning one license to that tier would have silently activated
a 5/open_source rung. `check_recipe` now fails on an unreachable rule.

## The `open` bucket needs an externally-open license

The invariant from #133, enforced by `tests/test_openness_buckets.py`:

> A class in the `open` bucket may only be reached through a license tier that is open by an
> external standard — OSI approval for code and weights, the Open Definition for data.

This is how a 0–5 score stays compatible with frameworks that are binary. The Model Openness
Framework classes a release under OpenRAIL, a Llama community license or AI2 ImpACT as
*source-available* rather than open; OSAID requires the freedom to use a system "for any
purpose". Both lines fall between our `open` and `open-ish` buckets, and levels 4 down to 1
subdivide what MOF treats as one bucket. A new ladder's top rung must respect it.
`docs/reference/openness.md` has the full reasoning and the two places the map departs
from MOF deliberately.

## Run the gate

```
uv run python -m build.check_recipe --category <slug> --verbose
```

It asserts what a machine can judge: a `because` on every rung, a `machine_signal` on every
dimension, no unreachable rule, an explicit license-tier order, no impossible `(score, class)`
pair, no product abstained on without a declared reason, and no evidence the components parser
silently discards. It runs in CI on every PR.

What it reports rather than fails on is worth reading. `clauses dropped` counts `components`
clauses with no key — `split_components` discards those silently, and 168 of 472 products have
at least one. Most are harmless free-text tails or prose restating a properly keyed value, but
a clause that is the *only* record of a dimension is lost evidence, and that cost
`dataset.yaml` five of its eight deferrals. Same for `undeclared keys`: 118 exist across the
map, and the gate fails only when one demonstrably holds an answer the ladder wanted.

Then the human checklist, which is only what a machine cannot judge:

- Is each dimension the right question to ask about **this product type**? A corpus has no
  runtime to self-host; a tune's data question is the post-training mixture, not the base
  model's corpus.
- Does each `because` explain why the rung produces *that score*, rather than restating the
  condition?
- Would a contributor reading only this file reach the same score for a product not in the
  roster?

## Boundaries

- **Never edit anything under `sources/scores/`.** Not one file, for any reason. You author the
  ladder and the `deferred:` block. A score you believe is wrong goes in a report for a human,
  batched for review. The verification guide rests on scores being re-derivable rather than
  asserted, and the first pass of `sources/scores/` was itself agent-authored, so authorship
  establishes no trust.
- `components` fields may only ever be edited via `build/components.py`, never by hand.
- Never hand-edit `build/notebook_data.json` or anything under `notebooks/` — bot-regenerated,
  and CI blocks PRs that touch them. `build/serialize` writes `notebook_data.json` as a side
  effect, so check `git status` after running it.
- Read-only on the warehouse. No uploads, no publish. `currentai.scores.openness_computed`
  mirrors this formula walk by hand in SQL and does not follow automatically — if you change
  resolution semantics, say so loudly in the PR.
- Open a PR. Do not merge.

## Full gate before a final commit

```
uv run python -m build.validate           # 0 error(s)
uv run pytest -q
uv run python -m build.check_recipe       # 0 failure(s)
uv run python -m build.check_rubric       # diff against a baseline captured BEFORE you start
uv run python -m build.check_verification
uv run python -m build.serialize_rubric --check
```

A new recipe legitimately changes `check_rubric` and `serialize_rubric --check` for its own
category and nothing else. **If any other category's counts move, stop and report** — you have
changed shared resolution semantics.
