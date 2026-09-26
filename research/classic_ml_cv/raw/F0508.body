---
license: other
license_name: exaone
license_link: LICENSE
pipeline_tag: tabular-classification
tags:
  - tabular
  - tabular-classification
  - tabular-regression
  - in-context-learning
  - foundation-model
  - pytorch
  - safetensors
  - exaone
metrics:
  - accuracy
---

<br>

<div align="center">
  <img src="assets/exaone_logo.png" alt="EXAONE Tabular" width="160">
  <h1>EXAONE Tabular</h1>
</div>

<br>

<div align="center">
  <a href="https://huggingface.co/LG-AI-Research/EXAONE-Tabular" style="text-decoration: none;">
    <img src="https://img.shields.io/badge/🤗-HuggingFace-FC926C?style=for-the-badge" alt="HuggingFace">
  </a>
  <a href="https://github.com/LGAI-Research/EXAONE-Tabular" style="text-decoration: none;">
    <img src="https://img.shields.io/badge/🖥️-GitHub-2B3137?style=for-the-badge" alt="GitHub">
  </a>
</div>

<br><br>

**EXAONE Tabular** is a transformer-based **foundation model for tabular data** that solves
**classification** and **regression** through **in-context learning**: you pass the labeled
rows to `fit` and the model predicts new rows in a single forward pass — **no gradient
updates and no per-dataset training**.

This repository is the **`exaonetabular` inference runtime** — a self-contained package
that loads a released checkpoint and serves predictions through a small, scikit-learn-style API.
The code here is permissively licensed; the released **weights are non-commercial** — see
[License](#license).

Both checkpoints are released: `EXAONETabularClassifier` and `EXAONETabularRegressor` each fetch
their own weights with a single `from_pretrained()` call. See
[Available checkpoints](#available-checkpoints).

For more details, please refer to the [GitHub repository](https://github.com/LGAI-Research/EXAONE-Tabular) and our [technical report](https://huggingface.co/LG-AI-Research/EXAONE-Tabular/blob/main/EXAONE_Tabular_v1.0_Technical_Report.pdf).
## Model Configuration

<div style="background-color: rgba(128, 128, 128, 0.1); border-radius: 12px; padding: 12px 24px;">

- Model Type: In-context tabular foundation model (Cross-axis Summary Transformer (CAST))

- Embedding dimension: 192
- Attention heads: 6
- Transformer layers: 12
- Feed-forward expansion: 4x
- MLP sharing: Single
- Feature-attention operations per layer: 2
- Feature-level summary tokens: 3
- Row-level summary tokens: 32
- Attention normalization: SSMax
- Total parameters
  - Classification: 20,807,866 (≈20.8M)
  - Regression: 21,110,247 (≈21.1M)

</div>


## Evaluation Results

### TabArena

EXAONE Tabular achieves an overall Elo of **1,755** on TabArena without per-dataset tuning or ensembling. It ranks second overall, first on classification with an Elo of **1,759**, and second on regression with an Elo of **1,883**, while using approximately 21M parameters.

All TabArena results reported below are taken from the official [TabArena leaderboard](https://huggingface.co/spaces/TabArena/leaderboard).

<div align="center">
  <img src="figures/tabarena_overall_elo_model_parameters.svg" alt="Overall TabArena Elo versus model parameters" width="92%">
  <br>
  <em>Figure 1. Overall TabArena Elo versus model size. EXAONE Tabular achieves competitive performance with approximately 21M parameters.</em>
</div>

<div align="center">
  <img src="figures/tabarena_elo_cls_reg.svg" alt="TabArena classification Elo on the left and regression Elo on the right" width="94%">
  <br>
  <em>Figure 2. TabArena Elo scores on classification (left) and regression (right) tasks.</em>
</div>

**Table 1.** *TabArena Elo scores and computational costs. Training and prediction costs are median seconds per 1,000 samples.*

<table>
  <thead>
    <tr>
      <th bgcolor="#EEF2FF" align="left">Model type</th>
      <th bgcolor="#EEF2FF" align="left">Model</th>
      <th bgcolor="#EEF2FF" align="left">Configuration</th>
      <th bgcolor="#EEF2FF" align="right">Overall Elo ↑</th>
      <th bgcolor="#EEF2FF" align="right">Cls. Elo ↑</th>
      <th bgcolor="#EEF2FF" align="right">Reg. Elo ↑</th>
      <th bgcolor="#EEF2FF" align="right">Cost: train / predict (s/1K) ↓</th>
    </tr>
  </thead>
  <tbody>
    <tr bgcolor="#F5F8FF" style="color:#1E3A8A; font-weight:700;"><td style="color:#1E3A8A;"><font color="#1E3A8A"><strong>Foundation Model</strong></font></td><td style="color:#1E3A8A;"><font color="#1E3A8A"><strong>EXAONE Tabular</strong></font></td><td style="color:#1E3A8A;"><font color="#1E3A8A"><strong>Default</strong></font></td><td align="right" style="color:#1E3A8A;"><font color="#1E3A8A"><strong>1,755</strong></font></td><td align="right" style="color:#1E3A8A;"><font color="#1E3A8A"><strong>1,759</strong></font></td><td align="right" style="color:#1E3A8A;"><font color="#1E3A8A"><strong>1,883</strong></font></td><td align="right" style="color:#1E3A8A;"><font color="#1E3A8A"><strong>5.79 / 0.605</strong></font></td></tr>
    <tr><td>Foundation Model</td><td>TabFM</td><td>Default</td><td align="right">1,765</td><td align="right">1,746</td><td align="right">1,993</td><td align="right">38.81 / 6.985</td></tr>
    <tr><td>Foundation Model</td><td>TabPFN-3</td><td>Default</td><td align="right">1,642</td><td align="right">1,635</td><td align="right">1,793</td><td align="right">3.66 / 0.399</td></tr>
    <tr><td>Foundation Model</td><td>TabPFN-2.6</td><td>Default</td><td align="right">1,592</td><td align="right">1,586</td><td align="right">1,734</td><td align="right">5.48 / 0.555</td></tr>
    <tr><td>Foundation Model</td><td>RealTabPFN-2.5</td><td>Tuned + ensembled</td><td align="right">1,572</td><td align="right">1,562</td><td align="right">1,731</td><td align="right">2,040.22 / 8.908</td></tr>
    <tr><td>Foundation Model</td><td>TabICLv2</td><td>Default</td><td align="right">1,569</td><td align="right">1,574</td><td align="right">1,672</td><td align="right">2.05 / 0.151</td></tr>
    <tr><td>Neural Network</td><td>RealMLP</td><td>Tuned + ensembled</td><td align="right">1,482</td><td align="right">1,468</td><td align="right">1,648</td><td align="right">2,950.72 / 11.975</td></tr>
    <tr><td>Foundation Model</td><td>TabDPT</td><td>Tuned + ensembled</td><td align="right">1,437</td><td align="right">1,398</td><td align="right">1,715</td><td align="right">4,910.38 / 286.537</td></tr>
    <tr><td>Neural Network</td><td>TabM</td><td>Tuned + ensembled</td><td align="right">1,426</td><td align="right">1,446</td><td align="right">1,449</td><td align="right">2,450.13 / 2.247</td></tr>
    <tr><td>Tree-based</td><td>LightGBM</td><td>Tuned + ensembled</td><td align="right">1,410</td><td align="right">1,415</td><td align="right">1,477</td><td align="right">417.05 / 2.639</td></tr>
    <tr><td>Tree-based</td><td>CatBoost</td><td>Tuned + ensembled</td><td align="right">1,398</td><td align="right">1,398</td><td align="right">1,484</td><td align="right">1,346.21 / 0.344</td></tr>
    <tr><td>Tree-based</td><td>XGBoost</td><td>Tuned + ensembled</td><td align="right">1,357</td><td align="right">1,364</td><td align="right">1,404</td><td align="right">693.49 / 1.689</td></tr>
    <tr><td>Foundation Model</td><td>TabSwift</td><td>Default</td><td align="right">1,334</td><td align="right">1,339</td><td align="right">1,397</td><td align="right">1.18 / 0.072</td></tr>
    <tr><td>Foundation Model</td><td>Nori-30M</td><td>Default</td><td align="right">1,156</td><td align="right">—</td><td align="right">1,753</td><td align="right">0.53 / 0.080</td></tr>
  </tbody>
</table>

Elo scores are reported for the same configuration shown in the `Configuration` column. Cost is the median training and prediction time per 1,000 samples from the overall TabArena results; lower is better. Nori-30M has no classification result in the source data.

### ScoringBench

The results below are taken from the official [ScoringBench leaderboard](https://scoringbench.com/). The reported average ranks were computed against the full ScoringBench comparison pool of 51 model entries across 102 datasets. Figure 3 visualizes a selected set of 28 models, while Table 2 displays only the 10 model families that overlap with the TabArena table; neither the figure nor the table recomputes ranks on these subsets.

<div align="center">
  <img src="figures/scoringbench_r2_crps_site_style_tikz.svg" alt="ScoringBench R-squared and CRPS mean ranks" width="92%">
  <br>
  <em>Figure 3. Mean-rank comparison on ScoringBench across R² and CRPS; lower ranks are better.</em>
</div>

**Table 2.** *ScoringBench average ranks for models also included in the TabArena comparison. Lower is better.*

<table>
  <thead>
    <tr>
      <th bgcolor="#EEF2FF" align="left">Model</th>
      <th bgcolor="#EEF2FF" align="right">R² average rank ↓</th>
      <th bgcolor="#EEF2FF" align="right">CRPS average rank ↓</th>
    </tr>
  </thead>
  <tbody>
    <tr bgcolor="#F5F8FF" style="color:#1E3A8A; font-weight:700;"><td style="color:#1E3A8A;"><font color="#1E3A8A"><strong>EXAONE Tabular</strong></font></td><td align="right" style="color:#1E3A8A;"><font color="#1E3A8A"><strong>8.75</strong></font></td><td align="right" style="color:#1E3A8A;"><font color="#1E3A8A"><strong>6.07</strong></font></td></tr>
    <tr><td>TabPFN-3</td><td align="right">10.03</td><td align="right">6.16</td></tr>
    <tr><td>Nori-30M</td><td align="right">14.90</td><td align="right">11.59</td></tr>
    <tr><td>TabICLv2</td><td align="right">15.99</td><td align="right">11.88</td></tr>
    <tr><td>TabPFN-2.6</td><td align="right">16.87</td><td align="right">18.89</td></tr>
    <tr><td>RealTabPFN-2.5</td><td align="right">20.70</td><td align="right">19.96</td></tr>
    <tr><td>CatBoost</td><td align="right">33.52</td><td align="right">34.62</td></tr>
    <tr><td>TabM</td><td align="right">35.95</td><td align="right">33.79</td></tr>
    <tr><td>RealMLP</td><td align="right">36.14</td><td align="right">34.05</td></tr>
    <tr><td>XGBoost</td><td align="right">38.83</td><td align="right">38.76</td></tr>
  </tbody>
</table>

The benchmark-specific ScoringBench entries for RealTabPFN-2.5, CatBoost, TabM, RealMLP, and XGBoost are `tabpfn_realv2_5`, `catboost_quantile`, `tabm_d`, `pytabkit_realmlp_td`, and `xgb_vector`, respectively. Models are matched across the two benchmarks by model family, so their configurations may differ: for example, Table 1 reports the tuned-and-ensembled RealTabPFN-2.5, whereas Table 2 uses the `tabpfn_realv2_5` entry evaluated by ScoringBench.


## Requirements

- **Python** ≥ 3.11
- **PyTorch** ≥ 2.6, < 3 &nbsp;(a **CUDA GPU is strongly recommended** — the model uses fused
  attention kernels and half precision; CPU inference works but is slow)
- NumPy ≥ 2.3.5 · scikit-learn ≥ 1.7.2 · safetensors ≥ 0.4 · huggingface_hub ≥ 0.24
  &nbsp;(floors are the versions this release was validated against)

Install the package — the dependencies above come with it:

```bash
pip install "exaonetabular @ git+https://github.com/LGAI-Research/EXAONE-Tabular.git"
```

From a checkout, `pip install .` (add `-e` for an editable install) or `uv sync` do the same.

`huggingface_hub` is included, so `from_pretrained` can fetch the released weights out of the box.
Downloads honor the standard Hub environment (`HF_HOME` for the cache, `HF_TOKEN` for a gated repo).

Verify the install:

```python
import exaonetabular
print(exaonetabular.__version__)
```

> Dependency ranges are declared in
> [`pyproject.toml`](https://github.com/LGAI-Research/EXAONE-Tabular/blob/main/pyproject.toml)
> (distribution name `exaonetabular`).


## Quickstart

EXAONE Tabular ships as **scikit-learn-style estimators**. `EXAONETabularClassifier` and
`EXAONETabularRegressor` both expose the familiar `fit` / `predict` surface, return `self` from
`fit`, and set the usual fitted attributes — `classes_`, `n_classes_` and `n_features_in_` on the
classifier, `n_features_in_` on the regressor — so they slot into the workflow you already use,
including as the final step of a `sklearn.pipeline.Pipeline`. `predict_proba` is classification
only; the regressor returns point estimates from `predict`.

`from_pretrained` handles the rest in one call: it fetches that task's released checkpoint from the
Hub, builds the model from its frozen manifest, and loads the weights. The repo id, revision, and
architecture are baked into the package for both tasks, so there is nothing to configure by hand.

Both snippets below run as written, on a stock scikit-learn dataset.

> **Inputs are NumPy arrays.** `X` is 2-D `float` (rows × features); `y` is 1-D — class labels for
> classification, real values for regression. Anything else raises
> `TypeError: features must be a NumPy array`.

> **scikit-learn interop.** These estimators implement the estimator *interface* — including
> `__sklearn_is_fitted__` and `__sklearn_tags__`, so `check_is_fitted`, `is_classifier` /
> `is_regressor`, and use as the final step of a `Pipeline` all work. They do not subclass
> `BaseEstimator`, so there is no `get_params` / `set_params` / `score`, and `clone`,
> `cross_val_score`, and `GridSearchCV` are therefore not supported.

<details open>
<summary><b>Classification</b></summary>

```python
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split

from exaonetabular import EXAONETabularClassifier

X_train, X_test, y_train, y_test = train_test_split(
    *load_breast_cancer(return_X_y=True), test_size=0.25, random_state=0
)

clf = EXAONETabularClassifier.from_pretrained(device="cuda:0")   # download + verify + load

clf.fit(X_train, y_train)              # no training — stores context + fits preprocessors
proba  = clf.predict_proba(X_test)     # (n_samples, n_classes)
labels = clf.predict(X_test)           # (n_samples,)
```

Datasets with more than the model's class capacity are handled automatically via **ECOC**;
tables wider than the feature limit are reduced by built-in
[**feature selection**](#feature-selection-wide-tables).
</details>

<details open>
<summary><b>Regression</b></summary>

```python
from sklearn.datasets import load_diabetes
from sklearn.model_selection import train_test_split

from exaonetabular import EXAONETabularRegressor

X_train, X_test, y_train, y_test = train_test_split(
    *load_diabetes(return_X_y=True), test_size=0.25, random_state=0
)

reg = EXAONETabularRegressor.from_pretrained(device="cuda:0")   # download + verify + load

reg.fit(X_train, y_train)          # y: (n,) real-valued, finite — fits ensemble weights
y_pred = reg.predict(X_test)       # (n_samples,) float64 point estimates
```

The head predicts a **999-quantile distribution** per row, which `predict` reduces to one number:
by default a **trimmed mean** — the trapezoidal average over the central 99.8% of the quantile
function, sorted first so crossed quantiles cannot flip the order. That targets the conditional
mean, which is what RMSE scores and what the median misses on skewed targets. To read the median
quantile instead, pass a `manifest=` whose `RegressionConfig` sets `point_estimate="median"`.

The ensemble members are then **weighted, not averaged**. `fit` holds out 20% of the support set,
predicts it from the rows that remain, and solves for non-negative member weights by least squares
(NNLS), rescaled to sum to one and blended 75/25 with the uniform `1/E`. Members whose preprocessing
rule suits your table earn more of the vote; non-negativity keeps the result a convex combination,
and the blend bounds how far a fit on a small split can stray from the uniform prior. This costs one
extra forward pass inside `fit` — `predict` stays single-pass.

The fit needs **2000 held-out rows** (`nnls_min_validation_rows`), so it engages from roughly 10k
support rows up; smaller tables log a warning and stay on the uniform mean, because a handful of
weights fitted against a few dozen rows is where the solve degenerates. Set
`RegressionConfig.member_weighting="uniform"` to switch it off entirely.

Targets are standardized against the fitted support set and the prediction is mapped back, so `y`
needs no scaling of your own — but it must be finite; `NaN`/`inf` targets raise.
Tables wider than **1024 columns** are narrowed by univariate `f_regression` (see
[Feature selection](#feature-selection-wide-tables)).
</details>

> **NaNs and categoricals.** `X` must be numeric — encode string/categorical columns to numeric
> codes before `fit` (e.g. a stable ordinal map), leaving unseen/missing values as `NaN`. The
> built-in preprocessor mean-imputes `NaN`s; it does not encode raw strings.

### Overrides

`from_pretrained` accepts optional overrides without leaving the one-call path:

```python
clf = EXAONETabularClassifier.from_pretrained(
    device="cuda:0",
    compute_dtype="bfloat16",  # wider exponent range (default: "float16")
    ensemble_count=8, seed=0,  # runtime knobs
    revision="main",           # pin a specific Hub revision (tag or commit sha)
    max_vram_bytes=24 << 30,   # cap the GPU memory budget (see Out-of-memory below)
)

# Load your own weights of the same architecture — a local file or a Hub repo id.
# The released SHA-256 pin only applies to the released file, so it is not enforced
# here (a warning is logged); shapes, dtype, and finiteness are still validated.
clf = EXAONETabularClassifier.from_pretrained(weights="/path/to/my-classifier.safetensors")
```

You can also redirect the weights without touching code via the environment:
`EXAONETABULAR_CLASSIFIER_WEIGHTS` / `EXAONETABULAR_REGRESSOR_WEIGHTS` (a local path or a repo id).

> **Precision.** The released weights are stored in **float32**. With the default
> `compute_dtype="float16"` they are cast to fp16 at load — the tested runtime path. fp16 is the
> default because it is the more precise of the two half formats at the same footprint and
> throughput — 10 mantissa bits to bf16's 7 — and this model's activations stay far from fp16's
> 65504 ceiling, so bf16's wider exponent range buys nothing here. The two score the same in our
> classification benchmarking; prefer `compute_dtype="bfloat16"` only if your inputs can
> drive activations to that ceiling. `compute_dtype="float32"` is a **CPU-only** path: part of
> the attention stack is pinned to the FlashAttention kernel, which implements fp16 and bf16
> only, so a float32 forward on a CUDA device fails with `RuntimeError: No available kernel`.

<details>
<summary><b>Advanced: fully custom checkpoint (explicit manifest)</b></summary>

`from_pretrained` is a thin layer over the low-level API. For a checkpoint with a **different
architecture**, describe it with an `InferenceManifest` and load it explicitly — this is the same
API the released presets are built from:

```python
from huggingface_hub import hf_hub_download
from exaonetabular import (
    EXAONETabularClassifier,
    InferenceManifest,
    ModelConfig,
    RuntimeConfig,
    load_classifier_checkpoint,
)

CKPT = hf_hub_download("your-org/your-repo", "your-classifier.safetensors")
manifest = InferenceManifest(
    task="classification",
    model=ModelConfig(class_capacity=10),       # must match the checkpoint's class-head width
    runtime=RuntimeConfig(ensemble_count=8, compute_dtype="float16", seed=0),
)

clf = EXAONETabularClassifier(manifest, device="cuda:0")   # builds the model
load_classifier_checkpoint(CKPT, clf.model, manifest)      # validates + loads weights
```

A classification manifest carries a `ClassificationConfig` too. Leaving it off, as above, fills in
the defaults; `n_svd=0` therefore leaves support-SVD augmentation disabled. To opt in, import
`ClassificationConfig` and pass `classification=ClassificationConfig(n_svd=8)` to the manifest.
This changes inference preprocessing only and does not require different checkpoint weights.

Regression is analogous with `EXAONETabularRegressor`, `load_regressor_checkpoint`, and a
`RegressionConfig`. Two of its fields describe the checkpoint and must match it —
`quantile_count=999` and `decoder_hidden_width=384` — while `point_estimate`, the `n_svd`/`svd_*`
fields, and the `member_weighting`/`nnls_*` fields are readout and ensembling choices you can
change without touching the weights.

The frozen manifests the released estimators use live in `presets.py` and are reachable via
`released_manifest("classification" | "regression")`.
</details>


### Feature selection (wide tables)

The classifier accepts tables of any width, but the model itself reads at most **100 columns**. When
`fit` receives a wider table, it chooses which columns to keep using the model's own attention —
there is no flag, and nothing to configure:

```python
clf = EXAONETabularClassifier.from_pretrained(device="cuda:0")
clf.fit(X_train, y_train)          # X_train: (n, 5000) — selection runs here

clf.n_features_in_                 # 5000 — the public width does not change
clf.selected_feature_indices_      # (100,) int64, the columns actually kept
clf.predict_proba(X_test)          # still takes all 5000 columns
```

**How it works.** One forward pass over a ≤512-row sample of the fitted table, with the
feature-attention blocks instrumented. Two signals are read per column — attention from the target
row, and the summed attention from the item-summary rows — each weighted by the value-vector norm so
the score reflects information actually routed through the attention path rather than raw attention
probability. The two are min-max normalized, averaged, and the top 100 columns are kept.

**What to expect.**

- Narrow tables (`n_features ≤ 100`) skip this entirely — the pass does not run.
- Selection is **internal**. `n_features_in_`, `predict`, and `predict_proba` all keep the original
  width; the fitted column subset is reapplied for you.
- It costs one extra forward pass per `fit` on a wide table. A GPU is strongly recommended, and in
  this version there is **no way to disable it**.
- Classification only — see below for the regressor.

The configuration is frozen in `config.py` as `FEATURE_SELECTION`. It belongs to the
architecture rather than to any one checkpoint — the scorers name the model's token layout, so
the same settings apply to every classifier checkpoint of this architecture.

**Optional support-SVD augmentation.** By default, the classifier does not append support-SVD
components (`ClassificationConfig.n_svd=0`). Set `n_svd` to a positive integer—for example,
`n_svd=8`—to append that many components to every ensemble member's features, with each member
projecting onto its own basis. Once enabled, this augmentation is unconditional: unlike the
regressor, classification has no small-table exemption or un-augmented comparison arm because
probability aggregation averages members rather than fitting member weights.

**The regressor narrows differently.** `EXAONETabularRegressor` reads up to **1024 columns** and
trims anything wider with univariate `f_regression` — an F-test against the target, so it costs no
extra forward pass and uses no attention. It then appends **16 support-SVD components** to every
ensemble member's features (`RegressionConfig.n_svd`), each member projecting onto its own basis,
so the model sees the kept columns plus that augmentation.

Two knobs control when that augmentation applies, both settled once in `fit` against the whole
support:

- **`svd_gate`** (default `False`) withholds it from small, narrow, all-numeric tables — fewer than
  1000 rows *and* fewer than 10 columns *and* no categorical column — where a near-full-rank SVD
  only restates the input. Off by default because the split below already prices the augmentation by
  weight; set `True` to make the exemption an all-or-nothing decision instead.
- **`svd_split`** (default `True`) runs **two** ensembles instead of one, an un-augmented pass and
  an augmented pass, and pools their members into a single prediction so the weight fit decides how
  much the augmentation is worth rather than the gate deciding all-or-nothing. It doubles both the
  member count and the **forwards, at predict as well as fit**. Both passes share the run's seed, so
  a member differs across them only by the augmentation. With nothing to contrast against — exempted
  by the gate, or `n_svd=0` — a split run collapses back to the single pass.

### Controlling the GPU memory budget

Before running, the estimator measures the GPU, plans one execution strategy that
fits a memory **budget** (how many ensemble members run at once, how query rows
and feed-forward tokens are chunked, whether the support cache is offloaded), and
executes that plan. `max_vram_bytes` sets the budget explicitly:

```python
clf = EXAONETabularClassifier.from_pretrained(device="cuda:0", max_vram_bytes=24 << 30)
```

It is a **hard cap**, in bytes, and CUDA-only: the planner both *prefers* to stay
under it and treats it as the *feasibility* limit, so it will chunk more
aggressively to fit and will refuse — rather than quietly exceed it — a forward
whose smallest possible plan does not. Left unset, the budget is everything your
process can address: total VRAM minus what other processes already hold.

**To spend a proportion of the GPU, compute the bytes yourself** — there is no
separate fraction argument, because the proportion is only meaningful once you
choose what it is a proportion *of*:

```python
import torch

free, total = torch.cuda.mem_get_info(0)   # free = unused now, total = card capacity
clf = EXAONETabularClassifier.from_pretrained(
    device="cuda:0",
    max_vram_bytes=int(0.7 * free),    # 70% of what is actually free right now
)
```

> **Pick the denominator deliberately.** `total` is the card's capacity; `free` is
> what is unused at that moment. On a shared GPU a fraction of `total` can exceed
> what your process is able to obtain, which plans a forward that cannot run — use
> `free` unless you own the whole device. Note also that the planner already keeps
> a ~10% safety margin against the budget on the memory-heaviest build phases, so
> a budget of *B* is planned to roughly *0.9B*; there is no need to discount twice.

### Out-of-memory and memory fragmentation

Large support sets on a memory-constrained GPU can trigger a CUDA out-of-memory
error. **The error is raised to you unchanged.** Inference plans once and runs
that plan; it does not catch the OOM, shrink the budget, and silently retry.
Recovering costs GPU time and is a policy decision — retry smaller, fall back to
CPU, fail the request — so it belongs to the caller:

```python
try:
    proba = clf.predict_proba(X)
except torch.cuda.OutOfMemoryError:
    # Your policy: e.g. re-fit with a lower max_vram_bytes or ensemble_count.
    ...
```

Before concluding the model does not fit, check whether the failure is
**external fragmentation** rather than a true capacity limit. In the CUDA error,
compare the amount it *tried to allocate* against the `reserved but unallocated`
figure: when a large amount is reserved-but-unallocated yet a much smaller
allocation fails, the data would fit but the caching allocator cannot place a
single contiguous block — that is fragmentation, not lack of memory.

For that case, run with PyTorch's expandable-segments allocator. It lets the
allocator grow and coalesce segments, which largely removes contiguous-block
fragmentation:

```bash
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True python your_script.py
```

> It is a **process-global** setting and must be present in the environment
> **before** CUDA initializes — set it when launching the process, not from inside
> Python after torch has already allocated. It changes only the allocator; results
> are unaffected.

If it still OOMs with expandable segments, the working set genuinely exceeds VRAM.
Reduce the footprint instead, roughly in order of cost to accuracy:

1. **Lower `max_vram_bytes`.** A smaller budget makes the planner chunk harder:
   slower, but the same computation — chunking splits batch dimensions and does
   not change the model. Chunked and unchunked results agree to numerical
   tolerance rather than bit-for-bit, which is visible only in reduced precision.
2. **Lower `ensemble_count`** (a `from_pretrained` override) — fewer ensemble
   members is directly less work and less memory, at some accuracy cost.
3. **Shrink the in-context support set** via the low-level
   `RuntimeConfig(support_row_limit=…)` manifest path. This is the only lever on
   the memory floor that grows with support rows, and the most costly to accuracy.
4. **Use a larger GPU.**


## Available checkpoints

| File | Task | Head | Dtype | Notes |
|---|---|---|---|---|
| `exaone-tabular-classifier-v1_default.safetensors` | Classification | 10-class | float32 | `> class_capacity` classes handled automatically via ECOC |
| `exaone-tabular-regressor-v1_default.safetensors`  | Regression    | 999 quantiles | float32 | Read out as a trimmed mean over the quantiles; needs a `RegressionConfig` in its manifest |

Both live in the same Hub repository, and each estimator's `from_pretrained()` fetches its own file
— there is no shared dual-head checkpoint, and a classifier file will not load into the regressor.

Each checkpoint's architecture is **frozen** and must match its `InferenceManifest`; a mismatched
file (wrong keys, shapes, or dtype) fails loudly at load — never silently. The regression loader is
stricter still: the file must carry a `quantile_levels` buffer in float32 that equals
`linspace(1/1000, 999/1000, 999)` exactly, so a head of a different width or spacing is rejected
rather than silently reinterpreted.

`InferenceManifest.checkpoint_sha256` can additionally pin one exact file. The released manifests in
`presets.py` leave it `None`, so **every load — both tasks — logs a warning** saying the bytes were
not integrity-checked; the structural validation above still runs. Set it to pin one exact byte
stream, and a checkpoint whose digest differs is rejected.


## Intended use

EXAONE Tabular is intended for **supervised tabular** classification and regression on structured
(row/column) data, for datasets within the tested sample/feature envelope. High-dimensional inputs
are handled by built-in [feature selection](#feature-selection-wide-tables); large support sets are
subsampled. Use of the released weights is limited to
**non-commercial research and educational** purposes by the EXAONE model license.

**Not intended for:** unstructured data (images, raw text, audio, video); inputs substantially
beyond the tested envelope, where accuracy and runtime are not guaranteed; any **commercial** use
of the released weights, or any use excluded by the [license](#license).


## Limitation

**Class-Count Handling**. 
The native classification head supports up to 10 classes. Datasets with larger label
spaces are handled through an ECOC-based decomposition at inference time. This procedure requires
multiple binary predictions and therefore increases inference cost as the number of classes grows. A class-
count-independent prediction head is a potential direction for future work.

**Large-Context Inference**. 
Query chunking controls peak query-side memory because query predictions
are conditionally independent given the support set. However, the current inference wrapper recomputes
the support representations for each estimator and query chunk, introducing redundant computation when
either the ensemble size or the number of query chunks is large. The model already provides a support-side
caching path for row-axis attention, but this path is not yet used by the default chunked-inference wrapper.
Activating support-representation caching could reduce repeated computation across query chunks.
Support sets beyond the configured inference limit are currently subsampled. Potential future directions
include support-side representation and KV caching, context compression, representative-context selec-
tion, clustering-based support reduction, retrieval-based context construction, memory-efficient attention,
and adaptive support-set sampling. These methods require systematic evaluation of the trade-offs among
inference latency, memory consumption, support compression, and predictive performance.


## License

Two licenses apply, to two different things:

- **The code in this repository** — the `exaonetabular` inference runtime — is released under the
  [BSD-3-Clause-LG AI Research License](https://github.com/LGAI-Research/EXAONE-Tabular/blob/main/LICENSE), which permits commercial use.
- **The released model weights** are licensed separately under the **EXAONE AI Model License
  Agreement 1.2 - NC**, which limits use to non-commercial research and education. The full terms
  ship with the weights on the [Hugging Face repository](https://huggingface.co/LG-AI-Research/EXAONE-Tabular).

Installing this package therefore does not grant commercial rights to the weights it downloads.


## Citation

If you find EXAONE Tabular useful in your research, please cite our technical report:

```bibtex
@article{eo2026exaonetabular,
  title         = {EXAONE Tabular 1.0: Technical Report},
  author        = {Eo, Moonjung and Suh, Min-Kook and Cho, Hye-Seung and Kim, Jiwon and Kim, Seoyoon and Nam, Sangjun and Lee, Soonyoung},
  year          = {2026},
  eprint        = {2608.25774},
  archivePrefix = {arXiv},
  primaryClass  = {cs.LG}
}
```

## Contact

LG AI Research Technical Support: contact_us@lgresearch.ai
