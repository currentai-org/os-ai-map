# Model hubs & registries seed: 2026-09-26

## Scope and boundary

This batch seeds the preliminary `model_hubs` category proposed in issue #601. A row belongs when it
is a platform or self-hostable service whose product is hosting, indexing and distributing model
artifacts from many publishers, as a registry other tools pull from by name. The litmus: can a client
fetch a named, versioned model artifact from it by API, git or registry protocol, where the thing on
offer is the registry itself rather than the runtime, UI or inference API in front of it?

The seed mixes four populations that answer that litmus differently, and one capability quantity
(registry scope, see the category's `scoring_recipe.note`) orders all four:

- public hosted hubs: Hugging Face Hub, ModelScope, Ollama Library, Civitai, Kaggle Models;
- cloud and vendor catalogs: Vertex AI Model Garden, Microsoft Foundry Models, SageMaker JumpStart,
  NVIDIA NGC Catalog, Qualcomm AI Hub Models;
- self-hostable hub and registry software: CSGHub, MatrixHub, Kubeflow Hub;
- domain model zoos: MONAI, BioImage, Kipoi, OpenML, PyTorch Hub.

Exclusions, each recorded in the category's `comments`: runtimes that pull from a registry
(`ollama` the runner, LocalAI's gallery, Docker Model Runner) stay in `deployment` or
`inference_code`; chat and desktop apps with a model browser (`lm-studio`) stay in `ui_api`; hosted
inference APIs (Replicate) and Spaces stay in `deployment`; hub client libraries (`huggingface-hub`,
kagglehub, the modelscope library, ngcsdk, csghub-sdk) stay in `ml_frameworks`; MLflow Model Registry
stays inside `mlflow`; versioned data layers and data catalogs (oxen, dvc, lakefs, DagsHub, Unity
Catalog) belong to `storage`; agent and MCP registries belong to `agent_protocols`; general research
repositories (Zenodo) are out.

Rulings applied from the 2026-09-26 decision record:

- The Hugging Face platform is the new row `huggingface-hub-platform`. The published head
  `huggingface-hub` is the Python client, per the #601 comment of 2026-09-24, and is not renamed.
- OCI packaging and generic registry tooling is out: KitOps, ModelPack, ORAS, Harbor and Docker
  Hub's `ai/` namespace are parked. Registry servers that show models as first-class artifacts
  (Harbor 2.15) are to be revisited once ModelPack leaves CNCF Sandbox.
- No closed regional hub is admitted beside ModelScope: Modelers, WiseModel and OpenXLab stay parked.
- One AWS surface, SageMaker JumpStart. Bedrock Marketplace deploys onto SageMaker endpoints, so it
  is the same registry behind a second storefront.
- The domain zoos and OpenML are kept. OpenML is the row to watch for a later move to
  `benchmark_eval_data`.
- Placement is Infrastructure → Platform, after `storage`. Weights are 0.3 adoption / 0.7
  capability. The recipe extends the shared `software` ladder.
- The category goes in the last promotion wave.

No row was scored. Each row carries identity and artifacts only, as the registry schema requires.

## Inputs swept

All fetched live on 2026-09-26. Every fact in the sweep carries an `F` id (curl fetches through
`research/rfetch.sh`, bodies saved) or a `W` id (WebSearch, WebFetch or a GitHub MCP read, with an
excerpt). The full trail is on the evidence branch `claude/research-model_hubs`, under
`research/model_hubs/`: `sweep.md`, `rows.yaml`, `fetch-log.tsv` with `raw/`, `web-log.tsv`, and
`audit.md` with its own `audit-fetch-log.tsv`.

Sources: the candidates named in #601; web search for hub, registry and model-zoo terms; the
ecosyste.ms repository and package APIs; raw GitHub LICENSE and README files; the Hugging Face,
ModelScope, Civitai and Kaggle public APIs; and the operators' own catalog and documentation pages.
Kubeflow Hub, SageMaker JumpStart, Qualcomm AI Hub Models, MONAI, BioImage, Kipoi, OpenVINO Open
Model Zoo, Unity Catalog, ORAS, PaddleHub and quic/aimet-model-zoo were added by the sweeper by name
and then verified live, so they are not search discoveries.

**No retrieval cutoff.** The searches were targeted rather than a walk down a ranked source. Many hub
sites render in JavaScript, and WebFetch returned only a title for ModelScope's home page, Kaggle,
OpenXLab, WiseModel, OpenML and bioimage.io; an API was used instead where one existed. The GitHub
API and ungh.cc returned 403 or 429 for several repositories, which is an access limit and not a
finding.

A two-pass independent audit re-fetched 22 claims live (all matched), confirmed every artifact
resolves, and failed the first draft on 12 sourcing and counting items. All 12 were fixed and passed
on the second pass.

## Reconciled counts

A duplicate is a signal that resolves to a product already in the corpus (5: `huggingface-hub`,
`ollama`, `lm-studio`, `mlflow`, `localai`) or to a second artifact or satellite of a candidate
already counted (26). LM Studio is two signals: the app is a mapped duplicate, and the catalog
surface is a unique candidate, parked because it fronts Hugging Face.

```text
raw_signals       = 78
duplicate_signals = 31
unique_candidates = 47
accepted          = 18
parked            = 29

78 = 31 + 47
47 = 18 + 29
```

The decision record added no candidate and removed none, and assigned no tail move into this
category, so the 18 accepted rows are the sweep's 18. No slug or artifact collides with a head
product, a retired alias, an existing registry row or the resolution ledger (`research/crosscheck.py`:
29 identity keys, 0 findings, before the registry file was written).

Openness mix at seed: 8 open, 2 source-available (no license file), 8 closed. 18 distinct org slugs,
17 independent parents: Kaggle has been Google's since 2017, so Google holds `kaggle-models` and
`vertex-ai-model-garden` (2 of 18, 11.1%). Every other parent holds one row.

## Organizations and handles

Eight org slugs are new: `civitai`, `kaggle`, `opencsg`, `daocloud`, `project-monai`, `bioimage-io`,
`kipoi`, `openml`. The other ten were reused: `hugging-face`, `modelscope-alibaba`, `ollama`,
`nvidia`, `google-cloud`, `microsoft-azure`, `amazon-web-services`, `kubeflow`, `qualcomm`,
`pytorch-foundation`. Each new org gets a stub `sources/organizations/<slug>.yaml` (`type: unknown`,
empty roster), because `validate` requires an org file behind every handle; the type is set when a
row is promoted.

Handles were registered in `sources/org_handles.yaml` for every route a row's artifacts travel that
its org had no handle for. Each GitHub handle is the owner segment of the declared repository, which
the sweep resolved through ecosyste.ms. Each homepage handle is the domain of a declared homepage the
audit fetched with a 200.

| org | github | homepage_domain |
|---|---|---|
| bioimage-io | bioimage-io | bioimage.io |
| civitai | civitai | civitai.com |
| daocloud | matrixhub-ai | |
| hugging-face | (had one) | huggingface.co |
| kaggle | | kaggle.com |
| kipoi | kipoi | |
| opencsg | OpenCSGs | opencsg.com |
| openml | openml | openml.org |
| project-monai | Project-MONAI | |
| pytorch-foundation | pytorch | pytorch.org |
| qualcomm | qualcomm | (had one) |

The handle-coverage pin in `tests/fixtures/identity_coverage_baseline.json` rose past its margin, so
it was re-pinned with `build.identity_eval --write-coverage-baseline`, and the pass fixture's tail
rows were regenerated with `--write-fixture`. The category was also added to the product-suggestion
issue form's dropdown.

`matrixhub-ai` is registered to `daocloud` with a note: it is the MatrixHub project account, and
Shanghai DaoCloud submitted MatrixHub to the CNCF Sandbox on 2026-07-30 (W0057). The Azure row's
homepage sits on `learn.microsoft.com`, which the existing `microsoft.com` handle of the `microsoft`
org covers. No docs-domain handle was added for `microsoft-azure`, since learn.microsoft.com is not
Azure's to own.

## Accepted candidates

Every row fetched 2026-09-26. The primary source is the fetch that establishes the row's identity and
that it is live.

| slug | open status | primary source | id |
|---|---|---|---|
| huggingface-hub-platform | closed | https://huggingface.co/models | F0063 |
| modelscope | closed | https://www.modelscope.cn/openapi/v1/models?page_size=1 | F0115 |
| ollama-library | closed | https://ollama.com/library | W0018 |
| civitai | open (Apache-2.0) | https://raw.githubusercontent.com/civitai/civitai/HEAD/README.md | F0108 |
| kaggle-models | closed | https://www.kaggle.com/api/v1/models/list?pageSize=1 | F0120 |
| nvidia-ngc-catalog | closed | https://catalog.ngc.nvidia.com/models | W0023 |
| vertex-ai-model-garden | closed | web search, "Vertex AI Model Garden 200+ models" (the direct fetch did not complete) | W0043 |
| azure-ai-foundry-models | closed | https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/foundry-models-overview | W0036 |
| sagemaker-jumpstart | closed | https://docs.aws.amazon.com/sagemaker/latest/dg/studio-jumpstart.html | W0068 |
| csghub | open (Apache-2.0) | https://raw.githubusercontent.com/OpenCSGs/csghub/HEAD/README.md | F0109 |
| matrixhub | open (Apache-2.0) | https://raw.githubusercontent.com/matrixhub-ai/matrixhub/HEAD/README.md | F0110 |
| kubeflow-hub | open (Apache-2.0) | https://raw.githubusercontent.com/kubeflow/hub/HEAD/README.md | F0111 |
| qualcomm-ai-hub-models | open (BSD-3-Clause) | https://pypi.org/pypi/qai-hub-models/json | F0131 |
| pytorch-hub | source-available (no license file) | https://raw.githubusercontent.com/pytorch/hub/HEAD/README.md | F0113 |
| monai-model-zoo | open (Apache-2.0) | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Project-MONAI%2Fmodel-zoo | F0020 |
| bioimage-model-zoo | source-available (no license file) | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/bioimage-io%2Fbioimage.io | F0114 |
| kipoi | open (MIT) | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/kipoi%2Fmodels | F0126 |
| openml | open (BSD-3-Clause) | https://docs.openml.org/ | W0069 |

The open status is the sweep's reading, not a score. The hosted rows say "closed" because their
server source was not checked, and their open clients are satellites that do not count.

## Parked candidates

All fetched 2026-09-26; the sweep's §7 carries the full source list per row.

| name | reason | id |
|---|---|---|
| Docker Hub `ai/` namespace | OCI distribution, out by ruling; also closed long tail | W0038, W0009 |
| Modelers (魔乐社区) | closed regional hub, out by ruling; operator unconfirmed on the fetched page | W0028, W0031 |
| WiseModel (始智AI) | closed regional hub, out by ruling | W0029 |
| OpenXLab model center | closed regional hub, out by ruling; its PyPI figure (4.78M/month on a placeholder `github.com/xxx/xxxx` repository) was not trusted | W0071, F0074, F0093 |
| Amazon Bedrock Marketplace | same registry as `sagemaker-jumpstart` behind a second storefront | W0037 |
| Replicate | boundary → deployment (hosted inference API) | W0025 |
| Tensor.art | closed long-tail image hub; page returned 403 | W0005, W0060 |
| SeaArt | closed long-tail image hub | W0005 |
| LiblibAI | closed long-tail image hub | W0005, W0061 |
| LM Studio catalog | not a registry: it downloads from Hugging Face | W0063, F0088 |
| GitHub Models | retired 2026-07-30 | W0067 |
| ONNX Model Zoo | superseded, moved to the HF `onnxmodelzoo` account | W0050, F0089 |
| TensorFlow Hub | retired alias of `kaggle-models` | W0012, F0018 |
| OpenVINO Open Model Zoo | superseded: in maintenance mode as a source of models | F0116 |
| GitCode AI | identity unclear: ai.gitcode.com redirects to gitcode.com | W0033 |
| Moark (formerly Gitee AI) | identity unclear and serving-first; rendered zero public models | W0054, W0059 |
| PaddleHub | identity unclear: ecosyste.ms shows a repository created 2025-06-25 with 82 stars, which does not fit a long-lived project | F0040 |
| Jozu Hub | closed long-tail ModelKit registry; hub and docs pages 404 | W0044, W0040, W0048 |
| DagsHub | closed long tail; boundary → storage | W0062 |
| KitOps | packaging CLI, out by ruling | F0004 |
| ModelPack | format spec, out by ruling | F0005, W0058 |
| ORAS | OCI registry client, out by ruling | F0039 |
| Harbor | general OCI registry, out by ruling; revisit per the ruling above | W0056, F0062 |
| Unity Catalog | boundary → storage (data and AI governance catalog) | F0008 |
| Zenodo | general research repository | F0022 |
| hf-mirror.com | mirror of the HF Hub, not a separate registry | W0030 |
| Melious | boundary → deployment or ui_api (inference API) | W0052 |
| EULLM | sovereign LLM platform, not a registry | W0052 |
| Docker Model Runner | boundary → deployment or inference_code (a runtime) | W0009 |

## Identity notes for promotion

- **`huggingface-hub-platform`** covers Models and Datasets. Spaces is its own head product in
  `deployment` and a separate surface under ADR-005 test 1.
- **`modelscope`** declares only the modelscope.cn homepage. modelscope.ai titles itself "Home -
  ModelScope"; that it is the international edition is inferred from the title, not fetched.
- **`ollama-library`** is the ollama.com registry that `ollama push` writes to (F0112), a separate
  surface from the `ollama` runner.
- **`civitai`** declares `civitai/civitai` (Apache-2.0). Score it as open software on the published
  code, with a note that the live site was not verified to run it.
- **`kaggle-models`** absorbed TensorFlow Hub; `tensorflow-hub` is a retired alias to record at
  promotion. The public models API returns a page-capped total, a lower bound only.
- **`vertex-ai-model-garden`** rests on a search snippet; the direct fetches did not complete.
  Search shows a rebrand to "Gemini Enterprise Agent Platform (formerly Vertex AI)" (W0043). Keep the
  slug and update the display name after a primary-source fetch.
- **`azure-ai-foundry-models`**: the declared homepage now redirects to
  `/azure/foundry-classic/concepts/foundry-models-overview` (audit). Observability is already
  `azure-ai-foundry-observability`; this row is the model catalog only.
- **`sagemaker-jumpstart`** publishes no model count.
- **`csghub`**: the canonical owner is `OpenCSGs`; `OpenCSG/csghub` returns 404. The backend
  `csghub-server` and `csghub-sdk` are second artifacts of this row.
- **`kubeflow-hub`** was renamed from `kubeflow/model-registry` and is still alpha. PyPI
  `model-registry` is its client and is not declared.
- **`qualcomm-ai-hub-models`** declares PyPI `qai-hub-models`, the catalog's own install path and the
  one declared usage instrument in the category. The package's repository URL `quic/ai-hub-models`
  is a previous name of the declared repository (ecosyste.ms `previous_names`, F0015). The compile
  service is not in scope.
- **`pytorch-hub`** has had no push since 2024-04-15 (F0010) and is the one seed row outside the
  12-month activity window. Submissions are a `hubconf.py` in the publisher's own repository, so it
  sits at the index rung.
- **`bioimage-model-zoo`** declares the website repository; `bioimage-io/collection` is a second
  artifact. It describes itself as "fully open" (W0045) and ships no license file.
- **`kipoi`** declares the zoo repository `kipoi/models`; `kipoi/kipoi` is the API and a second
  artifact.
- **`openml`**: models ("flows") are secondary to datasets, tasks and runs.

## Open questions left for the maintainer

1. **License rulings.** `pytorch/hub`, `bioimage-io/bioimage.io` and `bioimage-io/collection` ship
   no license file; the seed reads them as source-available. OpenML's docs say Apache for the code
   and CC-BY for the service, while the repository text is BSD-3-Clause. These go to the one
   license-rulings issue; products carrying them are deferred at promotion. An upstream issue for
   BioImage is recommended.
2. **Adoption instrument.** The category abstains on a shared instrument and leans on capability.
   Platform-native counters (models hosted, pulls, per-model downloads) are to be recorded as
   evidence. Declaring client-library downloads would repeat the satellite trap.
3. **The capability rungs** in the recipe note are proposed, not calibrated. Rungs 4 and 5 each hold
   one hosted and one self-hostable product, which is what lets the two share a quantity.
4. **Harbor and OCI model distribution**, to be revisited when ModelPack leaves CNCF Sandbox.
5. **Thin roster.** The category passes the fit test at 18 rows, with little slack. The first
   promotion tranche needs every sub-type and the closed comparators ADR-005 asks for.
