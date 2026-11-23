# History and triage: decisions proposed (2026-11-23)

Proposed answers to the open questions from the build-step pilot, for the maintainer to accept,
change or reject. Nothing here is in force. Accepted answers go to `docs/rulings/log.yaml` as
rulings, and the production design then goes to
[`../architecture/data-architecture.md`](../architecture/data-architecture.md).

Two sets of questions:

1. The five decisions that [`history-models-review.md`](history-models-review.md) lists before the
   observation-history models can become production datasets (ruling R-2026-11-21-g).
2. Whether the step 5 triage verdicts (`claim_triage`) should feed the proposals bridge, which would
   need a new proposal kind and so is a methodology question under R-2026-11-21-e and ADR-004.

The facts these rest on are in the review package and in
[`proposals-bridge.md`](proposals-bridge.md); they are not repeated here.

## Part 1: the history models

### 1. Schedule

**Proposed:** one weekly cron for every history model, Sunday 08:00 UTC.

- The last upstream sweep (`identity.candidates`) starts at 05:30 UTC. 08:00 leaves two and a half
  hours for it and the others to finish, and six days to re-run a failed week before the next sweep
  replaces the upstream.
- One time for all eight models, rather than one per upstream, keeps the alerting check (decision 2)
  simple: by Sunday 09:00 every model should hold that Sunday's date.
- The history models read only their upstreams, so they need no order among themselves.

**Open risks:**

- An upstream sweep that runs late (past 08:00) is read before it finishes. The model then records
  the previous week's sweep under its own date (for models dated by `fetched_at`, no new date at
  all) and the week is lost unless someone re-runs it. Decision 2's check catches this.
- `goodailist_history` adds no date when goodailist.com did not update. The check must not treat
  that as a missed week.

### 2. Alerting on a missed week

**Proposed:** a scheduled workflow in this repository, Sunday 10:00 UTC and again Wednesday
10:00 UTC, that reads the latest `observed_date` of each history model and the latest sweep time of
its upstream, and fails when a model is behind its upstream. The workflow is added to the list in
`report-failure.yml` (which `tests/test_sentinel_coverage.py` requires of any scheduled workflow),
so a failed run opens an issue and the next green run closes it.

- It compares each model with its own upstream, not with the calendar, so a late or skipped
  upstream sweep is not reported as a history failure, and `goodailist_history` (which follows the
  catalog's own update time) needs no exception.
- The Wednesday run is the reminder: a week still missing then has four days left.
- It needs no new credential: it reads the warehouse with `OSO_API_KEY`, as 13 workflows already do.
- The platform has no failure notice for a scheduled model run today. This check does not depend on
  one, and stays useful if one arrives, because it also catches a run that succeeded but read a
  stale upstream.

**Rejected alternative:** relying on the platform run history alone. Someone has to look, and the
recovery window is one week.

### 3. The two unreleased models

**Proposed:** release `identity_candidates_history` in scratch as it is, run it on two sweeps, and
add it to the review package. Do not release `product_adoption_history` as designed. Re-key it on
`(observation_id, observed_date)` first, with `observed_date` from the upstream's sweep, or drop it.

- As designed it keys on `observation_id` alone, so a value that changes under the same id
  overwrites the earlier one. That is a latest-value table, not history, and
  `observations.product_adoption_current` already is one.
- If observation ids already change whenever a value changes, the model is a log as it stands, and
  the re-key costs nothing but storage. That should be confirmed against the upstream before either
  version is released.

### 4. Where the models live

**Proposed:** one new production dataset, `currentai.history`, holding the eight history models and
nothing else.

- Apart from the feeds it reads, so a feed's release cannot recompute a history model.
- Apart from `currentai.proposals`, which `proposals-bridge.md` already keeps on its own.
- The models become governed assets in `warehouse/assets.yaml`, and their upstreams that are not yet
  listed become contracts in `warehouse/dependencies.yaml` (ADR-003), in the same pull request that
  creates the dataset.
- The scratch dataset `currentai.automation_probe` keeps its two observed dates as a frozen export
  and is then retired. The production models start empty on their first Sunday; the scratch dates
  are not copied in, because they were written by revisions that never passed review.

### 5. Schema changes

**Proposed:** as stated in the review package, made enforceable:

- History models are released only through `build/release_dataset.py`, which stages them
  forwards-only (R-2026-11-08-s). A release of `currentai.history` made any other way is a defect
  to report, not a shortcut.
- Non-additive changes (removing or retyping a column, changing the kind or the unique key) are
  forbidden until OSO-8315 is fixed. Adding a column is allowed.
- A frozen export precedes any fresh build, and any change the tool refuses.
- A test asserts that every model in `currentai.history` is incremental by unique key, has
  `observed_date` (or the documented exception) in its key, and is listed by
  `build/release_dataset.py` as a model that keeps history.

## Part 2: step 5 verdicts and the proposals bridge

**Question:** should `claim_triage` verdicts become proposals, and so pull requests?

**Proposed:** not yet. When they do, through a new kind that asks a person to re-verify one cited
source and changes nothing else.

Why not yet:

- Step 4 (`source_observation`) is not scheduled, so step 5 has no steady input.
- The verdicts are not yet good enough to put in front of a reviewer. Of the 18 in scratch, 5 are
  `cannot_tell`, and the economy model has returned replies without a reason, or empty replies,
  despite a strict schema. There is no measured agreement with a person yet.
- The bridge's one kind, `redate`, writes only what its own fetch confirms. A verdict is an LLM's
  reading of a page, and nothing in the applier can confirm it the same way.

What the kind would be, once those hold:

- **Kind `recheck`.** The applier writes no score, value, date or prose. It adds one line to a
  re-verification queue (product, category, axis, source URL, verdict, the quoted span) for a person
  or the next `refresh-category` run to take up. The verdict decides only what is looked at, never
  what is changed, which keeps it inside what R-2026-11-21-e allows agents to do ("generate evidence
  packets, and open PRs").
- **Only `claim_changed` and `claim_gone`,** and only when the quoted span was found on the page
  (`span_on_page`) or the verdict is `claim_gone`. `claim_holds` already has a better route:
  step 4's `redate` producer. `cannot_tell` goes nowhere.
- **Bar before it is switched on:** a person grades a sample of at least 50 verdicts, and the kind
  ships only if `claim_changed` and `claim_gone` agree with that person at least 80% of the time.
  The bar and the result go in the ruling that adds the kind.

Adding the kind is itself a methodology change, so it needs its own ruling. This document proposes
the shape so that ruling has something to accept or reject.

## What a reviewer should check

- Decision 1: whether 08:00 UTC leaves enough margin, given how long the upstream sweeps actually run.
- Decision 2: whether comparing each model with its upstream misses a failure mode that a calendar
  check would catch.
- Decision 3: whether `observation_id` already changes with the value, which decides whether
  `product_adoption_history` needs the re-key.
- Decision 4: whether retiring the scratch dates rather than copying them is right.
- Part 2: whether `recheck` stays inside R-2026-11-21-e, and whether the bar is high enough.
