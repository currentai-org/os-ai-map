# agent_memory promotion, 2026-11-20

The promotion of `agent_memory` from preliminary to published, following
`docs/workflows/promote-category.md`. The category record (`sources/categories/agent_memory.yaml`)
carries the outcome: the roster, the capability rungs and their width review in
`scoring_recipe.note`, the one deferral, and every rejection with its reason in `comments`. This
file records how the pass was run and what it leaves open.

## Method

- Every candidate repository was read through the GitHub search API (canonical name, archived,
  fork, last push, license id) before any record was written, then researched against its LICENSE
  body, README, package metadata and the vendor's pricing or self-hosting pages. Every cited source
  was fetched on 2026-11-20 through `build.fetch_source` and carries `http_status` and
  `content_sha256`.
- Openness and capability are dated 2026-11-20. Adoption is not dated: each non-null level was
  set from a hand-read count of the declared packages (or GitHub stars where no package is the
  product) and is held in `sources/verification_queue.yaml` with
  `settled_by: scheduled_reconciliation`. The two hyperscaler services abstain on adoption and
  that abstention is dated.
- Capability uses the five-part ladder in `scoring_recipe.note`, anchored on `graphiti`.

## Ledger re-rulings

The #413 sweep had parked the agent-memory cluster under the resolution-ledger boundary
`agent-memory-and-context-stores` until a category existed. This promotion re-ruled the entries
for the repositories it promotes (`getzep/graphiti`, `getzep/zep`, `supermemoryai/supermemory`,
`plastic-labs/honcho`, `nevamind-ai/memu`, `vectorize-io/hindsight`, `evermind-ai/everos`,
`memvid/memvid`, `mempalace/mempalace`, `rohitg00/agentmemory`, `gentleman-programming/engram`) and
`memtensor/memos`, which #413 had filed as authored agent content. The other entries under the
boundary keep their #413 verdicts; the category comments say why for each.

## Seed rows changed

- `a-mem`: the seed declared `WujiangXu/A-mem-sys`, the first author's copy. Its README points to
  `agiresearch/A-mem`, which ships the same installable package and is now the declared repository.
- `memobase`: `npm @memobase/memobase` added; its repository field points to `memodb-io/memobase`.
- `longmemory`: confirmed as the project formerly called OpenMemory (the two READMEs have the same
  digest). The `longmemory` package on npm still ships the earlier OpenMemory code, which the
  product's `comments` says.
- `cognee`'s org `topoteretes` is now a company seated in Germany (NOTICE.md gives a Berlin address).

## Open questions for a maintainer

1. `memu`'s modified Apache text: `osi` or `permissive_non_osi` (deferred in the recipe).
2. `agentmemory`: the bundled-part rule applied to its auto-downloaded iii engine under the Elastic
   License 2.0 gives 2/source_available. The alternative reading, as with `langgraph`, is
   open-core gating (4).
3. `memori`: read as `source: partial` because its extraction engine runs only as Memori's hosted
   service, even in bring-your-own-database mode; `public` plus `gated` (4) is the alternative.
4. Settled in review of #1109: `mem0`'s capability now reads the open library, as its openness does
   (band 2; the Platform's consolidation, decay and graph are named, not counted), and MIRIX is in,
   judged on its documented function rather than its README heading.
5. MIRIX's CLA.md names a project owner and says signing contributors get no right to commercially
   use the project except as permitted in writing; it cannot narrow the Apache-2.0 grant in LICENSE,
   on which the record is scored.
6. Redis Agent Memory, the closed successor to the deprecated Redis Agent Memory Server, was not
   added.
7. `memobase` is quiet (last commit 2026-01-11, its hosted cloud unreachable) but not archived.

## The identity pass fixture

The twelve ledger re-rulings lifted `equivalence` truth from 16 to 27 rulings on declared
candidates, past `MIN_TRUTH` (20), so `identity_eval --floors` graded the relation for the first
time and failed recall at 0.259. The fixture's equivalence block had stayed at the 16 edges it was
written with while the ledger grew: nine rulings already on main (instructor, outlines, paddleocr,
bindu, deepseek-ocr, nemotron-asr, glm, glm-ocr and mem0) had no edge, and main's recall of 0.438
went unreported only because it sat under the minimum. `warehouse/models/identity/equivalence_edges.sql`
emits a `resolution_ledger` edge at confidence 1.0 for every `existing_product` ruling, so the
fixture now carries that edge for each ruling on a declared candidate (20 added), with the
declaring tier as `candidate_tier`. No floor or minimum changed.

For declared candidates, the relation's recall is therefore measured on edges the graph emits
because a person ruled, which the module docstring names as a one-sided guard for pool truth. It
was already so for the seven edges the fixture carried before; it is a question about the
relation's design for a maintainer, not something this promotion settles.
