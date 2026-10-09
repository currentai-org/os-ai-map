# Agent front-door sweep: 2026-10-09

## Scope and boundary

This sweep follows a review of the OSO page "How to build your own open source Instinct", which
walks through Open Instinct (`mariagorskikh/open-instinct`, MIT, by Maria Gorskikh), a personal
agent you text. The review found two things.

1. **Products the page names that the map lacks.** These are Pi (the agent loop), Maritime (the
   microVM host), Inkbox (the agent's phone number, iMessage line and email inbox) and Stripe Link
   (the agent's wallet). Each was checked against primary sources fetched today. Pi and Maritime have a
   home category and get registry rows. Inkbox and Stripe Link have none, so they are parked here.
2. **The page's biggest gap.** The page says no open, self-hostable product gives an agent a phone
   number, an iMessage or SMS line, an email inbox and a payment wallet. This "front door" is what
   the sweep covers.

**In scope:** open-source and open-standard software that gives an agent its own reachable channel
(email inbox, phone number, SMS or iMessage line, multi-channel messaging identity) or its own
payment wallet. **Membership test applied:** a candidate is accepted only if it is **built for
agents**, meaning its own repository description or README presents it as giving an agent this
channel or wallet. A general-purpose messaging server, bridge or SMS gateway is **adjacent**, even
when people commonly wire agents to it. This mirrors ruling R-2026-10-09-b, which keeps
`agent_authorization` strictly agent-specific and admits a general-purpose system only once its
product identity becomes agent-first. An open SDK or MCP client of a closed hosted service is
parked as a closed-service client, mirroring R-2026-10-09-f.

**Not swept:** voice-agent frameworks and SIP stacks, which belong to a speech pass. Also not swept
are agent-to-agent messaging tools, which are `agent_protocols` territory, and closed products.
Closed products found along the way are recorded as comparators, not swept for.

**No category was created.** Rows were written to `sources/registry/` only where a home category
exists. The front-door candidates are held in `rows.yaml` for the maintainer to rule on. Nothing was
scored.

## Window

A single snapshot. Every source was read on 2026-10-09, with no creation-date floor. The next sweep
of this area can start from 2026-10-09.

## Files in this directory

| File | What it holds |
|---|---|
| `README.md` | This record |
| `fetch-log.tsv` | Every fetch: id (`F0001`…), date, HTTP status, bytes, sha256 of the body, URL. The `F` ids below point here |
| `candidates.tsv` | All 51 raw signals with the proposed slug, identifiers, proposed org, source, disposition and the fetch ids behind each |
| `rows.yaml` | The 10 accepted front-door candidates as registry rows (no `category` key), schema-valid against `docs/schemas/registry.schema.json` |

## Sources and retrieval cutoffs

GitHub repository search ran through the session's GitHub search connector. A direct call to
`api.github.com` returned 403 (F0006) and ecosyste.ms returned 402 (F0007, F0008), so star counts and
creation dates are the search connector's, as of 2026-10-09. READMEs and LICENSE files come from
`raw.githubusercontent.com`. Package facts come from the npm and PyPI registries.

**What counts as a raw signal.** A raw signal is one distinct product name that a source surfaced
and whose own description names an agent channel, a messaging or email server, an SMS or iMessage
gateway, or an agent wallet as its function. A **repeat** is a name already counted from an earlier
source. A **package-level hit** is another repository or package of a product already listed. A
**screened** result is one whose description is about something else: an agent that *uses* email,
an agent-to-agent bus, a template list. Awesome-lists are sources, not candidates.

**Retrieval cutoffs, declared before reading:** GitHub queries used the star floors shown, and every
result each query returned was read. No candidate was rejected for falling under a floor.

| Id | Source | Query or page | Cutoff | Read | Signals | Repeats | Screened |
|---|---|---|---|---|---|---|---|
| NAMED | The OSO page review, products named in Open Instinct's README (F0001) | Pi, Maritime, Inkbox, Stripe Link, Composio, Open Instinct | all | 6 | 6 | 0 | 0 |
| PAYPROTO | The brief: payment protocols already seeded in `agent_protocols` (#868) | x402, L402, AP2, MPP | all | 4 | 4 | 0 | 0 |
| LEAD | The brief's lead list plus the sweeper's leads, each looked up directly | BlueBubbles, mautrix iMessage, Google Messages, WhatsApp and Signal bridges, signal-cli, Jasmin, Stalwart, JMAP, SMS Gateway for Android, GOAT, AgentMail, imessage-kit, Spectrum, AgentKit | all | 15 | 15 | 0 | 0 |
| GH-1 | GitHub search | `agent email inbox in:name,description stars:>=100` | ≥100 | 6 of 6 | 3 | 0 | 3 |
| GH-2 | GitHub search | `imessage agent in:name,description stars:>=100` | ≥100 | 3 of 3 | 2 | 1 | 0 |
| GH-3 | GitHub search | `sms gateway in:name,description stars:>=500` | ≥500 | 9 of 9 | 7 | 2 | 0 |
| GH-4 | GitHub search | `agent wallet payments in:name,description stars:>=200` | ≥200 | 2 of 2 | 1 | 0 | 1 |
| GH-5 | GitHub search | `phone number ai agents telephony in:name,description stars:>=300` | ≥300 | 0 | 0 | 0 | 0 |
| GH-6 | GitHub search | `wallet for ai agents in:description stars:>=200` | ≥200 | 5 of 5 | 4 | 0 | 1 |
| GH-7 | GitHub search | `bluebubbles OR mautrix OR signal-cli OR stalwart in:name`, by stars | name lookup | first 30 of 1,569 | 1 | 7 | n/a |
| GH-8 | GitHub search | `email for ai agents in:description stars:>=100` | ≥100 | 17 of 17 | 6 | 3 | 8 |
| GH-9 | GitHub search | `topic:agent-communication stars:>=50` | ≥50 | 16 of 16 | 1 | 2 | 13 |
| GH-10 | GitHub search | `sms ai agent in:name,description stars:>=100` | ≥100 | 7 of 7 | 1 | 3 | 3 |
| | | | | | **51** | | |

**Queries used for lookups only.** GH-7 resolved the named leads. Its other results were the
BlueBubbles client app, mautrix bridges for non-front-door networks (Telegram, Discord, Meta,
Twitter, Slack, Google Chat) and unrelated SignalR libraries, and they were not read as signals.
Two owner listings were lookups too: `user:photon-hq`, which located Spectrum after the imessage-kit
README named it, and `user:KeyID-AI`. A query
`agentkit OR "virtual card" agent in:name,description stars:>=200` was malformed (the `OR` matched
the whole of GitHub) and was discarded unread. `agentkit user:coinbase` resolved AgentKit, and the
voice query `voice agent telephony sip phone in:name,description stars:>=500` returned nothing. PyPI
has no search API, so PyPI and npm were used for verification only. Hugging Face was not swept,
because the scope is software and standards.

**Screened results, by query.** GH-1: Lifecycle-Innovations-Limited/claude-ops,
tonykipkemboi/crewai-gmail-automation, gaoxin492/PaperFeeder. GH-4 and GH-6: nirholas/three.ws
(screened in both). GH-8: enescingoz/awesome-n8n-templates, macro-inc/macro, eracle/OpenOutreach,
OpenClaudia/openclaudia-skills, haoruilee/awesome-agent-native-services (an awesome-list),
kaymen99/langgraph-email-automation, mr-tbot/mesh-api, JayleeBot/ForgeFlow. GH-9, all agent-to-agent
messaging and not a front door: robustmq/robustmq, Prismer-AI/PrismerCloud, fujibee/agmsg,
AgentWorkforce/relay, 23blocks-OS/ai-maestro, sno-ai/sno-station, Cotal-AI/Cotal,
pilot-protocol/pilotprotocol, automatis-tools/agents-can-communicate, AgentAnycast/agentanycast,
Vortx-AI/emem, Riccardo8888/agent-link, blackwell-systems/gcf. GH-10: mr-tbot/mesh-api (repeat
screen), nickvasilescu/nicks-stack, IAmTomShaw/stock-tracker-agent. **Package-level hits:**
KeyID-AI/sdk-js and KeyID-AI/sdk-py (GH-8) and sv-number/skills (GH-10).

## Reconciled counts

```text
raw_signals       = 51   (NAMED 6 + PAYPROTO 4 + LEAD 15 + GH-1 3 + GH-2 2 + GH-3 7 + GH-4 1
                          + GH-6 4 + GH-7 1 + GH-8 6 + GH-9 1 + GH-10 1)
duplicate_signals = 6    (Composio: head product; x402, L402, AP2, MPP, Bindu: registry rows
                          in agent_protocols)
unique_candidates = 45   = 51 - 6
accepted          = 12   (2 written to sources/registry/ + 10 held in rows.yaml)
parked            = 33
check             : 6 + 45 = 51; 12 + 33 = 45
```

## Accepted candidates

### Written to `sources/registry/` (a home category exists)

| Slug | Category | Identifiers | What the primary sources say | Evidence |
|---|---|---|---|---|
| `pi-coding-agent` (Pi) | `orchestration_agents` | `github: earendil-works/pi`, `npm: @earendil-works/pi-coding-agent`, `homepage: https://pi.dev` | "A minimal, extensible agent harness" with an agent runtime (`pi-agent-core`), a unified multi-provider LLM API (`pi-ai`) and a coding-agent CLI. MIT, copyright 2025 Mario Zechner. The npm package is at 1.1.0, last published 2026-10-07. The repository was created 2025-08-09 and had 113,784 stars on 2026-10-09. pi.dev and earendil.com both name Earendil Inc. Open Instinct's architecture notes name `pi-agent-core` and `pi-ai` as its agent loop. | F0003, F0004, F0005, F0011, F0019, F0031 |
| `maritime` | `deployment` | `github: maritime-sh/maritime-sdk`, `npm: maritime-sdk`, `pypi: maritime`, `homepage: https://maritime.sh` | A hosted service that "hosts agents in Firecracker micro-VMs that sleep when idle". It provides a persistent disk, sleep and wake, and an optional Linux desktop. The service source is not published. The SDKs are MIT ("Copyright (c) 2026 Maritime"): npm `maritime-sdk` 0.9.0, published 2026-09-30, and PyPI `maritime` 0.8.0. A free plan of 3 machines, then flat monthly plans. Its peers in `deployment` are `fly-sprites` and `vercel-sandbox`, both hosted Firecracker microVM services. | F0009, F0010, F0012–F0015, F0018 |

Two notes on Maritime. **The identifiers are the SDKs, not the service.** A later `add-product`
must score openness on the hosted platform, as `vercel-sandbox` and `fly-sprites` are scored (an
open client over a closed runtime), not on the SDK's MIT license. The npm name `maritime` held a
2020 package whose versions were all unpublished on 2022-05-27; the name is now held by Maritime's
own maintainers with no versions (F0016, F0109). `@maritime-sh/sdk` does not exist (F0017). Neither
is used. **Disclosure:** Maritime and Open Instinct are not independent. Maria Gorskikh, Open
Instinct's author, is Maritime's co-founder and CEO (Maritime AI, Inc., Y Combinator Fall 2026;
F0107), and Maritime's own post on Open Instinct says "We built it" (F0108). The "paper" on
Maritime's homepage (F0010) is a demo graphic whose authors are Maritime's three staff. Open
Instinct's choice of host is the vendor's showcase, not evidence of Maritime's standing, and
Maritime's adoption should not be read from Open Instinct's.

*Corrected 2026-10-09 after a follow-up check (F0107–F0110). The first version of this note called
the npm `maritime` name an unrelated 2020 package, cited `composio` as the openness precedent, and
described the tie to Open Instinct only as a co-authored paper.*

### Held in `rows.yaml` (no home category; for the maintainer to rule on)

Stars and creation dates are the GitHub search connector's, 2026-10-09.

| Slug | Group | Repository | License (as read) | Self-hostable? | Stars, created | Evidence |
|---|---|---|---|---|---|---|
| `sentio-smtp` | Inbox | truespar/sentio | MIT OR Apache-2.0 | Yes. A full multi-tenant mail server in Rust, run with Docker | 251, 2026-08-23 | F0036, F0037 |
| `e2a` | Inbox | tokencanopy/e2a | Apache-2.0 | Yes (Docker), plus hosted e2a.dev | 193, 2026-04-25 | F0038, F0039 |
| `agenticmail` | Inbox, SMS, calls | agenticmail/agenticmail | MIT | Yes. Runs a local Stalwart server. SMS comes through Google Voice or 46elks, calls through 46elks or Twilio | 236, 2026-02-14 | F0040, F0041, F0093 |
| `mails` | Inbox | chekusu/mails | MIT per npm. No LICENSE file at the repository root (F0043 404) | Yes, on Cloudflare, plus hosted mails.dev | 367, 2026-03-17 | F0042, F0092, F0100 |
| `mailroom` | Inbox | wong2/cf-mailroom | Apache-2.0 | Yes, on the operator's own Cloudflare account | 334, 2026-04-17 | F0044, F0045 |
| `goshen-email` | Inbox | boringcomputers/goshen-email | FSL-1.1-ALv2 (source-available, not OSI until its Apache conversion) | Hosted service with published source | 150, 2026-09-15 | F0046, F0047 |
| `caspian` | Multi-channel | TryCaspian/caspian-sdk | **Conflicting.** The LICENSE file is AGPL-3.0, the README badge says Apache-2.0, and PyPI declares none | Partly. Self-host adapters cover email, Telegram, Slack and Discord. WhatsApp, phone and iMessage go only through Caspian's hosted gateway | 973, 2026-07-20 | F0050, F0051, F0096 |
| `spectrum` | Multi-channel | photon-hq/spectrum-ts | MIT | Partly. The framework is open, and its iMessage route is the hosted Spectrum Cloud | 1,974, 2025-12-20 | F0085, F0090, F0091, F0098 |
| `imsg` | iMessage and SMS line | openclaw/imsg | MIT | Yes, on a Mac signed in to Messages.app | 1,357, 2025-12-05 | F0052, F0053 |
| `coinbase-agentkit` | Wallet | coinbase/agentkit | Apache-2.0 | Library. Wallet-agnostic, with Coinbase's CDP API as the default wallet provider | 1,324, 2024-10-31 | F0081, F0082, F0095, F0099 |

Nine organizations supply the nine channel candidates, one each, so the largest share is 11%. With
the wallet it is ten from ten.

## Parked candidates

Each row's sources are in `candidates.tsv` and `fetch-log.tsv`. All fetches are dated 2026-10-09.

| Candidate | Reason parked |
|---|---|
| **Inkbox** (inkbox-ai/inkbox, npm `@inkbox/sdk`, PyPI `inkbox`) | **No home category** (the brief's rule). Inkbox is a hosted service that gives an agent email, a phone number, iMessage, an internet address, A2A, an encrypted vault and tunnels under one identity (F0023, F0026, F0030). The repository holds MIT SDKs, a CLI and skills, and no server source. Open Instinct's docs mention an `INKBOX_BASE_URL` "only for a self-hosted Inkbox" (F0020), but no published server was found. It is a closed comparator for the front door, and the closed-service-client rule applies to its SDK. |
| **Stripe Link agent wallet** (stripe/link-cli, npm `@stripe/link-cli`, `@stripe/link-sdk`) | **No home category.** A hosted Link wallet issues one-time virtual cards, Link Pay Tokens or Shared Payment Tokens (MPP) on the owner's approval. It is limited to US and Canadian accounts (F0024, F0033, F0035). The CLI and SDKs are MIT (F0034), and the wallet is closed. It is a closed comparator for the wallet. |
| Open Instinct (mariagorskikh/open-instinct) | **Outside this sweep's scope.** It is the personal agent the page describes, not a front-door component. It is MIT (F0002), at version 0.1, created 2026-10-03, with 275 stars. Its home would be `orchestration_agents` if the map wants personal agents as such. |
| raroque/boop-agent | **Outside scope**, for the same reason: an iMessage personal agent (F0057). |
| BlueBubbles server | **Adjacent, general-purpose.** An iMessage forwarding server for the BlueBubbles client apps, Apache-2.0 (F0058, F0059). |
| mautrix-imessage, mautrix-gmessages, mautrix-whatsapp, mautrix-signal | **Adjacent, general-purpose.** Matrix puppeting bridges, AGPL-3.0 (F0060–F0067). They need a Matrix homeserver, and `mautrix-imessage` needs a Mac. |
| signal-cli; bbernhard/signal-cli-rest-api | **Adjacent, general-purpose.** An unofficial Signal CLI and JSON-RPC interface, GPL-3.0 (F0068, F0069), and a Docker REST wrapper around it (F0070). |
| SMS Gateway for Android (capcom6), textbee, gosms, SMSSync, playSMS, Traccar SMS Gateway, android_income_sms_gateway_webhook | **Adjacent, general-purpose.** Phone-as-gateway and SMS web front ends. SMS Gateway for Android is Apache-2.0 (F0071, F0072) and textbee is MIT (F0073, F0074). Read from the search connector only: gosms, SMSSync, playSMS, Traccar, android_income_sms_gateway_webhook. |
| Jasmin | **Adjacent, general-purpose.** An SMPP and HTTP SMS gateway, Apache-2.0, PyPI `jasmin` 0.11.1 (F0076, F0105, F0106). |
| MddIdd/mdd-sim-gateway | **Adjacent, general-purpose.** A self-hosted SIM and eSIM gateway for calls and SMS (F0083). |
| Stalwart | **Adjacent, general-purpose.** An IMAP, JMAP and SMTP mail and collaboration server (F0077, F0078). AgenticMail runs on it. |
| JMAP (RFC 8620, RFC 8621) | **Adjacent, general-purpose open standard** for mail access (F0079, F0080, F0102). |
| Photon imessage-kit | **Adjacent.** Its identity is "a type-safe, elegant iMessage SDK for macOS". Agents are one use the README lists (F0085, F0086, F0094). Photon's agent-first product is Spectrum, which is accepted. |
| cloudflare/agentic-inbox | **Boundary.** A self-hosted email client for a person, with an AI assistant that reads that person's inbox (F0048). It is not an agent's own channel. |
| KeyID agent-kit (npm `@keyid/agent-kit`) | **Closed-service client.** MCP tools for the hosted keyid.ai email service (F0054, F0097). No LICENSE file in the repository (F0055 404). npm says MIT. |
| sv-number/mcp-server | **Closed-service client.** Rents phone numbers from a hosted service for SMS verification codes (F0056). |
| AgentMail (agentmail-to/agentmail-python) | **Closed-service client.** A generated SDK for the hosted AgentMail API (F0084). It is a closed comparator for inboxes. |
| GOAT (goat-sdk/goat) | **Archived.** The README says the repository "is a read-only historical snapshot" (F0087). |
| BlockRunAI/ClawRouter | **Boundary.** An LLM router that pays per call over x402. Its function is routing, not a wallet. |
| swapperfinance/swapper-toolkit, GMGNAI/gmgn-skills, okx/onchainos-skills, bitget-wallet-ai-lab/bitget-wallet-skill | **Closed-service clients.** Agent skills for trading on one exchange's or wallet's API, not an agent payment wallet. Read from the search connector only. |

## Duplicates

| Signal | Matched |
|---|---|
| Composio | head product `composio` (`agent_tools_connectors`) |
| x402, L402, AP2, MPP | registry rows `x402`, `l402`, `agent-payments-protocol` and `machine-payments-protocol` in `agent_protocols` (#868), counted as duplicates as the brief asked |
| Bindu | registry row `bindu` in `agent_protocols` (R-2026-10-09-g) |

No candidate matched a retired alias or a resolution-ledger entry. The warehouse discovery pool was
not consulted.

## Why these rows are held here

The workflow parks a candidate that fits no category and never edits the taxonomy
(`docs/workflows/discover-candidates.md`, step 4). Following the 2026-10-09 agent-authorization
record, the ten front-door rows sit in `rows.yaml` in registry form. If the maintainer creates a
category, its seeding PR moves them into `sources/registry/<category>.yaml` and confirms the
org slugs. No `category-proposal` issue was opened. This record and its PR are the proposal
material.

Proposed org slugs: `truespar`, `tokencanopy`, `agenticmail`, `chekusu`, `wong2`, `boringcomputers`,
`trycaspian`, `photon`, `openclaw` (exists already: it owns the published `openclaw` product) and
`coinbase`.

No candidate was stretched into a neighbor to get a row written. `imsg`, `caspian` and `spectrum`
could be read as connectors under `agent_tools_connectors`, whose test is "adapters that put a
system an agent does not own within its reach". Placing them there now would split the cluster
before the maintainer has ruled on it.

## Draft membership test and boundary notes

**Test:** software or an open standard whose primary identity is giving an AI agent its own
reachable channel (email address and inbox, phone number, SMS or iMessage line, a messaging
identity across channels), or its own means of payment.

- **vs `ui_api`.** OpenClaw, a published product there, is a personal assistant that *uses*
  channels. A front-door product is the channel layer an assistant like that is built on. Open
  Instinct and boop-agent are assistants and stay out.
- **vs `agent_tools_connectors`.** A connector reaches a system the agent does not own: Slack,
  GitHub, a browser. A front-door product gives the agent an address of its own. Messaging adapters
  such as `imsg` sit on the line, and the maintainer should rule which side they fall on.
- **vs `agent_protocols`.** Agent-to-agent transports and payment protocols stay there. An A2A
  endpoint offered by Inkbox does not move Inkbox into it.
- **vs `agent_authorization`.** Inkbox's vault and Stripe Link's spend approvals touch authority. Their
  primary function is a channel or a wallet, so they do not move.
- **General-purpose systems** (Stalwart, JMAP, mautrix, BlueBubbles, signal-cli, SMS gateways) are
  adjacent and named in the boundary notes, as R-2026-10-09-b does for IAM systems.

## What the sweep found about the gap

- **Email has open, self-hostable, agent-specific supply.** Six projects: Sentio, e2a, AgenticMail,
  mails, Mailroom and Goshen. All but Goshen carry an OSI license (mails only through its npm
record), and every one was created in 2026.
- **The messaging line does not.** Every open iMessage route needs a Mac signed in to an Apple ID.
  That is true of `imsg`, BlueBubbles, mautrix-imessage and imessage-kit. Otherwise the route goes
  through a hosted service: Inkbox, Spectrum Cloud, Caspian's gateway. SMS can be self-hosted only
  through an Android phone or SIM gateway (general-purpose) or a carrier account.
- **No open software supplies the phone number itself.** Numbers come from carriers or hosted
  services: Twilio, 46elks, Google Voice, Inkbox, sv-number. That is a structural limit, not a
  software gap.
- **Wallets split along fiat and crypto lines.** Open, agent-specific wallet code exists for crypto
  (AgentKit) and as protocols (x402, L402, AP2, MPP, already mapped). One-time cards on fiat rails
  come from a closed issuer (Stripe Link). One open candidate is not mass.

## Recommendation

**Not enough mass yet for a new category. Do not fold either.** This is for the maintainer to rule
on, and this PR creates nothing.

- Against the 2026-09-26 screening heuristic (`docs/sweeps/2026-09-26-new-categories-decisions.md`),
  the channel set is **9 accepted from 9 organizations**, with no organization above 11%. It passes
  the independence screens but falls short of 15. With the wallet it is 10. Adoption is thin: the
  median is 334 stars, and seven of the nine were created in 2026.
- **The shape is clear if the maintainer wants the gap visible now.** The heuristic permits an
  override for "an important emerging category with 12 products from 8 independent teams". A
  preliminary category for agent channels ("agent messaging identity", suggested slug
  `agent_channels`) would hold the nine channel rows, with Inkbox, AgentMail, KeyID and Spectrum
  Cloud as its closed comparators. The wallet should not ride along. AgentKit and Stripe Link are a
  separate payments question, beside the protocols R-2026-10-08-h already placed in
  `agent_protocols`.
- **Folding into `agent_tools_connectors` is the weaker option.** It would admit the adapters
  (`imsg`, `caspian`, `spectrum`) and leave the six inbox servers, the most open part of the
  cluster, with no home.

**Questions for the maintainer**, in order:

1. Create a preliminary category for agent channels now, by override, or wait for a second pass
   (npm search, lower star floors, closed comparators under ADR-005) and re-rule on the count?
2. If one is created, do messaging adapters (`imsg`, `caspian`, `spectrum`) belong in it or in
   `agent_tools_connectors`?
3. Where do agent wallets go (AgentKit open, Stripe Link closed)?
4. Is a general-purpose server that ships an agent mode (Stalwart, if it does) admitted only under
   the R-2026-10-09-b rule, meaning when its product identity becomes agent-first?

## Limits

- GitHub's REST API returned 403 (F0006) and ecosyste.ms returned 402 (F0007, F0008). Discovery and
  repository metadata depended on the session's GitHub search connector, which reports stars and
  dates but not licenses. Licenses were read from raw LICENSE files and package registries.
- npm and PyPI were not swept for discovery. Hugging Face was not swept.
- Closed products were not swept. The ones listed above were found along the way.
- Ten parked candidates were judged from the search connector's description alone: gosms, SMSSync,
  playSMS, Traccar SMS Gateway, android_income_sms_gateway_webhook, ClawRouter and the four
  trading skills. All are parked, so no accepted row rests on a description alone.
- Jasmin's `README.md` returned 404 (F0075). The repository's README is `README.rst` (F0105).
- Every evidence id resolves to a row in `fetch-log.tsv`. The bodies are not committed, but each
  row carries the sha256 of the body as fetched.
