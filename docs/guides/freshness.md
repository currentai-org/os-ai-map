# Score Freshness Guide

What it means for a score to be current, which date answers that, and which dates
look like they answer it but do not.

> This is the data-consumer / query reference, and it is normative. For the
> reader-facing methodology see `docs/methodology.md`. When the rule below changes,
> change it here first and make the code follow.
>
> This guide defines what `last_verified` MEANS. For who may write one, how an axis earns
> it, and the plan for populating every axis, see `docs/guides/verification.md`.

## The rule

**`last_verified` is the most recent date on which everything in the score was
confirmed still correct.**

That is the whole definition. Three consequences follow from it, and no other reading
is intended:

1. **"Everything" means every dimension the score records**, not only the ones the
   winning rule happens to read. A model scores the moment its license resolves to a
   capped tier — `use_bounded` or `commercial_forbidden` — so its `data` and `code`
   values never affect the outcome, but
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

Most axes carry no `last_verified` yet. For those, freshness falls back to **the date of
the last commit that changed what `sources/scores/<slug>.yaml` claims**.

Somebody committed that file on that date and left the score standing, which is a
review rather than a reading. Git records it, and nobody can inflate it. As #102 put
it, the git history of a score file *is* its verification record.

**Changed what it claims, not merely touched.** Some commits move a file without
reviewing it. The Phase 1a migration reshapes `openness.components` from a string into a
mapping in all 472 files, carrying a byte-identical `raw:` copy of the string it
replaced, so no published value moves — and dating by touch would have republished 78 of
the first batch's 84 products as reviewed on the migration day. A commit date is only
defensible here because it dates a review, so a commit that reviewed nothing must not
supply one. Otherwise the fallback makes the same category error as `sources[].accessed`:
a weak signal promoted into a confirmation claim.

`build/check_freshness.py` decides this by content rather than by convention. It walks a
file's history newest-first and skips any commit whose two revisions of that file have
the same `score_projection` — the whole document, with only the two storage shapes of
`openness.components` reduced to one. Nothing has to be labeled or trailered, a commit
cannot assert a review the content contradicts, and it works retroactively.

Two exceptions worth knowing before you go looking for them.

**Reordering the clauses of a `components` string does not advance the date**, because the
projection compares clauses as a key -> clause mapping and a mapping has no order. This is
the one case where something visible on the page moves — the published string is emitted in
file order — while the date stands still. It is the right call on the rule as written,
since clause order is storage rather than claim, but it is a real gap between what a reader
sees change and what the date says changed.

**A `git mv` of a score file resets its date to the rename commit.** Attribution runs with
`--no-renames`, so a rename reads as a delete plus an add, and an add is where a slug's
history starts. A rename is exactly the kind of structural touch this fix exists to skip,
so the exception is deliberate rather than an oversight: with rename detection on, a pure
rename is score-neutral for the new path and the walk runs off the end of its history with
nothing to date it from. The cost is bounded because slugs are tier-level and immutable, so
a score file should not be renamed in the normal course of things.

**What the fallback does not claim.** For a file untouched since it was added, the
commit date dates the import, not a review. That is still the answer to the question
the report exists to ask — has anyone revisited this — but it is not a confirmation,
and `build/check_freshness.py` labels it `commit` rather than `verified` so the two
can never be conflated.

## Which date to use

| field | where | what it answers |
|---|---|---|
| `last_verified` | `sources/scores/<slug>.yaml`, per axis | Is this score still right? Authoritative. |
| score file commit date | git | Same question, weaker. Used when `last_verified` is absent. Dates the last commit that changed a claim, skipping ones that only changed storage. |
| `sources[].accessed` | `sources/scores/<slug>.yaml`, per source | When was this specific URL read? Evidence provenance. **Not freshness.** |
| `last_checked` | `currentai.scores.openness_computed` | When did the pipeline last read *any* admitted evidence. Diagnostic. **Not freshness.** |
| `fact_accessed` | `currentai.scores.openness_facts`, per dimension | When the evidence behind one dimension was read or fetched. Provenance, per fact. **Not freshness.** |

## What it is for

Triage. A category whose oldest axis is 50 days old is a category to go and look at.
`build/check_freshness.py` reports per-category median and oldest, names the stalest
product, and takes `--max-age-days` to become a CI gate once enough axes carry a real
`last_verified` that gating would fail on genuine staleness rather than on the
pre-automation backlog.

## Who may write `last_verified`

**A person, and only a person.** No tool in this repo writes the field.

`build/apply_scores.py` is the only thing allowed to change a score file without
somebody typing the value, and it writes `openness.score` and `openness.class`
exclusively. It cannot earn `last_verified`, and the reason is structural rather than a
matter of current coverage: of the recorded openness dimensions only `license` and `weights`
have a dataset route at all. `signal_routing.yaml` declares `data` research-only, and the
GitHub code route carries `settles_dimension = false`, so both resolve to document grade in
`currentai.scores.openness_facts`. Document grade means a human read some prose and wrote it
into the score file — so for those dimensions the pipeline is reading the repo back to itself,
which confirms nothing.

Nothing hardcodes that any more, which is worth stating because the older wording said the
scoring model pinned `data` and `code` to document grade by name. It does not: a dataset row
wins wherever its route carries `settles_dimension`, and those two routes do not. The
conclusion is unchanged and now rests on a declaration rather than on a special case.
`all_recorded_dims_from_dataset` in `currentai.scores.openness_computed` reports the outcome
per axis, and it is the column a guarded write-when-fully-confirmed branch would have to read.

Since "everything confirmed" can never be true of a pipeline run, there is no date for
it to write.

## Both earlier divergences, and how they were closed

Kept because the mistake is easy to re-invent, and was, twice.

- **`apply_scores` wrote a derived date into the field.** #108 wrote the freshness bound
  (MIN `accessed`); #115 replaced it with `last_checked` (MAX over the same dates).
  Between them they put a derived date on **19 of the 26 axes** that carried one. Six
  overwrote a date a person had established: `apertus`, `lucie-7b`, `olmo` and `pythia`
  each lost their #105 verification date to a signal fetch one day later.

  Closed by deleting the writer, and reverting what it had written. Tracing every stored
  date to the commit that set it put the 26 into three groups: **2** set by hand (#105
  `rwkv`, #113 `mastra`) and kept; **4** restored to the #105 date the tool had
  overwritten; **20** removed, because no constituent had ever been hand-confirmed. The
  20 are 15 the tool wrote outright plus 5 the #121 tier merge carried forward from
  tool-written release files — a merge confirms nothing, so it cannot originate a date.

  Coverage went 26 → 6 axes, which is the honest number: six axes have actually been
  checked by somebody. The other 20 fall back to their commit date, correctly labeled
  `commit` rather than `verified`.

  Restoring rather than keeping was the right call because these were never confirmation
  records. The rule that a stored date is never moved backwards protects a person's
  observation; it does not protect a tool's arithmetic.
- **`freshness_floor`** was a per-dimension aggregate of access dates — the reverted
  backfill under another name. Removed from the model rather than refined.

Where a tier had absorbed several release-level products, the restored date is the
**oldest** constituent confirmation, because the tier's score covers all of them and one
stale member bounds the whole thing. That is an aggregate over confirmations, not over
readings, so it is consistent with the rule above.

## Related

- `docs/guides/verification.md` — how an axis earns `last_verified`, and the gates
- `docs/guides/adoption.md` — the adoption axis, and why a band nothing can measure still
  has to age
- `docs/guides/openness-spectrum.md` — the openness ladders
