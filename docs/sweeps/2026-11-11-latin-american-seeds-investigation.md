# Latin American seeds: Indigenous-language content, 2026-11-11

## Scope

The 2026-11-10 membership review left three CENIA seeds undecided: CHOCLO, the Trueque Benchmark and
the LatamGPT Corpus. All three target Spanish or Portuguese. Both languages are high at both ends of
their class, so on their declared languages the seeds fail the language half. The maintainer
deferred the decision until each seed's Indigenous-language content was checked, and ruled that
incidental coverage of an Indigenous language does not satisfy the purpose test (R-2026-11-11-f).

This record reports that check, and the maintainer's decision on it (R-2026-11-11-f, now in force):
all three stay out. **Nothing moves on it.** No registry row, roster or score changes.

## The test

A seed counts as having Indigenous-language content when its items or documents are **in** an
Indigenous language, and that content is part of what the set was built to cover. A Spanish question
about an Indigenous people, or one that asks what a single Quechua or Guaraní word means, is content
**about** Indigenous peoples, written in Spanish. That is the incidental coverage R-2026-11-11-f
excludes.

## Sources

Every source was read on 2026-11-11 with `uv run python -m build.fetch_source`. The two benchmarks'
files are pinned to the Hub revision that was current that day; fetching the pinned URL reproduces
the same bytes.

| Seed | Hub revision | Files read |
|---|---|---|
| CHOCLO | [`adf4dd55ec7a74ecb6d5b686c796c7ef23b7830a`](https://huggingface.co/datasets/latam-gpt/CHOCLO/tree/adf4dd55ec7a74ecb6d5b686c796c7ef23b7830a) | [card](https://huggingface.co/datasets/latam-gpt/CHOCLO/raw/adf4dd55ec7a74ecb6d5b686c796c7ef23b7830a/README.md) (sha256 `88de486a461a0611…`); [`BenchmarkCHOCLO.csv`](https://huggingface.co/datasets/latam-gpt/CHOCLO/resolve/adf4dd55ec7a74ecb6d5b686c796c7ef23b7830a/BenchmarkCHOCLO.csv) (sha256 `d19660868a14a8ee…`); [API record](https://huggingface.co/api/datasets/latam-gpt/CHOCLO); [row counts](https://datasets-server.huggingface.co/size?dataset=latam-gpt/CHOCLO) |
| Trueque Benchmark beta 0.1 | [`cbda7fd90a9b1b0cec91537a878faa0a4ef4b466`](https://huggingface.co/datasets/latam-gpt/Trueque-Benchmark-beta-0.1/tree/cbda7fd90a9b1b0cec91537a878faa0a4ef4b466) | [card](https://huggingface.co/datasets/latam-gpt/Trueque-Benchmark-beta-0.1/raw/cbda7fd90a9b1b0cec91537a878faa0a4ef4b466/README.md) (sha256 `9314efdde910cf6a…`); [`data/trueque_benchmark_beta_0_1.csv`](https://huggingface.co/datasets/latam-gpt/Trueque-Benchmark-beta-0.1/resolve/cbda7fd90a9b1b0cec91537a878faa0a4ef4b466/data/trueque_benchmark_beta_0_1.csv) (sha256 `f10568d5a4a74827…`); [API record](https://huggingface.co/api/datasets/latam-gpt/Trueque-Benchmark-beta-0.1); [row counts](https://datasets-server.huggingface.co/size?dataset=latam-gpt/Trueque-Benchmark-beta-0.1) |
| LatamGPT Corpus 1.0 | `f29566d17128a96b9e172a156b0d8c92fe24b8d4`, per the [API record](https://huggingface.co/api/datasets/latam-gpt/LatamGPT-Corpus-1.0) | the [Hub page](https://huggingface.co/datasets/latam-gpt/LatamGPT-Corpus-1.0), which renders the card (sha256 `c77c56b027e4f98f…`); the API record, including its gating terms; the [project dashboard](https://www.latamgpt.org/dashboard). The raw card, the data files and the datasets server returned 401 without accepting the terms, which this check did not do. |

## How the counts were made

Each count is a regular expression over the pinned CSV, case-insensitive, matched as Python `re`
patterns. `NAMES` stands for `quechua|kichwa|guaran[ií]|mapudungun|n[aá]huatl|aymara|maya|ta[ií]no`.

| Count | Field | Pattern |
|---|---|---|
| Mentions an Indigenous people, language or term | CHOCLO `Question` and `Answer` | `\b(?:NAMES\|mapuche\|ind[ií]gena\|originari[oa]s?)\b` |
| Asks about a word in an Indigenous language | CHOCLO `Question` | `\ben (?:(?:la )?(?:lengua\|idioma) )?(?:NAMES)\b` or `\ben (?:la )?(?:lengua\|idioma) ind[ií]gena\b` |
| Tagged as about Indigenous peoples or languages | Trueque `topic` | contains `Pueblos-Originarios`, or contains `Dialectos-y-Lenguas` |

The language of each item was checked in two passes:
1. **Function words.** An item counts as Spanish or Portuguese when it holds more of one language's
   function words than the other's.
   - Spanish: `el la los las al lo su de del que en y es un una por para con se qué cuál cuáles
     quién cómo dónde cuándo`.
   - Portuguese: `os as de do da que em e é um uma por para com se qual quais quem como onde quando
     no na`.
   - Words on both lists are ignored.
2. **The rest.** For each item the first pass left undecided:
   - CHOCLO: the question was checked for a Spanish interrogative (`qué`, `cuál`, `cuánto`,
     `quién`, `cómo`, `dónde`, `cuándo`, `según`, `por qué`, accents optional).
   - Trueque: the question and answer were read by hand.

The patterns are a screen for this decision. They are not a language-identification method for the
map.

## Findings

| Seed | Registry | Declared languages | Language of the items | Indigenous content | Finding |
|---|---|---|---|---|---|
| CHOCLO | `benchmark_eval_data` | `es` | Spanish: all 104,847 questions | 1,596 items mention an Indigenous people, language or term; 139 questions ask about a word in an Indigenous language, in Spanish | Incidental |
| Trueque Benchmark (beta 0.1) | `benchmark_eval_data` | `es`, `pt` | Spanish and Portuguese: all 500 questions and answers | 228 questions tagged `Pueblos-Originarios` (128) or `Dialectos-y-Lenguas` (118), all in Spanish or Portuguese | Incidental |
| LatamGPT Corpus 1.0 | `training_synthetic_datasets` | `es`, `pt`, `en` | Spanish, Portuguese and English, per the card | No Indigenous-language target is documented. "Indigenous Peoples" is a topic label. | No documented qualifying coverage |

### CHOCLO

- **Construction.** The card describes a cultural-knowledge benchmark about entities from 18 Latin
  American countries:
  - GPT-3.5 generated knowledge triplets from Wikipedia and Wikidata, then question-answer pairs
    from the triplets.
  - "both triplets and questions are subjected to human validation".
- **Language.** The metadata declares `es` only.
  - The first pass classed 104,497 of the 104,847 questions as Spanish and 7 as Portuguese. The
    rest were undecided.
  - All 350 questions not classed Spanish contain a Spanish interrogative. No question is in
    another language.
  - 104,837 open with `¿`; the other 10 open with `Según`.
- **Indigenous content.**
  - 1,596 items mention an Indigenous people, language or term.
  - 139 questions ask about a word in an Indigenous language, for example `¿Qué significa "balam"
    en lengua maya?`, answered in Spanish.
  - These test knowledge about Indigenous culture in Spanish, not ability in an Indigenous
    language.

### Trueque Benchmark

- **Construction.** The card describes a human-contributed benchmark of Latin American knowledge and
  culture across 20 countries. Beta 0.1 holds 500 questions; a full release of more than 3,000 is
  planned.
- **Language.** The metadata declares `es` and `pt`, and the contribution form is in Spanish only.
  - The first pass classed 459 questions as Spanish and 31 as Portuguese, and 457 answers as Spanish
    and 36 as Portuguese.
  - The 17 rows it left undecided in either field were read by hand. All are Spanish or
    Portuguese.
  - Two of those have one-word answers that are words of Indigenous origin, "Xocomil" and
    "Serra", to Spanish questions.
- **Indigenous content.**
  - 128 questions are tagged `Pueblos-Originarios` and 118 `Dialectos-y-Lenguas`; 228 carry
    either tag.
  - They are about Indigenous peoples and the languages spoken in the region, for example
    "¿Cúantas lenguas indígenas reconocidas existen en Bolivia?" (sic) and "¿Cómo se llamaba el
    trueque en lengua taína?".

### LatamGPT Corpus 1.0

- **Access.** The repository is gated with automatic approval. This check did not accept the terms,
  so it read none of the corpus's text. Its finding rests on what the project publishes.
- **Language.**
  - The card says the corpus "contains text in Spanish, Portuguese, and English associated with
    Latin America and the Caribbean".
  - It lists "Spanish, Portuguese, and English" as the languages represented in the open release.
  - Its schema documents `language` as "Detected language (`spanish`, `portuguese`, `english`)".
- **Indigenous content.**
  - "Indigenous Peoples" is one of ten topic labels. The card says it has "lower coverage in this
    corpus version", and its example record under that label is a Spanish text about Mexican
    legends.
  - The dashboard renders its statistics in the browser, and the served page carries no language
    breakdown.
- **What this establishes.**
  - It establishes that no qualifying Indigenous-language coverage is documented.
  - It does not establish that the corpus holds no Indigenous-language text. The card's detector
    labels only the three declared languages, so such text, if present, would not show in its
    statistics. Only a scan of the gated data would settle that.
- **Separate finding (openness).** The terms require CENIA's prior written authorization for
  entities above USD 1 billion in revenue or capital. The card itself says this keeps the
  compilation from qualifying as open data under the Open Definition. This matters for scoring if
  the corpus is ever promoted, not for membership.

## Decision (2026-11-11)

The maintainer decided that all three stay outside the language-specific categories
(R-2026-11-11-f).
- CHOCLO and Trueque are out: they are Spanish and Portuguese benchmarks about regional culture,
  including Indigenous peoples, not Indigenous-language evaluation sets.
- The LatamGPT Corpus is out provisionally: its published release declares Spanish, Portuguese and
  English and no Indigenous-language target.

Concretely:
- CHOCLO and the Trueque Benchmark keep their rows in `sources/registry/benchmark_eval_data.yaml`.
- The LatamGPT Corpus keeps its row in `sources/registry/training_synthetic_datasets.yaml`.
- No product or score changes.

**Conditions for reconsideration.** Any of these reopens a seed:
- a Trueque release that collects or evaluates questions written in an Indigenous language;
- a CHOCLO release that adds items in an Indigenous language;
- a LatamGPT Corpus version, card or dashboard that documents Indigenous-language text as a target
  or reports a language breakdown that includes one;
- a scan of the gated LatamGPT data that finds Indigenous-language text present by design rather
  than incidentally.
