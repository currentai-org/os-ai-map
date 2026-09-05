# Reviewer prompt — Phase 1 closeout (2026-09-05)

_Supersedes the 2026-09-04 reviewer prompt. The earlier one predates the identity fixes and
the corpus-diff repair, so a reviewer running it would rediscover already-settled issues.
Use this one._

## What you are reviewing, and the decision you are making

You are reviewing the Open Source AI Gap Map's data system (`currentai-org/os-ai-map`) at the
**close of Phase 1**. Phase 1's job was to build the machinery in
[`docs/architecture/adr-004-machine-proposals-and-the-public-tail.md`](../docs/architecture/adr-004-machine-proposals-and-the-public-tail.md):
**machines propose, humans accept.** A bot may open a labelled PR carrying a machine-generated
review sheet; only a human merges; tail products are published as *observed* products that
carry no axis scores; and **no tail field depends on an LLM judgment.**

The decision you are making now is **not** "is tail automation proven to hit its target." It
cannot be — the tail scoring SQL and the batcher **do not exist yet**, so no reviewer can
honestly conclude today that the machinery achieves the throughput. The decision you can make,
and the one this review is for, is:

> **Is the Phase 1 machinery sound enough to proceed to the controlled tail-automation pilot —
> with no remaining architectural or correctness blocker that should be fixed before the first
> 50–100-product batch is generated?**

Answer that. Do not pass it on architecture alone while pretending throughput has been shown,
and do not fail it because the 15-minute number has not been demonstrated yet — that number is
the pilot's job to demonstrate, not this review's.

## The one success criterion — the pilot's acceptance test

The criterion is empirical and is measured **by the pilot, not by this review**:

> **50–100 credible tail products per week, cleared in under ~15 minutes of Carl's review.**

Everything in this review serves that criterion. State, for every recommendation, its effect on
**review-cost-per-accepted-product**; a recommendation that raises that cost has to justify
itself against the 15-minute budget, and a finding that cannot move that number is out of scope
for this pass.

## The decision structure

Phase 1 is accepted in two steps, and you own only the first:

1. **Architecture acceptance (now — your call).** Yes or no: is it safe to build and run the
   first controlled batch? "No" requires naming a concrete architectural or correctness blocker
   that should be fixed *before* a batch is generated. Absent such a blocker, the answer is yes.
2. **Operational acceptance (after the batch — not now).** Phase 1 is operationally accepted
   only after a real batch of 50–100 products is generated, sheeted, reviewed against the clock,
   and merged or rejected, with the review cost actually measured. The scheduled infrastructure
   staying alive is not this; a batch clearing within budget is.

## Current state (only these two words change on merge)

- **#494** — EuroLLM, the first hand-authored product driven through the reviewed loop end to
  end (openness 3 / open_weights after two review rounds): **MERGED**.
- **#498** — adopt 51 first-party Hugging Face handles from #483, hold 18; the `princeton-nlp`
  shared-account correction applied: **GREEN / MERGE-READY**.
- **#500** — fix `build/check_corpus_diff.py` to compare freshly serialized payloads (#497):
  **GREEN / MERGE-READY**.

When #498 and #500 merge, change their two state words to **MERGED**. Nothing else in this
prompt depends on the merge.

## Identity is closed

Treat identity infrastructure as **closed unless you find a new, concrete, reproducible
defect.** Do **not** reopen — and do not ask to improve — handle thresholds, the org-handle
ownership model, mirror/aggregator design, digest ordering, coverage ratios, or the resolution
ledger. #498 settled the interpretation: a handle asserts account **ownership**, hosting and
provenance do not, and the ten-or-so uncovered orgs are correct negative space, not a number
to raise. If you believe you have a real identity defect, give the exact input, the wrong
output, and the file and line; otherwise state that identity is sound and move on. Coverage
that could be higher is not a finding.

## What to review (the questions that are actually open)

1. **Architecture sufficiency for the pilot.** Is the ADR-004 architecture — machines propose /
   humans accept, the per-PR semantic diff as the intentional-change gate, the observed-tail
   presentation — sound enough to run the first controlled batch, with no structural gap that
   would either let a wrong tail row through or push review cost above the budget? Name any such
   gap; if there is none, say so.

2. **Blocking correctness holes.** Are there remaining correctness holes that should **block**
   the first batch from being generated — not nice-to-haves, but defects that would let a wrong
   tail row reach `main`, or hide a real change from the reviewer? Anything short of that is
   non-blocking; say so.

3. **#500's corpus-diff safety model — review this specifically.** It is the semantic guardrail
   for every generated batch, so a gap here is the highest-priority finding. Confirm:
   (a) it compares payloads serialized fresh from source at **both** refs, not the committed
   `build/notebook_data.json` against itself (the #497 blind spot); (b) it is side-effect-free
   (no file written); (c) the untouched-row and stage-move gates still hold, and the
   `stage-move` label is still the only way a stage or gap-set moves; (d) the failure a bad
   batch would actually produce is caught by the sheet. Read `build/check_corpus_diff.py` and
   `tests/test_check_corpus_diff.py` — including the two integration tests that make a synthetic
   source change with `notebook_data.json` untouched.

4. **The tail-emission boundary (contracts, not code — the code does not exist yet).**
   Determine whether ADR-004 and the existing `sources/registry/` contracts define a
   sufficiently **sharp** boundary for the forthcoming tail scorer/batcher: every emitted field
   must be mechanically derivable from declared artifacts and deterministic observations
   (detected license, download band, artifact presence, dedup against existing head products);
   identity uncertainty must **hold** rather than guess; no openness or capability judgment may
   be synthesized; and no tail product may acquire axis scores or enter a stage/gap conclusion
   (ADR-004 §2, §4). Flag only an ambiguity in the *existing* contracts that would make a
   correct implementation impossible or likely to diverge. The actual SQL and batcher get
   reviewed when they exist; do not infer or critique an implementation that is not in the
   package.

5. **What the scheduled sequence proves, and what it does not.** Assess what the Sunday/Monday
   scheduled sequence — the deterministic re-verify pass, its agent leg, and the human review
   sheet — actually demonstrates: scheduling, freshness, mirror/eval, and digest operations
   staying alive. Then, **separately**, determine whether a real 50–100-product tail batch must
   still be generated and reviewed against the clock before the throughput claim can be
   considered demonstrated. (The expected conclusion, unless you find otherwise: the scheduled
   sequence proves the infrastructure stays alive; only a real batch proves the economics.)

## Held — do not design yet

**Phase 2 promotion machinery** (turning observed tail products into verified head products at
scale) is **held.** Do not review or design it — **except** to flag a Phase 1 choice that would
make a sound Phase 2 impossible or needlessly expensive later. If you see such a foreclosure,
name it as a Phase 1 finding; otherwise leave Phase 2 alone.

## Where to look

- [`docs/architecture/adr-004-machine-proposals-and-the-public-tail.md`](../docs/architecture/adr-004-machine-proposals-and-the-public-tail.md) — the governing decision.
- `build/check_corpus_diff.py`, `tests/test_check_corpus_diff.py` — the guardrail (#500).
- [`docs/workflows/discover-candidates.md`](../docs/workflows/discover-candidates.md), `sources/registry/` — where candidates enter, and the contracts a tail emitter would serialize from.
- [`docs/architecture/adr-002-registry-curated-catalog-discovered.md`](../docs/architecture/adr-002-registry-curated-catalog-discovered.md) — `registry` versus `catalog`.
- [`docs/architecture/adr-003-repository-scope-boundary.md`](../docs/architecture/adr-003-repository-scope-boundary.md), `CLAUDE.md`, `AGENTS.md` — the scope boundary and the read-only editor boundary.

(There is no tail-scorer/batcher design artifact yet; question 4 is deliberately about the
contracts, not an implementation. If a design file is added later, add it here and widen
question 4 to cover it.)

## How to answer

Lead with the **architecture-acceptance verdict**: yes or no — is it safe to build and run the
first controlled batch? If no, the blocking findings, each with file and line and the concrete
failure it prevents. Then non-blocking observations, explicitly marked as non-blocking. Do not
restate settled identity design, do not spend the review on things that cannot move the
15-minute number, and do not claim the throughput is proven — that is the pilot's acceptance
test, run after this review, not part of it.
