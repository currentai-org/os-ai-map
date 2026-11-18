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
| Burmese | XNLI, translated (`xnli-sea-translation`) | 600 | human translation | yes |
| Burmese | XCOPA, translated (`xcopa-sea-translation`) | 400 | human translation | yes |
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
provenance row. XNLI and XCOPA have no Burmese or Malay of their own, so those items get their own
lineage components, derived from the English sets, with the translator unknown. `sources/lineage.yaml` extends SEA-HELM's SEA-IFEval, SEA MT-Bench and LINDSEA
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
leaves out Khmer, Lao, Javanese and Sundanese entirely, leaves out Malay's NLI and causal-reasoning
tasks, and comments out Burmese MT-Bench, although each has published splits and task
configurations. Main already counted Javanese and Sundanese on the same basis, so this record
counts the rest the same way. Read the other way, counting only the default run, Khmer and Lao
fall back to 1 and Javanese and Sundanese stay at 2, and SEA-HELM still stands at 3.

### Is the correction even-handed?

The cap is code that reads no suite name: an imported test counts up to one band above the best
independent test in the same language, wherever it sits. The question is whether a global suite in
the same position would be treated the same way.

- **FLORES+** is the original source, not an import, so no cap binds; it stays 3.
- **INCLUDE** caps two languages (Arabic and Turkish), on imported exam questions, not FLORES; it
  stays 3.
- **AfroBench** caps 37 languages and stays at 1, which sits exactly on its median: 32 languages
  at 1, 24 above and 7 unmeasured. In 21 of the capped languages its only tests are FLORES and
  SIB-200, which is itself built on FLORES sentences, so there is nothing independent in the suite
  to find. Most of its natively annotated tests elsewhere are part-of-speech and named-entity
  tagging, which the ladder has no measurement model for. Five capped languages (Kirundi, Somali,
  Tsonga, Moroccan Arabic, Fon) carry an independent news, sentiment or diacritics test whose
  provenance is recorded as unknown. Establishing it is the same kind of correction as this one,
  and it would move AfroBench itself: with Kirundi's alone established, the median no longer stands
  and the band becomes unresolved between 1 and 3. It is left as follow-up work, and it is the
  next correction to make for the rule to be applied evenly.

## SEA-HELM's separately published members (#1094)

Issue #993 waited on the Neon `lineage_relation` enum gaining `part_of`. It needed no migration:
every Neon load creates its enum types inside the staging schema from the product schema's lineage
edges, which have included `part_of` since #949, and the site reads the relation as plain text. A
test now pins that.

Four members that AI Singapore publishes on their own as well as inside SEA-HELM are proposed as rows in
`language_specific_eval_sets`, linked by `lineage.part_of: [sea-helm]` and scored under the normal
rules: Kalahi (openness 5, capability 2), LINDSEA (3, 2), SEA-IFEval (3, 2) and SEA-MTBench (3, 1).
A suite and its members count once toward the stage, which does not move. SEA-NLI is the next
member once its per-language counts can be read; its repository requires manual approval.

Suites whose separately published members still have no rows: AfroBench (IrokoBench's three
sets, AfriSenti, MasakhaNER, MasakhaNEWS, MasakhaPOS, AfriQA, MAFAND-MT, SALT, Uhura,
InjongoIntent, NaijaRC, NollySenti, NTREX African, AfriADR), IndicXTREME (IndicCOPA, IndicQA,
IndicXParaphrase, IndicSentiment, Naamapadam, IndicXNLI, MASSIVE), SEACrowd (its hub datasets;
IndoNLU has a row but no link) and the AmericasNLP shared-task data (AmericasNLI).

## Per-language bands for test sets (#1090)

Each evaluation set's per-language bands, the figures its published band is the median of, are
now in the payload (`capability.depth.per_language`) and in a new site table,
`capability_languages`. A test recomputes every set's band from the published per-language bands
alone and checks it against the recorded score, for every set on the roster.

## Stale category comments (#1092)

`language_specific_datasets` no longer describes its top rung as evaluation sets, which moved out
on 2026-11-08. Its distribution is now the category's own on 2026-11-17: 77 banded, 13 at 4, 31 at
3, 21 at 2, 12 at 1, none at 5.

## Model hosts (#1093)

Ruling R-2026-11-17-c replaces R-2026-10-12-a: a host is a product in `inference_code` when it is
a distinct public service, with its own endpoint, documentation and terms, that serves more than
one model. The SEA-LION API meets the test (four models documented, a free tier under AI
Singapore's terms). ADR-005 places it in the tail: openness 1 and capability 2. #1093 recorded
adoption as abstaining for want of a usage figure, but AI Singapore's models page reports "180k +
Monthly API endpoint calls", a vendor figure that would read as reported traction at a low level.
At capability 2, with adoption and capability weighted equally, no adoption level reaches the line
of 4, so the placement stands (#1095). LLMLab does not clearly qualify, since it
is open only to PLGrid grant holders. SEA-Guard and the SEA-LION ModernBERT and E5 embedding models
join the tail as candidates.

## Score changes

| Product | Axis | Before | After | PR |
|---|---|---|---|---|
| SEA-HELM | capability | 2 | 3 | #1091 |
| Kalahi (proposed) | openness / adoption / capability | | 5 / 1 / 2 | #1094 |
| LINDSEA (proposed) | openness / adoption / capability | | 3 / 2 / 2 | #1094 |
| SEA-IFEval (proposed) | openness / adoption / capability | | 3 / 2 / 2 | #1094 |
| SEA-MTBench (proposed) | openness / adoption / capability | | 3 / 1 / 1 | #1094 |

The four member rows wait on a membership ruling for the eval-set roster, so their figures are
proposed until #1094 merges.

The SEA-LION API, SEA-Guard and the embedding model are unscored tail rows. The new rows'
adoption levels are held until the weekly reconciliation measures them.
