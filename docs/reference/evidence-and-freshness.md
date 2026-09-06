# Evidence and Freshness

The single normative home for score confirmation: what `last_verified` **means**, how an
axis **earns** one, and the gates that keep the two honest. For the reader-facing account
of the three axes see `docs/methodology.md`; when a rule here changes, change it here first
and make the code follow.

This document merges the former `freshness.md` (what the date means) and `verification.md`
(how it is earned). Part 1 is the meaning, Part 2 the mechanism, Part 3 the coverage rules.

---

# Part 1 — What `last_verified` means

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

Where an axis carries no `last_verified`, freshness falls back to **the date of the last
commit that changed what `sources/scores/<slug>.yaml` claims**.

Somebody committed that file on that date and left the score standing, which is a
review rather than a reading. Git records it, and nobody can inflate it. As #102 put
it, the git history of a score file *is* its verification record.

**When the fallback applies**, rather than how many axes are on it today: an axis with no
`last_verified` at all. Two things put an axis in that state — it is explicitly held in
`sources/verification_queue.yaml`, or nobody has confirmed it yet, which is where every newly
added product starts. The age gate below reads whichever signal an axis has.

The live count is in "Current state" further down, and `check_freshness` prints it. It is
recorded once in this document on purpose: the same number written in two places is how this
section spent a week disagreeing with the table below it.

A held axis reaches the payload as `basis: partial` rather than through the fallback — see
"What the payload publishes" below. The fallback covers products with **no** dated axis at all.

**Changed what it claims, not merely touched.** Some commits move a file without
reviewing it. The Phase 1a migration reshapes `openness.components` from a string into a
mapping in every score file, carrying a byte-identical `raw:` copy of the string it
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

### What the payload publishes, and the third basis

`build/freshness_payload.py` reduces the three per-axis dates to one per-product record, and
says which tier it used so the page can label the weaker claim rather than passing it off as
the stronger one:

| `basis` | means |
|---|---|
| `verified` | **every** axis carries a `last_verified`. The date is the **oldest** of them — see below. |
| `partial` | some axes are confirmed and at least one deliberately is not. The date is the oldest **confirmed** axis; `unconfirmed_axes` names the rest, and `verification_holds` carries the queue's reason where there is one. |
| `commit` | no axis carries a date. Falls back to the score file's last claim-changing commit — and still carries `unconfirmed_axes` and any holds, because a fully unconfirmed product is exactly where a hold most needs to be visible. |

**`partial` was added 2026-08-15, and its absence was a live defect.** The reduction took
`max()` over the axes that *had* a date and ignored the ones that did not, under a comment
claiming the result was "the date on which everything in the score was last standing". For a
product with a held axis that sentence is false, and three shipped that way — `falcon`,
`qualcomm-ai-engine-direct` and `aws-neuron` each published `basis: verified` over an axis
parked in `sources/verification_queue.yaml`.

The holds were honest inside the repo and invisible outside it. A held axis is a real
editorial state and must not be forced into a score to make a label tidy, so the payload
carries the state instead: **a product with a hold is publishable and visibly caveated.**

**The product date is the oldest confirmed axis, not the newest.** The rule at the top of this
document is that `last_verified` is the date on which *everything* was confirmed. Reduced to
one product-level date, "everything" is the constraint: a product whose axes were confirmed on
the 9th, 11th and 13th is defensibly current only through the **9th**. Publishing the 13th
says "at least one axis was confirmed then", which is a weaker claim wearing the stronger
one's label — the same overstatement as publishing a held axis as verified, in a less obvious
form. It was `max()` until 2026-08-15, and products whose axes carry differing dates are the
common case rather than an edge. `latest_axis_confirmation` carries the newest
date for anyone who wants "when was this last touched", emitted only where it differs.

Note what `partial` does *not* depend on. It follows from an axis being unconfirmed, not from
a queue entry — a hold explains an unconfirmed axis, and its absence does not make one
confirmed. An undated axis with no queue entry is still `partial`, and is separately a finding
for `check_freshness` and `sweep_status`.

## What it is for

Triage. A category whose oldest axis is 50 days old is a category to go and look at.
`build/check_freshness.py` reports per-category median and oldest and names the stalest
product. `--max-age-days N` turns that report into a gate: it exits non-zero if any
category's oldest axis is older than N days.

**The window is 45 days, temporarily.** The age-gate section below owns the number and holds
the reasoning; it is not restated here.

### Where the gate runs, and why not in `validate.yml`

**`.github/workflows/freshness.yml`, weekly, and nowhere else.** It is the only gate here that
fails on the passage of time rather than on something in a diff, and that difference decides
where it belongs.

Per-pull-request it would block work that has nothing to do with the stale category. Nobody can
clear it from within the offending pull request either: the remedy is to re-read a category
against its sources, which is a research pass (`skills/refresh-category`) ending in a pull
request of its own. An outside contributor adding one product would be handed a red check for a
category they have never touched and no way to turn it green. That is the failure mode
`parity.yml` is written to avoid — a gate that fails for a reason the person in front of it
cannot act on gets switched off.

Weekly rather than daily for the same reason parity is weekly: the cadence has to match the work
it polices. A category is re-read in one run, so all of its axes carry one date and all of them
age out together, and a few categories cross the 45-day line each week. A daily gate would
re-report the same cliff for as many days as the re-read takes, which is nagging rather than
information.

`validate.yml` runs the same report per pull request **without** `--max-age-days`, so it prints
and cannot fail. That is what makes a re-read pull request show, in its own check log, whether
the category it refreshed came back inside the window.

### What the fallback means under a gate

An axis with no `last_verified` is measured by its commit date, so a product added last week
passes the age gate without anybody having confirmed it. That is not the gate leaking: age and
confirmation are different questions, and "never confirmed" is `build/sweep_status.py`'s and
`build/check_verification.py`'s. The report prints how many of its ages rest on the fallback so
a pass can never quietly be resting on the weaker signal.

## The note is not the log

A score `note` says why the score is what it is. Between 2026-04 and 2026-08 the re-read passes
appended their own narrative to it — "Re-read 2026-08-13 - the source still says X … No change."
— until that text was 44% of all note prose, in 1,035 of 1,416 notes across 446 of 472 files.

Every fact those clauses state is already a field on the same record:

| The clause says | The field that holds it |
|---|---|
| when it was re-read | `last_verified` |
| that a source was fetched | `sources[].accessed`, `sources[].http_status` |
| that the source is unchanged | `sources[].content_sha256` |
| what the source says | `sources[].shows` |

And the product page already prints `Verified <date>` beneath the record, from `last_verified`.
So the prose was not adding a fact; it was moving a structured one into the copy a visitor reads
to understand a score, three times per product, once per axis.

**The rule.** A note holds durable reasoning: what was assessed, against what, and why that lands
on this rung. Anything whose truth depends on *when you read it* belongs in a field, not the note.
A re-read that finds nothing changed leaves no trace in the note — that is what `last_verified`
moving is for. A re-read that finds something changed edits the note to say the new durable thing,
not to narrate the discovery.

### Where the history lives

Removing the narrative from the note does not discard it. **The scoring history is the git
history of the score file**, which is complete, dated by commit, and maintained by the act of
committing rather than by anyone remembering to append a paragraph:

```bash
git log -p --follow sources/scores/<slug>.yaml     # every pass, with what each one changed
git log -L '/^  note:/,+20:sources/scores/<slug>.yaml'   # just one axis's note over time
```

An agent re-reading a product consults that before deciding a score has not moved. What it finds
there is richer than the prose ever was: not only what a previous pass concluded, but the exact
`content_sha256` it saw and the diff it produced.

This is a deliberate choice against the alternative — a `verification_log` field carried in the
score file and withheld from the payload. That would put the history where a file-reading agent
trips over it, at the cost of duplicating what git already holds and obliging every future pass
to maintain the copy. Duplicated history drifts; git's does not.

The public payload publishes `note` and `sources` verbatim, so anything written into a note is
published. That is the reason this boundary is a rule and not a style preference.

Cleaning the corpus is `skills/clean-score-notes/SKILL.md`, and issue #322 carries the audit.

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


---

# Part 2 — How an axis earns it, and the gates

## How an axis earns its date

**An axis earns `last_verified` when someone re-read its cited sources and re-derived its
value.** Not when a tool aggregated dates. Not when a value was copied forward.

Three consequences, and no other reading is intended:

1. **A re-check must be evidence-producing.** It records what was read and what that
   source showed, the way `sources[].shows` already does. A date that cannot be traced to
   a fresh observation is indistinguishable from a rubber stamp, and we have twice shipped
   the rubber stamp by accident (#108, #115).
2. **An agent re-reading a cited URL is a confirmation. The pipeline reading recorded
   values is not.** This is the distinction the whole plan below rests on, so it is worth
   stating precisely. When an agent fetches `https://…/model-card` and re-derives that the
   license is Apache-2.0, something outside the repo was consulted and the conclusion was
   re-established. When `apply_scores` reads `license:Apache-2.0` out of
   `sources/scores/foo.yaml`, computes on it, and writes a date back, the repo has been
   read to itself and nothing was confirmed.

   Who performed the re-check is not the test — re-derivability is. The first pass of
   `sources/scores/` was agent-authored, so authorship never established trust here and
   does not now. See the grading rule in `AGENTS.md`.
3. **A re-check that changes nothing still earns the date.** Confirming a value is
   unchanged is the normal outcome and the main point. Only recording the ones that moved
   would make the field a change log rather than a freshness measure.

### What may never write it

No tool that computes over already-recorded values. `build/apply_scores.py` writes
`openness.score` and `openness.class` and deliberately writes no date at all; the reasoning
is in its module docstring and in the divergence history below ("Both earlier divergences").

## The audit chain, and where it currently breaks

For a score to be auditable, a reader must be able to walk it back to something outside the
repo:

```
score  <-  the rule that fired      (category scoring_recipe)
       <-  the dimension values     (openness.components)
       <-  the evidence             (openness.sources[].shows)
       <-  a source                 (openness.sources[].url)
```

`openness.components` is either the legacy flat string or the structured mapping the corpus
is migrating to, one dimension at a time; every reader in this repo goes through
`build.check_rubric.components_of`, which returns the same key -> clause dict whichever
shape a given file carries, so the audit chain above holds unchanged either way.

A license is recorded differently from a dimension: as a LIST of parts, one per license the
product makes you accept.

```yaml
license:
- name: Apache-2.0
  detail: OSI
- name: per-task
```

`license_tier` resolves every part and the most restrictive governs, and it never splits a
value itself — so how many licenses there are is something the curator states rather than
something a reader infers from a `+`. Record one part when the product is governed by one
thing, even where the name contains a `+`: `culturax` records `follows mC4 + OSCAR-2301
terms` as a single part because that phrase is one declared name and neither operand is a
license. Every part must map to a tier or the whole value abstains, since an unmapped part
can only be more restrictive than the ones that mapped.

Three of those four links hold today. **The third does not.** `sources` is a flat list per
axis, so nothing records WHICH source establishes WHICH dimension. Measured on 2026-07-30:
324 of 470 openness axes cite exactly one source, asserted to establish `weights`, `data`,
`code` and `license` together. A reader cannot check that, and neither can a tool.

That is the gap that makes a re-check unfalsifiable, and closing it is what makes everything
below possible.

### `establishes`: per-dimension attribution

A source item gains an optional list naming the dimensions it settles:

```yaml
sources:
- url: https://huggingface.co/org/model
  shows: Apache-2.0 in the model card; safetensors weights downloadable
  accessed: '2026-07-30'
  establishes: [license, weights]
- url: https://github.com/org/model
  shows: pretraining configs and data-prep scripts in the repo
  accessed: '2026-07-30'
  establishes: [code, data]
```

Optional and forward-populated, so existing data is not retroactively invalid. The re-check
tooling writes it; the gates below apply only to axes that claim a confirmation.

### The invariant that makes a rubber stamp fail

> **`last_verified: D` is valid only if, for every dimension the score records, at least one
> source that `establishes` that dimension has `accessed >= D`.**

This is the mechanism, not a convention. Claiming a confirmation you did not perform now
requires also back-dating the `accessed` field of every dimension's source — and those are
what the content check below verifies.

**This validates a claimed date. It never derives one.** The distinction is the whole point
and it is easy to erode: someone will eventually notice that the invariant mentions
`accessed` and "simplify" it into `last_verified = max(accessed)`, which is #115 exactly.
Deriving the date asserts a confirmation nobody made; validating it rejects a confirmation
nobody could have made. the freshness rule above forbids the first and requires the second.

Note the aggregation direction, which is also load-bearing: the check is over EVERY recorded
dimension, so the binding constraint is the *least* recently re-read one. `max(accessed)`
across an axis would pass an axis where one dimension was re-read today and three were last
seen in June.

### Machine re-verification

`build/reverify.py` may write `accessed`, `http_status` and `content_sha256` on a source, and
`last_verified` on an axis, and only these, and only where every recorded dimension of the
axis has a digested source that `establishes` it and every such source re-fetched
non-transient and confirmed. The dimension set it demands a source for is not a second copy
of the gate's rule — it calls `build.check_verification.recorded_dimensions` directly, so a
non-evidence key like `free_text` is never treated as requiring one.

A source confirms one of three ways: the body is byte-identical (same `content_sha256`); the
source's recorded `shows` excerpt still occurs in the fresh body, after both sides are
whitespace-normalized and the body is tried through `html.unescape` (a placeholder `shows` —
see `check_verification.placeholder_shows` — never confirms this way); or, for a source
answering the `license` dimension from a GitHub license/repo API or a Hugging Face
model-info endpoint, the fresh response's SPDX id normalizes (through
`check_rubric.normalize_license`) to the same license already recorded, so long as the
recorded clause is a single license rather than a `+`-joined compound. Whichever path
confirms it, the source is rewritten with the fetch's actual `http_status` and its NEW
`content_sha256` — a shows match records that the page still says what the source was cited
for; the new digest is recorded so the next re-check compares against what was actually
read. It never derives a date, never records a transient fetch, and never touches an axis
whose evidence changed. A new verification date records a successful re-evaluation on that
date, not a claim that the fact was established or the source changed then. Ruling on #445
(2026-09): a byte-identical re-fetch confirms an openness dimension; adoption and
capability are excluded from machine re-dating because their sources carry numbers that
move. Their re-verification stays with the agent leg in `refresh-category`. Ruled again
2026-09-03 (#445 follow-up): byte identity is the wrong test for evidence pages that
legitimately re-render on every load, so shows-match and SPDX comparison are also
acceptable confirmations, on the terms above.

### Catching fabrication rather than just inconsistency

The invariant catches unsupported dates. It cannot catch a source that never said what
`shows` claims, or a URL that never existed. For that, the re-check tool records what it
actually fetched:

```yaml
- url: https://…
  accessed: '2026-07-30'
  http_status: 200
  content_sha256: 3f9a…          # of the fetched body at accessed time
```

A digest makes two later audits possible: a URL that 404s at re-check time was either never
real or has rotted, and a changed digest tells you the page moved under a claim that still
cites it. Neither is a hard failure on its own — pages legitimately change — but both are
reasons to re-check, and a *missing* digest on a newly claimed confirmation is a hard
failure, because it means the tool did not fetch anything.

**A digest is only ever the output of a fetch, and there is no other way to obtain one.** A
fabricated digest is worse than an absent one: an absent one fails the gate, while a fabricated
one passes it and then defeats the sampled re-fetch, which is the only thing that ever goes back
and checks whether a cited page says what it was recorded as saying. Three were fabricated on
2026-08-13 by padding truncated prefixes out to 64 characters, which is why this is stated here
rather than assumed. `docs/workflows/refresh-category.md` carries the command that produces one.

## The gates, and why they ratchet

Every failure mode this project has actually hit gets a mechanism, not a note. Cheap ones
gate every PR. The ones needing the network run periodically.

| gate | failure mode | mechanism | cost |
|---|---|---|---|
| invariant | a confirmation with no supporting evidence | the invariant above | free |
| digests | a claimed date with no fetch digest | required on axes claiming a confirmation | free |
| producible-pairs | an impossible score/class pair | the pair must be producible by some rule in the recipe | free |
| refetch | fabricated or rotted sources | sampled re-fetch, digest and `shows` token match | network, weekly |
| parity | repo and warehouse drifting apart | `build/check_parity.py`, a per-product differential | network, weekly |
| capability-anchors | a recorded peer comparison that does not hold | `relation` must agree with both scores, and a dated band's peer must be confirmed at least as recently | free |
| age | a corpus that was confirmed once and then quietly aged | `build/check_freshness.py --max-age-days 45`, scheduled weekly | free, weekly |

These were numbered G1-G6 until 2026-08-08. Older PRs and commit messages use the numbers.

The age gate is the last one on this table to arrive (2026-08-14) and the only one that fails on
the passage of time rather than on something in a diff. That is why it is scheduled rather than
per-pull-request: a contributor adding one product cannot re-read a category to turn it green, and
a gate nobody in front of it can act on is a gate that gets ignored. Step 5 below has the window
and its owner; the freshness rule above has the shape.

**They ratchet rather than switch on.** The invariant and the digest requirement apply only to
axes that carry a `last_verified`. So they cover exactly what has been done, never block progress,
and never permit a regression on ground already taken. A big-bang gate over every axis at once
would have failed on day one and been switched off, which is how gates die.

**The ratchet has closed.** That count was 137 when this section was written. The 08-13/14
sweep dated every axis, an audit then removed the confirmations it could not support, and the
08-16 reconciliation settled the last of those: as of the `baseline-472-2026-08-16` tag all
1,416 axes are confirmed and the queue is empty. So the invariant and the digest requirement
now cover every axis. The age gate above became possible only because coverage got this close:
gating on age while most axes carried no date would have measured the backlog rather than
staleness.

The queue being empty is a state, not a property. A hold is still the correct answer when
evidence contradicts a value, and the queue-consistency gate governs one when it exists — a
held axis may not carry a date at all. Read the live counts from `check_freshness`, not from
this paragraph.

The producible-pair check and the parity gate apply in full immediately — nothing has to be
populated first.

The parity gate runs on its own weekly schedule rather than inside the publish job.
Publishing pushes and materializes the static models; the three user models that read them do
not recompute on their own.

**The scoring-chain recompute is manual.** Those models carry a declared cron, and a declared
cron is not a schedule: they were set at the model-revision layer, the platform schedules from
the dataset, and run history shows every run of the `scores` dataset as `triggerType: MANUAL`.
Read the run history and check `triggerType` before believing any freshness claim that rests on
a cadence — see `docs/operations/deploy-models.md`.

**So parity is a drift-and-staleness detector, and it cannot tell those two apart.** A red
parity means the repo and the warehouse disagree; whether that is because the scoring logic
drifted or because nobody has recomputed since the last merge is a question for the run
history, and it is usually the second. That is also why parity is not chained onto a publish:
it would compare fresh rules against a warehouse that has not recomputed and fail for a reason
that is not a drift.

For a check now, refresh the three models by hand and run `check_parity`
(`docs/operations/deploy-models.md`).

The producible-pair check found 17 impossible pairs on its first run, not the two that were
known. `vellum`, `whylabs` and `tensorrt-llm` were recorded `4 / open_source`, a pair no rule
emits because 4 is `open_core`; five more were `2 / open_core`, which no rule emits either; and
nine carried a score of 3, which the software ladder cannot produce **at all**, its rungs being
1, 2, 4 and 5. All 17 were corrected by reading the products, in three groups:

- `2 / open_core` → `2 / source_available`. The class was wrong. `open_core` in this ladder
  means an OSI core with functionality withheld for a paid tier; these five have an open
  periphery around a closed engine, which is `source: partial`.
- score 3 → 2. The score was wrong. Every one of the nine is "you can read it and not run
  it freely" — a non-OSI restrictive license over public source, or a client standing in
  for a closed service — which the ladder scores at 2.
- `4 / open_source` → `5 / open_source`. The score was wrong. Each of the three publishes
  the whole self-hostable product under an OSI license with nothing withheld. The 4s
  encoded maturity or skepticism about the vendor's marketing, both of which belong on the
  adoption and capability axes and were already recorded there.

The producible-pair check caught something `check_rubric` could not: 16 of the 17 were sitting
in a category's `deferred` block, which excludes a product from reproduction. The check ignores
the evidence and asks only whether the pair exists in the ladder, so deferring cannot hide it.

### Two shared utilities, so the mechanism cannot be bypassed

- **`build/components.py`** — the only supported way to edit a `components` field. The
  block-safe rewriter with the reparse assertion. Many score files fold that
  scalar across lines, some across three or more, so any hand-rolled
  `^  components: (.*)$` substitution splices keys mid-string and corrupts the value
  silently. A shared helper means the next script cannot re-invent that. Generic over the
  field, so a score correction and a components edit are the same operation with the same
  assertion behind them.
- **`build/warehouse.py`** — the only supported way to read the warehouse, and it forces a
  cache-busting nonce. Results cache on query TEXT, so a fixed verification query returns
  its first answer forever and a tool reading through that cache reports success against
  stale data. It has already happened. `query()` has no parameter to switch the nonce off.

## Why openness can never be fully automated

By design, not for want of coverage. `all_recorded_dims_from_dataset` in
`currentai.scores.openness_computed` is the column that says so per axis, and it is false
almost everywhere. Of the recorded openness dimensions only `license` and `weights` have a
dataset route. `signal_routing.yaml` declares `data` research-only, and the
GitHub code route carries `settles_dimension: false` because a live repo establishes neither
a full training pipeline nor an ungated core. For software categories, `core_gated` needs a
pricing page read.

So every openness axis needs at least one read, permanently. Adoption and capability are
different in kind and can be automated — see the table below.

## What a capability confirmation attests to

Less than the other two axes, and the difference is worth stating before dates get written
across adoption and capability in step 3 — a paragraph now, rather than an audit of every one
of those dates later.

Capability is not measured on this map. Measured on 2026-08-08, 322 of 472 products record
`basis: feature_matrix` against 86 `benchmark`, and `value` is prose in every one of the 372
cases where it is populated — not a single bare number. There is no capability ladder in any of
the four rubrics, and `signal_routing.yaml` records the axis as effectively unroutable: both
external anchors are unbridged, and both rank *models*, so neither can say anything about a
training framework or a sandbox.

What actually places many bands is a comparison to a peer. Many products in the
corpus put themselves against another product in their own category — "one tier below the
Megatron-LM anchor", "mid-tier next to langfuse" — and in `finetuning_code` every note does
it. That comparison was the instrument, and it lived in an English sentence.

So it is recorded instead:

```yaml
capability:
  score: 4
  basis: feature_matrix
  relative_to: megatron-lm
  relation: one_below
```

**`relation` is arithmetic over two recorded integers, and it can be wrong.** That is the
point, and it is the producible-pair check's shape rather than the invariant's: two statements
of the same fact — the relation and the two scores — can disagree, and now one of them is
checkable. `build/check_capability.py` gates it, and it ratchets like the others, covering the
products that record a comparison rather than blocking on the ones that do not.

**A dated band cannot be fresher than the band it derives from.** If `trl` claims a
confirmation today while Megatron-LM's capability was last confirmed in June, `trl` is claiming
to have re-derived a comparison against a fact nobody re-read. This is the openness invariant's
insight applied to a different dependency: a date is worth no more than the least recently
confirmed thing underneath it.

### The evidence date and the comparison date are two dates

Stated as the rule, because the two get conflated and the conflation is what stopped the
comparison graph growing.

`capability.last_verified` dates **this product's own capability evidence**: the feature matrix
still reads as described, the benchmark number is still the published one. It ages the way any
axis ages, the 45-day freshness window applies.

`capability.comparison.last_attested` dates **the spacing between this product and a peer**. It
has a different lifecycle, because a comparison can go false with neither product changing: the
peer improves, a third product lands between them, or the category's discriminating rung is
rewritten. It is never derived from a source's `accessed` date, for the same reason
`last_verified` is not — opening a URL is a weaker claim than re-judging a conclusion.

The rule above binds the dependent's whole-axis date to the peer's whole-axis date. That is
sound but coarse, and it makes the comparison graph unable to grow: as the corpus expands, every
new product's natural peer was confirmed before the product existed, so a tranche can compare
its members only to each other. An edge that records its own attestation is freed from the
peer's axis date, and pays for that with its own evidence requirement: a source read on or after
`last_attested`, carrying `http_status` and `content_sha256`. The gate is
`build/check_capability.py`; `docs/reference/capability.md` is normative on the field shape.

**What a `content_sha256` match may prove, and what it may never prove.** A recorded digest that
reproduces from a live body is proof the fetch was real — SHA-256 preimages are not guessable, so
those bytes could only have come from that body. Where **every** source an axis cites reproduces,
that is a defensible basis for re-dating that axis's own `last_verified`, and it is worth
building. It is never a basis for dating a comparison. Not when the peer's sources reproduce, not
when both products' sources reproduce, because the thing that falsifies a spacing is a third
product that neither one cites. An attestation written on the strength of unchanged bytes is the
rubber stamp this apparatus was built to stop, wearing a digest.

So an attestation costs a real read of the peer. It is cheaper than a full anchor refresh in what
it **claims**, not in what it costs, and anyone who sells it as a shortcut will get the failure
mode back.

With that recorded, a capability `last_verified` means: **the feature matrix still reads as
described, and the comparison the band rests on has been re-derived against a peer confirmed at
least as recently, or attested on its own date under the split below.** It does not mean the band
was measured. Where `basis: benchmark`, it also
does not mean the benchmark was re-run — re-reading a published number is the claim, and the
number is a property of a harness-plus-model pairing rather than of the product alone.

Two things this deliberately does not do. It does not make capability derivable from evidence,
and the comparison itself still carries no cited source — recording it converts an
unfalsifiable claim into a falsifiable one, which is what `establishes` did for openness, and
`establishes` does not verify that a source says what it claims either. That is the sampled
re-fetch's job. Nor does it try to turn `capability.value` into structured components: at 61%
prose by `check_rubric`'s own measure, against the 71% that stopped `edge_hardware`, and with
four different instruments sharing one field name, there is no shared ladder at the end of that
work the way openness got four.

## Current state

| | count |
|---|---|
| axes total (472 products × 3) | 1416 |
| deliberately null — not claims | 46 (26 capability, 20 adoption) |
| **real claims to verify** | **1370** |
| of those, citing at least one source URL | 1370 |
| carrying a real `last_verified` | 1416 |
| explicitly held in `verification_queue.yaml` | 0 |
| distinct source URLs behind all of it | 1827 |

Read 2026-08-16. `check_freshness` reported median age 3d, oldest 8d, with no axis resting on
the commit-date fallback. Regenerate these rather than trusting them; the corpus grows most
weeks, and the figures in this table have already been wrong twice for exactly that reason.

The null axes are two different abstentions and both are deliberate. Capability is null where
the axis does not apply — datasets and a wire protocol are not capable of anything a benchmark
measures. Adoption is null where **no usage figure exists to band**, which is mostly the hosted
fine-tuning and evaluation features of a larger platform — Azure, OpenAI, Mistral, Together,
Vertex, Bedrock — none of which publishes a standalone number, plus the internal eval suites,
which have no users outside the lab that wrote them. Banding those on vendor prose would be
inventing the number, so the axis abstains instead.

Every real claim already cites a source. The work is not finding evidence; it is re-reading
what is cited. And the re-read surface is 1106 fetches, not 1370, because sources are shared.

### A null axis can earn a `last_verified`, and should

Settled 2026-08-13, because practice had diverged from silence: 9 of the 46 null axes carried
a date and 37 did not, with nothing saying which was right.

The table above excludes nulls from "real claims to verify", and that framing is correct about
one thing and misleading about another. A null is not a **claim** — nobody asserted a level. But
it *is* a **finding**: somebody went and looked, and the vendor publishes nothing. That finding
can be wrong, it can go stale, and it is exactly as re-checkable as any other:

> Re-read the page. If a figure has appeared, the abstention is over and the axis gets a band.
> If it has not, the abstention is re-confirmed and earns the date, the same way an unchanged
> value does.

This follows from a rule already stated above — *"a re-check that changes nothing still earns
the date"* — and refusing to date nulls would contradict it, treating "the answer is none" as
the one answer that cannot be confirmed.

**It is also load-bearing for coverage.** Products carrying at least one null axis are a real
slice of the corpus. If a null can never be dated, none of them can ever be fully verified,
however carefully anyone reads them — and the unreachable set is not random. It is almost entirely the hosted features sold
inside a larger platform, which is a real and interesting part of the map, not a rounding error.

Two things a dated abstention must still do:

- **Cite the page that publishes nothing**, with an `accessed` date and a `content_sha256`, so
  the absence decays like any other claim. An abstention with no source is not verifiable; it
  is just an empty field.
- **Say in the note what was looked for and not found** — "no jobs run, customers tuning or
  developer count is published" — so a later reader can tell a searched absence from an
  unexamined one.

What this does NOT license is abstaining to avoid work. `signal_routing.yaml`'s rule still
governs which way the doubt runs: abstain rather than substitute, but never abstain rather than
measure. If a figure exists and is countable, the axis owes a band.

**None of the 6 satisfied the invariant as first written**, which is worth recording because it
is the clearest evidence the invariant does something. `establishes` did not exist when those
dates were set, and beyond that the 2026-07-28 pass on the four model flagships re-read only
the dataset endpoint: `apertus`, `olmo`, `pythia` and `lucie-7b` all claimed a whole-axis
confirmation while citing 2026-06 reads for weights, code, checkpoints and license. Refetching
the 23 cited sources cleared it and turned up two things an exemption would have hidden — a
Lucie source URL that had never resolved as cited (missing the `/datasets/` segment, so the
Hub answered 401), and an `rwkv` `weights:open` claim with no source behind it at all.

### What automation can and cannot earn, per axis

Counted 2026-07-30, before the corpus reached 472 products. The per-axis totals have moved a
little since; the split has not.

| axis | axes | all sources signal-backed | can a fetch earn the date? |
|---|---|---|---|
| adoption | 470 | 204 (+68 partial) | **Yes** — the score IS a banded signal, so re-fetching re-derives it |
| capability | 446 | 198 (+55 partial) | **Yes where a benchmark row exists**; feature and internal-eval judgments need a read |
| openness | 470 | 272 (+86 partial) | **Never fully** — see above |

"Signal-backed" means every source the axis cites is on a host a fetcher already re-derives
automatically: the HF hub, GitHub, PyPI, LMArena, Artificial Analysis, OpenRouter.

## The age gate

`build/check_freshness.py --max-age-days 45` gates in
`.github/workflows/freshness.yml`, weekly. This is the entire point of having the field: a
category whose oldest axis is older than the window is a category to go and look at. A held
axis rides the commit-date fallback rather than evading the gate.

**The window is 45 days, temporarily, and returns to 30 four weeks after 2026-09-03 (#457).**
It is a judgment about how much re-reading the map is worth rather than anything derivable, so
it is owned here and not re-argued per category. Owner: Carl.

The raise exists because the whole corpus was dated in one August sweep and would have crossed
the 30-day gate together, between 09-07 and 09-12. The rolling re-verifier spreads those dates
over four weekly batches; once it has, the window reverts.

At 45 days the re-read is continuous rather than occasional: every category inside forty-five days is roughly three a week. Two things follow. A whole category shares one confirmation
date, because a category is re-read in a single run, so categories expire in cliffs rather
than drifting past the line one product at a time — that is the shape of the work, not a
backlog. And the sampled re-fetch will keep reporting drift on pages that change daily;
at this window that drift is noise, and a digest that *matches* remains the only thing it
positively proves.

The cliff is also why the gate is scheduled rather than per-pull-request, and weekly rather than
daily. Part 1 above has that argument and the shape of the workflow.


## Related

- `docs/reference/openness.md` — the openness ladders and license tiers
- `docs/reference/adoption.md` — the adoption axis, and why a band nothing can measure still has to age
- `docs/reference/capability.md` — the capability axis and what a capability comparison records
- `docs/workflows/refresh-category.md` — the procedure for re-reading a category to earn dates
- `docs/operations/deploy-models.md` — the warehouse chain the parity gate polices
