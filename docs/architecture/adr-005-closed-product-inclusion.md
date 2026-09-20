# ADR-005: Closed products are on the map to mark the frontier, not to be catalogued

**Status:** Accepted 2026-09-20. **This ADR is guidance a curator applies, not a predicate a
build evaluates.** Nothing in `build/` or `tests/` fails because a product sits below the line
described here, and the *Why there is no gate* section says why that is a decision rather than
an omission.

## Context

Closed and vendor-platform products have always been on the map. Nothing wrote down why they
are there or which ones belong, so every borderline case was argued from first principles, and
the same arguments were had more than once. This ADR writes the guidance down.

**The map carries the *capability surfaces* a platform sells, not the platform as a bundle.**
Vertex AI is not a product here; Vertex AI Pipelines is. SageMaker, Vertex AI, Azure ML, Triton,
Weights & Biases and Claude are each on the map in that form — `sagemaker-pipelines`, the four
`vertex-ai-*` surfaces, `azure-machine-learning-pipelines`, `triton`, `weave` and `claude-ai` —
which is easy to read as an absence if you look for the bundle. A rule was already operating. It
had simply never been written down.

### Which population this governs, and the two it does not

Three different sets in this repository are all called "closed", and they are not
interchangeable:

| Set | Where it comes from | What it is for |
|---|---|---|
| **`openness.score <= 1`** | the computed openness score on the product's score file | **the population this ADR governs** |
| `openness.class == "closed"` | the class vocabulary in [`../openness-class-map.json`](../openness-class-map.json) | positioning a product on the cross-category openness spectrum |
| the serializer's closed **bucket** | `_gap_bucket` in `build/serialize.py`, which also folds `documented` and `restricted` into `closed` | gap detection: which products may fire the `openness` gap |

This ADR reads the **score**, for two reasons. The score is the number the inclusion judgement
is actually about — how much of the product is open — and it is the same axis the screen below
reads for capability, so the guidance stays on one scale. The bucket is wider on purpose: it
exists so `restricted` and `documented` products can fire an openness gap, which is a question
about the *category*, not about whether the product belongs on the map at all. Borrowing it here
would put products under an inclusion policy for a reason that has nothing to do with inclusion.

The score set and the class set coincide today. They are still not the same statement, and a
future class could be added at score 2 without either of them moving. When quoting a number from
the survey, say which set it came from.

## Decision

A closed product is on the map to mark the frontier that open products are measured against.
Three tests express that. **They are read together, by a person, on one product at a time.**
A product that reads oddly against one of them can still belong, and a product that reads well
against all three can still be wrong for the map.

### 1. Surface, not bundle

A platform enters as the capability surfaces that map to a scored category, not as the platform.
`vertex-ai-pipelines` and `vertex-ai-tuning` are two products in two categories; "Vertex AI" is
not a product here at all. This **codifies existing practice** — it is what the corpus already
does, and writing it down changes nothing about what is on the map today.

### 2. Best-in-class

Carl's ruling, 2026-09-20, which is the source of this test:

> We do need some representations of the best-in-class (strongest / leading) closed products.
> But we don't need to populate the long tail of closed products.

The starting point he set for that judgement, on the same day and explicitly as a principle:

> `overall_score >= 4` as an initial screen. Where `overall_score` is null because adoption
> abstained, read `capability >= 4` instead.

**This is the new test, and the only one of the three that implies any change.** The line
orients the judgement; it does not make it. Sitting below it is a reason to look at a product,
and what the look concludes is open. Two standing reasons a product below the line belongs:

- it is the only representation of its category's closed frontier, so removing it would leave
  the category with nothing to be measured against;
- a gap statement in the map rests on it as the comparator.

**The null fallback is load-bearing, and is not an escape hatch to be optimised away.** A closed
hosted API frequently has no measurable adoption *in principle*, because there is no public
download channel to count. `overall_score` is null there because the adoption axis abstained,
not because the product is weak. Reading that as a shortfall would measure our instrument rather
than the product, and would take out `google-document-ai` and `azure-document-intelligence` at
capability 5, `nvidia-run-ai` at 5, and most of the closed side of `finetuning_code`.

**A product with neither number is unmeasured, which is a third state and not a quiet kind of
"below".** The line has nothing to say about it. It needs a measurement, and the survey reports
it separately so that the two never get added together — they call for opposite work, one
curatorial and one evidential.

### 3. Evidenceable

At least one axis carries a source a reader can open and check. This too **codifies existing
practice**, and it is worth being exact about what holds it up, because no check does.
`docs/schemas/score.schema.json` requires the three axis blocks and not one `sources` entry
under any of them, and the evidence gates — `check_verification`, `check_citations`,
`check_freshness` — constrain the evidence a score *records* rather than requiring that it
record any. What makes this a description of practice rather than an aspiration is the corpus:
measured on 2026-09-20, every closed product on the map carries at least one source on at least
one axis, with nothing enforcing it. The test writes down a convention curation already keeps.

## Why there is no gate

None of the three tests is enforced anywhere, and none should be.

- **Tests 1 and 3 describe practice.** A gate on either would be re-implementing a convention the
  corpus already follows, and would spend review time on the cases where the convention is
  imprecise rather than on the products.
- **Test 2 is a judgement.** A build that failed because a product scored 3.7 would convert the
  judgement into a threshold, and the threshold is the part Carl explicitly declined to make
  binding. `4` is a policy choice, not a measurement; it must not be derived from the corpus and
  it must not be tuned to make a count come out evenly.

Test 1 is the one that could conceivably carry a gate one day, and it would need a **declared
category capability** to do it. It cannot be done lexically: nothing about a bundle is visible
in its slug, and `spaces`, `aws-lambda` and `google-cloud-run` are legitimately rostered in
`deployment`. That design is not attempted here and nothing commits to it.

Two designs were considered and rejected before this one, and should not be reopened:

- **A leader-relative predicate** — "a closed product is in if it matches the best *open*
  product in its category" — fails in both directions. Where the open peers sit at 5/1 and 1/5, a
  closed product at 4/4 is turned away while beating both on blended score; where the open peers
  are weak, an entire proprietary tail walks in.
- **Invariance by assertion** — "removing a non-leading closed product cannot move a stage or a
  gap" — is simply false. `_stage_and_gaps` in `build/serialize.py` computes `mature_anywhere`
  over **all** products, so a closed product can hold a category off Stage 0 and can fire the
  `openness` gap. Any statement about what removing a product would cost has to be measured.

## The survey

`build/closed_inclusion.py` applies the line and reports what sits under it. Run it with
`uv run python -m build.closed_inclusion`. It reports three states — above the line, below it,
and unmeasured — and for every product not above the line it prints the values it was read on,
how the product's category looks around it, and the category's stage and gap set **recomputed
with that product withheld and the whole payload rebuilt**. Those recomputed numbers are printed
whether or not they differ from the built ones, because a row claiming no effect has to show the
numbers it is claiming it about.

The survey is advisory. It is not a removal list, it has no pass or fail column, and it always
exits 0. Where withholding a product does move a stage or a gap, the survey files it as a
decision for Carl rather than as a candidate for anything: the published shape of the map rests
on that product, so what happens to it is a ruling.

`docs/reference/gap-analysis.md` is the authority on what `stage` and `gaps` mean, and on why
a closed product can move either.

### Measured on 2026-09-20, the day of the ruling

Recorded because it is what the decision was taken against, not as a fact to maintain. Run the
module for today's numbers.

Of 145 products at `openness.score <= 1`: 81 above the line (59 with `overall_score >= 4`, and
22 more whose overall score abstained but whose capability is 4 or 5), 61 below it (48 scored
under 4, 13 whose capability was read and came in under 4), and 3 unmeasured. Withholding any
single one of the 145, one at a time, moved no category's stage and no category's gap set.

## Consequences

The next borderline closed product is argued against a written starting point instead of from
scratch, and the argument is recorded in the product's score file where it already belongs.

Nothing is removed by this decision, and no product file changes. The 61 products below the line
stay exactly where they are until someone rules on them one at a time. The 3 unmeasured ones are
a measurement backlog rather than a curation one.

The survey has no schedule and no gate. It is run when someone wants the question answered.

## Unchanged

One product, one category. A platform's surfaces are separate products. Openness class and the
serializer's closed bucket keep their existing meanings and their existing jobs; this ADR adds a
third reading of "closed" for inclusion and says which is which rather than merging them.
