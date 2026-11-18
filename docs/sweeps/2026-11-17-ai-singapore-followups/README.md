# AI Singapore follow-ups, 2026-11-17

AI Singapore raised concerns about how the Gap Map scores language work, and the maintainers
committed to fixes. A review on 2026-11-17 found several merged changes incomplete. This record
covers the engineering and data follow-ups that needed no new methodology decision, one pull
request each. No scoring rule changed in any of them.

## SEA-HELM's Khmer, Lao and Burmese evidence

**The claim checked.** Main scored SEA-HELM 2, down from 5, because its Khmer, Lao and Burmese
test material was only a copy of FLORES-200, so each of those languages sat at band 1 with nothing
independent to back the FLORES items. One more language at band 3 would have lifted the suite to 3.

**What the primary sources show.** The claim was right about FLORES and wrong about "only".
SEA-HELM's translation items in all three languages are sampled from FLORES-200, as its card says.
But since its v1.2 release (June 2026) the suite has published other tests in these languages,
and main's coverage record was built from the dataset cards' prose and README tables, which still
name only the first release's languages. The split metadata on each card (`dataset_info`) and the
suite's own dataset tables (`datasets_and_prompts.md` in the SEA-HELM repository) list the newer ones:

| Language | Test (component) | Items | Provenance, per the suite's tables | Independent of FLORES |
|---|---|---|---|---|
| Khmer | SEA-IFEval (`sea-helm`) | 105 | human translation of IFEval | yes |
| Khmer | SEA MT-Bench (`sea-helm`) | 58 | human translation of MT-Bench | yes |
| Khmer | Belebele (`belebele`) | 895 | human translation | no: its passages are FLORES sentences |
| Lao | SEA-IFEval | 105 | human translation of IFEval | yes |
| Lao | SEA MT-Bench | 58 | human translation | yes |
| Lao | Belebele | 895 | human translation | no |
| Burmese | SEA-IFEval | 105 | human translation of IFEval | yes |
| Burmese | XNLI (`xnli`) | 600 | human translation | yes |
| Burmese | XCOPA (`xcopa`) | 400 | human translation | yes |
| Burmese | XL-Sum (`xl-sum`) | 100 | native | yes |
| Burmese | SEA MT-Bench | 58 | human translation | yes |
| Burmese | Belebele | 120 | human translation | no |

Sources: the `dataset_info` of `aisingapore/Instruction-Following-IFEval`,
`MultiTurn-Chat-MT-Bench`, `NLU-Belebele-MCQA`, `NLR-NLI`, `NLR-Causal-Reasoning` and
`NLG-Abstractive-Summarization` on the Hugging Face API; the SEA-HELM tables row "Filipino,
Indonesian, Vietnamese, Malay, Burmese, Lao, Khmer | SEA-IFEval | Human translation" and its
siblings; the Belebele task config, which maps `km`, `lo` and `my` to `NLU-Belebele-MCQA`. Every
citation is recorded with its digest in `sources/scores/sea-helm.yaml`.

SEA-IFEval alone decides Khmer and Lao: 105 items is band 2, it is independent of FLORES, and an
imported test backed by an independent band-2 test counts up to band 3. Burmese has XNLI and XCOPA
as well. The margin is thin for Khmer and Lao, since 105 items clears the band-2 step of 100 by five.

**What changed.** `sources/scores/sea-helm.yaml` gains 26 coverage entries: the table above, plus
Belebele in every target language that has a split, SEA-IFEval, SEA MT-Bench, XNLI and XCOPA for
Malay, SEA MT-Bench for Filipino, and LINDSEA for Tamil. Each one rests on both a split count and a
provenance row. `sources/lineage.yaml` extends SEA-HELM's SEA-IFEval, SEA MT-Bench and LINDSEA
records with the tables' rows, since the cards those records cited name only the first release's
languages.

Left out, because the suite names no source for them: sentiment in Malay, Burmese and Lao and
toxicity in Burmese and Malay, which its tables mark "Native" with no dataset. Also left out:
Filipino's Batayan tasks (Filipino was already at 3, and the Batayan lineage record covers its
translation items only), the Global MMLU files kept in the SEA-HELM repository, Tamil SEA-IFEval
and MT-Bench (no provenance stated), and SEA-NLI, whose repository requires manual approval, so its
per-language counts cannot be read.

**Score changes.** From `build/depth_ladder.py`:

| Language | Before | After |
|---|---|---|
| Khmer | 1 | 3 |
| Lao | 1 | 3 |
| Burmese | 1 | 3 |
| Malay | 2 | 3 |
| Javanese | 2 | 3 |
| Sundanese | 2 | 3 |
| Filipino, Indonesian, Tamil, Thai, Vietnamese | 3 | 3 |
| **SEA-HELM** | **2** | **3** |

Face value stays 3 and the best original band stays 2. No language is capped any more, and the
sensitivity reading (unverified lineage treated as independent) is also 3. Javanese and Sundanese
rise through Belebele, backed by SEA-IFEval; Malay through XNLI, backed the same way. Even with
only the Khmer, Lao and Burmese entries the suite would reach 3, since eight of its eleven languages
would then be at 3.

The full-roster calibration record (`docs/sweeps/2026-11-03-depth-calibration-full-roster.md`) and
`tests/test_depth_calibration.py` are updated together, as the test requires, and the eval-set
category's strapline no longer names SEA-HELM among the suites that fall below 3.

**One caveat for review.** SEA-HELM's default run configuration (`seahelm_tasks/task_config.yaml`)
lists Burmese but not Khmer, Lao, Javanese or Sundanese, although each has published splits and
task configurations. Main already counted Javanese and Sundanese on the same basis, so this record
counts Khmer and Lao the same way.

### Is the correction even-handed?

The cap is code that reads no suite name: an imported test counts up to one band above the best
independent test in the same language, wherever it sits. The question is whether a global suite in
the same position would be treated the same way.

- **FLORES+** is the original source, not an import, so no cap binds; it stays 3.
- **INCLUDE** caps two languages (Arabic and Turkish), on imported exam questions, not FLORES; it
  stays 3.
- **AfroBench** caps 37 languages and stays at 1. In 23 of them its only tests are FLORES and
  SIB-200, which is itself built on FLORES sentences, so there is nothing independent in the suite
  to find. Most of its natively annotated tests elsewhere are part-of-speech and named-entity
  tagging, which the ladder has no measurement model for. A few languages (Kirundi, Tsonga,
  Moroccan Arabic, Fon) carry an independent news, sentiment or diacritics test whose provenance is
  recorded as unknown. Establishing it would be the same kind of correction as this one, and would
  lift those languages but not AfroBench's band. It is left as follow-up work.
