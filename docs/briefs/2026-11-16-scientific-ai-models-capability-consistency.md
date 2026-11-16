# Capability consistency in scientific_ai_models, 2026-11-16

This brief audits the four capability attributes across all 34 products in `scientific_ai_models`
against rulings (a) to (f) in the recipe note (`sources/categories/scientific_ai_models.yaml`,
`scoring_recipe.capability`) and R-2026-11-16-a (`docs/rulings/log.yaml`, applied in #1077). It
changes no score, value, note, comparison, hold or recipe text. Every proposal below is for the
maintainer to rule on. Like the other records in `docs/briefs/`, it describes the state on the date
above and gets refreshed by a new brief, not edited.

The evidence is what the category already holds: the capability blocks on `main` at `bf66c237`, the
bodies saved for the #1076 refresh and the #1077 rulings, and nine additional fetches listed under
[Sources](#sources). Every quote attributed to a recorded source was checked against the saved body
whose sha256 equals the record's `content_sha256`. The full matrix, with the source URL, verbatim
quote and digest for each of the 136 attribute cells, is the sibling file
`docs/briefs/2026-11-16-scientific-ai-models-capability-consistency.json`.

## The short answer

Six credits do not hold up against the rules the category already applies to their peers. Four are
`multi_scale` and two are `generative`:

| Product | Attribute | Recorded | Proposed | Why |
|---|---|---|---|---|
| terramind | multi_scale | 5 | 4 | Pixel- and token-level processing is internal representation. Every modality enters co-registered at 10 m. |
| prithvi-eo | multi_scale | 4 | 3 | The 0.1 m to 15 m span is a fine-tuned benchmark result. The model was pretrained only on 30 m data. |
| prithvi-wxc | multi_scale | 3 | 2 | Global versus regional coverage and a flexible lead time are extent, under (e). |
| pangu-weather | multi_scale | 2 | 1 | The four checkpoints differ only in lead time, and all four use one 0.25-degree grid. That is extent, under (e). |
| geneformer | generative | 3 | 2 | In silico perturbation outputs a shift in an embedding, which is a deterministic prediction under (d). |
| scgpt | generative | 4 | 3 | Its perturbation output is a deterministic expression profile from a model trained on mean squared error, which is prediction under (d). |

TerraMind's level 5 rests on one sentence in its model card: "simultaneously processing pixel-level and
token-level data". Its paper and its dataset card say all nine modalities are "co-registered at a 10-meter
resolution". Its authors list multi-resolution input as future work. That is the defect R-2026-11-16-a
removed from Surya: two internal representations of data sampled at one resolution. If TerraMind drops to
4, the category has no level 5.

The rubric separates sampling resolution from architecture case by case (Surya, AlphaGenome, Clay), but
it does not say so as a rule. This brief proposes one clarification, a ruling (g) for `multi_scale`, under
[Proposed ruling (g)](#proposed-ruling-g). It also states plainly the one choice it forces: whether a
resolution that a model meets only in a transfer test or after fine-tuning counts as scale. Read either
way, the four ruling (d) and (e) corrections stand.

If all six proposals land, the distribution moves from 2/10/16/5/1 to 3/11/16/4/0 across levels 1 to 5
(9/32/47/12/0 percent). 21 of the 23 recorded comparison edges would then need their relation rewritten.
Every one is enumerated below.

## The matrix

`Y` and `N` are what the record credits. A letter after a cell marks a finding:

- **x**: inconsistent with a ruling or with a peer's treatment (a proposal below).
- **g**: the credit holds, but the cited quote does not itself show it.
- **r**: the outcome holds, but the record's stated reason contradicts a ruling.
- **o**: open, left to an existing hold.

Unmarked cells are consistent. The JSON carries the quote behind every cell.

| Product | Score | Edge | adaptation | multi_instrument | generative | multi_scale |
|---|---|---|---|---|---|---|
| terramind | 5 | (top anchor) | Y | Y | Y | Y **x** |
| prithvi-eo | 4 | one_below terramind | Y | Y | N | Y **x** |
| clay | 4 | at prithvi-eo | Y | Y | N | Y |
| weathernext | 4 | one_below terramind | Y | N | Y | Y |
| nasa-ibm-lunar-foundation-model | 4 | at prithvi-eo | Y | Y | N | Y |
| scgpt | 4 | none | Y | Y | Y **x** | N |
| aurora-weather | 3 | two_below terramind | Y | N | N **o** | Y |
| prithvi-wxc | 3 | two_below terramind | Y | N | N | Y **x** |
| surya-heliophysics | 3 | two_below terramind | Y | Y | N | N |
| evo-2 | 3 | two_below terramind | Y | N | Y | N |
| climax | 3 | two_below terramind | Y | N | N | Y |
| neuralgcm | 3 | two_below terramind | N | N | Y | Y |
| alphagenome | 3 | one_below prithvi-eo | N | Y | N | Y |
| mattergen | 3 | one_below prithvi-eo | Y | N | Y | N |
| dofa | 3 | one_below prithvi-eo | Y | Y | N | N **r** |
| presto | 3 | one_below prithvi-eo | Y | Y | N | N |
| esm-3 | 3 | one_below prithvi-eo | N | Y | Y | N |
| openfold | 3 | one_below prithvi-eo | Y | Y | N | N |
| boltz | 3 | one_below prithvi-eo | Y | Y | N | N |
| geneformer | 3 | none | Y | N | Y **x** | N |
| uma | 3 | none | Y | Y | N | N |
| mace | 3 | none | Y | Y | N | N |
| esm-2 | 2 | two_below prithvi-eo | Y | N | N | N |
| granite-geospatial | 2 | two_below prithvi-eo | Y **g** | N | N | N |
| alphaearth-foundations | 2 | two_below prithvi-eo | N | Y | N | N |
| alphafold | 2 | two_below prithvi-eo | N | Y | N | N |
| chai | 2 | two_below prithvi-eo | N | Y | N | N |
| rfdiffusion | 2 | two_below prithvi-eo | N | N | Y | N |
| aifs | 2 | none | Y | N | N | N |
| pangu-weather | 2 | none | N | N | N | Y **x** |
| mattersim | 2 | none | Y **g** | N | N | N |
| orb | 2 | none | Y | N | N | N |
| uce | 1 | none | N | N | N | N |
| gnome | 1 | none | N | N | N | N |

Every recorded score equals one plus its count of credited attributes. The arithmetic is sound. The
findings are about which attributes are credited.

## Priority questions

### TerraMind: is the multi_scale credit a sampling resolution?

No. The credit rests on the architecture sentence. The record's own source, the TerraMind-1.0-large
model card ([HF card](https://huggingface.co/ibm-esa-geospatial/TerraMind-1.0-large/raw/main/README.md),
`1fac187c…d9d7`), says: "TerraMind uses a dual-scale transformer-based encoder-decoder architecture,
simultaneously processing pixel-level and token-level data." The paper's abstract
([arXiv 2504.11171](https://arxiv.org/abs/2504.11171), `e5a21686…8704`) describes what the two scales
are: "TerraMind is pretrained on dual-scale representations combining both token-level and pixel-level
data across modalities." Those are two representations of the same input, not two sampling resolutions.

The documentation shows one input resolution:

- TerraMesh, the pretraining dataset
  ([dataset card](https://huggingface.co/datasets/ibm-esa-geospatial/TerraMesh/raw/main/README.md),
  `e3b3cc93…ceea`): "TerraMesh fuses complementary optical, radar, topographic and thematic layers into
  pixel‑aligned 10 m cubes".
- The paper ([arXiv HTML](https://arxiv.org/html/2504.11171), `7babd2fe…a0ba0`): "Each modality is
  precisely co-registered at a 10-meter resolution, primarily based on Sentinel-2 grids." The one source
  with a different native resolution is resampled onto that grid: "DEM is extracted from the Copernicus
  DEM 30m dataset".
- The authors list multi-resolution input as future work (same body): "we expect that TerraMind-like
  models will expand to multi-temporal, multi-resolution, and hyperspectral data".
- The NASA-IBM lunar model, which credits `multi_scale`, describes its own multi-resolution training as an
  addition to TerraMind's recipe
  ([lunar card](https://huggingface.co/nasa-ibm-ai4science/NASA-IBM-Lunar-Foundation-Model/raw/main/README.md),
  `8b19ff32…dae6`): it "adapts the [TerraMind] masked-token recipe to the Moon with two extensions", the
  second being that "NAC- and WAC-anchored tiles train in a single mixed-batch loop at native resolution".

One piece of evidence points the other way, and the proposal has to answer it. In a few-shot test, the
frozen checkpoint classifies 1 m NAIP imagery (arXiv HTML, `7babd2fe…a0ba0`): "In those experiments, there
are no weight updates of any kind", and TerraMind "generalizes to high-resolution NAIP data with one order
of magnitude higher resolution than the pre-training data". That is one checkpoint run on inputs at two
ground sampling distances. It is a transfer test of a model built for 10 m input, though. The NAIP input is
not part of the model's specification, and nothing tells the model the resolution. How this test counts is
the one choice [ruling (g)](#proposed-ruling-g) has to make. The brief's recommendation is that it is not
scale, for the reason given there. If the maintainer decides it does count, TerraMind keeps its 5, and
Prithvi-EO and DOFA have to be read the same way ([Alternative reading](#the-alternative-reading)).

**Every edge that points at TerraMind.** Eight point at it directly and fifteen through Prithvi-EO, which
is `one_below terramind`. The columns show how each edge would read if only TerraMind moved to 4, and if
TerraMind and Prithvi-EO moved together (4 and 3), as proposed. "Holds" means the recorded relation is still
arithmetically true. Otherwise the cell gives the relation the arithmetic would need.

| Edge (recorded) | Scores now | TerraMind to 4 only | TerraMind 4, Prithvi-EO 3 |
|---|---|---|---|
| prithvi-eo one_below terramind | 4 / 5 | breaks: at | holds |
| weathernext one_below terramind | 4 / 5 | breaks: at | breaks: at |
| aurora-weather two_below terramind | 3 / 5 | breaks: one_below | breaks: one_below |
| prithvi-wxc two_below terramind | 3 / 5 | breaks: one_below | breaks: one_below (holds if prithvi-wxc also goes to 2) |
| surya-heliophysics two_below terramind | 3 / 5 | breaks: one_below | breaks: one_below |
| evo-2 two_below terramind | 3 / 5 | breaks: one_below | breaks: one_below |
| climax two_below terramind | 3 / 5 | breaks: one_below | breaks: one_below |
| neuralgcm two_below terramind | 3 / 5 | breaks: one_below | breaks: one_below |
| clay at prithvi-eo | 4 / 4 | holds | breaks: one_above (or at terramind) |
| nasa-ibm-lunar-foundation-model at prithvi-eo | 4 / 4 | holds | breaks: one_above (or at terramind) |
| alphagenome one_below prithvi-eo | 3 / 4 | holds | breaks: at |
| mattergen one_below prithvi-eo | 3 / 4 | holds | breaks: at |
| dofa one_below prithvi-eo | 3 / 4 | holds | breaks: at |
| presto one_below prithvi-eo | 3 / 4 | holds | breaks: at |
| esm-3 one_below prithvi-eo | 3 / 4 | holds | breaks: at |
| openfold one_below prithvi-eo | 3 / 4 | holds | breaks: at |
| boltz one_below prithvi-eo | 3 / 4 | holds | breaks: at |
| esm-2 two_below prithvi-eo | 2 / 4 | holds | breaks: one_below |
| granite-geospatial two_below prithvi-eo | 2 / 4 | holds | breaks: one_below |
| alphaearth-foundations two_below prithvi-eo | 2 / 4 | holds | breaks: one_below |
| alphafold two_below prithvi-eo | 2 / 4 | holds | breaks: one_below |
| chai two_below prithvi-eo | 2 / 4 | holds | breaks: one_below |
| rfdiffusion two_below prithvi-eo | 2 / 4 | holds | breaks: one_below |

Moving TerraMind alone breaks 8 edges. Moving it together with Prithvi-EO breaks 22, and with all six
proposals 21, because prithvi-wxc's `two_below terramind` holds again at 2 / 4. No product would sit at 5,
so the recipe note's "TerraMind is now the only 5", "TerraMind is the top anchor" and "All five rungs stay
occupied" would all need rewriting with the scores. No edge is changed here.

### Prithvi WxC: are regional/global coverage and flexible horizons extent?

Yes, both are. The record's source
([README](https://raw.githubusercontent.com/NASA-IMPACT/Prithvi-WxC/main/README.md), `189a67cd…5713`)
says "the masking pattern makes it suitable for both global and regional applications". A regional run
covers a window of the same MERRA-2 grid, which is spatial extent. The model card
([HF card](https://huggingface.co/ibm-nasa-geospatial/Prithvi-WxC-1.0-2300M/raw/main/README.md),
`9eb19787…ae459`, from the #1076 packet) says "The time delta between input timestamps is variable as is
the forecast lead time", and "the forecast lead time was chosen from [0, 6, 12, 24] hours". A lead time is
how far ahead the forecast reaches. Rule (e) calls that extent, and Surya's 2-to-12-hour horizons are not
credited. The variable gap between the two input timestamps is the length of a two-sample input window,
which is also extent. The README's other scale language, "We alternate between **local attention** (within
a window) and **global attention** (across windows).", is the architecture R-2026-11-16-a set aside for
Surya.

One fact could support the credit on other grounds, and it is not cited in the record. The card says Prithvi
WxC "has been fine-tuned for several tasks including climate downscaling (released as part of the
enterprise-grade [IBM granite](https://huggingface.co/ibm-granite) family of models)". A downscaling model
emits a finer grid than it takes in. That model is a separately named fine-tuned derivative, though, not a
checkpoint in Prithvi WxC's own release. Under the proposed ruling (g), it is adaptation. Proposal: 3 to 2.

### DOFA, Presto, AlphaEarth Foundations: one checkpoint across sampling resolutions, or one grid?

**The Clay standard.** R-2026-11-16-a credits Clay "for input across the documented sensor resolutions".
The specification that ruling rests on
([Clay spec](https://clay-foundation.github.io/model/release-notes/specification.html), `192ffac7…6e891`)
says the model takes each sensor at its own resolution and is told what that resolution is: "During
pre-training, the model processes stacks of chips from different sensors along with metadata such as
wavelengths, GSD, latitude/longitude, and time step", with position encoding "scaled according to the Ground
Sampling Distance (GSD)". So sensors that merely have different native resolutions are not enough. One
checkpoint has to take each input at its own ground sampling distance, with that distance carried into the
model. The lunar model meets the same standard another way: it trains NAC and WAC tiles "at native
resolution", and "per-tile illumination angles, solar-frame anchors, and tile footprint are
sequence-tokenized encoder inputs" (lunar card, `8b19ff32…dae6`).

- **DOFA.** Not credited, and that is consistent with the standard, though the record gives the wrong
  reason. The checkpoint does train across sensors at different resolutions
  ([arXiv HTML 2403.15356](https://arxiv.org/html/2403.15356), `857467b0…c2b4`): "DOFA is pretrained on a
  large-scale multimodal EO dataset comprising approximately 11.5 million images from five different
  modalities: Sentinel-1, Sentinel-2, NAIP, Gaofen, and EnMAP." Its conclusion calls the models "designed
  to operate flexibly across a wide range of sensors, spectral bands, and spatial resolutions". But the only
  input metadata is wavelength (section "3.3 Wavelength-conditioned dynamic patch embedding"), and "All
  images are resized to 224 × 224 and normalized using modality-specific statistics". No ground sampling
  distance or footprint reaches the model. The record says instead that "that same sensor diversity is not
  counted a second time as multiple scales". That reason contradicts R-2026-11-16-a, because Clay and the
  lunar model are credited for both `multi_instrument` and `multi_scale` from the same sensors. The score
  is unchanged, and the note's reason should change at the next refresh. DOFA is the closest call in the
  category. Under the [alternative reading](#the-alternative-reading), it rises to 4.
- **Presto.** Not credited, and that is consistent. Each instance is one pixel's band vector
  ([README](https://raw.githubusercontent.com/nasaharvest/presto/main/README.md), `b023f4f2…6836`: "of shape
  `[batch_size, num_timesteps, bands]`"). Sentinel-1, Sentinel-2, ERA5 and SRTM rasters are flattened onto
  one grid before they enter
  ([pipeline](https://raw.githubusercontent.com/nasaharvest/presto/main/presto/dataops/pipelines/s1_s2_era5_srtm.py),
  `7f371255…aaf4`: "x_np, lat_lon_np = resample_and_flatten_tif(tif)"). The 1-to-24 monthly timesteps are
  extent under (e).
- **AlphaEarth Foundations.** Not credited, and that is consistent. The paper
  ([arXiv HTML 2507.22291](https://arxiv.org/html/2507.22291), `6cc8998c…9b24`) says the model accepts
  sources "with C_{i} channels resampled to the same spatial resolution", and "We reproject all raster data
  to Universal Transverse Mercator (UTM) coordinates followed by spatial resampling to 10 m resolution using
  bilinear interpolation." The released product is that one grid
  ([STAC record](https://storage.googleapis.com/earthengine-stac/catalog/GOOGLE/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL.json),
  `1c5fb2ab…e012`): "Each 10-meter pixel in this dataset is a 64-dimensional representation". Its internal
  spatial pyramid is architecture.

### Geneformer and scGPT: generation or prediction under ruling (d)?

Both are prediction.

- **Geneformer.** The credit cites in silico reprogramming and perturbation from the model card
  ([HF card](https://huggingface.co/ctheodoris/Geneformer/raw/main/README.md), `56d6e570…dbd8`), which
  describes a model pretrained "to enable context-aware predictions". The tool that performs perturbation
  ([API docs](https://geneformer.readthedocs.io/en/latest/geneformer.in_silico_perturber.html),
  `71264b6c…f8a3`) "Performs in silico perturbation (e.g. deletion or overexpression) of defined set of
  genes or all genes in sample of cells" and "Outputs impact of perturbation on cell or gene embeddings."
  The output is a deterministic shift in an embedding. It is not a generated cell, expression profile or
  distribution. Proposal: `generative` N, 3 to 2.
- **scGPT.** The credited notebook
  ([Tutorial_Perturbation.ipynb](https://raw.githubusercontent.com/bowang-lab/scGPT/main/tutorials/Tutorial_Perturbation.ipynb),
  `a997191d…bdbb`) trains with "criterion = masked_mse_loss". Its prediction function is documented as
  "Predict the gene expression values for the given perturbations." That is a deterministic
  post-perturbation state predicted from a control state, which is the cellular form of the forecast (d)
  excludes. The README still lists cell generation as unfinished
  ([README](https://raw.githubusercontent.com/bowang-lab/scGPT/main/README.md), `b0503e8c…6c83`): "- [ ]
  Finetuning examples for multi-omics integration, cell type annotation, perturbation prediction, cell
  generation". Generative pretraining is an objective, and the rubric note already excludes masked
  reconstruction. Proposal: `generative` N, 4 to 3.

### Granite Geospatial: does the adaptation pathway update weights?

Yes. The credit holds, but it is cited to the wrong quote. The record's only source quotes SimMIM
pretraining. The model card lists the notebook's experiments
([HF card](https://huggingface.co/ibm-granite/granite-geospatial-biomass/raw/main/README.md),
`c80890ea…8b00`), ending with "3. Few-shot for a single biome". The notebook itself
([agb_getting_started.ipynb](https://raw.githubusercontent.com/ibm-granite/granite-geospatial-biomass/main/notebooks/agb_getting_started.ipynb),
`2f7073e0…e04d`) runs a weight-updating fine-tune from the released Lightning checkpoint: "print(f'terratorch
fit --config {finetune_config_path} --ckpt_path {full_lightning_ckpt_path}')". The two zero-shot experiments
are inference only. The few-shot one is fine-tuning, and ruling (b) is met. The next refresh should cite the
notebook. The score is unchanged.

### Prithvi-EO and AlphaGenome: are input, output and evaluation resolutions treated alike?

Not yet. AlphaGenome is credited for one model emitting outputs at several documented sampling resolutions
([output metadata](https://google-deepmind-alphagenome.readthedocs-hosted.com/exploring_model_metadata.html),
`835a5f14…4c36`: tracks at "1 bp", ChIP-seq "summed per 128 bp bin", contact maps at "2048 bp"), and its
1 Mb input window is extent. That is the output-side counterpart of Clay's input-side credit. Both are
properties of the model's own specification. Surya is denied because its input is one native resolution
and its scales are attention ranges.

Prithvi-EO is credited for neither of these. The credited sentence
([README](https://raw.githubusercontent.com/NASA-IMPACT/Prithvi-EO-2.0/main/README.md), `f13bf62e…d616`)
is "It also outperforms six other geospatial foundation models when benchmarked on remote sensing tasks from
different domains and resolutions (i.e. from 0.1m to 15m)". The paper
([arXiv HTML 2412.02732](https://arxiv.org/html/2412.02732), `382607a8…b019`) explains how that span was
reached: "We added the GEO-Bench datasets to TerraTorch and used its companion library TerraTorch-iterate"
for per-dataset tuning, and "We highlight that all fine-tuning experiments conducted in this work require a
single GPU." It also says the input resolution is single: "Prithvi-EO-2.0 showed good performance on
high-resolution tasks, despite being pretrained only with 30 m data." So the checkpoint's own input is one
resolution, as Surya's is, and the other resolutions come from fine-tuning. DOFA appears in the same
GEO-Bench tables and is not credited. Prithvi-EO's credit is out of line with Clay, AlphaGenome, Surya and
DOFA together. Proposal: `multi_scale` N, 4 to 3.

## Genuine discrepancies and their downstream effects

Each entry gives the proposed score and relation, and every comparison that points at the product.
Relations are read with all six proposals applied. The JSON's `scenarios.primary_proposal` lists every edge.

1. **terramind: multi_scale, 5 to 4.** No relation of its own. Eight edges point at it directly, and their
   effects are in the table above. Under all six proposals, `prithvi-eo one_below` and
   `prithvi-wxc two_below` hold. `weathernext one_below` becomes `at`. `aurora-weather`, `surya-heliophysics`,
   `evo-2`, `climax` and `neuralgcm` `two_below` become `one_below`.
2. **prithvi-eo: multi_scale, 4 to 3.** `one_below terramind` holds. Fifteen edges point at it.
   `alphagenome`, `mattergen`, `dofa`, `presto`, `esm-3`, `openfold` and `boltz` move from `one_below` to
   `at`. `esm-2`, `granite-geospatial`, `alphaearth-foundations`, `alphafold`, `chai` and `rfdiffusion` move
   from `two_below` to `one_below`. `clay` and `nasa-ibm-lunar-foundation-model` move from `at` to
   `one_above`, or each could be re-pointed `at terramind`. Prithvi-EO is the hub for most of the category,
   so it may be simpler to re-anchor the graph on one of the remaining 4s than to rewrite fifteen relations
   around a 3. That is the maintainer's choice.
3. **prithvi-wxc: multi_scale, 3 to 2.** `two_below terramind` holds once TerraMind is 4 (2 / 4). If
   TerraMind stays at 5, the gap is three levels and has no relation, so the edge would need re-pointing,
   for example `two_below prithvi-eo` at 2 / 4. Nothing points at Prithvi WxC.
4. **pangu-weather: multi_scale, 2 to 1.** The four checkpoints are "The 1-hour model", "The 3-hour model",
   "The 6-hour model" and "The 24-hour model". Each takes and returns the same grid
   ([README](https://raw.githubusercontent.com/198808xc/Pangu-Weather/master/README.md), `b21aeee7…19a1`:
   "It is a numpy array shaped (4,721,1440)", "the spacing is 0.25 degrees"). The only difference is
   forecast horizon, which (e) treats as extent. No relation and nothing points at it, so no edges are
   affected.
5. **geneformer: generative, 3 to 2.** No relation and nothing points at it.
6. **scgpt: generative, 4 to 3.** No relation and nothing points at it.

## Proposed ruling (g)

The rubric separates sampling resolution from architecture one product at a time. Surya's attention scales
are excluded, AlphaGenome's output bins are included, and Clay's sensor GSDs are included. It has no
sentence that settles TerraMind's pixel and token streams or Prithvi-EO's fine-tuned benchmark span. The
proposed clarification for `multi_scale` applies to the whole category:

> (g) `multi_scale` reads the sampling resolution of the data a model is specified to take in or put out:
> ground sampling distance, grid spacing, bin width or cadence. It is met by one checkpoint whose input
> carries each sample's resolution, so data at more than one resolution enter at their own; by one
> checkpoint whose documented outputs come at more than one resolution; or by checkpoints at different
> resolutions in the product's own release, under (a). It is not met by how the model represents data
> internally (pixel- and token-level streams, local and global attention, patch, window or pyramid levels),
> by sources resampled to one grid before they enter, by coverage, window length or forecast lead time,
> which are extent under (e), or by a resolution the model meets only in a transfer test or after
> fine-tuning on a downstream dataset, which is adaptation and is counted there.

The last clause is the one with a choice in it. A patch-based image backbone can be run on, or fine-tuned
to, imagery at any resolution. If benchmark coverage earned `multi_scale`, every Earth-observation backbone
with GEO-Bench or PANGAEA results would earn it, whatever its input specification. The credit would then
measure documentation, not the model, which the category comment warns against. Fine-tuning onto new data
is also what `adaptation_pathway` already counts.

How (g) reads on each product it touches:

| Product | Reading under (g) | multi_scale | Score |
|---|---|---|---|
| clay | GSD carried into the model with each sensor | Y | 4, unchanged |
| nasa-ibm-lunar-foundation-model | NAC and WAC at native resolution, footprint as input | Y | 4, unchanged |
| alphagenome | outputs at 1, 128 and 2,048 bp from one model | Y | 3, unchanged |
| weathernext, neuralgcm, climax, aurora-weather | checkpoints at different grid spacings in the product's release | Y | unchanged |
| surya-heliophysics | attention ranges at one native resolution | N | 3, unchanged |
| terramind | pixel and token streams over 10 m inputs; the NAIP result is a transfer test | N | 5 to 4 |
| prithvi-eo | 30 m input; 0.1 m to 15 m reached by fine-tuning | N | 4 to 3 |
| prithvi-wxc | regional window and lead time are extent; downscaling is a separately released fine-tune | N | 3 to 2 |
| pangu-weather | lead time is extent; one grid | N | 2 to 1 |
| dofa | trained across sensor resolutions, but no resolution carried in; chips resized to 224 px | N | 3, unchanged (reason corrected) |
| presto, alphaearth-foundations, aifs | sources resampled to one grid | N | unchanged |
| evo-2 | context length is extent | N | 3, unchanged |

(g) names no product, and it was not tuned to keep or remove any score. It costs the category its only
level 5.

### The alternative reading

If the maintainer decides that a documented run at another resolution counts, transfer and fine-tuned
benchmarks included, the last clause of (g) is dropped. Each EO product then reads as follows:

- **terramind** keeps 5 on the zero-shot NAIP test.
- **prithvi-eo** keeps 4 on GEO-Bench.
- **dofa** rises from 3 to 4. The paper says DOFA and DOFA+ "employ a single set of model parameters across
  all tasks". They are evaluated on the high-resolution DIOR dataset and on Sentinel-1 and Sentinel-2
  "benchmarks that involve much lower-resolution imagery", and trained on five sensors at different native
  resolutions.

The other four proposals stand either way, because they rest on (d) and (e), not on (g). Distribution:
3/11/14/5/1 (9/32/41/15/3 percent). Two edges break. `dofa one_below prithvi-eo` becomes `at`.
`prithvi-wxc two_below terramind` becomes a three-level gap with no relation and needs re-pointing.

## Resulting distributions

| Scenario | 1 | 2 | 3 | 4 | 5 | Edges broken |
|---|---|---|---|---|---|---|
| Recorded | 2 (6%) | 10 (29%) | 16 (47%) | 5 (15%) | 1 (3%) | 0 |
| All six proposals, with (g) | 3 (9%) | 11 (32%) | 16 (47%) | 4 (12%) | 0 | 21 of 23 |
| Alternative reading (no transfer clause) | 3 (9%) | 11 (32%) | 14 (41%) | 5 (15%) | 1 (3%) | 2 of 23 |

## Considered, no change proposed

- **aurora-weather, generative (open).** The Hugging Face file list saved in the #1076 packet
  ([API](https://huggingface.co/api/models/microsoft/aurora), `f39103b9…431c`) names
  "aurora-0.25-v1.5-ensemble.ckpt". If that checkpoint emits an ensemble, (d) credits it. The capability
  axis is already held in `sources/verification_queue.yaml` for a re-fetch, and that re-fetch should settle
  this.
- **terramind, generative.** Credited from "TerraMind can perform any-to-any generation based on varying
  combinations of inputs." The lunar model uses the same recipe and is denied only because its publisher
  says it is "Not a scientific-grade generative product". TerraMind's publisher makes no such disclaimer and
  evaluates its generations, so the two records are consistent with what each publisher claims.
- **chai, boltz and alphafold, generative.** They sample several structures for one input. (d) credits a
  probabilistic forecast of a stochastic future. Several samples of one fixed target are not that, and the
  records already say so.
- **prithvi-eo, multi_instrument.** HLS harmonizes Landsat OLI and Sentinel-2 MSI into one product. The
  credit is consistent with granite-geospatial's exclusion for the Landsat-only L30 half.
- **mattersim, adaptation_pathway.** The credited quote, "The model can be fine-tuned for atomistic
  simulations at a desired level of theory or for direct structure-to-property predictions with high data
  efficiency.", describes a pathway without executing one. Ruling (b) asks for the runnable entry point,
  which should be cited at the next refresh.
- **prithvi-wxc, adaptation_pathway.** "We have fine-tuned the model to a number of downstream tasks"
  points to linked repositories. The executable entry point should be cited at the next refresh.

## Sources

Recorded sources, as cited in `sources/scores/*.yaml` on `bf66c237`. The digest is the record's
`content_sha256`, and every quote above was matched against a saved body with that digest.

| URL | sha256 |
|---|---|
| https://huggingface.co/ibm-esa-geospatial/TerraMind-1.0-large/raw/main/README.md | 1fac187c72dfbc20c5c4588885b96ed4c1a6d3ec307e8ec6a17993e5d5b9d9d7 |
| https://raw.githubusercontent.com/NASA-IMPACT/Prithvi-EO-2.0/main/README.md | f13bf62e35eac8890f88d3d5b42f96738f3d7cac9b2319207e6757b4fb07d616 |
| https://clay-foundation.github.io/model/release-notes/specification.html | 192ffac7ff1ba4be73c044966d283784ff618cb70d9dd8534e346d8a6a26e891 |
| https://huggingface.co/nasa-ibm-ai4science/NASA-IBM-Lunar-Foundation-Model/raw/main/README.md | 8b19ff3221fcf45756a265f41883ce11145b3fdb18d5166b9b87393633abdae6 |
| https://raw.githubusercontent.com/NASA-IMPACT/Prithvi-WxC/main/README.md | 189a67cd59990516831cca4d6dcc556764c18b17919cfefc2bbcaa4e15715713 |
| https://raw.githubusercontent.com/198808xc/Pangu-Weather/master/README.md | b21aeee735b3196efd1334fc7f34caa0a5fb1e549d06d7ae3738db7b237a19a1 |
| https://raw.githubusercontent.com/nasaharvest/presto/main/README.md | b023f4f2fc565e15100f50149c19dcd3581a5df8eeddce53be9dc044d7fb6836 |
| https://raw.githubusercontent.com/nasaharvest/presto/main/presto/dataops/pipelines/s1_s2_era5_srtm.py | 7f371255202450ba4a63a39c90665579252976d8cd127aa866f7391c2607aaf4 |
| https://storage.googleapis.com/earthengine-stac/catalog/GOOGLE/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL.json | 1c5fb2abdcbf6d12a9b6cfecf10ccc55cbfac7d009645536d4e4828f9a14e012 |
| https://google-deepmind-alphagenome.readthedocs-hosted.com/exploring_model_metadata.html | 835a5f14f599be7fa2dff45c091fa12c0a752c29317232f789f2a86ad7bb4c36 |
| https://huggingface.co/ctheodoris/Geneformer/raw/main/README.md | 56d6e570b349cbedae9a54634421c94e7af8ea467ce0fdd79193372ae3cbdbd8 |
| https://raw.githubusercontent.com/bowang-lab/scGPT/main/README.md | b0503e8ca789f19f1fc2350c5aaf57b1b323bbae43b354655231b5f4a1586c83 |
| https://raw.githubusercontent.com/bowang-lab/scGPT/main/tutorials/Tutorial_Perturbation.ipynb | a997191d88e4c05969103e777f1323ebf4263238e64520877ae3a0f6aed4bdbb |
| https://huggingface.co/ibm-granite/granite-geospatial-biomass/raw/main/README.md | c80890eaf65aee0132469dc3507bd949aaa478515846773a720d690a11998b00 |
| https://raw.githubusercontent.com/NASA-IMPACT/Surya/main/README.md | 5198cb46082d52645d7cd1648befe08921afac8286c831cd54d319d0fba54873 |

Bodies saved by the #1076 refresh but not cited in a record:

| URL | sha256 |
|---|---|
| https://huggingface.co/ibm-nasa-geospatial/Prithvi-WxC-1.0-2300M/raw/main/README.md | 9eb1978782a865079baa619a4645e681585a808477411088dec8695c274ae459 |
| https://huggingface.co/api/models/microsoft/aurora | f39103b9c970c5eea3015e7cfd1ac082f020c0b30e44c3bb6ca02048889f431c |

Fetched for this audit on 2026-11-16 with `uv run python -m build.fetch_source --body-dir` into the session
scratchpad:

| URL | HTTP | sha256 | Question |
|---|---|---|---|
| https://arxiv.org/abs/2504.11171 | 200 | e5a216861f93d671d100b3ecb02d75cb3e05acf5ffab26df18d5017287398704 | terramind |
| https://huggingface.co/datasets/ibm-esa-geospatial/TerraMesh/raw/main/README.md | 200 | e3b3cc93aea873e434ed44200cec16a133d19dd8bdad1df6d6ec8e870e7cceea | terramind |
| https://arxiv.org/html/2504.11171 | 200 | 7babd2fe59f4165638819d32333adef042560a5dcf59762f5711d902c54a0ba0 | terramind |
| https://terrastackai.github.io/terratorch/stable/guide/terramind/ | 404 | 70d613e3acfba24fd2876fcbacaf639e1e111ef4d54baf70761c47673f37d6a3 | terramind (dead, unused) |
| https://arxiv.org/html/2412.02732 | 200 | 382607a8cabd9d726d9224deee2536fe9cbb30bcbf27cde640d45f740414b019 | prithvi-eo |
| https://arxiv.org/html/2403.15356 | 200 | 857467b047bf2fd2b00e9bef6c845a8df9a03512730ecc96a280d78b6c7cc2b4 | dofa |
| https://arxiv.org/html/2507.22291 | 200 | 6cc8998c146464311bb3aa670c11746a204b30c5edc6bf2791f3f6a9e1939b24 | alphaearth-foundations |
| https://raw.githubusercontent.com/ibm-granite/granite-geospatial-biomass/main/notebooks/agb_getting_started.ipynb | 200 | 2f7073e0b5992da7c3c470dd64d8e0d34e632a4decb95980c3f5dc802900e04d | granite-geospatial |
| https://geneformer.readthedocs.io/en/latest/geneformer.in_silico_perturber.html | 200 | 71264b6c0789a0c98753688628696421adbf374b86aa63879e3a7a16224bf8a3 | geneformer |
