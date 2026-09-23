# Evidence and Freshness

The single normative home for score confirmation: what `last_verified` **means**, how an
axis **earns** one, and the gates that keep the two honest. For the reader-facing account
of the three axes see `docs/methodology.md`; when a rule here changes, change it here first
and make the code follow.

Part 1 is the meaning, Part 2 the mechanism, Part 3 the coverage rules. Part 0 is why any of it
runs, and it governs the rest: a check exists to **refute** a score, and confirmation is what is
left when refutation fails.

---

# Part 0 — A check tries to refute a score

**The purpose of re-checking a score is to find out whether it is wrong.** Confirmation is the
residue of a failed refutation, not the objective. Everything in Part 1 still defines what
`last_verified` means and when an axis earns one; this part says what a check is *for*, and
where the two suggest different designs, this one decides.

The distinction is not academic, because the two framings build different machinery. A check
built to confirm has to establish sameness, and where a source exposes no structured field the
only general way to do that is to compare its bytes — which is why most re-fetches return
"drift", why a page carrying a number that changes daily can never be stable, and why the cost of
re-checking came to look like a reason to do less of it. Machine re-verification already escapes
this where it can, accepting a recorded fragment or an SPDX id in place of byte equality; Part 0
is the general statement of why those are the right shape and byte comparison is the fallback. A check built to refute asks a narrower question with a
cheaper answer: **does anything we already collect disagree with the record?**

That question is cheap because the signal tables already carry the answers. A repository's
archived flag, its SPDX license id, a package's download volume, a model's gated flag — all
collected on a weekly cadence, all structured, none requiring a fetch when the question is asked. A
sweep over them costs a warehouse read.

## Drift is not a finding; a contradiction is

Keep the two apart, in reports and in the queue a person works through.

| | What it says | What it is about | What to do |
|---|---|---|---|
| **Drift** | the source does not read byte-for-byte as it did | the fetch | read what changed, *then* re-record — a changed source is evaluated before its baseline is replaced, and a light sweep never authorizes that replacement |
| **Contradiction** | a collected signal disagrees with the record | the score | settle it: correct the record, or record why the signal is not it |

A re-check that cannot tell the difference reports both as the same event, and then the real
finding is indistinguishable from the noise. `build/reverify.py`'s SPDX comparison is the older
example of getting this right — it compares a structured field rather than a page — and
`build/check_contradictions.py` is the general form.

A leg of such a sweep is only worth having once its abstentions are right, and that is the hard
part rather than the comparison. The license comparison is the worked example: the corpus records
a license as a name plus a qualification, and the qualification appears in the detail, in the
detail after the grade, inside the name, and as one scoped part of a compound. A comparison that
misses any of those reports records that were already correct, and a queue that does it twice is
a queue nobody reads. Abstain until the comparison can see everything the record says.

That leg now ships, and what finally made it possible was naming what the observation is ABOUT.
A repository license is a statement about code, so it may only be compared against a recorded
license that also covers that code. An explicit scope on the part decides it; where the record
states none, the product's type supplies the default, because a model's or a dataset's
unqualified license is about the weights or the data. Under a naive comparison every finding the
leg produced was a model or a dataset whose recorded license and repository license are supposed
to differ. Under the scope rule there are none.

A leg that abstains this often has to prove it looked, so the sweep reports its abstentions
grouped by the rule that fired. A run finding nothing and a run whose comparison silently broke
print the same line otherwise.

## Two passes, and they are not the same job

**The light pass** runs often, over the whole corpus, and asks only what the collected signals
can answer. It settles nothing and dates nothing; it raises. `build/check_contradictions.py` and
the weekly `contradiction-sweep` workflow are this pass, and
`evaluation.adoption_reconciliation` is the same shape for adoption, where a disagreement
explicitly leaves the date where it was.

**The heavy pass** takes one category and re-reads everything in it, including what no signal
covers — the prose, the components, the judgment calls. It is expensive, it is scheduled
deliberately rather than continuously, and it is the only pass that can move an axis it did not
already have a measurement for. `docs/workflows/refresh-category.md` is that procedure.

A light pass is not a cheap heavy pass. It cannot confirm an axis, because the signals it reads
cover a fraction of what a score records, and treating a clean light pass as confirmation would
date an axis on evidence that never looked at most of it.

## What a light pass must not do

- **Decide.** A signal disagreeing with a record is a question. An archived repository is a fact
  about a repository; `end_of_life` is a claim about a product, and a project may be archived
  because it moved, was absorbed, or ended — only the last of those ends the product.
- **Date anything.** See above: it has not looked at enough to confirm.
- **Fire on a comparison it cannot make.** An abstention rule is not a weakness of such a check,
  it is most of its value. A sweep that reports every difference between a record and a signal
  produces a queue nobody reads by its second week. The known abstentions: a signal describing a
  different artifact than the record does (a repository's license id against a model's weights
  license), a compound record with no single value to disagree with, and a source that reports it
  could not classify something, which is not the source disagreeing.

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
   earns the date. This is what makes the field fill in as automation lands. It is the
   definition of the field, not the purpose of running a check — see Part 0 — and it applies
   to a pass that looked at everything the axis records, which a light contradiction sweep
   by construction does not.
3. **A date is never derived from `sources[].accessed`.** See below.

## Two evidence grades: dataset and document

Evidence is graded by re-derivability, not by who produced it — the first pass of
`sources/scores/` was agent-authored, so authorship never established trust and does not now.
What matters is whether the value can be arrived at again:

| grade | what it is | how it's re-derived |
|---|---|---|
| `dataset` | a named field in a machine-readable source | running a query; carries the table, the column and the transform |
| `document` | a specific URL whose content asserts the value | reading it again; carries the url, what it shows, and when it was read |

`dataset` is preferred wherever it can answer, because a document is an interpretation of prose
and a dataset field is a lookup. `rwkv` is the case that settled it: its data-openness score of
5 rested on a paper's claim of a 3.1T open corpus, and what corrected it to 4 was the Hugging
Face datasets API showing the published repos hold a component index and 100k/1M previews, no
corpus. The document was plausible, traceable and wrong; the dataset was neither plausible nor
implausible, it was just checkable.

`sources/signal_routing.yaml` decides *which* source is authoritative per dimension;
`sources/evidence_policy.yaml` decides *whether* a given observation is admissible at all.

## Why freshness is not `max(sources[].accessed)`

`accessed: 2026-06-08` says somebody opened that URL that day. `last_verified:
2026-06-08` says the conclusion was confirmed that day. The second is a stronger
claim, and deriving it from the first upgrades weak evidence into strong evidence
across every axis at once.

The mistake is easy to re-invent, which is why it is stated as a rule rather than left
implicit: any aggregate of access dates — max, min, per-dimension min — is still a
confirmation claim computed from readings, and changing the aggregation does not fix the
category error.

An access date and a review date are also independent quantities, so neither bounds the other.
A page can be opened without the claim being re-read, and a claim can be re-read without any
page being fetched. An aggregate of `accessed` is therefore not a conservative `last_verified`
and not a generous one — it is a different measurement that happens to be a date, and it can
land on either side of the day the score was last confirmed.

## The fallback: the score file's last commit date

Where an axis carries no `last_verified`, freshness falls back to **the date of the last
commit that changed what `sources/scores/<slug>.yaml` claims**.

Somebody committed that file on that date and left the score standing, which is a
review rather than a reading. Git records it, and nobody can inflate it: the git history of
a score file *is* its verification record.

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
reviewing it. A storage migration is the clearest case: reshaping `openness.components` from
a string into a mapping carries a byte-identical `raw:` copy of the string, so no published
value moves, and dating by touch would republish a whole batch as reviewed on the migration
day. A commit date is only defensible here because it dates a review, so a commit that
reviewed nothing must not supply one. Otherwise the fallback makes the same category error as
`sources[].accessed`: a weak signal promoted into a confirmation claim.

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

**A `git mv` of a score file resets its date to that commit.** Attribution runs with
`--no-renames`, so moving a file reads as a delete plus an add, and an add is where a slug's
history starts. That is deliberate rather than an oversight: with rename detection on, a pure
move is score-neutral for the new path and the walk runs off the end of its history with nothing
to date it from. The cost is bounded because slugs are tier-level and immutable, so a score file
should not move in the normal course of things.

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

**`partial` is what keeps a hold visible outside the repo.** A reduction that takes `max()`
over the axes that *have* a date and ignores the ones that do not cannot mean "the date on
which everything in the score was last standing": for a product with a held axis that sentence
is false, and the product publishes `basis: verified` over an axis parked in
`sources/verification_queue.yaml`. A held axis is a real editorial state and must not be forced
into a score to make a label tidy, so the payload carries the state instead: **a product with a
hold is publishable and visibly caveated.**

**The product date is the oldest confirmed axis, not the newest.** The rule at the top of this
document is that `last_verified` is the date on which *everything* was confirmed. Reduced to
one product-level date, "everything" is the constraint: a product whose axes were confirmed on
the 9th, 11th and 13th is defensibly current only through the **9th**. Publishing the 13th
says "at least one axis was confirmed then", which is a weaker claim wearing the stronger
one's label — the same overstatement as publishing a held axis as verified, in a less obvious
form. Products whose axes carry differing dates are the common case rather than an edge.
`latest_axis_confirmation` carries the newest date for anyone who wants "when was this last
touched", emitted only where it differs.

Note what `partial` does *not* depend on. It follows from an axis being unconfirmed, not from
a queue entry — a hold explains an unconfirmed axis, and its absence does not make one
confirmed. An undated axis with no queue entry is still `partial`, and is separately a finding
for `check_freshness` and `sweep_status`.

### A hold is a claim about now, not a record of history

A hold in `sources/verification_queue.yaml` is a claim about the CURRENT state of an axis, and
nothing in the repository forces it to stay true. A later pass that settles the question writes
its finding into the score note, where the queue cannot see it — so a stale hold does not
announce itself; it just sits there, contradicted by a note nobody re-read. Before adding an
entry, read the axis's note and its source dates. Before trusting an existing one, do the same.

## What it is for

Triage. A category whose oldest axis is 50 days old is a category to go and look at.
`build/check_freshness.py` reports per-category median and oldest and names the stalest
product. `--max-age-days N` turns that report into a gate: it exits non-zero if any
category's oldest axis is older than N days.

**The window is 45 days.** The age-gate section below owns the number and holds the reasoning;
it is not restated here.

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

A score `note` says why the score is what it is. A re-read pass that appends its own narrative
to it — "Re-read 2026-08-13 - the source still says X … No change." — grows without bound,
because every pass adds a line and no pass removes one, and it ends up as the bulk of the prose a
visitor reads.

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
`tests/test_score_notes.py` holds it, and `skills/clean-corpus-prose/SKILL.md` is the pass that
rewrites a note found carrying one.

## Who may write `last_verified`

**Whatever actually confirmed the evidence.** A person, or a tool that re-read every
establishing source behind the axis and found each still says what it was cited for. What may
never write the field is a computation over already-recorded values, which confirms nothing by
construction — the rule under "What may never write it" below.

`build/reverify.py` is the tool that qualifies. It re-fetches every establishing source, accepts
a confirmation only on a byte-identical body, a shows-match or an SPDX comparison, and stamps the
date only when every recorded dimension is covered and nothing drifted, went transient or was
skipped. "Machine re-verification" below carries the terms and the axes it may do this on, and it
is narrower than this paragraph: openness only.

`build/adoption_freshness.py` is the second, and it qualifies on the same test read against a
different kind of axis. It confirms nothing by computing over the file: the band it compares
against comes from an observation a collector fetched, and it writes a date only where that
measurement reproduces the recorded band. "How an adoption date is earned" below carries the
terms, and it is narrower still: adoption only, and only on the instrument the score records.

`build/apply_scores.py` is the case on the other side of that line. It is the only other thing
allowed to change a score file without somebody typing the value, and it writes
`openness.score` and `openness.class` exclusively. It cannot earn `last_verified`, and the reason is structural rather than a
matter of current coverage: of the recorded openness dimensions only `license` and `weights`
have a dataset route at all. `signal_routing.yaml` declares `data` research-only, and the
GitHub code route carries `settles_dimension = false`, so both resolve to document grade in
`currentai.scores.openness_facts`. Document grade means a human read some prose and wrote it
into the score file — so for those dimensions the pipeline is reading the repo back to itself,
which confirms nothing.

Nothing hardcodes that: no dimension is pinned to document grade by name. A dataset row wins
wherever its route carries `settles_dimension`, and those two routes do not, so the conclusion
rests on a declaration rather than on a special case.
`all_recorded_dims_from_dataset` in `currentai.scores.openness_computed` reports the outcome
per axis, and it is the column a guarded write-when-fully-confirmed branch would have to read.

Since "everything confirmed" can never be true of a pipeline run, there is no date for
it to write.

## A derived date is removed, not kept

Two constructions re-invent themselves and both are forbidden: a pipeline writing an
aggregate of `accessed` into `last_verified`, and a per-dimension `freshness_floor` that is the
same aggregate under another name. Neither is refined into something acceptable. The writer is
deleted and what it wrote is removed, because a derived date was never a confirmation record in
the first place.

**The rule that a stored date is never moved backwards protects a person's observation; it does
not protect a tool's arithmetic.** Where a tool has overwritten a hand-set date, the hand-set
date is restored; where no constituent was ever hand-confirmed, the date is removed and the axis
falls back to its commit date, correctly labeled `commit` rather than `verified`. Coverage falls
when this is done, and the smaller number is the honest one. A merge confirms nothing, so a tier
merge cannot originate a date either.

Where a tier absorbs several release-level products, its date is the **oldest** constituent
confirmation, because the tier's score covers all of them and one stale member bounds the whole
thing. That is an aggregate over confirmations, not over readings, so it is consistent with the
rule above.


---

# Part 2 — How an axis earns it, and the gates

## How an axis earns its date

**An axis earns `last_verified` when its cited sources were read again and found to still carry
the value.** A person or an agent re-deriving it is the general case; `build/reverify.py`
confirming every establishing source under the terms in "Machine re-verification" is the
mechanical one, and it is narrower — see there for which axes it may do this on. Not when a tool
aggregated dates. Not when a value was copied forward.

Three consequences, and no other reading is intended:

1. **A re-check must be evidence-producing.** It records what was read and what that
   source showed, the way `sources[].shows` already does. A date that cannot be traced to
   a fresh observation is indistinguishable from a rubber stamp.
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

Three of those four links hold unconditionally. **The third holds only where `establishes` is
populated.** `sources` is otherwise a flat list per axis, so nothing records WHICH source
establishes WHICH dimension, and an axis citing one source is asserting that it establishes
`weights`, `data`, `code` and `license` together. A reader cannot check that, and neither can a
tool.

That is the gap that makes a re-check unfalsifiable, and `establishes` below is what closes it.

### Why `shows` has no minimum length

Length measures verbosity, not specificity. A 25-character floor throws out `'MIT License text'`
and `'13,834 monthly downloads'`, both short and completely specific, while keeping every filler
row like `flagship phase-C verification source`, which is long.

### Abstention values live on the route, not here

A value that means "this source has no answer" — GitHub's `NOASSERTION`, the Hub's `other` — is
a fact about a SOURCE, so it is declared once, on that source's route in
`sources/signal_routing.yaml`, as `abstain_values`. `evidence_policy.yaml` never repeats it. Two
declarations of one rule is exactly the drift this split exists to prevent, and `NOASSERTION`
declared in both files alongside `signal_routing.yaml`'s own `abstain_when` is the shape it
takes.

What `evidence_policy.yaml` owns instead is the abstention policy that is *not* source-specific.
A null value is an abstention from every source and needs no per-source interpretation. And a
declared artifact that does not resolve is not a signal, whichever source it came from — a 404, a
redirect, or an `artifact_id` naming an organization rather than a repository all produce nothing
rather than something weak.

### `establishes`: per-dimension attribution

A source item may carry a list naming the dimensions it settles:

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

It is optional, so an axis written without it is not retroactively invalid. The re-check
tooling writes it; the gates below apply only to axes that claim a confirmation.

### The invariant that makes a rubber stamp fail

> **`last_verified: D` is valid only if, for every dimension the score records, at least one
> source that `establishes` that dimension has `accessed >= D`.**

This is the mechanism, not a convention. Claiming a confirmation you did not perform now
requires also back-dating the `accessed` field of every dimension's source — and those are
what the content check below verifies.

**This validates a claimed date. It never derives one.** The distinction is the whole point
and it is easy to erode: someone will eventually notice that the invariant mentions
`accessed` and "simplify" it into `last_verified = max(accessed)`, which is the derived-date
error above.
Deriving the date asserts a confirmation nobody made; validating it rejects a confirmation
nobody could have made. The freshness rule above forbids the first and requires the second.

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
source's recorded `shows` still checks out against the fresh body, after both sides are
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
whose evidence changed.

**What "the `shows` still checks out" means, and why it is not the whole sentence.** A
`shows` is only occasionally an excerpt. Far more often it is a curator's sentence *about*
the page with the verbatim material quoted inside it — *repo page carries the label "Public
archive" and the banner "This repository was archived by the owner on Jul 4, 2026"* — and a
sentence of that shape never occurs on the page it describes. Testing the whole of it tests
the curator's prose. So the whole sentence is tried first and still confirms where it fires,
and failing that the **quoted fragments** are tried: every fragment quoted inside the `shows`
must occur in the fresh body, and at least one of them must be at least
`reverify.MIN_FRAGMENT_CHARS` (24) characters long.

Both conditions are load-bearing. *Every* fragment, because a `shows` that quotes nine things
and finds two of them has been contradicted rather than confirmed, and "at least one matched"
is the rubber stamp this whole apparatus exists to prevent. *At least one long fragment*,
because the short quoted material in this corpus is overwhelmingly JSON key names and license
ids — `license`, `spdx_id`, `MIT` — which occur on every page of the kind being cited and so
prove nothing; a short fragment must still be present, it simply cannot be what earns the
date. A `shows` that quotes nothing keeps the whole-sentence test and nothing else, so saying
less never makes a source easier to confirm. The whole-sentence test confirms a small minority of
drifted sources on its own, which is why the fragment path exists at all.

A sentence whose quote marks do not pair off gets no fragment test at all. The unclosed quote
opens a claim whose text cannot be recovered — *the banner reads "Archived* — and confirming on
the fragments that did close would re-date the source on a strict subset of what it claims,
against a page that need not carry the missing claim anywhere. It keeps the whole-sentence test
and otherwise drifts to the agent leg, where a person can read both the sentence and the page.

A new verification date records a successful re-evaluation on that date, not a claim that the
fact was established or the source changed then. A byte-identical re-fetch confirms an openness
dimension; adoption and capability are excluded from re-dating by re-fetch because their sources
carry numbers that move. Capability's re-verification stays with the agent leg in
`refresh-category`; adoption's has a mechanism of its own, which re-measures the band instead of
re-reading the page — see "How an adoption date is earned". Byte identity is not the only
acceptable confirmation, because evidence pages legitimately re-render on every load, so
shows-match and SPDX comparison also confirm, on the terms above.

### How an adoption date is earned

Adoption is the one axis a machine can re-derive outright, because the band IS a measurement: a
usage figure, placed on a declared scale. So its date comes from the measurement, and the
mechanism is a comparison rather than a re-fetch.

Each week the reconciliation compares what the authoritative route measures for a product
against the band the score records, and each row reaches one of two outcomes:

* **The measured band equals the recorded one.** The recorded band has been re-derived from
  outside the repository — a collector fetched the figure, the warehouse recorded it with the
  time of the fetch, the routing tables banded it — so `adoption.last_verified` takes the date of
  that observation, and the axis records which snapshot and which route produced it under
  `derived_from`.
* **The measured band differs.** Nothing was confirmed. The stored date stays exactly where it
  is, and the product goes on the tier-change queue naming both levels and the route, for a
  person to settle. A run that disagrees with a score never writes to that score, and a date it
  declines to move is the normal outcome rather than a failure.

**A match is not an agreement until the run is attributable.** A current-state table cannot show
that a collector ran: a successful collection, a failed collector whose previous table stayed
readable, and a source that never ran at all leave the same rows behind. An equal band is a
comparison until something names the run the rows came from. So the reconciliation reads the
current observations inside a bracket — the model's newest materialization is read from the
control plane before the rows and again after — and a read served by one materialization
throughout is bound to that materialization's run, which is recorded on the axis beside the date.
A read that cannot be bound, because a refresh landed mid-bracket or because it came from the
frozen baseline, dates nothing at all, and emits its queue exactly as it otherwise would.

That attribution is of the read rather than of each observation, and the date is what covers the
difference. Where a collector has failed and the table is still serving last week's figures, what
gets written is those figures' own observation date: staleness is recorded rather than laundered
into currency.

**The run has to be the scheduled one.** Only a run the platform recorded as `SCHEDULED`, and
as having succeeded, may earn a date. A `MANUAL` run is a person refreshing a table, and a date
taken from one would be that person's date carrying a run id — which is the dependency this
mechanism exists to remove. The rule is also what makes the weekly claim checkable rather than
asserted: a cron that is configured and never fires produces no scheduled materialization, so no
date is earned and the run says why. A configured schedule is not evidence that a schedule ran;
an observed `SCHEDULED` run is. The trigger is read from the control plane at the moment of the
read and written into the snapshot ledger beside the measurement, because the control plane will
not answer for a run indefinitely and the gate has to be able to ask years later.

**The measurement is recorded twice.** The axis carries `derived_from` — the snapshot, the run,
the route, the level that was measured and the date it was observed — and the snapshot ledger
carries the same measurement under the product's slug, plus how the run that produced it was
started. The gate requires the two to agree, so a
date, a level or a route edited on one side alone fails; a single self-describing record can only
be checked against itself. The measured level is part of the support for the same reason. The run
confirmed the band it measured, so once a person re-bands the axis the confirmation describes a
band the score has left, and the date has to be earned again rather than inherited by the new
level.

Three things that date is not.

1. **Not the run's execution date.** The date written is the OLDEST observation behind the
   aggregate, so a figure is dated when it was observed. A run comparing month-old observations
   has confirmed a month-old figure, and stamping it with today would claim a currency nobody
   has.
2. **Not `sources[].accessed`.** The rule in Part 1 holds here exactly as it holds elsewhere:
   opening a URL is a weaker claim than re-deriving a conclusion, and this mechanism derives
   nothing from the dates already in the file.
3. **Not a comparison across instruments.** A route measuring stars says nothing about a band
   read from monthly downloads: the two levels neither agree nor disagree, so such a row can
   never date an axis. Where its levels differ it is queued as a route disagreement, because the
   finding is that the recorded instrument and the applicable route disagree about what to
   measure, and that repair is not a re-banding.

**A snapshot id has to resolve to a date.** The observation snapshot is content-addressed: the
id is a hash of the observations themselves and carries no calendar information at all, so a
score file recording one would be unauditable on its own. `sources/snapshots/observation_snapshots.yaml`
resolves each id to the window its observations cover, and the invariant requires a derived date
to fall inside the window of the snapshot it names. A date outside that window, or a snapshot
nothing recorded, fails the gate.

**What the counts-endpoint citations are for.** Most adoption citations point at an endpoint
whose body is a number that moves every day — a downloads count, a star count, a monthly total.
A digest over such a body proves a fetch really happened and records where the figure came from,
which is what the sampled re-fetch checks and what keeps a fabricated citation catchable. It is
not evidence that the figure is current: unchanged bytes on a counts endpoint would mean the
number had stopped moving, which is a stronger claim than the axis needs and usually a false
one. So those citations stay, as provenance, and the date rests on the observation instead.

**Who writes it.** `build/adoption_freshness.py`, and nothing else. `build/reverify.py` refuses
adoption at the flag, in the planner and in the writer, so a machine cannot re-date the axis by
re-fetching a cited page whatever it is asked to do. Two tools writing one field on two
different grounds is the state this avoids.

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
and checks whether a cited page says what it was recorded as saying. Padding a truncated prefix
out to 64 characters produces a digest of exactly that kind, which is why this is stated rather
than assumed. `docs/workflows/refresh-category.md` carries the command that produces a real one.

### Which arXiv URL to cite

An arXiv abstract page carries the title, the authors, the abstract and the submission history.
Tables, figures and appendices are not on it. So cite `https://arxiv.org/pdf/<id>` whenever the
claim rests on something in the body, and `https://arxiv.org/abs/<id>` only for what the abstract
page itself carries: the abstract's own wording, the authorship, a withdrawal notice. Do not cite
`https://arxiv.org/html/<id>vN`, which does not exist for older papers and whose version suffix
goes stale.

A digest over a PDF is a digest over a binary, so reading one back means `pdftotext` first. That
is the smaller cost: an abstract page cited for a table or a figure it does not carry is a claim
that is unfalsifiable as recorded. `build/check_citations.py` gates it, on the record's own words
rather than on a fetch, so it is free and runs per pull request.

## The gates, and why they ratchet

Every failure mode this project has actually hit gets a mechanism, not a note. Cheap ones
gate every PR. The ones needing the network run periodically.

| gate | failure mode | mechanism | cost |
|---|---|---|---|
| invariant | a confirmation with no supporting evidence | the invariant above | free |
| digests | a claimed date with no fetch digest | required on axes claiming a confirmation | free |
| producible-pairs | an impossible score/class pair | the pair must be producible by some rule in the recipe | free |
| refetch | fabricated or rotted sources | sampled re-fetch, digest and `shows` token match | network, weekly |
| parity | repo and warehouse drifting apart | `build/check_parity.py`, a per-product differential; a whole category present on one side only is reported as taxonomy lag and fails only past 14 days | network, weekly |
| citations | an arXiv `/abs` cited for a claim only the paper body carries | `build/check_citations.py`, on the record's own locator | free |
| capability-anchors | a recorded peer comparison that does not hold | `relation` must agree with both scores, and a dated band's peer must be confirmed at least as recently | free |
| age | a corpus that was confirmed once and then quietly aged | `build/check_freshness.py --max-age-days 45`, scheduled weekly | free, weekly |

The age gate is the only one that fails on the passage of time rather than on something in a
diff. That is why it is scheduled rather than per-pull-request: a contributor adding one product
cannot re-read a category to turn it green, and a gate nobody in front of it can act on is a gate
that gets ignored. "The age gate" below has the window and its owner; the freshness rule above has
the shape.

**They ratchet rather than switch on.** The invariant and the digest requirement apply only to
axes that carry a `last_verified`. So they cover exactly what has been done, never block progress,
and never permit a regression on ground already taken. A big-bang gate over every axis at once
would have failed on day one and been switched off, which is how gates die.

**The ratchet is closed.** Every axis in the corpus carries a confirmation and the hold queue is
empty, so the invariant and the digest requirement cover every axis rather than a subset. The age
gate is only meaningful at that coverage: gating on age while most axes carried no date would
measure the backlog rather than staleness.

An empty queue is a state, not a property. A hold is still the correct answer when evidence
contradicts a value, and the queue-consistency gate governs one when it exists — a held axis may
not carry a date at all. Read the live counts from `check_freshness`, not from this paragraph.

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

The producible-pair check asks one question — can any rule in the category's recipe emit this
score with this class — and it finds things `check_rubric` cannot, because a product in a
category's `deferred` block is excluded from reproduction but not from this check. It ignores the
evidence entirely, so deferring cannot hide a pair.

**It reports a pair, not a repair.** The gate's own message says so — one of the two values is
wrong, and the product settles which. Read the recorded components against the ladder: they are
what the recipe keys on, so they are what decides whether the score or the class has to move.
Widening the ladder to admit the pair is never the remedy.

The software ladder emits five pairs and nothing else, and every software category inherits it
unchanged through `extends: software`:

| score | class | the components that reach it |
|---|---|---|
| 1 | `closed` | `source: closed` |
| 2 | `source_available` | `source: partial`, or a `competition_restricted` license over public source |
| 3 | `source_available` | a `permissive_non_osi` license over public, ungated source |
| 4 | `open_core` | an OSI license over public source with a gated core |
| 5 | `open_source` | an OSI license over public, ungated source |

Two impossible pairs are worth spelling out, because each sits between two rungs that a
hand-entered value slips across.

- **`2 / open_core`.** `open_core` in this ladder means an OSI core with functionality withheld
  for a paid tier. An open periphery around a closed engine is `source: partial`, which reaches
  `2 / source_available`, so here it is the class that moves.
- **`4 / open_source`.** The two top rungs differ in one component, `core-gated`. Whether the
  record settles at `4 / open_core` or `5 / open_source` depends on what the vendor's pricing
  page supports, and either value may be the one that moves.

A mixed category has one ladder per product type, and each product is checked against its own
rather than against the union of the category's variants. `sources/rubrics/*.yaml` carries each
formula, and the model, dataset and hardware ladders emit their own pairs.

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

This is a statement about **deriving** an openness score, not about **confirming** one that was
already derived. A dimension nothing can settle from a dataset still has to be read by somebody
the first time; re-reading its cited source later to check it still says the same thing is a
different operation, and `build/reverify.py` does it under the terms in "Machine re-verification".

## What a capability confirmation attests to

Less than the other two axes, and the difference is worth stating before dates get written
across adoption and capability in step 3 — a paragraph now, rather than an audit of every one
of those dates later.

Capability is not measured on this map. Most bands carry `basis: feature_matrix` rather than
`benchmark`, `value` is prose wherever it is populated rather than a bare number, there is no
capability ladder in any of the four rubrics, and `signal_routing.yaml` records the axis as
effectively unroutable: both external anchors are unbridged, and both rank *models*, so neither
can say anything about a training framework or a sandbox.

What actually places many bands is a comparison to a peer. Many products in the
corpus put themselves against another product in their own category — "one tier below the
Megatron-LM anchor", "mid-tier next to langfuse" — and in `finetuning_code` every note does
it. That comparison is the instrument, and in an English sentence it is unreachable.

So it is recorded as data:

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
that is a defensible basis for re-dating that axis's own `last_verified`, and it is now built:
`build/reverify.py` does exactly this. The permission is narrower than the principle, on purpose:
machine re-dating is limited to **openness**, because adoption and capability cite numbers that
move — there, unchanged bytes would confirm a figure that has gone stale rather than a fact that
has stayed put. The tool enforces that limit rather than describing it. `--axes` refuses any axis
but openness, and refuses a name that is not an axis at all, since a name matching no axis plans
nothing and reports a clean run over zero dimensions. The check binds to the write as well as to
the flag:
`reverify_product` refuses a policy-breaking axis, and `apply`, the function that actually
writes the field, refuses a result stamped for one however it was assembled. It is
never a basis for dating a comparison. Not when the peer's sources reproduce, not
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
unfalsifiable claim into a falsifiable one, which is what `establishes` does for openness, and
`establishes` does not verify that a source says what it claims either. That is the sampled
re-fetch's job. Nor does it try to turn `capability.value` into structured components: the field
is mostly prose, on the same measure that stopped `edge_hardware`'s ladder, and four different
instruments share the one field name, so there is no shared ladder at the end of that work the
way openness has four.

## The verification sweep's bookkeeping

`build/sweep_status.py` derives where the sweep has got to from the corpus rather than from a stored pointer, and `/goal` (`refresh-all-categories`) asks it which category is next. The rules it implements:

### What "done" means for a product

The bar is per product rather than per axis:

  * every axis carries a real `last_verified`, or abstains deliberately (a null value, which
    `evidence-and-freshness.md` explains for the axes that have one), or the product is held;
  * held products count as resolved, not as remaining. A product whose evidence cannot be
    settled goes into `sources/verification_queue.yaml` with a reason and stops blocking its
    category, which is what let the pilot ship five of six.

The prose has no part in "done". A dated `Verified … via` line in `comments` is the one thing
about the prose a checker can see, and it is a third copy of the axis dates rendered as a
footnote about the product, so the field carries no such marker: the prose half of a refresh is
held by `product-copy.md`'s rules and the reviewer. `build/product_prose.py` checks that the line
has not come back.

Deliberately NOT counted as done: an axis whose value is null because nobody looked. The two
are indistinguishable in the file today, which is the gap the per-axis deferral idea closes.
Until that exists this over-counts, and `--verbose` prints the null axes so the number can be
read with that in mind.

### Order

Worst artifact coverage first, so the categories where automation helps least go while the
sweep is cheapest to change. Coverage is measured locally as the share of a category's products
carrying a routable artifact block, which is the same thing `check_routing` counts and does not
need the warehouse.

### Refreshing rather than finishing

Once a category is gate-clean it stays "done" forever, which is wrong the moment a confirmation
ages: `last_verified` is a claim about a day, and the map keeps moving. `--max-age-days` (or
`--since`) reads a confirmation older than the window as `stale` rather than `verified`, so the
same tooling that drove the first pass drives the recurring one. Prose has no date of its own
and ages with the axes it was written beside.

## Current state

| | count |
|---|---|
| axes total (763 products × 3) | 2289 |
| deliberately null — not claims | 84 (45 capability, 39 adoption) |
| **real claims to verify** | **2205** |
| of those, citing at least one source URL | 2205 |
| carrying a real `last_verified` | 2289 |
| explicitly held in `verification_queue.yaml` | 0 |
| distinct source URLs behind all of it | 2963 |

Read 2026-09-20. Regenerate these rather than trusting them; the corpus grows most weeks, and a
number typed into a guide is stale the week after it is typed. The shape is what the table is
for: every axis is dated, every real claim cites something, and nothing is held.

The null axes are two different abstentions and both are deliberate. Capability is null where
the axis does not apply — datasets and a wire protocol are not capable of anything a benchmark
measures. Adoption is null where **no usage figure exists to band**, which is mostly the hosted
fine-tuning and evaluation features of a larger platform — Azure, OpenAI, Mistral, Together,
Vertex, Bedrock — none of which publishes a standalone number, plus the internal eval suites,
which have no users outside the lab that wrote them. Banding those on vendor prose would be
inventing the number, so the axis abstains instead.

Every real claim cites a source. The work is not finding evidence; it is re-reading what is
cited, and the re-read surface is smaller than the claim count because sources are shared across
axes and across products.

### A null axis can earn a `last_verified`, and should

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
however carefully anyone reads them — and the unreachable set is not random. It is almost entirely
the hosted features sold inside a larger platform, which is a real and interesting part of the
map, not a rounding error.

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

**A whole-axis claim resting on a partial re-read is what the invariant exists to catch**, and
it is the failure a hand-dated axis falls into most easily: a pass re-reads the dataset endpoint,
dates the axis, and leaves the weights, code, checkpoint and license citations months behind. The
remedy is refetching every cited source, and it turns up things no exemption would have — a source
URL that never resolved as cited, or a dimension claim with no source behind it at all.

### What automation can and cannot earn, per axis

| axis | can a fetch earn the date? |
|---|---|
| adoption | **Yes** — the band IS a measurement, so a route that re-measures it re-derives the score. "How an adoption date is earned" has the mechanism |
| capability | **Yes where a benchmark row exists**; feature and internal-eval judgments need a read |
| openness | **Never fully** — see above |

What decides it per axis is whether every source the axis cites sits on a host a fetcher already
re-derives automatically: the HF hub, GitHub, PyPI, LMArena, Artificial Analysis, OpenRouter.

## The age gate

`build/check_freshness.py --max-age-days 45` gates in
`.github/workflows/freshness.yml`, weekly. This is the entire point of having the field: a
category whose oldest axis is older than the window is a category to go and look at. A held
axis rides the commit-date fallback rather than evading the gate.

**The window is 45 days.** It is a judgment about how much re-reading the map is worth rather
than anything derivable, so it is owned here and not re-argued per category. Owner: Carl.

It is the steady state, not a raise waiting to be reverted. Forty-five is what the re-reading
rate can actually hold: the rolling re-verifier reads 150 products a week and re-dates roughly
one in eight, because most cited pages have moved and a moved page confirms nothing. Against
2,289 axes that is not enough throughput to keep a 30-day line, and measuring it says so
plainly — at a 30-day window more than half the corpus would sit outside it, with the median
at 35 days and nothing older than 45.

Narrowing the window is therefore a decision about throughput, not about the number. It needs
either more re-reads that confirm — which means attacking why a re-read fails, not the batch
size — or a narrower scope for what the window governs. Changing the number alone would move
the whole corpus out of policy on the day it changed and report a backlog nobody created.

At 45 days the re-read is continuous rather than occasional: every category inside forty-five
days is roughly three a week. Two things follow. A whole category shares one confirmation date,
because a category is re-read in a single run, so categories expire in cliffs rather than
drifting past the line one product at a time — that is the shape of the work, not a backlog. And
the sampled re-fetch will keep reporting drift on pages that change daily; at this window that
drift is noise, and a digest that *matches* remains the only thing it positively proves.

The cliff is also why the gate is scheduled rather than per-pull-request, and weekly rather than
daily. Part 1 above has that argument and the shape of the workflow.


## Related

- `docs/reference/openness.md` — the openness ladders and license tiers
- `docs/reference/adoption.md` — the adoption axis, and why a band nothing can measure still has to age
- `docs/reference/capability.md` — the capability axis and what a capability comparison records
- `docs/workflows/refresh-category.md` — the procedure for re-reading a category to earn dates
- `docs/operations/deploy-models.md` — the warehouse chain the parity gate polices
