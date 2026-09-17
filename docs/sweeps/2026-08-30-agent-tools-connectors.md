# Agent tools & connectors sweep — 2026-08-30

## Scope and boundary

Swept from the warehouse discovery pool, `currentai.scores.repos_summary` (frozen since, under ADR-003),
at its 2026-08-24 snapshot, over the six subcategories that carry agent-facing tooling: AI Engineering / Give
agent tools, Give agent knowledge and Protocols, and Infrastructure / Protocols, Make world
agent-ready and Index & Search. Predeclared retrieval cutoff: the top 300 repositories by
all-time stars across those six, which bottoms out at 4,621 stars. Every row was verified
against the GitHub API on 2026-08-30, and every declared package against its registry API on
the same date.

**Counts not preserved.** The reconciled counts (`raw_signals`, `duplicate_signals`,
`unique_candidates`, `accepted`, `parked`) and the individual parked candidates with their
reasons were recorded only in the sweep summary on the original PR, which this header did not
restate and which was not available to reconstruct this document. What survives is the
retrieval cutoff and the verification method above, plus the identity notes below.

## Second addition — 2026-09-16

A second pass added the commercial connector layer. The roster before this addition was almost
entirely reference servers and SDKs, which made the category look like an open-source-only
space. That was a coverage gap in this map rather than a fact about the market: the
specifications and SDKs are open, but the products sold around them (hosted catalogues, managed
OAuth, SLAs) are mostly closed or open-core, and this pass's rows close that gap. No separate
counts were recorded for this addition either.

## Identity notes

- `smithery` and `arcade` share an org (`arcade`) deliberately: Smithery is now part of Arcade,
  and the Smithery CLI repository (`arcadeai-labs/smithery-cli`) redirects there. Whether they
  are one product or two is a promotion-time identity question, flagged rather than resolved by
  this sweep.

## Parked candidates

Not itemized here — see "Counts not preserved" above.
