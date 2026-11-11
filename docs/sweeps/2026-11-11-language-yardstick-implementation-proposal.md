# Language yardstick implementation proposal, 2026-11-11

## Scope

This is the scored implementation proposal R-2026-11-11-g asks for. It follows the sensitivity
analysis in [`2026-11-11-language-yardstick-dry-run.md`](2026-11-11-language-yardstick-dry-run.md).
That analysis reported only upper bounds, because no record states its band before the size cap.
This proposal scores that pre-cap rung band for every product whose band could rise. A real band is
then the lower of its rung band and its new cap, as the recipe defines.

It also resolves what the eight set-aside products block.

**Nothing changes on it.** No capability band, recipe or peer relation is edited, and #951 stays
held. The leading candidate is S3 with M2 (R-2026-11-11-g). The other schemes are shown for
comparison.

## How the rungs were scored

The rungs are the ones in the `scoring_recipe` of `language_specific_datasets`:

| Rung | Facts it needs |
|---|---|
| 5 | Documented; the publisher or a paper names a model or benchmark built on it; no other open row here covers the same languages in the same modality at comparable scale |
| 4 | Documented and used downstream by name, but a peer here is larger or broader for the same languages; or the largest for its languages with only community fine-tunes listed on the Hub. A single-task set tops out at 4 |
| 3 | Documented, with no downstream model or benchmark beyond its own paper's experiments; or superseded by the publisher's newer release; or a narrow single-task set |
| 2 | Thin documentation, or machine-generated, machine-translated or re-hosted content |
| 1 | A fragment |

**Which products.** Each rung band is read from the facts the product's own record cites in its
capability `value`, `note` and `sources` on `main`. Only the 21 products whose band could rise under
some scheme or rule are scored. The caps only relax, so no other product's band can change.

**Alternative readings.** Where a record supports two readings, the second is shown as an
alternative and carried through. The usual case is a card without a paper, or Hub-listed community
fine-tunes counted as downstream use.

**Applying the result.** A band never falls below today's under a relaxed cap.

## Rung bands

| Product | Rung | Alternative | Facts from the record |
|---|---|---|---|
| CorpusNós | 5 | none | PROPOR paper and card; the publisher, Proxecto Nós, trained Carballo and Carvalho on it; the only Galician pretraining row |
| Korpus Malti | 5 | none | Paper with per-subset sizes; its authors trained BERTu and mBERTu on it; the only Maltese row |
| Latxa Corpus | 5 | none | ACL paper and cards; the publisher, HiTZ, trained every Latxa model on it; the only Basque pretraining row |
| Icelandic Gigaword Corpus | 4 | 3 | Detailed homepage and card, no paper; the largest Icelandic corpus; only a community model lists it. Read as documentation with no named use: 3 |
| Kazakh Speech Corpus 2 | 4 | 3 | Interspeech paper; the largest open Kazakh speech; community Whisper fine-tunes on the Hub. Without counting Hub-listed fine-tunes: 3 |
| Khmer ASR Cultural Dataset | 4 | 2 | Detailed card, no paper; the largest Khmer speech; community Qwen3-ASR and Whisper models. Card read as thin documentation: 2 |
| Nepali Text Corpus | 4 | 5 | Paper and short card; the publisher's BERT, RoBERTa and GPT-2 are trained on it; Sangraha is larger for Nepali |
| Northern Sámi web corpus | 2 | 4 | Short card, no paper (thin); TurkuNLP's Finnish ModernBERT lists it, and it is the only Northern Sámi row. Card read as adequate: 4 |
| ViXSD | 3 | none | Paper and detailed card; no use beyond its own paper |
| Llamacha monolingual Quechua corpus | 3 | 2 | DeepLo paper and a mostly template card; only its authors' own models |
| ZA African Next Voices | 5 | 4 | Paper and card; the publishers' Whisper models; more than any other open set for these languages |
| AfriVoices-KE | 4 | none | Paper, no full card; community models; the largest for its Kenyan languages |
| NaijaVoices | 4 | none | Paper and card; community recognizers; its record names Afrivoice as its peer |
| WAXAL | 4 | none | Paper and card; community Ethio-ASR; Afrivoice holds more for many of the same languages |
| Bharat Parallel Corpus Collection | 5 | none | TMLR paper; the builders' IndicTrans2; the largest English-Indic parallel corpus |
| Pralekha | 3 | none | Paper and card; no use beyond its paper |
| Aksharantar | 4 | none | Single-task set (transliteration), which tops out at 4; the builders' IndicXlit |
| ChrEn | 3 | none | EMNLP paper; no use beyond the paper and its authors' demo |
| Jojajovai | 3 | 2 | README documents each source, no paper; no named use |
| Vuk'uzenzele corpus | 4 | 5 | Paper; the publisher's PuoBERTa; SMOL and OLDI Seed are broader for several of the same languages |
| OLDI Seed | 4 | 1 | NLLB paper and card; part of NLLB-200's training data; SMOL is broader. As a seed set it could be read as a fragment |

## Proposed bands under S3 with M2

Under the leading candidate, **nine products rise and no rung band holds any of them below its new
cap**. Every rise the sensitivity analysis projected is real at the scored rungs.

| Product | Profile | Today | New cap | Rung | Proposed band | With the alternative rung |
|---|---|---|---|---|---|---|
| Icelandic Gigaword Corpus | `isl` Y/N/N | 2 | 4 | 4 | **4** | 3 |
| Korpus Malti | `mlt` Y/N/N | 1 | 3 | 5 | **3** | 3 |
| CorpusNós | `glg` Y/Y/N | 2 | 3 | 5 | **3** | 3 |
| Latxa Corpus | `eus` Y/U/N | 2 | 3 (to 4) | 5 | **3** (to 4) | 3 (to 4) |
| Nepali Text Corpus | `nep` Y/Y/N | 2 | 3 | 4 | **3** | 3 |
| Khmer ASR Cultural Dataset | `khm` Y/Y/N | 2 | 3 | 4 | **3** | 2 |
| Kazakh Speech Corpus 2 | `kaz` Y/Y/N | 3 | 4 | 4 | **4** | 3 |
| Northern Sámi web corpus | `sme` Y/N/N | 1 | 2 | 2 | **2** | 2 |
| ViXSD | `xho` Y/Y/N | 1 | 2 | 3 | **2** | 2 |

- **Profiles.** A profile reads official / many speakers / large written material, with U for
  unresolved.
- **Latxa's range.** It comes from Basque's unresolved speaker axis. The applied band is the least
  relaxed, 3.
- **The alternative readings matter for three products.** Read the other way:
  - Kazakh Speech Corpus 2 and the Khmer dataset do not rise.
  - The Icelandic Gigaword Corpus rises one band instead of two.
- **No other product moves under S3 with M2.** The 12 other products scored above stay where they
  are.

### Under the other schemes and rules

The rungs bind in five places outside the leading candidate, two of them only at the most relaxed
end of a range:

| Product | Cell | New cap | Rung | Band |
|---|---|---|---|---|
| Icelandic Gigaword Corpus | S2, any rule | 5 | 4 | 4 |
| Northern Sámi web corpus | S2, any rule | 3 | 2 | 2 |
| ChrEn | S2 with M3 | 3 (to 4) | 3 | 3 (the range closes) |
| Pralekha | S2 with M3 | 4 | 3 | 3 |
| Aksharantar | S2 with M3 | 3 (to 5) | 4 | 3 (to 4) |

S4 with M2 gives five rises of one band each:
- Icelandic Gigaword Corpus, to 3;
- Korpus Malti, to 2;
- Latxa Corpus, to 3;
- Nepali Text Corpus, to 3;
- Khmer ASR Cultural Dataset, to 3.

The rungs bind none of them.

## Peer relations under S3 with M2

With the scored bands, **nine relations break**. They are now demonstrated at the scored rungs, not
only projected. With the alternative rung readings, seven break.

| Product | Recorded relation | Peer | Proposed bands (product vs peer) |
|---|---|---|---|
| Icelandic Gigaword Corpus | `at` | Danish Dynaword | 4 vs 2 |
| Korpus Malti | `one_below` | Danish Dynaword | 3 vs 2 |
| Northern Sámi web corpus | `one_below` | Danish Dynaword | 2 vs 2 |
| SMUGRI data | `at` | Northern Sámi web corpus | 1 vs 2 |
| Nepali Text Corpus | `two_below` | Sangraha | 3 vs 4 |
| Khmer ASR Cultural Dataset | `two_below` | IndicVoices | 3 vs 4 |
| Kazakh Speech Corpus 2 | `one_below` | IndicVoices | 4 vs 4 |
| ViXSD | `one_below` | BibleTTS | 2 vs 2 |
| L3Cube-MahaCorpus | `one_below` | Latxa Corpus | 1 vs 3 |

In each row the two sides now sit on different yardsticks:
- Danish Dynaword (Danish) keeps the reference yardstick.
- Sangraha, IndicVoices and BibleTTS are multilingual and keep today's yardstick under M2.
- L3Cube-MahaCorpus (Marathi, the reference profile) stays put while its peer Latxa moves.
- SMUGRI data is multilingual and stays put while its peer moves.

**Proposal.** In the implementation PR, each mover's `relative_to` names a same-modality peer judged
on the same yardstick, where one exists. Otherwise its band is a root and carries no `relative_to`,
as the recipe allows. The relations into a mover, SMUGRI's and L3Cube-MahaCorpus's, are re-attested
against the mover's new band or re-pointed.

## The five IIT Bombay comparisons

Under M2, English and Hindi keep IIT Bombay English-Hindi at 2, and the parallel corpora are
multilingual, so none moves:
- ChrEn, Jojajovai and OLDI Seed stay one below IIT Bombay. Those three comparisons hold.
- SMOL and AfriDocMT still state no pair total, so their comparisons stay provisional
  (R-2026-11-08-d).

## The eight set-aside products

**All eight are multilingual**, declaring from 5 to 489 languages. Under M2 every multilingual
product keeps today's yardstick, so none of the eight can move under the leading candidate, whatever
its size. They block adoption only of M1 or M3.

The size research on 2026-11-11 found, for each:

| Product | Cap unit | What a primary source states | Band that gives | Recorded |
|---|---|---|---|---|
| SMOL | pairs | SmolSent 76k sentence pairs; SmolDoc in documents only; no pair total | 1 on every stated figure | 1 |
| Bloom Library | tokens | No token count; about 43 MB of text files | 1 | 1 |
| Glot500-c | tokens | Paper: 600 GB corpus; public release: 308 GB | 4 (paper) or 3 (release) | 3 |
| BibleTTS | transcribed hours | Per language only, each under 100 h; no total | none stated | 2 |
| Kencorpus | tokens and transcribed hours | 5,601,915 words; 176.5 h of audio with no transcription stated; 27.5 transcribed hours in KenSpeech | 1 (text), 1 (transcribed speech) | 2 |
| AfriDocMT | pairs | 10k English sentences per domain, six-way parallel; no pair total | 1 on every stated figure | 1 |
| SMUGRI data | tokens | 129,863 one-sentence rows; no token or word count | 1 on any reading | 1 |
| Afrivoice | transcribed hours | Per release: 3,155.64, 3,096.87, 2,421.29 and 414.42; no product total; "15,000 hours" appears on no card | 3 per release | 3 |

Five of these do not support the recorded figure or band as it stands, apart from any yardstick:

- **Glot500-c.** The cap depends on whether it measures the full corpus or the redistributable
  release.
- **Kencorpus.** Its 2 holds only if untranscribed audio counts, and the recipe does not say which
  modality governs a mixed corpus.
- **BibleTTS.** Its 2 has no stated total of at least 100 transcribed hours behind it.
- **Bloom Library.** Its speech figure conflicts within its own paper: 428 hours in the prose,
  2,873 minutes in Table 1.
- **Afrivoice.** Its record's "15,000 hours" appears on no source card.

These are record-accuracy questions for a `refresh-category` pass on `language_specific_datasets`.
This proposal changes none of them.

## What an implementation PR would change

If S3 with M2 is adopted:

1. **Recipe note in `sources/categories/language_specific_datasets.yaml`.** It would state:
   - the multipliers, keyed on the resource profile in the classification table;
   - the reference profile, which stays unrelaxed;
   - M2;
   - the least-relaxed rule for unresolved profiles;
   - the dependency on `currentai.language_representation.classification`.
2. **Nine capability blocks:** the scores above, with each `value` and `note` stating the profile,
   the yardstick and the rung facts. The alternative readings are settled first.
3. **Peer relations.** The nine relations above are re-pointed or re-attested.
4. **The dry-run record.** Its three size labels are corrected in this PR (see below).
5. **A ruling** recording the adoption, and a score-change diff for review.

## Correction to the dry-run record

The sensitivity analysis showed three byte-sized corpora's token estimates under a "bytes" label:
Nepali Text Corpus, the Llamacha Quechua corpus and the Northern Sámi web corpus. This PR relabels
them, for example "27.5 GB (about 6.9B tokens, estimated)". The bands it computed were correct.

## Decisions (2026-11-11)

The maintainer ruled on all five (R-2026-11-11-h to -m). This record is the decision record; the
changes are made in a separate implementation PR.

1. **S3 with M2 is adopted as scoring policy (R-2026-11-11-h).**
   - Multipliers, keyed on the number of confirmed `yes` axes (three, two, one, none):
     - text and parallel text: 1×, 10×, 100×, 1,000×;
     - speech: 1×, 10×, 30×, 100×.
   - Unresolved axes earn no relaxation.
   - Multilingual products keep today's caps.
   - The nine bands in the table above are approved. Latxa Corpus publishes 3, the least-relaxed
     score, and keeps its range to 4 in the evidence.
2. **The three contested rung readings are 4 (R-2026-11-11-i):** Icelandic Gigaword Corpus, Kazakh
   Speech Corpus 2 and the Khmer ASR Cultural Dataset.
   - A paper is not required for a documented resource.
   - A community fine-tune is legitimate downstream use when its attribution to the dataset is
     explicit and verifiable. A generic Hugging Face tag alone is not enough.
3. **Peer relations (R-2026-11-11-j).** Each of the nine is re-pointed to a same-modality,
   same-yardstick peer where a defensible comparison exists. Otherwise `relative_to` is removed and
   the band is justified from the rubric directly. Weak comparisons are not invented. Outgoing
   relations and references from other products, including SMUGRI data and L3Cube-MahaCorpus, are
   both checked.
4. **The eight set-aside products do not block S3 with M2 (R-2026-11-11-k).** Their five
   source-accuracy questions go to a separate re-verification pass. This does not approve their
   current recorded sizes or bands.
5. **Glot500-c's cap reads the 308 GB public release, not the 600 GB assembled corpus
   (R-2026-11-11-l).** The full corpus is context only.

The maintainer also lifted the hold on #951 for revision against the adopted yardsticks
(R-2026-11-11-m).
