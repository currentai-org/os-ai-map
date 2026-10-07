# Rulings

`log.yaml` in this directory is the record of every decision a maintainer made that an agent
could not: a license reading the ladder does not name, a category boundary, a methodology call,
how a class of proposals should be handled from now on. It exists so a settled question is
never asked twice, and so an agent that applies a ruling can cite the ruling it applied.

It is a **record**, like `docs/sweeps/` and `docs/briefs/`, not a reference document. A ruling
that changes a rule is written into that rule's normative home (a reference doc, an ADR, a
workflow, a category's `scoring_recipe`), and the entry here points at that home with
`lands_in`. The log says who decided what and why; the home says what the rule is. Two
statements of one rule is the failure `docs/README.md` warns about, so the log never becomes
the place a rule is looked up.

## Where a decision is recorded

Some decisions already have a machine-read home, and those stay there:

| Decision | Home |
|---|---|
| An axis a pass could not settle, held with a reason | `sources/verification_queue.yaml` |
| A contradiction finding the record was right about | `sources/contradictions_settled.yaml` |
| An identity merge or split | `sources/resolution_ledger.yaml` |
| A new category's creation, seeding and promotion calls | `docs/sweeps/` |

This log carries everything else: rulings from a `ruling-session`, answers to a blocked OSO
agent task, a one-comment ruling on a GitHub issue, and a reviewer's call on a PR's "Needs a
ruling" section. When a ruling is also written into one of the homes above, record it here too,
so the log remains the one place to check before asking.

## An entry

```yaml
- id: R-2026-09-30-a          # R-<date>-<letter>, unique, never reused
  date: 2026-09-30            # when it was decided, not when it was written down
  by: ccerv1                  # the GitHub handle of the person who decided
  venue: session              # session | walk-and-talk | oso-task | issue | pr-review
  refs: [OSO-5769, "#811"]    # issues, PRs, tasks, products or categories it concerns
  question: >-
    What was asked, in one or two sentences, precise enough that the same question
    can be recognized when it comes round again.
  ruling: >-
    The decision, stated as a decision, in the decider's voice.
  reasoning: >-              # optional; the decider's reason, in their words
  status: in-force            # in-force | deferred | replaced
  executor: agent             # agent | maintainer | none -- who carries it out
  lands_in: []                # repo paths that now state the rule, once written
  applied_in: []              # PR URLs that carried it out
  replaced_by:                # the id of the ruling that replaced it, when status is replaced
```

Rules the gate (`tests/test_rulings.py`) enforces:

- Entries are appended in date order and never deleted. A ruling that is changed gets a new
  entry, and the old one moves to `status: replaced` with `replaced_by` naming the new id. That
  is the only edit an existing entry may receive besides filling in `lands_in` and `applied_in`.
- A `deferred` entry was asked and not answered. Its `ruling` says so, and its `reasoning`
  carries the reason given, so the next session knows whether the question is ready to come
  back. `build.review_queue` surfaces it.
- Every `lands_in` path exists.

Two things are checked by the `audit-repo-accuracy` skill rather than by a test, because each
needs reading: an `in-force` ruling that changes a rule but has no `lands_in`, and a `lands_in`
home that no longer says what the ruling says.

## Who writes here

A `ruling-session` writes its rulings after the confirmation read-back. The applier routine
fills in `applied_in` when its PR opens. Anyone recording a one-off ruling from an issue or a
review adds an entry in the same PR that acts on it. Every entry lands through a PR, like
everything else in the repository.
