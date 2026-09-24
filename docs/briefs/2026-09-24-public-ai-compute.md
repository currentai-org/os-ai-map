# Public AI compute: who can get capacity, 2026-09-24

This brief answers issue #687, which asked whether public AI compute can be a scored category
and what the unit of a row would be. The unit is the **access program**, the thing a person
applies to. It is not scored yet: the openness question has a clean answer in each program's
access terms, but adoption and capability can't be measured consistently from what programs
publish. This page is the inventory, and it is a dated record like the sweep records in
`docs/sweeps/`. Figures describe what the cited page said on the date above.

## The unit is the program

A program is what a researcher, startup or agency applies to. Three things rule out the other
candidate units:

- **One machine sits behind several programs.** LUMI, Leonardo and JUPITER take users through
  EuroHPC calls and through national calls. Frontier is allocated through both INCITE and ALCC.
  A row per machine counts the same capacity more than once.
- **Several programs own no machine.** The IndiaAI Mission subsidizes GPUs owned by empanelled
  private providers. Korea's GPU provision program is hosted at Naver Cloud, NHN Cloud and
  Kakao. Canada's AI Compute Access Fund is money spent on commercial clouds. A row per machine
  leaves these out entirely.
- **Hardware is already a separate proposal.** Accelerators as products are issue #599. What the
  compute runs on is a different question from who can get it.

A facility is an attribute of a program. Isambard-AI and Dawn are the facilities of the UK AI
Research Resource. The EuroHPC machines are the facilities of the AI Factories and of their
national hosts.

**The litmus**, from the issue: a program is in scope when it is publicly funded or publicly
mandated, and someone outside the operating institution can apply for or be allocated training
or inference capacity. Out of scope are:

- commercial cloud and inference APIs, which stay in `inference_code`
- hyperscaler research-credit programs, which are commercial access with a grants budget
- an institution's internal cluster with no outside call
- a private data center without a public allocation attached

A private build-out whose subsidy carries a public allocation is in scope. The IndiaAI
empanelment and Israel's Nebius tender are the clearest examples.

## Why it isn't scored

The three axes would have to mean something other than what they mean on the rest of the map.

| Axis | On the rest of the map | What it would have to mean here | Can it be measured today? |
|---|---|---|---|
| Openness | License and release of artifacts | Access terms: who is eligible, what it costs, whether commercial use is allowed, whether outputs must be open | Yes. Every live program publishes eligibility and cost. Open-output rules are published by fewer. |
| Adoption | Downloads, stars, dependents | Projects or users served, or GPU-hours allocated | No. About half the programs publish usage, in units that don't compare: projects, researchers a month, node-hours, credits. |
| Capability | Peer comparison on what the product does | Capacity available to outside users | Partly. Machine sizes are public, but the share allocated to outside users usually isn't, and vouchers have no fixed capacity. |

A scored category would also need a new product `type` and an openness ladder of its own, since
none of `model`, `software`, `dataset` or `hardware` fits a program. That is a schema change,
and it is not worth making until adoption and capacity can be filled in for more than a handful
of rows. A ranking built on the openness axis alone would compare a free, peer-reviewed allocation
against a subsidized voucher as if they were two grades of one thing.

## Inventory

**Provision** extends the typology in the Ada Lovelace Institute's *Computing Commons* report.
The first three values are Ada's:
- `direct-generalist`: a public HPC machine that also takes AI work
- `direct-ai`: a public machine built for AI
- `market-based`: public money spent on commercial capacity, as vouchers or subsidies

The last two are added here, because several programs fit none of Ada's values:
- `federated`: one program allocating across several public machines or sites
- `hybrid`: a private build with a public allocation or public co-funding attached

Ada's fourth type, decentralised provision, has no qualifying row here.

**Status** is one of:
- `live`: you can apply now
- `building`: funded, not yet generally usable
- `announced`: law, strategy or a call for proposals, with no capacity yet

Capacity and usage appear only where the program's own page, or a named government release,
publishes them. The notes after each table flag press-only figures.

### Americas

| Program | Jurisdiction | Provision | Status | Who can apply, on what terms | Capacity and usage (published) | Source |
|---|---|---|---|---|---|---|
| NAIRR Pilot, moving to the NAIRR Operations Center | US | federated | live | US academic, nonprofit, federal, state, local and tribal researchers and educators; startups only with a federal grant. Free and peer-reviewed. Results must be open and publishable. | 900 projects in all 50 states, DC and PR; 101 classroom awards. NSF's two-year update gives about 6,000 students. No capacity total. | [nairrpilot.org](https://nairrpilot.org/), [NSF release](https://www.nsf.gov/cise/updates/nsf-establishes-operations-center-national-artificial), [two-year update](https://nsf-gov-resources.nsf.gov/files/NAIRR-2-Year-Progress-Update.pdf) |
| NSF ACCESS | US | federated | live | US researchers and educators, grant or no grant. Free, in four tiers from an eligibility check (Explore) to panel review (Maximize). | More than 4,000 researchers a month; more than 2,000 projects. | [access-ci.org](https://access-ci.org/), [allocations](https://allocations.access-ci.org/) |
| NSF LCCF Horizon (TACC) | US | direct-generalist | live, early operations | AI users apply through NAIRR's Deep Partnerships track, HPC users through LCCF. | 2,000 GB200 nodes (press). | [LCCF allocations](https://lccf.tacc.utexas.edu/allocations/) |
| DOE INCITE and ALCC | US | federated | live | INCITE takes 60% of leadership-system time and is open to any researcher worldwide, industry included. ALCC takes about 20%. Free and competitive. | INCITE 2026: 75 projects, with requests over 141M node-hours. | [OLCF INCITE 2026](https://www.olcf.ornl.gov/2026/04/07/incite2026awards/), [ALCC call](https://science.osti.gov/ascr/Facilities/Accessing-ASCR-Facilities/ALCC/Call-for-Proposals) |
| DOE Genesis Mission | US | hybrid | live | Grant program bundling lab compute with models and data. First round: 87 lab-led, 168 university-led, 19 company-led and 4 nonprofit-led projects. | 278 projects. Compute share not published. | [DOE release](https://www.energy.gov/articles/secretary-energy-chris-wright-announces-first-genesis-mission-projects-selected-accelerate) |
| NSF State and Regional AI Infrastructure Hubs | US | federated | announced | Up to 10 hubs at $4M to $12M each. NSF pays for coordination; states, industry and philanthropy are expected to pay for the compute. Proposals due 2026-11-04. | None yet. | [NSF 26-513](https://www.nsf.gov/news/new-nsf-state-regional-ai-infrastructure-hubs-will-power-ai) |
| Empire AI | New York | direct-ai | live | Researchers at the ten member institutions only, through each institution's internal call. | Beta: 288 Blackwell GPUs in DGX GB200 systems, fully online, with 11x Alpha's training capacity. More than 130 projects ran on Alpha. | [Empire AI](https://www.empireai.edu/2025/06/27/empire-ai-launches-beta-one-of-the-most-powerful-academic-ai-supercomputers-in-the-nation/), [Governor's release](https://www.governor.ny.gov/news/governor-hochul-announces-empire-ai-beta-fully-online-federal-government-takes-inspiration-new) |
| Massachusetts AI Compute Resource | Massachusetts | direct-ai | building | Intended for startups, businesses, researchers and state agencies. Terms not published. | "Hundreds" of GPUs. | [MassTech](https://masstech.org/news/healey-driscoll-administration-celebrates-selection-cambridge-computer-build-landmark) |
| Redtail (University of Utah CHPC) | Utah | direct-ai | live, early access | Selected early-access projects now. A quarterly open allocation is planned for Utah higher education, state bodies and commercial users. | 264 H200; No. 159 on the June 2026 TOP500. | [CHPC](https://www.chpc.utah.edu/resources/utah-ai-supercomputer.php), [Redtail](https://www.chpc.utah.edu/redtail/index.php), [funding](https://attheu.utah.edu/research/state-backed-ai-supercomputer-set-to-expand-research-capacity-across-utah-this-summer/) |
| CalCompute | California | not yet decided | announced | SB 53 creates a consortium to deliver a framework for a public compute cluster by 2027-01-01. No machine and no appropriation found. | None. | [SB 53](https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202520260SB53) |
| AI Compute Access Fund | Canada | market-based | live, intake closed | Canadian firms under 500 staff. Covers two-thirds of costs on Canadian clouds and half on foreign ones. Commercial by design, with no open-output rule. | 44 projects, C$66M. | [ISED](https://ised-isde.canada.ca/site/ised/en/canadian-sovereign-ai-compute-strategy/ai-compute-access-fund), [release](https://www.canada.ca/en/innovation-science-economic-development/news/2026/05/government-of-canada-supports-44-canadian-companies-using-ai-to-transform-industries-and-create-jobs.html) |
| Resource Allocation Competition (Digital Research Alliance) | Canada | federated | live | Faculty at Canadian academic institutions apply as PIs; affiliated researchers get smaller Rapid Access allocations. Free. | Fir 640 H100, Nibi 288 H100, Trillium 252 H100, Rorqual 324 GPUs. RAC 2024 awarded 21% of the GPU-years requested. | [eligibility](https://alliancecan.ca/en/services/advanced-research-computing/account-management/user-roles-access-resources-and-services-federation), [systems](https://www.alliancecan.ca/en/services/compute), [RAC 2024](https://www.alliancecan.ca/en/2024-resource-allocations-competition-results) |
| Pan-Canadian AI Compute Environment (PAICE) | Canada | federated | live | Free. Priority goes to CIFAR AI Chairs and faculty at Mila, Amii and Vector, with other Canadian AI researchers phased in. | Not published. | [Alliance](https://www.alliancecan.ca/en/our-services/advanced-research-computing/pan-canadian-ai-compute-environment-paice) |
| AI Sovereign Compute Infrastructure Program | Canada | direct-ai | building | Applications were for building the machine. There is no user queue yet. | None yet. | [release](https://www.canada.ca/en/innovation-science-economic-development/news/2026/04/canada-launches-national-initiative-to-build-large-scale-ai-supercomputing-capacity.html) |
| SDumont (LNCC) | Brazil | direct-generalist | live | People at Brazilian institutions, for teaching and research. Free, merit-reviewed, continuous intake. | 248 H100, 36 GH200 nodes, 18 MI300A nodes. | [machine](https://sdumont.lncc.br/machine.php?pg=machine), [call](https://sdumont.lncc.br/call.php?pg=call) |
| PBIA national AI supercomputer | Brazil | direct-ai | building | Intended for companies, universities and government (press). | About 5,000 GPUs planned (press). | [LNCC](https://www.gov.br/lncc/pt-br/assuntos/noticias/ultimas-noticias-1/lncc-conduz-implantacao-de-supercomputador-de-inteligencia-artificial-que-ampliara-a-capacidade-computacional-do-brasil) |
| Clementina XXI and the IPAC calls | Argentina | direct-generalist | live, call closed | Free competitive calls for the national science system. | 83 projects in the latest round. | [IPAC](https://www.argentina.gob.ar/ciencia/sistemasnacionales/computacion-de-alto-desempeno/ipac) |
| Coatlicue | Mexico | direct-ai | announced | Science, government and startups, plus paid private-sector services. | 14,480 GPUs planned. | [SECIHTI](https://secihti.mx/sala-de-prensa/mexico-presenta-coatlicue-supercomputadora-mexicana-publica-mas-grande-de-america-latina/) |

Notes:
- Horizon's node count and the PBIA machine's plans come from press.
- Chile's CENIA cluster trained Latam-GPT but has no outside allocation, so it fails the litmus.
- El Capitan serves NNSA mission work and has no open call.

### Europe and the UK

| Program | Jurisdiction | Provision | Status | Who can apply, on what terms | Capacity and usage (published) | Source |
|---|---|---|---|---|---|---|
| EuroHPC AI Factories | EU | federated | live | Industry track: Playground (first come, first served, access within two working days), Fast Lane (up to 50k GPU-hours) and Large Scale. Free for AI SMEs and startups, paid for other industry. Science track: free for publicly funded research, with cut-offs every two months. | 19 factories and 13 antennas. EuroHPC takes 50% of time on its pre-exascale and exascale machines. No usage totals. | [access modes](https://www.eurohpc-ju.europa.eu/ai-factories/ai-factories-access-modes_en), [Playground](https://www.eurohpc-ju.europa.eu/playground-access-ai-factories_en) |
| EuroHPC AI Gigafactories | EU | hybrid | announced | Call open 2026-07-30 to 2026-11-12, for up to seven sites. Public money acts as anchor customer. Stated users: researchers, the public sector and businesses. | None yet. | [call](https://www.eurohpc-ju.europa.eu/eurohpc-joint-undertaking-launches-ai-gigafactories-call-2026-07-30_en) |
| UK AI Research Resource (Isambard-AI, Dawn) | UK | federated | live | UK academia, Companies House-registered firms, charities. Free compute through competitive routes, from Gateway (10k GPU-hours) to AI Open Access (up to 1.4M per project). No open-output rule on the call pages. | Isambard-AI: 5,448 GH200. No usage totals. | [AI Open Access](https://www.ukri.org/opportunity/airr-compute-opportunity-ai-open-access/), [Innovator route](https://www.ukri.org/opportunity/isambard-ai-and-dawn-airr-supercomputers-innovator-route/) |
| Jean Zay (GENCI, IDRIS) | France | direct-generalist | live | Free for open research. Dynamic Access gives up to 50k GPU-hours a year within days. Startups and SMEs are eligible. | 1,456 H100 plus 416 A100. Nearly 1,700 projects in 2025, about 5x oversubscribed. | [IDRIS](http://www.idris.fr/annonces/idris-extension-jean-zay-h100.html), [GENCI](https://www.genci.fr/actualites/2025-annee-charniere-pour-lia-au-service-de-la-science) |
| Alps and the Swiss AI Initiative (CSCS) | Switzerland | direct-ai | live | Swiss AI Initiative grants go to academic and public research organizations on rolling calls, with open-science commitments. | 10,752 GH200. | [CSCS](https://docs.cscs.ch/alps/hardware/), [Swiss AI](https://www.swiss-ai.org/) |
| Gefion (DCAI) | Denmark | hybrid | live | Public and private researchers in Denmark. Funded 85% by the Novo Nordisk Foundation and 15% by the state's EIFO. | Six pilot projects from more than 50 applicants. | [DCAI](https://dcai.dk/) |

Notes:
- The EuroHPC machines (JUPITER, LUMI, Leonardo, MareNostrum 5 and the Alice Recoque build) are facilities of the AI Factories and of their national hosts, not separate rows.
- JUPITER, for example, splits its time evenly between EuroHPC and the Gauss Centre for German researchers.

### Asia-Pacific and the Middle East

| Program | Jurisdiction | Provision | Status | Who can apply, on what terms | Capacity and usage (published) | Source |
|---|---|---|---|---|---|---|
| ABCI 3.0 (AIST) | Japan | direct-ai | live | Industry and academia. Paid, at 220 yen a point in FY2026 and 16 points an hour per eight-GPU node, which is about 440 yen a GPU-hour. | 6,128 H200. | [tariffs](https://abci.ai/en/how_to_use/tariffs.html), [arXiv 2411.09134](https://arxiv.org/abs/2411.09134) |
| GENIAC (METI, NEDO) | Japan | market-based | live | Subsidizes compute for foundation-model developers, mostly companies. | 16 projects in cycle 4. | [METI](https://www.meti.go.jp/english/press/2026/0604_001.html) |
| IndiaAI Mission compute | India | market-based | live | DPIIT-registered startups, MSMEs, academia, students and government bodies. Subsidy up to 40%, from 65 rupees a GPU-hour. | 38,231 GPUs onboarded, per a ministerial reply in the Lok Sabha. 190 approved projects. | [PIB](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2245069), [PIB projects](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2177598) |
| AIRAWAT and PARAM Siddhi-AI (C-DAC) | India | direct-ai | live | Academia, R&D institutes and startups, under a charging policy; startups get a free starter allocation. Some AIRAWAT GPUs were also offered through the IndiaAI empanelment. | The NSM page gives 656 A100 for PARAM Siddhi-AI; other C-DAC pages give different counts. | [C-DAC](https://cdac.in/index.aspx?id=hpc_nsf_siddhi-AI), [NSM](https://nsmindia.in/infrastructure/nsm-systems/param-siddhi-ai/) |
| Korea national GPU provision (MSIT, NIPA) | South Korea | market-based | live | Free for universities and public institutes. Private users pay 5 to 10% of market price. | First batch of about 4,000 GPUs for 159 projects (press). | [Korea Herald](https://www.koreaherald.com/article/10678398) |
| Korea National AI Computing Center | South Korea | direct-ai | building | Terms not published. | 15,000 GPUs planned by 2028 (press). | [Kyunghyang](https://www.khan.co.kr/en/article/202608031407017/) |
| NCHC (TWCC and the new system) | Taiwan | direct-ai | live | Time split among academia, government and industry. Startups get free GPU time through TAIWAN AI RAP. | Terms and usage unverified. | [NCHC](https://www.nchc.org.tw/Message/MessageView?id=3977&menutype=0&sitemenuid=8&mid=92) |
| NSCC ASPIRE 2A+ and 2B | Singapore | direct-ai | live | Through a research office at A*STAR, NUS, NTU, SUTD or SIT. Paid: S$0.98 an H100 card-hour at the public-research rate, higher for industry. | ASPIRE 2B: more than 1,500 H200. | [allocation policy](https://www.nscc.sg/srapolicy/) |
| NCMAS (NCI Gadi, Pawsey Setonix) | Australia | federated | live | Free, competitive annual merit calls for researchers. No dedicated AI or startup track. | 245 applications asking about 3x the pool. | [NCI](https://nci.org.au/news-events/news/record-demand-highlights-australias-growing-need-supercomputing-power) |
| National AI supercomputer (Israel Innovation Authority) | Israel | hybrid | live | 70% to companies, 30% to academia. Discounted below market, with minimum requests of 16 GPUs for industry and 8 for academia. | The equivalent of 1,000 B200 over several years. | [IIA](https://innovationisrael.org.il/en/press_release/supercomputer-access-2026/) |

Notes:
- The Korea rows, the IndiaAI figures and AIRAWAT's startup allocation come from press or search snippets, because the primary pages blocked fetching.
- Open Cloud Compute, the Indian network the Ada Lovelace report cites as decentralised provision, is left out. It is run by People+ai, part of the philanthropic EkStep Foundation, and no public funding or apply-here portal was found.
- Saudi Arabia's Shaheen III is framed for KAUST faculty, with no documented outside path, so it is left out.

### Africa

| Program | Jurisdiction | Provision | Status | Who can apply, on what terms | Capacity and usage (published) | Source |
|---|---|---|---|---|---|---|
| African Compute Initiative (UCT, IDIA) | South Africa, continental | direct-ai | building | University-affiliated African researchers, through a federated login. Funded through AI4D (FCDO and IDRC). | Target of 100 users in year one. | [UCT](https://ai.uct.ac.za/articles/2026-03-26-uct-lead-africas-first-higher-education-dedicated-ai-compute-initiative), [IDRC](https://idrc-crdi.ca/en/what-we-do/projects-we-support/project/africa-compute-initiative-expanding-african-access-compute) |
| CHPC (NICIS) | South Africa | direct-generalist | live, offline | Public and private users, including across SADC. Lengau has 30 V100 GPUs and was taken offline after a breach in May 2026. A replacement is due to start by the end of November 2026 (press). | 30 V100. | [CHPC](https://www.chpc.ac.za/) |

No publicly funded compute access program was found operating in Kenya, Nigeria or Rwanda.
Activity there is private data centers and draft national AI policies.

## What the inventory shows

- **Public AI compute is concentrated in a few jurisdictions.** Programs with an open queue for
  AI work are in the US, the EU, the UK, Switzerland, Japan, India, Korea, Taiwan, Singapore,
  Australia, Israel, Canada and Brazil.
  - Africa has one live program, and it is offline.
  - Latin America has two academic HPC machines, in Brazil and Argentina, and announcements
    elsewhere.
- **Startup and SME access is narrower still.**
  - Programs that name startups or SMEs and are open to them now: the EuroHPC AI Factories, the
    UK AIRR, Jean Zay, ABCI, the IndiaAI Mission, Korea's GPU provision, Israel's supercomputer and
    Canada's Access Fund (whose intake has closed). Redtail plans commercial access.
  - NAIRR admits a startup only when it holds a federal grant.
  - Empire AI, PAICE, the Alliance competition, SDumont and the Swiss AI Initiative are academic.
- **Much of the capacity is law or plans.**
  - CalCompute is a statute with no machine or appropriation.
  - The EU AI Gigafactories, Canada's SCIP, Brazil's PBIA machine, Mexico's Coatlicue, Korea's
    national center, Massachusetts and the African Compute Initiative are all funded or
    announced but not yet generally usable.
- **Open-output rules are rare.** NAIRR requires open and publishable results, and the Swiss AI
  Initiative and Jean Zay's open-research track require open science. The UK AIRR, the EuroHPC
  industry track and every market-based program publish no such rule, and Canada's fund is commercial
  by design.
- **Demand outruns supply where it is measured.**
  - Jean Zay is about 5x oversubscribed and NCMAS about 3x.
  - The Alliance's 2024 competition awarded 21% of the GPU-years requested.
  - INCITE requests exceeded 141M node-hours.
  - EuroHPC closed Fast Lane access to MareNostrum 5's GPU partition because of demand ([notice](https://www.eurohpc-ju.europa.eu/fast-lane-access-ai-factories-temporarily-closed_en)).
- **No program publishes evidence that its capacity sits unused.** That was the issue's
  hypothesis. The nearest thing is NAIRR's policy of reclaiming allocations that go unused in time
  ([policy](https://nairrpilot.org/allocation-management-policy)), which shows the program plans for
  slack but doesn't measure any. A widely quoted figure of under 20% utilization describes India's
  commercial GPU cloud market, not the IndiaAI program.

## What would make this a scored category

Reopen the question once adoption and outside-user capacity can be filled in for most rows. That
needs:

- a `program` product type, with its own openness ladder over access terms (eligibility breadth,
  cost, commercial use, open-output rule)
- one adoption unit, such as projects served in the latest published year, with a dated abstention
  where a program publishes none
- capacity counted as the accelerators or FLOPs allocated to outside users, not the machine's
  total, with market-based programs scored on the capacity they actually bought

Until then this inventory should be refreshed in a new dated brief rather than edited in place.

## Method and limits

Two research passes read operator and government pages first and press second. Figures without a
press note were read on the cited primary page. The gaps that remain:

- no aggregate usage for the EuroHPC AI Factories
- GENIAC's subsidy rate
- primary pages for the IndiaAI and Korea figures
- NCHC's access terms
- open-output rules for most programs

Sources on the policy framing:
- Sarosh Nagar and David Eaves, ["Building Public Compute for the Age of AI"](https://www.lawfaremedia.org/article/building-public-compute-for-the-age-of-ai), Lawfare, 2025-08-07.
- Matt Davies and Jai Vipra, [*Computing Commons: Designing public compute for people and society*](https://www.adalovelaceinstitute.org/report/computing-commons/), Ada Lovelace Institute, 2025-02-07. Epoch AI's data on AI data centers and Cleanview's
tracker are siting sources, not program sources, so no row here comes from them.
