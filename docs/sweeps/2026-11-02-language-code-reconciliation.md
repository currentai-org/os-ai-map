# Language code reconciliation: FLORES+, SEA-HELM and AfroBench, 2026-11-02

## Scope

The calibration of 2026-11-01 ([`2026-11-01-language-depth-calibration.md`](2026-11-01-language-depth-calibration.md),
"Language codes: needs reconciliation") found that three products' `languages` no longer match the
codes their sources use, and recorded twelve coverage entries as inferred mappings
(`source_language`) rather than change `languages` itself. `capability.md` leaves that to a curation
pass of its own. This is that pass, for FLORES+, SEA-HELM and AfroBench. ThaiExam had no
discrepancy.

Each product's declared `languages` was compared with what its current primary sources list, read
on 2026-11-02 with `uv run python -m build.fetch_source` ([Sources read](#sources-read)). Every
discrepancy is recorded below as one of three kinds:

- **Coding difference:** the same language under another code: a macrolanguage against an
  individual language, a two-letter against a three-letter code, or a code the source has renamed.
  Coverage does not change.
- **Coverage change:** a language the record should list and does not, or lists and should not.
  Where the dataset gained it after the record was made, the row says so; where the record simply
  missed it, the row says that instead, since the target population moves either way.
- **Source error or inconsistency:** the source's own documents disagree, or it uses a code
  inconsistently. It is documented and coverage is not changed to follow it. Where the case is
  genuinely ambiguous the code is left as it is and marked **needs ruling**.

What changed: `languages` on the three product files; on the score files, the `language` of every
`capability.language_coverage` entry whose code changed (with `source_language` dropped where it
now equals `language`, and added where the cited source's code now differs), and AfroBench's
`pivot_languages`. Nothing else moved: no `capability.score`, band, `relative_to`, `value`, `note`,
`last_verified`, count, provenance or source, and no description, since none names a count that
changed. No coverage entry was added for a language this pass adds; those languages are unknown
until a fill pass records them ([Evidence completeness](#evidence-completeness)).

Rule followed throughout: use the most specific code the source supports, the individual language
where the source names that variety and the macrolanguage only where the source means it.

## Every mapping and change

### FLORES+

The product's `languages` was built on 2026-09-30 from the card's metadata header, read through the
Hub API (`docs/sweeps/2026-09-30-identity-attributes/languages/batch-02.jsonl`: "card language list
(gated repo, read via Hugging Face API)"). That header still carries FLORES-200's codes, as
two-letter codes where one exists, while the card's Language Coverage table and the repository's
data configurations use the current ones. The table and the configs agree with each other exactly
(216 codes, 236 varieties), so they are the reading used here. "Card" below is
<https://huggingface.co/datasets/openlanguagedata/flores_plus>, "API" is
<https://huggingface.co/api/datasets/openlanguagedata/flores_plus> (its `cardData.language` is the
metadata header and `cardData.configs` the data configurations), and "FLORES-200" is
<https://raw.githubusercontent.com/facebookresearch/flores/main/flores200/README.md>.

| Old code | New code | Kind | What the source states |
|---|---|---|---|
| `ara` | `arb` | coding difference: macrolanguage to individual; metadata `ar` | Card: "arb \| Arab \| stan1318 \| Modern Standard Arabic" and "arb \| Latn \| stan1318 \| Modern Standard Arabic (Romanized)"; configs `arb_Arab`, `arb_Latn`; FLORES-200: "Modern Standard Arabic \| arb_Arab". 2 entries recoded, `source_language` dropped |
| `est` | `ekk` | coding difference: macrolanguage to individual; metadata `et` | Card: "ekk \| Latn \| esto1258 \| Estonian"; config `ekk_Latn`; FLORES-200: "Estonian \| est_Latn". 2 entries recoded, `source_language` dropped |
| `grn` | `gug` | coding difference: macrolanguage to individual; metadata `gn` | Card: "gug \| Latn \| para1311 \| Paraguayan Guaraní"; config `gug_Latn`; FLORES-200: "Guarani \| grn_Latn". 2 entries recoded, `source_language` dropped |
| `zho` | `cmn` | coding difference: macrolanguage to individual; metadata `zh` | Card: "cmn \| Hans \| beij1234 \| Mandarin Chinese (Standard Beijing)" and "cmn \| Hant \| taib1240 \| Mandarin Chinese (Taiwanese)"; configs `cmn_Hans`, `cmn_Hant`; FLORES-200: "Chinese (Simplified) \| zho_Hans". 2 entries recoded, `source_language` dropped; provenance stays `unknown` (both have data cards behind the gate). `yue` and `wuu` are separate rows of their own |
| `tgl` | `fil` | coding difference: renamed code; metadata `tl` | Card: "fil \| Latn \| fili1244 \| Filipino"; config `fil_Latn`; no `tgl` row or config; FLORES-200: "Tagalog \| tgl_Latn". No entry existed. `fil` has its own data card (`dataset_cards/fil_Latn.md` in the API's file list), so whether its text is FLORES-200's Tagalog relabeled or recreated is stated only behind the gate. The count is the same either way |
| `kon` | `ktu` | coding difference: renamed code; metadata `kg` | Card: "ktu \| Latn \| kitu1246 \| Kituba (DRC)"; config `ktu_Latn`; FLORES-200: "Kikongo \| kon_Latn". No entry existed. In `sources/snapshots/iso-639-3.tab`, `kon` is Kongo, scope M, and `ktu` is Kituba (Democratic Republic of Congo), scope I: the card now names the language Kituba rather than Kongo. `ktu` has no data card of its own |
| `aka` | `twi` (already listed): `aka` removed | coding difference: renamed code; metadata `ak` | Card: "twi \| Latn \| akua1239 \| Akuapem Twi" and "twi \| Latn \| asan1239 \| Asante Twi"; configs `twi_Latn_akua1239`, `twi_Latn_asan1239`; no `aka` row or config; FLORES-200: "Akan \| aka_Latn" and "Twi \| twi_Latn". No `aka` entry existed. The card codes both varieties `twi`, and the ISO 639-3 snapshot has no finer code for either (`aka` is the Akan macrolanguage, `twi` the individual language), so nothing finer can be kept |
| `tzm` | `zgh` (already listed): `tzm` removed | coding difference: renamed code; metadata still lists `tzm` | Card: "zgh \| Tfng \| stan1324 \| Standard Moroccan Tamazight", with a data card of its own (`dataset_cards/zgh_Tfng.md`); no `tzm` row or config; FLORES-200: "Central Atlas Tamazight \| tzm_Tfng". No `tzm` entry existed. If FLORES+ once carried both, this is a removal rather than a rename; the count is the same either way |
| none | `ccp` | coverage change: added to the dataset since the record | Card: "ccp \| Cakm \| chak1266 \| Chakma"; config `ccp_Cakm`. Now in the metadata header (`ccp`), and absent from it on 2026-09-30 (batch-02.jsonl) |
| none | `frp` | coverage change: added since the record | Card: "frp \| Latn \| savo1253 \| Savoyard \| Median Savoyard"; config `frp_Latn_savo1253`. Now in the metadata header, absent on 2026-09-30 |
| none | `seh` | coverage change: added since the record | Card: "seh \| Latn \| nucl1396 (with variant=MZ) \| Sena (Mozambique variety)"; config `seh_Latn_MZ`. Now in the metadata header, absent on 2026-09-30. The calibration's list of card codes the product lacks also omits it, though the repository's last modification (2026-10-25, per the API) predates that read |
| none | `arg` | coverage change: record omission | Card: "arg \| Latn \| arag1245 \| Aragonese"; config `arg_Latn`; never in the metadata header |
| none | `brx` | coverage change: record omission | Card: "brx \| Deva \| bodo1269 \| Bodo \| dev only"; config `brx_Deva` |
| none | `chv` | coverage change: record omission | Card: "chv \| Cyrl \| chuv1255 \| Chuvash"; config `chv_Cyrl` |
| none | `dgo` | coverage change: record omission | Card: "dgo \| Deva \| dogr1250 \| Dogri \| dev only"; config `dgo_Deva` |
| none | `gom` | coverage change: record omission | Card: "gom \| Deva \| goan1235 \| Goan Konkani \| dev only"; config `gom_Deva`. `gom` is the individual language; the card does not mean the `kok` macrolanguage |
| none | `kaa` | coverage change: record omission | Card: "kaa \| Latn \| kara1467 \| Karakalpak \| devtest only"; config `kaa_Latn` |
| none | `myv` | coverage change: record omission | Card: "myv \| Cyrl \| erzy1239 \| Erzya"; config `myv_Cyrl` |
| none | `nqo` | coverage change: record omission | Card: "nqo \| Nkoo \| nkoa1234 \| Nko"; config `nqo_Nkoo` |
| none | `tyv` | coverage change: record omission | Card: "tyv \| Cyrl \| tuvi1240 \| Tuvan"; config `tyv_Cyrl` |
| none | `vmw` | coverage change: record omission | Card: "vmw \| Latn \| cent2033 \| Emakhuwa (Central)"; config `vmw_Latn` |
| none | `wuu` | coverage change: record omission | Card: "wuu \| Hans \| suhu1238 \| Wu Chinese \| dev only"; config `wuu_Hans` |

The eleven "record omission" rows are in the coverage table and the data configs and have never been
in the metadata header the record was built from. When FLORES+ added them is not public: the
repository's `CHANGELOG.md` and commit history are behind the gate (HTTP 401), and the Wayback
Machine's July 2026 capture of the card could not be fetched. Either way the dataset carries them now.

Source inconsistencies in FLORES+, documented and not followed:

| What disagrees | Detail | Effect on the record |
|---|---|---|
| The metadata header against the coverage table and the configs | The header (`cardData.language`, 208 entries) lists `ak`, `ar`, `et`, `gn`, `kg`, `tl`, `tzm` and `zh`, and `ajp`, a code ISO 639-3 has retired (it is not in `sources/snapshots/iso-639-3.tab`); it omits `arb`, `cmn`, `ekk`, `gug`, `fil`, `ktu` and the eleven omission rows above. The table and the 236 configs carry none of the old codes. This is why the record drifted | `languages` now follows the table and configs |
| The card's language count | "Languages: Currently 230 language varieties"; the table has 236 rows and the repository 236 language configurations, over 216 ISO 639-3 codes | none: the description says "more than 200 language varieties", which both satisfy. The capability `value` and `note` say 230 and are band prose, left alone |

### SEA-HELM

| Old code | New code | Kind | What the source states |
|---|---|---|---|
| `msa` | `zsm` | coding difference: macrolanguage to individual | The translation card, <https://huggingface.co/datasets/aisingapore/NLG-Machine-Translation>: "It is sampled from FLORES 200 for Burmese, Chinese, English, Indonesian, Khmer, Malay, Tamil, Thai, and Vietnamese", with splits "en_to_zsm_Latn" and "zsm_Latn_to_en", 1012 each. Its translation entry drops `source_language: zsm`. The judge card, <https://huggingface.co/datasets/aisingapore/MultiTurn-Chat-MT-Bench-Judge>, says "Malay (ms)"; `ms` reads as `msa`, so that entry now carries `source_language: msa`. No source names a Malay other than Standard Malay |
| `tgl` | `tgl`, unchanged | source inconsistency, **needs ruling** | The Kalahi card, <https://huggingface.co/datasets/aisingapore/Cultural-Evaluation-Kalahi>: "Languages Tagalog (tl)", "Kalahi only has a Tagalog (tl) split". The judge card on the same `tl` split: "Filipino (tl)". The paper, <https://arxiv.org/html/2502.14301>: Kalahi is "composed of 150 high-quality Filipino-language" prompts, and "Filipino is the national language of the Philippines ... and is primarily based on Standard Tagalog". The GitHub tables, <https://raw.githubusercontent.com/aisingapore/SEA-HELM/main/docs/datasets_and_prompts.md>, name only "Filipino" ("\| Filipino \| Kalahi MC \| Native \|"). The suite names one language both ways |

Source errors and inconsistencies in SEA-HELM, documented and not followed:

| What disagrees | Detail | Effect on the record |
|---|---|---|
| The translation card's language list | "Languages Burmese (my) Chinese (zh) English (en) Indonesian (id) Javanese Khmer (km) Malay (ml) ..."; its metadata header also has `ml`. `ml` is Malayalam's ISO 639-1 code | none: Malayalam is not added |
| The GitHub tables' spelling | "Sudanese" for Sundanese (the sentiment and metaphor tables) | none: `sun` stays; Sudanese Arabic (`apd`) is not added |
| The translation card's README against its own YAML and data files | The README's table lists `en_to_zsm_Latn`, `en_to_mya_Mymr` and the rest at 1012, and no Lao or Filipino split. The card's YAML (`dataset_info` and `configs`, read through <https://huggingface.co/api/datasets/aisingapore/NLG-Machine-Translation>) and its data files use two-letter configurations instead: `en_to_ms` 1012, `en_to_lo` 1012, `en_to_my` 600, `en_to_tl` 600, and the reverse directions | none on `languages`: Lao and Filipino are already listed. It does bear on the coverage record; see [Needs a maintainer decision](#needs-a-maintainer-decision) |

Not a discrepancy: SEA-HELM's sources name Chinese as Chinese ("Chinese (zh)", `zho_Hans`, and the
Belebele task's `zh` and `zh_t` configurations), so its pivot stays `zho`. FLORES+'s move to `cmn` is
FLORES+'s own coding and does not carry over to a suite whose documents do not use it.

### AfroBench

The product's `languages` was built from Table 10 of the paper, <https://arxiv.org/html/2311.07978>
(v5), the list of the 64 African languages (batch-02.jsonl: "paper Table 10 language list"). Table 11
marks which datasets cover which language, and it disagrees with Table 10 on six languages and on
one code.

| Old code | New code | Kind | What the source states |
|---|---|---|---|
| none | `arb`, as a pivot | coverage change: record omission | Section 3.2: "we focus specifically on the African language subsets, along with select high-resource languages (English, French, Portuguese and Arabic), due to their widespread use across different African regions". Table 11 has an `ara` row (OpenAI-MMLU, XL-SUM); Table 2's caption reads "excl. arb: 4689 & eng: 11,535. (in XLSum)". The paper codes Arabic both ways; `arb` is the code it uses where it gives the figure, and the most specific one it supports |
| none | `eng`, as a pivot | coverage change: record omission | The same Section 3.2 sentence; Table 2's caption ("eng: 11,535"); "All translations are from English except for the Mafand benchmark with a few languages whose source is French" |
| none | `fra`, as a pivot | coverage change: record omission | The same Section 3.2 sentence; the translation sentence above; AfriQA has "context passages in English or French" |
| `orm` | `orm`, unchanged | source inconsistency | Table 10: "Oromo (orm)". Table 11 has an `orm` row (AfriHate, AfriSenti, AfriXNLI, Injongo-Intent, MasakhaNEWS, AfriMGSM, AfriMMLU, NTREX-128, XL-SUM) and a separate `gaz` row (SIB-200, Flores), the FLORES-200 code for West Central Oromo. One language under two codes; the paper counts it once. `orm` is kept because the language list and nine of the eleven datasets use it; the two FLORES-derived entries keep `source_language: gaz` |
| `plt` | `plt`, unchanged | coding difference: individual against macrolanguage | Table 10: "Malagasy (plt)"; Table 11 marks NTREX-128 under `plt`. The NTREX repository's configuration is `mlg_Latn` (<https://datasets-server.huggingface.co/size?dataset=masakhane/ntrex_african>). The suite names the individual language; its NTREX entry keeps `source_language: mlg` |
| `tir` | `tir`, unchanged | source error | Table 10: "Tigrinya (tig)"; `tig` is Tigre's code. Table 11 has `tir`. Already recorded as `tir` on 2026-09-30 |
| none | `nde`, not added | source inconsistency, **needs ruling** | Table 11 marks North Ndebele (`nde`) under NTREX-128; Table 10 does not list it. The NTREX repository has an `nde_Latn` configuration with 1997 test rows |
| none | `ven`, not added | source inconsistency, **needs ruling** | Table 11 marks Venda (`ven`) under NTREX-128; Table 10 does not list it. The NTREX repository has a `ven_Latn` configuration with 1997 test rows |
| `nqo` | `nqo`, unchanged | source inconsistency, **needs ruling** | Table 10: "N’Ko (nqo) \| Mande \| West \| Latin". Table 11 has no `nqo` row, and no AfroBench dataset carries it |
| `por` | `por`, unchanged | source inconsistency, **needs ruling** | Table 10 lists "Mozambican Portuguese (pt-MZ)" among the 64 African languages; Section 3.2 lists Portuguese among the "select high-resource languages"; Table 11 has no `por` row; AfriSenti's repository has a `por` configuration, 3,662 test rows (<https://datasets-server.huggingface.co/size?dataset=masakhane/afrisenti>) |

Not discrepancies: Table 10 counts 64 African languages over 63 ISO 639-3 codes because it lists
Kanuri (`knc`) twice, once per script, so the description's "64 African languages" is the paper's own
count and stays. AfroBench's own tables also use `aka`, `kon`, `tzm` and `swa`, which is FLORES-200's
coding of the data it uses; that FLORES+ has since recoded its text is FLORES+'s change, not AfroBench's.

### Discrepancies by kind

| Kind | FLORES+ | SEA-HELM | AfroBench | All |
|---|---|---|---|---|
| Coding difference | 8 (`ara`, `est`, `grn`, `zho`, `tgl`, `kon`, `aka`, `tzm`) | 1 (`msa`) | 1 (`plt`, unchanged) | 10 |
| Coverage change | 14 (3 added since the record, 11 record omissions) | 0 | 3 (pivots `arb`, `eng`, `fra`) | 17 |
| Source error or inconsistency | 2 | 4 (one needs ruling) | 6 (four need rulings, covering `nde`, `ven`, `nqo`, `por`) | 12 |

The mapped entries the calibration counted fall from 12 to 4: FLORES+'s eight and SEA-HELM's
translation entry no longer need `source_language`; SEA-HELM's judge entry now carries one
(`msa`); AfroBench's three (`gaz` twice, `mlg`) stand.

## Target population, before and after

The target languages are `languages` less `pivot_languages`, the population the median is taken
over (R-2026-11-01-b).

| Set | Before | After | Codes added | Codes removed | Codes recoded |
|---|---|---|---|---|---|
| FLORES+ | 203 (204 listed, pivot `eng`) | 215 (216 listed, pivot `eng`) | `arg`, `brx`, `ccp`, `chv`, `dgo`, `frp`, `gom`, `kaa`, `myv`, `nqo`, `seh`, `tyv`, `vmw`, `wuu` (14) | none outright; `aka` and `tzm` fold into the already-listed `twi` and `zgh` (2) | `ara` to `arb`, `est` to `ekk`, `grn` to `gug`, `zho` to `cmn`, `tgl` to `fil`, `kon` to `ktu` (6) |
| SEA-HELM | 11 (13 listed, pivots `eng`, `zho`) | 11 (13 listed, same pivots) | none | none | `msa` to `zsm` (1) |
| AfroBench | 63 (63 listed, no pivot) | 63 (66 listed, pivots `arb`, `eng`, `fra`) | none to the targets; `arb`, `eng`, `fra` added to `languages` as pivots | none | none |

FLORES+: 203, less the two folded codes, plus the fourteen added, is 215. No variety split here
changes a median: Akuapem and Asante Twi share one ISO 639-3 code, and the six recodes keep one code
per language.

## Evidence completeness

Measured target languages over all target languages, under the definition in `capability.md`
(an official-evaluation entry whose qualifying depth is established, or a documented zero),
recomputed from the files before and after this change.

| Set | Before | After | Why |
|---|---|---|---|
| FLORES+ | 188 of 203 | **188 of 215** | The recodes keep every entry and every measured language (`arb`, `ekk`, `gug` measured as before; `cmn` unmeasured as `zho` was). `aka` and `tzm`, unmeasured, fold away; `ktu` and `fil` replace the unmeasured `kon` and `tgl`; the fourteen added languages have no entry yet. Unmeasured: `apd`, `ast`, `cmn`, `kjh`, `lij`, `lld`, `mfe`, `mhr`, `nob`, `yue`, `zgh` (gated data cards, as before), `fil`, `ktu`, and the fourteen added |
| SEA-HELM | 10 of 11 | 10 of 11 | `zsm` is measured as `msa` was; Lao is still the one unmeasured language |
| AfroBench | 54 of 63 | 54 of 63 | No target changed; the pivots are outside the population |

As a check only, under the calibration's proposed and unadopted bands (highest task band per
language), the robustness test still agrees for all three: filling FLORES+'s 27 unmeasured
languages with 0 or with 5 leaves the median of 215 at 4, as it was for 203. A fill pass can raise
FLORES+'s count without a source this pass did not already read: the card states 997 dev and 1,012
devtest sentences for every language and marks `brx`, `dgo`, `gom` and `wuu` "dev only", which
would make those four documented zeros on `devtest`, and `ktu` has no data card of its own, which
under the calibration's reading makes it FLORES-200 text. How the other new languages' text was made
is in data cards behind the gate.

## Needs a maintainer decision

Left as they are and marked **needs ruling**:

1. **SEA-HELM: `tgl` or `fil`.** The Hugging Face cards call the `tl` split Tagalog (Kalahi) and
   Filipino (the judge card); the paper and the GitHub tables say Filipino, which the paper says "is
   primarily based on Standard Tagalog". Both are individual codes and the population is one
   language either way. Recommended: `fil`, since the suite's own prose names Filipino and its
   two-letter `tl` is the nearest ISO 639-1 code available for it. FLORES+, whose card names only
   Filipino, moved to `fil` in this pass.
2. **AfroBench: `nde` and `ven`.** Table 11 and the NTREX repository have them; Table 10, the
   64-language list, does not. Adding them makes 65 targets, both unmeasured until filled (NTREX's
   1997 sentences would place each with the other NTREX languages). Recommended: add, since Table 11
   is the per-dataset coverage and the data exists.
3. **AfroBench: `nqo`.** Table 10 lists it and no dataset in Table 11 covers it. It is one of the nine
   unmeasured target languages, and can never be measured from AfroBench's own sources.
   Recommended: remove.
4. **AfroBench: `por`.** Table 10 counts Mozambican Portuguese among the African languages;
   Section 3.2 calls Portuguese a high-resource comparison language, the same footing as the three
   pivots added here. Target, pivot, or neither is the question the calibration raised (its item 9).
   As a pivot, the population falls to 62 and completeness to 54 of 62.

None of these four moves a proposed median: each is one or two unmeasured languages in a population
whose robustness test already agrees.

Also for the maintainer, outside `languages`:

- **SEA-HELM's translation card disagrees with itself on counts.** Its README states 1012 for
  `en_to_mya_Mymr`; its YAML and data files have 600 for `en_to_my` and `en_to_tl`, and 1012 for
  `en_to_lo`. The calibration recorded Burmese at 1012 from the README. On the proposed translation
  ladder, 600 is a 3 rather than a 4, and Lao gains a stated count. Which half of the card is current
  is a coverage question for the next fill, not settled here.
- **FLORES+'s 230 against 236** is in the capability `value` and `note`, band prose this pass does
  not touch.

## Sources read

All fetched 2026-11-02 with `build.fetch_source`. Hub HTML pages, and arXiv's HTML for the
SEA-HELM paper, change between fetches; the digests are those of the bodies quoted from, and every
quoted fragment was checked against them. The Hub API, GitHub and datasets-server bodies were
stable across two fetches.

| URL | HTTP | sha256 |
|---|---|---|
| https://huggingface.co/datasets/openlanguagedata/flores_plus | 200 | `c70129c1fe7b2c2b6ea105862ebf0b907a64d61265d23baa55deaede438d8e0c` |
| https://huggingface.co/api/datasets/openlanguagedata/flores_plus | 200 | `b8e9c0e95fa87a3758edf49735319c98ca75ad10dfddbc80fd7c6e52420383d9` |
| https://raw.githubusercontent.com/facebookresearch/flores/main/flores200/README.md | 200 | `74ccbbe29feba9d92cb3ee472387579ab2aa5c0299d47dcec7614b2c06cd49fc` |
| https://huggingface.co/datasets/openlanguagedata/flores_plus/raw/main/CHANGELOG.md | 401 | gated |
| https://oldi.org/languages | 200 | `6f22f860ce47f3b65e1e63540d8f08c0b26bdcc47321d165da9fdfc69add43e0` |
| https://huggingface.co/datasets/aisingapore/NLG-Machine-Translation | 200 | `bce51a70bec127cb8dbc0ed6f66eea47690379d51bb835c0cbb5671c1fe914ee` |
| https://huggingface.co/api/datasets/aisingapore/NLG-Machine-Translation | 200 | `b9d7d37207788ea7b11af79cd019d4a575bc1cef9f5cf75080828fcee86ad95f` |
| https://huggingface.co/datasets/aisingapore/MultiTurn-Chat-MT-Bench-Judge | 200 | `4787ac2caf640de3caa33f1dec64c1f2debc2f6bfaf92396bab38340aba698e9` |
| https://huggingface.co/api/datasets/aisingapore/MultiTurn-Chat-MT-Bench-Judge | 200 | `6eb68d61b2480cb556a3c673aea5bd965196855736d12a390167407c87a7001b` |
| https://huggingface.co/datasets/aisingapore/Cultural-Evaluation-Kalahi | 200 | `15a425219bd2863211fb98efb256c619d18dec55d0b2f5296471b77d42a753ac` |
| https://huggingface.co/api/datasets/aisingapore/Cultural-Evaluation-Kalahi | 200 | `2968388ecbc40d40f12cd8aa62bfecb5b8e33f51d569f4a69384f4bee5803eaa` |
| https://huggingface.co/api/datasets/aisingapore/Instruction-Following-IFEval | 200 | `4b610d0820de4acca2a4eebde70ccde44419b9c591ea461458873cbaba42025c` |
| https://huggingface.co/api/datasets/aisingapore/NLU-Belebele-MCQA | 200 | `583b61f88fc26285145aaec67d0861c0f5d506e6015d52b0f4624bfb8107b900` |
| https://raw.githubusercontent.com/aisingapore/SEA-HELM/main/docs/datasets_and_prompts.md | 200 | `3cb8b1610ffe510997301fb267f6717bf63c574596a7aa4472a1f2f94d20135f` |
| https://raw.githubusercontent.com/aisingapore/SEA-HELM/main/README.md | 200 | `9739ddc4df04eb4b54c1005625549ae11143ed62651474102c4122e551c5d2b3` |
| https://arxiv.org/html/2502.14301 | 200 | `bcbe21592334eaffe4424505c065cf1e4e806929c5203618cb7f0a8b9ef85a25` (a second fetch the same day returned `7021b8e7ca3b0847fa4cd62ee04d69f6aed6cd911a6a3a8ae70ff7aec22274f6`, the digest the calibration recorded) |
| https://arxiv.org/html/2311.07978 | 200 | `ef2b0d2751fd66adfd660ee0f45c3e2c928ff04cf846b4c5b7130df0243f6822` |
| https://datasets-server.huggingface.co/size?dataset=masakhane/ntrex_african | 200 | `eea43d72e9d50175c01ce80c1d2671ebf27e7a508744808e6154afe9f199d315` |
| https://datasets-server.huggingface.co/size?dataset=masakhane/afrisenti | 200 | `41292f7ff74a7b63ae394537a594830fd26e7506c828ecc31597d693faf8fb88` |
| https://mcgill-nlp.github.io/AfroBench/ | 200 | `f85a45db10d5c58c17662013b986247ea836204be4493c605844d83de8612386` |
