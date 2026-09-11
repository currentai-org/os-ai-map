# Postmortem: the Scientific AI models category took a day

**Date:** 2026-09-10 to 2026-09-11
**Outcome:** the category shipped — 34 products, published, all gates green ([#537](https://github.com/currentai-org/os-ai-map/pull/537))
**Cost:** roughly seven hours wall clock from the first commit to the merge, most of it avoidable, and it required continuous supervision from the repository owner.

This is written for the next agent that adds a category. The corrective changes are already
made; this document explains why they were needed.

## What happened

A request to add two products — a multilingual eval harness and the NASA-IBM Lunar Foundation
Model — turned into a new category, because the lunar model had nowhere to go. The eval harness
took about forty minutes and was correct. The category took the rest of the day.

## The numbers

| | |
|---|---|
| CI runs on the category branch | 42 |
| `validate` failures on that branch | 6 |
| `validate` duration | 7–13 min, ~11 avg |
| Full local `pytest -q` runs | ~6, at 12 min each |
| `pytest -q -n auto -m "not serial"` | **4m10s** — documented in AGENTS.md, never used |
| `build.preflight --skip-tests` | **74s** — covers all six CI failures, never used |

Six CI failures at ~11 minutes each is over an hour of pure waiting, and each one cost a
round-trip of attention as well. Every one of them was reproducible locally in 74 seconds.

## Root cause: the tooling existed and was not discoverable

`build/preflight.py` runs what CI's `validate` workflow runs — all fifteen locally-runnable
steps — and accounts for the three it cannot. Its docstring opens with a near-identical
incident:

> The promotion of five products passed a local loop of `validate` + `check_recipe` +
> `check_rubric` + `check_verification` + `pytest`, then failed CI on `build.check_components`
> with ten errors: the `raw:` strings had been hand-written and did not recompose from their
> structured `components` mappings.

That is exactly what happened again, on six products instead of five. The tool built to prevent
it was referenced in **one** operations document and in none of the workflow docs, none of the
skills, and not in AGENTS.md. So the loop was reassembled by hand from the gate lists in the
workflow docs, which were themselves incomplete — `promote-category.md` named nine gates and CI
runs eighteen.

**A hand-assembled subset of `build.check_*` looks complete and is not.** It omits
`check_components`, `check_adoption --strict`, `check_instrument`, `check_routing`,
`check_payload`, `check_retirement`, the goldens check and four serializer dry-runs.

## Contributing: the skill was not invoked

`promote-category` is a registered skill whose workflow document carries the triage rules, the
boundary convention, the six files a promotion touches and the publication conditions. It was
not invoked until several hours in, and reading it then surfaced two rules already broken:

- **Step 7** — extending a shared license tier reaches every inheriting category and is a
  maintainer's ruling, not part of a promotion. Six tier names had already been added.
- **`build/components.py`** — the only sanctioned way to edit an existing corpus file. Hand
  edits to component details left six `raw:` strings behind, which is the CI failure above.

`CLAUDE.md` says to use the registered skill for the workflow. Doing so at minute zero would
have surfaced both.

## Contributing: research was serialized before it was parallelized

The first attempt at researching products worked through them one at a time under a
"calibration protocol", concluded the attributes were unreadable, and reported back. The owner
then scored ten products himself. The remaining twenty-four were done by four parallel agents in
about fifteen minutes of wall clock.

`add-product.md` already says parallel research agents work well for a batch. The batch was
twenty-four products from the first minute.

## Contributing: decisions were escalated that the repository had already answered

Four decisions went to the owner. Two were his to make — the category boundary, and the
shared-ladder ruling. Two were already answered in the repo and cost a round-trip each:

- How to derive a capability rubric with no scores to fit against. `base_pretrained` already
  ships `capability.bands: null` with a `bands_status` saying the thresholds await scores.
- Whether a one-third rung ceiling was a gate. It is one line of prose about rung *wording*,
  enforced nowhere, and **16 of 18 categories exceed it**.

## Contributing: one bad instruction propagated to twenty-four products

Four research agents were told PyPI could not be used for adoption banding pending an open
issue. The opposite was true: `signal_routing.yaml` already declares the precedence
`pypi > huggingface > stars`, and `check_channel_authority` forbids falling through to stars
once a usage route exists. Three products were mis-banded and an issue was filed on a false
premise. **A wrong rule in a batch brief is wrong twenty-four times.**

## What actually worked

- **Adversarial verification as a separate stage.** Four read-only agents re-derived every score
  and found seven real corrections. 22 of 24 sampled digests reproduced byte-for-byte, so the
  research was honest; what needed fixing was judgment.
- **Asking the second reviewer the question no gate covers.** Per-batch reviewers cannot see
  cross-batch inconsistency, because each sees only its own products. A Codex pass aimed
  specifically at that found three inconsistencies the four batch reviewers structurally could
  not, each becoming a roster-wide ruling.
- **The gates themselves.** Every score in the category reproduces mechanically from its
  components; every dated claim carries a digest that re-fetches.

## Changes made

1. `AGENTS.md` Testing now leads with `build.preflight` and says why a hand-assembled subset is
   not equivalent.
2. All seven `docs/workflows/*.md` Validation sections lead with `build.preflight` instead of a
   hand-copied gate list, keeping the individual gates below for re-running one after a failure.
3. All five skills with a "Scripts to run" section do the same.
4. `promote-category.md` gained the eight gates its list was missing, plus the two that bite a
   promotion specifically (`check_components`, `check_channel_authority`) and the rule that
   `tests/goldens/corpus.json` must never be regenerated in a PR.
5. `add-product.md`, `edit-category.md` and `update-product.md` gained the `org_handles.yaml`
   step and the pytest gate ([#531](https://github.com/currentai-org/os-ai-map/pull/531),
   [#534](https://github.com/currentai-org/os-ai-map/pull/534)).

## The shape of a category addition, next time

1. **Invoke the skill first.** `promote-category`, before reading anything else.
2. **Dispatch batch research in parallel from the first minute**, with one shared brief. Check
   every rule in that brief against the repo before sending it — a wrong rule is wrong once per
   product.
3. **`build.preflight --skip-tests` after every material change.** Seventy seconds.
   `pytest -q -n auto -m "not serial"` is four minutes, not twelve. Full `preflight` once before
   pushing.
4. **Run an adversarial cross-batch pass as a standard second stage**, not as a reaction to
   doubt. Ask it explicitly for consistency between batches, and tell it which gates already
   cover the mechanics so it does not re-derive them.
5. **Escalate exactly three things**: the category boundary and name, the capability rubric
   shape, and any shared-ladder ruling. Everything else is either mechanical or already answered
   in `docs/reference/`.
