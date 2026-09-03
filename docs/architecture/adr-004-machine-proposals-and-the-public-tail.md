# ADR-004: Machines propose, humans accept; the tail is public as an observed product

**Status:** Accepted 2026-09-03.
**Supersedes:** two rulings in the 2026-07-30 autopilot design: "no bot opens PRs" and
"tail products are excluded from the public visualization".

## Context

The map is moving from a hand-maintained collection of scored YAML files to an editorially
governed publication layer over a continuously observed product universe. The scarce
resource is editorial review time, fixed at a weekly budget. Two earlier rulings made that
budget unreachable: if every commit needs a human dispatch, the dispatch is most of the
budget; and if the observed tier is hidden, the map cannot show coverage at all.

## Decision

1. **Automation may open pull requests. Only a human merges.** A bot PR carries a
   machine-generated review sheet (`build/check_corpus_diff.py`) and exactly one label:
   `tail-batch`, `freshness`, `promotion`, or `re-band`. Head promotions, taxonomy changes,
   rubric changes, and category publication still originate from an explicit human
   dispatch. A stage or gap-set change requires the `stage-move` label, applied by a human.
2. **Tail products are public, as observed products.** They render with what was observed
   (detected license, download band, sources) and the statement that the product has not
   been assessed. They never carry axis scores or an overall score, and they do not
   participate in stage or gap conclusions. Head products are verified assessments.
3. **Corpus-wide generated fixtures are regenerated only after canonical state changes on
   `main`, and never appear in proposal PRs.** `tests/goldens/corpus.json` joins
   `build/notebook_data.json` under `regenerate.yml` and `generated-files-guard`.
4. **No tail field depends on an LLM judgment.** An agent may orchestrate serialization and
   PR creation without being epistemically involved in the result.

## Consequences

Two independent product PRs merge back to back with no fixture repair. The intentional
change gate moves from digest pins to the per-PR semantic diff. Review effort is spent on
the sheet and on confirmation tasks, not on re-pinning. The front end must implement the
observed-product presentation before any tail row is published; until then tail rows stay
out of the payload.

## Unchanged

One product, one category. Head products fade but are never demoted. Low-confidence
identity goes to a human. The resolution ledger never shrinks. Taxonomy cannot outrun the
rubrics. Every merge is human.
