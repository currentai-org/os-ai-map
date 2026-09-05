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

Your review answers one question: **is this machinery sufficient to turn on**, so that the map
can cover the long tail within a fixed weekly review budget? You are not asked whether it could
be improved. You are asked whether it is sound enough to run.

## The one success criterion — keep it in front of every finding

**Review cost per accepted product must fall.** Concretely: **Carl's tail review stays under
~15 minutes per week** while the system produces **50–100 credible tail products per week.**
Every recommendation must state its effect on review-cost-per-accepted-product. A
recommendation that raises that cost has to justify itself against the 15-minute budget, and a
finding that does not change whether the criterion is reachable is out of scope for this pass.

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

1. **Architecture sufficiency.** Does the ADR-004 architecture — machines propose / humans
   accept, the per-PR semantic diff as the intentional-change gate, the observed-tail
   presentation — support 50–100 tail products/week without pushing review cost back up? Name
   any structural gap that would.

2. **Blocking correctness holes.** Are there remaining correctness holes that should **block**
   tail automation from being switched on — not nice-to-haves, but defects that would let a
   wrong tail row reach `main`, or hide a real change from the reviewer? Anything short of that
   is non-blocking; say so.

3. **#500's corpus-diff safety model — review this specifically.** It is the semantic guardrail
   for every generated batch, so a gap here is the highest-priority finding. Confirm:
   (a) it compares payloads serialized fresh from source at **both** refs, not the committed
   `build/notebook_data.json` against itself (the #497 blind spot); (b) it is side-effect-free
   (no file written); (c) the untouched-row and stage-move gates still hold, and the
   `stage-move` label is still the only way a stage or gap-set moves; (d) the failure a bad
   batch would actually produce is caught by the sheet. Read `build/check_corpus_diff.py` and
   `tests/test_check_corpus_diff.py` — including the two integration tests that make a synthetic
   source change with `notebook_data.json` untouched.

4. **Tail scoring SQL and batcher design boundaries.** Review the **proposed** design (not yet
   built): what is legitimately **deterministic** — observed license, download band, artifact
   presence, dedup against existing head products — versus what must stay **human judgment.**
   ADR-004 §4 is binding: no tail field may depend on an LLM judgment; an agent may orchestrate
   serialization and PR creation without being epistemically involved in the result. Flag any
   place the proposed boundary lets a judgment leak into a machine-emitted field, or lets a
   tail row acquire an axis score.

5. **Operational-loop evidence.** Assess whether the scheduled acceptance sequence — the
   deterministic re-verify pass, its agent leg, and the human review sheet — is sufficient
   **evidence** that the operational loop works: that a week's worth of proposals can be
   produced and cleared within budget. Or is a real end-to-end dry run (a batch generated,
   sheeted, and cleared against the clock) still required before scaling? Say which.

## Held — do not design yet

**Phase 2 promotion machinery** (turning observed tail products into verified head products at
scale) is **held.** Do not review or design it — **except** to flag a Phase 1 choice that would
make a sound Phase 2 impossible or needlessly expensive later. If you see such a foreclosure,
name it as a Phase 1 finding; otherwise leave Phase 2 alone.

## Where to look

- [`docs/architecture/adr-004-machine-proposals-and-the-public-tail.md`](../docs/architecture/adr-004-machine-proposals-and-the-public-tail.md) — the governing decision.
- `build/check_corpus_diff.py`, `tests/test_check_corpus_diff.py` — the guardrail (#500).
- [`docs/workflows/discover-candidates.md`](../docs/workflows/discover-candidates.md), `sources/registry/` — where candidates enter the system.
- [`docs/architecture/adr-002-registry-curated-catalog-discovered.md`](../docs/architecture/adr-002-registry-curated-catalog-discovered.md) — `registry` versus `catalog`.
- [`docs/architecture/adr-003-repository-scope-boundary.md`](../docs/architecture/adr-003-repository-scope-boundary.md), `CLAUDE.md`, `AGENTS.md` — the scope boundary and the read-only editor boundary.

## How to answer

Lead with a **one-line verdict on the success criterion**: is Phase 1 sufficient to turn on
tail automation — yes or no. Then the **blocking findings** (if any), each with file and line
and the concrete failure it prevents. Then **non-blocking observations**, explicitly marked as
non-blocking. Do not restate settled identity design, and do not spend the review on things
that cannot move the 15-minute number.
