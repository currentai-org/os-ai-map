# AfroBench under the suite rules, 2026-11-18

Issue #1098 asked for AfroBench to be read under the same coverage, provenance and membership rules
that #1091 and #1094 applied to SEA-HELM. This record covers the coverage and provenance pass. No
scoring rule changed; where a rule left a question open, it is listed at the end rather than
settled here.

## What was read

- **What the suite runs.** AfroBench's own task configurations in `McGill-NLP/AfroBench`
  (`prompt_with_API/afrobench_tasks/*.yaml`), one per dataset, each naming the Hugging Face dataset,
  the test split and the language configurations it evaluates. Main's record was built from the
  paper's Table 2 and Table 11, which mark fewer languages than the configurations run.
- **What each member publishes.** The Hub's split metadata (`datasets-server /size` or the card's
  `dataset_info`), and the data files themselves for the two members whose loaders read from GitHub
  (MAFAND-MT and AfriQA). Where a paper's figure and the data disagree, the data wins
  (R-2026-11-02-a).
- **How the items were made.** The full papers this time, not only the cards and abstracts the
  2026-11-01 calibration read: MAFAND-MT (arXiv 2205.02022), MasakhaPOS (2305.13989), MasakhaNEWS
  (2304.09972), AfriSenti (2302.08956), AfriQA (2305.06897), IrokoBench (2406.03368), NollySenti
  (2305.10971), MasakhaNER (2103.11811) and MasakhaNER 2.0 (2210.12391), AfriHate (2501.08284),
  NaijaRC (2308.09768) and XL-Sum (2106.13822), plus SALT's card, site and README.

Every citation added to `sources/scores/afrobench.yaml` and `sources/lineage.yaml` was fetched with
`build.fetch_source` and carries its digest. All 20 of the record's older capability sources were
re-fetched too. Fifteen returned the same bytes. Five changed (three Hugging Face card pages, the
MAFAND card and the InjongoIntent abstract), and each still says what it is cited for, so they carry
the new digest and today's date.

## Provenance: 14 of the 62 unresolved entries resolved

| Component | Unresolved before | Resolved | Still `unknown` | What decides it |
|---|---|---|---|---|
| AfriADR (`afrobench`) | 5 | 3 (bbj, fon, wol) | 2 (ibo, yor) | AfroBench made AfriADR from MAFAND-MT's sentences ("we selected the five languages with extensive use of diacritics from Mafand MT dataset"). For eleven languages MAFAND-MT's own creation step 2 was "Translation of 5k–8k sentences by professional translators", from French news in Ghomálá', Fon and Wolof. MAFAND took its Igbo and Yorùbá from existing corpora (Ezeani et al. 2020, MENYO-20k) and does not say who translated them. |
| MasakhaPOS | 20 | 11 (bam, bbj, ewe, fon, lug, luo, mos, pcm, tsn, twi, wol) | 9 | Its Table 1 gives "MAFAND-MT" as the source for those eleven, so their text is MAFAND's professional translation. For the other nine the paper says "We collected monolingual news corpus with an open license for about eight African languages, mostly from local newspapers", which names a genre and a source, not how the text came to be in the language. |
| AfriSenti | 14 | 0 | 14 | The paper describes collecting tweets through the Twitter API by location and keyword lists, with native speakers checking the language and annotating. It never states the tweets are original text written in the language, so the "native" reading in `docs/reference/capability.md` is not met. Question 1 below. |
| MasakhaNEWS | 14 | 0 | 14 | "The collection process involved crawling the British Broadcasting Corporation (BBC) and Voice of America (VOA) websites." The card's "The source language was produced by journalists and writers employed by the news agency" says people wrote it, not that they wrote it in the language. Unchanged from the 2026-11-01 reading. |
| SALT | 7 | 0 | 7 | The card and site say every sentence "is translated into all languages" and never say by whom. The paper (Akera et al., AfricaNLP 2022) is on OpenReview, which refuses automated fetches (HTTP 403), so it could not be read or cited. A Makerere Applied AI Letters paper in the Ugandan national repository describes professional translators, but for a different 40,000-sentence corpus that includes Lumasaba, so it is not SALT's evidence. |
| MasakhaNER-X | 2 | 0 | 2 | MasakhaNER's Table 2 gives "DW & BBC" for Amharic and "Ramogi FM news" for Luo, with "Our data was obtained from local news sources". A source, not a statement about how the text was written. |
| **Total** | **62** | **14** | **48** | |

One entry moved the other way. AfroBench's Swahili AfriXNLI entry was recorded `human_translated` on
IrokoBench's abstract, but IrokoBench's text says it translated XNLI "into the 15 African languages
(excluding Swahili)": its Swahili items are XNLI's own. XNLI's paper says professional translators
translated it "into our ten target languages" while listing fourteen, so whether its Swahili is among
them is not stated, and the entry is now `unknown`. Its Swahili AfriMGSM entry keeps
`human_translated`, now cited to MGSM's paper, which says paid professional translators translated
each of its languages; IrokoBench says that Swahili set is MGSM's. Swahili stays at 5 through OpenAI's
MMMLU. That brings the unresolved count to 49.

The MasakhaPOS resolutions move no band, since part-of-speech tagging has no measurement model.
The AfriADR ones do: AfriADR is AfroBench's own task, so it counts in full, and it puts Ghomálá'
(previously unmeasured) and Fon at 3.

The MasakhaNER source also settles a lineage gap the 2026-11-02 audit left open. MasakhaNER's Luo
came from Ramogi FM, not from MAFAND-MT's Lolwe and Standard Media sources, so it does not overlap
MAFAND-MT. The registry record is unchanged, since the effort is still unknown and the entry has no
band either way.

## Coverage: 40 entries added

| Component | Languages added | Count | Provenance | Why it was missing |
|---|---|---|---|---|
| MAFAND-MT (`mafand-mt`, new) | bam, bbj, ewe, fon, lug, luo, mos, pcm, tsn, twi, wol | 1,430 to 1,579 test sentences | human_translated (MAFAND-MT, as above) | Dropped by the 2026-11-01 calibration because AfroBench's Table 2 total and the repository disagreed. The `mafand` task config runs 21 pairs on the `test` split. Bambara's test file holds 1,500 pairs where the paper's Table 1 says 1,600; the record takes the file. |
| AfriQA (`afriqa`, new) | bem, fon, hau, ibo, kin, swa, twi, yor, zul | 254 to 486 test questions | native: "1) question elicitation in an African language" by "a team of 2–6 native speakers"; Swahili reuses TyDi QA's elicited questions | Dropped for the same reason as MAFAND-MT. The counts are the gold-passage test files the loader reads, which differ from the card's table for Bemba, Swahili, Twi and Yorùbá. The context passages are English or French; question 2 below. |
| Belebele | fuv, kea, kin, lug, luo, nya, orm (source `gaz`), plt, som, sot, ssw, tsn | 900 test questions | human_translated, as in the existing Belebele entries | The `belebele` config runs 28 African languages; Table 11 marked 16. |
| SIB-200 | afr, sot, taq | 204 test sentences | human_translated | In the `sib` config, not marked in Table 11. |
| FLORES+ | fuv, tso | 1,012 devtest sentences | human_translated | In the `flores` config, not marked in Table 11. |
| NollySenti | pcm | 500 test reviews | human_translated: NollySenti's professional translators, and its Table 2 has "Naija (pcm)" | In the `nollysenti` config, not marked in Table 11. |
| AfriMGSM | wol, vai | 250 test questions | human_translated: IrokoBench names the Wolof translators and "the Vai translator for the MGSM data translation" | In the `afrimgsm` config and the Hub data. |

Vai was not among AfroBench's declared languages. Its `afrimgsm` configuration evaluates it, so it is
added to `languages` under R-2026-11-02-a, the ruling that added North Ndebele and Venda for the
same reason, and the language-code snapshot gains `vai` (confirmed on Artio). That gives AfroBench
64 target languages.

Two lineage components are new in `sources/lineage.yaml`. `mafand-mt` shares the `mafand-mt`
collection with AfriADR and MasakhaPOS's MAFAND languages, so `build.lineage` reads every pair
among them as dependent: MAFAND-MT cannot corroborate AfriADR, or the reverse. `afriqa` is
original, from a new `afriqa-questions` collection, with a Swahili override pointing at `tydi-qa`.

### Left out, and why

Each of these has a published split and a configuration, but no source that states how the items
were made (or, for AfriHate, no readable count). Under the SEA-HELM precedent they get no entry.

- **AfriHate** (15 languages, the `afrihate` task, added to AfroBench after the paper): tweets, with
  the same collection description as AfriSenti and no statement that they were written in the
  language. Its repository (`Davlan/afrihate`) also requires an access request, and the Hub's size
  endpoint returns HTTP 401, so no count can be read.
- **XL-Sum** (10 African languages): BBC articles, with no statement that they were written in the
  language rather than translated. SEA-HELM's Burmese XL-Sum is `native` because SEA-HELM's own
  tables say "Native"; AfroBench says nothing of the kind.
- **NaijaRC** (hau, ibo, yor; 82, 84 and 191 test questions): passages and questions from the
  WASSCE Hausa, Igbo and Yorùbá exams. The paper does not say the passages were written in those
  languages. All three languages are already at 4 or 5.
- **MAFAND-MT's other ten languages**: Hausa (the WMT Khamenei corpus), Igbo (Ezeani et al.),
  Swahili (Global Voices), Yorùbá (MENYO-20k) and isiZulu (Umsuka, "translated from
  English-isiZulu") come from existing corpora whose translators the paper does not name. Amharic,
  Kinyarwanda, Chichewa, chiShona and isiXhosa were added to the dataset after the paper, and no
  source describes them.
- **MasakhaNER-X's other 18 languages**: the Hub publishes their test sizes (966 to 1,000; 545 for
  Hausa). Nine come from MasakhaNER 2.0's MAFAND-MT sentences, but AfroBench's subsample of them is
  three citations away from MAFAND's statement, and named-entity tagging has no measurement model,
  so no band could move. Listed for a later pass.
- **Configuration artifacts**: the `flores` task includes Sundanese (`sun_Latn`), the `xlsum` task
  Telugu, and the `ntrex` task English to Tongan and Urdu. None is an African language, and none is
  in AfroBench's paper. They look like configuration errors rather than targets, so `languages` is
  not extended for them. This is a reading the maintainer may want to confirm.

## Score change

From `build/depth_ladder.py`:

| Languages | Before | After | Why |
|---|---|---|---|
| Bambara, Fon, Luo, Mossi | 1 | 3 | MAFAND-MT (band 3) is independent of FLORES; SIB-200 backs it. Fon also has AfriADR and AfriQA |
| Setswana | 1 | 4 | NTREX (band 4) was unbacked; Belebele now backs it |
| Chichewa, Malagasy, Somali, Swati | 3 | 4 | the same: Belebele backs NTREX one band higher than SIB-200 did |
| Ghomálá' | unmeasured | 3 | AfriADR, its own task, now has established provenance |
| Nigerian Pidgin | unmeasured | 3 | MAFAND-MT and NollySenti, independent of each other |
| Vai | not a target | 1 | AfriMGSM only, with nothing to back it |
| 27 other languages | 1 | 1 | in 22 of them every test is FLORES or built on FLORES's sentences (SIB-200, Belebele). Kirundi, Moroccan Arabic and Tsonga have an independent news or sentiment test whose provenance is still unknown. North Ndebele and Venda have NTREX alone |
| 20 other languages | 3 to 5 | unchanged | |
| Acholi, Algerian Arabic, Lugbara, Runyankole, Ateso | unmeasured | unmeasured | SALT and AfriSenti only, provenance unknown |
| **AfroBench** | **1** | **unresolved (1–3)** | |

Before: 32 at 1, 24 above, 7 unmeasured, of 63. After: 28 at 1, 31 above (11 at 3, 18 at 4, 2 at
5), 5 unmeasured, of 64. Filled at 0, the five unmeasured languages hold the median at 1; filled at
5, they lift it to 3. So the band does not stand, the record's score is null with
`unresolved_reason: evidence_incomplete`, and AfroBench is left out of the category's stage, which
stays at 2. Face value stays 3. 29 languages are capped, down from 37. Treating unverified lineage
as independent gives the same result.

How much each part carries:

- Without the MAFAND-MT entries the result is unresolved (1–2): MAFAND-MT is what lifts the upper end.
- Without the new Belebele entries it is still unresolved (1–3).
- Without AfriQA, or without Vai, it is still unresolved (1–3).
- The five unmeasured languages cut both ways. If SALT's translators were established, Acholi,
  Lugbara, Runyankole and Ateso would become measured at 1 (SALT is imported and nothing backs it),
  and the result would be unresolved (1–2). If AfriSenti's tweets counted as native, Algerian
  Arabic would become measured, Moroccan Arabic and Tsonga would rise, and AfroBench would stand at
  3. Neither reading is taken here.

The calibration record (`docs/sweeps/2026-11-03-depth-calibration-full-roster.md`) and
`tests/test_depth_calibration.py` move together. `tests/test_depth_ladder.py` now lists AfroBench
among the unresolved sets, and its stage tests use FLORES+ in place of AfroBench, because an
unresolved row never counts toward the stage. The eval-set strapline and
`docs/reference/capability.md`'s list of unresolved reasons are updated to match.

## Questions for the maintainer

None of these is settled here.

1. **Does a documented collection of posts count as "original text written in the language"?**
   AfriSenti and AfriHate collected tweets from the platform, with native speakers filtering by
   language, and describe no translation step. MasakhaNEWS and XL-Sum crawled broadcasters'
   language services, whose articles may be translated from English. Proposed answer: user posts
   collected from the platform and language-checked by native speakers count as `native`, and
   broadcaster news does not unless a source says it was written in the language. This would put
   AfroBench at 3.
2. **Is a cross-lingual QA item evidence for the question's language?** AfriQA's questions are
   written natively, but the passage and the scored answer are English or French. Proposed answer:
   record it as `reading_comprehension`, as here, and let a later ruling decide whether
   cross-lingual items need their own task class. AfriQA moves no band today.
3. **Is AfriADR AfroBench's own?** Its items are MAFAND-MT's sentences with the diacritics removed,
   and the reference answer is the original sentence. R-2026-11-03-i withdraws ownership for "cited
   reuse of complete items", and SIB-200 and Belebele stay their own because they write new labels
   or questions. AfriADR writes nothing new. Proposed answer: withdraw ownership with an
   `own_components` claim. That changes Ghomálá' from 3 to 1 and leaves Fon and Wolof where they are,
   since other independent tests back them, so AfroBench stays unresolved (1–3).
4. **Should obvious configuration artifacts extend `languages`?** Sundanese, Telugu, Tongan and Urdu
   appear in AfroBench's task configurations. Proposed answer: no; R-2026-11-02-a's "what it actually
   evaluates as targets" should be read as the suite's declared scope plus African languages its
   configurations evaluate.
5. **Part-of-speech and named-entity tagging still have no measurement model.** Eleven MasakhaPOS
   entries now have established provenance and still carry no band. Proposed answer: leave this to
   its own issue with a proposed ruling, as #1098 says.
