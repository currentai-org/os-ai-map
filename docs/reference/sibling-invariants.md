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
    - build/render.py            # inline
    - build/repair_placeholder_shows.py  # inline
  risk: >-
    A fourth axis narrows ten denominators at once, and a walk that quietly skips an axis
    passes green. None had drifted — no axis has ever been added — so this is the one entry
    fixed before it failed rather than after.
  disposition: fixed
  regression_test: test_no_module_holds_a_private_copy_of_the_axes

- construct: vocabulary — product artifact kinds
  canonical_owner: sources/signal_routing.yaml `artifact_key` (via build/vocabulary.artifact_kinds)
  duplicates:
    - build/propose_artifacts.py  # VERIFIABLE_KINDS, already missing arxiv
  risk: >-
    Already divergent. The same construct as the two check_routing defects, in a third module.
    Deriving it changes no behavior: `arxiv` is excluded explicitly, because this constant
    asks "does the product carry an artifact a proposal would target" and a paper id is not a
    distribution artifact. Whether it should count is a curation question, raised separately.
  disposition: fixed
  regression_test: test_verifiable_kinds_are_derived_with_an_explicit_exclusion

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
  regression_test: test_dates_are_parsed_not_shape_matched

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
