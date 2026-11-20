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
4. `mem0`: capability read from Mem0 Platform while openness reads the open library.
5. MIRIX: excluded because its README leads with a personal-assistant app; its self-hosted memory
   backend could argue for inclusion.
6. Redis Agent Memory, the closed successor to the deprecated Redis Agent Memory Server, was not
   added.
7. `memobase` is quiet (last commit 2026-01-11, its hosted cloud unreachable) but not archived.
