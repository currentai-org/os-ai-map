# Classic ML & computer vision seed: 2026-09-26

## Scope and boundary

This batch seeds the preliminary `classic_ml_cv` category proposed in issue #600. It holds the
libraries and pretrained model lines for machine learning outside the LLM stack: classical and
gradient-boosted estimators, classical NLP pipelines, time-series forecasters, tabular AutoML and
tabular foundation models, and computer-vision libraries, backbones and perception models.

The litmus is whether the product fits, runs or ships a prediction model (or the vision primitives
one is built from) that a data scientist would use before any LLM is involved. It passes only if
its reason for fame predates the LLM stack or runs orthogonal to it. Inside that, the scope test is
"does it fit or run a model", which keeps tabular AutoML and time-series estimator libraries in,
keeps CV primitives (OpenCV, scikit-image, Kornia, Albumentations, supervision) in because nothing
else on the map owns them, and parks tuning, explainability and curation tools with their
neighbors. The full boundary, with each neighbor named, is in the category's `comments`.

Rulings applied from the 2026-09-26 new-category decisions (`research/decisions.md` on the research
kit branch), and from the sweep's own recommendations where the decisions are silent:

- **One category, not two** (Q1a). The tabular/NLP/time-series half and the vision half each clear
  ten rows, and the split stays open for when the capability ladder shows it is needed.
- **Mixed type:** `extends: {model: pretrained, software: software}`, weights adopt 0.6 / cap 0.4,
  in Infrastructure → Compute & runtime after `ml_frameworks`.
- **Segment Anything moves here** from the `scientific_ai_models` tail. `segment-anything` and
  `sam2` were two tail rows there; they are now one `segment-anything` row that also covers SAM 3,
  whose custom SAM License is the line's most restrictive.
- **DINO and timm are owned here** (ruled on #600 on 2026-09-25). The pointer in
  `embeddings_retrieval`'s `comments` that deferred them to issue #9 now points here.
- **timm, torchvision and fastai** sit here rather than in `ml_frameworks` (Q2): they are
  vision-first libraries, not frameworks the rest of the stack imports.
- **DataRobot is held** (Q9). Google Cloud Vision and Amazon Rekognition are the closed
  comparators seeded.
- **MMDetection alone** stands for OpenMMLab (Q4); the YOLO academic releases are parked (Q11);
  Albumentations points at AlbumentationsX (Q7); timm's adoption is PyPI only (Q6); SAP RPT-1 OSS
  is held as-is for a satellite check at promotion (Q8); pretrained time-series forecasters wait
  for a follow-up sweep (Q3).

No row was scored. Each row carries identity and artifacts only, as the registry schema requires.

## Inputs swept

All fetched on 2026-09-26. The full fetch trail (every `Fnnnn` body under `raw/`, with its UTC
timestamp, HTTP code and sha256 in `fetch-log.tsv`, and every `Wnnnn` WebSearch or WebFetch call in
`web-log.tsv`) is on branch `claude/research-classic_ml_cv` under `research/classic_ml_cv/`,
together with the per-row evidence table (`sweep.md` §6b) and the two-pass independent audit
(`audit.md`, final status PASS).

| Input | What was read |
|---|---|
| Issue #600 brief | The named leads |
| Hugging Face task lists | The top 40 by downloads for seven pipeline tags: image-classification, object-detection, image-segmentation, mask-generation, depth-estimation, image-feature-extraction, tabular-classification |
| Search | 20 WebSearch and WebFetch calls for 2025–2026 releases, awesome lists and "alternatives to" pages |
| Per candidate | ecosyste.ms and ungh repository metadata (canonical name, archived, fork, push date), the LICENSE text at HEAD, PyPI JSON and ecosyste.ms package downloads, the Hugging Face model API |

**Retrieval cutoff.** The Hugging Face task lists were read to rank 40 and nothing below it was
reviewed. Model families inside the top 40 that were not researched individually are parked as
"identity unclear (not researched this run)" rather than dropped. There was no numeric cutoff on
libraries.

## Reconciled counts

A raw signal is one input naming one candidate. Duplicate signals are candidates already in the
index (head or tail) or folded into another accepted candidate. The sweep's own equations hold as
written; this seed then applies the decisions on top of them.

```text
sweep:
raw_signals       = duplicate_signals + unique_candidates
137               = 14                + 123
unique_candidates = accepted + parked
123               = 81       + 42

seed (after the decisions):
unique_candidates = accepted + parked
123               = 80       + 43        (DataRobot held: accepted -> parked)

registry rows     = accepted + moved in
81                = 80       + 1         (segment-anything from the scientific_ai_models tail, sam2 folded in)
```

The moved-in row is not a new candidate: the sweep counted `segment-anything`, `sam2` and SAM 3
among its 14 duplicate signals, because both tail rows were already in the index. The move removes
those two rows from `sources/registry/scientific_ai_models.yaml` and adds one here.

By type: 58 software and 23 model rows. By status at sweep time: 64 open, 14 open-weights, 1
source-available and 2 closed. The 81 rows name 67 organizations; the largest, Meta, holds 6
(detectron2, prophet, dino, sapiens, cotracker and segment-anything), 7.4%.

No row collides with a head product, a retired alias or an existing registry row
(`research/crosscheck.py`: 0 findings before the registry file was written).

## Organizations and handles

Of the 67 organizations, 54 had no organization file. Each now has a minimal one
(`products: []`, since tail rows sit in no org roster) so that its accounts could be registered in
`sources/org_handles.yaml`, which the handle-coverage ratchet in `tests/test_identity_eval.py`
requires. Handles are the repository owner on GitHub and the namespace on Hugging Face, as the rows
declare them, with a `note` where the account name differs from the org (CatBoost for Yandex,
piskvorky for RaRe Technologies, SAP-samples for SAP, limix-ldm-ai for Stable AI, alana89 for
alanarazi7). Three existing orgs gained a handle on a route they had none for: `pytorch-foundation`
(github `pytorch`), `amazon-web-services` (github `awslabs`) and `apple` (github
`apple-aiml-research`, huggingface `apple`).

Two Hugging Face namespaces were deliberately left unassigned: `PekingU` (RT-DETR, org
`lyuwenyu`) and `ustc-community` (D-FINE, org `peterande`). Each is an institutional account
publishing a personal repository's weights, and claiming it for the individual would be wrong
ownership evidence.

Types are `unknown` wherever the affiliation was not fetched, including most community projects.
No homepage was written, because none was fetched for the org as such.

## Accepted candidates

The primary source is the artifact the row's identity rests on: the GitHub repository where there
is one, else the Hugging Face model, else the homepage. The status is the sweep's reading of the
license texts, not a score.

| Candidate | Slug | Type | Org | Status at sweep | Primary source | Fetched |
|---|---|---|---|---|---|---|
| scikit-learn | `scikit-learn` | software | `scikit-learn` | open | https://github.com/scikit-learn/scikit-learn | 2026-09-26 |
| XGBoost | `xgboost` | software | `dmlc` | open | https://github.com/dmlc/xgboost | 2026-09-26 |
| LightGBM | `lightgbm` | software | `lightgbm-org` | open | https://github.com/lightgbm-org/LightGBM | 2026-09-26 |
| CatBoost | `catboost` | software | `yandex` | open | https://github.com/catboost/catboost | 2026-09-26 |
| statsmodels | `statsmodels` | software | `statsmodels` | open | https://github.com/statsmodels/statsmodels | 2026-09-26 |
| imbalanced-learn | `imbalanced-learn` | software | `scikit-learn-contrib` | open | https://github.com/scikit-learn-contrib/imbalanced-learn | 2026-09-26 |
| PyOD | `pyod` | software | `yzhao062` | open | https://github.com/yzhao062/pyod | 2026-09-26 |
| UMAP | `umap` | software | `lmcinnes` | open | https://github.com/lmcinnes/umap | 2026-09-26 |
| HDBSCAN | `hdbscan` | software | `scikit-learn-contrib` | open | https://github.com/scikit-learn-contrib/hdbscan | 2026-09-26 |
| cuML | `cuml` | software | `nvidia` | open | https://github.com/NVIDIA/cuml | 2026-09-26 |
| River | `river` | software | `online-ml` | open | https://github.com/online-ml/river | 2026-09-26 |
| skrub | `skrub` | software | `skrub-data` | open | https://github.com/skrub-data/skrub | 2026-09-26 |
| mlpack | `mlpack` | software | `mlpack` | open | https://github.com/mlpack/mlpack | 2026-09-26 |
| H2O-3 | `h2o-3` | software | `h2o-ai` | open | https://github.com/h2oai/h2o-3 | 2026-09-26 |
| NGBoost | `ngboost` | software | `stanfordmlgroup` | open | https://github.com/stanfordmlgroup/ngboost | 2026-09-26 |
| Perpetual | `perpetual` | software | `perpetual-ml` | open | https://github.com/perpetual-ml/perpetual | 2026-09-26 |
| ML.NET | `ml-net` | software | `microsoft` | open | https://github.com/dotnet/machinelearning | 2026-09-26 |
| Dask-ML | `dask-ml` | software | `dask` | open | https://github.com/dask/dask-ml | 2026-09-26 |
| spaCy | `spacy` | software | `explosion` | open | https://github.com/explosion/spaCy | 2026-09-26 |
| NLTK | `nltk` | software | `nltk` | open | https://github.com/nltk/nltk | 2026-09-26 |
| Gensim | `gensim` | software | `rare-technologies` | open | https://github.com/piskvorky/gensim | 2026-09-26 |
| Stanza | `stanza` | software | `stanford-nlp` | open | https://github.com/stanfordnlp/stanza | 2026-09-26 |
| Stanford CoreNLP | `corenlp` | software | `stanford-nlp` | open | https://github.com/stanfordnlp/CoreNLP | 2026-09-26 |
| Flair | `flair` | software | `flairnlp` | open | https://github.com/flairNLP/flair | 2026-09-26 |
| TextBlob | `textblob` | software | `sloria` | open | https://github.com/sloria/TextBlob | 2026-09-26 |
| OpenCV | `opencv` | software | `opencv` | open | https://github.com/opencv/opencv | 2026-09-26 |
| timm (PyTorch Image Models) | `timm` | software | `hugging-face` | open | https://github.com/huggingface/pytorch-image-models | 2026-09-26 |
| torchvision | `torchvision` | software | `pytorch-foundation` | open | https://github.com/pytorch/vision | 2026-09-26 |
| Ultralytics YOLO | `ultralytics` | software | `ultralytics` | open | https://github.com/ultralytics/ultralytics | 2026-09-26 |
| Detectron2 | `detectron2` | software | `meta` | open | https://github.com/facebookresearch/detectron2 | 2026-09-26 |
| MMDetection | `mmdetection` | software | `open-mmlab` | open | https://github.com/open-mmlab/mmdetection | 2026-09-26 |
| Kornia | `kornia` | software | `kornia` | open | https://github.com/kornia/kornia | 2026-09-26 |
| Albumentations | `albumentations` | software | `albumentations-team` | open | https://github.com/albumentations-team/AlbumentationsX | 2026-09-26 |
| supervision | `supervision` | software | `roboflow` | open | https://github.com/roboflow/supervision | 2026-09-26 |
| scikit-image | `scikit-image` | software | `scikit-image` | open | https://github.com/scikit-image/scikit-image | 2026-09-26 |
| MediaPipe | `mediapipe` | software | `google` | open | https://github.com/google-ai-edge/mediapipe | 2026-09-26 |
| PaddleDetection | `paddledetection` | software | `paddlepaddle` | open | https://github.com/PaddlePaddle/PaddleDetection | 2026-09-26 |
| MONAI | `monai` | software | `project-monai` | open | https://github.com/Project-MONAI/MONAI | 2026-09-26 |
| Lightly | `lightly` | software | `lightly-ai` | open | https://github.com/lightly-ai/lightly | 2026-09-26 |
| LightlyTrain | `lightly-train` | software | `lightly-ai` | open | https://github.com/lightly-ai/lightly-train | 2026-09-26 |
| fastai | `fastai` | software | `fastai` | open | https://github.com/fastai/fastai | 2026-09-26 |
| dlib | `dlib` | software | `davisking` | open | https://github.com/davisking/dlib | 2026-09-26 |
| InsightFace | `insightface` | software | `deepinsight` | open | https://github.com/deepinsight/insightface | 2026-09-26 |
| TorchGeo | `torchgeo` | software | `torchgeo` | open | https://github.com/torchgeo/torchgeo | 2026-09-26 |
| sktime | `sktime` | software | `sktime` | open | https://github.com/sktime/sktime | 2026-09-26 |
| Darts | `darts` | software | `unit8` | open | https://github.com/unit8co/darts | 2026-09-26 |
| StatsForecast | `statsforecast` | software | `nixtla` | open | https://github.com/Nixtla/statsforecast | 2026-09-26 |
| NeuralForecast | `neuralforecast` | software | `nixtla` | open | https://github.com/Nixtla/neuralforecast | 2026-09-26 |
| Prophet | `prophet` | software | `meta` | open | https://github.com/facebook/prophet | 2026-09-26 |
| pmdarima | `pmdarima` | software | `alkaline-ml` | open | https://github.com/alkaline-ml/pmdarima | 2026-09-26 |
| GluonTS | `gluonts` | software | `amazon-web-services` | open | https://github.com/awslabs/gluonts | 2026-09-26 |
| AutoGluon | `autogluon` | software | `autogluon` | open | https://github.com/autogluon/autogluon | 2026-09-26 |
| FLAML | `flaml` | software | `microsoft` | open | https://github.com/microsoft/FLAML | 2026-09-26 |
| PyCaret | `pycaret` | software | `pycaret` | source-available | https://github.com/pycaret/pycaret | 2026-09-26 |
| TPOT | `tpot` | software | `epistasislab` | open | https://github.com/EpistasisLab/tpot | 2026-09-26 |
| auto-sklearn | `auto-sklearn` | software | `automl-freiburg` | open | https://github.com/automl/auto-sklearn | 2026-09-26 |
| DINO (DINOv2, DINOv3) | `dino` | model | `meta` | open-weights | https://github.com/facebookresearch/dinov3 | 2026-09-26 |
| C-RADIO | `radio` | model | `nvidia` | open-weights | https://github.com/NVlabs/RADIO | 2026-09-26 |
| Depth Anything | `depth-anything` | model | `bytedance-seed-volcano-engine` | open-weights | https://github.com/ByteDance-Seed/Depth-Anything-3 | 2026-09-26 |
| Depth Pro | `depth-pro` | model | `apple` | open-weights | https://github.com/apple-aiml-research/ml-depth-pro | 2026-09-26 |
| RT-DETR | `rt-detr` | model | `lyuwenyu` | open | https://github.com/lyuwenyu/RT-DETR | 2026-09-26 |
| RF-DETR | `rf-detr` | model | `roboflow` | open | https://github.com/roboflow/rf-detr | 2026-09-26 |
| D-FINE | `d-fine` | model | `peterande` | open | https://github.com/Peterande/D-FINE | 2026-09-26 |
| DEIM | `deim` | model | `intellindust` | open | https://github.com/Intellindust-AI-Lab/DEIM | 2026-09-26 |
| BiRefNet | `birefnet` | model | `zhengpeng7` | open | https://github.com/ZhengPeng7/BiRefNet | 2026-09-26 |
| BRIA RMBG | `rmbg` | model | `bria-ai` | open-weights | https://huggingface.co/briaai/RMBG-2.0 | 2026-09-26 |
| SegFormer | `segformer` | model | `nvidia` | open-weights | https://github.com/NVlabs/SegFormer | 2026-09-26 |
| Sapiens | `sapiens` | model | `meta` | open-weights | https://github.com/facebookresearch/sapiens2 | 2026-09-26 |
| Segment Anything (SAM) | `segment-anything` | model | `meta` | open-weights | https://github.com/facebookresearch/sam3 | 2026-09-26 |
| EoMT | `eomt` | model | `tue-mps` | open | https://github.com/tue-mps/eomt | 2026-09-26 |
| CoTracker | `cotracker` | model | `meta` | open-weights | https://github.com/facebookresearch/co-tracker | 2026-09-26 |
| TabPFN | `tabpfn` | model | `prior-labs` | open-weights | https://github.com/PriorLabs/TabPFN | 2026-09-26 |
| TabICL | `tabicl` | model | `inria-soda` | open | https://github.com/soda-inria/tabicl | 2026-09-26 |
| SAP RPT-1 (OSS) | `sap-rpt-1` | model | `sap` | open | https://github.com/SAP-samples/sap-rpt-1-oss | 2026-09-26 |
| LimiX | `limix` | model | `stable-ai` | open-weights | https://github.com/limix-ldm-ai/LimiX | 2026-09-26 |
| TabFM | `tabfm` | model | `google-research` | open-weights | https://github.com/google-research/tabfm | 2026-09-26 |
| Nori | `nori` | model | `synthefy` | open | https://huggingface.co/Synthefy/Nori | 2026-09-26 |
| TabSTAR | `tabstar` | model | `alanarazi7` | open-weights | https://huggingface.co/alana89/TabSTAR | 2026-09-26 |
| EXAONE Tabular | `exaone-tabular` | model | `lg-ai-research` | open-weights | https://github.com/LGAI-Research/EXAONE-Tabular | 2026-09-26 |
| Google Cloud Vision API | `google-cloud-vision` | software | `google-cloud` | closed | https://cloud.google.com/vision | 2026-09-26 |
| Amazon Rekognition | `amazon-rekognition` | software | `amazon-web-services` | closed | https://aws.amazon.com/rekognition/ | 2026-09-26 |

## Parked candidates

All fetched 2026-09-26. The source column is the fetch id in the evidence branch's logs.
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
| 43 | DataRobot Predictive AI | held by the 2026-09-26 decisions (Q9): the closed comparator is accepted only once its surface is pinned, and the platform page now leads with agentic products rather than the predictive/AutoML product | F0513 (https://www.datarobot.com/platform/) | 2026-09-26 |

## Identity notes for promotion

- **One artifact per kind.** For a multi-checkpoint line the Hugging Face id is the current
  flagship checkpoint (DINOv3, Depth Anything 3, Sapiens2, C-RADIOv3, TabPFN 3), and the GitHub
  repository is the current line's. `segment-anything` follows the same rule and now points at
  `facebookresearch/sam3` and `facebook/sam3`; the retired tail rows pointed at
  `facebookresearch/segment-anything` and `facebookresearch/sam2`, which are the line's earlier
  releases and are Apache-2.0. All four artifacts were fetched live in the sweep (F0152 and
  F0386 for SAM 3, F0443 and F0444 for the earlier repositories; SAM License text F0333).
- **Packages** are declared only where PyPI `project_urls` (or ecosyste.ms `repository_url`) point
  back at the declared repository. Two exceptions: `opencv-python` is built from the OpenCV org's
  packaging repository, and `tabstar`'s package comes from its card's install line.
- **ml-net** carries GitHub only: its adoption channel is NuGet, which has no registry field.
- **nori** carries Hugging Face and PyPI but no GitHub: the repository is named on the card and was
  not fetched.
- **Moved repositories:** LightGBM moved from `microsoft/` to `lightgbm-org/`, Depth Pro from
  `apple/` to `apple-aiml-research/`, gensim's canonical owner is `piskvorky`, and LimiX's account
  was renamed from `limix-ldm`.
- **Adoption instruments.** timm is PyPI only, because the HF `timm/` namespace mirrors DINO, SigLIP
  and CLIP weights. Albumentations is AlbumentationsX; the archived MIT package's downloads are a
  note, not adoption. torchvision's downloads partly reflect installation alongside torch.
- **Activity.** MMDetection and SegFormer have had no push in over two years at sweep time; TPOT
  missed the twelve-month window by days. Recheck all three before promoting them.
- **Licenses that need a ruling first** (one maintainer license-rulings issue, never a category PR):
  FSL-1.1-MIT (pycaret), BSL-1.0 Boost (dlib, which must not match BSL-1.1 Business Source), the
  DINOv3 License, the SAM License, the Sapiens2 License, the Prior Labs TabPFN weights licenses,
  TabFM Non-Commercial, the Stable AI LimiX code and weights licenses, EXAONE AI Model License
  1.2-NC, apple-amlr, and the NVIDIA Source Code License (SegFormer, RADIO code). InsightFace ships
  no root LICENSE file and states an MIT-code, non-commercial-models split in its README. Products
  carrying one of these are deferred at promotion.
- **Open satellite check.** SAP RPT-1 OSS may be the open satellite of a closed SAP service; this
  was not fetched and should be settled against `docs/reference/identity.md` at promotion.

## Open items for the maintainer

1. **The split.** One category now; revisit the tabular / vision split when the capability ladder
   is built, since that is where it would pay off.
2. **Pretrained time-series forecasters** (Chronos and its kind) are in scope in principle and wait
   for a follow-up sweep.
3. **DataRobot** as a closed comparator, once its predictive surface is pinned.
4. **Org slugs** that are personal or moved accounts (`lightgbm-org`, `lyuwenyu`, `peterande`,
   `yzhao062`, `lmcinnes`) keep the account slug until promotion attributes them to an institution.
5. **The two unassigned Hugging Face namespaces** (`PekingU`, `ustc-community`) above.
6. **The license strings** listed above, in the shared license-rulings issue.
