# Model hubs & registries sweep — 2026-09-26

Brief 4, issue #601, proposed slug `model_hubs`. Every fact below carries a fetch id: `Fnnnn`
rows are in `fetch-log.tsv` (bodies in `raw/`), and `Wnnnn` rows are in `web-log.tsv`
(WebSearch/WebFetch, with an excerpt). A number with no id is not a claim this sweep makes.

## 1. Verdict

**GO-WITH-CHANGES.** Supply is not the problem the brief expected. 18 distinct registry surfaces
survive the litmus with live evidence: 8 closed hosted hubs and catalogs, 8 open ones and 2
source-available ones, from 18 distinct org slugs (17 independent parents, since Kaggle is Google's, W0072). What needs changing is scope. The raw
signal mixes four populations that answer the litmus in different ways: (a) public hosted hubs
(Hugging Face Hub, ModelScope, Ollama Library, Civitai, Kaggle Models); (b) cloud and vendor
catalogs (Model Garden, Foundry Models, JumpStart, NGC, Qualcomm AI Hub); (c) self-hostable hub
and registry software (CSGHub, MatrixHub, Kubeflow Hub); (d) domain model zoos (MONAI, BioImage,
Kipoi, OpenML, PyTorch Hub). One capability quantity (§4) can order all four. Two things have to
be ruled before seeding. First, whether OCI packaging and registry tooling (KitOps, ModelPack,
ORAS, Harbor) is in scope; I recommend it stays out except as a question on Harbor. Second, how
many closed regional hubs ADR-005's best-in-class test admits. Adoption has no shared instrument.
Only one row has a download channel it owns, so the category has to be weighted toward capability
or read platform-native counters (§2, §9 Q5).

## 2. Fit metrics (computed from section 6)

- accepted candidates: **18** (open: 8, open-weights: 0, source-available: 2, closed: 8)
  - open: civitai, csghub, matrixhub, kubeflow-hub, qualcomm-ai-hub-models, monai-model-zoo,
    kipoi, openml
  - source-available (public code, no license file found): pytorch-hub, bioimage-model-zoo
  - closed: huggingface-hub-platform, modelscope, ollama-library, kaggle-models,
    nvidia-ngc-catalog, vertex-ai-model-garden, azure-ai-foundry-models, sagemaker-jumpstart
- independent organizations: **18 distinct org slugs, 17 independent parents**. Kaggle has been
  Google's since 2017 (W0072), so Google holds `kaggle-models` and `vertex-ai-model-garden`.
  Largest parent's share is **11.1% (Google, 2 of 18)**; every other parent holds one row.
- candidates active in the last 12 months (since 2025-09-26): **17 of 18**. For repo-backed rows
  this means a last push on or after 2025-09-26. For hosted rows it means a live listing, or an
  operator document dated within the window (see 6b). The one exception is `pytorch-hub`: its last
  push was 2024-04-15 (F0010) and its page is dated 2025-01-16 (W0049).
- candidates with a usage instrument on a **declared artifact**: **1** (`qualcomm-ai-hub-models`,
  PyPI `qai-hub-models`, 31,663 in the last month, F0083). The rest break down as follows:
  - **platform-native counters** that can be read live but have no registry channel: 5.
    Hugging Face Hub model and dataset totals (F0063/F0064), ModelScope per-model downloads and
    total (F0115), Ollama pulls (W0018), Civitai per-model downloads (F0067/F0127), and the NGC
    catalog count (W0023).
  - **client-library downloads** that are proxies and are not declared (see 5 and Q5): 8.
    huggingface-hub 225.5M (F0069), modelscope 3.47M (F0070), kagglehub 1.57M (F0071),
    ngcsdk 292k (F0082), openml 73k (F0079), model-registry 15k (F0086),
    bioimageio.core 11.9k (F0080), csghub-sdk 1.0k (F0073).
  - stars only: matrixhub, monai-model-zoo, kipoi, pytorch-hub. Model count only: the three
    hyperscaler catalogs.
- retrieval cutoff: there is no numeric cutoff. Coverage limit: many hub sites render in
  JavaScript, and WebFetch returned only the title for ModelScope's home page, Kaggle, OpenXLab,
  WiseModel, OpenML and bioimage.io (W0017, W0020, W0022, W0024, W0027, W0032, W0034, W0041,
  W0042).
  Where an API existed I used it instead (F0067, F0115, F0120). GitHub API and ungh.cc returned
  403/429 for several repos (F0024–F0035). That is an access limit, not a finding.

## 3. Boundary

- **Definition.** A platform or self-hostable service whose product is hosting, indexing and
  distributing model artifacts (and optionally datasets) from many publishers, as a registry
  other tools pull from by name.
- **Litmus.** Can a client fetch a named, versioned model artifact from it (by API, git or
  registry protocol), where the thing being sold or run is the registry itself rather than the
  runtime, UI or inference API in front of it?
- **Explicit exclusions:**
  - *Runtimes that pull from a registry* → `deployment` / `inference_code`. `ollama` (the
    runner), `localai` (its model gallery is a feature), and Docker Model Runner (W0009).
  - *Chat or desktop apps with a model browser* → `ui_api`. The `lm-studio` catalog downloads
    from Hugging Face (W0063), and its models live under the `lmstudio-community` HF org (F0088).
  - *Hosted inference APIs with a model gallery* → `deployment`. Replicate runs models in its
    cloud ("models that you can run in the cloud", W0025).
  - *Client libraries for a hub* → `ml_frameworks`. `huggingface-hub` stays per the #601 ruling (W0073),
    and kagglehub, the modelscope library, ngcsdk and csghub-sdk go the same way.
  - *Experiment tracking with a registry tab* → `telemetry_observability` / `ml_orchestration`.
    MLflow Model Registry is part of the head product `mlflow`.
  - *Versioned data layers and data catalogs* → `storage`. `oxen`, `dvc`, `lakefs`, Unity
    Catalog (F0008) and DagsHub (W0062).
  - *Packaging formats and generic registry clients* → out of taxonomy, recommend not here.
    KitOps (F0004), ModelPack (F0005/W0058) and ORAS (F0039).
  - *General research repositories* → out. Zenodo (F0022).
  - *Agent skill and MCP registries* → `agent_protocols` (`mcp-registry`), not models.
- **Contested products:**

| product | where it is now | recommendation | reason |
|---|---|---|---|
| huggingface-hub (Python client) | ml_frameworks (head) | stay | #601 comment 2026-09-24 ruled it the client (W0073). The platform becomes the new row `huggingface-hub-platform`. |
| Hugging Face Hub (platform) | absent | move here (new row) | It is the reference registry: 3,097,949 models and 1,064,437 datasets on 2026-09-26 (F0063, F0064). |
| spaces | deployment (head) | stay | Spaces hosts apps, not model artifacts. It is a separate HF surface under ADR-005 test 1. |
| ollama | deployment (head) | stay; add `ollama-library` here | The runner and the registry are separate products. `ollama push` to ollama.com (F0112) is the registry surface. |
| lm-studio | ui_api (head) | stay; do not add a catalog row | Its catalog is a curated view of Hugging Face (W0063, F0088). Parked. |
| mlflow (Model Registry tab) | telemetry_observability (head) | stay | It is one open product. Carving out the registry tab would split one repo's adoption across two rows. |
| kubeflow-hub | absent (kubeflow org in ml_orchestration) | here | It is a model registry and catalog (F0111), not a scheduler. Overlaps `ml_orchestration` members by org only. |
| localai model gallery | inference_code (`localai`, head) | stay | The gallery is a feature of the runtime. |
| harbor | absent | open question (Q3) | A general OCI registry. Since 2.15 it presents models as first-class artifacts (W0056). |
| unity-catalog | absent | → storage (flag for the storage owner) | "Open, Multi-modal Catalog for Data & AI" (F0008) is a governance catalog, not a model hub. |
| qualcomm-ai-hub-models | absent (qualcomm has aimet in compilers) | here | A vendor model catalog (235 models / 541 variants, W0066). Flag for the sibling `datacenter_accelerators` / edge sweeps only as an org overlap. |
| Civitai | absent | here | Image-model hub. Sibling `media_generation` parks LoRAs/checkpoints *as a class*. The hub hosting them belongs here, not there. Flag for that session. |
| MONAI / BioImage / Kipoi zoos | absent | here, or park if Q4 excludes domain zoos | Domain registries. Sibling `classic_ml_cv` may claim vision backbones, but not their zoos. Flag. |

## 4. Capability quantity

**Registry scope**: how much of the publish, version, discover and pull cycle the surface
provides, and for how many artifact kinds. Scale is left out; that is adoption. This quantity
works for hosted hubs and self-hostable software alike, because it describes what the registry
does, not how big one deployment is.

1. **Index only.** It points at weights hosted elsewhere and has no storage of its own.
   `pytorch-hub` fits here: submissions are a `hubconf.py` in the publisher's GitHub repo, merged
   by PR (F0113).
2. **Operator-curated zoo.** It hosts weights, but only the operator (or an accepted PR)
   publishes. Examples: `nvidia-ngc-catalog` (W0023), `qualcomm-ai-hub-models` (W0066),
   `monai-model-zoo` (F0020), `kipoi` (F0126), `bioimage-model-zoo` (W0045).
3. **Curated multi-provider catalog with deploy integration.** Third-party providers are listed
   by the operator and deployed through it. Examples: `vertex-ai-model-garden` (W0043),
   `azure-ai-foundry-models` (W0036), `sagemaker-jumpstart` (W0068).
4. **Open-upload registry for one artifact class, versioned, with a pull API.** Examples:
   `ollama-library` (F0112), `civitai` (F0108, F0067), `kaggle-models` (F0120), `kubeflow-hub`
   (F0111), `matrixhub` (F0110), `openml` (W0069).
5. **Open-upload, git-versioned, multi-artifact hub** (models, datasets and apps), with a
   programmatic API that other tools treat as an endpoint. Examples: `csghub` (on-prem, "a
   private, on-premise version of Huggingface", F0109) and `modelscope` (F0115). **Top-rung
   anchor: `huggingface-hub-platform`** (F0063/F0064). Both self-hosted replacements define
   themselves against it (F0109, F0110).

Rungs 4 and 5 both hold one hosted and one self-hostable product, which answers the brief's
question: they can share the quantity. They cannot share an adoption instrument (see Q5).

## 5. Scoring ladder inputs

- **Shared ladder:** every row is `type: software` → the **software** ladder. No row needs the
  model, pretrained, dataset or hardware ladder. The hosted rows are closed services, so the
  openness read is "closed service; server source not checked". Where a vendor publishes an open client, that
  client is a satellite (identity.md, "An open satellite around a closed core"). It must not lift
  the platform's openness: `huggingface_hub` Apache-2.0 (F0069), `modelscope` library Apache-2.0
  (F0056), `kagglehub` Apache-2.0 (F0095), `ollama` runner, `ngcsdk`.
- **License strings met**, with the text read where marked:
  - **Apache-2.0** (text read): civitai/civitai (F0052), OpenCSGs/csghub (F0049),
    matrixhub-ai/matrixhub (F0050), kitops-ml/kitops (F0051), kubeflow/hub (F0053),
    onnx/models (F0054), modelscope/modelscope (F0056), Project-MONAI/model-zoo (F0059),
    unitycatalog/unitycatalog (F0061), goharbor/harbor (F0062); kagglehub (PyPI metadata, F0095).
    Label only, text not read: modelpack/model-spec (F0005), oras-project/oras (F0039),
    openvinotoolkit/open_model_zoo (F0017; its README also says Apache-2.0, F0116),
    tensorflow/hub (F0018), OpenCSGs/csghub-server (F0048), replicate/cog (F0041).
  - **BSD-3-Clause** (text read): openml/OpenML (F0055, "Copyright (c) 2014-2021, OpenML") and
    qualcomm/ai-hub-models (F0057; plain BSD-3 text behind a Qualcomm copyright line, no added
    clause).
  - **MIT** (text read): kipoi/kipoi (F0118). Label only: kipoi/models (F0126), mudler/LocalAI
    (F0023), DagsHub/client (F0043), lmstudio-ai/lms (F0042).
  - **GPL-2.0** (label only, text not read): zenodo/zenodo (F0022). Parked, so it doesn't matter
    here.
  - **"other"** (label only): openml/openml-python (F0013), the client. Not declared.
  - **No license file found** (flag: needs a maintainer tier call):
    - pytorch/hub: LICENSE, LICENSE.md, LICENSE.txt and COPYING all return 404 (F0058, F0119,
      F0122, F0123); ecosyste.ms license null (F0010).
    - bioimage-io/bioimage.io: LICENSE, LICENSE.md and LICENSE.txt return 404 (F0117, F0124,
      F0125); license null (F0114).
    - bioimage-io/collection: LICENSE 404 (F0060).
  - **Service/content terms, unusual:** OpenML says its "service is free to use under the CC-BY
    licence, while the code of the platform itself is released under the Apache licence"
    (W0046). The Apache claim conflicts with the BSD-3 text in openml/OpenML (F0055). Flag it:
    read the repo text, not the docs sentence. The hosted platforms' terms of service were not
    fetched.

## 6. Accepted candidates

### 6a. Registry rows

See `rows.yaml` (validated against `docs/schemas/registry.schema.json`, "ok"). The same content:

```yaml
category: model_hubs
products:
  - {slug: huggingface-hub-platform, display_name: Hugging Face Hub, type: software, org: hugging-face, homepage: https://huggingface.co/models}
  - {slug: modelscope, display_name: ModelScope, type: software, org: modelscope-alibaba, homepage: https://www.modelscope.cn/models}
  - {slug: ollama-library, display_name: Ollama Library, type: software, org: ollama, homepage: https://ollama.com/library}
  - {slug: civitai, display_name: Civitai, type: software, org: civitai, github: civitai/civitai, homepage: https://civitai.com/}
  - {slug: kaggle-models, display_name: Kaggle Models, type: software, org: kaggle, homepage: https://www.kaggle.com/models}
  - {slug: nvidia-ngc-catalog, display_name: NVIDIA NGC Catalog, type: software, org: nvidia, homepage: https://catalog.ngc.nvidia.com/models}
  - {slug: vertex-ai-model-garden, display_name: Vertex AI Model Garden, type: software, org: google-cloud, homepage: https://cloud.google.com/model-garden}
  - {slug: azure-ai-foundry-models, display_name: Microsoft Foundry Models (model catalog), type: software, org: microsoft-azure, homepage: https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/foundry-models-overview}
  - {slug: sagemaker-jumpstart, display_name: Amazon SageMaker JumpStart, type: software, org: amazon-web-services, homepage: https://docs.aws.amazon.com/sagemaker/latest/dg/studio-jumpstart.html}
  - {slug: csghub, display_name: CSGHub, type: software, org: opencsg, github: OpenCSGs/csghub, homepage: https://opencsg.com/csghub}
  - {slug: matrixhub, display_name: MatrixHub, type: software, org: daocloud, github: matrixhub-ai/matrixhub}
  - {slug: kubeflow-hub, display_name: Kubeflow Hub (Model Registry), type: software, org: kubeflow, github: kubeflow/hub}
  - {slug: qualcomm-ai-hub-models, display_name: Qualcomm AI Hub Models, type: software, org: qualcomm, github: qualcomm/ai-hub-models, pypi: qai-hub-models, homepage: https://aihub.qualcomm.com/models}
  - {slug: pytorch-hub, display_name: PyTorch Hub, type: software, org: pytorch-foundation, github: pytorch/hub, homepage: https://pytorch.org/hub/}
  - {slug: monai-model-zoo, display_name: MONAI Model Zoo, type: software, org: project-monai, github: Project-MONAI/model-zoo}
  - {slug: bioimage-model-zoo, display_name: BioImage Model Zoo, type: software, org: bioimage-io, github: bioimage-io/bioimage.io, homepage: https://bioimage.io/}
  - {slug: kipoi, display_name: Kipoi, type: software, org: kipoi, github: kipoi/models}
  - {slug: openml, display_name: OpenML, type: software, org: openml, github: openml/OpenML, homepage: https://www.openml.org/}
```

Orgs reused from the corpus: hugging-face, modelscope-alibaba, ollama, nvidia, google-cloud,
microsoft-azure, amazon-web-services, kubeflow, qualcomm, pytorch-foundation. New org slugs:
civitai, kaggle, opencsg, daocloud, project-monai, bioimage-io, kipoi, openml. None of the 18
slugs, and none of their github/pypi artifacts, match `corpus-index.tsv`, `sources/registry/` or
`sources/resolution_ledger.yaml` (checked 2026-09-26).

### 6b. Evidence table

"push" = GitHub last push per ecosyste.ms; "release" = the first entry ecosyste.ms returns from
its releases endpoint.

| slug | open status | license(s) + source | archived/fork | last push | last release | adoption signal + value + source | member surfaces/SKUs | org handle | notes |
|---|---|---|---|---|---|---|---|---|---|
| huggingface-hub-platform | closed | server source not checked. Client `huggingface/huggingface_hub` Apache-2.0 is a satellite and is not declared (F0069) | n/a | n/a (hub-docs pushed 2026-09-26, F0027) | n/a | 3,097,949 public models; 1,064,437 datasets on 2026-09-26 (F0063, F0064). Community post: 3,012,377 on 2026-08-21 (W0016) | Models, Datasets (Spaces is a separate head product, `spaces`) | huggingface | Slug chosen to avoid confusion with head `huggingface-hub` (client). See Q1. |
| modelscope | closed | hub server source not checked. `modelscope/modelscope` library Apache-2.0 (F0056), a satellite | library: false/false (F0014) | library 2026-09-24 (F0014) | PyPI latest release 2026-09-15 (F0070); v1.40.1 (F0094). GitHub release list first entry v1.38.0, 2026-07-03 (F0103) | 259,500 models total via openapi, 2026-09-26 (F0115); top model Qwen/Qwen-Image-2.1, 28,631 downloads (F0115). Client PyPI `modelscope` 3,465,915/month (F0070), a proxy | modelscope.cn; modelscope.ai titled "Home - ModelScope" (W0020). That it is the international edition is inferred from the title, not fetched | modelscope | Use the F0115 total; no other count was fetched. |
| ollama-library | closed | registry server source not checked. `ollama` runner is a head product in deployment | n/a | n/a | n/a | llama3.1 119.9M pulls; deepseek-r1 93.2M; nomic-embed-text 87.2M (W0018) | ollama.com/library, user namespaces via `ollama push` (F0112) | ollama | The registry is a separate surface from the runner (ADR-005 test 1). |
| civitai | open | Apache-2.0 text (F0052); README "License: Apache License 2.0" (F0108) | false/false (F0009) | 2026-09-21 (F0009) | none listed (F0106) | 7,252 stars (F0009). Per-model downloads via API: Realistic Vision V6.0 B1 2,330,029 (F0127); Pony Diffusion V6 XL 1,093,783 (F0067). civitai-py 11,144/month (F0076) is a stale client, last release 2024-06-24 | civitai.com (W0021) | civitai | README: "a platform where people can share their stable diffusion models" (F0108). Whether the live site runs this code was not verified. Q6. |
| kaggle-models | closed | platform source not checked. `Kaggle/kagglehub` Apache-2.0 (F0095), a satellite | client false/false (F0016) | client 2026-08-05 (F0016) | client 1.0.2 (F0095) | Public models API responds; totalResults 10000 is a page cap, a lower bound (F0120). kagglehub 1,573,202/month (F0071), a proxy | TF Hub merged in: "links to tfhub.dev will redirect" (W0012) | Kaggle | `tensorflow-hub` parked as a retired alias of this row. |
| nvidia-ngc-catalog | closed | platform source not checked | n/a | n/a | n/a | 903 models, 1,233 containers, 301 Helm charts (W0023). ngcsdk 292,132/month (F0082), a proxy | models, containers, Helm charts, collections (W0023) | nvidia | The NIM API catalog was not separately verified. |
| vertex-ai-model-garden | closed | platform source not checked | n/a | n/a | n/a | "200+ models" (W0043, search snippet; direct fetch did not complete, W0035, W0039, W0047) | Model Garden only (not Vertex AI) | google-cloud | Search shows the rebrand "Gemini Enterprise Agent Platform (formerly Vertex AI)" (W0043). The display name may need to follow it. Q7. |
| azure-ai-foundry-models | closed | platform source not checked | n/a | n/a | n/a | "The catalog includes over 10,000 models, with approximately 50 new models published each month" (W0036, doc dated 2026-07-28) | Foundry Models catalog; backed by Azure ML registries (W0036) | microsoft-azure | Surface only. Observability is already `azure-ai-foundry-observability`. |
| sagemaker-jumpstart | closed | platform source not checked | n/a | n/a | n/a | model count not published. "On 3/13/2026, we delisted a few models" shows live curation (W0068) | SageMakerPublicHub, Private/Curated Hubs (W0068) | amazon-web-services | Bedrock Marketplace parked in favor of this row. Q2. |
| csghub | open | Apache-2.0 text (F0049). Backend csghub-server Apache-2.0 label (F0048) | false/false (F0047) | 2026-09-19 (F0047) | v2.5.0-ce, 2026-09-16 (F0098) | 4,111 stars (F0047). csghub-sdk 1,046/month (F0073), a proxy | CE on-prem + OpenCSG SaaS (W0015, F0109) | OpenCSGs | Canonical owner is `OpenCSGs`; `OpenCSG/csghub` returns 404 (F0036, W0013). |
| matrixhub | open | Apache-2.0 text (F0050) | false/false (F0003) | 2026-09-22 (F0003) | v0.2.0, 2026-09-18 (F0096) | 352 stars (F0003); repo created 2026-01-08 (F0003) | single product | matrixhub-ai | Submitted to CNCF Sandbox by Shanghai DaoCloud, 2026-07-30, in voting (W0057), hence org `daocloud`. |
| kubeflow-hub | open | Apache-2.0 text (F0053) | false/false (F0045) | 2026-09-22 (F0045) | v0.3.17, 2026-09-21 (F0099) | 184 stars (F0045). PyPI `model-registry` client 15,044/month, repo kubeflow/hub (F0086), not declared | Model Registry + Catalog (F0111) | kubeflow | Renamed from kubeflow/model-registry (previous_names, F0045; W0014). README says "formerly known as Model Registry", alpha (F0111). |
| qualcomm-ai-hub-models | open | BSD-3-Clause text behind Qualcomm copyright (F0057) | false/false (F0015) | 2026-09-19 (F0015) | PyPI 0.63.0, 2026-09-23 (F0131); GitHub release v0.62.2, 2026-09-11 (F0101) | PyPI qai-hub-models 31,663/month (F0083); 235 models / 541 variants (W0066). HF org `qualcomm` downloads small (F0090) | catalog + compile service (the service is not in scope) | qualcomm | PyPI repository_url `quic/ai-hub-models` (F0083) is a previous name of `qualcomm/ai-hub-models`: ecosyste.ms previous_names lists quic/ai-stack-models → quic/ai-hub-models → qualcomm/ai-hub-models (F0015). Package homepage is the product page. |
| pytorch-hub | source-available (no license file) | none found (F0058, F0119, F0122, F0123); license null (F0010) | false/false (F0010) | 2024-04-15 (F0010) | none: releases endpoint returns [] (F0129) | 1,435 stars (F0010) | index of hubconf.py entries in publisher repos (F0113) | pytorch | Dormant. Page dated 2025-01-16, "beta release" (W0049). |
| monai-model-zoo | open | Apache-2.0 text (F0059) | false/false (F0020) | 2026-07-08 (F0020) | model_zoo_bundle_data, 2024-08-21 (F0104) | 340 stars (F0020) | MONAI Bundle-format models (F0020) | Project-MONAI | Medical imaging domain zoo. |
| bioimage-model-zoo | source-available (no license file) | none found in bioimage.io (F0117, F0124, F0125) or collection (F0060) | false/false (F0114) | 2026-09-13 (F0114) | none: releases endpoint returns [] (F0130) | 12 stars (F0114); bioimageio.core 11,856/month (F0080), a proxy | website repo + collection repo (F0019) | bioimage-io | "community-driven, fully open resource" (W0045) conflicts with no license file. Q9. |
| kipoi | open | MIT (label kipoi/models F0126; text of kipoi/kipoi F0118) | false/false (F0126) | 2025-12-17 (F0126) | none fetched | 173 stars (F0126) | zoo repo `kipoi/models` + API `kipoi/kipoi` (F0021) | kipoi | Genomics domain zoo. Active inside the 12-month window by 9 months. |
| openml | open | BSD-3-Clause text (F0055); docs claim Apache for code and CC-BY for the service (W0046) | false/false (F0012) | 2026-08-06 (F0012) | client v0.15.1, 2025-01-25 (F0107) | 751 stars (F0012). openml PyPI client 73,119/month (F0079), a proxy | datasets, tasks, flows, runs (W0046, W0069) | openml | Models ("flows") are secondary to datasets and benchmarks. Could be contested by `benchmark_eval_data`. Q4. |

### 6c. Source list

Every URL behind sections 6–7, with its UTC fetch time, is in `fetch-log.tsv` (F0001–F0131, all
2026-09-26) and `web-log.tsv` (W0001–W0073, all 2026-09-26). An index of the ids cited above is
appended at the end of this file (generated from the logs).

## 7. Parked candidates

| name | reason | source | fetch date |
|---|---|---|---|
| Docker Hub `ai/` namespace | closed long-tail (ADR-005). 110 repos; gemma4 1M+ pulls (W0038). Also Q3 | W0038, W0009 | 2026-09-26 |
| Modelers (魔乐社区) | closed long-tail regional hub. 5,702 models in a Jan-2025 figure (W0028). Home page 503 (W0026). Operator unconfirmed on the fetched page (W0031) | W0028, W0031 | 2026-09-26 |
| WiseModel (始智AI) | closed long-tail regional hub. Launched 2023-09-04 (W0029). Home page title only (W0027, W0032) | W0029 | 2026-09-26 |
| OpenXLab 浦源 model center | closed long-tail regional hub (Shanghai AI Lab; 2,000+ models, W0071). PyPI `openxlab` shows 4,780,663/month (F0074) with repository `github.com/xxx/xxxx` (F0093), a number that looks implausible for a placeholder-repo package. Parked, not trusted | W0071, F0074, F0093 | 2026-09-26 |
| Amazon Bedrock Marketplace | closed; overlaps `sagemaker-jumpstart` (it deploys "to an endpoint managed by SageMaker AI", W0037). Q2 | W0037 | 2026-09-26 |
| Replicate | boundary → deployment (inference API; "models that you can run in the cloud", W0025) | W0025, F0041, F0084 | 2026-09-26 |
| Tensor.art | closed long-tail image hub; page 403 (W0060) | W0005, W0060 | 2026-09-26 |
| SeaArt | closed long-tail image hub | W0005 | 2026-09-26 |
| LiblibAI | closed long-tail image hub | W0005, W0061 | 2026-09-26 |
| LM Studio catalog / Hub | not a registry: downloads from Hugging Face (W0063), models under the `lmstudio-community` HF org (F0088). The app is head `lm-studio` | W0019, W0063, W0064, F0088 | 2026-09-26 |
| GitHub Models | retired 2026-07-30: "playground, model catalog, inference API ... no longer available" (W0067) | W0007, W0065, W0067 | 2026-09-26 |
| ONNX Model Zoo | superseded: "preserving ... for historical purposes only", moved to HF `onnxmodelzoo` (W0050, F0089) | W0050, F0011, F0054 | 2026-09-26 |
| TensorFlow Hub | retired alias of `kaggle-models` (W0012). tensorflow/hub last push 2025-01-17 (F0018) | W0012, F0018 | 2026-09-26 |
| OpenVINO Open Model Zoo | superseded: "Open Model Zoo is in maintenance mode as a source of models" (F0116) | F0017, F0116 | 2026-09-26 |
| GitCode AI | identity unclear: ai.gitcode.com 302 → gitcode.com (W0033) | W0030, W0033 | 2026-09-26 |
| 模力方舟 Moark (formerly Gitee AI) | identity unclear / serving-first. Rendered "共 0 个公开模型" (W0059); search describes serverless API and 70+ models (W0054) | W0054, W0059 | 2026-09-26 |
| PaddleHub | identity unclear: ecosyste.ms lists `PaddlePaddle/PaddleHub` created 2025-06-25 with 82 stars (F0040), which doesn't fit a long-lived project. The number bothered me, so parked | F0040 | 2026-09-26 |
| Jozu Hub | closed long-tail SaaS ModelKit registry (W0044). jozu.com/hub and docs return 404 (W0040, W0048) | W0044 | 2026-09-26 |
| DagsHub | closed long-tail; boundary → storage/telemetry ("manage AI data & models", W0062) | W0001, W0062, F0043 | 2026-09-26 |
| KitOps | boundary: a packaging CLI, not a place models live (F0004, W0004). Q3 | F0004, F0051, F0097 | 2026-09-26 |
| ModelPack | boundary: a format spec (CNCF Sandbox 2025-05-13, W0058) | F0005, W0058 | 2026-09-26 |
| ORAS | boundary: OCI registry client (F0039) | F0039, F0081 | 2026-09-26 |
| Harbor | boundary: general-purpose OCI registry, though 2.15 displays models as first-class artifacts (W0056). Q3 | F0006, F0062, F0100, W0053, W0056 | 2026-09-26 |
| Unity Catalog | boundary → storage (data & AI governance catalog, F0008) | F0008, F0061, F0105 | 2026-09-26 |
| Zenodo | boundary: general research repository, not ML-specific (F0022) | F0022 | 2026-09-26 |
| hf-mirror.com | mirror of the HF Hub, not a separate registry (W0030) | W0030 | 2026-09-26 |
| Melious | boundary → deployment/ui_api (inference API over 60+ models, W0052) | W0052 | 2026-09-26 |
| EULLM | boundary: sovereign LLM platform, not a registry (W0052) | W0052 | 2026-09-26 |
| Docker Model Runner | boundary → deployment/inference_code (the runtime; W0009) | W0009 | 2026-09-26 |

## 8. Reconciled counts

Duplicate signals (31). Each one was caught by the index or by self-dedup:
- Already mapped, 5: huggingface-hub (client; brief), ollama (runner; brief), lm-studio (the app;
  brief), mlflow (brief), localai (F0023).
- Self-dedup, 26:
  - second artifacts of one product (25): csghub-server (F0048), csghub-sdk (F0073), kagglehub
    (F0071), the modelscope library (F0014/F0070), huggingface/hub-docs (F0027),
    openml-python (F0013/F0079), bioimage-io/collection (F0019), bioimageio.core (F0080),
    civitai-py (F0076), DagsHub/client (F0043), lmstudio-ai/lms (F0042), lmstudio PyPI
    (F0078), replicate/cog (F0041), replicate PyPI (F0084), ngcsdk (F0082), model-registry
    PyPI (F0086), openmind-hub (F0072), openxlab PyPI (F0074), oras PyPI (F0081), ollama
    PyPI client (F0077), @huggingface/hub npm (F0092), lmstudio-community HF org (F0088),
    onnxmodelzoo HF org (F0089), qualcomm HF org (F0090), kipoi/kipoi (F0021).
  - satellite of mapped `aimet` (1): quic/aimet-model-zoo, archived, last push 2026-02-12
    (F0128).

LM Studio is two signals, not one counted twice. The **app** (`lm-studio`, head in `ui_api`)
is an already-mapped duplicate. The **catalog** surface is a unique candidate, parked because it
fronts Hugging Face (W0063, F0088).

Removed after audit: fork repos seen in search results (their excerpts were not logged), and the
Together, Modal, vLLM, Spaces and Eden AI signals, whose search excerpts don't name them.
Northflank is dropped too: W0001 lists it only as the publisher of an alternatives blog, not as a
candidate. None of these is counted anywhere.

```
raw_signals       = duplicate_signals + unique_candidates
78                = 31                + 47
unique_candidates = accepted + parked
47                = 18       + 29
```

Candidates the brief did not name:
- **Surfaced by search:** MatrixHub (W0002), Harbor as a model registry (W0004, W0053),
  Docker Hub `ai/` (W0004, W0009), Jozu Hub (W0044), DagsHub (W0001),
  Tensor.art, SeaArt and LiblibAI (W0005), GitHub Models' retirement (W0007),
  Moark and hf-mirror.com (W0030, W0054), Melious and EULLM
  (W0052).
- **Added by the sweeper by name, then verified live** (so these are not search discoveries):
  Kubeflow Hub (W0014, F0045), SageMaker JumpStart (W0068), Qualcomm AI Hub Models (W0008,
  F0015), MONAI Model Zoo (F0020), BioImage Model Zoo (F0019, W0045), Kipoi (F0021, F0126),
  OpenVINO Open Model Zoo (F0017), Unity Catalog (F0008), ORAS (F0039), PaddleHub (F0040),
  quic/aimet-model-zoo (F0128).

## 9. Open questions for the maintainer

1. **Slug for the HF platform.** `huggingface-hub-platform`, or rename the head client and give
   the platform `huggingface-hub`? Recommend **keep `huggingface-hub-platform`**. Renaming a
   published slug costs a redirect; this row costs nothing.
2. **One AWS surface or two?** (a) JumpStart only, (b) JumpStart + Bedrock Marketplace.
   Recommend **(a)**: Bedrock Marketplace deploys onto SageMaker endpoints (W0037), so it is
   the same registry behind a second storefront.
3. **OCI model distribution: in or out?** (a) out entirely (park KitOps, ModelPack, ORAS,
   Harbor, Docker Hub `ai/`), (b) admit registry *servers* that display models first-class
   (Harbor, W0056) plus Docker Hub `ai/`, (c) admit the tooling too. Recommend **(a) now, with
   (b) revisited** once ModelPack leaves Sandbox. Tooling fails the "place models live" litmus
   under any reading.
4. **Domain zoos (MONAI, BioImage, Kipoi) and OpenML: here, or park?** Recommend **keep them**.
   They satisfy the litmus and fill rungs 2 and 4, and OpenML's datasets-first profile is the
   one to watch for a later move to `benchmark_eval_data`.
5. **Adoption instrument.** (a) client-library downloads as a proxy, (b) platform-native
   counters (models hosted, pulls), (c) abstain and weight capability heavily (for example
   adopt 0.3 / cap 0.7). Recommend **(c) plus (b) as recorded evidence**. Declaring clients
   repeats the satellite trap (identity.md), and client counts differ by about 5 orders of magnitude
   for reasons unrelated to registry use (F0069 vs F0073).
6. **Civitai openness.** The repo is Apache-2.0 and active (F0009, F0052), but it was not
   verified that production runs this code. Score it as open software? Recommend **yes**, on the
   published code, with a note.
7. **Model Garden naming.** Keep "Vertex AI Model Garden" or follow the "Gemini Enterprise Agent
   Platform" rebrand (W0043)? Recommend **keep the slug, and update the display name after a
   primary-source fetch** (this sweep's direct fetches did not complete).
8. **Declare PyPI `qai-hub-models` on the Qualcomm row?** Its repository URL `quic/ai-hub-models`
   is a previous name of the declared repo (F0015), and the package homepage is the catalog page
   (F0083). Recommend **yes**. It is the catalog's own install path. Resolved by evidence; this
   only needs a sign-off.
9. **PyTorch Hub and BioImage with no license file.** Treat as `source-available` or ask
   upstream? Recommend **source-available now**, and open an upstream issue for BioImage, whose
   self-description says "fully open" (W0045).
10. **Regional closed hubs (Modelers, WiseModel, OpenXLab).** Park under ADR-005's best-in-class
    test, or admit one as the China-region comparator beside ModelScope? Recommend **park**.
    ModelScope already holds that frontier at 259,500 models (F0115).


## Appendix: fetch-id index (generated from the logs)

| id | fetched (UTC) | http/tool | url or query |
|---|---|---|---|
| F0001 | 2026-09-26T20:01:45Z | 404 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/opencsg%2Fcsghub |
| F0003 | 2026-09-26T20:01:46Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/matrixhub-ai%2Fmatrixhub |
| F0004 | 2026-09-26T20:01:46Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/kitops-ml%2Fkitops |
| F0005 | 2026-09-26T20:01:47Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/modelpack%2Fmodel-spec |
| F0006 | 2026-09-26T20:01:47Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/goharbor%2Fharbor |
| F0008 | 2026-09-26T20:01:48Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/unitycatalog%2Funitycatalog |
| F0009 | 2026-09-26T20:01:49Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/civitai%2Fcivitai |
| F0010 | 2026-09-26T20:01:49Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/pytorch%2Fhub |
| F0011 | 2026-09-26T20:01:50Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/onnx%2Fmodels |
| F0012 | 2026-09-26T20:01:51Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/openml%2FOpenML |
| F0013 | 2026-09-26T20:01:51Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/openml%2Fopenml-python |
| F0014 | 2026-09-26T20:01:52Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/modelscope%2Fmodelscope |
| F0015 | 2026-09-26T20:01:52Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/qualcomm%2Fai-hub-models |
| F0016 | 2026-09-26T20:01:52Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Kaggle%2Fkagglehub |
| F0017 | 2026-09-26T20:01:53Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/openvinotoolkit%2Fopen_model_zoo |
| F0018 | 2026-09-26T20:01:53Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/tensorflow%2Fhub |
| F0019 | 2026-09-26T20:01:54Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/bioimage-io%2Fcollection |
| F0020 | 2026-09-26T20:01:55Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Project-MONAI%2Fmodel-zoo |
| F0021 | 2026-09-26T20:01:55Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/kipoi%2Fkipoi |
| F0022 | 2026-09-26T20:01:56Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/zenodo%2Fzenodo |
| F0023 | 2026-09-26T20:01:56Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/mudler%2FLocalAI |
| F0024 | 2026-09-26T20:02:09Z | 403 | https://ungh.cc/repos/OpenCSG/csghub |
| F0027 | 2026-09-26T20:02:11Z | 200 | https://ungh.cc/repos/huggingface/hub-docs |
| F0035 | 2026-09-26T20:02:52Z | 429 | https://ungh.cc/repos/openxlab-dev/openxlab |
| F0036 | 2026-09-26T20:02:59Z | 404 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/OpenCSG%2Fcsghub |
| F0039 | 2026-09-26T20:03:03Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/oras-project%2Foras |
| F0040 | 2026-09-26T20:03:05Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/PaddlePaddle%2FPaddleHub |
| F0041 | 2026-09-26T20:03:06Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/replicate%2Fcog |
| F0042 | 2026-09-26T20:03:07Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/lmstudio-ai%2Flms |
| F0043 | 2026-09-26T20:03:09Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/DagsHub%2Fclient |
| F0045 | 2026-09-26T20:03:25Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/kubeflow%2Fhub |
| F0047 | 2026-09-26T20:03:41Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/OpenCSGs%2Fcsghub |
| F0048 | 2026-09-26T20:03:41Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/OpenCSGs%2Fcsghub-server |
| F0049 | 2026-09-26T20:03:48Z | 200 | https://raw.githubusercontent.com/OpenCSGs/csghub/HEAD/LICENSE |
| F0050 | 2026-09-26T20:03:48Z | 200 | https://raw.githubusercontent.com/matrixhub-ai/matrixhub/HEAD/LICENSE |
| F0051 | 2026-09-26T20:03:48Z | 200 | https://raw.githubusercontent.com/kitops-ml/kitops/HEAD/LICENSE |
| F0052 | 2026-09-26T20:03:48Z | 200 | https://raw.githubusercontent.com/civitai/civitai/HEAD/LICENSE |
| F0053 | 2026-09-26T20:03:49Z | 200 | https://raw.githubusercontent.com/kubeflow/hub/HEAD/LICENSE |
| F0054 | 2026-09-26T20:03:49Z | 200 | https://raw.githubusercontent.com/onnx/models/HEAD/LICENSE |
| F0055 | 2026-09-26T20:03:49Z | 200 | https://raw.githubusercontent.com/openml/OpenML/HEAD/LICENSE |
| F0056 | 2026-09-26T20:03:50Z | 200 | https://raw.githubusercontent.com/modelscope/modelscope/HEAD/LICENSE |
| F0057 | 2026-09-26T20:03:50Z | 200 | https://raw.githubusercontent.com/qualcomm/ai-hub-models/HEAD/LICENSE |
| F0058 | 2026-09-26T20:03:50Z | 404 | https://raw.githubusercontent.com/pytorch/hub/HEAD/LICENSE |
| F0059 | 2026-09-26T20:03:51Z | 200 | https://raw.githubusercontent.com/Project-MONAI/model-zoo/HEAD/LICENSE |
| F0060 | 2026-09-26T20:03:51Z | 404 | https://raw.githubusercontent.com/bioimage-io/collection/HEAD/LICENSE |
| F0061 | 2026-09-26T20:03:51Z | 200 | https://raw.githubusercontent.com/unitycatalog/unitycatalog/HEAD/LICENSE |
| F0062 | 2026-09-26T20:03:52Z | 200 | https://raw.githubusercontent.com/goharbor/harbor/HEAD/LICENSE |
| F0063 | 2026-09-26T20:04:17Z | 200 | https://huggingface.co/models |
| F0064 | 2026-09-26T20:04:18Z | 200 | https://huggingface.co/datasets |
| F0067 | 2026-09-26T20:04:43Z | 200 | https://civitai.com/api/v1/models?limit=1 |
| F0069 | 2026-09-26T20:07:48Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/huggingface-hub |
| F0070 | 2026-09-26T20:07:49Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/modelscope |
| F0071 | 2026-09-26T20:07:50Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/kagglehub |
| F0072 | 2026-09-26T20:07:51Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/openmind-hub |
| F0073 | 2026-09-26T20:07:52Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/csghub-sdk |
| F0074 | 2026-09-26T20:07:54Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/openxlab |
| F0076 | 2026-09-26T20:07:55Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/civitai-py |
| F0077 | 2026-09-26T20:07:56Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/ollama |
| F0078 | 2026-09-26T20:07:57Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/lmstudio |
| F0079 | 2026-09-26T20:07:58Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/openml |
| F0080 | 2026-09-26T20:07:59Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/bioimageio.core |
| F0081 | 2026-09-26T20:08:00Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/oras |
| F0082 | 2026-09-26T20:08:01Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/ngcsdk |
| F0083 | 2026-09-26T20:08:01Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/qai-hub-models |
| F0084 | 2026-09-26T20:08:02Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/replicate |
| F0086 | 2026-09-26T20:08:04Z | 200 | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/model-registry |
| F0088 | 2026-09-26T20:08:13Z | 200 | https://huggingface.co/api/models?author=lmstudio-community&sort=downloads&limit=3 |
| F0089 | 2026-09-26T20:08:14Z | 200 | https://huggingface.co/api/models?author=onnxmodelzoo&sort=downloads&limit=3 |
| F0090 | 2026-09-26T20:08:14Z | 200 | https://huggingface.co/api/models?author=qualcomm&sort=downloads&limit=3 |
| F0092 | 2026-09-26T20:08:15Z | 200 | https://api.npmjs.org/downloads/point/last-month/@huggingface%2Fhub |
| F0093 | 2026-09-26T20:08:15Z | 200 | https://pypi.org/pypi/openxlab/json |
| F0094 | 2026-09-26T20:08:15Z | 200 | https://pypi.org/pypi/modelscope/json |
| F0095 | 2026-09-26T20:08:15Z | 200 | https://pypi.org/pypi/kagglehub/json |
| F0096 | 2026-09-26T20:08:40Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/matrixhub-ai%2Fmatrixhub/releases?per_page=1 |
| F0097 | 2026-09-26T20:08:41Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/kitops-ml%2Fkitops/releases?per_page=1 |
| F0098 | 2026-09-26T20:08:41Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/OpenCSGs%2Fcsghub/releases?per_page=1 |
| F0099 | 2026-09-26T20:08:42Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/kubeflow%2Fhub/releases?per_page=1 |
| F0100 | 2026-09-26T20:08:42Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/goharbor%2Fharbor/releases?per_page=1 |
| F0101 | 2026-09-26T20:08:43Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/qualcomm%2Fai-hub-models/releases?per_page=1 |
| F0103 | 2026-09-26T20:08:44Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/modelscope%2Fmodelscope/releases?per_page=1 |
| F0104 | 2026-09-26T20:08:44Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Project-MONAI%2Fmodel-zoo/releases?per_page=1 |
| F0105 | 2026-09-26T20:08:45Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/unitycatalog%2Funitycatalog/releases?per_page=1 |
| F0106 | 2026-09-26T20:08:45Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/civitai%2Fcivitai/releases?per_page=1 |
| F0107 | 2026-09-26T20:08:46Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/openml%2Fopenml-python/releases?per_page=1 |
| F0108 | 2026-09-26T20:08:53Z | 200 | https://raw.githubusercontent.com/civitai/civitai/HEAD/README.md |
| F0109 | 2026-09-26T20:08:54Z | 200 | https://raw.githubusercontent.com/OpenCSGs/csghub/HEAD/README.md |
| F0110 | 2026-09-26T20:08:54Z | 200 | https://raw.githubusercontent.com/matrixhub-ai/matrixhub/HEAD/README.md |
| F0111 | 2026-09-26T20:08:54Z | 200 | https://raw.githubusercontent.com/kubeflow/hub/HEAD/README.md |
| F0112 | 2026-09-26T20:08:54Z | 200 | https://raw.githubusercontent.com/ollama/ollama/HEAD/docs/import.mdx |
| F0113 | 2026-09-26T20:08:55Z | 200 | https://raw.githubusercontent.com/pytorch/hub/HEAD/README.md |
| F0114 | 2026-09-26T20:09:34Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/bioimage-io%2Fbioimage.io |
| F0115 | 2026-09-26T20:10:33Z | 200 | https://www.modelscope.cn/openapi/v1/models?page_size=1 |
| F0116 | 2026-09-26T20:10:34Z | 200 | https://raw.githubusercontent.com/openvinotoolkit/open_model_zoo/HEAD/README.md |
| F0117 | 2026-09-26T20:10:34Z | 404 | https://raw.githubusercontent.com/bioimage-io/bioimage.io/HEAD/LICENSE |
| F0118 | 2026-09-26T20:10:34Z | 200 | https://raw.githubusercontent.com/kipoi/kipoi/HEAD/LICENSE |
| F0119 | 2026-09-26T20:10:35Z | 404 | https://raw.githubusercontent.com/pytorch/hub/HEAD/LICENSE.md |
| F0120 | 2026-09-26T20:10:45Z | 200 | https://www.kaggle.com/api/v1/models/list?pageSize=1 |
| F0122 | 2026-09-26T20:12:28Z | 404 | https://raw.githubusercontent.com/pytorch/hub/HEAD/LICENSE.txt |
| F0123 | 2026-09-26T20:12:29Z | 404 | https://raw.githubusercontent.com/pytorch/hub/HEAD/COPYING |
| F0124 | 2026-09-26T20:12:29Z | 404 | https://raw.githubusercontent.com/bioimage-io/bioimage.io/HEAD/LICENSE.md |
| F0125 | 2026-09-26T20:12:29Z | 404 | https://raw.githubusercontent.com/bioimage-io/bioimage.io/HEAD/LICENSE.txt |
| F0126 | 2026-09-26T20:12:29Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/kipoi%2Fmodels |
| F0127 | 2026-09-26T20:12:30Z | 200 | https://civitai.com/api/v1/models?limit=1&sort=Most%20Downloaded |
| F0128 | 2026-09-26T20:21:59Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/quic%2Faimet-model-zoo |
| F0129 | 2026-09-26T20:22:00Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/pytorch%2Fhub/releases?per_page=1 |
| F0130 | 2026-09-26T20:22:01Z | 200 | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/bioimage-io%2Fbioimage.io/releases?per_page=1 |
| F0131 | 2026-09-26T20:22:01Z | 200 | https://pypi.org/pypi/qai-hub-models/json |
| W0001 | 2026-09-26T20:00:39Z | WebSearch | Hugging Face alternatives model hub platforms 2026 |
| W0002 | 2026-09-26T20:00:39Z | WebSearch | open source self-hosted model hub registry like Hugging Face Hub (CSGHub, private model registry) 2025 |
| W0004 | 2026-09-26T20:00:39Z | WebSearch | OCI model artifacts registry ModelPack KitOps Docker Model Runner Hub AI models 2026 |
| W0005 | 2026-09-26T20:01:03Z | WebSearch | Civitai alternatives model sharing site Tensor.art SeaArt LiblibAI checkpoints LoRA hub |
| W0007 | 2026-09-26T20:01:03Z | WebSearch | GitHub Models catalog marketplace models 2026 |
| W0008 | 2026-09-26T20:01:03Z | WebSearch | Qualcomm AI Hub models catalog on-device model zoo |
| W0009 | 2026-09-26T20:01:22Z | WebSearch | Docker Hub ai namespace models Docker Model Runner pull models OCI 2026 |
| W0012 | 2026-09-26T20:01:22Z | WebSearch | Kaggle Models TensorFlow Hub migration kagglehub model hub |
| W0013 | 2026-09-26T20:03:24Z | WebFetch | https://github.com/OpenCSG/csghub |
| W0014 | 2026-09-26T20:03:24Z | WebFetch | https://github.com/kubeflow/model-registry |
| W0015 | 2026-09-26T20:03:40Z | WebSearch | CSGHub OpenCSG github repository open source LLM asset management platform |
| W0016 | 2026-09-26T20:04:17Z | WebFetch | https://huggingface.co/blog/ivanfioravanti/three-million-models-and-counting |
| W0017 | 2026-09-26T20:04:17Z | WebFetch | https://www.modelscope.cn/models |
| W0018 | 2026-09-26T20:04:17Z | WebFetch | https://ollama.com/library |
| W0019 | 2026-09-26T20:04:17Z | WebFetch | https://lmstudio.ai/models |
| W0020 | 2026-09-26T20:04:41Z | WebFetch | https://modelscope.ai/ |
| W0021 | 2026-09-26T20:04:41Z | WebFetch | https://civitai.com/ |
| W0022 | 2026-09-26T20:04:41Z | WebFetch | https://www.kaggle.com/models |
| W0023 | 2026-09-26T20:04:41Z | WebFetch | https://catalog.ngc.nvidia.com/models |
| W0024 | 2026-09-26T20:05:08Z | WebFetch | https://www.kaggle.com/docs/models |
| W0025 | 2026-09-26T20:05:08Z | WebFetch | https://replicate.com/explore |
| W0026 | 2026-09-26T20:05:08Z | WebFetch | https://modelers.cn/ |
| W0027 | 2026-09-26T20:05:08Z | WebFetch | https://wisemodel.cn/ |
| W0028 | 2026-09-26T20:05:26Z | WebSearch | 魔乐社区 Modelers openMind 华为 模型 数量 2026 |
| W0029 | 2026-09-26T20:05:26Z | WebSearch | wisemodel 始智AI 开源社区 模型 平台 运营 公司 |
| W0030 | 2026-09-26T20:05:26Z | WebSearch | GitCode AI 社区 模型 托管 Hugging Face 镜像 2026 |
| W0031 | 2026-09-26T20:05:45Z | WebFetch | https://modelers.cn/docs/zh/community/models/overview.html |
| W0032 | 2026-09-26T20:05:45Z | WebFetch | https://wisemodel.cn/en |
| W0033 | 2026-09-26T20:05:45Z | WebFetch | https://ai.gitcode.com/ |
| W0034 | 2026-09-26T20:05:45Z | WebFetch | https://openxlab.org.cn/models |
| W0035 | 2026-09-26T20:06:00Z | WebFetch | https://cloud.google.com/vertex-ai/generative-ai/docs/model-garden/explore-models |
| W0036 | 2026-09-26T20:06:00Z | WebFetch | https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/foundry-models-overview |
| W0037 | 2026-09-26T20:06:00Z | WebFetch | https://docs.aws.amazon.com/bedrock/latest/userguide/amazon-bedrock-marketplace.html |
| W0038 | 2026-09-26T20:06:00Z | WebFetch | https://hub.docker.com/u/ai |
| W0039 | 2026-09-26T20:06:14Z | WebFetch | https://docs.cloud.google.com/vertex-ai/generative-ai/docs/model-garden/explore-models |
| W0040 | 2026-09-26T20:06:14Z | WebFetch | https://jozu.com/hub |
| W0041 | 2026-09-26T20:06:14Z | WebFetch | https://www.openml.org/ |
| W0042 | 2026-09-26T20:06:14Z | WebFetch | https://bioimage.io/ |
| W0043 | 2026-09-26T20:06:32Z | WebSearch | Vertex AI Model Garden "200+" models catalog discover test customize deploy |
| W0044 | 2026-09-26T20:06:32Z | WebSearch | Jozu Hub ModelKit registry public hub KitOps |
| W0045 | 2026-09-26T20:06:32Z | WebSearch | BioImage Model Zoo bioimage.io community models paper number of models |
| W0046 | 2026-09-26T20:06:32Z | WebSearch | OpenML platform datasets tasks runs open source machine learning 2026 |
| W0047 | 2026-09-26T20:06:44Z | WebFetch | https://cloud.google.com/model-garden |
| W0048 | 2026-09-26T20:06:44Z | WebFetch | https://jozu.ml/docs/getting-started/overview.html |
| W0049 | 2026-09-26T20:06:44Z | WebFetch | https://pytorch.org/hub/ |
| W0050 | 2026-09-26T20:06:44Z | WebFetch | https://github.com/onnx/models |
| W0052 | 2026-09-26T20:07:09Z | WebSearch | European sovereign AI model hub platform hosting open models 2026 |
| W0053 | 2026-09-26T20:07:09Z | WebSearch | Harbor model registry AI models CNCF 2026 release ModelPack support |
| W0054 | 2026-09-26T20:07:09Z | WebSearch | Gitee AI 模力方舟 模型 托管 社区 2026 |
| W0056 | 2026-09-26T20:07:25Z | WebFetch | https://goharbor.io/blog/cloud-native-ai-model-management/ |
| W0057 | 2026-09-26T20:07:25Z | WebFetch | https://github.com/cncf/sandbox/issues/510 |
| W0058 | 2026-09-26T20:07:25Z | WebFetch | https://www.cncf.io/projects/modelpack/ |
| W0059 | 2026-09-26T20:07:39Z | WebFetch | https://moark.com/models |
| W0060 | 2026-09-26T20:07:39Z | WebFetch | https://tensor.art/models |
| W0061 | 2026-09-26T20:07:39Z | WebFetch | https://www.liblib.art/ |
| W0062 | 2026-09-26T20:07:39Z | WebFetch | https://dagshub.com/ |
| W0063 | 2026-09-26T20:09:18Z | WebFetch | https://lmstudio.ai/docs/app/basics/download-model |
| W0064 | 2026-09-26T20:09:18Z | WebFetch | https://lmstudio.ai/hub |
| W0065 | 2026-09-26T20:09:18Z | WebFetch | https://www.developersdigest.tech/blog/github-models-retired-2026 |
| W0066 | 2026-09-26T20:09:18Z | WebFetch | https://aihub.qualcomm.com/models |
| W0067 | 2026-09-26T20:09:33Z | WebFetch | https://github.blog/changelog/2026-07-30-github-models-is-now-retired/ |
| W0068 | 2026-09-26T20:09:33Z | WebFetch | https://docs.aws.amazon.com/sagemaker/latest/dg/studio-jumpstart.html |
| W0069 | 2026-09-26T20:09:33Z | WebFetch | https://docs.openml.org/ |
| W0071 | 2026-09-26T20:12:18Z | WebSearch | OpenXLab 浦源 模型中心 上海人工智能实验室 openxlab.org.cn models |
| W0072 | 2026-09-26T20:22:14Z | WebSearch | Google acquires Kaggle |
| W0073 | 2026-09-26T20:22:14Z | mcp__github__issue_read(get_comments) | https://github.com/currentai-org/os-ai-map/issues/601#issuecomment-5819306219 |
