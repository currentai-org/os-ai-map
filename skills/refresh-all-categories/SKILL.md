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

A sensible default once the first pass is done is 90 days, matching the age gate
`docs/guides/verification.md` step 5 turns on. Do not invent a tighter one silently: a window is
a decision about how much re-reading the map is worth, and it belongs to whoever is paying for
it.

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
