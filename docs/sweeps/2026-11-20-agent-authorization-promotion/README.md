# agent_authorization promotion, 2026-11-20

The promotion of `agent_authorization` from preliminary to published, following
`docs/workflows/promote-category.md`, on the seed roster of the 2026-10-09 sweep
(`docs/sweeps/2026-10-09-agent-authorization/`). The category record carries the outcome: the
roster, the capability rungs and their distribution in `scoring_recipe.note`, four license
deferrals, and the closed-product pass, the one rejection and the Policy and Tenancy boundary in
`comments`.

## Method

- Each seed row's repository was re-read through the GitHub search API, then researched against
  its LICENSE body, README, package metadata and the vendor's pricing or self-hosting pages. Every
  cited source was fetched on 2026-11-20 through `build.fetch_source` and carries `http_status` and
  `content_sha256`.
- Openness and capability are dated 2026-11-20. Each non-null adoption level is a hand-read count
  held in `sources/verification_queue.yaml` with `settled_by: scheduled_reconciliation`; the three
  closed services with no product-specific download channel abstain, and that abstention is dated.
- Capability uses the five-part ladder in `scoring_recipe.note`, anchored on
  `agent-governance-toolkit`.

## Seed rows changed

- `grantex`: relicensed after the sweep. The sweep read Apache-2.0 on 2026-10-09; since 2026-10-21
  the server, portal and specification text are under the Orchestrum Personal Use License 1.0.
  Added `npm @grantex/sdk` and `pypi grantex`, both pointing to the repository.
- `caracal`: added `pypi caracalai-sdk` and `npm @caracalai/sdk` (PyPI `caracal` is an unrelated
  radio-astronomy package).
- `oxdeai`: added `npm @oxdeai/guard`. `emilia-protocol`: added `@emilia-protocol/gate` and
  `@emilia-protocol/verify`. `bolyra`: added `@bolyra/sdk` and `@bolyra/gateway`.
  `agntcy-identity`: added `pypi agntcy-identity-sdk`. `agent-governance-toolkit`: added its PyPI,
  npm and crates packages and `steward: linux-foundation` (its CHARTER makes it a Series of LF
  Projects, LLC).
- `kontext`: added its Homebrew formula, the first `homebrew` artifact on the map.
- `mcp-auth`: declares both `mcp-auth/js` and `mcp-auth/python`, as the sweep read them.
- The two IETF drafts declare their working-group editing repositories.
- Org records filled in from primary pages (type, homepage, country where a page states it).

## Open questions for a maintainer

1. Four licenses no tier names (deferred in the recipe): the Orchestrum Personal Use License
   (`grantex`), the OpenID Foundation copyright license (`authzen-authorization-api`) and the IETF
   Trust Legal Provisions (`identity-assertion-authz-grant`, `wimse-ai-identity-management`).
2. Gating calls: `permit0` is read gated on a planned private enterprise fork that is not yet on
   sale; `aegis-agentguard`'s gates can be switched on by an unvalidated environment variable;
   `kontext` is read public and gated because enforcement needs a hosted workspace's policy (the
   alternative is source partial); `halofy`'s managed-only subsystems are read as a separate service.
3. `wimse-ai-identity-management` bands 5 at low confidence: the draft composes existing standards,
   and a strict reading of "defines" would cap it at 2.
4. `agntcy-identity`: the PyPI authors are at Cisco; owner `linux-foundation` was kept from the seed.
5. Keycard (agent authorization, not yet generally available) and Amazon Bedrock AgentCore Policy
   are the natural next closed entries.
6. Several closed-product sources are dynamic pages (learn.microsoft.com, aws.amazon.com, an Okta
   newsroom post) whose digests changed between two reads on the same day; `check_refetch` will
   report them as drift.
