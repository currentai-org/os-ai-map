# Score Freshness Guide

What it means for a score to be current, which date answers that, and which dates
look like they answer it but do not.

> This is the data-consumer / query reference, and it is normative. For the
> reader-facing methodology see `docs/methodology.md`. When the rule below changes,
> change it here first and make the code follow.

## The rule

**`last_verified` is the most recent date on which everything in the score was
confirmed still correct.**

That is the whole definition. Three consequences follow from it, and no other reading
is intended:

1. **"Everything" means every dimension the score records**, not only the ones the
   winning rule happens to read. `falcon-3` scores 2 the moment its license resolves
   to `use_restricted`, so its `data` and `code` values never affect the outcome — but
   they are still published claims, so they still have to be confirmed. A fresh
   license cannot carry a stale corpus claim.
2. **Confirmation means the axis was re-checked against its sources**, whether or not
   the value moved. A re-check that changes nothing is still a confirmation and still
   earns the date. This is what makes the field fill in as automation lands.
3. **A date is never derived from `sources[].accessed`.** See below.

## Why freshness is not `max(sources[].accessed)`

`accessed: 2026-06-08` says somebody opened that URL that day. `last_verified:
2026-06-08` says the conclusion was confirmed that day. The second is a stronger
claim, and deriving it from the first upgrades weak evidence into strong evidence
across every axis at once.

This was tried and reverted deliberately (#102). It is worth restating because the
mistake is easy to re-invent: any aggregate of access dates — max, min, per-dimension
min — is still a confirmation claim computed from readings. Changing the aggregation
does not fix the category error.

It is also, as it happens, the less accurate number. `max(accessed)` reported a median
staleness of 55 days when the files had in fact been revised a median of 35 days ago.

## The fallback: the score file's last commit date

Most axes carry no `last_verified` yet. For those, freshness falls back to **the last
commit date of `sources/scores/<slug>.yaml`**.

Somebody committed that file on that date and left the score standing, which is a
review rather than a reading. Git records it, and nobody can inflate it. As #102 put
it, the git history of a score file *is* its verification record.

**What the fallback does not claim.** For a file untouched since it was added, the
commit date dates the import, not a review. That is still the answer to the question
the report exists to ask — has anyone revisited this — but it is not a confirmation,
and `build/check_freshness.py` labels it `commit` rather than `verified` so the two
can never be conflated.

## Which date to use

| field | where | what it answers |
|---|---|---|
| `last_verified` | `sources/scores/<slug>.yaml`, per axis | Is this score still right? Authoritative. |
| score file commit date | git | Same question, weaker. Used when `last_verified` is absent. |
| `sources[].accessed` | `sources/scores/<slug>.yaml`, per source | When was this specific URL read? Evidence provenance. **Not freshness.** |
| `last_checked` | `currentai.scores.openness_computed` | When did the pipeline last read *any* admitted evidence. Diagnostic. **Not freshness.** |

## What it is for

Triage. A category whose oldest axis is 50 days old is a category to go and look at.
`build/check_freshness.py` reports per-category median and oldest, names the stalest
product, and takes `--max-age-days` to become a CI gate once enough axes carry a real
`last_verified` that gating would fail on genuine staleness rather than on the
pre-automation backlog.

## Known divergences, as of 2026-07-29

Recorded so nobody mistakes the current data for the rule.

- **`build/apply_scores.py` writes `last_verified` from the pipeline's `last_checked`**,
  which is the max over any admitted evidence. That contradicts the rule twice over: it
  is derived from access dates, and it takes the newest rather than requiring everything
  to have been confirmed. Consequences in the data today: 6 axes carry a date newer than
  some of their own evidence (`deepseek-v3-2`, `deepseek-v4-pro`, `phi-4`, `kimi-k2-6`,
  `mistral-large-3`, `minimax-m3`), and 4 carry a date that no source in the file was
  read on, because it came from a signal fetch (`pythia`, `apertus`, `olmo-3`,
  `lucie-7b`). Both need fixing in `apply_scores`, not by reinterpreting the rule.
- **`freshness_floor` in `currentai.scores.openness_computed`** is a per-dimension
  aggregate of access dates. It is the reverted backfill under another name and should
  be removed rather than refined.
