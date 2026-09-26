# Federated learning seed: 2026-09-26

## Scope and boundary

This batch seeds the preliminary `federated_learning` category proposed in issue #574. It sits in
Model components → Pipeline code, after `finetuning_code`, weighted adoption 0.5 / capability 0.5,
and its `scoring_recipe` extends the shared `software` ladder. Every row is typed `software`.

**Membership test.** Does the raw data stay with its owner for the whole run of training,
evaluation or querying, with only model updates, aggregates or queries leaving the silo? The
brief's test said "training data". It is widened here so that federated evaluation, federated
analytics and federated retrieval pass on their stated function. Without the widening, `syfthub`
(federated RAG) fails and stays in `orchestration_agents`, and the federated-statistics surfaces of
vantage6 and Rhino FCP sit on the edge.

**Contested rulings**, all recorded in the category's `comments`:

- `pysyft` (head, `ml_frameworks`) and `syfthub` (head, `orchestration_agents`) move into this
  category **at promotion, not in this seed**. Both are head products, so they have no registry
  rows. They stay in their current rosters until the promotion PR moves them.
- **Flower is one product.** `flwr-datasets` ships in the same repository as a partitioning
  utility for Flower users. Declaring it would count Flower's own users twice, so it is not declared.
- **FedML and Substra are tail rows**, not first-tranche promotions. FedML's README now leads with
  TensorOpera's generative-AI cloud, and its last PyPI release was 2025-02-24. Substra's core SDK
  has not moved since 2024-10-14, while its FL library `substrafl` was pushed on 2026-07-17.
- **OpenFL** says it "is no longer under active development and will soon be archived" and points
  users to Flower. It stays a tail row until an end date is announced or the repository is archived.
- **Privacy-computing platforms with an FL layer** beside MPC (SecretFlow, PrimiHub) are in. They
  pass the litmus, and no other category owns them.
- **FedTree** (federated gradient-boosted trees) stays here and not in `classic_ml_cv`: federation
  is the product, and the tree learner runs inside it. **FeatureCloud's** app store is a catalog of
  federated apps, not a model hub. **FedScale** and **PFLlib** call themselves platform plus
  benchmark, and the runtime is what makes them products.
- **Closed rows: Apheris Networks and Rhino FCP only.** These are the ADR-005 best-in-class
  comparators. HPE Swarm Learning and Scaleout Edge are parked (see below).

**Exclusions, by neighbor.** DP, HE and MPC primitive libraries with no federation runtime are out,
and no category owns them. FL benchmarks (FL-bench, blades, VFLAIR) go to `evaluation_code` or
`benchmark_eval_data`. FL datasets (MedMNIST) go to the dataset categories. Cloud reference
architectures go to `deployment`, or are not products. Privacy-measurement tools go to
`assurance_evidence`.

**Out of scope:** volunteer and decentralized inference (Petals, exo), decentralized training
networks (hivemind, Prime Intellect, Gensyn), chain SDKs (Bittensor) and compute marketplaces. They
pool compute rather than keep data in place.

No row was scored. Each row carries identity and artifacts only, as the registry schema requires.

## Inputs swept

All fetched on 2026-09-26. The full evidence trail is on the branch
[`claude/research-federated_learning`](https://github.com/currentai-org/os-ai-map/tree/claude/research-federated_learning/research/federated_learning),
under `research/federated_learning/`. It holds the sweep (`sweep.md`), the rows (`rows.yaml`), the
fetch log (`fetch-log.tsv`, with 272 fetches and each body in `raw/Fnnnn.body` with its sha256), the
WebSearch and WebFetch log (`web-log.tsv`, 30 entries), and the two-pass independent audit
(`audit.md`). The `F` and `W` ids below point there.

- **Repository metadata** (canonical name, archived, fork, license key, last push, stars) came from
  each repository's ecosyste.ms record. **License text** came from the raw `LICENSE` file, because
  the label is not reliable: Fed-BioMed's label reads "other" over Apache-2.0 text.
- **Packages:** PyPI JSON, ecosyste.ms package records (monthly downloads), and pypistats as a
  cross-check.
- **Discovery:** the GitHub topic pages `federated-learning` (sorted by stars) and
  `federated-learning-framework`, 17 WebSearch queries, and vendor pages for the closed platforms.

**Retrieval cutoff, declared:** the first page (20 repositories) of each topic page. Results past
it were not read. That limits coverage and rejects nothing. The auditor's breadth probe found three
platforms past the cutoff (FLGo, EasyFL, iQua FLSim), and all three were triaged and accepted. So
the cutoff does miss real candidates, and the next sweep should read deeper. Hugging Face was not
swept, because the category holds software only and no federated model line surfaced in search.

## Reconciled counts

A raw signal is one distinct candidate name surfaced across the brief's leads and every discovery
source before dedup, including the three names the auditor's probe added. The brief's own
out-of-scope examples (Prime Intellect, Gensyn, Bittensor, compute marketplaces) were not re-swept
and are not counted. exo and Petals were re-fetched and are counted. Awesome-lists and survey papers
are sources, not candidates.

The four duplicates are names that turned out to be another listed name: FEDn = Scaleout Edge,
TensorOpera = FedML, Rhino Health = Rhino FCP, IBMFL = IBM Federated Learning.

```text
raw_signals       = 80
duplicate_signals = 4
unique_candidates = 76
accepted          = 36
parked            = 40

80 = 4 + 76
76 = 36 + 40
```

`pysyft` and `syfthub` count among the parked, as already mapped. With them, the category would
hold 38 products at promotion. No accepted row collides with a head product, a retired alias, an
existing registry row, or another row's artifact. `research/crosscheck.py` reported 0 findings
across 89 identity keys before this file was written.

**Fit, measured on the 36 accepted rows:** 33 open, 1 source-available and 2 closed. There are
33 independent organizations, and the largest, Google, holds 3 rows (8.3%). 22 of the 34 rows
with a repository were pushed on or after 2025-09-26. 19 declare a PyPI package with a fetched
monthly figure. Declared PyPI installs total 111,577 a month. Flower is 67.0% of that, and Flower
plus NVIDIA FLARE is 88.9% (F0046, F0050, F0108).

## Organizations and handles

Every row's organization has a `sources/organizations/` file. The 27 organizations new to the
corpus were created with `products: []`. Every one of them has its account declared in
`sources/org_handles.yaml`: the GitHub owner of the row's repository, or the homepage domain for
the two closed rows. A handle that is a project account rather than the organization's own account
(`APPFL` for Argonne, `fedbiomed` for Inria, `FedML-AI` for TensorOpera) carries a note saying so.
Organization type is `unknown` wherever the sweep's evidence did not establish an affiliation.

The slug choices follow the sweep's §9 Q7, which decisions.md left standing. `secretflow` is a new
slug and not `ant-group`, because Ant Group ownership was not fetched. `fedlearner` goes to a new
`bytedance`, not `bytedance-seed-volcano-engine`, because the repository sits under the `bytedance`
GitHub account, not a Seed or Volcano Engine one. `fate` goes to `federatedai`, not
`lf-ai-and-data`, because its README says "hosted by Linux Foundation" without naming LF AI & Data.
`openfl` and `substra` use `lf-ai-and-data`, following the `onnx` precedent for LF-hosted projects.
`federatedscope` uses `alibaba-cloud`, the corpus's slug for `alibaba/` repositories.

## Accepted candidates

Open status and license are as read from the `LICENSE` text. Last push is from the ecosyste.ms
record. The package is the declared `pypi` identifier, where one exists.

| Candidate | Slug | Org | Open status | License as read | Last push | Package | Primary source | Fetched | Evidence ids |
|---|---|---|---|---|---|---|---|---|---|
| Flower | `flower` | `flower-labs` | open | Apache-2.0 | 2026-09-21 | `flwr` | https://github.com/flwrlabs/flower | 2026-09-26 | F0001 F0079 F0102 |
| NVIDIA FLARE | `nvidia-flare` | `nvidia` | open | Apache-2.0 | 2026-09-19 | `nvflare` | https://github.com/NVIDIA/NVFlare | 2026-09-26 | F0005 F0082 F0103 W0026 |
| FedML | `fedml` | `tensoropera` | open | Apache-2.0 | 2025-10-28 | `fedml` | https://github.com/FedML-AI/FedML | 2026-09-26 | F0004 F0094 F0268 |
| OpenFL (Open Federated Learning) | `openfl` | `lf-ai-and-data` | open | Apache-2.0 | 2026-08-25 | `openfl` | https://github.com/securefederatedai/openfederatedlearning | 2026-09-26 | F0006 F0083 F0107 F0140 |
| Substra | `substra` | `lf-ai-and-data` | open | Apache-2.0 | 2024-10-14 | `substra` | https://github.com/Substra/substra | 2026-09-26 | F0007 F0052 F0084 |
| FATE (Federated AI Technology Enabler) | `fate` | `federatedai` | open | Apache-2.0 | 2024-11-19 | – | https://github.com/FederatedAI/FATE | 2026-09-26 | F0009 F0092 F0128 F0137 |
| TensorFlow Federated | `tensorflow-federated` | `google` | open | Apache-2.0 | 2026-09-19 | `tensorflow-federated` | https://github.com/google-parfait/tensorflow-federated | 2026-09-26 | F0011 F0085 F0106 F0139 |
| Federated Compute Platform | `federated-compute-platform` | `google` | open | Apache-2.0 | 2026-09-17 | – | https://github.com/google-parfait/federated-compute | 2026-09-26 | F0036 F0134 F0249 |
| FedJAX | `fedjax` | `google` | open | Apache-2.0 | 2026-08-06 | `fedjax` | https://github.com/google/fedjax | 2026-09-26 | F0035 F0076 F0269 |
| FederatedScope | `federatedscope` | `alibaba-cloud` | open | Apache-2.0 | 2024-08-10 | – | https://github.com/alibaba/FederatedScope | 2026-09-26 | F0013 F0058 F0205 F0216 F0266 |
| Fed-BioMed | `fed-biomed` | `inria` | open | Apache-2.0 | 2026-09-22 | `fedbiomed` | https://github.com/fedbiomed/fedbiomed | 2026-09-26 | F0014 F0086 F0099 |
| APPFL | `appfl` | `argonne-national-laboratory` | open | MIT | 2026-09-21 | `appfl` | https://github.com/APPFL/APPFL | 2026-09-26 | F0015 F0087 F0105 |
| SecretFlow | `secretflow` | `secretflow` | open | Apache-2.0 | 2026-04-24 | `secretflow` | https://github.com/secretflow/secretflow | 2026-09-26 | F0020 F0091 F0129 |
| vantage6 | `vantage6` | `vantage6` | open | Apache-2.0 LICENSE vs MIT on PyPI | 2026-09-19 | `vantage6` | https://github.com/vantage6/vantage6 | 2026-09-26 | F0024 F0067 F0088 F0104 |
| pfl-research | `pfl-research` | `apple` | open | Apache-2.0 | 2026-09-16 | `pfl` | https://github.com/apple/pfl-research | 2026-09-26 | F0023 F0093 F0239 |
| PFLlib | `pfllib` | `tsingz0` | open | Apache-2.0 | 2025-11-25 | – | https://github.com/TsingZ0/PFLlib | 2026-09-26 | F0021 F0135 F0250 |
| FedLab | `fedlab` | `smilelab-fl` | open | Apache-2.0 | 2025-10-20 | `fedlab` | https://github.com/SMILELab-FL/FedLab | 2026-09-26 | F0022 F0065 F0270 |
| PaddleFL | `paddlefl` | `paddlepaddle` | open | Apache-2.0 | 2023-07-26 | `paddle-fl` | https://github.com/PaddlePaddle/PaddleFL | 2026-09-26 | F0018 F0062 F0271 |
| Fedlearner | `fedlearner` | `bytedance` | open | Apache-2.0 | 2026-07-06 | – | https://github.com/bytedance/fedlearner | 2026-09-26 | F0027 F0131 F0237 |
| Plato | `plato-fl` | `tl-system` | open | Apache-2.0 | 2026-06-08 | `plato-learn` | https://github.com/TL-System/plato | 2026-09-26 | F0028 F0072 F0272 |
| Flame | `flame-fl` | `cisco` | open | Apache-2.0 | 2025-11-06 | – | https://github.com/cisco-open/flame | 2026-09-26 | F0029 F0132 F0238 |
| NEBULA | `nebula-dfl` | `cyberdatalab` | open | AGPL-3.0 | 2026-06-29 | – | https://github.com/CyberDataLab/nebula | 2026-09-26 | F0031 F0123 F0133 |
| P2PFL | `p2pfl` | `p2pfl` | open | GPL-3.0 | 2026-05-09 | `p2pfl` | https://github.com/p2pfl/p2pfl | 2026-09-26 | F0032 F0074 F0124 |
| PrimiHub | `primihub` | `primihub` | open | Apache-2.0 | 2024-12-02 | – | https://github.com/primihub/primihub | 2026-09-26 | F0026 F0136 F0251 |
| FedTree | `fedtree` | `xtra-computing` | open | Apache-2.0 | 2025-01-20 | – | https://github.com/Xtra-Computing/FedTree | 2026-09-26 | F0145 F0235 F0242 |
| FeatureCloud | `featurecloud` | `featurecloud` | open | Apache-2.0 | 2026-02-04 | – | https://github.com/FeatureCloud/FeatureCloud | 2026-09-26 | F0144 F0252 F0257 |
| MetisFL | `metisfl` | `bioint` | open | Clear BSD | 2024-06-27 | – | https://github.com/bioint/MetisFL | 2026-09-26 | F0033 F0075 F0122 |
| FedScale | `fedscale` | `symbioticlab` | open | Apache-2.0 | 2023-12-18 | `fedscale` | https://github.com/SymbioticLab/FedScale | 2026-09-26 | F0019 F0063 F0267 |
| XFL | `xfl` | `paritybit-ai` | open | Apache-2.0 | 2026-03-17 | – | https://github.com/paritybit-ai/XFL | 2026-09-26 | F0154 F0236 F0243 |
| Galaxy Federated Learning (GFL) | `galaxy-federated-learning` | `galaxylearning` | open | Apache-2.0 | 2023-01-14 | – | https://github.com/GalaxyLearning/GFL | 2026-09-26 | F0148 F0253 F0258 |
| FLGo | `flgo` | `wwzzz` | open | Apache-2.0 | 2025-06-04 | `flgo` | https://github.com/WwZzz/easyFL | 2026-09-26 | F0245 F0254 F0262 |
| EasyFL | `easyfl` | `easyfl-ai` | open | Apache-2.0 | 2023-08-23 | `easyfl` | https://github.com/EasyFL-AI/EasyFL | 2026-09-26 | F0244 F0255 F0265 |
| FLSim (iQua) | `flsim-iqua` | `iqua` | open | Apache-2.0 | 2022-04-09 | – | https://github.com/iQua/flsim | 2026-09-26 | F0247 F0256 F0261 |
| FL4Health | `fl4health` | `vector-institute` | source-available | Vector Institute License (custom) | 2026-09-21 | – | https://github.com/VectorInstitute/FL4Health | 2026-09-26 | F0030 F0073 F0109 |
| Apheris Networks | `apheris-networks` | `apheris` | closed | proprietary | – | – | https://www.apheris.com/ | 2026-09-26 | W0018 |
| Rhino Federated Computing Platform | `rhino-fcp` | `rhino-federated-computing` | closed | proprietary | – | – | https://www.rhinofcp.com/solutions/platform | 2026-09-26 | W0019 |

The rows with dormant repositories are accepted, and the pushes are dated so promotion can see
them. Dormancy is not a parking reason. Twelve repositories were last pushed before 2025-09-26:
substra, fate, federatedscope, paddlefl, primihub, fedtree, metisfl, fedscale,
galaxy-federated-learning, flgo, easyfl and flsim-iqua.

## Parked candidates

All fetched on 2026-09-26. Ids point to the evidence branch.

| # | Candidate | Reason | Source | Evidence ids |
|---|---|---|---|---|
| 1 | PySyft | already mapped (`ml_frameworks`); moves here at promotion | https://github.com/OpenMined/PySyft | F0002 F0048 |
| 2 | SyftHub | already mapped (`orchestration_agents`); moves here at promotion under the widened litmus | https://github.com/OpenMined/syft-hub-sdk | F0003 F0141 |
| 3 | Flower Datasets (`flwr-datasets`) | SKU of `flower`: a component in the same repository, not declared | https://pypi.org/project/flwr-datasets/ | F0047 F0080 F0115 |
| 4 | substrafl | SKU of `substra` | https://github.com/Substra/substrafl | F0008 F0053 |
| 5 | FATE-LLM | SKU of `fate` | https://github.com/FederatedAI/FATE-LLM | F0010 F0078 |
| 6 | FederatedScope-LLM | SKU of `federatedscope` (a branch of the same repository) | https://github.com/alibaba/FederatedScope/tree/LLM | W0003 |
| 7 | FedGraphNN | SKU of `fedml` (a FedML-AI sub-project, last pushed 2023-12-19) | https://github.com/FedML-AI/FedGraphNN | F0156 |
| 8 | Scaleout Edge (formerly FEDn) | identity unclear: the open repository is now only the client SDK of a platform that needs registration, an open satellite around a gated core. The older `fedn` package still ships | https://github.com/scaleoutsystems/scaleout-client | F0039 F0069 F0089 F0090 F0142 W0012 |
| 9 | IBM Federated Learning | unmaintained: archived, with IBMFL 2.0.1 announced as the final release | https://github.com/IBM/federated-learning-lib | F0017 W0008 |
| 10 | Microsoft FLUTE | unmaintained: archived, last pushed 2024-01-11 | https://github.com/microsoft/msrflute | F0016 |
| 11 | FLSim (facebookresearch) | unmaintained: archived, last pushed 2024-08-26 | https://github.com/facebookresearch/FLSim | F0034 |
| 12 | HPE Swarm Learning | closed long tail: the runtime needs an AutoPass license server and ships "for non-commercial and experimental use", despite Apache-2.0 text in the repository | https://github.com/HewlettPackard/swarm-learning | F0114 F0121 F0126 W0013 |
| 13 | KatherLab/swarm-learning-hpe | SKU of HPE Swarm Learning (an application repository) | https://github.com/KatherLab/swarm-learning-hpe | F0159 |
| 14 | Owkin | SKU of `substra`: Owkin's FL software is Substra, now LF-hosted | https://github.com/Substra/substra | F0111 W0004 |
| 15 | OpenFedLLM | identity unclear: a paper codebase with no releases and no package | https://github.com/rui-ye/OpenFedLLM | F0037 W0003 |
| 16 | Photon | identity unclear: a paper codebase on Flower with 0 stars | https://github.com/relogu/photon | F0040 W0010 |
| 17 | FL-bench | boundary → `evaluation_code` | https://github.com/KarhouTam/FL-bench | F0038 W0006 |
| 18 | blades | boundary → `evaluation_code` (an attack and defense benchmark suite) | https://github.com/lishenghui/blades | F0149 |
| 19 | VFLAIR | boundary → `evaluation_code` (a research library and benchmark); repository not fetched | web search | W0025 |
| 20 | HeFlwr | identity unclear: a research extension of Flower | https://github.com/QVQZZZ/HeFlwr | F0150 |
| 21 | FractalAndroid | identity unclear: an edge-compute and FL Android node; license text not read | https://github.com/Fractal-Compute-Orchestrations/FractalAndroid | F0151 |
| 22 | RIS-FL | identity unclear: simulation code for one paper | https://github.com/liuhang1994/RIS-FL | F0152 |
| 23 | FedCLS | identity unclear: paper code with no license | https://github.com/Yujun-Shi/FedCLS | F0155 |
| 24 | NErlNet | boundary: a distributed-ML research framework, not FL-specific | https://github.com/leondavi/NErlNet | F0153 |
| 25 | shaoxiongji/federated-learning | identity unclear: a tutorial implementation | https://github.com/shaoxiongji/federated-learning | F0157 |
| 26 | AshwinRJ/Federated-Learning-PyTorch | identity unclear: a tutorial implementation of the FedAvg paper | https://github.com/AshwinRJ/Federated-Learning-PyTorch | F0158 |
| 27 | MedMNIST | boundary: a biomedical dataset, not FL software | https://github.com/topics/federated-learning?o=desc&s=stars | W0005 |
| 28 | GoogleCloudPlatform/federated-learning | boundary → `deployment` (a cloud reference architecture) | https://github.com/GoogleCloudPlatform/federated-learning | F0146 W0024 |
| 29 | Petals | boundary: out of scope (volunteer inference) | https://github.com/bigscience-workshop/petals | F0160 F0163 |
| 30 | exo | boundary: out of scope (local and distributed inference) | https://github.com/exo-explore/exo | F0161 F0165 |
| 31 | hivemind | boundary: out of scope (decentralized training) | https://github.com/learning-at-home/hivemind | F0162 F0164 |
| 32 | ReFedEz | no addressable artifact: a search snippet only | web search | W0001 W0014 |
| 33 | Fedstellar | identity unclear: a search snippet only, possibly NEBULA's predecessor | web search | W0008 |
| 34 | FedLess | no addressable artifact: named in a search snippet | web search | W0014 |
| 35 | OpenFed | no addressable artifact: named in a search snippet | web search | W0014 |
| 36 | FedCampus | no addressable artifact: a paper mention only | web search | W0015 |
| 37 | WebFed | no addressable artifact: a paper mention only | web search | W0015 |
| 38 | FLaaS | no addressable artifact: a paper only | https://arxiv.org/abs/2206.10963 | W0015 |
| 39 | FS-REAL | no addressable artifact: a paper mention only | web search | W0015 |
| 40 | FLINT | no addressable artifact: a paper mention only | web search | W0015 |

## Identity notes for promotion

- **`flower`** declares `flwr` only. `flwr-datasets` (the same repository) is a component. Its
  installs are Flower's own users, so it is not a second instrument.
- **`tensorflow-federated`** lives at `google-parfait/tensorflow-federated`. The old
  `tensorflow/federated` name does not resolve on ecosyste.ms (F0012), and the canonical repository
  comes from PyPI's `project_urls` (F0085).
- **`openfl`**: PyPI's URL `securefederatedai/openfl` resolves to
  `securefederatedai/openfederatedlearning` (W0027). Add `end_of_life` when a date is announced or
  the repository is archived.
- **`federatedscope`** declares no package, because `federatedscope` returns 404 on pypi.org (F0205,
  F0216), although ecosyste.ms still lists it. Its LICENSE is Apache-2.0 followed by bundled
  third-party notices, mostly MIT (F0266), so read past the first page.
- **`fate`**: `fate-client` is a client, not the product, so it is not declared.
- **`vantage6`** declares `vantage6`. `vantage6-client` is not declared.
- **`featurecloud`**: PyPI `featurecloud` points to `FeatureCloud/app-template` (F0147), so it is
  not declared. **`metisfl`**: PyPI `metisfl` points to `nevronai/metisfl` (F0075), so it is not
  declared. **`fl4health`**: the PyPI release carries no repository URL (F0073), so it is not
  declared.
- **`flgo`**: the repository is `WwZzz/easyFL`, and PyPI `flgo` names it (F0262). It is distinct from
  **`easyfl`**, which is `EasyFL-AI/EasyFL` (F0265). **`flsim-iqua`** is distinct from
  facebookresearch's archived FLSim.
- **Slug suffixes.** `plato-fl`, `flame-fl` and `nebula-dfl` carry one because the bare names are
  generic words.
- **First tranche.** Leave FedML and Substra out of it (decisions.md, Q1a). The tranche should cover
  the sub-types (simulation, research multi-party, production cross-silo, cross-device or HPC, and
  privacy-computing platforms) and include both closed comparators.

## The volunteer-inference insight

The brief put volunteer inference and decentralized training out of scope. Today's numbers support
that as a finding, not just a boundary. Petals has 10,586 stars but was last pushed 2024-09-07,
has shipped no release since 2023-09-06, and reads 202 installs a month (F0160, F0163), down from
452 on 2026-09-14 (W0028). hivemind reads 5,784 a month, with a last release on 2026-01-03
(F0164). exo has 45,525 stars (F0161), but its PyPI name belongs to an unrelated project (F0165),
so it has no usage instrument at all. The population that pools compute is either fading
(Petals) or unmeasurable (exo). Neither shares a quantity with frameworks that keep data in place.
It is worth an insight line on the map when the category publishes.

## Decisions recorded on the draft

Applied from the 2026-09-26 decision record, which rules on all nine sweeps:

1. Create preliminary. The category passes the fit test: at least 15 accepted, at least 6 orgs
   with none above 30%, one capability quantity (federation reach), and contested products
   assigned.
2. Model components → Pipeline code, after `finetuning_code`. Weights 0.5 / 0.5.
   `extends: software`.
3. `pysyft` and `syfthub` move in at promotion. The litmus widens to "training, evaluation or
   querying".
4. FedML and Substra are tail rows, not in the first promotion tranche. Flower is one product.
   Apheris and Rhino FCP are the only closed rows.
5. Where the decision record is silent, the sweep's recommendations stand: privacy-computing
   platforms are in (Q4), Scaleout Edge is parked (Q6), org slugs follow Q7, OpenFL stays a tail
   row (Q9), and `flsim-iqua` stays a tail row flagged dormant (Q11).

## Open items for the maintainer

- **License rulings** go to the one shared "license rulings" issue and are never settled in this
  PR. Products carrying one are deferred at promotion.
  - **Clear BSD** (`metisfl`): expressly grants no patent rights (F0122), and the software ladder
    does not tier it.
  - **Vector Institute License** (`fl4health`): academic, sponsor and partner use only, with no
    right to sell (F0109). PyPI says Apache-2.0 (F0073). The sweep recommends scoring on the LICENSE
    text, as source-available.
  - **vantage6**: the LICENSE file is Apache-2.0 (F0104), but PyPI and ecosyste.ms say MIT (F0088,
    F0067). The recommendation is to score on the LICENSE text and record the other label in the
    product's `comments`.
- **The litmus widening** is a proposal in the decision record. If the maintainer keeps the
  training-only test, `syfthub` stays in `orchestration_agents` and the category's `comments` need
  their first paragraph rewritten.
- **Org affiliations** left `unknown`: whether `secretflow` is Ant Group's, and whether `fate`'s
  "Linux Foundation" host is LF AI & Data. Each needs a fetch before its org is merged into an
  existing record.
- **Capability rungs.** The federation-reach ladder in `scoring_recipe.note` is a sketch. Only
  FedJAX, pfl-research, PFLlib, Substra, vantage6, FATE, TensorFlow Federated, the Federated
  Compute Platform and NVIDIA FLARE have a cited rung. Flower's secure-aggregation and DP features
  were not fetched.
- **Coverage.** The topic pages past their first 20 results, and a Hugging Face pass if a
  federated model line ever appears.
