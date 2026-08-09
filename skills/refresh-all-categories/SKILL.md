---
name: refresh-all-categories
description: Use when driving the verification sweep toward its goal — every product in os-ai-map gate-clean. Reports what is finished, picks the next category by worst artifact coverage, and hands it to refresh-category. One category per run, because each one is reviewed before the next starts.
---

# Refresh All Categories

The objective: **every product on the map gate-clean** — each axis dated or deliberately
abstaining, each source carrying a status and a digest, each product's prose satisfying
`product-info.md`.

This skill is the driver. It holds no verification logic of its own: it works out where the
sweep has got to, picks what is next, and hands one category to `refresh-category`.

## One category per run

Each category is reviewed and merged before the next starts. That is a deliberate gate, not a
limitation — a systemic defect in one batch costs one category rather than fifteen, and the
pilot found three defect classes that only a human reading a PR would have caught.

So this skill advances the goal by one category per invocation, then stops. Run it again for
the next.

## Steps

### 1. Report

```bash
uv run python -m build.sweep_status                     # what has never been confirmed
uv run python -m build.sweep_status --max-age-days 30   # what has also gone stale
```

```
category                        done  held   of  artifacts
finetuning_code                    5     0   27       41%
inference_code                     0     0   20       45%
...
TOTAL                              5     0  472

next: finetuning_code — 22 products remaining, 41% carry a routable artifact
```

State is **derived from the corpus, never stored**. A pointer file recording "we are on category
N" is a second copy of a fact `sources/` already carries, and it desyncs the first time someone
finishes a category by hand, half-finishes one, or reverts. So this is correct after any of
those, and after a run that crashed halfway.

Give the user the table. It is the answer to "how far along are we", which is the question this
skill exists to answer.

**Ask which question they mean**, unless they said. Without a window the sweep is finishing
something: every product confirmed once. With `--max-age-days 30` it is maintaining something:
every product confirmed within the month, so a category that finished in June comes back round.
The first is the current job. The second is what this becomes afterwards, and the same tooling
does both — pass the window straight through to `refresh-category`, which refreshes only the
products it returns.

**The window is 30 days**, decided 2026-08-09 by the person paying for the re-reading. So
`--max-age-days 30` is the maintenance-mode invocation, and `docs/guides/verification.md` step 5
turns the age gate on at the same number. It had been an unmade decision carrying a suggested 90;
this replaces it rather than adding an option.

Two consequences worth stating, because both were weighed:

- **A month is not a promise about any individual page.** Live pages change daily, and the weekly
  sampled re-fetch will keep reporting drift on the volatile ones. That drift is noise at this
  window, not a signal to chase. What 30 days buys is that no score sits unexamined for a quarter.
- **Categories will come back round in cliffs.** A category is re-read in one run, so all of its
  axes carry one date and all of them age out together. Sixteen categories against a 30-day window
  means roughly four categories a week, and the queue from each lands at the same time. Do not
  read a cliff as a backlog.

### 2. Pick

Take the category `sweep_status` names, unless the user asks for a different one. The order is
**worst artifact coverage first**: the categories where machine signal helps least go while the
sweep is still cheap to change, so no manual reading duplicates what an automated pass would
later have earned for free.

Two reasons to override it, and say which applies:

- **A category is mid-flight.** `finetuning_code` has five products done and one held; finishing
  a started category beats starting a new one.
- **An anchor lives elsewhere.** If the next category's products place their capability bands
  against a peer in another category, that peer needs a date first. `check_capability` enforces
  it, so this surfaces as a failure rather than silently.

### 3. Hand off

Invoke `refresh-category` with the chosen slug and let it run to its PR. It spends a cheap model
tier on the per-product research and an expensive one on the audits and the orchestration; that
choice is explained there and is worth preserving, because the research is the bulk of the cost
and the audit is the thing that makes it safe. Do not reimplement any
of it here, and do not "help" by pre-fetching or pre-deciding — its preflight exists because a
pilot run invented product slugs from a summary.

### 4. Stop

Report the PR, the counts, and what the next invocation will pick up. Then stop. The human
merges.

**On how long this takes.** A category is roughly an hour of wall-clock, not the minutes an
agent count suggests: concurrency is capped at `min(16, cores - 2)`, so a 22-product category
runs in six waves on a six-core machine, and the audit re-fetches every digest afterwards. The
ordering makes the early categories the slow ones — worst artifact coverage first means the
products with no repository to read, where a license has to come from pricing pages and terms
documents. Quote a range and say what it depends on rather than a single figure; the first
estimate given for `finetuning_code` was 20 minutes and it took 50.

## What finished looks like

```
TOTAL                            472     n  472
every category is finished.
```

At which point the remaining work is the queue: `sources/verification_queue.yaml` holds the
products whose evidence could not be settled, each with a reason and a date. That backlog is the
honest residue of the sweep, and working it is a different job from running it.

## Boundaries

- Holds no verification rules. They live in the guides `refresh-category` points at.
- Does not merge. Every category PR is reviewed by a human.
- Does not batch two categories into one PR, however small they look.

## Related

- `skills/refresh-category/SKILL.md` — the unit of work this drives
- `build/sweep_status.py` — the derived state, and its own docstring on what "done" means
- `docs/runbooks/verification-pass.md` — the phases the sweep is executing
