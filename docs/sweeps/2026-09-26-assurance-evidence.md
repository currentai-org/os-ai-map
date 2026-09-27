# Assurance & compliance evidence seed: 2026-09-26

## Scope and boundary

This seed creates the preliminary `assurance_evidence` category proposed in issue #93. It came out
of one sweep that researched two proposals together: #93 (assurance evidence, called 6a below) and
#30 (responsible-AI measurement, 6b). 6a is created. 6b is **parked**, and its watermarking rows come
here; its fairness and carbon rows are recorded at the end of this file so #30 can pick them up.

The raw evidence trail is on the branch `claude/research-assurance_evidence`, under
`research/assurance_evidence/`: `sweep.md` (the full sweep), `fetch-log.tsv` (every `F` id: URL,
UTC timestamp, HTTP status, sha256, with bodies under `raw/`), `web-log.tsv` (every `W` id: query or
URL, timestamp, excerpt) and `audit.md` (a two-pass independent audit whose corrections are applied
here). Every fact below was fetched on 2026-09-26 and carries its id.

**Definition.** Tools whose main output is machine-readable evidence about an AI system, model,
dataset or generated content, produced for a party outside the operating team: an auditor, a
regulator, an acquirer or a downstream deployer.

**Litmus.** Is the main artifact evidence that a third party consumes? Yes means here.

**Tie-breaker (from #93).** When one artifact is both a control and its evidence, classify by what
reaches the outside party.

**Exclusions, one per neighbor:**

- `safeguards`: runtime policy enforcement, guardrails and red-teaming. agent-governance-toolkit
  stays there, because it enforces agent policy first (W0001).
- `evaluation_code` / `benchmark_eval_data`: capability or quality benchmarking for builders.
- `telemetry_observability`: operator-facing traces and metrics.
- `deployment`: confidential-compute runtimes whose main product is a deployment surface. dstack goes
  there as a follow-up (F0162); attestation verifiers such as nvtrust stay here.
- `model_hubs`, and `huggingface-hub` in `ml_frameworks`: hosting models and model cards. The Hub
  client's ModelCard API is one module of `huggingface-hub` (F0188), not a product.
- `speech_audio` / `media_generation`: generating media. Watermarking generated media is here.
- Out of scope: general, non-AI software supply chain (in-toto F0010, cdxgen F0012, SPDX tooling)
  and ISO 42001 document templates with no tool behind them (W0008).

**Contested rulings**, all recorded in the category's `comments`:

| product | from | ruling | reason |
|---|---|---|---|
| synthid-text | `safeguards` tail | **moved here** | A watermark embedder and detector filters no unsafe I/O; it answers where text came from (F0053, F0171). |
| c2pa-sdk | absent | **here** | A signed manifest is provenance a third party verifies (W0009). |
| content-seal, invisible-watermark, trustmark, markllm | 6b seed | **here** | 6b was parked; watermarking joins C2PA as the provenance leg. |
| compl-ai | absent | **here** (vs `evaluation_code`) | Its benchmarks are mapped to EU AI Act articles for a conformity report (F0167, W0016). |
| ai-verify | absent | **here** (vs `evaluation_code`) | A governance testing framework that produces structured reports for stakeholders (F0160). Its LLM red-team sibling, Moonshot, would be `safeguards`. |
| halo-record | absent | **here** (vs `telemetry_observability`) | Its hash-chained records are built for the customer to verify, not the operator (W0019, F0177). |
| croissant | absent | **here** (vs `model_hubs`) | Machine-readable dataset documentation (F0158). Hubs serve Croissant; this row is the format and its library. |
| validmind-library | absent | **here** | Automates model documentation for model-risk validators; the open library of a closed platform (W0012). |
| dstack | absent | **`deployment`**, follow-up | A confidential-VM deployment framework; attestation is a feature of the runtime (F0162). |
| agent-governance-toolkit | `safeguards` tail | **stays** | Runtime policy enforcement first (W0001). |

## The trust tag

Issue #93 asks for every row to be tagged **SA** (self-attested: an auditor reads it and takes it on
trust) or **IV** (independently verifiable: a signature, attestation or proof a third party checks
without trusting the operator). The registry has no field for it, so the tag is recorded per row in
the category's `comments`, and a promoted product repeats it in its own `comments`.

The watermarking rows are tagged SA. A detector reports a statistical signal with an error rate, not
a signed claim, and SynthID-Text's detector also needs the embedder's watermarking keys (F0171), so
even that check trusts the operator. The promotion PR should revisit this.

## Capability quantity

One quantity orders the set: **how independently checkable the evidence is.**

1. Template or checklist a person fills in (the ISO 42001 toolkits, parked, W0008).
2. Generated structured documentation, self-attested (verifyml, validmind-library, mlte, ai-verify).
3. Standard-schema, machine-validated evidence mapped to a control framework (compliance-trestle
   OSCAL, croissant, owasp-aibom-generator CycloneDX, venturalitica).
4. Cryptographically signed or tamper-evident evidence checkable offline (model-signing, c2pa-sdk,
   halo-record).
5. Hardware- or proof-backed verification of the execution itself (nvtrust GPU attestation, F0006,
   F0103; ezkl, deepprove and zkml zero-knowledge proofs of inference, W0003).

Rungs 1 to 3 are the SA rows and rungs 4 and 5 the IV ones. The watermarking rows don't climb this
ladder cleanly, which the category's `scoring_recipe.note` records. Openness uses the shared
`software` ladder (`extends: software`): every row is typed `software`.

## Reconciled counts

```
raw_signals       = duplicate_signals + unique_candidates  ->  99 = 9 + 90   (whole sweep, 6a + 6b)
unique_candidates = accepted + parked                      ->  90 = 46 + 44
accepted          = 23 (6a) + 23 (6b)
seeded here       = 23 (6a) + 4 (6b watermarking) + 1 (synthid-text, moved from safeguards) = 28
```

The nine duplicate signals: agent-governance-toolkit and synthid-text (both already in the
`safeguards` tail), HF model-card tooling (`huggingface-hub`), zeus-ml (zeus), aiverify-test-engine
(ai-verify), genai-impact/ecologits (ecologits), "OpenSSF Model Signing v1.0" (model-signing), "Meta
Seal" (content-seal), and the responsibleai package (responsible-ai-toolbox).

The 28 seeded rows come from 28 organizations, one row each. 21 of the 23 6a rows are open or
source-available and 2 are closed; 8 are IV and 20 SA. Of the 6a rows with a repository, 17 of 21
were pushed in the twelve months before the sweep. `research/crosscheck.py` against the corpus found
no slug, GitHub or package collision before the file was written.

**Retrieval cutoff**, declared before the long-tail pass: GitHub repos with fewer than 10 stars and
no PyPI package drawing at least 100 downloads a month were not researched further. Five surfaced
candidates fell under it and are parked below. Venturalitica (6 stars, 648/mo, F0109) clears it on
its package. Coverage limit: awesome-eu-ai-act (W0001, W0016) and the `ai-governance` / `iso-42001`
GitHub topics (W0008) list more sub-10-star repos that the sweep did not enumerate.

## Organizations and handles

Twenty-three of the 28 orgs were new. Each got a minimal `sources/organizations/<slug>.yaml` (empty
`products:`, since tail rows sit on no org roster; `type` is `unknown` wherever the sweep did not
establish it), because a handle must name an org that has a file. Each was registered in
`sources/org_handles.yaml` on the route its row declares (`github`, or `homepage_domain` for
credo-ai). Three handles differ from
the org slug and say why in a `note`: content-authenticity-initiative publishes as `contentauth`,
owasp's AIBOM Generator lives under `GenAI-Security-Project`, and bluewave-labs (the licensor named in
VerifyWise's LICENSE, F0075) publishes as `verifywise-ai`. nvidia, ibm, meta, adobe and google
already had handles covering their rows.

## Accepted candidates

Stars and pushes are from ecosyste.ms, downloads are PyPI last-month unless noted, and last-release
values are from pypi.org JSON, following the audit.

### Assurance and compliance evidence (6a)

| slug | status / tag | license (source) | last push | adoption | notes |
|---|---|---|---|---|---|
| compliance-trestle | open / SA | Apache-2.0 (F0001, F0174) | 2026-09-24 | PyPI 63,201/mo (F0098); 278★ | OSCAL compliance-as-code |
| ai-verify | open / SA | Apache-2.0 (F0002, F0160) | 2026-03-23 | 96★ | `aiverify-test-engine` not declared: no repository link, not the documented path (F0099) |
| mlte | open / SA | MIT (F0003) | 2026-08-11 | PyPI 392/mo (F0100) | 2.7.0, 2026-08-21 (F0190) |
| model-signing | open / IV | Apache-2.0 (F0004) | 2026-09-17 | PyPI 13,307/mo (F0101); 244★ | OMS format; NGC signs NVIDIA models with it (W0010) |
| croissant | open / SA | Apache-2.0 (F0005) | 2026-07-15 | `mlcroissant` 33,784/mo (F0102); 883★ | format spec + library (F0158) |
| nvtrust | open / IV | Apache-2.0 (F0006, F0159); verifier BSD-3-Clause (F0104) | 2026-09-01 | `nv-attestation-sdk` 6,341/mo (F0103); 323★ | GPU attestation |
| c2pa-sdk | open / IV | MIT OR Apache-2.0 (F0091, F0092) | 2026-09-24 | crate `c2pa` 1,150,875 in 90 days (F0153); c2pa-python 171,819/mo (F0108) | c2pa-rs, c2pa-python, c2patool, c2pa-js are one product (W0009) |
| owasp-aibom-generator | open / SA | Apache-2.0 text (F0068) | 2026-09-02 | 100★ (F0011) | CycloneDX output (W0002); no package (F0168) |
| compl-ai | open / SA | Apache-2.0 (F0017, F0167) | 2026-09-18 | 211★ | ETH Zurich, INSAIT, LatticeFlow (W0016) |
| validmind-library | open (AGPL option) / SA | AGPL-3.0 OR ValidMind Commercial (F0073) | 2026-09-14 | PyPI 1,370/mo (F0110) | feeds a closed platform (W0012) |
| verifywise | source-available / SA | BSL 1.1, changes to Apache-2.0 (F0075) | 2026-09-25 | 358★ (F0019) | |
| venturalitica | open / SA | Apache-2.0 (F0016, F0109) | 2026-08-27 | PyPI 648/mo (F0109) | OSCAL + CycloneDX ML-BOM + Annex IV output (W0016) |
| air-blackbox | open / SA | Apache-2.0 (F0151, F0136) | 2026-09-13 | PyPI 431/mo (F0136) | |
| opencomplai | open / SA | AGPL-3.0-only (F0027, F0147) | 2026-09-23 | PyPI 113/mo (F0137) | |
| halo-record | open / IV | Apache-2.0 (F0177, F0179) | 2026-09-15 | PyPI 1,103/mo (F0179) | created 2026-06-11; halo-record-ts is a SKU (F0221) |
| ezkl | source-available / IV | **no license grant**: no LICENSE (F0063–F0066), no Cargo field (F0093), CLA only (F0094) | 2026-02-20 | PyPI 3,013/mo (F0105); 1,222★ | |
| deepprove | source-available / IV | Lagrange License, proprietary evaluation use (F0172, F0164) | 2025-10-01 | 3,359★ (F0021) | the ecosyste.ms `apache-2.0` label is wrong |
| data-provenance-collection | open / SA | Apache-2.0 (F0024) | 2025-03-26 | 282★ | dormant |
| aicert | open / IV | Apache-2.0 (F0025) | 2024-06-25 | 20★ | dormant |
| zkml | open / IV | Apache-2.0 (F0022) | 2024-05-17 | 379★ | dormant; TensorFlow to Halo2 compiler (W0003) |
| verifyml | open / SA | Apache-2.0 (F0009) | 2022-02-07 | PyPI 38/mo (F0107) | the churn evidence #93 cites |
| ibm-watsonx-governance | closed / SA | proprietary SaaS (F0156) | — | Gartner MQ 2026 Leader (W0014) | closed comparator |
| credo-ai | closed / SA | proprietary SaaS (F0157) | — | Forrester Wave Leader Q3 2025 (W0014) | closed comparator |

### Watermarking and provenance, from the 6b seed

| slug | status / tag | license (source) | last push | adoption | notes |
|---|---|---|---|---|---|
| content-seal | open / SA | MIT (F0176, F0180); member Stable Signature CC-BY-NC-4.0 (F0088) | 2026-07-08 | 243★; member AudioSeal 127,614/mo (F0128) | one suite row: AudioSeal, Video Seal, Watermark Anything, Stable Signature, Pixel Seal, TextSeal (F0180). No package declared, since AudioSeal's downloads belong to one member. |
| invisible-watermark | open / SA | MIT (F0058) | 2023-09-23 | PyPI 120,631/mo (F0130) | dormant; downloads are a dependency pull |
| trustmark | open / SA | MIT with Adobe notice (F0090) | 2026-09-08 | PyPI 26,879/mo (F0131) | |
| markllm | open / SA | Apache-2.0 text (F0186); PyPI says MIT (F0132) | 2026-09-05 | PyPI 134/mo; 1,076★ | 0.1.5, 2024-10-21 (F0219) |
| synthid-text | open / SA | Apache-2.0 | — | — | moved from the `safeguards` tail, row unchanged; keyed detector (F0171) |

## License notes for promotion

Custom or unusual strings go to the maintainer's single license-rulings issue, and products carrying
one are deferred at promotion rather than scored: validmind-library (AGPL-3.0 OR a commercial
license), verifywise (BSL 1.1), deepprove (Lagrange License), ezkl (no grant), and content-seal's
CC-BY-NC member. Rows citing only an ecosyste.ms body rest on the GitHub license label; the auditor
checked six against LICENSE text, and a maintainer should read the text before promotion.

## Parked candidates

| # | name | reason | source |
|---|---|---|---|
| 1 | tensorflow/model-card-toolkit | unmaintained: archived, last push 2023-07-26 | F0008 |
| 2 | in-toto | out of scope: general software supply chain | F0010, F0067 |
| 3 | cdxgen | out of scope: general SBOM generator; ML-BOM is one feature | F0012, W0002 |
| 4 | dstack (Dstack-TEE) | boundary: `deployment` (follow-up) | F0020, F0162, W0007 |
| 5 | XDgov/model-card-generator | below the retrieval cutoff (5★, no package) | F0026, F0077 |
| 6 | giselleevita/sai-platform | below the retrieval cutoff (0★) | F0029, F0079 |
| 7 | bilgekayali/ModelRiskOps | below the retrieval cutoff (1★) | F0030, F0078 |
| 8 | AbdelStark/eu-ai-act-toolkit | below the retrieval cutoff (8★) | F0028 |
| 9 | ark-forge/mcp-eu-ai-act | boundary: a builder-facing code scanner with no third-party artifact | F0181, W0001 |
| 10 | Ankit-Uniyal/iso-42001-ai-governance-toolkit | document templates, not a tool | W0008 |
| 11 | suchan99/iso-42001-ai-management-system-framework | document templates, not a tool | W0008 |
| 12 | Proof-of-Control v1.0 | a draft standard, to track rather than list | F0178, W0020 |
| 13–17 | Holistic AI Governance Platform, OneTrust AI Governance, ServiceNow AI Control Tower, Collibra AI governance, Modulos | closed long tail | W0014 |
| 18 | VeriTrace | no repository located | W0011 |
| 19 | Attested Intelligence MCP proxy | no repository located | W0011 |
| 20–23 | chutesai/sek8s, Tinfoil, voltage-verify, venice-e2ee-proxy | not verified in this run (boundary likely `deployment`) | W0007 |
| 24 | encypherai/encypher-c2pa | not verified in this run; check against c2pa-sdk | W0009 |
| 25 | zkComposer | no addressable artifact (paper) | W0003 |
| 26 | RISC Zero SmartCore ML | not verified in this run | W0003 |
| 27 | Breakend/experiment-impact-tracker | unmaintained: archived, last push 2024-01-30 | F0034, F0114 |
| 28 | Kepler | out of scope: Kubernetes power exporter, not AI-specific | F0041 |
| 29 | Scaphandre | out of scope: general energy metrology | F0042 |
| 30–33 | AudioSeal, Video Seal, Stable Signature, Watermark Anything | SKUs of content-seal | F0054–F0057, F0180 |
| 34–35 | c2pa-python, c2patool | SKUs of c2pa-sdk | F0014, F0015 |
| 36 | nv-local-gpu-verifier | SKU of nvtrust | F0104 |
| 37–38 | GreenBench, LLMCO2 | no addressable artifact (papers) | W0004 |
| 39 | DelorneN007/fairness_pipeline_dev_toolkit | not verified in this run | W0006 |
| 40 | halo-record-ts | SKU of halo-record | F0221 |
| 41 | DocML | no addressable artifact located | W0013 |
| 42 | CardGen | no addressable artifact (paper, arXiv 2405.06258) | W0013 |
| 43 | ZeroPath AI-BOM | closed long tail | W0002 |
| 44 | Regula (kuzivaai/getregula) | below the retrieval cutoff; `regula-ai` has no PyPI distribution | F0197, F0222, F0223 |

"Not verified in this run" means only a search mention exists. These are follow-ups, not rejections.

## 6b `responsible_ai_measurement` (#30): parked

The sweep found enough supply for #30 (23 accepted, 22 open, 19 orgs) but no single capability
quantity. Carbon/energy, fairness and watermarking measure three unrelated things: joules or kgCO2e,
group-disparity metrics, and watermark robustness. No one ladder orders CodeCarbon against Fairlearn
against TrustMark, so the category fails the fit test's single-quantity rule. **Decision: park #30.**
Watermarking came here. Fairness (10 rows) and carbon/energy (9 rows) each fall short of the
15-candidate bar for a category of their own, so neither is created and **no registry file is
written for them**. #30 stays open for a fairness-only or carbon-only proposal, and the rows below are
ready to paste when one is ruled. The paste-ready YAML is
`research/assurance_evidence/rows.responsible_ai_measurement.yaml` on the evidence branch.

### Fairness (10)

| slug | org | artifacts | license (source) | last push | adoption |
|---|---|---|---|---|---|
| fairlearn | fairlearn | `fairlearn/fairlearn`, PyPI `fairlearn` | MIT (F0043, F0187) | 2026-09-21 | 154,164/mo (F0117); 2,287★ |
| aif360 | trusted-ai | `Trusted-AI/AIF360`, PyPI `aif360` | Apache-2.0 (F0044) | 2026-06-15 | 30,259/mo (F0118); no release since 2024-04 |
| aequitas | dssg | `dssg/aequitas`, PyPI `aequitas` | MIT (F0045) | 2026-05-12 | 17,542/mo (F0119) |
| what-if-tool | google | `PAIR-code/what-if-tool`, PyPI `witwidget` | Apache-2.0 (F0046) | 2026-09-21 | 21,055/mo (F0120); last release 2021-10 |
| fairness-indicators | google | `tensorflow/fairness-indicators`, PyPI `fairness-indicators` | Apache-2.0 (F0047) | 2026-07-10 | 1,311/mo (F0121) |
| holisticai | holistic-ai | `holistic-ai/holisticai`, PyPI `holisticai` | Apache-2.0 text (F0185); PyPI says MIT (F0122) | 2026-07-31 | 2,404/mo (F0122) |
| langfair | cvs-health | `cvs-health/langfair`, PyPI `langfair` | Apache-2.0 + MIT components (F0089) | 2026-09-11 | 505/mo (F0123); 0.8.0, 2026-01-09 (F0214) |
| responsible-ai-toolbox | microsoft | `microsoft/responsible-ai-toolbox`, PyPI `raiwidgets` | MIT (F0050, F0169) | 2026-09-10 | raiwidgets 4,052/mo (F0124) |
| lift | linkedin | `linkedin/LiFT` | BSD-2-Clause (F0051) | 2025-12-19 | 173★ |
| fairlens | synthesized | `synthesized-io/fairlens`, PyPI `fairlens` | BSD-3-Clause (F0052) | 2026-08-17 | 34/mo (F0126) |

Boundary for a future fairness category: these are scikit-learn-adjacent, but their reason for fame
is fairness measurement, so flag the `classic_ml_cv` sibling. Fairness benchmarks and datasets (BBQ
and the like) stay in `benchmark_eval_data`. The closed fairness capability sits inside the GRC suites
seeded here, so a fairness category would have no closed comparator of its own.

### Carbon and energy (9)

| slug | org | artifacts | license (source) | last push | adoption |
|---|---|---|---|---|---|
| codecarbon | mlco2 | `mlco2/codecarbon`, PyPI `codecarbon` | MIT (F0031) | 2026-09-19 | 142,686/mo (F0111); 1,920★ |
| zeus | ml-energy | `ml-energy/zeus`, PyPI `zeus` | Apache-2.0 (F0032, F0149) | 2026-09-21 | 6,166/mo (F0112) |
| carbontracker | saintslab | `saintslab/carbontracker`, PyPI `carbontracker` | MIT (F0220, F0096) | 2026-08-27 | 1,203/mo (F0096); canonical repo per the audit |
| ecologits | mlco2 | `mlco2/ecologits`, PyPI `ecologits` | MPL-2.0 (F0175, F0097) | 2026-09-22 | 8,322/mo (F0097) |
| eco2ai | sb-ai-lab | `sb-ai-lab/Eco2AI`, PyPI `eco2ai` | Apache-2.0 (F0038) | 2025-03-10 | 138/mo (F0115); dormant |
| perun | helmholtz-ai-energy | `Helmholtz-AI-Energy/perun`, PyPI `perun` | BSD-3-Clause (F0040) | 2026-09-24 | 4,264/mo (F0116) |
| ml-co2-impact | mlco2 | `mlco2/impact`, homepage mlco2.github.io/impact | MIT (F0035) | 2026-04-13 | 270★; web calculator (F0184) |
| ai-energy-score | hugging-face | `huggingface/AIEnergyScore` | MIT (F0036) | 2025-12-02 | 42★ (W0015); flag vs `evaluation_code` |
| ml-energy-leaderboard | ml-energy | `ml-energy/leaderboard` | none (F0080–F0083 404) | 2026-05-07 | 13★; flag vs `evaluation_code` |

Boundary for a future carbon category: general datacenter or host energy metrology (Kepler,
Scaphandre) is out of scope as not AI-specific. mlco2 holds three of the nine rows, above the fit
test's 30% single-org ceiling at this size, which a carbon proposal would also need to answer.

## Open items for promotion

1. Band the capability ladder above against real products, and decide whether watermark robustness
   is a second quantity that needs its own reading or a sub-note.
2. Revisit the SA tag on the watermarking rows.
3. Send the custom license strings above to the license-rulings issue before scoring.
4. Follow-ups outside this seed: dstack to `deployment`; the "not verified in this run" parked rows;
   Regula once `regula-ai` ships a distribution (read its `LicenseRef-DRL-1.1` component then).
5. The first promotion tranche should carry both closed comparators and cover each rung, including
   at least one IV row from the signing leg and one from the proof leg.
