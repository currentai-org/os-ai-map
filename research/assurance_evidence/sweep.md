# Assurance & compliance evidence (#93) + Responsible-AI measurement (#30) sweep — 2026-09-26

One sweep, two proposed categories, two verdicts. Every fact below carries an `F` id
(`fetch-log.tsv`, body under `raw/`) or a `W` id (`web-log.tsv`). All fetches were made on
2026-09-26 (UTC). Registry rows: `rows.assurance_evidence.yaml` and
`rows.responsible_ai_measurement.yaml`, both validated against `docs/schemas/registry.schema.json`
and deduped against `research/corpus-index.tsv` (no slug, GitHub or PyPI collision).

Legend for the 6a trust tag (issue #93, edited 2026-09-26): **SA** = self-attested (an auditor
reads it and takes it on trust), **IV** = independently verifiable (signature, attestation or
proof a third party can check without trusting the operator).

---

## 1. Verdict

### 6a `assurance_evidence` — **GO-WITH-CHANGES**

Supply is there: 23 accepted candidates from 23 independent organizations (no org above 4.3%),
21 of them open or source-available, and 13 carry a download instrument. Two findings the
proposer's list did not show: (1) a 2026 wave of EU AI Act "evidence pack" tools (Venturalitica,
AIR Blackbox, OpenComplAI, COMPL-AI, VerifyWise; Regula parked because its PyPI package has no files) that are small, young and mostly
single-vendor, and (2) the independently-verifiable tag holds 8 rows, and those split between
healthy signing/attestation infrastructure (model-signing 13.3K/mo, C2PA 1.15M crate downloads
in 90 days, nvtrust) and a thin, fragile zkML tail (EZKL has no license file; DeepProve's
"Apache-2.0" label hides a proprietary evaluation-only license). The changes: take C2PA
here (not in 6b), tag every row SA/IV, and treat the GRC suites (IBM watsonx.governance,
Credo AI) as the only closed comparators. One capability quantity does order the set:
how independently checkable the evidence is (§4).

### 6b `responsible_ai_measurement` — **PARK** as a single category (sub-areas can stand alone; see §9)

There's enough supply (23 accepted, 22 open, 19 orgs, 18 with a download instrument), but it
doesn't hang together. Carbon/energy (9), fairness (10) and watermarking (4, 5 if
`synthid-text` moves) measure three unrelated quantities: joules/kgCO2e, group-disparity
metrics, and watermark robustness/detectability. No single ladder orders a CodeCarbon against a
Fairlearn against a TrustMark. Fairness alone reaches 10 and, with adoption this strong
(Fairlearn 154K/mo, AIF360 30K/mo), would make a coherent category. Carbon/energy reaches 9, one
short. Watermarking is the weakest as a stand-alone, and it fits 6a's provenance leg better than it
fits carbon or fairness. So a gap statement *would* come out of attribute tooling. The fairness
field is mature but thinly maintained (AIF360's last PyPI release was 2024-04, the What-If Tool's
2021-10), and energy tooling is young. The seed rows are still written, so the maintainer can
act on whichever split is ruled.

---

## 2. Fit metrics (computed from §6)

### 6a `assurance_evidence`
- accepted candidates: **23** (open: 18, open-weights: 0, source-available: 3, closed: 2)
  - open: compliance-trestle, ai-verify, mlte, model-signing, croissant, nvtrust, c2pa-sdk,
    owasp-aibom-generator, compl-ai, validmind-library (AGPL-3.0 option), venturalitica,
    air-blackbox, opencomplai, halo-record,
    data-provenance-collection, aicert, zkml, verifyml
  - source-available: verifywise (BSL 1.1), ezkl (no license file), deepprove (Lagrange License)
  - closed: ibm-watsonx-governance, credo-ai
- trust tag: IV 8 (model-signing, nvtrust, c2pa-sdk, halo-record, ezkl, deepprove, aicert,
  zkml), SA 15
- independent organizations: **23**; largest org's share: **4.3%** (every org holds one row)
- candidates active in the last 12 months (last push on/after 2025-09-26): **17 of the 21**
  artifact-backed rows (inactive: data-provenance-collection 2025-03-26, aicert 2024-06-25, zkml
  2024-05-17, verifyml 2022-02-07; deepprove at 2025-10-01 counts as active). The 2 closed rows
  have no repo and aren't counted.
- candidates with a usage instrument: **13** (PyPI: compliance-trestle, mlte, model-signing,
  croissant, nvtrust, validmind-library, venturalitica, air-blackbox, opencomplai,
  halo-record, ezkl, verifyml; crates: c2pa-sdk)
- retrieval cutoff: declared before the long-tail verification pass. GitHub repos surfaced by
  search or awesome-lists with **fewer than 10 stars and no documented PyPI package drawing ≥100
  downloads/month** were not researched further. Five already-surfaced candidates fell under it
  and are parked (§7), not dropped: XDgov/model-card-generator (5), sai-platform (0), ModelRiskOps
  (1), eu-ai-act-toolkit (8), and Regula (4 stars; its `regula-ai` PyPI name has no
  distributions: pypi.org JSON 404 F0197, empty simple index F0222, README "PyPI distribution is
  currently unavailable" F0223, so the 384/mo mirror figure F0135 doesn't count). Venturalitica
  (6 stars, 648/mo) clears it through its package. Coverage limit: awesome-eu-ai-act (W0001, W0016) and the
  `ai-governance` / `iso-42001` GitHub topics (W0008) list more sub-10-star repos that this sweep
  didn't enumerate.

### 6b `responsible_ai_measurement`
- accepted candidates: **23** (open: 22, open-weights: 0, source-available: 1 (ml-energy-leaderboard, no
  license file), closed: 0)
  - per sub-area: carbon/energy **9**, fairness **10**, watermarking **4** (+1 if `synthid-text` moves
    from the safeguards tail, §3)
- independent organizations: **19**; largest org's share: **13.0%** (mlco2: codecarbon, ecologits,
  ml-co2-impact)
- active in the last 12 months: **21** (inactive: eco2ai 2025-03-10, invisible-watermark 2023-09-23;
  carbontracker pushed 2026-08-27 under its canonical name saintslab/carbontracker, F0220)
- usage instrument: **18** (all PyPI): codecarbon, zeus, carbontracker, ecologits, eco2ai, perun,
  fairlearn, aif360, aequitas, what-if-tool, fairness-indicators, holisticai, langfair,
  responsible-ai-toolbox, fairlens, invisible-watermark, trustmark, markllm
- retrieval cutoff: the same rule as 6a. No 6b candidate fell under it. Closed comparators: none
  accepted. The sweep found no best-in-class closed carbon or fairness *product* to mark a
  frontier, which is itself a finding (the closed fairness capability sits inside the GRC suites in 6a).

---

## 3. Boundary

### 6a `assurance_evidence`
- **Definition:** tools whose main output is machine-readable evidence about an AI system,
  model or dataset, produced for a party outside the operating team (auditor, regulator,
  acquirer, downstream deployer).
- **Litmus:** is the main artifact evidence that a third party consumes? (Yes → here.)
- **Tie-breaker (issue #93):** when one artifact is both a control and its evidence, classify by what
  reaches the outside party. Tag each row SA or IV.
- **Exclusions:**
  - runtime policy enforcement, guardrails and red-teaming → `safeguards`
  - capability or quality benchmarking for builders → `evaluation_code` / `benchmark_eval_data`
  - operator-facing traces and metrics → `telemetry_observability`
  - general (non-AI) software supply chain: in-toto, cdxgen, SPDX tooling → out of scope (parked)
  - confidential-compute *runtimes* whose main product is a deployment surface → `deployment`
    (dstack parked; attestation *verifiers* like nvtrust stay here)
  - footprint, fairness and watermark *measurement* → 6b (or its successor categories)
  - model hosting and model-card *hosting* → `model_hubs` (sibling sweep) and `huggingface-hub`
- **Contested products:**

| product | where it is now | recommendation | reason |
|---|---|---|---|
| agent-governance-toolkit (microsoft) | `safeguards` tail | **stay** | It enforces runtime policy on agents first. Its compliance mappings are secondary (W0001). Its receipts could make it a 6a cross-reference. |
| synthid-text (google) | `safeguards` tail | **move to 6b (watermarking)**, or to 6a if watermarking folds there | A watermark embedder/detector doesn't filter unsafe I/O. It quantifies provenance (F0053, F0171). |
| huggingface-hub ModelCard API | `ml_frameworks` head (`huggingface-hub`) | **stay** | Model-card tooling is one module of the Hub client (F0188). It's not a separate product. |
| compl-ai | absent | **here (flag vs `evaluation_code`)** | Its benchmarks are mapped to EU AI Act articles for a compliance report (F0167, W0016). What reaches the outside party is the conformity reading, not the score. |
| ai-verify | absent | **here (flag vs `evaluation_code`)** | It's a governance testing framework that produces structured reports for stakeholders (F0160). Moonshot (its LLM red-team sibling) would be `safeguards`. |
| validmind-library | absent | **here** | It automates model documentation for model-risk validators (W0012). It's the open library for a closed platform. |
| dstack | absent | **other → `deployment`** (flag) | It's a confidential-VM deployment framework. Attestation is a feature of the runtime (F0162). Needs a ruling (Q5). |
| c2pa-sdk | absent | **here (not 6b)** | Signed manifests are cryptographic provenance a third party verifies (W0009): IV evidence, not a measurement. |
| halo-record | absent | **here (flag vs `telemetry_observability`)** | Its hash-chained records are built to be verified by the customer, not the operator (W0019, F0177). |
| croissant | absent | **here** (ruled 2026-09-25) | Machine-readable dataset documentation (F0158). Flag the `model_hubs` sibling: hubs *serve* Croissant, and this row is the format + library. |
| content-seal, audioseal (meta) | absent | **6b**; flag the `speech_audio` / `media_generation` siblings | Watermarking of generated media, not generation or ASR/TTS. |
| fairlearn, aif360 etc. | absent | **6b**; flag the `classic_ml_cv` sibling | They are scikit-learn-adjacent libraries, but their reason for fame is fairness measurement. |

### 6b `responsible_ai_measurement`
- **Definition:** tools that quantify a responsibility attribute of an AI system: energy/carbon
  footprint, group fairness/bias, or watermark embedding/detection.
- **Litmus:** does it *measure* a footprint or responsibility property (as opposed to filtering
  I/O, which is `safeguards`, or documenting for a third party, which is 6a)?
- **Exclusions:** general datacenter/host energy metrology (Kepler, Scaphandre) → out of scope
  (not AI-specific; parked). Fairness *benchmarks/datasets* (BBQ etc.) → `benchmark_eval_data`.
  C2PA → 6a. Energy leaderboards: kept here (AI Energy Score, ML.ENERGY), with a flag against
  `evaluation_code`.
- **Seam ruling proposed:** C2PA → 6a (a signed manifest is evidence), watermarking → 6b (a
  statistical signal whose robustness is measured). If 6b is parked, watermarking should go to 6a
  with C2PA, since both answer "where did this content come from" for an outside party.

---

## 4. Capability quantity

### 6a: **how independently checkable the evidence is**
1. **Template/checklist** a human fills in (ISO-42001 toolkits: parked, W0008)
2. **Generated structured documentation**, self-attested (verifyml, validmind-library, mlte, ai-verify)
3. **Standard-schema, machine-validated evidence** mapped to a control framework (compliance-trestle
   OSCAL, croissant, owasp-aibom-generator CycloneDX, venturalitica)
4. **Cryptographically signed / tamper-evident** evidence checkable offline (model-signing,
   c2pa-sdk, halo-record)
5. **Hardware- or proof-backed verification** of execution itself (nvtrust GPU attestation;
   ezkl / deepprove / zkml zero-knowledge proofs of inference). The **top-rung anchors are nvtrust**
   for production maturity (F0006, F0103) and **deepprove** for scope, claiming full LLM inference
   proofs (W0003), though it is source-available.

This lines up with the SA/IV tag: rungs 1–3 are SA and rungs 4–5 are IV.

### 6b: **no single quantity**
- carbon/energy: measurement fidelity (static estimate → hardware counters → per-request attribution; Zeus/perun at top)
- fairness: breadth of metrics × mitigation (metrics-only → metrics + mitigation → LLM use-case bias; Fairlearn/AIF360 at top)
- watermarking: modality coverage × robustness (single-modality image → multi-modality suite; Content Seal at top)

This is the finding: the three sub-areas don't share a ladder.

---

## 5. Scoring ladder inputs

- **Product types:** every accepted row in both files is `software`, so both need the shared
  `software` ladder. Content Seal and the MarkLLM/SynthID lines ship model weights (for example
  `facebook/audioseal` on HF, F0154), so a `{model: model, software: software}` map would be
  needed only if watermark *models* get their own rows. This sweep collapsed them into the suite
  (§6).
- **License strings met.** Where a LICENSE file or README license section was read, its F id is cited. Rows citing only an ecosyste.ms body (F00xx repo records) rest on the GitHub license *label*, which the auditor spot-checked against LICENSE text for six rows (audit.md). A maintainer should read the text before promotion.

| license | products | note |
|---|---|---|
| Apache-2.0 | compliance-trestle, ai-verify, model-signing, croissant, nvtrust (nv-attestation-sdk), owasp-aibom-generator (label `other`, text Apache F0068), compl-ai, venturalitica, air-blackbox, halo-record, data-provenance-collection, aicert, zkml, verifyml, zeus, eco2ai, aif360, what-if-tool, fairness-indicators, holisticai, markllm, synthid-text, in-toto (label `other`, text Apache F0067) | holisticai and markllm: the PyPI metadata says MIT, but the repo LICENSE text is Apache-2.0 (F0122 vs F0185, F0132 vs F0186) |
| MIT | mlte, codecarbon, carbontracker, ml-co2-impact, ai-energy-score, fairlearn, aequitas, responsible-ai-toolbox, content-seal, invisible-watermark, trustmark (Adobe notice + MIT, F0090) | |
| MIT OR Apache-2.0 | c2pa-sdk (LICENSE-MIT F0092 + LICENSE-APACHE F0091; GitHub label `other`) | a dual license, both OSI |
| BSD-3-Clause | perun, fairlens, nv-local-gpu-verifier (nvtrust component, F0104) | nvtrust ships two licenses across its packages |
| BSD-2-Clause | lift | |
| MPL-2.0 | ecologits | weak copyleft |
| Apache-2.0 + MIT components | langfair (F0089) | GitHub label `other` |
| AGPL-3.0 OR ValidMind Commercial | validmind-library (F0073) | **unusual**: a dual license with a commercial option. The AGPL leg is OSI. |
| AGPL-3.0-only | opencomplai (F0027, F0137) | |
| (Apache-2.0 OR EUPL-1.2) AND LicenseRef-DRL-1.1 | regula (parked; F0135; LICENSE file 404, F0183) | **custom**: the DRL-1.1 component is unidentified and needs a maintainer read |
| BSL 1.1 (internal use only; changes to Apache-2.0) | verifywise (F0075) | **source-available** |
| Lagrange License (proprietary, evaluation/Platform use only) | deepprove (F0172, F0164) | **custom, and the label is wrong**: ecosyste.ms reports `apache-2.0` (F0021) |
| none (no LICENSE file; CLA only) | ezkl (F0063–F0066 404; Cargo.toml no license field F0093; README CLA F0094) | **no grant**. The issue's "hold" still applies. |
| none (no LICENSE file) | ml-energy-leaderboard (F0080–F0083 404) | |
| CC-BY-NC-4.0 | stable_signature (Content Seal member, F0088) | non-commercial member inside an MIT suite |
| CC0-1.0 / US public domain | XDgov model-card-generator (F0077, parked) | |
| proprietary SaaS | ibm-watsonx-governance, credo-ai | closed |

---

## 6. Accepted candidates

### 6a. Registry rows

The paste-ready files are `rows.assurance_evidence.yaml` (23 rows) and
`rows.responsible_ai_measurement.yaml` (23 rows). Package declarations follow the package trap
rule. Each declared PyPI/crates package either has `repository_url` equal to the declared repo
(ecosyste.ms) or is named as the install path in the README or project_urls cited in §6b. Packages
that couldn't be tied to the product that way were left off the row: aiverify-test-engine
(F0099: no repository link, not in the README), videoseal (F0129, whose README installs from
requirements, F0161), and dstack-sdk (parked row).

### 6b. Evidence tables

Stars and pushes come from ecosyste.ms, downloads are PyPI last-month from packages.ecosyste.ms
unless noted, and "last release" means the latest release on the registry.

#### Assurance & compliance evidence

| slug | open status / tag | license(s) + source | archived/fork | last push | last release | adoption signal | members | org handle | notes |
|---|---|---|---|---|---|---|---|---|---|
| compliance-trestle | open / SA | Apache-2.0 (F0001, README F0174) | no/no (F0001) | 2026-09-24 (F0001) | 5.1.0, 2026-09-02 (F0098) | PyPI 63,201/mo (F0098); 278★ | — | oscal-compass | OSCAL compliance-as-code |
| ai-verify | open / SA | Apache-2.0 (F0002, README F0160) | no/no (F0002) | 2026-03-23 (F0002) | aiverify-test-engine 2.2.1, 2026-03-20 (F0099) | 96★ (F0002); package 819/mo not declared (not the documented path) | aiverify-test-engine | aiverify-foundation | Moonshot sibling not swept |
| mlte | open / SA | MIT (F0003) | no/no (F0003) | 2026-08-11 (F0003) | 2.7.0, 2026-08-21 (F0190) | PyPI 392/mo (F0100); 20★ | — | mlte-team | `pip install mlte` (F0166) |
| model-signing | open / IV | Apache-2.0 (F0004) | no/no (F0004) | 2026-09-17 (F0004) | 1.1.1, 2025-10-10 (F0101) | PyPI 13,307/mo (F0101); 244★ | CLI + library; OMS format | sigstore | v1.0 April 2025; NGC signs all NVIDIA models with OMS (W0010); `pip install model-signing` (F0165) |
| croissant | open / SA | Apache-2.0 (F0005) | no/no (F0005) | 2026-07-15 (F0005) | mlcroissant 1.1.0, 2026-04-16 (F0102) | PyPI 33,784/mo (F0102); 883★ | format spec + `mlcroissant` | mlcommons | install path `pip install mlcroissant` (F0158) |
| nvtrust | open / IV | Apache-2.0 (F0006, F0159); nv-local-gpu-verifier BSD-3-Clause (F0104) | no/no (F0006) | 2026-09-01 (F0006) | nv-attestation-sdk 2.7.3, 2026-05-04 (F0103) | PyPI 6,341/mo (F0103); 323★ | nv-attestation-sdk, nv-local-gpu-verifier (2,861/mo F0104) | NVIDIA | the README names the PyPI SDK (F0159) |
| c2pa-sdk | open / IV | MIT OR Apache-2.0 (F0091, F0092; label `other` F0013) | no/no (F0013) | 2026-09-24 (F0013) | crate c2pa 0.91.0, updated 2026-09-21 (F0153) | crates recent (90-day) 1,150,875; total 10,397,885 (F0153); c2pa-python 171,819/mo (F0108); 424★ | c2pa-rs, c2pa-python (F0014), c2patool (F0015), c2pa-js (W0009) | contentauth | official SDKs are c2pa-rs, c2pa-js, c2pa-python (W0009) |
| owasp-aibom-generator | open / SA | Apache-2.0 text (F0068; label `other` F0011) | no/no (F0011) | 2026-09-02 (F0011) | none on a registry | 100★ (F0011) | — | GenAI-Security-Project | installs from requirements.txt, so no package (F0168); CycloneDX output (W0002) |
| compl-ai | open / SA | Apache-2.0 (F0017, F0167) | no/no (F0017) | 2026-09-18 (F0017) | no PyPI package (F0138 404) | 211★ | — | compl-ai | ETH Zurich, INSAIT, LatticeFlow (W0016) |
| validmind-library | open (AGPL option) / SA | AGPL-3.0 OR ValidMind Commercial (F0073) | no/no (F0018) | 2026-09-14 (F0018) | 2.13.14, 2026-09-03 (F0110) | PyPI 1,370/mo (F0110); 9★ | — | validmind | feeds a closed platform (W0012) |
| verifywise | source-available / SA | BSL 1.1, internal-use grant, changes to Apache-2.0 (F0075) | no/no (F0019) | 2026-09-25 (F0019) | — | 358★ (F0019) | — | verifywise-ai | licensor BlueWave Labs (F0075) |
| venturalitica | open / SA | Apache-2.0 (F0016, F0109) | no/no (F0016) | 2026-08-27 (F0016) | 0.8.2, 2026-08-27 (F0109) | PyPI 648/mo (F0109); 6★ | — | Venturalitica | OSCAL + CycloneDX ML-BOM + Annex IV output (W0016) |
| air-blackbox | open / SA | Apache-2.0 (F0151, F0136) | no/no (F0151) | 2026-09-13 (F0151) | 1.16.0, 2026-09-26 (F0196) | PyPI 431/mo (F0136); 22★ (F0151) | — | airblackbox | |
| opencomplai | open / SA | AGPL-3.0-only (F0027, F0147) | no/no (F0027) | 2026-09-23 (F0027) | 0.8.0, 2026-09-24 (F0198) | PyPI 113/mo (F0137); 17★ | — | Opencomplai | homepage opencomplai.com via project_urls (F0147) |
| halo-record | open / IV | Apache-2.0 (F0177, F0179) | no/no (F0177) | 2026-09-15 (F0177) | 0.2.45, 2026-09-14 (F0199) | PyPI 1,103/mo (F0179); 80★ | halo-record-ts (F0221) | bkuan001 | created 2026-06-11 (F0177) |
| ezkl | source-available / IV | **none**: no LICENSE (F0063–F0066), no Cargo license field (F0093), CLA only (F0094) | no/no (F0007) | 2026-02-20 (F0007) | 23.0.5, 2026-02-20 (F0200) | PyPI 3,013/mo (F0105); 1,222★ | — | zkonduit | the issue's "hold" still applies |
| deepprove | source-available / IV | Lagrange License, proprietary, test/evaluation use (F0172, F0164) | no/no (F0021) | 2025-10-01 (F0021) | — | 3,359★ (F0021) | — | Lagrange-Labs | ecosyste.ms label `apache-2.0` is **wrong** |
| data-provenance-collection | open / SA | Apache-2.0 (F0024) | no/no (F0024) | 2025-03-26 (F0024) | — | 282★ | — | Data-Provenance-Initiative | dormant 18 months |
| aicert | open / IV | Apache-2.0 (F0025) | no/no (F0025) | 2024-06-25 (F0025) | — | 20★ | — | mithril-security | dormant |
| zkml | open / IV | Apache-2.0 (F0022) | no/no (F0022) | 2024-05-17 (F0022) | — | 379★ | — | ddkang | dormant; TensorFlow→Halo2 compiler (W0003) |
| verifyml | open / SA | Apache-2.0 (F0009) | no/no (F0009) | 2022-02-07 (F0009) | 0.0.6, 2022-02-07 (F0107) | PyPI 38/mo (F0107); 23★ | — | cylynx | the churn evidence #93 cites |
| ibm-watsonx-governance | closed / SA | proprietary SaaS; no license offered (F0156) | — | — | — | Gartner MQ 2026 Leader (W0014) | — | ibm | "compliance evidence capture" (F0156) |
| credo-ai | closed / SA | proprietary SaaS; no license offered (F0157) | — | — | — | Forrester Wave Leader Q3 2025; Gartner Visionary (W0014) | — | credo-ai | "audit-ready evidence" (F0157) |

#### Responsible-AI measurement

| slug | sub-area / status | license(s) + source | archived/fork | last push | last release | adoption signal | members | org handle | notes |
|---|---|---|---|---|---|---|---|---|---|
| codecarbon | carbon / open | MIT (F0031) | no/no (F0031) | 2026-09-19 (F0031) | 3.3.1, 2026-09-09 (F0111) | PyPI 142,686/mo (F0111); 1,920★ | — | mlco2 | |
| zeus | energy / open | Apache-2.0 (F0032, F0149) | no/no (F0032) | 2026-09-21 (F0032) | 0.16.0, 2026-07-07 (F0112) | PyPI 6,166/mo (F0112); 374★ | old package `zeus-ml` 332/mo (F0113) | ml-energy | |
| carbontracker | carbon / open | MIT (F0220, F0096) | no/no (F0220) | 2026-08-27 (F0220) | 2.4.7, 2026-08-27 (F0204) | PyPI 1,203/mo (F0096); 483★ (F0220) | — | saintslab | canonical repo is saintslab/carbontracker; PyPI still points at lfwa/carbontracker, and ecosyste.ms 404s the old name (F0096, F0033) |
| ecologits | carbon / open | MPL-2.0 (F0175, F0097) | no/no (F0175) | 2026-09-22 (F0175) | 0.11.1, 2026-07-07 (F0097) | PyPI 8,322/mo (F0097); 335★ | — | mlco2 | moved from genai-impact (W0017; F0037 404) |
| eco2ai | carbon / open | Apache-2.0 (F0038) | no/no (F0038) | 2025-03-10 (F0038) | 0.3.12, 2025-03-10 (F0115) | PyPI 138/mo (F0115); 280★ | — | sb-ai-lab | dormant |
| perun | energy / open | BSD-3-Clause (F0040) | no/no (F0040) | 2026-09-24 (F0040) | 1.0.0, 2026-08-31 (F0116) | PyPI 4,264/mo (F0116); 94★ | — | Helmholtz-AI-Energy | |
| ml-co2-impact | carbon / open | MIT (F0035) | no/no (F0035) | 2026-04-13 (F0035) | — | 270★ (F0035) | web calculator (F0184) | mlco2 | |
| ai-energy-score | energy / open | MIT (F0036) | no/no (F0036) | 2025-12-02 (F0036) | — | 42★; 1–5 star rating on H100 (W0015) | leaderboard Space | huggingface | flag vs `evaluation_code` |
| ml-energy-leaderboard | energy / source-available | none (F0080–F0083 404; F0039 null) | no/no (F0039) | 2026-05-07 (F0039) | — | 13★ | — | ml-energy | sibling of zeus (W0015) |
| fairlearn | fairness / open | MIT (F0043, F0187) | no/no (F0043) | 2026-09-21 (F0043) | 0.14.0, 2026-06-07 (F0117) | PyPI 154,164/mo (F0117); 2,287★ | — | fairlearn | |
| aif360 | fairness / open | Apache-2.0 (F0044) | no/no (F0044) | 2026-06-15 (F0044) | 0.6.1, 2024-04-08 (F0118) | PyPI 30,259/mo (F0118); 2,866★ | — | Trusted-AI | no release in 29 months |
| aequitas | fairness / open | MIT (F0045) | no/no (F0045) | 2026-05-12 (F0045) | 1.1.0, 2026-02-03 (F0119) | PyPI 17,542/mo (F0119); 774★ | — | dssg | |
| what-if-tool | fairness / open | Apache-2.0 (F0046) | no/no (F0046) | 2026-09-21 (F0046) | witwidget 1.8.1, 2021-10-12 (F0120) | PyPI 21,055/mo (F0120); 1,018★ | — | PAIR-code | `pip install witwidget` (F0170) |
| fairness-indicators | fairness / open | Apache-2.0 (F0047) | no/no (F0047) | 2026-07-10 (F0047) | 0.52.0, 2026-07-10 (F0121) | PyPI 1,311/mo (F0121); 358★ | — | tensorflow | |
| holisticai | fairness / open | Apache-2.0 text (F0185); PyPI says MIT (F0122) | no/no (F0048) | 2026-07-31 (F0048) | 1.0.14, 2025-03-03 (F0122) | PyPI 2,404/mo (F0122); 113★ | — | holistic-ai | open library of a closed-platform vendor (W0006, W0014) |
| langfair | fairness / open | Apache-2.0 + MIT components (F0089) | no/no (F0049) | 2026-09-11 (F0049) | 0.8.0, 2026-01-09 (F0214) | PyPI 505/mo (F0123); 262★ | — | cvs-health | LLM use-case bias (W0006) |
| responsible-ai-toolbox | fairness / open | MIT (F0050, F0169) | no/no (F0050) | 2026-09-10 (F0050) | 0.36.0, 2024-07-08 (F0124) | PyPI raiwidgets 4,052/mo (F0124); responsibleai 7,881/mo (F0125); 1,834★ | raiwidgets, responsibleai | microsoft | the README documents `pip install raiwidgets` (F0169); multi-attribute (fairness, error analysis) |
| lift | fairness / open | BSD-2-Clause (F0051) | no/no (F0051) | 2025-12-19 (F0051) | — | 173★ | — | linkedin | Scala/Spark |
| fairlens | fairness / open | BSD-3-Clause (F0052) | no/no (F0052) | 2026-08-17 (F0052) | 0.1.0, 2021-08-12 (F0126) | PyPI 34/mo (F0126); 94★ | — | synthesized-io | |
| content-seal | watermark / open | MIT (F0176, F0180); member Stable Signature CC-BY-NC-4.0 (F0088) | no/no (F0176) | 2026-07-08 (F0176) | — | 243★; member audioseal PyPI 127,614/mo (F0128), HF `facebook/audioseal` 46,580 (F0154) | AudioSeal (F0054), Video Seal (F0055, F0129, F0155), Watermark Anything (F0057), Stable Signature (F0056), Pixel Seal, TextSeal (F0180) | facebookresearch | Meta markets one suite (Meta Seal, now Content Seal; W0005, W0018, F0180) |
| invisible-watermark | watermark / open | MIT (F0058) | no/no (F0058) | 2023-09-23 (F0058) | 0.2.0, 2023-07-06 (F0130) | PyPI 120,631/mo (F0130); 1,982★ | — | ShieldMnt | dormant, high downloads (a dependency pull, not a new signal) |
| trustmark | watermark / open | MIT with Adobe notice (F0090) | no/no (F0059) | 2026-09-08 (F0059) | 0.9.2, 2026-09-08 (F0131) | PyPI 26,879/mo (F0131); 144★ | — | adobe | |
| markllm | watermark / open | Apache-2.0 text (F0186); PyPI says MIT (F0132) | no/no (F0060) | 2026-09-05 (F0060) | 0.1.5, 2024-10-21 (F0219) | PyPI 134/mo (F0132); 1,076★ | — | THU-BPM | text-watermark toolkit (W0005) |

### 6c. Source list

Every URL is in `fetch-log.tsv` (F0001–F0223: URL, UTC timestamp, HTTP code, sha256) and
`web-log.tsv` (W0001–W0020: query/URL, timestamp, excerpt). All were fetched 2026-09-26. Key
families: ecosyste.ms repo API (F0001–F0060, F0095, F0150–F0152, F0175–F0178, F0181–F0182),
packages.ecosyste.ms PyPI (F0096–F0139, F0179), pypi.org JSON (F0140–F0149),
raw.githubusercontent.com LICENSE/README (F0063–F0094, F0158–F0174, F0180, F0183, F0185–F0187),
crates.io (F0153), Hugging Face API (F0154–F0155), vendor pages (F0156, F0157, F0184, F0188), post-audit pypi.org JSON re-checks (F0189–F0219), and post-audit fetches (F0220–F0223).

---

## 7. Parked candidates

All sources were fetched 2026-09-26.

| # | name | reason | source |
|---|---|---|---|
| 1 | tensorflow/model-card-toolkit | unmaintained: archived, last push 2023-07-26, 453★ (evidence of churn, as #93 says) | F0008 |
| 2 | in-toto | boundary → out of scope: a general software supply-chain framework, not AI-specific (model-signing uses in-toto statements) | F0010, F0067 |
| 3 | cdxgen | boundary → out of scope: a general SBOM generator. ML-BOM is one feature (W0002). | F0012 |
| 4 | dstack (Dstack-TEE) | boundary → `deployment`: a confidential-VM runtime. Attestation is a feature (Q5). | F0020, F0162, W0007 |
| 5 | XDgov/model-card-generator | below retrieval cutoff (5★, no package); CC0 | F0026, F0077 |
| 6 | giselleevita/sai-platform | below retrieval cutoff (0★) | F0029, F0079 |
| 7 | bilgekayali/ModelRiskOps | below retrieval cutoff (1★) | F0030, F0078 |
| 8 | AbdelStark/eu-ai-act-toolkit | below retrieval cutoff (8★; package not checked) | F0028 |
| 9 | ark-forge/mcp-eu-ai-act | boundary → builder-facing code scanner. It claims no third-party artifact. | F0181, W0001 |
| 10 | Ankit-Uniyal/iso-42001-ai-governance-toolkit | identity unclear: document templates, not a tool | W0008 |
| 11 | suchan99/iso-42001-ai-management-system-framework | identity unclear: document templates, not a tool | W0008 |
| 12 | Proof-of-Control v1.0 | a standard (working draft, final targeted 2027-02-01), so track it and don't list it | F0178, W0020 |
| 13 | Holistic AI Governance Platform | closed long-tail (Gartner Challenger). Its open library is in 6b. | W0014 |
| 14 | OneTrust AI Governance | closed long-tail | W0014 |
| 15 | ServiceNow AI Control Tower | closed long-tail | W0014 |
| 16 | Collibra AI governance | closed long-tail | W0014 |
| 17 | Modulos | closed long-tail | W0014 |
| 18 | VeriTrace | identity unclear: no repo located in this run | W0011 |
| 19 | Attested Intelligence MCP proxy | identity unclear: no repo located | W0011 |
| 20 | chutesai/sek8s | not verified in this run (boundary likely `deployment`) | W0007 |
| 21 | Tinfoil | not verified in this run | W0007 |
| 22 | voltage-verify | not verified in this run | W0007 |
| 23 | venice-e2ee-proxy | not verified in this run | W0007 |
| 24 | encypherai/encypher-c2pa | not verified in this run. It's a verification-only C2PA SDK, so check it against c2pa-sdk. | W0009 |
| 25 | zkComposer | no addressable artifact (paper) | W0003 |
| 26 | RISC Zero SmartCore ML | not verified in this run | W0003 |
| 27 | Breakend/experiment-impact-tracker | unmaintained: archived, last push 2024-01-30; last PyPI release 2020-01-31 | F0034, F0114 |
| 28 | Kepler (sustainable-computing-io) | boundary → out of scope: Kubernetes power exporter, not AI-specific | F0041 |
| 29 | Scaphandre | boundary → out of scope: general energy metrology agent | F0042 |
| 30 | AudioSeal | SKU of content-seal | F0054, F0128, F0154, F0180 |
| 31 | Video Seal | SKU of content-seal | F0055, F0129, F0155, F0161 |
| 32 | Stable Signature | SKU of content-seal (CC-BY-NC member) | F0056, F0088 |
| 33 | Watermark Anything | SKU of content-seal | F0057, F0180 |
| 34 | c2pa-python | SKU of c2pa-sdk (a binding of c2pa-rs) | F0014, F0108 |
| 35 | c2patool | SKU of c2pa-sdk (CLI) | F0015 |
| 36 | nv-local-gpu-verifier | SKU of nvtrust | F0104 |
| 37 | GreenBench | no addressable artifact verified (paper) | W0004 |
| 38 | LLMCO2 | no addressable artifact verified (paper) | W0004 |
| 39 | DelorneN007/fairness_pipeline_dev_toolkit | not verified in this run | W0006 |
| 40 | halo-record-ts | SKU of halo-record | F0221 |
| 41 | DocML | no addressable artifact located | W0013 |
| 42 | CardGen | no addressable artifact (paper, arXiv 2405.06258) | W0013 |
| 43 | ZeroPath AI-BOM | closed long-tail | W0002 |
| 44 | Regula (kuzivaai/getregula) | below retrieval cutoff (4★; `regula-ai` has no PyPI distribution: F0197 404, F0222 empty index, F0223 README) | F0150, F0182, F0135 |

"Not verified in this run" means only a search mention exists. These are follow-ups, not
rejections.

---

## 8. Reconciled counts

Duplicate signals (9): agent-governance-toolkit (index, safeguards tail), synthid-text (index,
safeguards tail), HF model-card tooling (index `huggingface-hub`), zeus-ml (self: zeus),
aiverify-test-engine (self: ai-verify), genai-impact/ecologits (self: mlco2/ecologits), "OpenSSF
Model Signing v1.0" (self: model-signing), "Meta Seal" (self: content-seal), responsibleai
package (self: responsible-ai-toolbox).

```
raw_signals       = duplicate_signals + unique_candidates  →  99 = 9 + 90
unique_candidates = accepted + parked                      →  90 = 46 + 44
accepted = 23 (assurance_evidence) + 23 (responsible_ai_measurement)
```

**Found by a logged search, not named in either brief** (accepted): ValidMind Library (W0012),
Venturalitica, COMPL-AI, OpenComplAI (W0016), AIR Blackbox (W0001), Halo Record (W0011, W0019),
DeepProve, ZKML (W0003), OWASP AIBOM Generator (W0002), IBM watsonx.governance (W0014),
EcoLogits (W0004), ML.ENERGY Leaderboard (W0015), Holistic AI Library, LangFair, FairLens
(W0006), Content Seal, MarkLLM (W0005, W0018). Parked ones surfaced the same way are cited in §7.

**Not named in the briefs and added from the sweeper's own lead list, with no discovery search
logged** (every fact about them is still fetched): VerifyWise, AICert, Data Provenance Collection,
eco2AI, perun, Responsible AI Toolbox, LiFT.

---

## 9. Open questions for the maintainer

1. **Create `assurance_evidence` with the SA/IV tag as a documented row attribute (in prose, since
   the registry has no field)?** Recommend **yes**.
2. **C2PA: 6a or 6b?** Options: (a) 6a, (b) 6b. Recommend **(a)**: a signed manifest is evidence a
   third party verifies. It's not a measurement.
3. **6b's shape.** Options: (a) one `responsible_ai_measurement` category with a per-sub-area note;
   (b) park 6b and create `fairness_bias` (10 rows) alone; (c) (b) plus watermarking into 6a
   as a provenance leg, with carbon/energy parked at 9 rows until it clears 10; (d) close #30 as
   out of scope. Recommend **(c)**. It gives each quantity its own ladder, and
   carbon is one row short, not zero.
4. **Move `synthid-text` from the `safeguards` tail** into whichever category owns watermarking?
   Recommend **yes**.
5. **dstack (confidential runtime with attestation): `deployment` or 6a?** Recommend **`deployment`**,
   with nvtrust (the verifier) in 6a. That keeps the tie-breaker about the artifact, not the stack.
6. **EZKL (no license grant) and DeepProve (proprietary evaluation license): list as
   source-available IV rows, or hold?** Recommend **list**. The IV tag's thinness is the #93 finding,
   and both licenses are recorded here.
7. **Content Seal: one suite row, or split AudioSeal / Video Seal?** Recommend **one row**, because
   Meta markets one suite (F0180). Note that the row then declares no package: AudioSeal's
   127K/mo belongs to a member, and declaring it would assert the suite's numbers. The
   alternative is to split by modality and declare `audioseal` on its own row.
8. **Regula (parked): revisit once `regula-ai` ships a distribution?** Recommend **yes**, and read
   its `LicenseRef-DRL-1.1` component then. The LICENSE file wasn't at the repo root (F0183).
9. **compl-ai and ai-verify vs `evaluation_code`.** Recommend **6a** under the tie-breaker (their
   deliverable is a conformity report). Say no if the map would rather keep all benchmark runners together.
