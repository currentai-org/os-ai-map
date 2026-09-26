# Classic ML & computer-vision libraries sweep — 2026-09-26

Brief 3, issue #600, proposed slug `classic_ml_cv`. Every fact below carries a fetch id: `Fnnnn`
rows are in `fetch-log.tsv` (body under `raw/`), `Wnnnn` rows are WebSearch/WebFetch calls in
`web-log.tsv`. All fetches were made on 2026-09-26 UTC. A few cited ids are deliberate non-200s
(404 on a repo's old name, a 401 gate, a 403 from ungh); each is cited only to show that a lookup
failed or a repo moved, never as the source of a value. F0244 and F0528 are malformed fetches (a failed write and a mistyped URL) that nothing cites.

## 1. Verdict

**GO-WITH-CHANGES.**

Supply is not the issue. 81 candidates survive with live artifacts from 68 organizations; the
largest org, Meta, holds 5 (6.2%). 73 of them carry a monthly download instrument, and the
leading PyPI figures are the largest on the map: scikit-learn at 183.8M a month (F0009), NLTK at
42.3M (F0055), statsmodels at 31.4M (F0022), OpenCV at 29.9M (F0452), XGBoost at 29.9M (F0013).
None of the 81 collides with a slug or artifact in the index. Four changes are needed before
building it:
1. **Cut the drift.** Hyperparameter tuning (Optuna, Hyperopt) and explainability (SHAP, LIME,
   Captum, InterpretML) do not fit a model, so they are parked here with boundary targets.
2. **Declare the category mixed-type.** 59 software rows (timm among them, by ruling) and 22 model rows: vision
   backbones and perception model lines, plus the tabular foundation models. Use `extends: {model: pretrained, software: software}`.
3. **Move the SAM line here** from `scientific_ai_models` as one product-line row.
4. **Accept that the capability axis will be weak** (section 4).

The category is also wide enough to split: tabular/NLP/time-series has 45 rows and computer
vision has 33. Section 9, Q1, asks the maintainer to choose.

## 2. Fit metrics (computed from section 6)

- accepted candidates: **81** (open: 64, open-weights: 13, source-available: 1, closed: 3)
  - by type: software 59, model 22
  - by sub-area: classical ML estimators 18, CV libraries/toolkits 19, vision model lines 14,
    tabular foundation models 8, classical NLP 7, time series 7, tabular AutoML 5, closed 3
- independent organizations: **68** org slugs (google, google-research and google-cloud count as three, following the index's own slugs); largest org share: **6.2% (meta, 5 rows:** detectron2, prophet,
  dino, sapiens, cotracker). Next: nvidia 3 (cuml, radio, segformer).
- candidates active in the last 12 months (push or release on or after 2025-09-26): **75 of 78**
  non-closed rows. Inactive: mmdetection (last push 2024-08-21, F0086) and segformer (2024-08-02,
  F0167). tpot misses by 15 days (2025-09-11, F0211).
- candidates with a usage instrument (PyPI monthly or HF 30-day downloads), not stars only:
  **73**. Stars or none: ml-net (NuGet lifetime total only, F0510), corenlp, detectron2,
  paddledetection, deim, and the 3 closed rows.
- retrieval cutoff: Hugging Face task lists read to the **top 40 by downloads** for 7 pipeline
  tags (image-classification F0001, object-detection F0002, image-segmentation F0003,
  mask-generation F0004, depth-estimation F0005, image-feature-extraction F0006,
  tabular-classification F0007). Nothing below rank 40 was reviewed. Model families inside the top
  40 that were not researched individually are parked as "identity unclear (not researched this
  run)", not dropped. Library discovery ran on the brief's leads plus 20 WebSearch/WebFetch calls
  (W0001–W0020). There was no numeric cutoff on libraries.
- **candidates the brief did not name (56 of 81 accepted).** Surfaced by search (14): ngboost,
  perpetual, ml-net, dask-ml (W0008, W0014); rf-detr, d-fine (W0002); tabpfn, tabicl, limix (W0003);
  tabfm (W0011); radio (W0012); statsforecast (W0006); autogluon, flaml (W0010). Surfaced from the
  HF top-40 lists (12): depth-anything, depth-pro, birefnet, rmbg, segformer, sapiens, eomt (F0003,
  F0005); rt-detr (F0002); sap-rpt-1, nori, tabstar, exaone-tabular (F0007). Added by the sweeper
  as known neighbors of the leads and then verified by fetch, with no search surfacing them (27):
  umap, hdbscan, cuml, river, skrub, mlpack, h2o-3, corenlp, textblob, flair, scikit-image,
  mediapipe, paddledetection, monai, lightly, lightly-train, dlib, insightface, torchgeo, deim,
  cotracker, neuralforecast, pmdarima, gluonts, tpot, auto-sklearn, pycaret. Closed comparators (3):
  google-cloud-vision, amazon-rekognition, datarobot.

## 3. Boundary

**Definition.** Libraries and pretrained model lines for machine learning outside the LLM stack:
classical and gradient-boosted estimators, classical NLP pipelines, time-series forecasters,
tabular AutoML and tabular foundation models, and computer-vision libraries, toolkits and vision
backbone or perception model lines.

**Litmus.** Does the product fit, run or ship a prediction model (or the vision primitives one is
built from) that a data scientist would use before any LLM is involved? It passes only if its
reason for fame predates the LLM stack or runs orthogonal to it.

**Scope line inside the brief's question marks.** The rule is *does it fit or run a model?*
- **In:** tabular AutoML (AutoGluon, FLAML, H2O-3, PyCaret, TPOT, auto-sklearn), because they
  fit models. Time series (sktime, Darts, StatsForecast, Prophet …) is in, because these are
  estimator libraries. CV primitives (OpenCV, scikit-image, Kornia, Albumentations, supervision)
  are in, because a CV model cannot be built without them and nothing else on the map owns them.
- **Out (parked):** hyperparameter search (Optuna, Hyperopt) goes to `ml_orchestration`, which
  already holds Katib. Explainability (SHAP, LIME, Captum, InterpretML) goes to `evaluation_code`,
  or to the sibling `responsible_ai_measurement` proposal if it passes. Data curation (FiftyOne)
  goes to `dataset_processing_tools`, where label-studio and cleanlab already sit. Inference
  servers (Roboflow Inference) go to `inference_code`/`deployment`.

**Explicit exclusions and who owns them**
- Deep-learning frameworks every layer imports (PyTorch, TF, JAX, Keras, PyTorch Lightning) → `ml_frameworks`.
- Text-prompted / open-vocabulary vision-language models (Grounding DINO, Falcon Perception,
  CLIPSeg, LocateAnything) → brief 2 `multimodal_models` (sibling sweep; flagged, not resolved).
- Contrastive image–text encoders (CLIP, SigLIP, Perception Encoder) → `embeddings_retrieval`.
- Layout/table detection (Table Transformer, PP-DocLayout) and OCR → `document_conversion`.
- Domain foundation models (pathology backbones UNI/CONCH/Virchow, geospatial Prithvi) → `scientific_ai_models`.
- Image/video generation (diffusion) → brief 1 `media_generation` (sibling sweep).
- Robot perception stacks → brief 5a `robotics_embodied` (sibling sweep).

**The `ml_frameworks` boundary** (brief question). Each `ml_frameworks` product was checked
against both readings:

| ml_frameworks product | fails "LLM-era foundational framework"? | passes this litmus? | recommendation |
|---|---|---|---|
| pytorch-lightning | no: general DL training abstraction | no, no model of its own | stay |
| keras | no | no | stay |
| feluda | partly: a content-analysis engine, not a framework (sources/products/feluda.yaml) | weakly: image/text feature operators | stay for now; closest mover (Q2) |
| openvino | no: inference runtime, CV origins | no | stay |
| paddle, pytorch, tensorflow, jax, flax, mlx | no | no | stay |
| every other row (HF stack, formats, compilers, deepspeed, ggml, pysyft) | no | no | stay (pysyft → sibling `federated_learning`) |

None of the `ml_frameworks` rows should move. The rows that actually test this boundary are
**fastai**, **timm** and **torchvision**, which this sweep proposes as new rows here. They are
vision-first libraries, not frameworks the rest of the stack imports (Q2).

**Contested products**

| product | where it is now | recommendation | reason |
|---|---|---|---|
| segment-anything (SAM) | `scientific_ai_models` tail | **move here**, merged with sam2 | That category is "models trained on instrument, measurement, or scientific-simulation data rather than human-authored text, images" (sources/categories/scientific_ai_models.yaml). SAM is a general image-segmentation model. |
| sam2 | `scientific_ai_models` tail | **move here, fold into segment-anything** | Vendor sells "Segment Anything" (SAM, SAM 2, SAM 3). SAM 3 released 2025-11-19 (W0004), repo live (F0152), HF facebook/sam3 2,113,397 / 30d (F0386). SAM 3's license is a custom "SAM License" (F0333), while SAM/SAM 2 are Apache-2.0 (F0444, F0443). Most restrictive = SAM License. |
| DINOv3 / "timm mirrors" | excluded from `embeddings_retrieval`, pointer to #9 (sources/categories/embeddings_retrieval.yaml) | **own here** as `dino` and `timm` | 2026-09-25 ruling on #600. The pointer in embeddings_retrieval.yaml should be edited to say #600. |
| clip, openclip, siglip | `embeddings_retrieval` head | stay | Their reason for fame is retrieval. timm's hosted SigLIP/CLIP checkpoints (F0006) are mirrors and count for neither. |
| Perception Encoder | absent | → `embeddings_retrieval` (or brief 2) | Contrastive vision–language encoder (W0015). |
| Grounding DINO, Falcon Perception | absent | → brief 2 `multimodal_models` (flag to sibling) | Text-prompted detection/segmentation (W0013, F0412). |
| pytorch-lightning | `ml_frameworks` | stay | Brief marked it (?). It is a DL training abstraction, not classic ML. |
| katib | `ml_orchestration` | stay | Anchor for putting HPO (Optuna/Hyperopt) there rather than here. |
| optuna, hyperopt | absent | → `ml_orchestration` | Tuning, not modelling (F0217, F0220). |
| shap, lime, captum, interpret | absent | → `evaluation_code` or sibling `responsible_ai_measurement` | Explains a model, fits none (F0223, F0226, F0237, F0232). |
| fiftyone | absent | → `dataset_processing_tools` | Dataset curation (F0144). |
| chronos (and other time-series FMs) | absent | open question (Q3) | autogluon/chronos-2 is the top model of HF author=autogluon, whose 26.2M / 30d (F0429) is mostly Chronos. Pretrained forecasters are the time-series analogue of TabPFN. Repo live (F0492). |
| medsam, pathology backbones | absent | → `scientific_ai_models` | Domain-trained (F0004, F0006). |
| mediapipe | absent | here (edge boundary noted) | Perception pipelines; `edge_hardware` holds boards, not libraries. |

## 4. Capability quantity

**No single quantity orders the whole set cleanly. That is a finding.** The best candidate is
**how much of the prediction task the product does for you**, which roughly nests:

1. **Primitives.** Operations and transforms a model is built from, with no learner:
   OpenCV, scikit-image, Kornia, Albumentations, supervision.
2. **One learner family.** A single algorithm, well engineered: XGBoost, LightGBM, CatBoost,
   Prophet, HDBSCAN, UMAP, NGBoost.
3. **Toolkit.** Many learners plus pipelines, evaluation and a model zoo: scikit-learn,
   statsmodels, sktime, spaCy, Ultralytics, Detectron2, timm, MONAI. Contains rung 2.
4. **Pretrained, usable without task training.** Zero-shot or in-context on a new task:
   TabPFN, TabFM, SAM, Depth Anything, DINO features. Contains 3 only loosely.
5. **Automated end to end.** Searches, fits and ensembles for you, and now embeds rung-4
   models (AutoGluon ships Mitra checkpoints, F0402). **Anchor: AutoGluon**, with closed
   comparator DataRobot Predictive AI (F0513).

The weakness is between rungs 3–5 across sub-areas. A CV toolkit and a tabular AutoML system are
not more or less of the same thing, and rung 4 vs 5 is not a clean containment for vision (no
vision AutoML row surfaced). If the category splits (Q1), each half gets a cleaner quantity:
tabular gets the rung ladder above, and CV gets task coverage (classify → detect → segment →
track/depth, anchor Ultralytics or Detectron2). Benchmarks exist per task (COCO AP is cited for
RF-DETR in W0002; TabPFN reports win rates against XGBoost in W0003), but none spans the set.

## 5. Scoring ladder inputs

- **Ladders:** software rows → `software` (59). Model rows → `pretrained` (22). Backbones and
  tabular FMs are pretrained from scratch, so the data/code-release questions `pretrained` asks
  apply unchanged, which argues against the fine-tune `model` ladder. Recipe shape:
  `extends: {model: pretrained, software: software}`. Weights: adopt 0.6 / cap 0.4, matching
  `ml_frameworks` and `document_conversion`, because the adoption instrument here is unusually
  strong. This is a recommendation (Q10).
- **License strings met** (text read unless noted):

| license | carried by | note |
|---|---|---|
| BSD-3-Clause | scikit-learn, statsmodels, umap, hdbscan, river, skrub, mlpack, torchvision, scikit-image, sktime, auto-sklearn, dask-ml, tabicl (code+weights), captum*, hyperopt* | mlpack, scikit-image and tabicl are labelled `other` by GitHub, but the text is BSD-3 (F0279, F0320, F0356) |
| BSD-2-Clause | pyod, lime* | |
| MIT | lightgbm, imbalanced-learn, spacy, flair, textblob, supervision, lightly, torchgeo, prophet, pmdarima, flaml, ml-net, birefnet, eomt, fasttext*, shap*, optuna*, interpret*, mask2former* | flair is labelled `other` (F0062), but the text is MIT (F0283) |
| Apache-2.0 | xgboost, catboost, cuml, h2o-3, ngboost, perpetual, nltk, stanza, opencv, timm, detectron2, mmdetection, kornia, mediapipe, paddledetection, monai, fastai, darts, statsforecast, neuralforecast, gluonts, autogluon, rt-detr, rf-detr, d-fine, deim, sap-rpt-1, nori, tabpfn (code), tabfm (code), depth-anything (code), dino (DINOv2 only) | tabpfn: W0003 says "modified Apache", but the LICENSE at HEAD is unmodified Apache-2.0 (F0355). The modification lives in the weights licenses |
| LGPL-2.1 | gensim | |
| LGPL-3.0 | tpot | |
| GPL-3.0 | corenlp, yolov9* | |
| AGPL-3.0 | ultralytics (+ commercial Enterprise License, W0018), albumentations (AlbumentationsX), lightly-train, yolov10*, yolov12* | |
| BSL-1.0 (Boost) | dlib (F0329) | **Flag:** do not confuse with BSL-1.1 (Business Source), which `software.yaml` lists as source-available. Boost is OSI-approved. |
| FSL-1.1-MIT | pycaret (F0371) | **Flag, custom/unlisted:** `software.yaml` names FSL-1.1-ALv2 but not the MIT-future variant. PyPI still says MIT (F0209). |
| CC-BY-NC-4.0 | depth-anything (Large/DA3 weights), cotracker, sapiens v1, rmbg (via bria-rmbg-2.0 link) | |
| CC-BY-4.0 | tabstar weights | permissive_non_osi (per the speech ruling's precedent) |
| DINOv3 License | dino | **custom**, Meta; includes trade-control/ITAR terms (F0339) |
| SAM License | segment-anything (SAM 3) | **custom**, Meta (F0333). Contested row, not a new one |
| Sapiens2 License | sapiens | **custom** (F0494) |
| NVIDIA Source Code License (non-commercial) | segformer (F0347), radio code (F0496) | research/evaluation only |
| NVIDIA Open Model License | radio weights (F0453) | already in model/pretrained examples |
| TABPFN-3 License v1.0 / tabpfn-2.5-license-v1.1 / priorlabs-1-1 | tabpfn weights | **custom, non-commercial/non-production** (F0419) |
| TabFM Non-Commercial License v1.0 | tabfm weights | **custom** (F0420) |
| Stable AI Technology Co. License v1.0 (Apache-derived + attribution/naming) | limix code | **custom** (F0369) |
| stableai-limix-non-commercial-license-v1.0 | limix weights | **custom** (F0404, F0421) |
| EXAONE AI Model License 1.2 - NC | exaone-tabular | **custom** (F0517) |
| apple-amlr / Apple sample-code license | depth-pro | **custom** (F0495, F0418) |
| MIT code + non-commercial models (README) | insightface | no LICENSE file at repo root; README states the split (F0455) |
| Roboflow Inference: Apache core + enterprise directories | roboflow-inference* | parked (F0326) |

`*` = parked row, listed so the maintainer sees the string.

## 6. Accepted candidates

### 6a. Registry rows

See `rows.yaml` (validated against `docs/schemas/registry.schema.json`; 81 rows). Artifact
choices worth knowing:
- **One artifact per kind.** For multi-checkpoint lines, the HF id is the current flagship
  checkpoint, and the family sum is in 6b.
- **Packages** are declared only where PyPI `project_urls` (or ecosyste.ms `repository_url`) point
  back at the declared repo; each is cited in 6b. Exceptions stated in 6b: opencv-python is built
  from the OpenCV org's packaging repo, and tabstar's install line comes from its card.
- **ml-net** carries github only, because NuGet has no schema field.
- **nori** carries HF + PyPI but no github, because its repo was named on the card and not fetched.

```yaml
# Seed rows for the proposed classic_ml_cv category (issue #600), swept 2026-09-26.
# Signal-only; no scores. Evidence per row in sweep.md section 6b (fetch ids in fetch-log.tsv / web-log.tsv).
category: classic_ml_cv
products:
- slug: scikit-learn
  display_name: scikit-learn
  type: software
  org: scikit-learn
  github: scikit-learn/scikit-learn
  pypi: scikit-learn
- slug: xgboost
  display_name: XGBoost
  type: software
  org: dmlc
  github: dmlc/xgboost
  pypi: xgboost
- slug: lightgbm
  display_name: LightGBM
  type: software
  org: lightgbm-org
  github: lightgbm-org/LightGBM
  pypi: lightgbm
- slug: catboost
  display_name: CatBoost
  type: software
  org: yandex
  github: catboost/catboost
  pypi: catboost
- slug: statsmodels
  display_name: statsmodels
  type: software
  org: statsmodels
  github: statsmodels/statsmodels
  pypi: statsmodels
- slug: imbalanced-learn
  display_name: imbalanced-learn
  type: software
  org: scikit-learn-contrib
  github: scikit-learn-contrib/imbalanced-learn
  pypi: imbalanced-learn
- slug: pyod
  display_name: PyOD
  type: software
  org: yzhao062
  github: yzhao062/pyod
  pypi: pyod
- slug: umap
  display_name: UMAP
  type: software
  org: lmcinnes
  github: lmcinnes/umap
  pypi: umap-learn
- slug: hdbscan
  display_name: HDBSCAN
  type: software
  org: scikit-learn-contrib
  github: scikit-learn-contrib/hdbscan
  pypi: hdbscan
- slug: cuml
  display_name: cuML
  type: software
  org: nvidia
  github: NVIDIA/cuml
  pypi: cuml-cu12
- slug: river
  display_name: River
  type: software
  org: online-ml
  github: online-ml/river
  pypi: river
- slug: skrub
  display_name: skrub
  type: software
  org: skrub-data
  github: skrub-data/skrub
  pypi: skrub
- slug: mlpack
  display_name: mlpack
  type: software
  org: mlpack
  github: mlpack/mlpack
  pypi: mlpack
- slug: h2o-3
  display_name: H2O-3
  type: software
  org: h2o-ai
  github: h2oai/h2o-3
  pypi: h2o
- slug: ngboost
  display_name: NGBoost
  type: software
  org: stanfordmlgroup
  github: stanfordmlgroup/ngboost
  pypi: ngboost
- slug: perpetual
  display_name: Perpetual
  type: software
  org: perpetual-ml
  github: perpetual-ml/perpetual
  pypi: perpetual
- slug: ml-net
  display_name: ML.NET
  type: software
  org: microsoft
  github: dotnet/machinelearning
- slug: dask-ml
  display_name: Dask-ML
  type: software
  org: dask
  github: dask/dask-ml
  pypi: dask-ml
- slug: spacy
  display_name: spaCy
  type: software
  org: explosion
  github: explosion/spaCy
  pypi: spacy
- slug: nltk
  display_name: NLTK
  type: software
  org: nltk
  github: nltk/nltk
  pypi: nltk
- slug: gensim
  display_name: Gensim
  type: software
  org: rare-technologies
  github: piskvorky/gensim
  pypi: gensim
- slug: stanza
  display_name: Stanza
  type: software
  org: stanford-nlp
  github: stanfordnlp/stanza
  pypi: stanza
- slug: corenlp
  display_name: Stanford CoreNLP
  type: software
  org: stanford-nlp
  github: stanfordnlp/CoreNLP
- slug: flair
  display_name: Flair
  type: software
  org: flairnlp
  github: flairNLP/flair
  pypi: flair
- slug: textblob
  display_name: TextBlob
  type: software
  org: sloria
  github: sloria/TextBlob
  pypi: textblob
- slug: opencv
  display_name: OpenCV
  type: software
  org: opencv
  github: opencv/opencv
  pypi: opencv-python
- slug: timm
  display_name: timm (PyTorch Image Models)
  type: software
  org: hugging-face
  github: huggingface/pytorch-image-models
  pypi: timm
- slug: torchvision
  display_name: torchvision
  type: software
  org: pytorch-foundation
  github: pytorch/vision
  pypi: torchvision
- slug: ultralytics
  display_name: Ultralytics YOLO
  type: software
  org: ultralytics
  github: ultralytics/ultralytics
  pypi: ultralytics
- slug: detectron2
  display_name: Detectron2
  type: software
  org: meta
  github: facebookresearch/detectron2
- slug: mmdetection
  display_name: MMDetection
  type: software
  org: openmmlab
  github: open-mmlab/mmdetection
  pypi: mmdet
- slug: kornia
  display_name: Kornia
  type: software
  org: kornia
  github: kornia/kornia
  pypi: kornia
- slug: albumentations
  display_name: Albumentations
  type: software
  org: albumentations-team
  github: albumentations-team/AlbumentationsX
  pypi: albumentationsx
- slug: supervision
  display_name: supervision
  type: software
  org: roboflow
  github: roboflow/supervision
  pypi: supervision
- slug: scikit-image
  display_name: scikit-image
  type: software
  org: scikit-image
  github: scikit-image/scikit-image
  pypi: scikit-image
- slug: mediapipe
  display_name: MediaPipe
  type: software
  org: google
  github: google-ai-edge/mediapipe
  pypi: mediapipe
- slug: paddledetection
  display_name: PaddleDetection
  type: software
  org: paddlepaddle
  github: PaddlePaddle/PaddleDetection
- slug: monai
  display_name: MONAI
  type: software
  org: project-monai
  github: Project-MONAI/MONAI
  pypi: monai
- slug: lightly
  display_name: Lightly
  type: software
  org: lightly-ai
  github: lightly-ai/lightly
  pypi: lightly
- slug: lightly-train
  display_name: LightlyTrain
  type: software
  org: lightly-ai
  github: lightly-ai/lightly-train
  pypi: lightly-train
- slug: fastai
  display_name: fastai
  type: software
  org: fastai
  github: fastai/fastai
  pypi: fastai
- slug: dlib
  display_name: dlib
  type: software
  org: davisking
  github: davisking/dlib
  pypi: dlib
- slug: insightface
  display_name: InsightFace
  type: software
  org: deepinsight
  github: deepinsight/insightface
  pypi: insightface
- slug: torchgeo
  display_name: TorchGeo
  type: software
  org: torchgeo
  github: torchgeo/torchgeo
  pypi: torchgeo
- slug: sktime
  display_name: sktime
  type: software
  org: sktime
  github: sktime/sktime
  pypi: sktime
- slug: darts
  display_name: Darts
  type: software
  org: unit8
  github: unit8co/darts
  pypi: darts
- slug: statsforecast
  display_name: StatsForecast
  type: software
  org: nixtla
  github: Nixtla/statsforecast
  pypi: statsforecast
- slug: neuralforecast
  display_name: NeuralForecast
  type: software
  org: nixtla
  github: Nixtla/neuralforecast
  pypi: neuralforecast
- slug: prophet
  display_name: Prophet
  type: software
  org: meta
  github: facebook/prophet
  pypi: prophet
- slug: pmdarima
  display_name: pmdarima
  type: software
  org: alkaline-ml
  github: alkaline-ml/pmdarima
  pypi: pmdarima
- slug: gluonts
  display_name: GluonTS
  type: software
  org: amazon-web-services
  github: awslabs/gluonts
  pypi: gluonts
- slug: autogluon
  display_name: AutoGluon
  type: software
  org: autogluon
  github: autogluon/autogluon
  pypi: autogluon
- slug: flaml
  display_name: FLAML
  type: software
  org: microsoft
  github: microsoft/FLAML
  pypi: flaml
- slug: pycaret
  display_name: PyCaret
  type: software
  org: pycaret
  github: pycaret/pycaret
  pypi: pycaret
- slug: tpot
  display_name: TPOT
  type: software
  org: epistasislab
  github: EpistasisLab/tpot
  pypi: tpot
- slug: auto-sklearn
  display_name: auto-sklearn
  type: software
  org: automl-freiburg
  github: automl/auto-sklearn
  pypi: auto-sklearn
- slug: dino
  display_name: DINO (DINOv2, DINOv3)
  type: model
  org: meta
  github: facebookresearch/dinov3
  huggingface_model: facebook/dinov3-vitl16-pretrain-lvd1689m
- slug: radio
  display_name: C-RADIO
  type: model
  org: nvidia
  github: NVlabs/RADIO
  huggingface_model: nvidia/C-RADIOv3-H
- slug: depth-anything
  display_name: Depth Anything
  type: model
  org: bytedance-seed-volcano-engine
  github: ByteDance-Seed/Depth-Anything-3
  huggingface_model: depth-anything/DA3-LARGE
  pypi: depth-anything-3
- slug: depth-pro
  display_name: Depth Pro
  type: model
  org: apple
  github: apple-aiml-research/ml-depth-pro
  huggingface_model: apple/DepthPro-hf
- slug: rt-detr
  display_name: RT-DETR
  type: model
  org: lyuwenyu
  github: lyuwenyu/RT-DETR
  huggingface_model: PekingU/rtdetr_v2_r18vd
- slug: rf-detr
  display_name: RF-DETR
  type: model
  org: roboflow
  github: roboflow/rf-detr
  huggingface_model: Roboflow/rf-detr-base
  pypi: rfdetr
- slug: d-fine
  display_name: D-FINE
  type: model
  org: peterande
  github: Peterande/D-FINE
  huggingface_model: ustc-community/dfine-xlarge-coco
- slug: deim
  display_name: DEIM
  type: model
  org: intellindust
  github: Intellindust-AI-Lab/DEIM
- slug: birefnet
  display_name: BiRefNet
  type: model
  org: zhengpeng7
  github: ZhengPeng7/BiRefNet
  huggingface_model: ZhengPeng7/BiRefNet
- slug: rmbg
  display_name: BRIA RMBG
  type: model
  org: bria-ai
  huggingface_model: briaai/RMBG-2.0
- slug: segformer
  display_name: SegFormer
  type: model
  org: nvidia
  github: NVlabs/SegFormer
  huggingface_model: nvidia/segformer-b0-finetuned-ade-512-512
- slug: sapiens
  display_name: Sapiens
  type: model
  org: meta
  github: facebookresearch/sapiens2
  huggingface_model: facebook/sapiens2-seg-0.4b
- slug: eomt
  display_name: EoMT
  type: model
  org: tue-mps
  github: tue-mps/eomt
  huggingface_model: tue-mps/coco_panoptic_eomt_large_640
- slug: cotracker
  display_name: CoTracker
  type: model
  org: meta
  github: facebookresearch/co-tracker
  huggingface_model: facebook/cotracker3
- slug: tabpfn
  display_name: TabPFN
  type: model
  org: prior-labs
  github: PriorLabs/TabPFN
  huggingface_model: Prior-Labs/tabpfn_3
  pypi: tabpfn
- slug: tabicl
  display_name: TabICL
  type: model
  org: inria-soda
  github: soda-inria/tabicl
  pypi: tabicl
- slug: sap-rpt-1
  display_name: SAP RPT-1 (OSS)
  type: model
  org: sap
  github: SAP-samples/sap-rpt-1-oss
  huggingface_model: SAP/sap-rpt-1-oss
- slug: limix
  display_name: LimiX
  type: model
  org: stable-ai
  github: limix-ldm-ai/LimiX
  huggingface_model: stable-ai/LimiX-2
- slug: tabfm
  display_name: TabFM
  type: model
  org: google-research
  github: google-research/tabfm
  huggingface_model: google/tabfm-1.0.0-pytorch
- slug: nori
  display_name: Nori
  type: model
  org: synthefy
  huggingface_model: Synthefy/Nori
  pypi: synthefy-nori
- slug: tabstar
  display_name: TabSTAR
  type: model
  org: alanarazi7
  huggingface_model: alana89/TabSTAR
  pypi: tabstar
- slug: exaone-tabular
  display_name: EXAONE Tabular
  type: model
  org: lg-ai-research
  github: LGAI-Research/EXAONE-Tabular
  huggingface_model: LG-AI-Research/EXAONE-Tabular
- slug: google-cloud-vision
  display_name: Google Cloud Vision API
  type: software
  org: google-cloud
  homepage: https://cloud.google.com/vision
- slug: amazon-rekognition
  display_name: Amazon Rekognition
  type: software
  org: amazon-web-services
  homepage: https://aws.amazon.com/rekognition/
- slug: datarobot
  display_name: DataRobot Predictive AI
  type: software
  org: datarobot
  homepage: https://www.datarobot.com/platform/
```

### 6b. Evidence table

| slug | open status | license(s) | archived/fork | last push | last release | adoption signal | member checkpoints/SKUs | org handle | notes |
|---|---|---|---|---|---|---|---|---|---|
| scikit-learn | open | BSD-3-Clause (LICENSE text F0276) | no / no F0012 | 2026-09-19 F0012 | 1.9.1, 2026-09-10 F0010 F0009 | PyPI 183,826,718 / last-month F0009 | - | github scikit-learn | PyPI project_urls source -> scikit-learn/scikit-learn F0010 |
| xgboost | open | Apache-2.0 (F0254) | no / no F0011 | 2026-09-20 F0011 | 3.4.1, 2026-08-15 F0008 | PyPI 29,901,651 / last-month F0013 | - | github dmlc | project_urls -> dmlc/xgboost F0008 |
| lightgbm | open | MIT (F0253; copyright Microsoft Corporation and the LightGBM developers) | no / no F0235 | 2026-09-24 F0235 | 4.7.0, 2026-07-18 F0015 | PyPI 18,191,249 / last-month F0016 | - | github lightgbm-org (was microsoft/LightGBM: ecosyste.ms 404 on old name F0014) | Repo moved from microsoft/ to lightgbm-org/; PyPI project_urls already point at lightgbm-org F0015. Org slug is a judgment call (Q5). |
| catboost | open | Apache-2.0, copyright YANDEX LLC (F0255) | no / no F0017 | 2026-09-19 F0017 | 1.2.10, 2026-02-18 F0018 F0450 | PyPI 5,053,734 / last-month F0450 | - | github catboost | project_urls -> catboost/catboost F0018 |
| statsmodels | open | BSD-3-Clause (F0265) | no / no F0020 | 2026-09-24 F0020 | 0.15.0, 2026-08-27 F0022 (latest file upload 2026-08-30 F0021) | PyPI 31,358,911 / last-month F0022 | - | github statsmodels | project_urls -> statsmodels/statsmodels F0021 |
| imbalanced-learn | open | MIT (F0257) | no / no F0023 | 2026-06-29 F0023 | 0.14.2, 2026-06-07 F0024 | PyPI 6,711,265 / last-month F0025 | - | github scikit-learn-contrib |  |
| pyod | open | BSD-2-Clause (F0259) | no / no F0026 | 2026-09-17 F0026 | 3.6.6, 2026-09-17 F0027 | PyPI 2,770,131 / last-month F0028 | - | github yzhao062 (personal account) | Outlier detection. |
| umap | open | BSD-3-Clause (F0271) | no / no F0029 | 2026-09-24 F0029 | 0.5.12, 2026-04-08 F0030 | PyPI 5,340,690 / last-month F0031 | - | github lmcinnes (personal) | PyPI name umap-learn; project_urls -> lmcinnes/umap F0030. PyPI `umap` is a different project (not fetched; do not declare). |
| hdbscan | open | BSD-3-Clause (F0262) | no / no F0032 | 2026-06-12 F0032 | 0.8.44, 2026-06-01 F0033 | PyPI 2,037,372 / last-month F0034 | - | github scikit-learn-contrib | Standalone density-clustering library. |
| cuml | open | Apache-2.0 (F0263) | no / no F0249 | 2026-09-24 F0245 | 26.8.0, 2026-08-06 F0036 | PyPI cuml-cu12 418,656 / last-month F0037 | cuml-cu12, cuml-cu13 wheels (cu13 exists F0529; only cu12 counted) | github NVIDIA (was rapidsai/cuml: ecosyste.ms 404 F0035; ungh canonical NVIDIA/cuml F0245) | GPU scikit-learn-compatible estimators. Downloads split across CUDA-suffixed wheels; the figure undercounts. |
| river | open | BSD-3-Clause (F0264) | no / no F0038 | 2026-09-21 F0038 | 0.26.1, 2026-08-21 F0039 | PyPI 174,766 / last-month F0040 | - | github online-ml | Online/streaming ML. |
| skrub | open | BSD-3-Clause (F0278) | no / no F0041 | 2026-09-18 F0041 | 0.10.1, 2026-09-01 F0042 | PyPI 142,039 / last-month F0043 | - | github skrub-data | Tabular preprocessing for scikit-learn pipelines (formerly dirty_cat per LICENSE F0278). Borderline: feature engineering, not an estimator library (Q3). |
| mlpack | open | BSD-3-Clause (F0279; GitHub label 'other' F0044 - the text is plain BSD-3) | no / no F0044 | 2026-09-17 F0044 | 4.8.0, 2026-06-17 F0046 (latest file upload 2026-06-19 F0045) | PyPI 1,430 / last-month F0046 (PyPI is one install channel; others not measured) | - | github mlpack | Label lies: ecosyste.ms 'other', text is BSD-3. |
| h2o-3 | open | Apache-2.0 (F0270) | no / no F0047 | 2026-09-25 F0047 | 3.46.0.12, 2026-08-12 F0048 | PyPI 156,866 / last-month F0049 | - | github h2oai | Distributed ML + AutoML. The '-3' is part of the repo name h2oai/h2o-3 (F0047), not a version token. |
| ngboost | open | Apache-2.0 (LICENSE text F0521; ecosyste.ms F0440) | no / no F0440 | 2026-09-02 F0440 | 2026-06-26 F0446 | PyPI 180,490 / last-month F0446 | - | github stanfordmlgroup | Surfaced by search W0014, not in the brief. |
| perpetual | open | Apache-2.0 (LICENSE text F0522; ecosyste.ms F0439) | no / no F0439 | 2026-04-02 F0439 | 2026-03-06 F0445 | PyPI 6,093 / last-month F0445 | - | github perpetual-ml | Surfaced by search W0014. Rust core. |
| ml-net | open | MIT, copyright .NET Foundation (F0497) | no / no F0490 | 2026-09-18 F0490 | NuGet Microsoft.ML 5.0.0 stable F0510 | NuGet Microsoft.ML 17,259,797 lifetime total F0510 (no monthly figure; NuGet has no registry field in the schema) | - | github dotnet | Surfaced by search W0008. Only .NET entry; its adoption channel (NuGet) is not a schema field, so the row carries github only. |
| dask-ml | open | BSD-3-Clause (F0500) | no / no F0491 | 2025-09-27 F0491 | 2025-02-08 F0502 | PyPI 48,533 / last-month F0502 | - | github dask | Surfaced by search W0008. Last release 19 months old; pushed within 12 months. |
| spacy | open | MIT (F0272) | no / no F0050 | 2026-08-24 F0050 | 3.8.16, 2026-08-24 F0051 F0449 | PyPI 21,026,566 / last-month F0449 | spaCy pipelines (en_core_web_* etc., not measured) | github explosion | Explosion is operating as a smaller company W0017. |
| nltk | open | Apache-2.0 (F0288) | no / no F0053 | 2026-09-23 F0053 | 3.10.3, 2026-08-12 F0054 | PyPI 42,263,867 / last-month F0055 | - | github nltk |  |
| gensim | open | LGPL-2.1 (F0292) | no / no F0056 | 2025-11-01 F0056 | 4.4.0, 2025-10-18 F0057 | PyPI 2,857,631 / last-month F0058 | - | github piskvorky (PyPI project_urls still say RaRe-Technologies/gensim F0057) | Canonical owner per ecosyste.ms is piskvorky F0056. |
| stanza | open | Apache-2.0 (F0280; GitHub label 'other' F0059) | no / no F0059 | 2026-09-20 F0059 | 1.14.0, 2026-07-15 F0060 | PyPI 719,497 / last-month F0061 | - | github stanfordnlp | Org slug reused from index (dspy). |
| corenlp | open | GPL-3.0 (F0295) | no / no F0068 | 2026-09-25 F0068 | v4.5.10, 2025-06-07 F0469 | stars only 10,121 F0068 (Java; Maven not fetched) | - | github stanfordnlp | Stars-only row. |
| flair | open | MIT (F0283; GitHub label 'other' F0062) | no / no F0062 | 2025-10-27 F0062 | 0.15.1, 2025-02-05 F0063 | PyPI 51,250 / last-month F0064 | - | github flairNLP | Last release 19 months old. |
| textblob | open | MIT (F0286) | no / no F0069 | 2026-09-22 F0069 | 0.20.1, 2026-07-18 F0070 | PyPI 3,735,355 / last-month F0071 | - | github sloria (personal) |  |
| opencv | open | Apache-2.0 (F0290); opencv-python packaging repo MIT (F0303) | no / no F0072 | 2026-09-25 F0072 | 4.14.0 GitHub 2026-07-19 F0484; opencv-python 5.0.0.93 on PyPI F0073; OpenCV 5.0 announced 2026-06 W0016 | PyPI opencv-python 29,918,110 / last-month F0452 | opencv-python, opencv-contrib-python (F0531), opencv-python-headless (F0532) wheels; only opencv-python counted | github opencv | The PyPI wheel is built from opencv/opencv-python (OpenCV org) F0452; declared because it is the documented pip path of the same org. ecosyste.ms latest_release date for the package is stale (2023) F0452 - PyPI JSON shows 5.0.0.93 F0073. |
| timm | open | Apache-2.0 (F0293); hosted weights licenses vary per checkpoint (e.g. apache-2.0 F0409) | no / no F0076 | 2026-09-18 F0076 | 1.0.30, 2026-09-22 F0077 | PyPI 10,328,111 / last-month F0078; HF author=timm top-1000 checkpoints 47,174,954 / 30d F0427 | timm/* HF checkpoints (1000+ F0427), incl. DINOv2/v3 and SigLIP mirrors | github huggingface; HF timm | Ruled into this category (issue #600 comment, 2026-09-25). HF 'timm' namespace mirrors other vendors' weights (DINO, SigLIP) - do not count those toward timm's own adoption without care (Q6). |
| torchvision | open | BSD-3-Clause (F0294) | no / no F0079 | 2026-09-23 F0079 | 0.29.0, 2026-09-02 F0080 | PyPI 15,858,954 / last-month F0081 | - | github pytorch | Installed alongside torch; downloads partly reflect that pairing. |
| ultralytics | open | AGPL-3.0 (F0296) with a paid Enterprise License W0018; HF YOLO26/YOLO11 weights agpl-3.0 F0407 F0408 | no / no F0082 | 2026-09-19 F0082 | v8.4.150 GitHub 2026-09-12 F0486; PyPI 8.4.163 F0083 | PyPI 5,557,129 / last-month F0447 | YOLOv8, YOLO11, YOLO26 checkpoints (F0407 F0408; W0002 says YOLO26 released Jan 2026) | github ultralytics; HF Ultralytics | Library and its YOLO checkpoints are one product (the vendor ships both through one package). Dual license: AGPL or commercial. |
| detectron2 | open | Apache-2.0 (F0298) | no / no F0085 | 2026-08-19 F0085 | v0.6, 2021-11-15 F0456 | stars only 34,729 F0085 (not on PyPI) | - | github facebookresearch | No release since 2021; still pushed 2026-08. |
| mmdetection | open | Apache-2.0 (F0299) | no / no F0086 | 2024-08-21 F0086 | 3.3.0, 2024-01-05 F0087 | PyPI mmdet 136,099 / last-month F0088 | - | github open-mmlab | Dormant: no push in 25 months. Stands in for the OpenMMLab toolbox family (Q4). |
| kornia | open | Apache-2.0 (F0305) | no / no F0101 | 2026-09-25 F0101 | 0.8.3, 2026-05-19 F0102 | PyPI 2,191,987 / last-month F0103 | - | github kornia | Differentiable CV ops. |
| albumentations | open | AGPL-3.0 for AlbumentationsX (F0307; PyPI AGPL-3.0-only F0108); the archived original is MIT (F0306) | AlbumentationsX no / no F0107; original repo ARCHIVED F0104 | 2026-09-18 F0107 (original: 2025-06-25 F0104) | albumentationsx 2.4.10, 2026-09-14 F0108 (albumentations 2.0.8, 2025-05-27 F0105) | PyPI albumentationsx 10,732 / last-month F0109; frozen albumentations 2,741,847 / last-month F0106 | albumentations (MIT, archived) -> AlbumentationsX (AGPL) | github albumentations-team | Same team relicensed and moved the line to a new repo and package. Row points at the live successor; the usage still sits on the frozen MIT package (Q7). |
| supervision | open | MIT (F0313) | no / no F0110 | 2026-09-22 F0110 | 0.30.5, 2026-09-22 F0111 | PyPI 814,864 / last-month F0112 | - | github roboflow |  |
| scikit-image | open | BSD-3-Clause (F0320, DEP-5 style file; GitHub label 'other' F0113) | no / no F0113 | 2026-09-19 F0113 | 0.26.0, 2025-12-20 F0114 F0448 | PyPI 23,581,656 / last-month F0448 | - | github scikit-image |  |
| mediapipe | open | Apache-2.0 (F0310) | no / no F0116 | 2026-09-24 F0116 | 1.0.1, 2026-08-14 F0117 | PyPI 1,839,565 / last-month F0118 | - | github google-ai-edge (PyPI still links google/mediapipe F0117) | On-device perception pipelines; boundary with edge deployment (flagged, stays here). |
| paddledetection | open | Apache-2.0 (F0311) | no / no F0119 | 2026-05-28 F0119 | v2.8.1, 2025-02-14 F0479 | stars only 14,433 F0119 (PyPI name not verified) | PP-YOLOE, RT-DETR configs (not fetched) | github PaddlePaddle |  |
| monai | open | Apache-2.0 (F0314) | no / no F0123 | 2026-09-26 F0123 | 1.6.0, 2026-06-22 F0124 | PyPI 787,110 / last-month F0125 | - | github Project-MONAI | Medical imaging. Contest with scientific_ai_models is weak: that category holds models, this is a library. |
| lightly | open | MIT (F0328) | no / no F0126 | 2026-09-21 F0126 | 1.5.26, 2026-07-27 F0127 | PyPI 82,095 / last-month F0128 | - | github lightly-ai | Self-supervised learning for vision. |
| lightly-train | open | AGPL-3.0 (F0317) | no / no F0129 | 2026-09-14 F0129 | 0.17.0, 2026-07-28 F0130 | PyPI 5,377 / last-month F0131 | - | github lightly-ai | Separate product and license from `lightly`. |
| fastai | open | Apache-2.0 (F0318) | no / no F0132 | 2026-09-14 F0132 | 2.8.12, 2026-09-09 F0133 | PyPI 457,458 / last-month F0134 | - | github fastai | General DL training library, famous for vision; boundary with ml_frameworks (Q2). |
| dlib | open | BSL-1.0 (F0329) | no / no F0135 | 2026-09-23 F0135 | 20.0.1, 2026-03-29 F0136 | PyPI 176,440 / last-month F0137 | - | github davisking (personal) | C++ ML + CV toolkit. |
| insightface | open | Code MIT per README (F0455; no LICENSE file at repo root, 6 names tried); models and training data non-commercial research only (F0455) | no / no F0138 | 2026-09-09 F0138 | 2.0, 2026-09-08 F0139 | PyPI 1,045,422 / last-month F0140 | buffalo_* model packs (not fetched) | github deepinsight | Code/weights license split: record both. |
| torchgeo | open | MIT (F0323) | no / no F0236 | 2026-09-25 F0248 | 0.10.0, 2026-08-14 F0142 | PyPI 42,497 / last-month F0143 | - | github torchgeo (was microsoft/torchgeo: ecosyste.ms 404 F0141) | Geospatial imagery; contest with scientific_ai_models weak (library, not model). |
| sktime | open | BSD-3-Clause (F0359) | no / no F0181 | 2026-09-20 F0181 | 1.2.0, 2026-09-22 F0182 | PyPI 1,126,565 / last-month F0183 | - | github sktime |  |
| darts | open | Apache-2.0 (F0361) | no / no F0184 | 2026-09-18 F0184 | 0.47.0, 2026-09-04 F0185 | PyPI darts 183,156 / last-month F0186 | u8darts is a second PyPI name (exists F0530; not summed) | github unit8co | Undercounts: u8darts not summed. |
| statsforecast | open | Apache-2.0 (F0362) | no / no F0187 | 2026-09-21 F0187 | 2.1.1, 2026-07-16 F0188 | PyPI 1,553,614 / last-month F0189 | - | github Nixtla |  |
| neuralforecast | open | Apache-2.0 (F0364) | no / no F0190 | 2026-09-18 F0190 | 3.2.2, 2026-09-08 F0191 | PyPI 273,230 / last-month F0192 | - | github Nixtla | Separate package and repo from statsforecast. |
| prophet | open | MIT (F0365) | no / no F0193 | 2026-08-27 F0193 | 1.4.0, 2026-08-15 F0194 | PyPI 4,058,052 / last-month F0195 | - | github facebook |  |
| pmdarima | open | MIT (F0366) | no / no F0196 | 2025-11-17 F0196 | 2.1.1, 2025-11-17 F0197 | PyPI 1,607,451 / last-month F0198 | - | github alkaline-ml |  |
| gluonts | open | Apache-2.0 (F0367) | no / no F0199 | 2026-07-31 F0199 | 0.17.0, 2026-07-31 F0200 | PyPI 286,670 / last-month F0201 | - | github awslabs | Org slug reused from index. |
| autogluon | open | Apache-2.0 (F0368) | no / no F0202 | 2026-09-19 F0202 | 1.6.3 F0203; 2026-09-18 F0451 | PyPI autogluon meta-package 98,236 / last-month F0451 (sub-packages autogluon.tabular etc. not summed) | Mitra tabular FM checkpoints (HF autogluon/mitra-classifier 231,157 / 30d F0402) | github autogluon; HF autogluon | HF author=autogluon sums 26.2M / 30d F0429 but that is mostly Chronos time-series models (top=autogluon/chronos-2) - not this row's usage. |
| flaml | open | MIT (F0370) | no / no F0205 | 2026-09-22 F0205 | 2.7.0, 2026-09-18 F0206 | PyPI 327,311 / last-month F0207 | - | github microsoft |  |
| pycaret | source-available | FSL-1.1-MIT, 'Copyright 2026 Moez Ali' (LICENSE text F0371). PyPI metadata still says MIT F0209 and GitHub label 'other' F0208 - the text governs | no / no F0208 | 2026-07-23 F0208 | 3.3.2, 2024-04-28 F0209 | PyPI 226,451 / last-month F0210 | - | github pycaret | Relicensed to Functional Source License. Last PyPI release (2024, MIT) predates the relicense; the repo HEAD is FSL. Flag for tier placement. |
| tpot | open | LGPL-3.0 (F0372) | no / no F0211 | 2025-09-11 F0211 | 1.1.0, 2025-07-03 F0212 | PyPI 14,887 / last-month F0213 | - | github EpistasisLab | Last push 12.5 months ago. |
| auto-sklearn | open | BSD-3-Clause (F0383) | no / no F0214 | 2026-09-15 F0214 | 0.15.0, 2022-09-20 F0215 | PyPI 4,393 / last-month F0216 | - | github automl | No release in 4 years although the repo was pushed in 2026-09. |
| dino | open-weights | DINOv3: custom 'DINOv3 License' (repo F0339; HF license other/dinov3-license, gated manual F0384). DINOv2: Apache-2.0 (repo F0330; HF F0385). Most restrictive across SKUs = DINOv3 License | dinov3 no / no F0151; dinov2 no / no F0150 | dinov3 2026-07-15 F0151; dinov2 2026-06-03 F0150 | no GitHub releases listed F0458 F0457; DINOv3 HF weights 2025-08-19 F0384 | HF facebook DINO checkpoints 9,914,994 / 30d F0422 (plus timm mirrors, e.g. timm/vit_small_patch14_dinov2 1,289,215 F0006) | DINO v1 (facebook/dino-vitb16), DINOv2 small/base/large/giant, DINOv3 ViT S/B/L/H+/7B and ConvNeXt F0006 F0422 | github facebookresearch; HF facebook | Product-line rule: one row for DINO; v2 and v3 are versions. embeddings_retrieval.yaml already excludes DINOv3 and points it at #9; the 2026-09-25 ruling moves it here. |
| radio | open-weights | Code: NVIDIA Source Code License for RADIO, non-commercial (F0496). Weights: nvidia-open-model-license (HF cardData F0453; W0012) | no / no F0438 | 2026-05-29 F0438 | no GitHub releases listed F0471 | HF nvidia RADIO checkpoints 62,322 / 30d F0454 (C-RADIOv3-H alone 2,735 F0453) | C-RADIO, C-RADIOv2, v3 (B/L/H/g), v4 (H, SO400M) F0454 W0012 | github NVlabs; HF nvidia | Surfaced by search W0012, not in the brief. Agglomerative backbone distilled from CLIP, DINOv2, SAM (W0012). |
| depth-anything | open-weights | Code Apache-2.0 (DA3 F0334; V2 F0335). Weights mixed: V2-Small apache-2.0 (F0390), V2-Large cc-by-nc-4.0 (F0391), DA3-LARGE cc-by-nc-4.0 (F0389). Most restrictive = CC-BY-NC-4.0 | DA3 no / no F0153; V2 no / no F0156 | DA3 2026-07-27 F0153; V2 2026-03-24 F0156 | depth-anything-3 0.1.1, 2026-03-04 F0154 | HF author=depth-anything 4,577,714 / 30d F0424; PyPI depth-anything-3 5,212 / last-month F0155 | Depth Anything V1 (LiheYoung/*), V2 S/B/L + metric, DA3 SMALL/LARGE/GIANT/METRIC/MONO/NESTED F0005 | github ByteDance-Seed, DepthAnything; HF depth-anything | Surfaced from HF depth-estimation top-40 F0005. Org slug reused from index. |
| depth-pro | open-weights | Apple sample-code style license (repo LICENSE F0495; ecosyste.ms repo lookup 404 F0489); weights apple-amlr (F0418 F0505) | no / no F0527 (repo moved: apple/ml-depth-pro 404 on ecosyste.ms F0489) | 2026-09-11 F0527 | none listed W0020 | HF apple/DepthPro-hf 26,401 / 30d F0418; apple/DepthPro 5,488 F0505 | - | github apple-aiml-research (moved from apple/, F0527 F0489); HF apple | Surfaced from HF depth-estimation list F0005. 5,728 stars F0527. |
| rt-detr | open | Apache-2.0 (code F0336; weights apache-2.0 F0392) | no / no F0157 | 2026-08-17 F0157 | no GitHub releases listed F0462 | HF author=PekingU 2,113,211 / 30d F0425 | RT-DETR r18/r50/r101 (+O365), RT-DETRv2 F0002 | github lyuwenyu (personal); HF PekingU | Authoring institution not fetched; org slug is the repo owner handle (Q5). |
| rf-detr | open | Apache-2.0 (code F0338; HF weights apache-2.0 F0393) | no / no F0158 | 2026-09-18 F0158 | 1.10.1 GitHub 2026-09-07 F0485; PyPI 1.11.0, 2026-09-24 F0159 | PyPI rfdetr 416,071 / last-month F0160; HF author=Roboflow 90,156 / 30d F0426 | rf-detr base/nano/.../2XL, rf-detr-seg F0002 F0003; W0002 reports ICLR 2026 and 60.1 AP for 2XL | github roboflow; HF Roboflow | Surfaced by search W0002. |
| d-fine | open | Apache-2.0 (code F0340; weights apache-2.0 F0394) | no / no F0161 | 2026-08-19 F0161 | no GitHub releases listed F0463 | HF author=ustc-community 94,094 / 30d F0430 | D-FINE nano/small/.../xlarge F0002 | github Peterande (personal); HF ustc-community | Surfaced by search W0002. |
| deim | open | Apache-2.0 with copyright notice (F0341; GitHub label 'other' F0162) | no / no F0162 | 2026-03-24 F0162 | no GitHub releases listed F0473 | stars only 1,607 F0162 (HF not fetched) | - | github Intellindust-AI-Lab | DETR training recipe on D-FINE. Weak identity: could be a SKU of D-FINE lineage (kept separate: different org). |
| birefnet | open | MIT (code F0346; weights mit F0395) | no / no F0166 | 2026-09-02 F0166 | v1, 2024-05-13 F0464 | HF author=ZhengPeng7 1,279,955 / 30d F0431 | BiRefNet, _lite, _HR, _HR-matting F0003 | github/HF ZhengPeng7 (personal) | Dichotomous segmentation / background removal. Surfaced from HF list F0003. |
| rmbg | open-weights | HF license other/bria-rmbg-2.0 linking CC BY-NC 4.0 (F0396); gated auto F0396; README behind gate (401 F0519 - access limit, not a finding) | n/a (HF only) | HF lastModified 2026-04-06 F0396 | - | HF briaai/RMBG-2.0 547,561 / 30d F0396 (RMBG-1.4 326,522 F0003) | RMBG-1.4, RMBG-2.0 F0003 | HF briaai | Surfaced from HF list F0003. No GitHub repo fetched. |
| segformer | open-weights | NVIDIA Source Code License for SegFormer, non-commercial / research or evaluation only (F0347); HF card license 'other' F0397 F0520 | no / no F0167 | 2024-08-02 F0167 | no GitHub releases listed F0476 | HF nvidia/segformer-b0-finetuned-ade-512-512 368,469 / 30d F0397 (b1-b5 not summed F0003) | b0-b5, ADE/Cityscapes fine-tunes F0003 | github NVlabs; HF nvidia | Dormant since 2024-08. Surfaced from HF list F0003. |
| sapiens | open-weights | Sapiens2 License (custom, F0494; HF other/sapiens2-license F0398); Sapiens v1 CC-BY-NC-4.0 (F0350) | sapiens2 no / no F0488; v1 no / no F0169 | sapiens2 2026-05-24 F0488; v1 2024-11-18 F0169 | no GitHub releases listed (v1) F0477 | HF facebook/sapiens2-seg-0.4b 35,476 / 30d F0398 | Sapiens v1, Sapiens2 (seg 0.4b, ...) F0003 | github facebookresearch; HF facebook | Human-centric vision models. Surfaced from HF list F0003. |
| eomt | open | MIT (code F0352; weights mit F0411) | no / no F0170 | 2026-07-22 F0170 | no GitHub releases listed F0470 | HF author=tue-mps 132,121 / 30d F0434 | COCO/ADE/Cityscapes EoMT, eomt-dinov3 variants F0003 | github/HF tue-mps (TU/e Mobile Perception Systems Lab, F0352) | Surfaced from HF list F0003. |
| cotracker | open-weights | CC-BY-NC-4.0 (repo F0360; HF F0413) | no / no F0172 | 2026-03-03 F0172 | no GitHub releases listed F0468 | HF facebook/cotracker3 17,576 / 30d F0413 | CoTracker3 (F0413); earlier versions not fetched | github facebookresearch; HF facebook | Point tracking in video. |
| tabpfn | open-weights | Code Apache-2.0 (LICENSE F0355, plain text; W0003 calls it 'modified Apache' - the current file is unmodified). Weights: TABPFN-3 License v1.0, non-commercial/non-production (F0419; HF other/tabpfn-3-license-v1.0 F0399); v2.5 tabpfn-2.5-license-v1.1 F0401; v2 priorlabs-1-1 F0400 | no / no F0173 | 2026-09-21 F0173 | v9.0.0, 2026-09-15 F0487 F0174 | PyPI tabpfn 207,148 / last-month F0175; HF author=Prior-Labs 139,781 / 30d F0428 | TabPFN v2 clf/reg, 2.5, 2.6, 3, 3.5 F0007 | github PriorLabs; HF Prior-Labs | TabPFN-3 released May 2026 W0003. |
| tabicl | open | BSD-3-Clause, 'Soda team @ Inria' (F0356; GitHub label 'other' F0176); HF jingang/TabICL bsd-3-clause F0504 | no / no F0176 | 2026-06-05 F0176 | 2.2.0, 2026-09-02 F0177 | PyPI tabicl 133,045 / last-month F0178; HF jingang/TabICL reports 0 F0504 (HF id not declared) | TabICL, TabICLv2 (W0003) | github soda-inria; HF jingang | HF checkpoint jingang/TabICL (bsd-3-clause F0504) sits in a personal namespace with 0 reported downloads, so it is left off the row. Surfaced by search W0003. |
| sap-rpt-1 | open | Apache-2.0 (code F0357; HF weights apache-2.0, gated auto F0403) | no / no F0179 | 2025-11-27 F0179 | v1.1.2, 2025-11-27 F0480 | HF SAP/sap-rpt-1-oss 94,516 / 30d F0403 | - | github SAP-samples; HF SAP | Surfaced from HF tabular list F0007. Open satellite of a closed SAP RPT-1 service? Not fetched - do not assume (Q8). |
| limix | open-weights | Code: 'Stable AI Technology Co., Ltd. License v1.0', Apache-2.0-derived + Section 10 attribution and model-naming terms (F0369). Weights LimiX-2: stableai-limix-non-commercial-license-v1.0 (F0404; LICENSE F0421) | no / no F0250 | 2026-09-18 F0247 | V1.1.0, 2025-11-10 F0481 | HF stable-ai/LimiX-2 8,391 / 30d F0404 | LimiX, LimiX-2, LimiX-2M (W0003) | github limix-ldm-ai (ungh canonical F0247; old limix-ldm 404 F0180); HF stable-ai | Custom license: flag for tier placement. |
| tabfm | open-weights | Code Apache-2.0 (LICENSE text F0523; ecosyste.ms F0437). Weights: TabFM Non-Commercial License v1.0 (F0420; HF F0405) | no / no F0437 | 2026-09-18 F0437 | v1.0.1, 2026-07-21 F0472 | HF google tabfm 33,896 / 30d F0436 | tabfm-1.0.0-pytorch, -jax F0007 | github google-research; HF google | Released 2026-06-30 W0011. Surfaced from HF tabular list F0007 and search W0011. |
| nori | open | Apache-2.0 (HF card F0507, cardData F0414; PyPI license_expression Apache-2.0 F0514) | GitHub Synthefy/synthefy-nori named in card F0507, not fetched | HF lastModified 2026-08-24 F0414 | synthefy-nori 0.21.0 F0514 | HF author=Synthefy 269,601 / 30d F0435 | Nori, Nori-30M, Nori-100M F0007 | HF Synthefy | Tabular regression FM (F0507). Surfaced from HF tabular list F0007. github left off the row until the repo is fetched. |
| tabstar | open-weights | Weights CC-BY-4.0 (F0415 F0509); PyPI package MIT (F0515) | n/a | HF lastModified 2025-06-11 F0415 | 2026-03-15 F0515 | HF alana89/TabSTAR 91,172 / 30d F0415; PyPI tabstar 4,863 / last-month F0515 | - | HF alana89; GitHub alanarazi7 (logo URL in card F0509) | Built on intfloat/e5-small-v2 (F0509) - uses a text encoder. Surfaced from HF tabular list F0007. PyPI backlink not verified (ecosyste.ms repository_url null F0515) - package declared on the card's own install line F0509. |
| exaone-tabular | open-weights | EXAONE AI Model License Agreement 1.2 - NC, commercial use prohibited (F0517; HF other/exaone F0416) | ungh repo exists, created 2026-07-31 F0518 (archive flag not fetched) | 2026-08-27 F0518 | - | HF 67,150 / 30d F0416 | - | github LGAI-Research; HF LG-AI-Research | Surfaced from HF tabular list F0007. Name collides with LG's EXAONE LLM line (not in index); product line is the tabular model. |
| google-cloud-vision | closed | proprietary (no artifact) | n/a | n/a | n/a | none measurable; homepage title 'Vision AI: Image and visual AI tools / Google Cloud' F0512 | - | - | Capability surface of Google Cloud (not the platform). Pre-trained vision APIs F0512. Best-in-class claim is a judgment (Q9). |
| amazon-rekognition | closed | proprietary | n/a | n/a | n/a | none measurable; homepage F0511 | - | - | Image and video analysis API F0511 (Q9). |
| datarobot | closed | proprietary | n/a | n/a | n/a | none measurable; homepage F0513 | - | - | Surface is the predictive/AutoML product, linked from the platform page (predictive-ai path F0513), not the whole platform (Q9). |

### 6c. Source list

Every URL behind section 6, with fetch timestamp (UTC). F rows come from `fetch-log.tsv`, W rows
from `web-log.tsv`.

| id | http | fetched (UTC) | url | label |
|---|---|---|---|---|
| F0001 | 200 | 2026-09-26T20:00:54Z | https://huggingface.co/api/models?pipeline_tag=image-classification&sort=downloads&limit=40 | HF top40 by downloads: image-classification |
| F0002 | 200 | 2026-09-26T20:00:54Z | https://huggingface.co/api/models?pipeline_tag=object-detection&sort=downloads&limit=40 | HF top40 by downloads: object-detection |
| F0003 | 200 | 2026-09-26T20:00:54Z | https://huggingface.co/api/models?pipeline_tag=image-segmentation&sort=downloads&limit=40 | HF top40 by downloads: image-segmentation |
| F0004 | 200 | 2026-09-26T20:00:55Z | https://huggingface.co/api/models?pipeline_tag=mask-generation&sort=downloads&limit=40 | HF top40 by downloads: mask-generation |
| F0005 | 200 | 2026-09-26T20:00:55Z | https://huggingface.co/api/models?pipeline_tag=depth-estimation&sort=downloads&limit=40 | HF top40 by downloads: depth-estimation |
| F0006 | 200 | 2026-09-26T20:00:55Z | https://huggingface.co/api/models?pipeline_tag=image-feature-extraction&sort=downloads&limit=40 | HF top40 by downloads: image-feature-extraction |
| F0007 | 200 | 2026-09-26T20:00:56Z | https://huggingface.co/api/models?pipeline_tag=tabular-classification&sort=downloads&limit=40 | HF top40 by downloads: tabular-classification |
| F0008 | 200 | 2026-09-26T20:02:21Z | https://pypi.org/pypi/xgboost/json | pypi json xgboost (xgboost) |
| F0009 | 200 | 2026-09-26T20:02:22Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/scikit-learn | ecosystems pypi downloads scikit-learn (scikit-learn) |
| F0010 | 200 | 2026-09-26T20:02:21Z | https://pypi.org/pypi/scikit-learn/json | pypi json scikit-learn (scikit-learn) [truncated-to-300KB] |
| F0011 | 200 | 2026-09-26T20:02:22Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/dmlc%2Fxgboost | ecosystems repo dmlc/xgboost (xgboost) |
| F0012 | 200 | 2026-09-26T20:02:22Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/scikit-learn%2Fscikit-learn | ecosystems repo scikit-learn/scikit-learn (scikit-learn) |
| F0013 | 200 | 2026-09-26T20:02:22Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/xgboost | ecosystems pypi downloads xgboost (xgboost) |
| F0014 | 404 | 2026-09-26T20:02:22Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/microsoft%2FLightGBM | ecosystems repo microsoft/LightGBM (lightgbm) |
| F0015 | 200 | 2026-09-26T20:02:22Z | https://pypi.org/pypi/lightgbm/json | pypi json lightgbm (lightgbm) |
| F0016 | 200 | 2026-09-26T20:02:22Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/lightgbm | ecosystems pypi downloads lightgbm (lightgbm) |
| F0017 | 200 | 2026-09-26T20:02:23Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/catboost%2Fcatboost | ecosystems repo catboost/catboost (catboost) |
| F0018 | 200 | 2026-09-26T20:02:22Z | https://pypi.org/pypi/catboost/json | pypi json catboost (catboost) [truncated-to-300KB] |
| F0020 | 200 | 2026-09-26T20:02:22Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/statsmodels%2Fstatsmodels | ecosystems repo statsmodels/statsmodels (statsmodels) |
| F0021 | 200 | 2026-09-26T20:02:22Z | https://pypi.org/pypi/statsmodels/json | pypi json statsmodels (statsmodels) |
| F0022 | 200 | 2026-09-26T20:02:23Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/statsmodels | ecosystems pypi downloads statsmodels (statsmodels) |
| F0023 | 200 | 2026-09-26T20:02:23Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/scikit-learn-contrib%2Fimbalanced-learn | ecosystems repo scikit-learn-contrib/imbalanced-learn (imbalanced-learn) |
| F0024 | 200 | 2026-09-26T20:02:22Z | https://pypi.org/pypi/imbalanced-learn/json | pypi json imbalanced-learn (imbalanced-learn) |
| F0025 | 200 | 2026-09-26T20:02:23Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/imbalanced-learn | ecosystems pypi downloads imbalanced-learn (imbalanced-learn) |
| F0026 | 200 | 2026-09-26T20:02:23Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/yzhao062%2Fpyod | ecosystems repo yzhao062/pyod (pyod) |
| F0027 | 200 | 2026-09-26T20:02:23Z | https://pypi.org/pypi/pyod/json | pypi json pyod (pyod) |
| F0028 | 200 | 2026-09-26T20:02:23Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/pyod | ecosystems pypi downloads pyod (pyod) |
| F0029 | 200 | 2026-09-26T20:02:23Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/lmcinnes%2Fumap | ecosystems repo lmcinnes/umap (umap) |
| F0030 | 200 | 2026-09-26T20:02:23Z | https://pypi.org/pypi/umap-learn/json | pypi json umap-learn (umap) |
| F0031 | 200 | 2026-09-26T20:02:23Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/umap-learn | ecosystems pypi downloads umap-learn (umap) |
| F0032 | 200 | 2026-09-26T20:02:23Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/scikit-learn-contrib%2Fhdbscan | ecosystems repo scikit-learn-contrib/hdbscan (hdbscan) |
| F0033 | 200 | 2026-09-26T20:02:23Z | https://pypi.org/pypi/hdbscan/json | pypi json hdbscan (hdbscan) |
| F0034 | 200 | 2026-09-26T20:02:23Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/hdbscan | ecosystems pypi downloads hdbscan (hdbscan) |
| F0035 | 404 | 2026-09-26T20:02:23Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/rapidsai%2Fcuml | ecosystems repo rapidsai/cuml (cuml) |
| F0036 | 200 | 2026-09-26T20:02:23Z | https://pypi.org/pypi/cuml-cu12/json | pypi json cuml-cu12 (cuml) |
| F0037 | 200 | 2026-09-26T20:02:24Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/cuml-cu12 | ecosystems pypi downloads cuml-cu12 (cuml) |
| F0038 | 200 | 2026-09-26T20:02:24Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/online-ml%2Friver | ecosystems repo online-ml/river (river) |
| F0039 | 200 | 2026-09-26T20:02:23Z | https://pypi.org/pypi/river/json | pypi json river (river) |
| F0040 | 200 | 2026-09-26T20:02:24Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/river | ecosystems pypi downloads river (river) |
| F0041 | 200 | 2026-09-26T20:02:24Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/skrub-data%2Fskrub | ecosystems repo skrub-data/skrub (skrub) |
| F0042 | 200 | 2026-09-26T20:02:23Z | https://pypi.org/pypi/skrub/json | pypi json skrub (skrub) |
| F0043 | 200 | 2026-09-26T20:02:24Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/skrub | ecosystems pypi downloads skrub (skrub) |
| F0044 | 200 | 2026-09-26T20:02:24Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/mlpack%2Fmlpack | ecosystems repo mlpack/mlpack (mlpack) |
| F0045 | 200 | 2026-09-26T20:02:24Z | https://pypi.org/pypi/mlpack/json | pypi json mlpack (mlpack) |
| F0046 | 200 | 2026-09-26T20:02:24Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/mlpack | ecosystems pypi downloads mlpack (mlpack) |
| F0047 | 200 | 2026-09-26T20:02:24Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/h2oai%2Fh2o-3 | ecosystems repo h2oai/h2o-3 (h2o-3) |
| F0048 | 200 | 2026-09-26T20:02:24Z | https://pypi.org/pypi/h2o/json | pypi json h2o (h2o-3) |
| F0049 | 200 | 2026-09-26T20:02:24Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/h2o | ecosystems pypi downloads h2o (h2o-3) |
| F0050 | 200 | 2026-09-26T20:02:24Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/explosion%2FspaCy | ecosystems repo explosion/spaCy (spacy) |
| F0051 | 200 | 2026-09-26T20:02:24Z | https://pypi.org/pypi/spacy/json | pypi json spacy (spacy) [truncated-to-300KB] |
| F0053 | 200 | 2026-09-26T20:02:24Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/nltk%2Fnltk | ecosystems repo nltk/nltk (nltk) |
| F0054 | 200 | 2026-09-26T20:02:24Z | https://pypi.org/pypi/nltk/json | pypi json nltk (nltk) |
| F0055 | 200 | 2026-09-26T20:02:24Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/nltk | ecosystems pypi downloads nltk (nltk) |
| F0056 | 200 | 2026-09-26T20:02:25Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/piskvorky%2Fgensim | ecosystems repo piskvorky/gensim (gensim) |
| F0057 | 200 | 2026-09-26T20:02:24Z | https://pypi.org/pypi/gensim/json | pypi json gensim (gensim) |
| F0058 | 200 | 2026-09-26T20:02:25Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/gensim | ecosystems pypi downloads gensim (gensim) |
| F0059 | 200 | 2026-09-26T20:02:24Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/stanfordnlp%2Fstanza | ecosystems repo stanfordnlp/stanza (stanza) |
| F0060 | 200 | 2026-09-26T20:02:24Z | https://pypi.org/pypi/stanza/json | pypi json stanza (stanza) |
| F0061 | 200 | 2026-09-26T20:02:25Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/stanza | ecosystems pypi downloads stanza (stanza) |
| F0062 | 200 | 2026-09-26T20:02:25Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/flairNLP%2Fflair | ecosystems repo flairNLP/flair (flair) |
| F0063 | 200 | 2026-09-26T20:02:24Z | https://pypi.org/pypi/flair/json | pypi json flair (flair) |
| F0064 | 200 | 2026-09-26T20:02:25Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/flair | ecosystems pypi downloads flair (flair) |
| F0065 | 200 | 2026-09-26T20:02:25Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/facebookresearch%2FfastText | ecosystems repo facebookresearch/fastText (fasttext) |
| F0067 | 200 | 2026-09-26T20:02:25Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/fasttext | ecosystems pypi downloads fasttext (fasttext) |
| F0068 | 200 | 2026-09-26T20:02:25Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/stanfordnlp%2FCoreNLP | ecosystems repo stanfordnlp/CoreNLP (corenlp) |
| F0069 | 200 | 2026-09-26T20:02:25Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/sloria%2FTextBlob | ecosystems repo sloria/TextBlob (textblob) |
| F0070 | 200 | 2026-09-26T20:02:25Z | https://pypi.org/pypi/textblob/json | pypi json textblob (textblob) |
| F0071 | 200 | 2026-09-26T20:02:25Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/textblob | ecosystems pypi downloads textblob (textblob) |
| F0072 | 200 | 2026-09-26T20:02:25Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/opencv%2Fopencv | ecosystems repo opencv/opencv (opencv) |
| F0073 | 200 | 2026-09-26T20:02:25Z | https://pypi.org/pypi/opencv-python/json | pypi json opencv-python (opencv) [truncated-to-300KB] |
| F0075 | 200 | 2026-09-26T20:02:25Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/opencv%2Fopencv-python | ecosystems repo opencv/opencv-python (opencv-python) |
| F0076 | 200 | 2026-09-26T20:02:26Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/huggingface%2Fpytorch-image-models | ecosystems repo huggingface/pytorch-image-models (timm) |
| F0077 | 200 | 2026-09-26T20:02:25Z | https://pypi.org/pypi/timm/json | pypi json timm (timm) |
| F0078 | 200 | 2026-09-26T20:02:26Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/timm | ecosystems pypi downloads timm (timm) |
| F0079 | 200 | 2026-09-26T20:02:26Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/pytorch%2Fvision | ecosystems repo pytorch/vision (torchvision) |
| F0080 | 200 | 2026-09-26T20:02:25Z | https://pypi.org/pypi/torchvision/json | pypi json torchvision (torchvision) |
| F0081 | 200 | 2026-09-26T20:02:26Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/torchvision | ecosystems pypi downloads torchvision (torchvision) |
| F0082 | 200 | 2026-09-26T20:02:26Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/ultralytics%2Fultralytics | ecosystems repo ultralytics/ultralytics (ultralytics) |
| F0083 | 200 | 2026-09-26T20:02:26Z | https://pypi.org/pypi/ultralytics/json | pypi json ultralytics (ultralytics) [truncated-to-300KB] |
| F0085 | 200 | 2026-09-26T20:02:26Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/facebookresearch%2Fdetectron2 | ecosystems repo facebookresearch/detectron2 (detectron2) |
| F0086 | 200 | 2026-09-26T20:02:26Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/open-mmlab%2Fmmdetection | ecosystems repo open-mmlab/mmdetection (mmdetection) |
| F0087 | 200 | 2026-09-26T20:02:26Z | https://pypi.org/pypi/mmdet/json | pypi json mmdet (mmdetection) |
| F0088 | 200 | 2026-09-26T20:02:26Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/mmdet | ecosystems pypi downloads mmdet (mmdetection) |
| F0089 | 200 | 2026-09-26T20:02:26Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/open-mmlab%2Fmmsegmentation | ecosystems repo open-mmlab/mmsegmentation (mmsegmentation) |
| F0092 | 200 | 2026-09-26T20:02:26Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/open-mmlab%2Fmmcv | ecosystems repo open-mmlab/mmcv (mmcv) |
| F0095 | 200 | 2026-09-26T20:02:27Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/open-mmlab%2Fmmpretrain | ecosystems repo open-mmlab/mmpretrain (mmpretrain) |
| F0098 | 200 | 2026-09-26T20:02:27Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/open-mmlab%2Fmmpose | ecosystems repo open-mmlab/mmpose (mmpose) |
| F0101 | 200 | 2026-09-26T20:02:27Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/kornia%2Fkornia | ecosystems repo kornia/kornia (kornia) |
| F0102 | 200 | 2026-09-26T20:02:27Z | https://pypi.org/pypi/kornia/json | pypi json kornia (kornia) |
| F0103 | 200 | 2026-09-26T20:02:27Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/kornia | ecosystems pypi downloads kornia (kornia) |
| F0104 | 200 | 2026-09-26T20:02:27Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/albumentations-team%2Falbumentations | ecosystems repo albumentations-team/albumentations (albumentations) |
| F0105 | 200 | 2026-09-26T20:02:27Z | https://pypi.org/pypi/albumentations/json | pypi json albumentations (albumentations) |
| F0106 | 200 | 2026-09-26T20:02:27Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/albumentations | ecosystems pypi downloads albumentations (albumentations) |
| F0107 | 200 | 2026-09-26T20:02:27Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/albumentations-team%2FAlbumentationsX | ecosystems repo albumentations-team/AlbumentationsX (albumentationsx) |
| F0108 | 200 | 2026-09-26T20:02:27Z | https://pypi.org/pypi/albumentationsx/json | pypi json albumentationsx (albumentationsx) |
| F0109 | 200 | 2026-09-26T20:02:27Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/albumentationsx | ecosystems pypi downloads albumentationsx (albumentationsx) |
| F0110 | 200 | 2026-09-26T20:02:27Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/roboflow%2Fsupervision | ecosystems repo roboflow/supervision (supervision) |
| F0111 | 200 | 2026-09-26T20:02:27Z | https://pypi.org/pypi/supervision/json | pypi json supervision (supervision) |
| F0112 | 200 | 2026-09-26T20:02:27Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/supervision | ecosystems pypi downloads supervision (supervision) |
| F0113 | 200 | 2026-09-26T20:02:28Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/scikit-image%2Fscikit-image | ecosystems repo scikit-image/scikit-image (scikit-image) |
| F0114 | 200 | 2026-09-26T20:02:27Z | https://pypi.org/pypi/scikit-image/json | pypi json scikit-image (scikit-image) [truncated-to-300KB] |
| F0116 | 200 | 2026-09-26T20:02:28Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/google-ai-edge%2Fmediapipe | ecosystems repo google-ai-edge/mediapipe (mediapipe) |
| F0117 | 200 | 2026-09-26T20:02:27Z | https://pypi.org/pypi/mediapipe/json | pypi json mediapipe (mediapipe) |
| F0118 | 200 | 2026-09-26T20:02:28Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/mediapipe | ecosystems pypi downloads mediapipe (mediapipe) |
| F0119 | 200 | 2026-09-26T20:02:28Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/PaddlePaddle%2FPaddleDetection | ecosystems repo PaddlePaddle/PaddleDetection (paddledetection) |
| F0120 | 200 | 2026-09-26T20:02:28Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/PaddlePaddle%2FPaddleX | ecosystems repo PaddlePaddle/PaddleX (paddlex) |
| F0123 | 200 | 2026-09-26T20:02:28Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Project-MONAI%2FMONAI | ecosystems repo Project-MONAI/MONAI (monai) |
| F0124 | 200 | 2026-09-26T20:02:28Z | https://pypi.org/pypi/monai/json | pypi json monai (monai) |
| F0125 | 200 | 2026-09-26T20:02:28Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/monai | ecosystems pypi downloads monai (monai) |
| F0126 | 200 | 2026-09-26T20:02:28Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/lightly-ai%2Flightly | ecosystems repo lightly-ai/lightly (lightly) |
| F0127 | 200 | 2026-09-26T20:02:28Z | https://pypi.org/pypi/lightly/json | pypi json lightly (lightly) |
| F0128 | 200 | 2026-09-26T20:02:28Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/lightly | ecosystems pypi downloads lightly (lightly) |
| F0129 | 200 | 2026-09-26T20:02:28Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/lightly-ai%2Flightly-train | ecosystems repo lightly-ai/lightly-train (lightly-train) |
| F0130 | 200 | 2026-09-26T20:02:28Z | https://pypi.org/pypi/lightly-train/json | pypi json lightly-train (lightly-train) |
| F0131 | 200 | 2026-09-26T20:02:28Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/lightly-train | ecosystems pypi downloads lightly-train (lightly-train) |
| F0132 | 200 | 2026-09-26T20:02:29Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/fastai%2Ffastai | ecosystems repo fastai/fastai (fastai) |
| F0133 | 200 | 2026-09-26T20:02:28Z | https://pypi.org/pypi/fastai/json | pypi json fastai (fastai) |
| F0134 | 200 | 2026-09-26T20:02:29Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/fastai | ecosystems pypi downloads fastai (fastai) |
| F0135 | 200 | 2026-09-26T20:02:29Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/davisking%2Fdlib | ecosystems repo davisking/dlib (dlib) |
| F0136 | 200 | 2026-09-26T20:02:28Z | https://pypi.org/pypi/dlib/json | pypi json dlib (dlib) |
| F0137 | 200 | 2026-09-26T20:02:29Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/dlib | ecosystems pypi downloads dlib (dlib) |
| F0138 | 200 | 2026-09-26T20:02:29Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/deepinsight%2Finsightface | ecosystems repo deepinsight/insightface (insightface) |
| F0139 | 200 | 2026-09-26T20:02:28Z | https://pypi.org/pypi/insightface/json | pypi json insightface (insightface) |
| F0140 | 200 | 2026-09-26T20:02:29Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/insightface | ecosystems pypi downloads insightface (insightface) |
| F0141 | 404 | 2026-09-26T20:02:29Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/microsoft%2Ftorchgeo | ecosystems repo microsoft/torchgeo (torchgeo) |
| F0142 | 200 | 2026-09-26T20:02:29Z | https://pypi.org/pypi/torchgeo/json | pypi json torchgeo (torchgeo) |
| F0143 | 200 | 2026-09-26T20:02:29Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/torchgeo | ecosystems pypi downloads torchgeo (torchgeo) |
| F0144 | 200 | 2026-09-26T20:02:29Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/voxel51%2Ffiftyone | ecosystems repo voxel51/fiftyone (fiftyone) |
| F0147 | 200 | 2026-09-26T20:02:29Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/roboflow%2Finference | ecosystems repo roboflow/inference (roboflow-inference) |
| F0150 | 200 | 2026-09-26T20:02:29Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/facebookresearch%2Fdinov2 | ecosystems repo facebookresearch/dinov2 (dinov2) |
| F0151 | 200 | 2026-09-26T20:02:29Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/facebookresearch%2Fdinov3 | ecosystems repo facebookresearch/dinov3 (dinov3) |
| F0152 | 200 | 2026-09-26T20:02:30Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/facebookresearch%2Fsam3 | ecosystems repo facebookresearch/sam3 (sam3) |
| F0153 | 200 | 2026-09-26T20:02:30Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/ByteDance-Seed%2FDepth-Anything-3 | ecosystems repo ByteDance-Seed/Depth-Anything-3 (depth-anything-3) |
| F0154 | 200 | 2026-09-26T20:02:29Z | https://pypi.org/pypi/depth-anything-3/json | pypi json depth-anything-3 (depth-anything-3) |
| F0155 | 200 | 2026-09-26T20:02:30Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/depth-anything-3 | ecosystems pypi downloads depth-anything-3 (depth-anything-3) |
| F0156 | 200 | 2026-09-26T20:02:30Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/DepthAnything%2FDepth-Anything-V2 | ecosystems repo DepthAnything/Depth-Anything-V2 (depth-anything-v2) |
| F0157 | 200 | 2026-09-26T20:02:30Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/lyuwenyu%2FRT-DETR | ecosystems repo lyuwenyu/RT-DETR (rt-detr) |
| F0158 | 200 | 2026-09-26T20:02:30Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/roboflow%2Frf-detr | ecosystems repo roboflow/rf-detr (rf-detr) |
| F0159 | 200 | 2026-09-26T20:02:30Z | https://pypi.org/pypi/rfdetr/json | pypi json rfdetr (rf-detr) |
| F0160 | 200 | 2026-09-26T20:02:30Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/rfdetr | ecosystems pypi downloads rfdetr (rf-detr) |
| F0161 | 200 | 2026-09-26T20:02:30Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Peterande%2FD-FINE | ecosystems repo Peterande/D-FINE (d-fine) |
| F0162 | 200 | 2026-09-26T20:02:30Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Intellindust-AI-Lab%2FDEIM | ecosystems repo Intellindust-AI-Lab/DEIM (deim) |
| F0163 | 200 | 2026-09-26T20:02:30Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/sunsmarterjie%2Fyolov12 | ecosystems repo sunsmarterjie/yolov12 (yolov12) |
| F0165 | 200 | 2026-09-26T20:02:30Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/WongKinYiu%2Fyolov9 | ecosystems repo WongKinYiu/yolov9 (yolov9) |
| F0166 | 200 | 2026-09-26T20:02:30Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/ZhengPeng7%2FBiRefNet | ecosystems repo ZhengPeng7/BiRefNet (birefnet) |
| F0167 | 200 | 2026-09-26T20:02:30Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/NVlabs%2FSegFormer | ecosystems repo NVlabs/SegFormer (segformer) |
| F0168 | 200 | 2026-09-26T20:02:31Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/facebookresearch%2FMask2Former | ecosystems repo facebookresearch/Mask2Former (mask2former) |
| F0169 | 200 | 2026-09-26T20:02:31Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/facebookresearch%2Fsapiens | ecosystems repo facebookresearch/sapiens (sapiens) |
| F0170 | 200 | 2026-09-26T20:02:31Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/tue-mps%2Feomt | ecosystems repo tue-mps/eomt (eomt) |
| F0171 | 200 | 2026-09-26T20:02:31Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/IDEA-Research%2FGroundingDINO | ecosystems repo IDEA-Research/GroundingDINO (grounding-dino) |
| F0172 | 200 | 2026-09-26T20:02:31Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/facebookresearch%2Fco-tracker | ecosystems repo facebookresearch/co-tracker (cotracker) |
| F0173 | 200 | 2026-09-26T20:02:31Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/PriorLabs%2FTabPFN | ecosystems repo PriorLabs/TabPFN (tabpfn) |
| F0174 | 200 | 2026-09-26T20:02:31Z | https://pypi.org/pypi/tabpfn/json | pypi json tabpfn (tabpfn) |
| F0175 | 200 | 2026-09-26T20:02:31Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/tabpfn | ecosystems pypi downloads tabpfn (tabpfn) |
| F0176 | 200 | 2026-09-26T20:02:31Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/soda-inria%2Ftabicl | ecosystems repo soda-inria/tabicl (tabicl) |
| F0177 | 200 | 2026-09-26T20:02:31Z | https://pypi.org/pypi/tabicl/json | pypi json tabicl (tabicl) |
| F0178 | 200 | 2026-09-26T20:02:31Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/tabicl | ecosystems pypi downloads tabicl (tabicl) |
| F0179 | 200 | 2026-09-26T20:02:31Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/SAP-samples%2Fsap-rpt-1-oss | ecosystems repo SAP-samples/sap-rpt-1-oss (sap-rpt-1-oss) |
| F0180 | 404 | 2026-09-26T20:02:31Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/limix-ldm%2FLimiX | ecosystems repo limix-ldm/LimiX (limix) |
| F0181 | 200 | 2026-09-26T20:02:31Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/sktime%2Fsktime | ecosystems repo sktime/sktime (sktime) |
| F0182 | 200 | 2026-09-26T20:02:31Z | https://pypi.org/pypi/sktime/json | pypi json sktime (sktime) |
| F0183 | 200 | 2026-09-26T20:02:31Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/sktime | ecosystems pypi downloads sktime (sktime) |
| F0184 | 200 | 2026-09-26T20:02:31Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/unit8co%2Fdarts | ecosystems repo unit8co/darts (darts) |
| F0185 | 200 | 2026-09-26T20:02:31Z | https://pypi.org/pypi/darts/json | pypi json darts (darts) |
| F0186 | 200 | 2026-09-26T20:02:32Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/darts | ecosystems pypi downloads darts (darts) |
| F0187 | 200 | 2026-09-26T20:02:32Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Nixtla%2Fstatsforecast | ecosystems repo Nixtla/statsforecast (statsforecast) |
| F0188 | 200 | 2026-09-26T20:02:31Z | https://pypi.org/pypi/statsforecast/json | pypi json statsforecast (statsforecast) |
| F0189 | 200 | 2026-09-26T20:02:32Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/statsforecast | ecosystems pypi downloads statsforecast (statsforecast) |
| F0190 | 200 | 2026-09-26T20:02:32Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Nixtla%2Fneuralforecast | ecosystems repo Nixtla/neuralforecast (neuralforecast) |
| F0191 | 200 | 2026-09-26T20:02:31Z | https://pypi.org/pypi/neuralforecast/json | pypi json neuralforecast (neuralforecast) |
| F0192 | 200 | 2026-09-26T20:02:32Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/neuralforecast | ecosystems pypi downloads neuralforecast (neuralforecast) |
| F0193 | 200 | 2026-09-26T20:02:32Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/facebook%2Fprophet | ecosystems repo facebook/prophet (prophet) |
| F0194 | 200 | 2026-09-26T20:02:32Z | https://pypi.org/pypi/prophet/json | pypi json prophet (prophet) |
| F0195 | 200 | 2026-09-26T20:02:32Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/prophet | ecosystems pypi downloads prophet (prophet) |
| F0196 | 200 | 2026-09-26T20:02:32Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/alkaline-ml%2Fpmdarima | ecosystems repo alkaline-ml/pmdarima (pmdarima) |
| F0197 | 200 | 2026-09-26T20:02:32Z | https://pypi.org/pypi/pmdarima/json | pypi json pmdarima (pmdarima) |
| F0198 | 200 | 2026-09-26T20:02:32Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/pmdarima | ecosystems pypi downloads pmdarima (pmdarima) |
| F0199 | 200 | 2026-09-26T20:02:32Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/awslabs%2Fgluonts | ecosystems repo awslabs/gluonts (gluonts) |
| F0200 | 200 | 2026-09-26T20:02:32Z | https://pypi.org/pypi/gluonts/json | pypi json gluonts (gluonts) |
| F0201 | 200 | 2026-09-26T20:02:32Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/gluonts | ecosystems pypi downloads gluonts (gluonts) |
| F0202 | 200 | 2026-09-26T20:02:32Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/autogluon%2Fautogluon | ecosystems repo autogluon/autogluon (autogluon) |
| F0203 | 200 | 2026-09-26T20:02:32Z | https://pypi.org/pypi/autogluon/json | pypi json autogluon (autogluon) [truncated-to-300KB] |
| F0205 | 200 | 2026-09-26T20:02:33Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/microsoft%2FFLAML | ecosystems repo microsoft/FLAML (flaml) |
| F0206 | 200 | 2026-09-26T20:02:32Z | https://pypi.org/pypi/flaml/json | pypi json flaml (flaml) |
| F0207 | 200 | 2026-09-26T20:02:33Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/flaml | ecosystems pypi downloads flaml (flaml) |
| F0208 | 200 | 2026-09-26T20:02:33Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/pycaret%2Fpycaret | ecosystems repo pycaret/pycaret (pycaret) |
| F0209 | 200 | 2026-09-26T20:02:32Z | https://pypi.org/pypi/pycaret/json | pypi json pycaret (pycaret) |
| F0210 | 200 | 2026-09-26T20:02:33Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/pycaret | ecosystems pypi downloads pycaret (pycaret) |
| F0211 | 200 | 2026-09-26T20:02:33Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/EpistasisLab%2Ftpot | ecosystems repo EpistasisLab/tpot (tpot) |
| F0212 | 200 | 2026-09-26T20:02:32Z | https://pypi.org/pypi/tpot/json | pypi json tpot (tpot) |
| F0213 | 200 | 2026-09-26T20:02:33Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/tpot | ecosystems pypi downloads tpot (tpot) |
| F0214 | 200 | 2026-09-26T20:02:33Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/automl%2Fauto-sklearn | ecosystems repo automl/auto-sklearn (auto-sklearn) |
| F0215 | 200 | 2026-09-26T20:02:33Z | https://pypi.org/pypi/auto-sklearn/json | pypi json auto-sklearn (auto-sklearn) |
| F0216 | 200 | 2026-09-26T20:02:33Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/auto-sklearn | ecosystems pypi downloads auto-sklearn (auto-sklearn) |
| F0217 | 200 | 2026-09-26T20:02:33Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/optuna%2Foptuna | ecosystems repo optuna/optuna (optuna) |
| F0219 | 200 | 2026-09-26T20:02:33Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/optuna | ecosystems pypi downloads optuna (optuna) |
| F0220 | 200 | 2026-09-26T20:02:33Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/hyperopt%2Fhyperopt | ecosystems repo hyperopt/hyperopt (hyperopt) |
| F0223 | 200 | 2026-09-26T20:02:33Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/shap%2Fshap | ecosystems repo shap/shap (shap) |
| F0225 | 200 | 2026-09-26T20:02:33Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/shap | ecosystems pypi downloads shap (shap) |
| F0226 | 200 | 2026-09-26T20:02:34Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/marcotcr%2Flime | ecosystems repo marcotcr/lime (lime) |
| F0227 | 200 | 2026-09-26T20:02:33Z | https://pypi.org/pypi/lime/json | pypi json lime (lime) |
| F0232 | 200 | 2026-09-26T20:02:34Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/interpretml%2Finterpret | ecosystems repo interpretml/interpret (interpret) |
| F0235 | 200 | 2026-09-26T20:03:07Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/lightgbm-org%2FLightGBM | ecosystems repo retry lightgbm-org%2FLightGBM |
| F0236 | 200 | 2026-09-26T20:03:07Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/torchgeo%2Ftorchgeo | ecosystems repo retry torchgeo%2Ftorchgeo |
| F0237 | 200 | 2026-09-26T20:03:08Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/meta-pytorch%2Fcaptum | ecosystems repo retry meta-pytorch%2Fcaptum |
| F0244 | 000000 | 2026-09-26T20:03:13Z | https://ungh.cc/repos/microsoft/torchgeo | ungh repo microsoft/torchgeo |
| F0245 | 200 | 2026-09-26T20:03:39Z | https://ungh.cc/repos/rapidsai/cuml | ungh repo retry rapidsai/cuml |
| F0246 | 200 | 2026-09-26T20:03:44Z | https://ungh.cc/repos/THU-MIG/yolov10 | ungh repo retry THU-MIG/yolov10 |
| F0247 | 200 | 2026-09-26T20:03:50Z | https://ungh.cc/repos/limix-ldm/LimiX | ungh repo retry limix-ldm/LimiX |
| F0248 | 200 | 2026-09-26T20:03:56Z | https://ungh.cc/repos/microsoft/torchgeo | ungh repo retry microsoft/torchgeo |
| F0249 | 200 | 2026-09-26T20:04:15Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/NVIDIA%2Fcuml | ecosystems repo retry NVIDIA%2Fcuml |
| F0250 | 200 | 2026-09-26T20:04:16Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/limix-ldm-ai%2FLimiX | ecosystems repo retry limix-ldm-ai%2FLimiX |
| F0253 | 200 | 2026-09-26T20:04:17Z | https://raw.githubusercontent.com/lightgbm-org/LightGBM/HEAD/LICENSE | license text lightgbm-org/LightGBM (LICENSE) |
| F0254 | 200 | 2026-09-26T20:04:17Z | https://raw.githubusercontent.com/dmlc/xgboost/HEAD/LICENSE | license text dmlc/xgboost (LICENSE) |
| F0255 | 200 | 2026-09-26T20:04:16Z | https://raw.githubusercontent.com/catboost/catboost/HEAD/LICENSE | license text catboost/catboost (LICENSE) |
| F0257 | 200 | 2026-09-26T20:04:17Z | https://raw.githubusercontent.com/scikit-learn-contrib/imbalanced-learn/HEAD/LICENSE | license text scikit-learn-contrib/imbalanced-learn (LICENSE) |
| F0259 | 200 | 2026-09-26T20:04:17Z | https://raw.githubusercontent.com/yzhao062/pyod/HEAD/LICENSE | license text yzhao062/pyod (LICENSE) |
| F0262 | 200 | 2026-09-26T20:04:17Z | https://raw.githubusercontent.com/scikit-learn-contrib/hdbscan/HEAD/LICENSE | license text scikit-learn-contrib/hdbscan (LICENSE) |
| F0263 | 200 | 2026-09-26T20:04:17Z | https://raw.githubusercontent.com/NVIDIA/cuml/HEAD/LICENSE | license text NVIDIA/cuml (LICENSE) |
| F0264 | 200 | 2026-09-26T20:04:17Z | https://raw.githubusercontent.com/online-ml/river/HEAD/LICENSE | license text online-ml/river (LICENSE) |
| F0265 | 200 | 2026-09-26T20:04:17Z | https://raw.githubusercontent.com/statsmodels/statsmodels/HEAD/LICENSE.txt | license text statsmodels/statsmodels (LICENSE.txt) |
| F0270 | 200 | 2026-09-26T20:04:17Z | https://raw.githubusercontent.com/h2oai/h2o-3/HEAD/LICENSE | license text h2oai/h2o-3 (LICENSE) |
| F0271 | 200 | 2026-09-26T20:04:17Z | https://raw.githubusercontent.com/lmcinnes/umap/HEAD/LICENSE.txt | license text lmcinnes/umap (LICENSE.txt) |
| F0272 | 200 | 2026-09-26T20:04:17Z | https://raw.githubusercontent.com/explosion/spaCy/HEAD/LICENSE | license text explosion/spaCy (LICENSE) |
| F0276 | 200 | 2026-09-26T20:04:18Z | https://raw.githubusercontent.com/scikit-learn/scikit-learn/HEAD/COPYING | license text scikit-learn/scikit-learn (COPYING) |
| F0278 | 200 | 2026-09-26T20:04:18Z | https://raw.githubusercontent.com/skrub-data/skrub/HEAD/LICENSE.txt | license text skrub-data/skrub (LICENSE.txt) |
| F0279 | 200 | 2026-09-26T20:04:18Z | https://raw.githubusercontent.com/mlpack/mlpack/HEAD/LICENSE.txt | license text mlpack/mlpack (LICENSE.txt) |
| F0280 | 200 | 2026-09-26T20:04:18Z | https://raw.githubusercontent.com/stanfordnlp/stanza/HEAD/LICENSE | license text stanfordnlp/stanza (LICENSE) |
| F0283 | 200 | 2026-09-26T20:04:18Z | https://raw.githubusercontent.com/flairNLP/flair/HEAD/LICENSE | license text flairNLP/flair (LICENSE) |
| F0286 | 200 | 2026-09-26T20:04:18Z | https://raw.githubusercontent.com/sloria/TextBlob/HEAD/LICENSE | license text sloria/TextBlob (LICENSE) |
| F0288 | 200 | 2026-09-26T20:04:18Z | https://raw.githubusercontent.com/nltk/nltk/HEAD/LICENSE.txt | license text nltk/nltk (LICENSE.txt) |
| F0290 | 200 | 2026-09-26T20:04:18Z | https://raw.githubusercontent.com/opencv/opencv/HEAD/LICENSE | license text opencv/opencv (LICENSE) |
| F0292 | 200 | 2026-09-26T20:04:18Z | https://raw.githubusercontent.com/piskvorky/gensim/HEAD/COPYING | license text piskvorky/gensim (COPYING) |
| F0293 | 200 | 2026-09-26T20:04:18Z | https://raw.githubusercontent.com/huggingface/pytorch-image-models/HEAD/LICENSE | license text huggingface/pytorch-image-models (LICENSE) |
| F0294 | 200 | 2026-09-26T20:04:18Z | https://raw.githubusercontent.com/pytorch/vision/HEAD/LICENSE | license text pytorch/vision (LICENSE) |
| F0295 | 200 | 2026-09-26T20:04:18Z | https://raw.githubusercontent.com/stanfordnlp/CoreNLP/HEAD/LICENSE.txt | license text stanfordnlp/CoreNLP (LICENSE.txt) |
| F0296 | 200 | 2026-09-26T20:04:18Z | https://raw.githubusercontent.com/ultralytics/ultralytics/HEAD/LICENSE | license text ultralytics/ultralytics (LICENSE) |
| F0298 | 200 | 2026-09-26T20:04:19Z | https://raw.githubusercontent.com/facebookresearch/detectron2/HEAD/LICENSE | license text facebookresearch/detectron2 (LICENSE) |
| F0299 | 200 | 2026-09-26T20:04:19Z | https://raw.githubusercontent.com/open-mmlab/mmdetection/HEAD/LICENSE | license text open-mmlab/mmdetection (LICENSE) |
| F0303 | 200 | 2026-09-26T20:04:19Z | https://raw.githubusercontent.com/opencv/opencv-python/HEAD/LICENSE.txt | license text opencv/opencv-python (LICENSE.txt) |
| F0305 | 200 | 2026-09-26T20:04:19Z | https://raw.githubusercontent.com/kornia/kornia/HEAD/LICENSE | license text kornia/kornia (LICENSE) |
| F0306 | 200 | 2026-09-26T20:04:19Z | https://raw.githubusercontent.com/albumentations-team/albumentations/HEAD/LICENSE | license text albumentations-team/albumentations (LICENSE) |
| F0307 | 200 | 2026-09-26T20:04:19Z | https://raw.githubusercontent.com/albumentations-team/AlbumentationsX/HEAD/LICENSE | license text albumentations-team/AlbumentationsX (LICENSE) |
| F0310 | 200 | 2026-09-26T20:04:19Z | https://raw.githubusercontent.com/google-ai-edge/mediapipe/HEAD/LICENSE | license text google-ai-edge/mediapipe (LICENSE) |
| F0311 | 200 | 2026-09-26T20:04:19Z | https://raw.githubusercontent.com/PaddlePaddle/PaddleDetection/HEAD/LICENSE | license text PaddlePaddle/PaddleDetection (LICENSE) |
| F0313 | 200 | 2026-09-26T20:04:19Z | https://raw.githubusercontent.com/roboflow/supervision/HEAD/LICENSE.md | license text roboflow/supervision (LICENSE.md) |
| F0314 | 200 | 2026-09-26T20:04:19Z | https://raw.githubusercontent.com/Project-MONAI/MONAI/HEAD/LICENSE | license text Project-MONAI/MONAI (LICENSE) |
| F0317 | 200 | 2026-09-26T20:04:19Z | https://raw.githubusercontent.com/lightly-ai/lightly-train/HEAD/LICENSE | license text lightly-ai/lightly-train (LICENSE) |
| F0318 | 200 | 2026-09-26T20:04:19Z | https://raw.githubusercontent.com/fastai/fastai/HEAD/LICENSE | license text fastai/fastai (LICENSE) |
| F0320 | 200 | 2026-09-26T20:04:19Z | https://raw.githubusercontent.com/scikit-image/scikit-image/HEAD/LICENSE.txt | license text scikit-image/scikit-image (LICENSE.txt) |
| F0323 | 200 | 2026-09-26T20:04:20Z | https://raw.githubusercontent.com/torchgeo/torchgeo/HEAD/LICENSE | license text torchgeo/torchgeo (LICENSE) |
| F0326 | 200 | 2026-09-26T20:04:20Z | https://raw.githubusercontent.com/roboflow/inference/HEAD/LICENSE | license text roboflow/inference (LICENSE) |
| F0328 | 200 | 2026-09-26T20:04:20Z | https://raw.githubusercontent.com/lightly-ai/lightly/HEAD/LICENSE.txt | license text lightly-ai/lightly (LICENSE.txt) |
| F0329 | 200 | 2026-09-26T20:04:20Z | https://raw.githubusercontent.com/davisking/dlib/HEAD/LICENSE.txt | license text davisking/dlib (LICENSE.txt) |
| F0330 | 200 | 2026-09-26T20:04:20Z | https://raw.githubusercontent.com/facebookresearch/dinov2/HEAD/LICENSE | license text facebookresearch/dinov2 (LICENSE) |
| F0333 | 200 | 2026-09-26T20:04:20Z | https://raw.githubusercontent.com/facebookresearch/sam3/HEAD/LICENSE | license text facebookresearch/sam3 (LICENSE) |
| F0334 | 200 | 2026-09-26T20:04:20Z | https://raw.githubusercontent.com/ByteDance-Seed/Depth-Anything-3/HEAD/LICENSE | license text ByteDance-Seed/Depth-Anything-3 (LICENSE) |
| F0335 | 200 | 2026-09-26T20:04:20Z | https://raw.githubusercontent.com/DepthAnything/Depth-Anything-V2/HEAD/LICENSE | license text DepthAnything/Depth-Anything-V2 (LICENSE) |
| F0336 | 200 | 2026-09-26T20:04:20Z | https://raw.githubusercontent.com/lyuwenyu/RT-DETR/HEAD/LICENSE | license text lyuwenyu/RT-DETR (LICENSE) |
| F0338 | 200 | 2026-09-26T20:04:20Z | https://raw.githubusercontent.com/roboflow/rf-detr/HEAD/LICENSE | license text roboflow/rf-detr (LICENSE) |
| F0339 | 200 | 2026-09-26T20:04:20Z | https://raw.githubusercontent.com/facebookresearch/dinov3/HEAD/LICENSE.md | license text facebookresearch/dinov3 (LICENSE.md) |
| F0340 | 200 | 2026-09-26T20:04:20Z | https://raw.githubusercontent.com/Peterande/D-FINE/HEAD/LICENSE | license text Peterande/D-FINE (LICENSE) |
| F0341 | 200 | 2026-09-26T20:04:20Z | https://raw.githubusercontent.com/Intellindust-AI-Lab/DEIM/HEAD/LICENSE | license text Intellindust-AI-Lab/DEIM (LICENSE) |
| F0343 | 200 | 2026-09-26T20:04:20Z | https://raw.githubusercontent.com/sunsmarterjie/yolov12/HEAD/LICENSE | license text sunsmarterjie/yolov12 (LICENSE) |
| F0344 | 200 | 2026-09-26T20:04:21Z | https://raw.githubusercontent.com/THU-MIG/yolov10/HEAD/LICENSE | license text THU-MIG/yolov10 (LICENSE) |
| F0346 | 200 | 2026-09-26T20:04:21Z | https://raw.githubusercontent.com/ZhengPeng7/BiRefNet/HEAD/LICENSE | license text ZhengPeng7/BiRefNet (LICENSE) |
| F0347 | 200 | 2026-09-26T20:04:21Z | https://raw.githubusercontent.com/NVlabs/SegFormer/HEAD/LICENSE | license text NVlabs/SegFormer (LICENSE) |
| F0350 | 200 | 2026-09-26T20:04:21Z | https://raw.githubusercontent.com/facebookresearch/sapiens/HEAD/LICENSE | license text facebookresearch/sapiens (LICENSE) |
| F0351 | 200 | 2026-09-26T20:04:21Z | https://raw.githubusercontent.com/WongKinYiu/yolov9/HEAD/LICENSE.md | license text WongKinYiu/yolov9 (LICENSE.md) |
| F0352 | 200 | 2026-09-26T20:04:21Z | https://raw.githubusercontent.com/tue-mps/eomt/HEAD/LICENSE | license text tue-mps/eomt (LICENSE) |
| F0355 | 200 | 2026-09-26T20:04:21Z | https://raw.githubusercontent.com/PriorLabs/TabPFN/HEAD/LICENSE | license text PriorLabs/TabPFN (LICENSE) |
| F0356 | 200 | 2026-09-26T20:04:21Z | https://raw.githubusercontent.com/soda-inria/tabicl/HEAD/LICENSE | license text soda-inria/tabicl (LICENSE) |
| F0357 | 200 | 2026-09-26T20:04:21Z | https://raw.githubusercontent.com/SAP-samples/sap-rpt-1-oss/HEAD/LICENSE | license text SAP-samples/sap-rpt-1-oss (LICENSE) |
| F0359 | 200 | 2026-09-26T20:04:21Z | https://raw.githubusercontent.com/sktime/sktime/HEAD/LICENSE | license text sktime/sktime (LICENSE) |
| F0360 | 200 | 2026-09-26T20:04:21Z | https://raw.githubusercontent.com/facebookresearch/co-tracker/HEAD/LICENSE.md | license text facebookresearch/co-tracker (LICENSE.md) |
| F0361 | 200 | 2026-09-26T20:04:21Z | https://raw.githubusercontent.com/unit8co/darts/HEAD/LICENSE | license text unit8co/darts (LICENSE) |
| F0362 | 200 | 2026-09-26T20:04:21Z | https://raw.githubusercontent.com/Nixtla/statsforecast/HEAD/LICENSE | license text Nixtla/statsforecast (LICENSE) |
| F0364 | 200 | 2026-09-26T20:04:21Z | https://raw.githubusercontent.com/Nixtla/neuralforecast/HEAD/LICENSE | license text Nixtla/neuralforecast (LICENSE) |
| F0365 | 200 | 2026-09-26T20:04:21Z | https://raw.githubusercontent.com/facebook/prophet/HEAD/LICENSE | license text facebook/prophet (LICENSE) |
| F0366 | 200 | 2026-09-26T20:04:21Z | https://raw.githubusercontent.com/alkaline-ml/pmdarima/HEAD/LICENSE | license text alkaline-ml/pmdarima (LICENSE) |
| F0367 | 200 | 2026-09-26T20:04:22Z | https://raw.githubusercontent.com/awslabs/gluonts/HEAD/LICENSE | license text awslabs/gluonts (LICENSE) |
| F0368 | 200 | 2026-09-26T20:04:22Z | https://raw.githubusercontent.com/autogluon/autogluon/HEAD/LICENSE | license text autogluon/autogluon (LICENSE) |
| F0369 | 200 | 2026-09-26T20:04:22Z | https://raw.githubusercontent.com/limix-ldm-ai/LimiX/HEAD/LICENSE.txt | license text limix-ldm-ai/LimiX (LICENSE.txt) |
| F0370 | 200 | 2026-09-26T20:04:22Z | https://raw.githubusercontent.com/microsoft/FLAML/HEAD/LICENSE | license text microsoft/FLAML (LICENSE) |
| F0371 | 200 | 2026-09-26T20:04:22Z | https://raw.githubusercontent.com/pycaret/pycaret/HEAD/LICENSE | license text pycaret/pycaret (LICENSE) |
| F0372 | 200 | 2026-09-26T20:04:22Z | https://raw.githubusercontent.com/EpistasisLab/tpot/HEAD/LICENSE | license text EpistasisLab/tpot (LICENSE) |
| F0383 | 200 | 2026-09-26T20:04:22Z | https://raw.githubusercontent.com/automl/auto-sklearn/HEAD/LICENSE.txt | license text automl/auto-sklearn (LICENSE.txt) |
| F0384 | 200 | 2026-09-26T20:04:55Z | https://huggingface.co/api/models/facebook/dinov3-vitl16-pretrain-lvd1689m?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model facebook/dinov3-vitl16-pretrain-lvd1689m |
| F0385 | 200 | 2026-09-26T20:04:56Z | https://huggingface.co/api/models/facebook/dinov2-base?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model facebook/dinov2-base |
| F0386 | 200 | 2026-09-26T20:04:56Z | https://huggingface.co/api/models/facebook/sam3?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model facebook/sam3 |
| F0389 | 200 | 2026-09-26T20:04:57Z | https://huggingface.co/api/models/depth-anything/DA3-LARGE?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model depth-anything/DA3-LARGE |
| F0390 | 200 | 2026-09-26T20:04:57Z | https://huggingface.co/api/models/depth-anything/Depth-Anything-V2-Small-hf?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model depth-anything/Depth-Anything-V2-Small-hf |
| F0391 | 200 | 2026-09-26T20:04:57Z | https://huggingface.co/api/models/depth-anything/Depth-Anything-V2-Large?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model depth-anything/Depth-Anything-V2-Large |
| F0392 | 200 | 2026-09-26T20:04:57Z | https://huggingface.co/api/models/PekingU/rtdetr_v2_r18vd?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model PekingU/rtdetr_v2_r18vd |
| F0393 | 200 | 2026-09-26T20:04:57Z | https://huggingface.co/api/models/Roboflow/rf-detr-base?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model Roboflow/rf-detr-base |
| F0394 | 200 | 2026-09-26T20:04:57Z | https://huggingface.co/api/models/ustc-community/dfine-xlarge-coco?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model ustc-community/dfine-xlarge-coco |
| F0395 | 200 | 2026-09-26T20:04:58Z | https://huggingface.co/api/models/ZhengPeng7/BiRefNet?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model ZhengPeng7/BiRefNet |
| F0396 | 200 | 2026-09-26T20:04:58Z | https://huggingface.co/api/models/briaai/RMBG-2.0?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model briaai/RMBG-2.0 |
| F0397 | 200 | 2026-09-26T20:04:58Z | https://huggingface.co/api/models/nvidia/segformer-b0-finetuned-ade-512-512?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model nvidia/segformer-b0-finetuned-ade-512-512 |
| F0398 | 200 | 2026-09-26T20:04:58Z | https://huggingface.co/api/models/facebook/sapiens2-seg-0.4b?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model facebook/sapiens2-seg-0.4b |
| F0399 | 200 | 2026-09-26T20:04:58Z | https://huggingface.co/api/models/Prior-Labs/tabpfn_3?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model Prior-Labs/tabpfn_3 |
| F0400 | 200 | 2026-09-26T20:04:59Z | https://huggingface.co/api/models/Prior-Labs/TabPFN-v2-clf?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model Prior-Labs/TabPFN-v2-clf |
| F0401 | 200 | 2026-09-26T20:04:59Z | https://huggingface.co/api/models/Prior-Labs/tabpfn_2_5?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model Prior-Labs/tabpfn_2_5 |
| F0402 | 200 | 2026-09-26T20:04:59Z | https://huggingface.co/api/models/autogluon/mitra-classifier?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model autogluon/mitra-classifier |
| F0403 | 200 | 2026-09-26T20:04:59Z | https://huggingface.co/api/models/SAP/sap-rpt-1-oss?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model SAP/sap-rpt-1-oss |
| F0404 | 200 | 2026-09-26T20:04:59Z | https://huggingface.co/api/models/stable-ai/LimiX-2?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model stable-ai/LimiX-2 |
| F0405 | 200 | 2026-09-26T20:05:00Z | https://huggingface.co/api/models/google/tabfm-1.0.0-pytorch?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model google/tabfm-1.0.0-pytorch |
| F0406 | 200 | 2026-09-26T20:05:00Z | https://huggingface.co/api/models/tiiuae/Falcon-Perception?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model tiiuae/Falcon-Perception |
| F0407 | 200 | 2026-09-26T20:05:00Z | https://huggingface.co/api/models/Ultralytics/YOLO26?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model Ultralytics/YOLO26 |
| F0408 | 200 | 2026-09-26T20:05:00Z | https://huggingface.co/api/models/Ultralytics/YOLO11?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model Ultralytics/YOLO11 |
| F0409 | 200 | 2026-09-26T20:05:00Z | https://huggingface.co/api/models/timm/mobilenetv3_small_100.lamb_in1k?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model timm/mobilenetv3_small_100.lamb_in1k |
| F0410 | 200 | 2026-09-26T20:05:01Z | https://huggingface.co/api/models/google/vit-base-patch16-224?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model google/vit-base-patch16-224 |
| F0411 | 200 | 2026-09-26T20:05:01Z | https://huggingface.co/api/models/tue-mps/coco_panoptic_eomt_large_640?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model tue-mps/coco_panoptic_eomt_large_640 |
| F0412 | 200 | 2026-09-26T20:05:01Z | https://huggingface.co/api/models/IDEA-Research/grounding-dino-base?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model IDEA-Research/grounding-dino-base |
| F0413 | 200 | 2026-09-26T20:05:01Z | https://huggingface.co/api/models/facebook/cotracker3?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model facebook/cotracker3 |
| F0414 | 200 | 2026-09-26T20:05:01Z | https://huggingface.co/api/models/Synthefy/Nori?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model Synthefy/Nori |
| F0415 | 200 | 2026-09-26T20:05:02Z | https://huggingface.co/api/models/alana89/TabSTAR?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model alana89/TabSTAR |
| F0416 | 200 | 2026-09-26T20:05:02Z | https://huggingface.co/api/models/LG-AI-Research/EXAONE-Tabular?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model LG-AI-Research/EXAONE-Tabular |
| F0417 | 200 | 2026-09-26T20:05:02Z | https://huggingface.co/api/models/mudler/locate-anything.cpp-gguf?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model mudler/locate-anything.cpp-gguf |
| F0418 | 200 | 2026-09-26T20:05:02Z | https://huggingface.co/api/models/apple/DepthPro-hf?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model apple/DepthPro-hf |
| F0419 | 200 | 2026-09-26T20:05:15Z | https://huggingface.co/Prior-Labs/tabpfn_3/raw/main/LICENSE | hf license file Prior-Labs/tabpfn_3 |
| F0420 | 200 | 2026-09-26T20:05:15Z | https://huggingface.co/google/tabfm-1.0.0-pytorch/raw/main/LICENSE | hf license file google/tabfm |
| F0421 | 200 | 2026-09-26T20:05:15Z | https://huggingface.co/stable-ai/LimiX-2/raw/main/LICENSE | hf license file stable-ai/LimiX-2 |
| F0422 | 200 | 2026-09-26T20:05:15Z | https://huggingface.co/api/models?author=facebook&search=dinov&sort=downloads&limit=1000 | hf family sum author=facebook&search=dinov |
| F0424 | 200 | 2026-09-26T20:05:16Z | https://huggingface.co/api/models?author=depth-anything&sort=downloads&limit=1000 | hf family sum author=depth-anything |
| F0425 | 200 | 2026-09-26T20:05:16Z | https://huggingface.co/api/models?author=PekingU&sort=downloads&limit=1000 | hf family sum author=PekingU |
| F0426 | 200 | 2026-09-26T20:05:16Z | https://huggingface.co/api/models?author=Roboflow&sort=downloads&limit=1000 | hf family sum author=Roboflow |
| F0427 | 200 | 2026-09-26T20:05:17Z | https://huggingface.co/api/models?author=timm&sort=downloads&limit=1000 | hf family sum author=timm |
| F0428 | 200 | 2026-09-26T20:05:17Z | https://huggingface.co/api/models?author=Prior-Labs&sort=downloads&limit=1000 | hf family sum author=Prior-Labs |
| F0429 | 200 | 2026-09-26T20:05:17Z | https://huggingface.co/api/models?author=autogluon&sort=downloads&limit=1000 | hf family sum author=autogluon |
| F0430 | 200 | 2026-09-26T20:05:17Z | https://huggingface.co/api/models?author=ustc-community&sort=downloads&limit=1000 | hf family sum author=ustc-community |
| F0431 | 200 | 2026-09-26T20:05:17Z | https://huggingface.co/api/models?author=ZhengPeng7&sort=downloads&limit=1000 | hf family sum author=ZhengPeng7 |
| F0434 | 200 | 2026-09-26T20:05:18Z | https://huggingface.co/api/models?author=tue-mps&sort=downloads&limit=1000 | hf family sum author=tue-mps |
| F0435 | 200 | 2026-09-26T20:05:18Z | https://huggingface.co/api/models?author=Synthefy&sort=downloads&limit=1000 | hf family sum author=Synthefy |
| F0436 | 200 | 2026-09-26T20:05:18Z | https://huggingface.co/api/models?author=google&search=tabfm&sort=downloads&limit=1000 | hf family sum author=google&search=tabfm |
| F0437 | 200 | 2026-09-26T20:05:47Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/google-research%2Ftabfm | ecosystems repo google-research%2Ftabfm |
| F0438 | 200 | 2026-09-26T20:05:48Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/NVlabs%2FRADIO | ecosystems repo NVlabs%2FRADIO |
| F0439 | 200 | 2026-09-26T20:05:49Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/perpetual-ml%2Fperpetual | ecosystems repo perpetual-ml%2Fperpetual |
| F0440 | 200 | 2026-09-26T20:05:50Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/stanfordmlgroup%2Fngboost | ecosystems repo stanfordmlgroup%2Fngboost |
| F0441 | 200 | 2026-09-26T20:05:50Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/facebookresearch%2Fperception_models | ecosystems repo facebookresearch%2Fperception_models |
| F0442 | 200 | 2026-09-26T20:05:50Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/tiiuae%2FFalcon-Perception | ecosystems repo tiiuae%2FFalcon-Perception |
| F0443 | 200 | 2026-09-26T20:05:51Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/facebookresearch%2Fsam2 | ecosystems repo facebookresearch%2Fsam2 |
| F0444 | 200 | 2026-09-26T20:05:51Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/facebookresearch%2Fsegment-anything | ecosystems repo facebookresearch%2Fsegment-anything |
| F0445 | 200 | 2026-09-26T20:05:51Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/perpetual | ecosystems pypi perpetual (meta2) |
| F0446 | 200 | 2026-09-26T20:05:52Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/ngboost | ecosystems pypi ngboost (meta2) |
| F0447 | 200 | 2026-09-26T20:05:52Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/ultralytics | ecosystems pypi ultralytics (meta2) |
| F0448 | 200 | 2026-09-26T20:05:53Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/scikit-image | ecosystems pypi scikit-image (meta2) |
| F0449 | 200 | 2026-09-26T20:05:53Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/spacy | ecosystems pypi spacy (meta2) |
| F0450 | 200 | 2026-09-26T20:05:53Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/catboost | ecosystems pypi catboost (meta2) |
| F0451 | 200 | 2026-09-26T20:05:53Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/autogluon | ecosystems pypi autogluon (meta2) |
| F0452 | 200 | 2026-09-26T20:05:54Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/opencv-python | ecosystems pypi opencv-python (meta2) |
| F0453 | 200 | 2026-09-26T20:05:54Z | https://huggingface.co/api/models/nvidia/C-RADIOv3-H?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model nvidia/C-RADIOv3-H |
| F0454 | 200 | 2026-09-26T20:05:54Z | https://huggingface.co/api/models?author=nvidia&search=RADIO&sort=downloads&limit=100 | hf family sum author=nvidia&search=RADIO |
| F0455 | 200 | 2026-09-26T20:05:54Z | https://raw.githubusercontent.com/deepinsight/insightface/HEAD/README.md | readme deepinsight/insightface |
| F0456 | 200 | 2026-09-26T20:06:19Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/facebookresearch%2Fdetectron2/releases?per_page=1 | releases facebookresearch/detectron2 |
| F0457 | 200 | 2026-09-26T20:06:19Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/facebookresearch%2Fdinov2/releases?per_page=1 | releases facebookresearch/dinov2 |
| F0458 | 200 | 2026-09-26T20:06:20Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/facebookresearch%2Fdinov3/releases?per_page=1 | releases facebookresearch/dinov3 |
| F0462 | 200 | 2026-09-26T20:06:22Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/lyuwenyu%2FRT-DETR/releases?per_page=1 | releases lyuwenyu/RT-DETR |
| F0463 | 200 | 2026-09-26T20:06:23Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Peterande%2FD-FINE/releases?per_page=1 | releases Peterande/D-FINE |
| F0464 | 200 | 2026-09-26T20:06:23Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/ZhengPeng7%2FBiRefNet/releases?per_page=1 | releases ZhengPeng7/BiRefNet |
| F0468 | 200 | 2026-09-26T20:06:25Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/facebookresearch%2Fco-tracker/releases?per_page=1 | releases facebookresearch/co-tracker |
| F0469 | 200 | 2026-09-26T20:06:25Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/stanfordnlp%2FCoreNLP/releases?per_page=1 | releases stanfordnlp/CoreNLP |
| F0470 | 200 | 2026-09-26T20:06:26Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/tue-mps%2Feomt/releases?per_page=1 | releases tue-mps/eomt |
| F0471 | 200 | 2026-09-26T20:06:26Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/NVlabs%2FRADIO/releases?per_page=1 | releases NVlabs/RADIO |
| F0472 | 200 | 2026-09-26T20:06:27Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/google-research%2Ftabfm/releases?per_page=1 | releases google-research/tabfm |
| F0473 | 200 | 2026-09-26T20:06:27Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/Intellindust-AI-Lab%2FDEIM/releases?per_page=1 | releases Intellindust-AI-Lab/DEIM |
| F0476 | 200 | 2026-09-26T20:06:29Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/NVlabs%2FSegFormer/releases?per_page=1 | releases NVlabs/SegFormer |
| F0477 | 200 | 2026-09-26T20:06:29Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/facebookresearch%2Fsapiens/releases?per_page=1 | releases facebookresearch/sapiens |
| F0479 | 200 | 2026-09-26T20:06:30Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/PaddlePaddle%2FPaddleDetection/releases?per_page=1 | releases PaddlePaddle/PaddleDetection |
| F0480 | 200 | 2026-09-26T20:06:30Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/SAP-samples%2Fsap-rpt-1-oss/releases?per_page=1 | releases SAP-samples/sap-rpt-1-oss |
| F0481 | 200 | 2026-09-26T20:06:31Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/limix-ldm-ai%2FLimiX/releases?per_page=1 | releases limix-ldm-ai/LimiX |
| F0484 | 200 | 2026-09-26T20:06:33Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/opencv%2Fopencv/releases?per_page=1 | releases opencv/opencv |
| F0485 | 200 | 2026-09-26T20:06:34Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/roboflow%2Frf-detr/releases?per_page=1 | releases roboflow/rf-detr |
| F0486 | 200 | 2026-09-26T20:06:36Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/ultralytics%2Fultralytics/releases?per_page=1 | releases ultralytics/ultralytics |
| F0487 | 200 | 2026-09-26T20:06:37Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/PriorLabs%2FTabPFN/releases?per_page=1 | releases PriorLabs/TabPFN |
| F0488 | 200 | 2026-09-26T20:08:15Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/facebookresearch%2Fsapiens2 | ecosystems repo facebookresearch%2Fsapiens2 |
| F0489 | 404 | 2026-09-26T20:08:16Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/apple%2Fml-depth-pro | ecosystems repo apple%2Fml-depth-pro |
| F0490 | 200 | 2026-09-26T20:08:16Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/dotnet%2Fmachinelearning | ecosystems repo dotnet%2Fmachinelearning |
| F0491 | 200 | 2026-09-26T20:08:17Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/dask%2Fdask-ml | ecosystems repo dask%2Fdask-ml |
| F0492 | 200 | 2026-09-26T20:08:17Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/amazon-science%2Fchronos-forecasting | ecosystems repo amazon-science%2Fchronos-forecasting |
| F0494 | 200 | 2026-09-26T20:08:18Z | https://raw.githubusercontent.com/facebookresearch/sapiens2/HEAD/LICENSE.md | license text facebookresearch/sapiens2 (LICENSE.md) |
| F0495 | 200 | 2026-09-26T20:08:18Z | https://raw.githubusercontent.com/apple/ml-depth-pro/HEAD/LICENSE | license text apple/ml-depth-pro (LICENSE) |
| F0496 | 200 | 2026-09-26T20:08:18Z | https://raw.githubusercontent.com/NVlabs/RADIO/HEAD/LICENSE | license text NVlabs/RADIO (LICENSE) |
| F0497 | 200 | 2026-09-26T20:08:19Z | https://raw.githubusercontent.com/dotnet/machinelearning/HEAD/LICENSE | license text dotnet/machinelearning (LICENSE) |
| F0500 | 200 | 2026-09-26T20:08:19Z | https://raw.githubusercontent.com/dask/dask-ml/HEAD/LICENSE.txt | license text dask/dask-ml (LICENSE.txt) |
| F0502 | 200 | 2026-09-26T20:08:20Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/dask-ml | ecosystems pypi dask-ml |
| F0504 | 200 | 2026-09-26T20:08:20Z | https://huggingface.co/api/models/jingang/TabICL?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model jingang/TabICL |
| F0505 | 200 | 2026-09-26T20:08:20Z | https://huggingface.co/api/models/apple/DepthPro?expand[]=downloads&expand[]=likes&expand[]=cardData&expand[]=lastModified&expand[]=gated | hf model apple/DepthPro |
| F0507 | 200 | 2026-09-26T20:08:21Z | https://huggingface.co/Synthefy/Nori/raw/main/README.md | hf readme Synthefy/Nori |
| F0509 | 200 | 2026-09-26T20:08:21Z | https://huggingface.co/alana89/TabSTAR/raw/main/README.md | hf readme alana89/TabSTAR |
| F0510 | 200 | 2026-09-26T20:08:45Z | https://azuresearch-usnc.nuget.org/query?q=packageid:Microsoft.ML&prerelease=false | nuget search Microsoft.ML downloads |
| F0511 | 200 | 2026-09-26T20:08:46Z | https://aws.amazon.com/rekognition/ | homepage Amazon Rekognition |
| F0512 | 200 | 2026-09-26T20:08:46Z | https://cloud.google.com/vision | homepage Google Cloud Vision [truncated-to-300KB] |
| F0513 | 200 | 2026-09-26T20:08:48Z | https://www.datarobot.com/platform/ | homepage DataRobot platform |
| F0514 | 200 | 2026-09-26T20:08:48Z | https://pypi.org/pypi/synthefy-nori/json | pypi json synthefy-nori |
| F0515 | 200 | 2026-09-26T20:08:48Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/tabstar | ecosystems pypi tabstar |
| F0517 | 200 | 2026-09-26T20:09:57Z | https://huggingface.co/LG-AI-Research/EXAONE-Tabular/raw/main/LICENSE | hf license file LG-AI-Research/EXAONE-Tabular |
| F0518 | 200 | 2026-09-26T20:09:57Z | https://ungh.cc/repos/LGAI-Research/EXAONE-Tabular | ungh repo LGAI-Research/EXAONE-Tabular |
| F0519 | 401 | 2026-09-26T20:09:57Z | https://huggingface.co/briaai/RMBG-2.0/raw/main/README.md | hf readme briaai/RMBG-2.0 |
| F0520 | 200 | 2026-09-26T20:09:58Z | https://huggingface.co/nvidia/segformer-b0-finetuned-ade-512-512/raw/main/README.md | hf readme nvidia/segformer-b0 |
| F0521 | 200 | 2026-09-26T20:12:46Z | https://raw.githubusercontent.com/stanfordmlgroup/ngboost/HEAD/LICENSE | license text stanfordmlgroup/ngboost (LICENSE) |
| F0522 | 200 | 2026-09-26T20:12:46Z | https://raw.githubusercontent.com/perpetual-ml/perpetual/HEAD/LICENSE | license text perpetual-ml/perpetual (LICENSE) |
| F0523 | 200 | 2026-09-26T20:12:46Z | https://raw.githubusercontent.com/google-research/tabfm/HEAD/LICENSE | license text google-research/tabfm (LICENSE) |
| F0527 | 200 | 2026-09-26T20:23:57Z | https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/apple-aiml-research%2Fml-depth-pro | ecosystems repo apple-aiml-research/ml-depth-pro |
| F0528 | 000000 | 2026-09-26T20:23:57Z | https://raw.githubusercontent.com/cuml?  | x |
| F0529 | 200 | 2026-09-26T20:23:58Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/cuml-cu13 | ecosystems pypi cuml-cu13 (sibling wheel) |
| F0530 | 200 | 2026-09-26T20:23:58Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/u8darts | ecosystems pypi u8darts (sibling wheel) |
| F0531 | 200 | 2026-09-26T20:23:59Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/opencv-contrib-python | ecosystems pypi opencv-contrib-python (sibling wheel) |
| F0532 | 200 | 2026-09-26T20:23:59Z | https://packages.ecosyste.ms/api/v1/registries/pypi.org/packages/opencv-python-headless | ecosystems pypi opencv-python-headless (sibling wheel) |
| W0001 | WebSearch | 2026-09-26T20:00:26Z | most downloaded Python machine learning libraries PyPI 2026 scikit-learn xgboost lightgbm | (excerpt in web-log.tsv) |
| W0002 | WebSearch | 2026-09-26T20:00:26Z | new open source object detection model 2026 real-time DETR YOLO release Apache-2.0 | (excerpt in web-log.tsv) |
| W0003 | WebSearch | 2026-09-26T20:00:26Z | tabular foundation model 2025 2026 TabPFN open source release | (excerpt in web-log.tsv) |
| W0004 | WebSearch | 2026-09-26T20:00:26Z | DINOv3 SAM 3 release Meta vision backbone license 2025 | (excerpt in web-log.tsv) |
| W0006 | WebSearch | 2026-09-26T20:00:46Z | time series forecasting library python 2026 sktime darts statsforecast nixtla comparison | (excerpt in web-log.tsv) |
| W0008 | WebSearch | 2026-09-26T20:00:46Z | alternatives to scikit-learn 2026 new ML library skrub cuML river | (excerpt in web-log.tsv) |
| W0010 | WebSearch | 2026-09-26T20:00:46Z | hyperparameter optimization AutoML library 2026 Optuna AutoGluon FLAML release | (excerpt in web-log.tsv) |
| W0011 | WebSearch | 2026-09-26T20:05:47Z | Google TabFM tabular foundation model release 2026 | (excerpt in web-log.tsv) |
| W0012 | WebSearch | 2026-09-26T20:05:47Z | NVIDIA C-RADIO v3 vision foundation backbone license huggingface | (excerpt in web-log.tsv) |
| W0013 | WebSearch | 2026-09-26T20:05:47Z | Falcon Perception TII open vocabulary segmentation model 2026 | (excerpt in web-log.tsv) |
| W0014 | WebSearch | 2026-09-26T20:05:47Z | gradient boosting library new 2025 2026 PerpetualBooster ngboost open source release | (excerpt in web-log.tsv) |
| W0015 | WebSearch | 2026-09-26T20:05:47Z | Meta Perception Encoder vision backbone release license PE core | (excerpt in web-log.tsv) |
| W0016 | WebSearch | 2026-09-26T20:08:15Z | OpenCV 5.0 release 2026 | (excerpt in web-log.tsv) |
| W0017 | WebSearch | 2026-09-26T20:08:15Z | spaCy Explosion 2025 2026 maintenance status future of spaCy | (excerpt in web-log.tsv) |
| W0018 | WebSearch | 2026-09-26T20:08:15Z | Ultralytics enterprise license AGPL-3.0 YOLO commercial use | (excerpt in web-log.tsv) |
| W0020 | WebFetch | 2026-09-26T20:13:23Z | https://github.com/apple/ml-depth-pro | (excerpt in web-log.tsv) |

## 7. Parked candidates

All fetched 2026-09-26. "Source" is the fetch id; the URL is in the log.

| # | name | reason | source | fetch date |
|---|---|---|---|---|
| 1 | fastText (facebookresearch/fastText) | unmaintained: repo **archived**, last push 2024-03-22; PyPI still 1,961,463 / month (F0067), so the downloads outlived the repo | F0065 | 2026-09-26 |
| 2 | Mask2Former | unmaintained: repo **archived** (last push 2024-07-29) | F0168 | 2026-09-26 |
| 3 | MMSegmentation | identity unclear: one row per OpenMMLab toolbox, or MMDetection standing in for the family (Q4); dormant since 2024-08-13 | F0089 | 2026-09-26 |
| 4 | MMCV | identity: the shared foundation library of the OpenMMLab toolboxes rather than a user-facing product (Q4) | F0092 | 2026-09-26 |
| 5 | MMPretrain | identity unclear (Q4); dormant since 2024-11-01 | F0095 | 2026-09-26 |
| 6 | MMPose | identity unclear (Q4); last push 2025-08-04 | F0098 | 2026-09-26 |
| 7 | YOLOv9 (WongKinYiu) | identity unclear: named for a release with a version token; not a product line (Q11); GPL-3.0 (F0351) | F0165 | 2026-09-26 |
| 8 | YOLOv10 (THU-MIG) | identity unclear (Q11); AGPL-3.0 (F0344); last push 2025-03-14 | F0246 | 2026-09-26 |
| 9 | YOLOv12 (sunsmarterjie) | identity unclear (Q11); AGPL-3.0 (F0343) | F0163 | 2026-09-26 |
| 10 | Grounding DINO | boundary → `multimodal_models` (text-prompted detection) | F0171, F0412 | 2026-09-26 |
| 11 | Falcon Perception (TII) | boundary → `multimodal_models` (open-vocabulary grounding from language prompts, W0013) | F0442, F0406 | 2026-09-26 |
| 12 | Perception Encoder (Meta) | boundary → `embeddings_retrieval` (contrastive vision–language encoder) | F0441, W0015 | 2026-09-26 |
| 13 | LocateAnything GGUF (mudler/locate-anything.cpp-gguf) | community re-upload of an NVIDIA 3B model (card links nvidia/LocateAnything-3B); boundary → `multimodal_models` | F0417 | 2026-09-26 |
| 14 | ViT (google/vit-base-patch16-224) | identity: a 2020 research checkpoint; Google's vision code home google-research/big_vision is already claimed by `siglip` in the index | F0410 | 2026-09-26 |
| 15 | PaddleX | boundary: all-in-one Paddle pipeline tool overlapping `paddleocr` (document_conversion) and deployment | F0120 | 2026-09-26 |
| 16 | Roboflow Inference | boundary → `inference_code`/`deployment` (serving); Apache core + enterprise dirs (F0326) | F0147 | 2026-09-26 |
| 17 | FiftyOne | boundary → `dataset_processing_tools` | F0144 | 2026-09-26 |
| 18 | Optuna | boundary → `ml_orchestration` (HPO; Katib precedent). PyPI 15,452,541 / month (F0219) | F0217 | 2026-09-26 |
| 19 | Hyperopt | boundary → `ml_orchestration` | F0220 | 2026-09-26 |
| 20 | SHAP | boundary → `evaluation_code` / `responsible_ai_measurement`. PyPI 8,775,575 / month (F0225) | F0223 | 2026-09-26 |
| 21 | LIME | boundary, as SHAP; last release 2020-06-26 (F0227) | F0226 | 2026-09-26 |
| 22 | Captum | boundary, as SHAP; repo now meta-pytorch/captum | F0237 | 2026-09-26 |
| 23 | InterpretML | boundary, as SHAP | F0232 | 2026-09-26 |
| 24 | Mitra (autogluon/mitra-classifier) | SKU of AutoGluon (shipped as an AutoGluon model, HF org autogluon) | F0402 | 2026-09-26 |
| 25 | Chronos (amazon-science/chronos-forecasting) | boundary: time-series foundation models, in or out (Q3) | F0492, F0429 | 2026-09-26 |
| 26 | Spark MLlib | SKU of Apache Spark; no artifact of its own fetched | W0008 | 2026-09-26 |
| 27 | Community fine-tuned checkpoints (class: NSFW/gender/age classifiers, YOLOv8 table/licence-plate fine-tunes, Xenova ONNX conversions, *-random test models) | not products | F0001, F0002, F0003, F0004 | 2026-09-26 |
| 28 | Table Transformer (microsoft) | boundary → `document_conversion` | F0002 | 2026-09-26 |
| 29 | PP-DocLayout (PaddlePaddle) | boundary → `document_conversion` | F0002 | 2026-09-26 |
| 30 | CLIPSeg (CIDAS) | boundary → `multimodal_models` (text-prompted segmentation) | F0003 | 2026-09-26 |
| 31 | DETR (facebook/detr-resnet-50) | identity unclear (not researched this run; 340,748 / 30d) | F0002 | 2026-09-26 |
| 32 | YOLOS (hustvl) | identity unclear (not researched this run) | F0002 | 2026-09-26 |
| 33 | OneFormer (shi-labs) | identity unclear (not researched this run) | F0003 | 2026-09-26 |
| 34 | MedSAM | derivative of SAM, domain-tuned → `scientific_ai_models` | F0004 | 2026-09-26 |
| 35 | SAM derivatives (class: SlimSAM, EdgeTAM, SAM-HQ, sam3-litetext) | derivatives of the SAM line, not separate products (not researched further) | F0004 | 2026-09-26 |
| 36 | Depth long tail (class: DPT/ZoeDepth by Intel, Marigold, DepthCrafter, Distill-Any-Depth) | identity unclear (not researched this run) | F0005 | 2026-09-26 |
| 37 | Pathology backbones (class: MahmoodLab UNI/CONCH/TITAN, Virchow2, H-optimus-0) | boundary → `scientific_ai_models` | F0006 | 2026-09-26 |
| 38 | nomic-embed-vision, MegaLoc | boundary → `embeddings_retrieval` | F0006 | 2026-09-26 |
| 39 | TabPFN-mix (autogluon/tabpfn-mix-1.0-classifier) | SKU of AutoGluon | F0007 | 2026-09-26 |
| 40 | BEN2 (PramaLLC) | identity unclear (not researched this run) | F0003 | 2026-09-26 |
| 41 | FoMo-0D, MetaTree (class) | identity unclear (not researched this run) | F0007 | 2026-09-26 |
| 42 | Legacy architecture checkpoints (class: microsoft/resnet-50, swinv2, beit; facebook/convnextv2, deit) | not separate products: architecture releases whose use runs through timm/transformers | F0001, F0003 | 2026-09-26 |

## 8. Reconciled counts

Unit: one distinct named candidate (or one named class, rows 27/35/36/37/41/42) that reached
triage from the brief's leads, the HF lists (F0001–F0007) or search (W0001–W0020).

Duplicate signals (14), caught by dedup:
- **Index head or tail (6):** segment-anything (F0004, scientific_ai_models tail), sam2 (F0004,
  tail), SAM 3 (F0152, F0386, a new SKU of that tail line), pytorch-lightning (ml_frameworks head,
  brief lead), CLIP via timm mirror (F0006, embeddings_retrieval head), SigLIP via timm mirror
  (F0006, head).
- **Self-dedup into an accepted row (8):** opencv-python repo → opencv (F0075); albumentations
  MIT package → albumentations (F0104); Depth-Anything-V2 repo → depth-anything (F0156); Depth
  Anything V1 LiheYoung checkpoints → depth-anything (F0005); dinov2 repo → dino (F0150);
  tabfm-jax → tabfm (F0007); Ultralytics YOLO11/YOLO26 HF → ultralytics (F0407, F0408);
  RMBG-1.4 → rmbg (F0003).

```
raw_signals       = duplicate_signals + unique_candidates
137               = 14                + 123
unique_candidates = accepted + parked
123               = 81       + 42
```

## 9. Open questions for the maintainer

1. **One category or two?** (a) one `classic_ml_cv` (81 rows); (b) split into `classic_ml`
   (tabular/NLP/time-series/AutoML/tabular FMs, 45 rows + 1 closed) and `computer_vision`
   (libraries + vision model lines, 33 rows + 2 closed). **Recommend (a) now and (b) later.** Both
   halves clear 10, but one category is cheaper to build first, and the capability ladder is where
   the split would pay off.
2. **Do timm, torchvision and fastai sit here, not in `ml_frameworks`?** Recommend **yes**: they
   are vision-first libraries, not frameworks the stack imports. Feluda stays in `ml_frameworks`
   for now.
3. **Are pretrained time-series forecasters (Chronos and similar) in scope, the way tabular FMs
   are?** Recommend **yes, as a follow-up sweep**. They are the forecasting analogue of TabPFN,
   but this run did not research them. skrub is kept as feature-engineering-for-sklearn. Say
   no if the line is "fits a model" in the strict sense.
4. **OpenMMLab: one row per toolbox, or MMDetection alone?** Recommend **MMDetection alone for
   now**. The toolboxes are dormant (MMDetection last pushed 2024-08-21, F0086; MMSegmentation
   2024-08-13, F0089; MMPretrain 2024-11-01, F0095), so per-toolbox rows would add four inactive
   rows from one org.
5. **Org slugs where the repo owner is a person or a moved org** (lightgbm-org vs microsoft,
   lyuwenyu for RT-DETR, peterande for D-FINE, yzhao062, lmcinnes). Recommend **keep the handle
   slugs**, because institution attribution was not fetched, and revisit when org files are
   written at promotion.
6. **timm's adoption: count the HF `timm/*` namespace** (47.2M / 30d, F0427), which mirrors
   DINO/SigLIP/CLIP weights, **or PyPI only** (10.3M, F0078)? Recommend **PyPI only**; the HF
   namespace double-counts other vendors' models.
7. **Albumentations after the relicense.** Point the row at AlbumentationsX (live, AGPL, 10.7K /
   month, F0109), as drafted, or at the archived MIT package that still draws 2.74M / month
   (F0106)? Recommend **AlbumentationsX, as drafted**, with the frozen package's figure recorded
   as a note, not as adoption.
8. **SAP RPT-1 OSS: an open satellite of a closed SAP service?** Not fetched. Recommend **hold
   the row as-is and check at promotion** (identity.md, "An open satellite around a closed core").
9. **Closed comparators (ADR-005).** Accept Google Cloud Vision API, Amazon Rekognition and
   DataRobot Predictive AI, or none until a best-in-class reading is done? Recommend **accept the
   two vision APIs, and hold DataRobot** until the surface is pinned. Its platform page (F0513)
   now leads with agentic products.
10. **Ladder map and weights.** Use `extends: {model: pretrained, software: software}` with adopt
    0.6 / cap 0.4? Recommend **yes**.
11. **YOLO academic releases (v9, v10, v12).** Park them as release-named (drafted), or accept
    one row each with a version-free slug? Recommend **park**. Ultralytics is the product line,
    and the other three are single paper releases from different labs.
12. **SAM line.** Move `segment-anything` here and fold `sam2` and SAM 3 into it, with the SAM
    License as most restrictive? Recommend **yes** (section 3).
13. **Custom licenses to place in tiers:** FSL-1.1-MIT (pycaret), BSL-1.0 Boost (dlib, must not
    match BSL-1.1), DINOv3 License, SAM License, Sapiens2 License, TABPFN-3, TabFM-NC,
    Stable AI/LimiX, EXAONE 1.2-NC, apple-amlr, NVIDIA Source Code License. Recommend
    **a maintainer ruling on each before promotion**, as with embeddings_retrieval's three.

