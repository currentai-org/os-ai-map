# Sibling invariants

A record of every place in `build/` where the same fact was stated twice, and what was done
about each. Written 2026-08-15 after four defects of that exact shape shipped in a fortnight.

## Why this exists

None of the four failed loudly. Each reported success over a **narrower question than the one
it claimed to answer**:

| defect | the narrower question it actually answered |
|---|---|
| `check_routing.SOURCE_ARTIFACT` named five sources; the table declared seven | "is this one of the five sources I know about?" |
| `check_routing.artifacts_of` enumerated the same vocabulary again, in the same file | "does the product declare one of seven hardcoded keys?" |
| `apply_provenance` reimplemented `METHOD_WORDS` more narrowly | "is this document name one of three forbidden phrases?" |
| `check_payload` and `apply_provenance` each validated a date by shape | "does this string look like a date?" |

Three were found by review rather than by any gate, and the fourth was found only because the
third was. The pattern is not carelessness about a particular constant — it is that a fix gets
applied to the instance in front of the author and the sibling is never searched for.

**The rule this settles on: a vocabulary with a declarative owner is derived from it, never
copied.** Where a literal genuinely differs from its source, the difference is written down
and tested, so it stays a decision instead of becoming drift.

## Inventory

```yaml
- construct: vocabulary — the three scored axes
  canonical_owner: docs/schemas/score.schema.json (via build/vocabulary.axes)
  duplicates:
    - build/check_freshness.py
    - build/check_refetch.py
    - build/check_verification.py
    - build/freshness_payload.py
    - build/serialize_rubric.py
    - build/sweep_status.py
    - build/check_payload.py
    - build/validate.py          # inline, in the schema gate itself
    - build/repair_placeholder_shows.py  # inline
    - build/render.py            # inline
  risk: >-
    A fourth axis narrows ten denominators at once, and a walk that quietly skips an axis
    passes green. None had drifted — no axis has ever been added — so this is the one entry
    fixed before it failed rather than after.

    render.py was briefly EXEMPTED here because it was the only build module invoked as a
    script, so it could not import from the package. That exemption was unsound: a fourth
    axis would have left the rendered methodology silently omitting its sources while every
    other test passed, which is the very defect this entry is about. The invocation moved to
    `-m` instead — two workflows and three docs — and the exemption is gone.
  disposition: fixed
  regression_test: test_no_module_holds_a_private_copy_of_the_axes

- construct: vocabulary — product artifact kinds
  canonical_owner: sources/signal_routing.yaml `artifact_key` (via build/vocabulary.artifact_kinds)
  duplicates:
    - build/propose_artifacts.py  # VERIFIABLE_KINDS, already missing arxiv
  risk: >-
    Already divergent. The same construct as the two check_routing defects, in a third module.

    The first fix derived it FROM the routing table, which was wrong in the other direction:
    a newly declared `artifact_key` would have become an accepted `--kind` with no URL
    pattern, no live check and no renderer behind it. Routed and proposable are different
    questions, and the two sets being equal today is what made the coincidence look like a
    definition. Support is now defined by the three handlers a kind needs, and asserted to be
    an intentional subset of routed kinds with `arxiv` the named gap.
  disposition: fixed
  regression_test: test_proposer_support_is_defined_by_handlers_not_by_routing

- construct: vocabulary — capability `relation`
  canonical_owner: docs/schemas/score.schema.json
  duplicates:
    - build/check_capability.py   # DELTA
  risk: >-
    DELTA maps each relation to an integer offset, which the schema cannot express, so the
    dict stays. What it must not do is disagree about which relations EXIST: a relation in the
    schema but missing from DELTA is accepted by validate and raises in the gate.
  disposition: intentionally_distinct
  regression_test: test_capability_relation_deltas_match_the_schema_enum

- construct: vocabulary — the method words a provenance line may not name
  canonical_owner: build/prose_provenance.py METHOD_WORDS
  duplicates:
    - build/apply_provenance.py   # fixed in #283
  risk: >-
    The sibling was narrower and let `substitute sources` through as a document name — the
    exact phrase behind four hardware records that a rewording pass nearly promoted into
    canonical form.
  disposition: fixed
  regression_test: test_the_method_vocabulary_has_exactly_one_definition

- construct: date validation
  canonical_owner: datetime.date.fromisoformat
  duplicates:
    - build/check_payload.py      # fixed
    - build/apply_provenance.py   # fixed in #283
  risk: >-
    A `\d{4}-\d{2}-\d{2}` regex accepts 2026-99-99 and 2026-02-30 in a check whose stated job
    on that field is validating a date. The same defect appeared in two modules three days
    apart, the second written after the first was fixed.
  disposition: fixed
  regression_test: >-
    test_check_payload_rejects_impossible_dates and
    test_apply_provenance_rejects_impossible_dates — behavioral, calling the validator rather
    than grepping for `fromisoformat`. The check now requires BOTH the hyphenated shape and a
    successful parse: shape alone accepted 2026-99-99, and parse alone accepts the compact
    `20260815` from Python 3.11, which would put a second date spelling into a corpus whose
    schema declares `format: date`.

- construct: the verification-clause boundary
  canonical_owner: build/prose_provenance.py BOUND — and only as a PROPOSAL
  duplicates:
    - build/apply_provenance.py   # CLAUSE, removed
  risk: >-
    The sibling copy re-matched the clause at write time, so every boundary bug became a
    silent corruption of prose rather than a visible wrong string. `[^.;]*` stopped inside
    `huggingface.co`; adding a whitespace test then split `the U.S. AI Safety Institute
    report` into two grammatical-looking halves, which is worse, because nothing looks wrong.

    Deduplicating it would have missed the point. A heuristic good enough to PROPOSE a clause
    for review is not good enough to rewrite prose unsupervised, so the applier now holds no
    pattern at all: the boundary is confirmed once by a reviewer in the packet and substituted
    literally. `BOUND` stays a heuristic and is labelled as one.
  disposition: fixed
  regression_test: >-
    test_the_applier_holds_no_clause_pattern — AST, asserting the module neither imports nor
    references `re`. A text search would have matched the docstring quoting the very fragments
    it no longer uses, and would then have been weakened until it matched nothing.

- construct: many-valued fact flattened to one value
  canonical_owner: n/a
  duplicates:
    - build/apply_provenance.py   # score_sources
  risk: >-
    A URL is routinely cited on more than one axis with different `accessed` dates. `url ->
    accessed` kept whichever instance came last in axis order, so the check answered "was the
    LAST instance accessed on the claimed date?" while reporting an answer to "was one". Found
    by the first real manifest: it refused two correct packets, and in the other direction
    would have vouched for a URL whose date-aligned instance was not the one under review.
  disposition: fixed
  regression_test: test_a_url_cited_on_two_axes_is_checked_against_every_date_it_carries

- construct: a composition nothing exercises
  canonical_owner: n/a
  duplicates:
    - build/apply_provenance.py   # apply_one
  risk: >-
    `check` and `rewrite` were each tested alone and thoroughly. `apply_one`, which joins
    them, referenced an undefined `CANONICAL` — so every real application would have raised
    `NameError` after passing every check it was subjected to. The same shape as the rest of
    this table, one level up: the parts were verified, the composition was not.
  disposition: fixed
  regression_test: test_an_unresolved_packet_of_any_state_applies — end to end, on a synthetic corpus

- construct: openness class → bucket map
  canonical_owner: docs/openness-class-map.json
  duplicates:
    - build/serialize.py          # _GAP_OPEN / _GAP_OPENISH
    - build/render.py             # _OPEN
  risk: >-
    A divergence would make the gap stage disagree with the published bucket, silently.
  disposition: intentionally_distinct
  regression_test: >-
    tests/test_openness_buckets.py already asserts all three copies agree. That is the same
    protection this sweep adds elsewhere, arrived at first; moving the constants would churn a
    working invariant for symmetry.

- construct: adoption instrument subset
  canonical_owner: none — not a copy
  duplicates:
    - build/check_adoption.py     # _DOWNLOAD_INSTRUMENTS
  risk: none
  disposition: intentionally_distinct
  regression_test: >-
    Not a mirror of the signal_type enum. It names the subset measured on a download scale,
    and the module states why `unknown` is excluded. A narrower vocabulary with a written
    reason is a decision, not a duplicate.

- construct: status/exit derived from fewer conditions than the printed report
  canonical_owner: n/a
  duplicates:
    - build/check_instrument.py   # fixed in #276
  risk: >-
    `--strict` printed an unattributed-figure violation, followed it with `[OK]`, and exited
    0. Every other checker was read: `check_verification` iterates all gates so its exit
    covers everything it prints, and `check_rubric`'s non-gating lines are marked `~` with a
    written reason. No further instances.
  disposition: fixed
  regression_test: test_strict_exits_nonzero_on_an_unattributed_figure

- construct: malformed or unknown input becoming a pass
  canonical_owner: n/a
  duplicates: []
  risk: >-
    Swept and clean. The three `except` paths in build/ each record the failure — `False`, an
    `unreachable` list, or an error — rather than falling through to success.
  disposition: intentionally_distinct
  regression_test: none needed
```

## What was deliberately not done

No new abstraction for the sake of deduplication. `build/vocabulary.py` holds two functions,
both deriving from a file that already owns the fact. Constants that are genuinely local, or
that already have a working gate, were left where they are — noted above with the reason, so
the next sweep does not rediscover them as findings.
