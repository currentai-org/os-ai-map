# Scientific AI models seed — 2026-09-10

## Scope and boundary

This batch converts the candidate roster in issue #533 into the identity-only seed for the
preliminary `scientific_ai_models` category. The boundary is the product's data: models trained
on instrument, measurement, or scientific-simulation output belong; general-purpose models
trained on human-authored text, natural images, speech, or video do not. A reusable backbone is
not required. Software harnesses are outside the category even when they run scientific models.

Every accepted row below resolved to a live addressable artifact on 2026-09-10. Repository
license labels were not treated as weights licenses, and no score was inferred during discovery.

## Reconciled counts

```text
raw_signals       = 35
duplicate_signals = 1
unique_candidates = 34
accepted          = 34
parked            = 0

35 = 1 + 34
34 = 34 + 0
```

The duplicate signal was `google-deepmind/graphcast`. GitHub redirects it to
`google-deepmind/weathernext`, whose current README presents GraphCast and GenCast as models in
the WeatherNext family. The seed therefore carries one `weathernext` product line rather than a
separate GraphCast product.

## Accepted candidates and primary discovery sources

All sources were fetched on 2026-09-10.

| Candidate | Primary source used for identity |
|---|---|
| Prithvi-EO | https://github.com/NASA-IMPACT/Prithvi-EO-2.0 |
| TerraMind | https://github.com/IBM/terramind |
| Clay | https://github.com/Clay-foundation/model |
| Granite Geospatial | https://huggingface.co/ibm-granite/granite-geospatial-biomass |
| DOFA | https://github.com/zhu-xlab/DOFA |
| Presto | https://github.com/nasaharvest/presto |
| AlphaEarth Foundations | https://arxiv.org/abs/2507.22291 |
| Aurora | https://github.com/microsoft/aurora |
| WeatherNext | https://github.com/google-deepmind/weathernext |
| Prithvi WxC | https://github.com/NASA-IMPACT/Prithvi-WxC |
| ClimaX | https://github.com/microsoft/ClimaX |
| NeuralGCM | https://github.com/neuralgcm/neuralgcm |
| AIFS | https://huggingface.co/ecmwf/aifs-single-1.0 |
| Pangu-Weather | https://github.com/198808xc/Pangu-Weather |
| Surya | https://github.com/NASA-IMPACT/Surya |
| NASA-IBM Lunar Foundation Model | https://github.com/NASA-IMPACT/NASA-IBM-Lunar-Foundation-Model |
| ESM-2 | https://huggingface.co/facebook/esm2_t33_650M_UR50D |
| ESM-3 | https://huggingface.co/biohub/esm3-sm-open-v1 |
| AlphaFold | https://github.com/google-deepmind/alphafold |
| OpenFold | https://huggingface.co/OpenFold/OpenFold3 |
| Boltz | https://github.com/jwohlwend/boltz |
| Chai | https://github.com/chaidiscovery/chai-lab |
| RFdiffusion | https://github.com/RosettaCommons/RFdiffusion |
| Evo 2 | https://github.com/ArcInstitute/evo2 |
| Geneformer | https://huggingface.co/ctheodoris/Geneformer |
| scGPT | https://github.com/bowang-lab/scGPT |
| UCE | https://github.com/snap-stanford/UCE |
| AlphaGenome | https://huggingface.co/google/alphagenome-all-folds |
| MatterGen | https://huggingface.co/microsoft/mattergen |
| MatterSim | https://github.com/microsoft/mattersim |
| UMA | https://github.com/facebookresearch/fairchem |
| MACE | https://github.com/ACEsuit/mace |
| Orb | https://github.com/orbital-materials/orb-models |
| GNoME | https://github.com/google-deepmind/materials_discovery |

## Identity and evidence notes for promotion

- `google-deepmind/graphcast` redirects to `google-deepmind/weathernext`; promotion must keep
  GraphCast, GenCast, and WeatherNext checkpoints under one product-line slug unless a primary
  source later establishes separately sold or governed products.
- ESM-2's original `facebookresearch/esm` repository is archived, so the seed uses the live
  weights artifact. ESM-3's open repository and checkpoint now live under Biohub accounts even
  though EvolutionaryScale published the product; the organization and handle records preserve
  that transfer explicitly.
- Granite Geospatial is a line of task-specific checkpoints. The seed uses the biomass model as
  its addressable representative; promotion must inventory the family before writing the head
  product's complete artifact list.
- Pangu-Weather's reference implementation is published under a lead author's account rather
  than a Huawei organization. That ownership bridge is explicit in `sources/org_handles.yaml`.
- AlphaFold and GNoME have open repositories whose contents do not by themselves prove that
  trained weights are distributed. AlphaGenome was initially described as API-only, but the
  first-party `google/alphagenome-all-folds` Hub repository is gated and contains checkpoint
  manifests; promotion must read its access terms and governing license rather than repeating
  the withdrawn API-only claim.
- MACE, UMA, Boltz, and Orb have package distribution paths. Issue #536 governs whether their
  adoption signal should route through those packages; this batch records the package identifiers
  but does not change the adoption methodology.

## Parked candidates

None. The one duplicate proposal row was reconciled as a duplicate signal rather than parked as
a distinct candidate.
