# Sibling invariants

The rule is in `AGENTS.md` ("One fact, one owner"). This file is what it leaves behind: the
register of constructs in `build/` that state the same fact in more than one place **and are
meant to**, each with the reason and the test that holds it.

It is a decision register, not an incident log. The four defects that produced the rule in
August 2026 are fixed and each has a named regression test; git carries the narrative. What a
future sweep needs is the other half — which duplicates are deliberate — because without it
the same three constants get rediscovered as findings every time somebody greps for them.

## Owned, and derived rather than copied

| construct | owner | derived via | test |
|---|---|---|---|
| the three scored axes | `docs/schemas/score.schema.json` | `build/vocabulary.axes` | `test_no_module_holds_a_private_copy_of_the_axes` |
| product artifact kinds | `sources/signal_routing.yaml` `artifact_key` | `build/vocabulary.artifact_kinds` | `test_proposer_support_is_defined_by_handlers_not_by_routing` |
| method words a provenance line may not name | `build/product_prose.py` `METHOD_WORDS` | imported | `test_the_method_vocabulary_has_exactly_one_definition` |
| date handling | `build/vocabulary.py` — `is_iso_date`, `parse_date` | imported | `test_date_validation_rejects_impossible_dates`, `test_date_handling_has_exactly_one_owner` |
| which products are publicly visible | `build/validate.published_products` | imported by `serialize` | `test_preliminary_products_reach_no_public_index`, `test_long_tail_scored_counts_published_categories_only` |

Several of these carry a decision worth keeping in view.

**`render.py` is not exempt from the axes rule**, though it was briefly, on the grounds that it
was the only build module invoked as a script and so could not import from the package. That
exemption was unsound — a fourth axis would have left the rendered methodology silently
omitting its sources while every other test passed — and the invocation moved to `-m` instead.

**Proposable is not the same set as routed.** The first fix derived `propose_artifacts`'
supported kinds *from* the routing table, which fails in the other direction: a newly declared
`artifact_key` would become an accepted `--kind` with no URL pattern, no live check and no
renderer behind it. Support is defined by the three handlers a kind needs, and asserted to be
an intentional subset with `arxiv` the named gap.

**Visibility is one fact, and it was three copies before anyone looked.** A category's lifecycle
status decides whether its products appear in the map, and the payload emits five indexes that each
have to honour it: the categories themselves, `n_total`, the organization rosters, the alias
redirects, and the long-tail sample. When preliminary status was introduced, three of the five did
and two did not, so marking a category preliminary hid its products from `/map` while leaving them
listed under `/map/org/<slug>` and shipping organizations that existed on the map nowhere else. The
long-tail count had the same shape one level up, comparing a snapshot against every product file
while the payload showed only the published ones - and it passed silently, because a count that is
too high looks like a count.

The rule that follows generalizes past this axis: **when a filter has to be applied in more than one
place, it is not a filter, it is a set.** Compute it once, name it, and derive every consumer from
it. Anything the payload grows next derives from `published_products` or it leaks.

**There are two date helpers, and the split is deliberate.** `is_iso_date` GATES a field's
spelling and requires both the hyphenated shape and a successful parse: shape alone accepts
`2026-99-99`, and parse alone accepts Python 3.11's compact `20260815`, which would put a
second date spelling into a corpus whose schema declares `format: date`. `parse_date` is the
permissive one, and exists to COMPARE — refusing to compare a date because it was spelled
unusually would fail a freshness check for a formatting reason.

Five modules held four definitions between them before 2026-08-16. The two `parse_date` copies
differed in one line — one accepted a `date` object and the other did not — and PyYAML returns
an object for an unquoted date and a string from a payload, so the same freshness question was
answered differently depending on which side of the pipeline the value came from.

Its regression test matches on what a function RETURNS, not on its name. A name test let
`validate_sources` through as a false positive because it parses a date inline, and the fix
for that must never be to name the exception: a test that passes by listing whatever it
happens to find has stopped being a test.

## Deliberately distinct — do not "fix" these

| construct | where | why it stays |
|---|---|---|
| capability `relation` → integer offset | `check_capability.DELTA` | the schema cannot express the offset. What DELTA may not do is disagree about which relations *exist*, and `test_capability_relation_deltas_match_the_schema_enum` holds that. |
| openness class → bucket | `serialize._GAP_OPEN` / `_GAP_OPENISH`, `render._OPEN` | `tests/test_openness_buckets.py` already asserts all three agree with `docs/openness-class-map.json`. Same protection, arrived at first; moving the constants would churn a working invariant for symmetry. |
| adoption instrument subset | `check_adoption._DOWNLOAD_INSTRUMENTS` | not a mirror of the `signal_type` enum. It names the subset measured on a download scale, and the module states why `unknown` is excluded. A narrower vocabulary with a written reason is a decision. |

## Three related shapes, all swept clean

**A status or exit derived from fewer conditions than the printed report.** `check_instrument
--strict` once printed a violation, followed it with `[OK]`, and exited 0. Every checker was
read after that: `check_verification` iterates all its sub-gates so its exit covers everything
it prints, and a line that is deliberately non-gating is marked `~` with a written reason
(`check_rubric`'s no-tier lines). Held by
`test_strict_exits_nonzero_on_an_unattributed_figure`.

**Malformed or unknown input becoming a pass.** The `except` paths in `build/` each record the
failure — `False`, an `unreachable` list, or an error — rather than falling through to success.

**A normalizer for two syntaxes must not become an exemption for one of them.** `taxonomy.yaml`
accepts a category as a bare slug or as a mapping with a lifecycle status, and `build/taxonomy.py`
normalizes both - a scalar entry means published. The category contract in `validate` then keyed off
which SPELLING had been used rather than off the normalized status, on the reasonable-sounding
ground that scalar entries predate the feature and should not be disturbed. What that bought was a
published category owing nothing: a scalar entry pointing at a file with only `name`,
`display_name` and an empty roster produced zero errors and would have shipped visibly empty. The
checks now run on the normalized value, and every one of the sixteen scalar entries already
satisfied them, which is the measurement that should have preceded the exemption.


## What was deliberately not done

No new abstraction for the sake of deduplication. `build/vocabulary.py` holds two functions,
both deriving from a file that already owns the fact.
