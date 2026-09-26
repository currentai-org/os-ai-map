# Federated learning sweep — 2026-09-26

Category slug `federated_learning` (issue #574, Brief 7). Every figure below was fetched in this
run on 2026-09-26. `Fnnnn` ids point to `fetch-log.tsv` and `raw/`; `Wnnnn` ids point to
`web-log.tsv`.

## 1. Verdict

**GO-WITH-CHANGES.** Supply is deep. This run found 33 new candidates from 31 organizations, plus
`pysyft` and `syfthub` moving in, and at least 14 of them are active and carry a PyPI download
instrument. So the set clears 10 without padding. The largest organization, Google, holds 3 of 33
rows (9.1%). The changes are to the 2026-09-14 framing, not to the category itself.
(1) **Openness is no longer uniform.** The set now spans Apache-2.0, MIT, GPL-3.0, AGPL-3.0,
Clear BSD, a custom academic-only license (FL4Health) and two closed platforms, so #533's "uniformly
open" objection is weaker than the issue said.
(2) **Flower's lead is narrower than the issue recorded.** Flower reads 74,715
installs a month today on both ecosyste.ms and pypistats (F0046, F0108), not the 120,618 read on 2026-09-14 (W0028). It is
about 3.1x NVIDIA FLARE (24,429, F0050), down from the issue's 4.5x (W0028), and the two together are 89% of the declared PyPI downloads
in the set.
(3) **Two of the six "known" products are winding down.** OpenFL's README says the project "is no
longer under active development and will soon be archived" and points users to Flower (F0110).
FedML's README now leads with TensorOpera's generative-AI cloud, and its last PyPI release was
2025-02-24 (F0112, F0094).
(4) The litmus should cover federated **evaluation, analytics and retrieval** as well as training,
so that `syfthub` (federated RAG) and vantage6/Rhino (federated statistics) pass it on their stated
function (see §3).

## 2. Fit metrics (computed from section 6, not estimated)

- accepted candidates: **33** (open: 30, open-weights: 0, source-available: 1, closed: 2). With
  the two contested moves (`pysyft`, `syfthub`, both Apache-2.0: F0002, F0003, F0127), the category
  would hold 35.
- independent organizations: **31**. Largest org's share: **9.1% (google: tensorflow-federated,
  federated-compute-platform, fedjax)**. `lf-ai-and-data` holds 2 (openfl, substra). With the
  moves, google holds 3/35 (8.6%) and openmined 2/35.
- candidates active in the last 12 months (last push on or after 2025-09-26): **22** of the 31 with
  a repository. The 9 below the line are substra, fate, federatedscope, paddlefl, primihub,
  fedtree, metisfl, fedscale and galaxy-federated-learning. The 2 closed rows have no push date.
- candidates with a usage instrument (a declared PyPI package with a fetched monthly figure):
  **17**. federatedscope declares a package, but ecosyste.ms reports 0 with a null period (F0058),
  so it isn't counted.
- adoption concentration (derived from §6b): declared PyPI total 111,216 a month. Flower is 67.2%,
  and Flower plus NVIDIA FLARE is 89.1%.
- retrieval cutoff: GitHub topic pages `federated-learning` (sorted by stars) and
  `federated-learning-framework`, first page of 20 each (W0005, W0006), plus 17 WebSearch queries.
  Topic-page results past the first 20 were not read. That is a coverage limit, not a rejection.
  Hugging Face was not swept: the category holds software only, and no FL model line surfaced in
  search.
- brief leads **not** named but surfaced by search: secretflow, pfl-research, pfllib, vantage6,
  federated-compute-platform, fedjax, fedlab, fedlearner, plato-fl, flame-fl, nebula-dfl, p2pfl,
  primihub, fedtree, featurecloud, metisfl, xfl, galaxy-federated-learning, fl4health, Scaleout
  Edge (parked), HPE Swarm Learning (parked), Photon (parked).

## 3. Boundary

**Definition.** Software that trains, evaluates or queries a shared model across data holders who
never pool their raw data. It coordinates model updates, aggregates or queries, never datasets.

**Litmus.** Does the raw data stay with its owner for the whole run, with only model updates or
aggregates leaving the silo? (This widens the brief's "training data" to cover federated
evaluation, analytics and RAG. Q5 asks whether to keep that.)

**Explicit exclusions:**
- Volunteer and decentralized inference (Petals, exo) belongs to `inference_code` or is out of
  scope. Decentralized training networks (hivemind, Prime Intellect, Gensyn) and chain SDKs are out
  of scope under #428's general-infrastructure exclusion, per the brief.
- Differential-privacy, homomorphic-encryption and MPC primitive libraries with no federation
  runtime: no category, and out. Searches for secure-aggregation or federated-analytics *libraries*
  returned only papers (W0009).
- FL benchmarks and leaderboards (FL-bench, blades, VFLAIR) belong to `evaluation_code` or
  `benchmark_eval_data`.
- FL datasets (MedMNIST, and `flwr-datasets` if it is ever split out) belong to
  `dataset_processing_tools` or the dataset categories.
- Cloud reference architectures (GoogleCloudPlatform/federated-learning) belong to `deployment` or
  are not products.

**Contested products:**

| product | where it is now | recommendation | reason |
|---|---|---|---|
| pysyft | `ml_frameworks` (index) | move here | "Perform data science on data that remains in someone else's server" (W0005). Passes the litmus. PyPI syft 4,941/mo (F0048). |
| syfthub | `orchestration_agents` (index) | move here, **if** the litmus covers querying (Q5) | Federated RAG, not training (sources/products/syfthub.yaml). Under the brief's training-only litmus it fails. |
| flwr-datasets | absent | fold into `flower` (Q2) | Same repo (F0080, F0115). It is a partitioning utility for Flower users, and declaring it would double-count one population. |
| secretflow, primihub | absent | here, flagged (Q4) | Privacy-computing platforms with an FL layer beside MPC (F0117, F0118). No other category owns PET platforms. |
| fedtree | absent | here; **flag to classic_ml_cv sibling** | Federated GBDT (W0025). A classic-ML sweep could claim tree libraries. |
| featurecloud | absent | here; flag to model_hubs sibling | Has an FL "App Store" (W0024), which is not a model hub. Recommend stay here. |
| fedscale, pfllib | absent | here | Both call themselves platform/library plus benchmark (F0019, F0166). The runtime is the product; `evaluation_code` could claim the benchmark half. |
| exo, petals, hivemind | absent | out | Population A/B (F0160–F0162). See Q3. |
| assurance_evidence / responsible_ai_measurement siblings | n/a | flag only | No privacy-measurement tool surfaced here. Any DP-accounting library those sweeps find stays with them. |

## 4. Capability quantity

**Federation reach:** how far outside a single machine the framework can actually run a federated
job, and under what trust assumptions.

1. **Single-machine simulation only.** FedJAX ("Federated learning simulation with JAX", F0113),
   pfl-research ("Simulation framework", F0023), PFLlib ("run it on your PC", F0166).
2. **Real multi-party runs across a few silos, research-grade.** Plato, P2PFL and FedLab. Their
   placement is still to verify at promotion.
3. **Production cross-silo with deployment tooling.** Substra "deployed and used by hospitals and
   biotech companies" (MELLODDY, F0111). vantage6 PET platform "without sharing the data" (W0020).
   FATE "industrial grade", with HE/MPC protocols (F0116).
4. **Cross-silo plus cross-device or HPC scale, large models.** TensorFlow Federated and the
   Federated Compute Platform for on-device FL (F0120, F0119). Flower-based Photon pre-trains up to
   7B federated (W0010).
5. **Top rung, anchored by NVIDIA FLARE.** 2.9.0 ships Docker, Kubernetes and Slurm launchers and
   "hardening large-model training ... for production deployments" (W0026). Flower is the other
   likely top-rung product, but its secure-aggregation and DP features were not fetched in this
   run.

One quantity orders the set. The rung for each product not cited above is a sketch to verify at
promotion, not a finding.

## 5. Scoring ladder inputs

- Ladder: **software** for every row (all 33 are `type: software`). No model, dataset or hardware
  rows.
- License strings met:
  - `Apache-2.0`: flower, nvidia-flare, fedml, openfl, substra, fate, tensorflow-federated,
    federated-compute-platform, fedjax, federatedscope, fed-biomed (text Apache-2.0 while the repo
    label reads "other", F0099), secretflow, pfl-research, pfllib, fedlab, paddlefl, fedlearner,
    plato-fl, flame-fl, primihub, fedtree, featurecloud, fedscale, xfl, galaxy-federated-learning,
    and the moves pysyft and syfthub.
  - `MIT`: appfl (F0105).
  - **Conflict** for vantage6: the LICENSE file is Apache-2.0 (F0104), but PyPI and ecosyste.ms say
    MIT (F0088, F0067).
  - `AGPL-3.0`: nebula-dfl (F0123). `GPL-3.0`: p2pfl (F0124).
  - **`Clear BSD`** (USC): metisfl (F0122). Unusual: it expressly grants no patent rights.
  - **`Vector Institute License`** (custom): fl4health (F0109). Academic entities, sponsors and
    partners only, with no right to "Sell". Unusual, and it conflicts with PyPI's `Apache-2.0` on
    fl4health 0.4.2 (F0073).
  - Proprietary: apheris-networks, rhino-fcp (W0018, W0019).
  - Parked but worth recording: **HPE Swarm Learning**. The repo label and the linked
    `docs/Generic/LICENSE.md` are both Apache-2.0 text (F0121, F0126), yet the README says the
    distribution is "for non-commercial and experimental use" and needs an AutoPass license server
    (F0114).

## 6. Accepted candidates

### 6a. Registry rows

See `rows.yaml` (33 rows, validated against `docs/schemas/registry.schema.json`, no slug or
artifact collision with `research/corpus-index.tsv`). Slug notes: `plato-fl`, `flame-fl` and
`nebula-dfl` carry a suffix because the bare names are generic words. Org notes: `substra` and
`openfl` use `lf-ai-and-data`, following the `onnx` precedent for LF-hosted projects (F0111,
W0016). `federatedscope` uses `alibaba-cloud`, the index's slug for `alibaba/` repos.
`secretflow` uses a new org slug (see Q7).

```yaml
category: federated_learning
products:
  - slug: flower
    display_name: Flower
    type: software
    org: flower-labs
    github: flwrlabs/flower
    pypi: flwr
  - slug: nvidia-flare
    display_name: NVIDIA FLARE
    type: software
    org: nvidia
    github: NVIDIA/NVFlare
    pypi: nvflare
  - slug: fedml
    display_name: FedML
    type: software
    org: tensoropera
    github: FedML-AI/FedML
    pypi: fedml
  - slug: openfl
    display_name: OpenFL (Open Federated Learning)
    type: software
    org: lf-ai-and-data
    github: securefederatedai/openfederatedlearning
    pypi: openfl
  - slug: substra
    display_name: Substra
    type: software
    org: lf-ai-and-data
    github: Substra/substra
    pypi: substra
  - slug: fate
    display_name: FATE (Federated AI Technology Enabler)
    type: software
    org: federatedai
    github: FederatedAI/FATE
  - slug: tensorflow-federated
    display_name: TensorFlow Federated
    type: software
    org: google
    github: google-parfait/tensorflow-federated
    pypi: tensorflow-federated
  - slug: federated-compute-platform
    display_name: Federated Compute Platform
    type: software
    org: google
    github: google-parfait/federated-compute
  - slug: fedjax
    display_name: FedJAX
    type: software
    org: google
    github: google/fedjax
    pypi: fedjax
  - slug: federatedscope
    display_name: FederatedScope
    type: software
    org: alibaba-cloud
    github: alibaba/FederatedScope
    pypi: federatedscope
  - slug: fed-biomed
    display_name: Fed-BioMed
    type: software
    org: inria
    github: fedbiomed/fedbiomed
    pypi: fedbiomed
  - slug: appfl
    display_name: APPFL
    type: software
    org: argonne-national-laboratory
    github: APPFL/APPFL
    pypi: appfl
  - slug: secretflow
    display_name: SecretFlow
    type: software
    org: secretflow
    github: secretflow/secretflow
    pypi: secretflow
  - slug: vantage6
    display_name: vantage6
    type: software
    org: vantage6
    github: vantage6/vantage6
    pypi: vantage6
  - slug: pfl-research
    display_name: pfl-research
    type: software
    org: apple
    github: apple/pfl-research
    pypi: pfl
  - slug: pfllib
    display_name: PFLlib
    type: software
    org: tsingz0
    github: TsingZ0/PFLlib
  - slug: fedlab
    display_name: FedLab
    type: software
    org: smilelab-fl
    github: SMILELab-FL/FedLab
    pypi: fedlab
  - slug: paddlefl
    display_name: PaddleFL
    type: software
    org: paddlepaddle
    github: PaddlePaddle/PaddleFL
    pypi: paddle-fl
  - slug: fedlearner
    display_name: Fedlearner
    type: software
    org: bytedance
    github: bytedance/fedlearner
  - slug: plato-fl
    display_name: Plato
    type: software
    org: tl-system
    github: TL-System/plato
    pypi: plato-learn
  - slug: flame-fl
    display_name: Flame
    type: software
    org: cisco
    github: cisco-open/flame
  - slug: nebula-dfl
    display_name: NEBULA
    type: software
    org: cyberdatalab
    github: CyberDataLab/nebula
  - slug: p2pfl
    display_name: P2PFL
    type: software
    org: p2pfl
    github: p2pfl/p2pfl
    pypi: p2pfl
  - slug: primihub
    display_name: PrimiHub
    type: software
    org: primihub
    github: primihub/primihub
  - slug: fedtree
    display_name: FedTree
    type: software
    org: xtra-computing
    github: Xtra-Computing/FedTree
  - slug: featurecloud
    display_name: FeatureCloud
    type: software
    org: featurecloud
    github: FeatureCloud/FeatureCloud
  - slug: metisfl
    display_name: MetisFL
    type: software
    org: bioint
    github: bioint/MetisFL
  - slug: fedscale
    display_name: FedScale
    type: software
    org: symbioticlab
    github: SymbioticLab/FedScale
    pypi: fedscale
  - slug: xfl
    display_name: XFL
    type: software
    org: paritybit-ai
    github: paritybit-ai/XFL
  - slug: galaxy-federated-learning
    display_name: Galaxy Federated Learning (GFL)
    type: software
    org: galaxylearning
    github: GalaxyLearning/GFL
  - slug: fl4health
    display_name: FL4Health
    type: software
    org: vector-institute
    github: VectorInstitute/FL4Health
  - slug: apheris-networks
    display_name: Apheris Networks
    type: software
    org: apheris
    homepage: https://www.apheris.com/
  - slug: rhino-fcp
    display_name: Rhino Federated Computing Platform
    type: software
    org: rhino-federated-computing
    homepage: https://www.rhinofcp.com/solutions/platform
```

### 6b. Evidence table

Stars, archive and push dates come from ecosyste.ms repository JSON. Monthly downloads come from
ecosyste.ms `downloads` with `downloads_period: last-month`, cross-checked on pypistats where
noted. A release date is the upload time of the current version in PyPI JSON when a package is
declared, and the latest GitHub release otherwise.

| slug | open status | license(s) + source | archived/fork | last push | last release | adoption signal | member checkpoints/components | org handle | notes |
|---|---|---|---|---|---|---|---|---|---|
| flower | open | Apache-2.0: LICENSE text F0102; PyPI license_expression Apache-2.0 F0079 | no/no F0001 | 2026-09-21 F0001 | flwr 1.38.0, 2026-09-22 F0079 | PyPI flwr 74,715/mo (ecosyste.ms F0046; pypistats F0108); 7,140 stars F0001 | framework `flwr`; companion `flwr-datasets` 0.6.1 (24,394/mo F0047, same repo F0080/F0115) held as a component, not declared | gh flwrlabs | Install path `pip install flwr` W0021. The 2026-09-14 sweep read 120,618/mo; both sources read 74,715 today (-38%). |
| nvidia-flare | open | Apache-2.0: LICENSE text F0103; PyPI Apache-2.0 F0082 | no/no F0005 | 2026-09-19 F0005 | nvflare 2.9.0, 2026-09-04 F0082; release 2.9.0 W0026 | PyPI nvflare 24,429/mo (F0050; pypistats 23,969 F0096); 974 stars F0005 | 2.x line | gh NVIDIA | Install path `pip install nvflare` W0022. Corporate (NVIDIA). |
| fedml | open | Apache 2.0 (PyPI F0094; repo apache-2.0 F0004) | no/no F0004 | 2025-10-28 F0004 | fedml 0.9.6, 2025-02-24 F0094 | PyPI fedml 2,132/mo F0049; 4,065 stars F0004 | FedGraphNN (dormant sub-project, F0156) | gh FedML-AI | README now leads with TensorOpera generative-AI cloud F0112, W0011. Corporate. No release in 19 months. |
| openfl | open | Apache-2.0: LICENSE text F0107 | no/no F0006 | 2026-08-25 F0006 | openfl 1.9, 2025-06-10 F0083; GH v1.9 2025-06-23 F0140 | PyPI openfl 467/mo F0051; 843 stars F0006 | none | gh securefederatedai | README: 'no longer under active development and will soon be archived ... recommend the community transitions to Flower' F0110, W0016. PyPI URL securefederatedai/openfl resolves to openfederatedlearning W0027. LF AI & Data project W0016. |
| substra | open | Apache-2.0 (license text embedded in PyPI metadata F0052; repo apache-2.0 F0007) | no/no F0007 | 2024-10-14 F0007 | substra 1.0.0, 2024-10-14 F0084 | PyPI substra 750/mo F0052; 278 stars F0007 | `substrafl` FL library (245/mo F0053; repo pushed 2026-07-17 F0008) | gh Substra | Hosted by LF AI & Data, Owkin main contributor F0111. Core SDK dormant 23 months; substrafl repo still pushed. |
| fate | open | Apache-2.0: LICENSE text F0128 | no/no F0009 | 2024-11-19 F0009 | GH v2.2.0, 2024-07-31 F0137; fate-client 2.2.0 2024-08-06 F0092 | 6,098 stars F0009 (fate-client 609/mo F0055 is a client, not declared) | FATE-LLM (250 stars, pushed 2026-02-21 F0010; fate-llm 135/mo F0078) | gh FederatedAI | 'hosted by Linux Foundation' F0116. Core repo dormant 22 months; FATE-LLM still pushed. |
| tensorflow-federated | open | Apache-2.0: LICENSE text F0106 | no/no F0011 | 2026-09-19 F0011 | tensorflow-federated 0.87.0, 2024-09-17 F0085; GH v0.88.0 2024-09-26 F0139 | PyPI tensorflow-federated 2,230/mo F0057; 2,452 stars F0011 | none | gh google-parfait | ecosyste.ms has no tensorflow/federated (F0012); PyPI points to google-parfait F0085. Repo active, no release in 2 years. |
| federated-compute-platform | open | apache-2.0 (ecosyste.ms F0036; LICENSE not read) | no/no F0036 | 2026-09-17 F0036 | no GitHub releases F0134 | 111 stars F0036 | none | gh google-parfait | Google's server/client platform for federated programs F0119. |
| fedjax | open | Apache 2.0 (PyPI F0076; repo apache-2.0 F0035) | no/no F0035 | 2026-08-06 F0035 | fedjax 0.0.17, 2023-07-12 F0076 | PyPI fedjax 69/mo F0076; 272 stars F0035 | none | gh google | Simulation library; 'not an officially supported Google product' F0113. |
| federatedscope | open | Apache License 2.0 (PyPI F0058; repo apache-2.0 F0013) | no/no F0013 | 2024-08-10 F0013 | federatedscope 0.1.9, 2022-06-27 F0058 | 1,541 stars F0013; PyPI reports 0 with null period F0058 (no usable figure) | FederatedScope-LLM (branch, W0003) | gh alibaba | Dormant 25 months. |
| fed-biomed | open | Apache-2.0: LICENSE text (Inria/UCA) F0099; repo field 'other' F0014 | no/no F0014 | 2026-09-22 F0014 | fedbiomed 6.4.1, 2026-08-06 F0086 | PyPI fedbiomed 375/mo F0059; 93 stars F0014 | none | gh fedbiomed | Label says 'other'; text is Apache-2.0 behind an Inria/UCA notice F0099. |
| appfl | open | MIT: LICENSE text (Argonne) F0105 | no/no F0015 | 2026-09-21 F0015 | appfl 1.11.0, 2026-08-25 F0087 | PyPI appfl 526/mo F0060; 184 stars F0015 | none | gh APPFL | Argonne National Laboratory copyright F0105. |
| secretflow | open | Apache-2.0: LICENSE text F0129 | no/no F0020 | 2026-04-24 F0020 | secretflow 1.14.0b0, 2025-09-26 F0091 | PyPI secretflow 435/mo F0064; 2,712 stars F0020 | none | gh secretflow | Privacy-computing framework with horizontal/vertical FL layer plus MPC devices F0117 (boundary question Q4). |
| vantage6 | open | CONFLICT: LICENSE file Apache-2.0 F0104 vs PyPI license 'MIT' F0088 / ecosyste.ms MIT F0067 | no/no F0024 | 2026-09-19 F0024 | vantage6 5.0.3, 2026-09-21 F0088 | PyPI vantage6 4,113/mo F0067 (vantage6-client 6,722/mo F0068, pypistats 3,365 F0098, not declared); 50 stars F0024 | vantage6 CLI, server, node, client | gh vantage6 | Install path `pip install vantage6` W0023. PET platform for FL and MPC W0020, W0007. |
| pfl-research | open | apache-2.0 (ecosyste.ms F0023; LICENSE not read) | no/no F0023 | 2026-09-16 F0023 | pfl 0.5.2, 2026-09-16 F0093 | PyPI pfl 64/mo F0066; 358 stars F0023 | none | gh apple | Simulation framework for private FL F0093. |
| pfllib | open | apache-2.0 (ecosyste.ms F0021; LICENSE not read) | no/no F0021 | 2025-11-25 F0021 | GH v0.1.12, 2025-03-26 F0135 | 2,006 stars F0021 | none | gh TsingZ0 | 'PFLlib: Personalized Federated Learning Library and Benchmark' F0166; JMLR paper; individual owner handle. |
| fedlab | open | Apache-2.0 License (PyPI F0065; repo apache-2.0 F0022) | no/no F0022 | 2025-10-20 F0022 | fedlab 1.3.0, 2022-10-26 F0065 | PyPI fedlab 497/mo F0065; 828 stars F0022 | none | gh SMILELab-FL |  |
| paddlefl | open | Apache 2.0 (PyPI F0062; repo apache-2.0 F0018) | no/no F0018 | 2023-07-26 F0018 | paddle-fl 1.2.0, 2021-12-06 F0062 | PyPI paddle-fl 192/mo F0062; 512 stars F0018 | none | gh PaddlePaddle | Dormant 38 months. |
| fedlearner | open | apache-2.0 (ecosyste.ms F0027; LICENSE not read) | no/no F0027 | 2026-07-06 F0027 | GH v1.5, 2021-03-22 F0131 | 900 stars F0027 | none | gh bytedance | 'A multi-party collaborative machine learning framework' F0027. |
| plato-fl | open | Apache-2.0 (PyPI F0072; repo apache-2.0 F0028) | no/no F0028 | 2026-06-08 F0028 | plato-learn 1.4.3, 2025-10-25 F0072 | PyPI plato-learn 54/mo F0072; 399 stars F0028 | none | gh TL-System | Slug suffixed: bare `plato` is generic. |
| flame-fl | open | apache-2.0 (ecosyste.ms F0029; LICENSE not read) | no/no F0029 | 2025-11-06 F0029 | GH v0.4.0, 2023-12-15 F0132 | 59 stars F0029 | none | gh cisco-open | 'federated learning system for edge' F0029; cisco-open org. |
| nebula-dfl | open | AGPL-3.0: LICENSE text F0123 | no/no F0031 | 2026-06-29 F0031 | GH 1.0.0, 2025-07-02 F0133 | 82 stars F0031 | none | gh CyberDataLab | Decentralized (serverless) FL platform W0006; only copyleft-network license in set. |
| p2pfl | open | GPL-3.0: LICENSE text F0124; PyPI GPL-3.0-only F0074 | no/no F0032 | 2026-05-09 F0032 | p2pfl 0.4.4, 2025-09-30 F0074 | PyPI p2pfl 66/mo F0074; 155 stars F0032 | none | gh p2pfl | Gossip-based decentralized FL W0008. |
| primihub | open | apache-2.0 (ecosyste.ms F0026; LICENSE not read) | no/no F0026 | 2024-12-02 F0026 | GH 1.7.1.pre, 2024-06-04 F0136 | 1,324 stars F0026 | none | gh primihub | Privacy-computing platform (MPC + FL) F0118; boundary question Q4. Dormant 21 months. |
| fedtree | open | apache-2.0 (ecosyste.ms F0145; LICENSE not read) | no/no F0145 | 2025-01-20 F0145 | not fetched | 153 stars F0145 | none | gh Xtra-Computing | Tree-based (GBDT) horizontal/vertical FL W0025. |
| featurecloud | open | apache-2.0 (ecosyste.ms F0144; LICENSE not read) | no/no F0144 | 2026-02-04 F0144 | not fetched | 11 stars F0144 (PyPI `featurecloud` points to FeatureCloud/app-template F0147; not declared) | none | gh FeatureCloud | Biomedical FL platform with app store W0024; hosted service at featurecloud.ai (not fetched). |
| metisfl | open | Clear BSD (USC): LICENSE text F0122; repo field 'other' F0033 | no/no F0033 | 2024-06-27 F0033 | no GitHub tags F0033; PyPI metisfl 1.0.0 2023-09-22 points to nevronai/metisfl F0075 (not declared) | 523 stars F0033 | none | gh bioint | Clear BSD: 'NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED' F0122; flag for tiering. |
| fedscale | open | apache-2.0 (PyPI F0063; repo F0019) | no/no F0019 | 2023-12-18 F0019 | fedscale 1.0, 2024-04-06 F0063 | PyPI fedscale 102/mo F0063; 421 stars F0019 | none | gh SymbioticLab | 'scalable and extensible open-source federated learning (FL) platform' F0019. Dormant 33 months. |
| xfl | open | apache-2.0 (ecosyste.ms F0154; LICENSE not read) | no/no F0154 | 2026-03-17 F0154 | not fetched | 43 stars F0154 | none | gh paritybit-ai |  |
| galaxy-federated-learning | open | apache-2.0 (ecosyste.ms F0148; LICENSE not read) | no/no F0148 | 2023-01-14 F0148 | not fetched | 253 stars F0148 | none | gh GalaxyLearning | Dormant 44 months. |
| fl4health | source-available | Vector Institute License (academic/sponsor/partner only, no right to Sell) LICENSE.md F0109; repo field 'other' F0030; PyPI fl4health 0.4.2 says Apache-2.0 F0073 | no/no F0030 | 2026-09-21 F0030 | fl4health 0.4.2, 2026-01-21 F0073 (PyPI has no repo URL; not declared) | 56 stars F0030 | none | gh VectorInstitute | Custom license, last updated 12-08-2025 F0109; the PyPI Apache label predates or contradicts it. Flag. |
| apheris-networks | closed | proprietary (no open-source statement W0018) | n/a | n/a | n/a | none | Apheris also sells Foundry, ApherisFold (out of scope) W0018 | homepage apheris.com | Surface = 'Networks - Federated AI training' W0018, W0004. |
| rhino-fcp | closed | proprietary (no open-source mention W0019) | n/a | n/a | n/a | none | federated statistics, learning, inference W0019 | homepage rhinofcp.com | W0004, W0019. |

### 6c. Source list

Every id cited in §6b, with fetch date. The full trail, including ids cited only in §1–§5 and
§7–§9, is in `fetch-log.tsv` (166 fetches) and `web-log.tsv` (28 entries).

- F0001 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/flwrlabs%2Fflower
- F0004 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/FedML-AI%2FFedML
- F0005 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/NVIDIA%2FNVFlare
- F0006 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/securefederatedai%2Fopenfederatedlearning
- F0007 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Substra%2Fsubstra
- F0008 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Substra%2Fsubstrafl
- F0009 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/FederatedAI%2FFATE
- F0010 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/FederatedAI%2FFATE-LLM
- F0011 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/google-parfait%2Ftensorflow-federated
- F0012 (2026-09-26, HTTP 404): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/tensorflow%2Ffederated
- F0013 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/alibaba%2FFederatedScope
- F0014 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/fedbiomed%2Ffedbiomed
- F0015 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/APPFL%2FAPPFL
- F0018 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/PaddlePaddle%2FPaddleFL
- F0019 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/SymbioticLab%2FFedScale
- F0020 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/secretflow%2Fsecretflow
- F0021 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/TsingZ0%2FPFLlib
- F0022 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/SMILELab-FL%2FFedLab
- F0023 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/apple%2Fpfl-research
- F0024 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/vantage6%2Fvantage6
- F0026 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/primihub%2Fprimihub
- F0027 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/bytedance%2Ffedlearner
- F0028 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/TL-System%2Fplato
- F0029 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/cisco-open%2Fflame
- F0030 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/VectorInstitute%2FFL4Health
- F0031 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/CyberDataLab%2Fnebula
- F0032 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/p2pfl%2Fp2pfl
- F0033 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/bioint%2FMetisFL
- F0035 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/google%2Ffedjax
- F0036 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/google-parfait%2Ffederated-compute
- F0046 (2026-09-26, HTTP 200): https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/flwr
- F0047 (2026-09-26, HTTP 200): https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/flwr-datasets
- F0049 (2026-09-26, HTTP 200): https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/fedml
- F0050 (2026-09-26, HTTP 200): https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/nvflare
- F0051 (2026-09-26, HTTP 200): https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/openfl
- F0052 (2026-09-26, HTTP 200): https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/substra
- F0053 (2026-09-26, HTTP 200): https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/substrafl
- F0055 (2026-09-26, HTTP 200): https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/fate-client
- F0057 (2026-09-26, HTTP 200): https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/tensorflow-federated
- F0058 (2026-09-26, HTTP 200): https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/federatedscope
- F0059 (2026-09-26, HTTP 200): https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/fedbiomed
- F0060 (2026-09-26, HTTP 200): https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/appfl
- F0062 (2026-09-26, HTTP 200): https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/paddle-fl
- F0063 (2026-09-26, HTTP 200): https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/fedscale
- F0064 (2026-09-26, HTTP 200): https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/secretflow
- F0065 (2026-09-26, HTTP 200): https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/fedlab
- F0066 (2026-09-26, HTTP 200): https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/pfl
- F0067 (2026-09-26, HTTP 200): https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/vantage6
- F0068 (2026-09-26, HTTP 200): https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/vantage6-client
- F0072 (2026-09-26, HTTP 200): https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/plato-learn
- F0073 (2026-09-26, HTTP 200): https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/fl4health
- F0074 (2026-09-26, HTTP 200): https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/p2pfl
- F0075 (2026-09-26, HTTP 200): https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/metisfl
- F0076 (2026-09-26, HTTP 200): https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/fedjax
- F0078 (2026-09-26, HTTP 200): https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/fate-llm
- F0079 (2026-09-26, HTTP 200): https://pypi.org/pypi/flwr/json
- F0080 (2026-09-26, HTTP 200): https://pypi.org/pypi/flwr-datasets/json
- F0082 (2026-09-26, HTTP 200): https://pypi.org/pypi/nvflare/json
- F0083 (2026-09-26, HTTP 200): https://pypi.org/pypi/openfl/json
- F0084 (2026-09-26, HTTP 200): https://pypi.org/pypi/substra/json
- F0085 (2026-09-26, HTTP 200): https://pypi.org/pypi/tensorflow-federated/json
- F0086 (2026-09-26, HTTP 200): https://pypi.org/pypi/fedbiomed/json
- F0087 (2026-09-26, HTTP 200): https://pypi.org/pypi/appfl/json
- F0088 (2026-09-26, HTTP 200): https://pypi.org/pypi/vantage6/json
- F0091 (2026-09-26, HTTP 200): https://pypi.org/pypi/secretflow/json
- F0092 (2026-09-26, HTTP 200): https://pypi.org/pypi/fate-client/json
- F0093 (2026-09-26, HTTP 200): https://pypi.org/pypi/pfl/json
- F0094 (2026-09-26, HTTP 200): https://pypi.org/pypi/fedml/json
- F0096 (2026-09-26, HTTP 200): https://pypistats.org/api/packages/nvflare/recent
- F0098 (2026-09-26, HTTP 200): https://pypistats.org/api/packages/vantage6-client/recent
- F0099 (2026-09-26, HTTP 200): https://raw.githubusercontent.com/fedbiomed/fedbiomed/HEAD/LICENSE.md
- F0102 (2026-09-26, HTTP 200): https://raw.githubusercontent.com/flwrlabs/flower/HEAD/LICENSE
- F0103 (2026-09-26, HTTP 200): https://raw.githubusercontent.com/NVIDIA/NVFlare/HEAD/LICENSE
- F0104 (2026-09-26, HTTP 200): https://raw.githubusercontent.com/vantage6/vantage6/HEAD/LICENSE
- F0105 (2026-09-26, HTTP 200): https://raw.githubusercontent.com/APPFL/APPFL/HEAD/LICENSE
- F0106 (2026-09-26, HTTP 200): https://raw.githubusercontent.com/google-parfait/tensorflow-federated/HEAD/LICENSE
- F0107 (2026-09-26, HTTP 200): https://raw.githubusercontent.com/securefederatedai/openfederatedlearning/HEAD/LICENSE
- F0108 (2026-09-26, HTTP 200): https://pypistats.org/api/packages/flwr/recent
- F0109 (2026-09-26, HTTP 200): https://raw.githubusercontent.com/VectorInstitute/FL4Health/HEAD/LICENSE.md
- F0110 (2026-09-26, HTTP 200): https://raw.githubusercontent.com/securefederatedai/openfederatedlearning/HEAD/README.md
- F0111 (2026-09-26, HTTP 200): https://raw.githubusercontent.com/Substra/substra/HEAD/README.md
- F0112 (2026-09-26, HTTP 200): https://raw.githubusercontent.com/FedML-AI/FedML/HEAD/README.md
- F0113 (2026-09-26, HTTP 200): https://raw.githubusercontent.com/google/fedjax/HEAD/README.md
- F0115 (2026-09-26, HTTP 200): https://raw.githubusercontent.com/flwrlabs/flower/HEAD/datasets/README.md
- F0116 (2026-09-26, HTTP 200): https://raw.githubusercontent.com/FederatedAI/FATE/HEAD/README.md
- F0117 (2026-09-26, HTTP 200): https://raw.githubusercontent.com/secretflow/secretflow/HEAD/README.md
- F0118 (2026-09-26, HTTP 200): https://raw.githubusercontent.com/primihub/primihub/HEAD/README.md
- F0119 (2026-09-26, HTTP 200): https://raw.githubusercontent.com/google-parfait/federated-compute/HEAD/README.md
- F0122 (2026-09-26, HTTP 200): https://raw.githubusercontent.com/bioint/MetisFL/HEAD/LICENSE
- F0123 (2026-09-26, HTTP 200): https://raw.githubusercontent.com/CyberDataLab/nebula/HEAD/LICENSE
- F0124 (2026-09-26, HTTP 200): https://raw.githubusercontent.com/p2pfl/p2pfl/HEAD/LICENSE.md
- F0128 (2026-09-26, HTTP 200): https://raw.githubusercontent.com/FederatedAI/FATE/HEAD/LICENSE
- F0129 (2026-09-26, HTTP 200): https://raw.githubusercontent.com/secretflow/secretflow/HEAD/LICENSE
- F0131 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/bytedance%2Ffedlearner/releases?per_page=1
- F0132 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/cisco-open%2Fflame/releases?per_page=1
- F0133 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/CyberDataLab%2Fnebula/releases?per_page=1
- F0134 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/google-parfait%2Ffederated-compute/releases?per_page=1
- F0135 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/TsingZ0%2FPFLlib/releases?per_page=1
- F0136 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/primihub%2Fprimihub/releases?per_page=1
- F0137 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/FederatedAI%2FFATE/releases?per_page=1
- F0139 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/google-parfait%2Ftensorflow-federated/releases?per_page=1
- F0140 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/securefederatedai%2Fopenfederatedlearning/releases?per_page=1
- F0144 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/FeatureCloud%2FFeatureCloud
- F0145 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Xtra-Computing%2FFedTree
- F0147 (2026-09-26, HTTP 200): https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/featurecloud
- F0148 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/GalaxyLearning%2FGFL
- F0154 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/paritybit-ai%2FXFL
- F0156 (2026-09-26, HTTP 200): https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/FedML-AI%2FFedGraphNN
- F0166 (2026-09-26, HTTP 200): https://raw.githubusercontent.com/TsingZ0/PFLlib/HEAD/README.md
- W0003 (2026-09-26, WebSearch): new federated learning framework release 2025 open source LLM fine-tuning
- W0004 (2026-09-26, WebSearch): Apheris Rhino Federated Computing Platform Owkin federated learning platform 2026
- W0006 (2026-09-26, WebFetch): https://github.com/topics/federated-learning-framework
- W0007 (2026-09-26, WebSearch): vantage6 FEDn Scaleout federated learning open source platform
- W0008 (2026-09-26, WebSearch): federated learning framework github 2026 release announcement
- W0011 (2026-09-26, WebSearch): FedML TensorOpera federated learning status 2026
- W0016 (2026-09-26, WebSearch): federated learning Linux Foundation LF AI Data project OpenFL Substra 2026
- W0018 (2026-09-26, WebFetch): https://www.apheris.com/
- W0019 (2026-09-26, WebFetch): https://www.rhinofcp.com/solutions/platform
- W0020 (2026-09-26, WebFetch): https://docs.vantage6.ai/
- W0021 (2026-09-26, WebFetch): https://flower.ai/docs/framework/how-to-install-flower.html
- W0022 (2026-09-26, WebFetch): https://nvflare.readthedocs.io/en/main/installation.html
- W0023 (2026-09-26, WebFetch): https://docs.vantage6.ai/en/main/node/install.html
- W0024 (2026-09-26, WebSearch): FeatureCloud federated learning platform open source github
- W0025 (2026-09-26, WebSearch): vertical federated learning open source library gradient boosting FedTree SecureBoost
- W0026 (2026-09-26, WebSearch): NVIDIA FLARE 2.9 release federated learning 2026
- W0027 (2026-09-26, WebFetch): https://github.com/securefederatedai/openfl

## 7. Parked candidates

| # | name | reason | source | fetch date |
|---|---|---|---|---|
| 1 | pysyft | already mapped (`ml_frameworks`); contested, move here (§3) | F0002, F0048 | 2026-09-26 |
| 2 | syfthub | already mapped (`orchestration_agents`); contested, move here if Q5 (§3) | F0003, F0141 | 2026-09-26 |
| 3 | flwr-datasets (Flower Datasets) | SKU of flower (component in the same repo; Q2) | F0047, F0080, F0115 | 2026-09-26 |
| 4 | substrafl | SKU of substra | F0008, F0053 | 2026-09-26 |
| 5 | FATE-LLM | SKU of fate | F0010, F0078 | 2026-09-26 |
| 6 | FederatedScope-LLM | SKU of federatedscope (a branch of the same repo) | W0003 | 2026-09-26 |
| 7 | FedGraphNN | SKU of fedml (FedML-AI sub-project, last push 2023-12-19) | F0156 | 2026-09-26 |
| 8 | Scaleout Edge (formerly FEDn) | identity unclear: the open repo is now only the client SDK ("A flexible SDK (this repository)"), and the platform needs registration (F0142). An open satellite around a gated core, per `identity.md`. The older `fedn` 0.33.0 (2025-09-15, 4,941/mo) still ships (F0069, F0089). Q6 | F0039, F0142, F0069, F0090, W0012 | 2026-09-26 |
| 9 | IBM Federated Learning (federated-learning-lib) | unmaintained: archived (F0017); "archived on July 27, 2026 ... IBMFL 2.0.1 ... final release" (W0008) | F0017, W0008 | 2026-09-26 |
| 10 | Microsoft FLUTE (msrflute) | unmaintained: archived, last push 2024-01-11 | F0016 | 2026-09-26 |
| 11 | FLSim (facebookresearch) | unmaintained: archived, last push 2024-08-26 | F0034 | 2026-09-26 |
| 12 | HPE Swarm Learning | closed long-tail: the runtime needs an AutoPass license server and ships "for non-commercial and experimental use" (F0114), despite Apache-2.0 text in the repo (F0126, F0121). 354 stars, pushed 2026-07-27 | F0114, F0121, F0126, W0013 | 2026-09-26 |
| 13 | KatherLab/swarm-learning-hpe | SKU of HPE Swarm Learning (an application repo, 14 stars) | F0159 | 2026-09-26 |
| 14 | Owkin | SKU of substra: Owkin's FL software is Substra, now LF-hosted (F0111). No separate FL product found | F0111, W0004 | 2026-09-26 |
| 15 | OpenFedLLM | identity unclear: paper codebase, no releases, no package, last push 2024-12-12 | F0037, W0003 | 2026-09-26 |
| 16 | Photon | identity unclear: paper codebase on Flower, 0 stars, last push 2025-04-10 | F0040, W0010 | 2026-09-26 |
| 17 | FL-bench | boundary → `evaluation_code` ("Benchmark of federated learning"), GPL-3.0 | F0038, W0006 | 2026-09-26 |
| 18 | blades | boundary → `evaluation_code` (attack/defense benchmark suite) | F0149 | 2026-09-26 |
| 19 | VFLAIR | boundary → `evaluation_code` ("research library and benchmark"); repo not fetched | W0025 | 2026-09-26 |
| 20 | HeFlwr | identity unclear: research extension of Flower for heterogeneous devices, 127 stars | F0150 | 2026-09-26 |
| 21 | FractalAndroid | identity unclear: edge-compute plus FL Android node; license label "other", text not read | F0151 | 2026-09-26 |
| 22 | RIS-FL | identity unclear: simulation code for one paper | F0152 | 2026-09-26 |
| 23 | FedCLS | identity unclear: ICLR 2023 paper code, no license | F0155 | 2026-09-26 |
| 24 | NErlNet | boundary → distributed-ML research framework, not FL-specific | F0153 | 2026-09-26 |
| 25 | shaoxiongji/federated-learning | identity unclear: tutorial implementation (1,393 stars, last push 2024-07-25) | F0157 | 2026-09-26 |
| 26 | AshwinRJ/Federated-Learning-PyTorch | identity unclear: tutorial implementation of the FedAvg paper | F0158 | 2026-09-26 |
| 27 | MedMNIST | boundary → a biomedical dataset, not FL software | W0005 | 2026-09-26 |
| 28 | GoogleCloudPlatform/federated-learning | boundary → `deployment` (cloud reference architecture, 21 stars) | F0146, W0024 | 2026-09-26 |
| 29 | Petals | boundary → out (volunteer inference). Last push 2024-09-07, PyPI 202/mo, last release 2023-09-06 | F0160, F0163 | 2026-09-26 |
| 30 | exo | boundary → out (local and distributed inference). 45,525 stars. PyPI `exo` is a different project (CEGRcode, F0165) | F0161, F0165 | 2026-09-26 |
| 31 | hivemind | boundary → out (decentralized training). PyPI 5,784/mo | F0162, F0164 | 2026-09-26 |
| 32 | ReFedEz | no addressable artifact: search snippet only, no repo found | W0001, W0014 | 2026-09-26 |
| 33 | Fedstellar | identity unclear: search snippet only (W0008). Possibly NEBULA's predecessor, not fetched | W0008 | 2026-09-26 |
| 34 | FedLess | no addressable artifact: named in a search snippet, not fetched | W0014 | 2026-09-26 |
| 35 | OpenFed | no addressable artifact: named in a search snippet, not fetched | W0014 | 2026-09-26 |
| 36 | FedCampus | no addressable artifact: paper mention only | W0015 | 2026-09-26 |
| 37 | Felicitas | no addressable artifact: paper mention only | W0015 | 2026-09-26 |
| 38 | FLaME | no addressable artifact: paper mention only | W0015 | 2026-09-26 |
| 39 | WebFed | no addressable artifact: paper (arXiv 2110.11646) only | W0015 | 2026-09-26 |

## 8. Reconciled counts

Raw signals are the distinct names surfaced across the brief and every discovery source before
dedup. Duplicate signals are names that turned out to be another listed name:
1. FEDn = Scaleout Edge (W0007, W0012)
2. TensorOpera = FedML (W0011, F0112)
3. Rhino Health = Rhino FCP (W0004)
4. IBMFL = IBM Federated Learning (W0008)
5. PyGrid = part of PySyft (W0014)
6. FlowerLLM = Photon, the same Flower Labs federated pre-training effort (W0010)

- raw_signals = **78**
- duplicate_signals = **6**
- unique_candidates = **72**
- accepted = **33**
- parked = **39**

78 = 6 + 72 ✓. 72 = 33 + 39 ✓.

## 9. Open questions for the maintainer

1. **Admit FedML and Substra?** Recommend **yes, as tail rows** (both are in `rows.yaml`), each
   flagged dormant.
   - FedML: last push 2025-10-28, last PyPI release 2025-02-24, 2,132 installs a month (F0004,
     F0094, F0049). Its README has pivoted to TensorOpera (F0112).
   - Substra's core SDK: last push and release 2024-10-14, 750 a month (F0007, F0084, F0052). Its
     FL library substrafl was still pushed on 2026-07-17 (F0008).

   Dormancy doesn't disqualify a candidate, but neither should be among the first 10 promoted.
   Options: (a) tail rows, not promoted first *(recommended)*; (b) promote now; (c) drop.
2. **Is Flower one product or two?** Recommend **one** (`flower`, declaring `flwr` only).
   `flwr-datasets` lives in the same repo (F0080, F0115) and describes itself as a library "to
   quickly and easily create datasets for federated learning" by the Flower team (F0115). Its
   24,394 installs a month (F0047) come mostly from Flower's own users, so declaring it on `flower`
   would mix two measurement populations (`identity.md`, "A real binding whose usage is not the head
   product's usage"). Options: (a) one product, `flwr-datasets` undeclared *(recommended)*; (b) a
   separate row in `dataset_processing_tools`.
3. **Record the volunteer-inference finding as an insight?** Recommend **yes**. Today's numbers
   sharpen it:
   - Petals: 10,586 stars, last push 2024-09-07, no release since 2023-09-06, 202 installs a month
     (F0160, F0163). Down from 452 on 2026-09-14 (W0028).
   - hivemind: 5,784 a month, last release 2026-01-03 (F0164).
   - exo: 45,525 stars (F0161). Its PyPI name belongs to an unrelated project (F0165), so exo has no
     usage instrument at all.
4. **Are privacy-computing platforms with an FL layer (SecretFlow, PrimiHub) in?** Recommend
   **yes**. They pass the litmus, and no other category owns them. Options: (a) in *(recommended)*;
   (b) in only if FL is the primary documented module; (c) out.
5. **Widen the litmus from "training" to "training, evaluation or querying"?** Recommend **yes**.
   Without it, `syfthub` (federated RAG) fails and should stay in `orchestration_agents`, and the
   federated-statistics surfaces of vantage6 and Rhino FCP (W0020, W0019) sit on the edge.
6. **Scaleout Edge (formerly FEDn): park, or add as closed?** Recommend **park**. The open repo is
   now only the client SDK (F0142), and declaring it would lift a gated platform's openness. The
   older fully open `fedn` package (F0089) could be a separate row if the maintainer wants the
   legacy line.
7. **Org slugs.**
   - `secretflow`: new slug, or reuse `ant-group` (already in `sources/organizations/`)? Ant Group
     ownership was **not fetched** in this run. Recommend the new slug until a fetch confirms it.
   - `fate`: `federatedai`, or `lf-ai-and-data`? Its README says "hosted by Linux Foundation"
     (F0116) without naming LF AI & Data. Recommend `federatedai` until the umbrella is confirmed.
8. **License conflicts to settle before scoring.**
   - vantage6: the LICENSE file is Apache-2.0 (F0104), but PyPI says MIT (F0088).
   - fl4health: the Vector Institute License (F0109) versus PyPI's Apache-2.0 (F0073).

   Recommend scoring each on the repo LICENSE text: Apache-2.0 for vantage6, the custom license
   (source-available) for fl4health. Record the other label in `comments`.
9. **OpenFL end of life.** The README says it "will soon be archived" (F0110) but gives no date.
   Recommend keeping it as a tail row now, and adding `end_of_life` when a date is announced or the
   repo is archived.
10. **Closed comparators (ADR-005).** Recommend **only Apheris Networks and Rhino FCP** as
    best-in-class. Both are FL-first surfaces with the data kept in place (W0018, W0019). HPE
    Swarm Learning stays parked as closed long-tail.
