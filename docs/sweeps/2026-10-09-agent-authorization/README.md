# Agent authorization sweep: 2026-10-09

## Scope and boundary

This sweep carries out the agent-authorization part of maintainer ruling R-2026-10-08-n
(`docs/rulings/log.yaml`; refs #723, OSO-6218): "Run discover-candidates for agent authorization
before proposing a category." It follows #723 point 5, which asked for candidates first and a
boundary check against `safeguards` and #93 (now `assurance_evidence`), and the Mozilla comparison
record of 2026-10-07, which found the report names only OPA, Omnigent, meta-harness tooling and
"agent governance toolkits" for this layer.

**In scope:** open-source and open-standard software for authorizing AI agents. That covers delegated
authorization and OAuth extensions for agents, agent identity and credentials, permission and policy
engines used to decide agent tool access, MCP authorization, consent and approval flows, and
agent-to-agent authorization. **Not swept:** closed products. A category would need its ADR-005
comparators from a separate pass (see Limits).

**No category was created, and no row was written to `sources/registry/`.** No category in the
taxonomy holds these candidates (see "Why the rows are held here"), so the accepted candidates are
recorded in this directory, in registry form, for the maintainer to rule on.

No candidate was scored.

## Window

A single snapshot: every source was read on 2026-10-09, with no creation-date floor on repositories
or packages. The IETF census counts individual Internet-Drafts updated on or after 2025-01-01. The
next sweep of this area can start from 2026-10-09.

## Files in this directory

| File | What it holds |
|---|---|
| `README.md` | This record |
| `fetch-log.tsv` | Every fetch: id (`F0001`…), date, HTTP status, bytes, sha256 of the body, URL. The `F` ids below point here |
| `candidates.tsv` | All 147 raw signals, with the proposed slug, identifiers, proposed org, source and disposition |
| `rows.yaml` | The 35 accepted candidates as registry rows (no `category` key), schema-valid against `docs/schemas/registry.schema.json` |
| `ietf-individual-drafts.txt` | The census of 110 individual Internet-Drafts, not triaged as candidates |

## Sources and retrieval cutoffs

The GitHub queries ran through the session's GitHub search connector. Direct calls to
`api.github.com` and `github.com` returned 403 (F0006, F0007), so repository metadata comes from
ecosyste.ms, and READMEs and LICENSE files from `raw.githubusercontent.com`. Star counts are
ecosyste.ms's and may trail the search connector's by a few.

**What counts as a raw signal.** A raw signal is one distinct product name that a source surfaced and
whose own description names authorization, identity, credentials, permission, policy or approval as
the product's function. Three kinds of search result are not signals. A **repeat** is a name already
counted from an earlier source. A **package-level hit** is another package of a product already
listed. A **screened** result is one whose description names none of those functions, or names one
only in a list of features of something else, such as a framework with human-in-the-loop among ten
features. Awesome-lists are sources, not candidates. The screened names are listed after the table.

**Retrieval cutoff, declared:** 100 stars for GitHub search. It was set after GH-4 was read
(that query had no star floor) and is stated per query in the table. GH-5 used 50 and GH-10 used 150,
and GH-6 and GH-11 used higher floors to bound general-purpose results. Candidates already surfaced
below 100 stars were parked with that reason, not dropped. npm searches were read to their first 20
results.

| Id | Source | Query or page | Cutoff | Read | Signals | Repeats | Screened |
|---|---|---|---|---|---|---|---|
| GH-1 | GitHub search | `agent authorization in:name,description,topics stars:>100`, by stars | ≥100 stars | 24 of 24 | 21 | 0 | 3 |
| GH-2 | GitHub search | `mcp oauth authorization in:name,description,topics stars:>=100` | ≥100 | 2 of 2 | 0 | 1 | 1 |
| GH-3 | GitHub search | `agent identity in:name,description,topics stars:>=100` | ≥100, first 30 | 30 of 44 | 10 | 2 | 18 |
| GH-4 | GitHub search | `topic:agent-authorization`, by stars | none, first 25 | 25 of 52 | 24 | 1 | 0 |
| GH-5 | GitHub search | `mcp authorization in:name,description stars:>=50` | ≥50 | 6 of 6 | 4 | 1 | 1 |
| GH-6 | GitHub search | `topic:fine-grained-authorization stars:>=200` | ≥200 | 5 of 5 | 3 | 1 | 1 |
| GH-7 | GitHub search | `mcp gateway auth in:name,description stars:>=100` | ≥100 | 4 of 4 | 1 | 1 | 2 |
| GH-8 | GitHub search | `human approval ai agents in:name,description stars:>=100` | ≥100 | 17 of 17 | 4 | 1 | 12 |
| GH-9 | GitHub search | `policy ai agents tool calls in:description stars:>=100` | ≥100 | 1 of 1 | 0 | 1 | 0 |
| GH-10 | GitHub search | `permissions ai agents in:description stars:>=150` | ≥150 | 12 of 12 | 3 | 1 | 8 |
| GH-11 | GitHub search | `topic:authorization stars:>=2500`, by stars | ≥2,500, first 30 | 30 of 36 | 22 | 5 | 3 |
| GH-12 | GitHub search | `omnigent OR meta-harness OR agentgateway in:name` | name lookup | 10 of 441 | 0 | 3 | n/a |
| NPM-1 | npm registry search (F0388) | `keywords:agent-authorization` | first 20 | 20 of 31 | 11 | 9 package-level | 0 |
| NPM-2 | npm registry search (F0389) | `mcp authorization oauth` | first 20 | 20 of 155,974 | 11 | 4 | 5 |
| MOZ | Mozilla comparison record, `docs/sweeps/2026-10-07-mozilla-state-of-osai-comparison.md` | named leads for this layer | all | 4 names | 2 | 2 | 0 |
| LEAD | The sweeper's lead list, each looked up directly (ecosyste.ms, raw README, standards page) | named projects and SDKs | all | 24 names | 24 | 0 | 0 |
| IETF | IETF datatracker API (F0009–F0012, F0298) | drafts named `agent`, `oauth` (since 2025-06-01), `aauth`, `wimse` | working-group documents only | 4 listings | 5 | 0 | census of 110 |
| OIDF | OpenID Foundation (F0287, F0296) | AuthZEN working group; CIBA | all | 2 pages | 2 | 0 | 0 |
| | | | | **Total** | **147** | | |

GH-12 was used only to resolve the three named leads (Omnigent and meta-harness from MOZ,
agentgateway from LEAD). Its other seven results were not read as signals. PyPI has no search API,
and its search page returned a bot challenge (F0390), so PyPI was used for verification only.
Hugging Face was not swept, because the scope is software and standards.

**The IETF rule.** Only documents a working group has adopted (`draft-ietf-*`) are candidates. An
individual Internet-Draft has no formal standing in the IETF process. The datatracker page for one
says so (F0297), so it is a proposal and not an open standard. The 110 individual drafts on agent
identity, authorization or delegation updated since 2025-01-01 are a census for the mass question,
listed in `ietf-individual-drafts.txt`, and are not triaged. The census uses a keyword filter and is
approximate. It includes the AAuth series (nine drafts, most by Dick Hardt).

**Screened results, by query.** GH-1: NAalytics/Assemblies-of-putative-SARS-CoV2…,
angusdevgo/Seep-Reverse-Lab, sandsmark/polkit-dumb-agent. GH-2: cerberauth/awesome-openid-connect.
GH-3: google-labs-code/design.md, unicity-aos/capsule-identity, osaurus-ai/osaurus,
unicity-sphere/sphere-sdk, mvanhorn/cli-printing-press, letta-ai/letta-code, allenpeng0705/EnvoyMesh,
Dicklesworthstone/mcp_agent_mail, ghostwright/phantom, Scottcjn/Rustchain,
arnabbagxd/Brand-building-skills, open-gitagent/gitagent, Railly/tinte, zszszszsz/.config,
ZSeven-W/dsh-ios, Doble-2/osint-d2, AngusKit/AngusKit, 0xNyk/awesome-agent-cortex. GH-5:
26zl/cybersec-toolkit. GH-6: warrant-dev/awesome-authorization. GH-7: butterbase-ai/butterbase,
smg-project/smg. GH-8: Atmosphere/atmosphere, samugit83/redamon, Deuz-AI/Deuz-SDK,
worldliberty/agentpay-sdk, huisezhiyin/sdd-riper, sagents-ai/sagents, Maneek21/Deft,
Cloudgeni-ai/opengeni, manor-os/manor-ai, spring-ai-community/spring-ai-playground,
x-glacier/kali-pentest, agentailor/fullstack-langgraph-nextjs-agent. GH-10:
ai-boost/awesome-harness-engineering, pipeshub-ai/pipeshub-ai, cosmicstack-labs/mercury-agent,
Ryder-Sun/Meldwork, ZhixiangLuo/10xProductivity, WrongStack/WrongStack, jin-bo/agentao,
FrankHui/paragents. GH-11: zoontek/react-native-permissions, zenstackhq/zenstack, hexclave/hexclave.
NPM-2: @automattic/mcp-wordpress-remote, @palisadeemail/mcp, @theia/ai-mcp, @tacticlaunch/mcp-linear,
@postman/postman-mcp-server.

## Reconciled counts

```text
raw_signals       = 147
duplicate_signals = 18
unique_candidates = 129
accepted          = 35
parked            = 94

147 = 18 + 129
129 = 35 + 94
```

The 18 duplicates: 4 match head products, 1 matches a registry row, 3 match the resolution ledger,
and 10 are self-dedup (another repository, package or draft of a candidate already listed). Every
accepted and parked candidate was checked against current product slugs, retired aliases, every
registry slug and artifact, and the resolution ledger. None collides. The check ran against `main` at
`6058e799`.

## Accepted candidates

These pass the draft membership test at the end of this record. They are held here, not written to
the registry. Open status and license are as read from the `LICENSE` file. Stars, created and last
push are from the ecosyste.ms record. A package is listed only where the registry record names the
repository.

### A. Agent-specific authorization, identity and approval

| Candidate | Proposed slug | Proposed org | Open status | License as read | Stars | Created | Last push | Package | Primary source | Fetched | Evidence ids | Note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Tenuo | `tenuo` | `tenuo` | open | Apache-2.0 | 103 | 2025-12-03 | 2026-10-09 | `pypi:tenuo`, `npm:@tenuo/core`, `crates:tenuo` | https://github.com/tenuo-ai/tenuo | 2026-10-09 | F0015 F0090 F0091 F0262 F0263 F0264 | task-scoped warrants that attenuate at each delegation hop; PyPI, npm and crates.io packages all name the repository |
| Caracal | `caracal` | `garudex-labs` | open | Apache-2.0 | 221 | 2025-06-23 | 2026-10-05 | – | https://github.com/Garudex-Labs/caracal | 2026-10-09 | F0014 F0088 F0089 | gateway-mediated agents hold no upstream credentials; policy-approved, revocable delegation. PyPI `caracal` is an unrelated project (F0276), so no package is declared |
| Permit0 | `permit0` | `permit0` | open | Apache-2.0 | 188 | 2026-04-01 | 2026-06-22 | – | https://github.com/permit0-ai/permit0 | 2026-10-09 | F0013 F0086 F0087 | pre-execution policy engine for agent actions; no PyPI or crates.io package (F0274, F0275) |
| OpenFirma | `openfirma` | `firma-ai` | open | GPL-3.0 | 140 | 2026-03-22 | 2026-09-12 | – | https://github.com/Firma-AI/openfirma | 2026-10-09 | F0016 F0092 F0093 | local sidecar gating every outbound agent call against Cedar policies |
| Clawvisor | `clawvisor` | `clawvisor` | source-available | Elastic License 2.0 | 282 | 2026-03-01 | 2026-10-04 | – | https://github.com/clawvisor/clawvisor | 2026-10-09 | F0017 F0094 F0095 | task-scoped approval and credential injection; agents never hold credentials |
| Kontext | `kontext` | `kontext-security` | open (setup needs a hosted-dashboard install token) | MIT | 222 | 2026-04-05 | 2026-10-05 | – | https://github.com/kontext-security/kontext | 2026-10-09 | F0018 F0096 F0097 | local policy between agents and the tools they call |
| Cordum | `cordum` | `cordum` | source-available | Business Source License 1.1 | 510 | 2026-01-11 | 2026-10-03 | – | https://github.com/cordum-io/cordum | 2026-10-09 | F0021 F0102 F0103 | policy and human approval before risky tool calls |
| Aegis (AgentGuard) | `aegis-agentguard` | `justin0504` | open | MIT | 454 | 2026-03-04 | 2026-09-06 | – | https://github.com/Justin0504/Aegis | 2026-10-09 | F0022 F0104 F0105 | runtime policy enforcement, approvals and kill switch. The PyPI and npm packages it names carry no repository link (F0265, F0266), so none is declared |
| Attestix | `attestix` | `vibetensor` | open | Apache-2.0 | 875 | 2026-02-16 | 2026-10-01 | `pypi:attestix` | https://github.com/VibeTensor/attestix | 2026-10-09 | F0026 F0112 F0113 F0267 | DID-based agent identity, W3C verifiable credentials and delegation chains |
| Halofy | `halofy` | `halofy` | open | AGPL-3.0 | 336 | 2026-08-22 | 2026-09-22 | – | https://github.com/halofyai/halofy | 2026-10-09 | F0027 F0114 F0115 | identity and policy layer between organizational context and agents; also keeps durable context, so it borders `agent_memory` |
| AGNTCY Identity | `agntcy-identity` | `linux-foundation` | open | Apache-2.0 | 103 | 2025-05-27 | 2026-09-29 | – | https://github.com/agntcy/identity | 2026-10-09 | F0070 F0200 F0201 | verifiable agent identities and badges, with MCP and A2A integrations |
| Phantasm | `phantasm` | `edwinkys` | open | GPL-3.0 | 197 | 2024-10-13 | 2024-11-28 | – | https://github.com/edwinkys/phantasm | 2026-10-09 | F0031 F0122 F0123 | human-in-the-loop approval layer for agent actions; dormant, last push 2024-11-28 |
| pi-permission-system | `pi-permission-system` | `masurii` | open | MIT | 157 | 2026-03-02 | 2026-07-03 | `npm:pi-permission-system` | https://github.com/MasuRii/pi-permission-system | 2026-10-09 | F0039 F0138 F0139 F0280 | permission gates for one coding harness (Pi); a plugin rather than a platform |
| OxDeAI | `oxdeai` | `oxdeai` | open | Apache-2.0 | 13 | 2026-02-26 | 2026-10-04 | `npm:@oxdeai/core` | https://github.com/oxdeai/oxdeai | 2026-10-09 | F0306 F0438 F0439 F0440 F0388 | deterministic execution authorization; surfaced twice: below the GitHub cutoff (13 stars) and inside the npm cutoff (752 downloads a month), so it is judged on its merits |
| Grantex | `grantex` | `orchestrum` | open | Apache-2.0 (with an owner copyright header) | 34 | 2026-02-25 | 2026-10-05 | – | https://github.com/mishrasanjeev/grantex | 2026-10-09 | F0391 F0392 F0393 F0388 | delegated access and authorization for agents; surfaced through its x402 package, which is not declared because it is an integration |
| EMILIA Protocol | `emilia-protocol` | `emilia-protocol` | open | Apache-2.0 | 612 | 2026-03-13 | 2026-10-02 | – | https://github.com/emiliaprotocol/emilia-protocol | 2026-10-09 | F0394 F0395 F0396 F0435 | authority check before a protected tool runs, with receipts |
| Besa | `besa` | `dorigjo` | open | MIT | 0 | 2026-06-12 | 2026-10-03 | `npm:@dorigjo/besa` | https://github.com/dorigjo/besa | 2026-10-09 | F0403 F0404 F0405 F0436 | admission decision and signed evidence per consequential action; 0 stars, 574 npm downloads a month |
| Bolyra | `bolyra` | `zkprova` | open | Apache-2.0 | 0 | 2026-04-21 | 2026-09-29 | – | https://github.com/bolyra/bolyra | 2026-10-09 | F0406 F0407 F0408 F0388 | authorization policy, signed receipts and audit for tool calls (ZKProva Inc.) |
| OVID-ME | `ovid-me` | `clawdreyhepburn` | open | Apache-2.0 | 2 | 2026-03-23 | 2026-07-22 | `npm:@clawdreyhepburn/ovid-me` | https://github.com/clawdreyhepburn/ovid-me | 2026-10-09 | F0415 F0416 F0417 F0437 | enforces narrowed mandates when one agent spawns another, using Cedar |

### B. MCP authorization libraries

| Candidate | Proposed slug | Proposed org | Open status | License as read | Stars | Created | Last push | Package | Primary source | Fetched | Evidence ids | Note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MCP Auth | `mcp-auth` | `silverhand` | open | MIT | 50 | 2025-04-19 | 2026-08-31 | `npm:mcp-auth`, `pypi:mcpauth` | https://github.com/mcp-auth/js | 2026-10-09 | F0060 F0061 F0180 F0181 F0182 F0183 F0268 F0269 | authorization library for MCP servers (Node.js and Python, one product); npm 71,080 downloads a month (F0389) |
| Workers OAuth Provider | `workers-oauth-provider` | `cloudflare` | open | MIT | 1,879 | 2025-03-11 | 2026-10-05 | `npm:@cloudflare/workers-oauth-provider` | https://github.com/cloudflare/workers-oauth-provider | 2026-10-09 | F0062 F0184 F0236 F0270 | OAuth 2.1 authorization for remote MCP servers on Workers; npm 3,931,972 downloads a month (F0389) |

### C. General-purpose identity and authorization systems whose own docs ship an agent or MCP function

| Candidate | Proposed slug | Proposed org | Open status | License as read | Stars | Created | Last push | Package | Primary source | Fetched | Evidence ids | Note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ThunderID | `thunderid` | `thunder-id` | open | Apache-2.0 | 587 | 2025-05-01 | 2026-10-08 | – | https://github.com/thunder-id/thunderid | 2026-10-09 | F0034 F0128 F0129 | IAM stack that manages agents as first-class identities with delegated authority |
| Open Policy Agent | `open-policy-agent` | `cncf` | open | Apache-2.0 | 12,307 | 2015-12-28 | 2026-10-03 | – | https://github.com/open-policy-agent/opa | 2026-10-09 | F0041 F0142 F0143 F0244 | general-purpose engine; its homepage example is a policy over which tools an agent may call. Named by Mozilla |
| Cerbos | `cerbos` | `cerbos` | open core (its own description) | Apache-2.0 | 4,607 | 2021-03-21 | 2026-10-02 | – | https://github.com/cerbos/cerbos | 2026-10-09 | F0043 F0146 F0147 F0240 | homepage: "Define AI agent and MCP boundaries before they go live" |
| OpenFGA | `openfga` | `cncf` | open | Apache-2.0 | 5,904 | 2022-06-08 | 2026-10-02 | – | https://github.com/openfga/openfga | 2026-10-09 | F0045 F0150 F0151 F0259 | docs section "Authorization for Agents" (agents as principals, MCP servers, task-based) |
| SpiceDB | `spicedb` | `authzed` | open | Apache-2.0 | 7,116 | 2021-08-16 | 2026-10-02 | – | https://github.com/authzed/spicedb | 2026-10-09 | F0044 F0148 F0149 F0260 | docs page "Secure AI Agents with Fine Grained Authorization" |
| Cedar | `cedar` | `amazon-web-services` | open | Apache-2.0 | 1,774 | 2023-04-25 | 2026-10-08 | `crates:cedar-policy` | https://github.com/cedar-policy/cedar | 2026-10-09 | F0047 F0154 F0155 F0273 F0246 F0247 F0248 F0282 | policy language and engine; the project's `cedar-for-agents` repository generates Cedar schemas from MCP tool descriptions |
| Keycloak | `keycloak` | `cncf` | open | Apache-2.0 | 37,169 | 2013-07-02 | 2026-10-07 | – | https://github.com/keycloak/keycloak | 2026-10-09 | F0056 F0172 F0234 F0243 | guide "Using Keycloak as an authorization server for MCP servers" |
| Pomerium | `pomerium` | `pomerium` | open | Apache-2.0 | 5,026 | 2019-01-01 | 2026-10-03 | – | https://github.com/pomerium/pomerium | 2026-10-09 | F0067 F0194 F0195 F0249 | identity-aware proxy; MCP docs cover protecting servers and limiting tool calls |
| Casdoor | `casdoor` | `casdoor` | open | Apache-2.0 | 14,506 | 2020-10-22 | 2026-10-03 | – | https://github.com/casdoor/casdoor | 2026-10-09 | F0033 F0126 F0127 | describes itself as agent-first IAM and an MCP auth server |
| Logto | `logto` | `silverhand` | open | MPL-2.0 | 14,660 | 2021-06-19 | 2026-10-08 | – | https://github.com/logto-io/logto | 2026-10-09 | F0055 F0170 F0171 | README: built for "SaaS, AI, and agent-based platforms"; the same company publishes MCP Auth. The weakest claim in group C |
| Better Auth | `better-auth` | `better-auth` | open | MIT | 30,215 | 2024-05-19 | 2026-10-08 | `npm:better-auth` | https://github.com/better-auth/better-auth | 2026-10-09 | F0421 F0422 F0433 F0431 F0432 | TypeScript auth framework with a first-party MCP plugin (`@better-auth/mcp`, 1,286,875 npm downloads a month, F0389) |

### D. Open standards with a working-group home

| Candidate | Proposed slug | Proposed org | Status | License as read | Primary source | Fetched | Evidence ids | Note |
|---|---|---|---|---|---|---|---|---|
| AuthZEN Authorization API | `authzen-authorization-api` | `openid-foundation` | open standard | OpenID Foundation Final Specification; no LICENSE file in the repository | https://openid.net/specs/authorization-api-1_0.html | 2026-10-09 | F0085 F0230 F0287 F0288 F0289 | Final since January 2026; the working group's COAZ-MCP binding (draft) maps MCP calls onto it |
| Identity Assertion JWT Authorization Grant | `identity-assertion-authz-grant` | `ietf` | open standard (OAuth WG draft) | IETF Trust (BCP 78/79) | https://datatracker.ietf.org/doc/draft-ietf-oauth-identity-assertion-authz-grant/ | 2026-10-09 | F0010 F0292 | OAuth WG document; appendix A.4 "AI Agent using External Tools" |
| AI Identity Management System (WIMSE) | `wimse-ai-identity-management` | `ietf` | open standard (WIMSE WG draft) | IETF Trust (BCP 78/79) | https://datatracker.ietf.org/doc/draft-ietf-wimse-aims/ | 2026-10-09 | F0290 F0291 F0298 | WG document on authentication and authorization of AI agent interactions; replaces draft-klrc-aiagent-auth |

## Parked candidates

All fetched on 2026-10-09.

| # | Candidate | Source | Reason | Primary source | Fetched | Evidence ids |
|---|---|---|---|---|---|---|
| 1 | decionis/agent-safe-pipeline | GH-1 | open enforcement proxy whose decisions come from the hosted Decionis control plane ("It decides nothing itself"); same reason as auth0-ai | https://github.com/decionis/agent-safe-pipeline | 2026-10-09 | F0019 F0098 F0099 |
| 2 | auth0/auth0-ai-js | LEAD | open client of a closed hosted service (Auth0 Token Vault, async authorization, FGA); out of this sweep's open-source scope, a candidate for the closed-comparator pass | https://github.com/auth0/auth0-ai-js | 2026-10-09 | F0068 F0069 F0196 F0198 F0271 F0272 |
| 3 | MetapriseAI/OrgKernel | GH-3 | implausible signal: 2,695 stars and 249 forks on a 111 KB repository with 0 open issues and no push since 2026-07-06 | https://github.com/MetapriseAI/OrgKernel | 2026-10-09 | F0025 F0110 F0111 |
| 4 | permitio/opal | GH-1 | general-purpose policy administration; the README's "agent" hits are OPA policy agents, not AI agents | https://github.com/permitio/opal | 2026-10-09 | F0042 F0144 F0145 |
| 5 | golf-mcp/golf | GH-1 | boundary → `agent_protocols`: a framework for building MCP servers, auth one feature | https://github.com/golf-mcp/golf | 2026-10-09 | F0036 F0132 |
| 6 | arcjet/arcjet-js | GH-1 | boundary → `safeguards`: prompt-injection detection, PII redaction and bot protection lead; tool-call authorization is one feature | https://github.com/arcjet/arcjet-js | 2026-10-09 | F0023 F0106 F0286 |
| 7 | dengyier/OpenWorkProof | GH-1 | boundary → `assurance_evidence`: verifiable execution evidence and acceptance lead; authorization is one of three | https://github.com/dengyier/OpenWorkProof | 2026-10-09 | F0030 F0120 |
| 8 | chaitin/OctoBus | GH-1 | boundary → `agent_tools_connectors`: a local gateway exposing service packages over gRPC and MCP | https://github.com/chaitin/OctoBus | 2026-10-09 | F0024 F0108 |
| 9 | NapthaAI/http-oauth-mcp-server | GH-1 | identity unclear: a reference server with no release or package, last push 2025-05-07 | https://github.com/NapthaAI/http-oauth-mcp-server | 2026-10-09 | F0037 F0134 |
| 10 | netbirdio/netbird | GH-3 | out of scope: zero-trust network access, not agent authorization | https://github.com/netbirdio/netbird | 2026-10-09 | F0300 |
| 11 | ascending-llc/jarvis-registry | GH-3 | boundary, MCP and agent gateways (see boundary notes): routing and federation are the stated function and authorization is one feature | https://github.com/ascending-llc/jarvis-registry | 2026-10-09 | F0032 F0124 |
| 12 | Authing/Authing | GH-3 | unmaintained: last push 2022-08-21, and the README makes no agent claim | https://github.com/Authing/Authing | 2026-10-09 | F0035 F0130 |
| 13 | BillionsNetwork/verified-agent-identity | GH-3 | identity unclear: an agent skill for one network's DID protocol (Billions/iden3); no LICENSE file found | https://github.com/BillionsNetwork/verified-agent-identity | 2026-10-09 | F0029 F0118 F0119 F0233 |
| 14 | dp-web4/SAGE | GH-4 | below the 100-star GitHub retrieval cutoff (27 stars) | https://github.com/dp-web4/SAGE | 2026-10-09 | F0302 |
| 15 | PlawIO/veto | GH-4 | below the 100-star GitHub retrieval cutoff (14 stars) | https://github.com/PlawIO/veto | 2026-10-09 | F0304 |
| 16 | dp-web4/web4 | GH-4 | below the 100-star GitHub retrieval cutoff (12 stars) | https://github.com/dp-web4/web4 | 2026-10-09 | F0308 |
| 17 | anivar/decern | GH-4 | below the 100-star GitHub retrieval cutoff (12 stars) | https://github.com/anivar/decern | 2026-10-09 | F0310 |
| 18 | hellocosmos/ai-security-gateway | GH-4 | below the 100-star GitHub retrieval cutoff (3 stars) | https://github.com/hellocosmos/ai-security-gateway | 2026-10-09 | F0312 |
| 19 | kinde-starter-kits/jev-agent-authorization | GH-4 | below the 100-star GitHub retrieval cutoff (5 stars) | https://github.com/kinde-starter-kits/jev-agent-authorization | 2026-10-09 | F0314 |
| 20 | Kisyntra/Agent_Sudo | GH-4 | below the 100-star GitHub retrieval cutoff (5 stars) | https://github.com/Kisyntra/Agent_Sudo | 2026-10-09 | F0316 |
| 21 | dp-web4/hestia | GH-4 | below the 100-star GitHub retrieval cutoff (5 stars) | https://github.com/dp-web4/hestia | 2026-10-09 | F0318 |
| 22 | Draco-Tech-ai/draco-toolkit | GH-4 | below the 100-star GitHub retrieval cutoff (3 stars) | https://github.com/Draco-Tech-ai/draco-toolkit | 2026-10-09 | F0321 |
| 23 | KeelStack-me/guard | GH-4 | below the 100-star GitHub retrieval cutoff (3 stars) | https://github.com/KeelStack-me/guard | 2026-10-09 | F0322 |
| 24 | attenu-io/attenu-guard | GH-4 | below the 100-star GitHub retrieval cutoff (2 stars) | https://github.com/attenu-io/attenu-guard | 2026-10-09 | F0324 |
| 25 | Insomniac-VibeLabs/two-key-concept | GH-4 | below the 100-star GitHub retrieval cutoff (1 star) | https://github.com/Insomniac-VibeLabs/two-key-concept | 2026-10-09 | F0326 |
| 26 | attenu-io/attenu-derive | GH-4 | below the 100-star GitHub retrieval cutoff (1 star) | https://github.com/attenu-io/attenu-derive | 2026-10-09 | F0328 |
| 27 | EVVM-org/erc8004-evvm | GH-4 | below the 100-star GitHub retrieval cutoff (0 stars) | https://github.com/EVVM-org/erc8004-evvm | 2026-10-09 | F0330 |
| 28 | identities-ai/ratify-labs | GH-4 | below the 100-star GitHub retrieval cutoff (1 star) | https://github.com/identities-ai/ratify-labs | 2026-10-09 | F0332 |
| 29 | Cubitrek/agent-passport | GH-4 | below the 100-star GitHub retrieval cutoff (1 star) | https://github.com/Cubitrek/agent-passport | 2026-10-09 | F0334 |
| 30 | surroundapps/agent-provenance | GH-4 | below the 100-star GitHub retrieval cutoff (1 star) | https://github.com/surroundapps/agent-provenance | 2026-10-09 | F0337 |
| 31 | zvectorlabs/pgauthz | GH-4 | below the 100-star GitHub retrieval cutoff (1 star) | https://github.com/zvectorlabs/pgauthz | 2026-10-09 | F0338 |
| 32 | DaevMithran/agnap | GH-4 | below the 100-star GitHub retrieval cutoff (1 star) | https://github.com/DaevMithran/agnap | 2026-10-09 | F0341 |
| 33 | Andy11-cpu/agent-authorization-case-study | GH-4 | below the 100-star GitHub retrieval cutoff (0 stars); a research write-up, not software | https://github.com/Andy11-cpu/agent-authorization-case-study | 2026-10-09 | F0343 |
| 34 | Gamino17/AMI | GH-4 | below the 100-star GitHub retrieval cutoff (0 stars) | https://github.com/Gamino17/AMI | 2026-10-09 | F0344 |
| 35 | Aankirz/agentauth | GH-4 | below the 100-star GitHub retrieval cutoff (0 stars) | https://github.com/Aankirz/agentauth | 2026-10-09 | F0346 |
| 36 | AuthPlane/authserver | GH-5 | below the 100-star GitHub retrieval cutoff (79 stars) | https://github.com/AuthPlane/authserver | 2026-10-09 | F0080 F0220 |
| 37 | empires-security/mcp-oauth2-aws-cognito | GH-5 | below the 100-star GitHub retrieval cutoff (60 stars); an example | https://github.com/empires-security/mcp-oauth2-aws-cognito | 2026-10-09 | F0348 |
| 38 | christian-posta/mcp-auth-step-by-step | GH-5 | below the 100-star GitHub retrieval cutoff (55 stars); a tutorial | https://github.com/christian-posta/mcp-auth-step-by-step | 2026-10-09 | F0350 |
| 39 | atrawog/mcp-oauth-gateway | GH-5 | below the 100-star GitHub retrieval cutoff (60 stars) | https://github.com/atrawog/mcp-oauth-gateway | 2026-10-09 | F0081 F0222 |
| 40 | warrant-dev/warrant | GH-6 | general-purpose; the fetched README (and homepage, where one was fetched) presents no agent or MCP use case | https://github.com/warrant-dev/warrant | 2026-10-09 | F0046 F0152 |
| 41 | affaan-m/agentshield | GH-10 | boundary → `safeguards`: a scanner of agent configurations and MCP servers | https://github.com/affaan-m/agentshield | 2026-10-09 | F0040 F0140 |
| 42 | apache/casbin-gateway | GH-10 | boundary, MCP and agent gateways (see boundary notes): routing and federation are the stated function and authorization is one feature | https://github.com/apache/casbin-gateway | 2026-10-09 | F0038 F0136 |
| 43 | WORLD3-ai/world_ai_protocol | GH-10 | below the 100-star GitHub retrieval cutoff (54 stars); on-chain delegation, last push 2025-04-03 | https://github.com/WORLD3-ai/world_ai_protocol | 2026-10-09 | F0352 |
| 44 | goauthentik/authentik | GH-11 | general-purpose; the fetched README (and homepage, where one was fetched) presents no agent or MCP use case | https://github.com/goauthentik/authentik | 2026-10-09 | F0053 F0166 F0253 |
| 45 | apache/casbin | GH-11 | general-purpose; the fetched README (and homepage, where one was fetched) presents no agent or MCP use case | https://github.com/apache/casbin | 2026-10-09 | F0050 F0160 F0256 |
| 46 | dromara/Sa-Token | GH-11 | general-purpose; the fetched README (and homepage, where one was fetched) presents no agent or MCP use case | https://github.com/dromara/Sa-Token | 2026-10-09 | F0354 F0355 |
| 47 | ory/hydra | GH-11 | general-purpose; the agent and MCP claim is on Ory's company page (F0251), not on Hydra's README | https://github.com/ory/hydra | 2026-10-09 | F0052 F0164 F0251 |
| 48 | zitadel/zitadel | GH-11 | general-purpose; the fetched README (and homepage, where one was fetched) presents no agent or MCP use case | https://github.com/zitadel/zitadel | 2026-10-09 | F0054 F0168 F0252 |
| 49 | apereo/cas | GH-11 | general-purpose; the fetched README (and homepage, where one was fetched) presents no agent or MCP use case | https://github.com/apereo/cas | 2026-10-09 | F0356 F0357 |
| 50 | stalniy/casl | GH-11 | general-purpose; the fetched README (and homepage, where one was fetched) presents no agent or MCP use case | https://github.com/stalniy/casl | 2026-10-09 | F0057 F0174 |
| 51 | Permify/permify | GH-11 | general-purpose; the fetched README (and homepage, where one was fetched) presents no agent or MCP use case | https://github.com/Permify/permify | 2026-10-09 | F0049 F0158 F0250 |
| 52 | CanCanCommunity/cancancan | GH-11 | general-purpose; the fetched README (and homepage, where one was fetched) presents no agent or MCP use case | https://github.com/CanCanCommunity/cancancan | 2026-10-09 | F0358 F0359 |
| 53 | doorkeeper-gem/doorkeeper | GH-11 | general-purpose; the fetched README (and homepage, where one was fetched) presents no agent or MCP use case | https://github.com/doorkeeper-gem/doorkeeper | 2026-10-09 | F0360 F0361 |
| 54 | unkeyed/unkey | GH-11 | general-purpose; the fetched README (and homepage, where one was fetched) presents no agent or MCP use case | https://github.com/unkeyed/unkey | 2026-10-09 | F0362 F0363 |
| 55 | ory/keto | GH-11 | general-purpose; the fetched README (and homepage, where one was fetched) presents no agent or MCP use case | https://github.com/ory/keto | 2026-10-09 | F0051 F0162 |
| 56 | build-trust/ockam | GH-11 | general-purpose; the fetched README (and homepage, where one was fetched) presents no agent or MCP use case | https://github.com/build-trust/ockam | 2026-10-09 | F0058 F0176 |
| 57 | google/santa | GH-11 | out of scope: binary authorization on macOS; archived | https://github.com/google/santa | 2026-10-09 | F0364 F0365 |
| 58 | marmotedu/iam | GH-11 | out of scope: a teaching project for a Go course | https://github.com/marmotedu/iam | 2026-10-09 | F0366 F0367 |
| 59 | simov/grant | GH-11 | general-purpose; the fetched README (and homepage, where one was fetched) presents no agent or MCP use case | https://github.com/simov/grant | 2026-10-09 | F0368 F0369 |
| 60 | panva/node-oidc-provider | GH-11 | general-purpose; the fetched README (and homepage, where one was fetched) presents no agent or MCP use case | https://github.com/panva/node-oidc-provider | 2026-10-09 | F0059 F0178 F0235 |
| 61 | thephpleague/oauth2-client | GH-11 | general-purpose; the fetched README (and homepage, where one was fetched) presents no agent or MCP use case | https://github.com/thephpleague/oauth2-client | 2026-10-09 | F0370 F0371 |
| 62 | JosephSilber/bouncer | GH-11 | general-purpose; the fetched README (and homepage, where one was fetched) presents no agent or MCP use case | https://github.com/JosephSilber/bouncer | 2026-10-09 | F0372 |
| 63 | oauthlib/oauthlib | GH-11 | general-purpose; the fetched README (and homepage, where one was fetched) presents no agent or MCP use case | https://github.com/oauthlib/oauthlib | 2026-10-09 | F0374 |
| 64 | stanford-iris-lab/meta-harness | MOZ | out of scope: research code for harness optimization (named by Mozilla) | https://github.com/stanford-iris-lab/meta-harness | 2026-10-09 | F0078 F0216 |
| 65 | aserto-dev/topaz | LEAD | general-purpose; the fetched README (and homepage, where one was fetched) presents no agent or MCP use case | https://github.com/aserto-dev/topaz | 2026-10-09 | F0048 F0156 F0255 |
| 66 | agentgateway/agentgateway | LEAD | boundary, MCP and agent gateways (see boundary notes): routing and federation are the stated function and authorization is one feature (Linux Foundation; 5,224 stars) | https://github.com/agentgateway/agentgateway | 2026-10-09 | F0063 F0186 |
| 67 | IBM/mcp-context-forge | LEAD | boundary, MCP and agent gateways (see boundary notes): routing and federation are the stated function and authorization is one feature (IBM; 4,568 stars) | https://github.com/IBM/mcp-context-forge | 2026-10-09 | F0064 F0188 |
| 68 | docker/mcp-gateway | LEAD | boundary, MCP and agent gateways (see boundary notes): routing and federation are the stated function and authorization is one feature | https://github.com/docker/mcp-gateway | 2026-10-09 | F0065 F0190 |
| 69 | obot-platform/obot | LEAD | boundary, MCP and agent gateways (see boundary notes): routing and federation are the stated function and authorization is one feature | https://github.com/obot-platform/obot | 2026-10-09 | F0066 F0192 |
| 70 | invariantlabs-ai/invariant | LEAD | boundary → `safeguards`: contextual guardrails; last push 2026-01-12 | https://github.com/invariantlabs-ai/invariant | 2026-10-09 | F0071 F0202 |
| 71 | humanlayer/humanlayer | LEAD | unmaintained: the README says the code is deprecated | https://github.com/humanlayer/humanlayer | 2026-10-09 | F0072 F0204 |
| 72 | spiffe/spire | LEAD | general-purpose; the fetched README (and homepage, where one was fetched) presents no agent or MCP use case; the WIMSE drafts build on SPIFFE | https://github.com/spiffe/spire | 2026-10-09 | F0073 F0206 F0254 |
| 73 | eclipse-biscuit/biscuit | LEAD | general-purpose; the fetched README (and homepage, where one was fetched) presents no agent or MCP use case (capability tokens) | https://github.com/eclipse-biscuit/biscuit | 2026-10-09 | F0074 F0208 |
| 74 | ucan-wg/spec | LEAD | general-purpose; the fetched README (and homepage, where one was fetched) presents no agent or MCP use case ("agent" is UCAN's word for a DID principal) | https://github.com/ucan-wg/spec | 2026-10-09 | F0075 F0210 |
| 75 | osohq/oso | LEAD | library last pushed 2025-02-26 with no agent claim; Oso's agent product is a closed service, for the closed-comparator pass | https://github.com/osohq/oso | 2026-10-09 | F0083 F0226 F0257 |
| 76 | permitio/permit-mcp | LEAD | open client of a closed hosted service (Permit.io access requests); 3 stars, last push 2025-05-05 | https://github.com/permitio/permit-mcp | 2026-10-09 | F0084 F0228 F0258 |
| 77 | oauth-transaction-tokens | IETF | general-purpose: the draft's only "agent" is the HTTP User-Agent | https://datatracker.ietf.org/doc/draft-ietf-oauth-transaction-tokens/ | 2026-10-09 | F0293 |
| 78 | oauth-identity-chaining | IETF | general-purpose: no agent text | https://datatracker.ietf.org/doc/draft-ietf-oauth-identity-chaining/ | 2026-10-09 | F0294 |
| 79 | openid-ciba | OIDF | general-purpose (Final, 2021): its "agent" is a call-center agent | https://openid.net/specs/openid-client-initiated-backchannel-authentication-core-1_0.html | 2026-10-09 | F0296 |
| 80 | quirna/quirna-mcp | NPM-1 | open client of a closed hosted service (Quirna approvals) | https://github.com/quirna/quirna-mcp | 2026-10-09 | F0397 F0398 F0399 |
| 81 | ziffer-hq/ziffer-sdk | NPM-1 | open client of a closed hosted service ("ZIFFER is the agent authorization service") | https://github.com/ziffer-hq/ziffer-sdk | 2026-10-09 | F0400 F0401 F0402 |
| 82 | BlockSiFr/ttp-protocol | NPM-1 | boundary: consequence routing and evidence lead, not authorization | https://github.com/BlockSiFr/ttp-protocol | 2026-10-09 | F0412 F0413 F0414 |
| 83 | AgentAuthorityChain/aac | NPM-1 | repository named by the npm package does not resolve, so function and license cannot be read | https://github.com/AgentAuthorityChain/aac | 2026-10-09 | F0409 F0410 F0411 F0441 |
| 84 | openclaw-veto | NPM-1 | identity unclear: no repository link; may be an OpenClaw plugin of PlawIO veto | https://registry.npmjs.org/openclaw-veto | 2026-10-09 | F0430 |
| 85 | aeternm/authoxi | NPM-1 | repository named by the npm package does not resolve | https://github.com/aeternm/authoxi | 2026-10-09 | F0418 F0419 F0420 F0442 |
| 86 | octokit/oauth-authorization-url.js | NPM-2 | general-purpose: one vendor's OAuth URL helper | https://github.com/octokit/oauth-authorization-url.js | 2026-10-09 | F0389 |
| 87 | panva/openid-client | NPM-2 | general-purpose; the npm record names no agent or MCP function (OAuth client) | https://github.com/panva/openid-client | 2026-10-09 | F0389 |
| 88 | panva/oauth4webapi | NPM-2 | general-purpose; the npm record names no agent or MCP function (OAuth client) | https://github.com/panva/oauth4webapi | 2026-10-09 | F0389 |
| 89 | ddo/oauth-1.0a | NPM-2 | general-purpose; the npm record names no agent or MCP function (OAuth 1.0a signing; last release 2019-06-05) | https://github.com/ddo/oauth-1.0a | 2026-10-09 | F0389 |
| 90 | punkpeye/mcp-remote | NPM-2 | boundary → `agent_protocols`: a stdio-to-remote MCP bridge that handles the client side of OAuth (4,843,049 npm downloads a month) | https://github.com/punkpeye/mcp-remote | 2026-10-09 | F0389 F0427 F0428 F0429 |
| 91 | slackapi/node-slack-sdk | NPM-2 | general-purpose: one vendor's OAuth helper | https://github.com/slackapi/node-slack-sdk | 2026-10-09 | F0389 |
| 92 | compwright/axios-oauth-client | NPM-2 | general-purpose; the npm record names no agent or MCP function (OAuth client) | https://github.com/compwright/axios-oauth-client | 2026-10-09 | F0389 |
| 93 | jaredhanson/oauth2orize | NPM-2 | general-purpose; the npm record names no agent or MCP function (OAuth server toolkit; last release 2023-10-13) | https://github.com/jaredhanson/oauth2orize | 2026-10-09 | F0389 |
| 94 | codefox-inc/convex-oauth-provider | NPM-2 | general-purpose; the npm record names no agent or MCP function (OAuth provider for one backend) | https://github.com/codefox-inc/convex-oauth-provider | 2026-10-09 | F0389 |

The **closed-service clients** (rows 1, 2, 76, 80 and 81) were parked under one rule, stated here so
it can be reviewed. An open client whose function is to call a closed hosted service is outside this
sweep's open-source scope, because what makes the decision is the service. Each belongs with its
service in the closed-comparator pass. Kontext was kept: its policy is evaluated locally, though setup
needs a token from its hosted dashboard. AgentSafe was parked because its README says the proxy
"decides nothing itself".

## Duplicates and resolution-ledger hits

| # | Signal | Source | Resolves to | Primary source | Fetched | Evidence ids |
|---|---|---|---|---|---|---|
| 1 | GetBindu/Bindu | GH-3 | resolution ledger: `excluded_boundary` (#413, 2026-08-30) | https://github.com/GetBindu/Bindu | 2026-10-09 | F0028 F0116 |
| 2 | omnigent-ai/omnigent | MOZ | resolution ledger: `excluded_boundary`, general-agent-frameworks (#413). Named by Mozilla | https://github.com/omnigent-ai/omnigent | 2026-10-09 | F0077 F0214 |
| 3 | NangoHQ/nango | LEAD | resolution ledger: `excluded_boundary`, domain-applications (#413) | https://github.com/NangoHQ/nango | 2026-10-09 | F0076 F0212 |
| 4 | oomol-lab/open-connector | GH-7 | head product `open-connector` (`agent_tools_connectors`) | https://github.com/oomol-lab/open-connector | 2026-10-09 | F0376 |
| 5 | tadata-org/fastapi_mcp | GH-11 | head product `fastapi-mcp` (`agent_protocols`) | https://github.com/tadata-org/fastapi_mcp | 2026-10-09 | F0079 |
| 6 | MCP authorization specification | LEAD | head product `model-context-protocol`: the MCP authorization section is part of the specification | https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization | 2026-10-09 | F0299 |
| 7 | microsoft/agent-governance-toolkit | GH-3 | registry row `agent-governance-toolkit` in `safeguards` (see boundary notes) | https://github.com/microsoft/agent-governance-toolkit | 2026-10-09 | F0082 F0224 F0281 |
| 8 | open-policy-agent/opa-envoy-plugin | GH-1 | self-dedup: component of Open Policy Agent | https://github.com/open-policy-agent/opa-envoy-plugin | 2026-10-09 | F0378 |
| 9 | open-policy-agent/npm-opa-wasm | GH-1 | self-dedup: component of Open Policy Agent | https://github.com/open-policy-agent/npm-opa-wasm | 2026-10-09 | F0380 |
| 10 | open-policy-agent/opa-docker-authz | GH-1 | self-dedup: component of Open Policy Agent | https://github.com/open-policy-agent/opa-docker-authz | 2026-10-09 | F0382 |
| 11 | open-policy-agent/example-api-authz-go | GH-1 | self-dedup: an Open Policy Agent example | https://github.com/open-policy-agent/example-api-authz-go | 2026-10-09 | F0384 |
| 12 | decionis/docker | GH-8 | self-dedup: Docker packaging of AgentSafe (Decionis) | https://github.com/decionis/docker | 2026-10-09 | F0020 F0100 |
| 13 | attenu-io/attenu-guard-ts | GH-4 | self-dedup: TypeScript port of attenu-guard | https://github.com/attenu-io/attenu-guard-ts | 2026-10-09 | F0386 |
| 14 | cedar-policy/cedar-for-agents | LEAD | self-dedup: component of Cedar | https://github.com/cedar-policy/cedar-for-agents | 2026-10-09 | F0246 F0247 |
| 15 | mcp-auth/python | LEAD | self-dedup: the Python SDK of MCP Auth | https://github.com/mcp-auth/python | 2026-10-09 | F0061 F0182 |
| 16 | auth0/auth0-ai-python | LEAD | self-dedup: the Python SDK of the Auth0 AI SDKs | https://github.com/auth0/auth0-ai-python | 2026-10-09 | F0069 F0198 |
| 17 | draft-klrc-aiagent-auth | IETF | self-dedup: replaced by draft-ietf-wimse-aims | https://datatracker.ietf.org/doc/draft-klrc-aiagent-auth/ | 2026-10-09 | F0291 |
| 18 | modelcontextprotocol/typescript-sdk | NPM-2 | head product `mcp-typescript-sdk` (`@modelcontextprotocol/core`) | https://github.com/modelcontextprotocol/typescript-sdk | 2026-10-09 | F0389 |

**Resolution-ledger hits.** All three were ruled `excluded_boundary` under #413 on 2026-08-30. That
verdict is in `NOT_A_NEW_PRODUCT`, so the candidates are dropped and not re-triaged. One is worth the
maintainer's attention. Bindu's note says "the payments dimension has no peer anywhere in the
taxonomy". R-2026-10-08-h has since put agent payment protocols into `agent_protocols`, so the reason
recorded for Bindu may no longer hold. The ledger is append-only, so revisiting it is a new ruling, not
an edit.

## Why the rows are held here

The workflow says a candidate that fits no category is parked against a category proposal, and
that this workflow never edits the taxonomy (`docs/workflows/discover-candidates.md`, steps 4 and
"Stop and escalate"). The ruling says to discover before proposing. The precedent is the 2026-09-26
decision record, where `responsible_ai_measurement` was parked and its seed rows stayed in the sweep
record. So:

- no `sources/registry/` file was written, and no new `category-proposal` issue was opened. #723 is
  already the tracking issue, and the recommendation below is the material for that proposal if the
  maintainer wants one;
- `rows.yaml` holds the 35 rows in registry form. It passes the registry schema once a
  `category` key is added. If a category is created, its seeding PR moves these rows into
  `sources/registry/<category>.yaml` and confirms the org slugs. Six rows use org slugs that already
  exist (`cncf`, `amazon-web-services`, `cloudflare`, `linux-foundation`); the rest are new;
- no candidate was forced into a neighbor to get a row written. The ones that do belong to a
  neighbor are parked with that destination, so a sweep of that category can emit them.

## Draft membership test and boundary notes

**Draft membership test.** Does the product decide, prove or delegate what an AI agent may do, and on
whose authority, before the action runs? It passes if that is its primary function and either:

- (a) it is built for agents; or
- (b) it is a general-purpose identity or authorization system whose own README or documentation ships
  an agent or MCP function, such as a guide, a plugin or a documented integration, and not just a
  passing mention.

An open standard passes on the same test when a standards body's working group holds it. An
individual Internet-Draft does not pass.

The function breaks into five parts, each readable from a product's own documentation:

| Part | Question |
|---|---|
| Identity | Is the agent instance issued its own credential, rather than borrowing a user's secret? |
| Decision | Is each action decided against policy, at the level of tool and arguments, rather than once per session scope? |
| Delegation | Is the principal's authority carried, and narrowed, across hops between agents? |
| Approval | Can a person hold a consequential action before it runs? |
| Evidence | Is there a verifiable record of what was allowed or refused? |

A **capability quantity sketch** for a later ladder counts how many of the five parts a product
implements, with Decision required for band 3 and above. It is a sketch for `build-rubric`, not a
proposal. It has not been tested against the candidates.

**Boundary notes, by neighbor.**

- **`safeguards`** decides by **content**: whether an input or output is harmful. This test decides by
  **authority**: whether this principal may take this action. Arcjet, Invariant and agentshield stay in
  `safeguards`, and so does LlamaFirewall (head). The contested product is
  `agent-governance-toolkit`, a `safeguards` registry row (6,380 stars, MIT) whose description leads with
  policy enforcement and zero-trust agent identity (F0082, F0224). Under this test it would move. That is a
  ruling, not something this sweep does.
- **`agent_tools_connectors`** holds adapters, and its capability ladder already rewards credential
  custody: band 4 and 5 need credentials the product manages. So **credential custody inside an
  adapter stays there.** Composio, Arcade, Open Connector, Pipedream and (per the ledger) Nango stay. A
  standalone authorization server, policy point or approval gate with no adapter belongs here.
  Clawvisor is the edge case: it injects credentials, but it adapts no system, so it is accepted.
- **`agent_protocols`** holds wire contracts and the SDKs that implement them. The MCP authorization
  section stays part of `model-context-protocol`, and A2A's security scheme stays part of
  `agent2agent-protocol`. Agent payment authorization stays there too (x402, AP2 mandates;
  R-2026-10-08-h). Libraries that implement only the authorization half of a protocol (MCP Auth,
  Workers OAuth Provider) come here. The stdio-to-remote bridge `mcp-remote` stays protocol tooling,
  and so do MCP server frameworks with auth as a feature (`golf`, `fastapi-mcp`). The three
  standards in group D could go either way. They are authorization specifications, not agent wire
  protocols, so they are accepted here. Placing them in `agent_protocols` instead is a maintainer
  call.
- **`orchestration_agents`** keeps the permission prompts built into a harness or framework (Claude
  Code, Omnigent per the ledger, LangGraph interrupts). A plugin whose only function is to add
  permission enforcement to a harness (`pi-permission-system`) comes here.
- **`assurance_evidence`** keeps evidence about systems: provenance, verifiable execution and work
  receipts (OpenWorkProof). Evidence of an authorization decision, emitted by the product that made it,
  is the Evidence part of this test.
- **`agent_memory`**: Halofy also keeps durable context. Its README leads with identity, policy and
  audit, so it is accepted here.
- **No identity or security category exists.** General IAM and authorization engines with no
  documented agent function (Permify, ZITADEL, authentik, Ory Hydra and Keto, Topaz, Casbin, CASL,
  SPIRE, Biscuit, UCAN and others) are out. Under test (b), one joins when its own documentation ships
  an agent function. That makes group C time-varying, but each claim is a URL anyone can re-fetch.
- **MCP and agent gateways are unresolved.** These are agentgateway (Linux Foundation, 5,224 stars),
  IBM ContextForge (4,568), Jarvis Registry (3,362), Docker MCP Gateway (1,589), Obot (1,083),
  casbin-gateway (641) and OctoBus (203). Seven products state routing and federation first, with
  authentication and policy as features. Pomerium was accepted because access is its stated function ("an identity and context-aware access
  proxy", F0067). Whether gateways belong here, in `agent_tools_connectors`, or nowhere is a question for
  the maintainer.

## Recommendation

**Propose a new preliminary category.** A suggested slug is `agent_authorization`, displayed as "Agent
identity & authorization". It would sit in Product / UX → Agent interop after `agent_tools_connectors`
and extend the shared `software` ladder. It would stay preliminary, as `world_models` did, and
promotion would wait on the open questions below. This is a recommendation for the maintainer to rule
on. This PR creates nothing.

The counts behind it:

- **35 accepted from 31 organizations** by proposed slug. The largest is `cncf` with 3, or
  8.6%. That passes all three numeric screens of the 2026-09-26 fit heuristic: at least 15 accepted,
  at least 6 organizations, and no organization above 30%.
- **The core alone passes too.** Groups A and B, the 21 products built for agents, come from 21
  organizations. The largest share is 4.8%. If the maintainer rules group C out and puts group D in
  `agent_protocols`, the category still clears the heuristic.
- **Fold into an existing category is not supported.** No neighbor's test admits the core. Group A
  decides by authority and not by content, so `safeguards` does not fit. It adapts no system, so
  `agent_tools_connectors` does not fit. It is not a wire contract, so `agent_protocols` does not fit.
  Stretching any of them to hold it would be the failure the workflow warns about.
- **"Not enough mass" does not hold on count, but adoption is thin where the category is new.** In
  group A, no repository reaches 1,000 stars. The median is 188, 15 of 19 were created in 2026, and 18
  of 19 were pushed in the last six months (Phantasm is dormant). The adoption is elsewhere. Workers
  OAuth Provider has 3,931,972 npm downloads a month, `@better-auth/mcp` 1,286,875 and MCP Auth 71,080.
  Group C's median is 7,116 stars, though its agent function is one documented use among many.
- **The standards gap is real.** Two working-group documents are written for agents (WIMSE AIMS, and
  ID-JAG's AI-agent appendix). AuthZEN is Final, but its MCP binding is a draft. Against these sit
  110 individual drafts. #723 suggested this layer could be the first place the **void** gap
  fires. The sweep does not support a void: open software exists. What it shows is immaturity:
  young, low-adoption agent-specific projects and unsettled standards. That reads more like an
  adoption gap and a standardization gap than an empty cell.

**Questions for the maintainer**, in order:

1. Create `agent_authorization` (or another name) as a preliminary category with the 35 rows in
   `rows.yaml`?
2. Does group C belong, meaning general-purpose systems admitted by test (b)? It is 11 of the 35
   and holds most of the adoption.
3. Do the group D standards belong here or in `agent_protocols`?
4. Where do MCP and agent gateways go (seven parked products)?
5. Does `agent-governance-toolkit` move from the `safeguards` registry?
6. Is the closed-service-client rule above right, and should a closed-comparator pass (ADR-005) run
   before promotion? Its leads are Permit.io (F0258), Oso for Agents (F0257), Auth0, Decionis, Quirna
   and Ziffer.
7. Should Bindu's ledger entry be revisited now that payments have a home?

## Limits

- GitHub's REST API and website returned 403. Discovery depended on the session's search connector,
  and on ecosyste.ms for metadata. Two npm-named repositories (AgentAuthorityChain/aac,
  aeternm/authoxi) did not resolve on either, and they are parked for that reason, not judged.
- PyPI and Hugging Face were not swept for discovery.
- Closed products were not swept.
- The OpenID Foundation's AI identity management community group page returned 404 (F0295) and was
  not used.
- The GitHub cutoff was declared after GH-4 was read. The workflow requires that already-surfaced
  candidates under a cutoff be parked rather than dropped, and they were. OxDeAI was below the cutoff
  on GitHub but inside the npm cutoff, so it was judged on its merits and accepted.
- npm monthly downloads are the `downloads.monthly` field of the npm search API at fetch time.
- Every evidence id resolves to a row in `fetch-log.tsv`. The bodies themselves are not committed,
  but each row carries the sha256 of the body as fetched.
