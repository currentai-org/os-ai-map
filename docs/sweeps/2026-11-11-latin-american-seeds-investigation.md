# Latin American seeds: Indigenous-language content, 2026-11-11

## Scope

The 2026-11-10 membership review left three CENIA seeds undecided: CHOCLO, the Trueque Benchmark and
the LatamGPT Corpus. All three target Spanish or Portuguese. Both languages are high at both ends of
their class, so on their declared languages the seeds fail the language half. The maintainer
deferred the decision until each seed's Indigenous-language content was checked, and ruled that
incidental coverage of an Indigenous language does not satisfy the purpose test (R-2026-11-11-f).

This record reports that check. **Nothing moves on it.** The maintainer decides; if the seeds stay
out, R-2026-11-11-f is recorded as decided and their registry rows stay where they are.

## The test

A seed counts as having Indigenous-language content when its items or documents are **in** an
Indigenous language, and that content is part of what the set was built to cover. A Spanish question
about an Indigenous people, or one that asks what a single Quechua or Guaraní word means, is content
**about** Indigenous peoples, written in Spanish. That is the incidental coverage R-2026-11-11-f
excludes.

## Findings

Every source below was read on 2026-11-11: the Hugging Face API record, the dataset card, the
datasets server, and for the two benchmarks the full data file.

| Seed | Registry | Declared languages | Language of the items | Indigenous-language content | Finding |
|---|---|---|---|---|---|
| CHOCLO | `benchmark_eval_data` | `es` | Spanish: 104,847 questions | None in an Indigenous language. 122 questions ask what a word means in Guaraní, Maya, Quechua or another Indigenous language, and answer in Spanish. | Incidental |
| Trueque Benchmark (beta 0.1) | `benchmark_eval_data` | `es`, `pt` | Spanish and Portuguese: 500 questions | None in an Indigenous language. 128 questions are tagged `Pueblos-Originarios`, and all are asked and answered in Spanish or Portuguese. | Incidental |
| LatamGPT Corpus 1.0 | `training_synthetic_datasets` | `es`, `pt`, `en` | Spanish, Portuguese and English. The card's `language` field takes only those three values. | None stated. "Indigenous Peoples" is one of ten topic labels, and the card says it has "lower coverage in this corpus version". | Incidental, as documented |

### CHOCLO

- **Construction.** The card describes a cultural-knowledge benchmark about entities from 18 Latin
  American countries. GPT-3.5 generated the questions from Wikipedia and Wikidata, and people
  validated them afterward.
- **Language.** The metadata declares `es` only, and the data file holds 104,847 Spanish questions.
- **Indigenous content.**
  - 1,551 questions mention an Indigenous people, language or term.
  - 122 have the form "what does X mean in Guaraní, Maya, Quechua…", for example `¿Qué significa
    "balam" en lengua maya?`, answered in Spanish.
  - These test knowledge about Indigenous culture in Spanish, not ability in an Indigenous language.

### Trueque Benchmark

- **Construction.** The card describes a human-contributed benchmark of Latin American knowledge
  and culture across 20 countries. Beta 0.1 holds 500 questions; a full release of more than 3,000
  is planned.
- **Language.** The metadata declares `es` and `pt`. The contribution form is in Spanish only.
- **Indigenous content.**
  - The topic labels include `Pueblos-Originarios` (128 questions) and `Dialectos-y-Lenguas`
    (118).
  - Those questions are about Indigenous peoples and the languages spoken in the region, for
    example "¿Cúantas lenguas indígenas reconocidas existen en Bolivia?" (sic) and "¿Cómo se llamaba el
    trueque en lengua taína?". Every one is in Spanish or Portuguese.

### LatamGPT Corpus 1.0

- **Access.** The repository is gated with automatic approval: the card loads on the Hub page,
  but the raw card file and the datasets server return 401 without accepting the terms. The figures
  here come from the Hub page, the API record and the card's own tables. No data was downloaded.
- **Language.** The card says the corpus "contains text in Spanish, Portuguese, and English
  associated with Latin America and the Caribbean". Its schema documents `language` as "Detected
  language (`spanish`, `portuguese`, `english`)".
- **Indigenous content.**
  - "Indigenous Peoples" is a topic label. The card's example record under it is a Spanish text
    about Mexican legends.
  - The card states that Indigenous Peoples has "lower coverage in this corpus version".
- **Limits of this check.** The project dashboard at latamgpt.org/dashboard renders its statistics
  in the browser, and its served page contains no language breakdown. The card's language
  detector recognizes only the three declared languages, so it cannot show Indigenous-language
  text even if some exists. On the evidence published, though, nothing presents Indigenous-language
  text as part of the corpus.
- **Separate finding (openness).** The terms require prior written authorization from CENIA for
  entities above USD 1 billion in revenue or capital. The card says itself that this keeps the
  compilation from qualifying as open data under the Open Definition. This matters for scoring
  if the corpus is ever promoted, and not for membership.

## Proposed decision

All three stay out of the language categories. None carries content in an Indigenous language;
what each has is content about Indigenous peoples, written in Spanish or Portuguese, which
R-2026-11-11-f rules incidental. Concretely:

- CHOCLO and the Trueque Benchmark keep their rows in `sources/registry/benchmark_eval_data.yaml`.
- The LatamGPT Corpus keeps its row in `sources/registry/training_synthetic_datasets.yaml`.
- R-2026-11-11-f moves from deferred to decided.

**What would reopen it.** Any of these would change the finding, and the quarterly
re-classification would catch them:

- a later Trueque release that collects questions in an Indigenous language;
- a LatamGPT Corpus version that declares Indigenous-language text;
- a published language breakdown on the corpus dashboard.
