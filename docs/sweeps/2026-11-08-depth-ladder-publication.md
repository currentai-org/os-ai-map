# Depth ladder publication: `language_specific_eval_sets`, 2026-11-08

## Scope

This publishes the depth ladder. The 22 evaluation sets calibrated on 2026-11-03
([`2026-11-03-depth-calibration-full-roster.md`](2026-11-03-depth-calibration-full-roster.md),
accepted as R-2026-11-07-a) move from `language_specific_datasets` to `language_specific_eval_sets`,
which is published, and their capability bands become the bands `build/depth_ladder.py` computes.
R-2026-11-07-b set the conditions, and R-2026-11-08-a and -b settled the unresolved sets and the
basis. [`../reference/capability.md`](../reference/capability.md), "The depth ladder", is normative
on what is published.

What changed:

- `build/depth_ladder.py` computes each set's band and its companion figures.
  `build/depth_calibration.py` now uses it, and its output is byte-identical to the 2026-11-03
  calibration.
- `build.validate` recomputes every band in the category and refuses a record whose score differs,
  whose basis is not `evaluation_depth`, or that names a `relative_to` peer.
- `capability.basis` gains `evaluation_depth` (R-2026-11-08-b).
- In each of the 22 records, the capability header (`score`, `basis`, `basis_detail`, `value`,
  `confidence`, `note`) is rewritten from the computed result, and `relative_to`, `relation` and
  `last_verified` are removed. Sources, coverage, pivots and ownership claims are untouched.
- The payload carries `capability.depth` on each row of the category, and `overall_basis` on every
  row of the map.
- `sources/lineage.yaml` becomes a declaration input.
- Five comparisons in `language_specific_datasets` that named a set leaving the category were
  re-judged (below).

## Membership

The category holds the 22 calibrated sets and no others. The membership is frozen at this
publication, and the boundary between a language-specific evaluation set and a general benchmark
is provisional (R-2026-11-07-b): a set joins or leaves only by a later ruling. Every product stays
published exactly once. `language_specific_datasets` keeps 75 products, and no row moved anywhere
else.

## The score-change diff

Main score is the score on `main` before this change, the interim ladder's band in
`language_specific_datasets`. Published band is what this change publishes. Face value is the median
before the corroboration cap, and best original the median over the set's own components alone.
Measured is completeness, the target languages with a usable measurement. Cap binds in counts the
target languages where the cap lowers the language's band. Unverified as independent is the
sensitivity reading (R-2026-11-02-m). Entry statuses tally the official-split coverage entries by
`build.evidence_status`, as status/reason. Every band is provisional and count-based: a ceiling read
from item counts, not an estimated confidence interval. No method for an estimated band is approved
yet.

| Set | Main score | Published band | Face value | Best original | Status | Measured | Tasks | Cap binds in | Unverified as independent | Entry statuses |
|---|---|---|---|---|---|---|---|---|---|---|
| ArabicMMLU | 5 | 5 | 5 | 5 | provisional | 1 of 1 | 1 | 0 | 5 | provisional/count_model 1 |
| KazMMLU | 3 | 5 | 5 | 5 | provisional | 2 of 2 | 1 | 0 | 5 | provisional/count_model 2 |
| Khayyam Challenge | 4 | 5 | 5 | 5 | provisional | 1 of 1 | 1 | 0 | 5 | provisional/count_model 1 |
| TurkishMMLU | 3 | 5 | 5 | 5 | provisional | 1 of 1 | 1 | 0 | 5 | provisional/count_model 2 |
| IndicXTREME | 4 | 4 | 4 | 4 | provisional | 19 of 21 | 4 | 0 | 4 | provisional/count_model 67, provisional/measured_zero 3, unresolved/depth_unknown 7, unresolved/no_measurement_model 25 |
| LaoBench | 3 | 4 | 4 | 4 | provisional | 1 of 1 | 1 | 0 | 4 | provisional/count_model 1 |
| MILU | 3 | 4 | 4 | 4 | provisional | 10 of 10 | 1 | 0 | 4 | provisional/count_model 11 |
| Belebele | 5 | 3 | 3 | 3 | provisional | 114 of 114 | 1 | 0 | 3 | provisional/count_model 114, unresolved/depth_unknown 1 |
| FLORES+ | 5 | 3 | 3 | 3 | provisional | 188 of 215 | 1 | 0 | 3 | provisional/count_model 185, provisional/measured_zero 3, unresolved/depth_unknown 12 |
| INCLUDE | 4 | 3 | 3 | 3 | provisional | 44 of 44 | 1 | 2 | 3 | provisional/count_model 88 |
| IndicGenBench | 3 | 3 | 3 | 3 | provisional | 29 of 29 | 3 | 1 | 3 | provisional/count_model 86, unresolved/depth_unknown 12 |
| SeaExam | 3 | 3 | 3 | unresolved (3-4) | provisional | 4 of 4 | 1 | 1 | 3 | provisional/count_model 6, provisional/measured_zero 4 |
| ThaiExam | 4 | 3 | 3 | 3 | provisional | 1 of 1 | 1 | 0 | 3 | provisional/count_model 1 |
| SEA-HELM | 5 | 2 | 3 | 2 | provisional | 11 of 11 | 9 | 4 | 2 | provisional/count_model 58, provisional/measured_zero 1, unresolved/depth_unknown 5 |
| SIB-200 | 3 | 2 | 2 | 2 | provisional | 194 of 195 | 1 | 0 | 2 | provisional/count_model 194, unresolved/depth_unknown 2 |
| AfroBench | 5 | 1 | 3 | unavailable | provisional | 56 of 63 | 6 | 37 | 1 | provisional/count_model 215, unresolved/depth_unknown 62 |
| AmericasNLP shared-task data | 3 | 1 | 3 | unresolved (0-5) | provisional | 10 of 10 | 1 | 9 | 1 | provisional/count_model 10 |
| DarijaMMLU | 2 | null (review_scope_unstated) | unresolved (0-5) | unavailable | unresolved | 0 of 1 | 0 | 0 | unresolved (0-5) | unresolved/depth_unknown 1 |
| FLEURS | 5 | null (no_measurement_model) | unresolved (0-5) | unavailable | unresolved | 0 of 101 | 0 | 0 | unresolved (0-5) | unresolved/depth_unknown 3, unresolved/no_measurement_model 303 |
| IndoNLU | 4 | null (provenance_unknown) | unresolved (0-5) | unavailable | unresolved | 0 of 1 | 0 | 0 | unresolved (0-5) | unresolved/depth_unknown 12 |
| Lahaja | 3 | null (no_measurement_model) | unresolved (0-5) | unavailable | unresolved | 0 of 1 | 0 | 0 | unresolved (0-5) | unresolved/no_measurement_model 1 |
| VMLU | 4 | null (no_official_split) | unresolved (0-5) | unavailable | unresolved | 0 of 1 | 0 | 0 | unresolved (0-5) |  |

Five bands rise, eight fall, and four hold. Five sets have no band that stands. The four native
exams (ArabicMMLU, KazMMLU, Khayyam Challenge and TurkishMMLU) reach 5, four of 22, below the
one-third review trigger. The large falls are the corroboration policy at work:

- AfroBench's face value is 3, but in 37 of its 63 target languages that face value rests on an
  imported component with nothing independent backing it, so its median falls to 1.
- SEA-HELM's face value is 3, and the cap takes four languages down, so its median is 2.
- AmericasNLP's face value is 3, and the cap binds in 9 of its 10 languages, so its band is 1.
- FLORES+ and Belebele fall from 5 to 3 without any cap. Their median language has between 400 and
  1,599 qualifying items.

No band changes under the unverified-lineage sensitivity reading.

## Rankings and tiers

Ranks here order the rows by overall score within the category, ties broken by slug. Main ranks the
sets among all 97 products of `language_specific_datasets`; this change ranks them among the 22.
Four sets lose a tier: FLEURS (leading on main) because it is unresolved, and Belebele, FLORES+ and
SEA-HELM (strong on main) because their bands fall. ArabicMMLU is the only set with a tier.

| Set | Main overall | Main rank (of 97) | Main tier | New overall | New rank (of 22) | New tier | Overall basis |
|---|---|---|---|---|---|---|---|
| ArabicMMLU | 4.1 | 5 | strong | 4.1 | 1 | strong | adoption_and_capability |
| KazMMLU | 2.4 | 48 | - | 3.8 | 3 | - | adoption_and_capability |
| Khayyam Challenge | 3.1 | 18 | - | 3.8 | 4 | - | adoption_and_capability |
| TurkishMMLU | 2.4 | 55 | - | 3.8 | 5 | - | adoption_and_capability |
| IndicXTREME | 3.4 | 11 | - | 3.4 | 6 | - | adoption_and_capability |
| LaoBench | 2.4 | 50 | - | 3.1 | 8 | - | adoption_and_capability |
| MILU | 2.7 | 33 | - | 3.4 | 7 | - | adoption_and_capability |
| Belebele | 4.4 | 2 | strong | 3.0 | 9 | - | adoption_and_capability |
| FLORES+ | 4.4 | 3 | strong | 3.0 | 10 | - | adoption_and_capability |
| INCLUDE | 3.7 | 7 | - | 3.0 | 11 | - | adoption_and_capability |
| IndicGenBench | 2.7 | 29 | - | 2.7 | 12 | - | adoption_and_capability |
| SeaExam | 2.4 | 53 | - | 2.4 | 14 | - | adoption_and_capability |
| ThaiExam | 3.4 | 13 | - | 2.7 | 13 | - | adoption_and_capability |
| SEA-HELM | 4.4 | 4 | strong | 2.3 | 15 | - | adoption_and_capability |
| SIB-200 | 3.0 | 22 | - | 2.3 | 16 | - | adoption_and_capability |
| AfroBench | 3.8 | 6 | - | 1.0 | 18 | - | adoption_and_capability |
| AmericasNLP shared-task data | 2.4 | 45 | - | 1.0 | 19 | - | adoption_and_capability |
| DarijaMMLU | 2.0 | 58 | - | 2.0 | 17 | - | adoption_only |
| FLEURS | 4.7 | 1 | leading | 4.0 | 2 | - | adoption_only |
| IndoNLU | 3.1 | 16 | - | 1.0 | 20 | - | adoption_only |
| Lahaja | 2.4 | 49 | - | 1.0 | 21 | - | adoption_only |
| VMLU | 3.1 | 19 | - | 1.0 | 22 | - | adoption_only |

## The five unresolved sets

FLEURS, Lahaja, VMLU, IndoNLU and DarijaMMLU publish `capability.score: null`, `status: unresolved`
and a reason, and no interim score (R-2026-11-08-a). Each stays in the category with its overall
score labeled `overall_basis: adoption_only`. It takes no tier, is never `mature`, and is left out of
the stage computation.

Their effect on rankings: an adoption-only overall sorts beside the resolved rows. FLEURS, open
with adoption 4, has an overall of 4.0 and sits second of 22, above every resolved set but
ArabicMMLU. DarijaMMLU's 2.0 sits seventeenth, above AfroBench and AmericasNLP. IndoNLU, Lahaja and
VMLU are at 1.0, tied with AfroBench and AmericasNLP. The label marks these scores as adoption alone, but the sort order does not.
Whether an unresolved row should sort after the resolved ones is left for review.

Their effect on stages: the category is at stage 2, gaps `capability` and `adoption`. Its best open
resolved rows are Belebele and INCLUDE, both at 3.0 overall. If FLEURS counted on adoption alone, it
would be the best open product at 4.0 and lift the category to stage 3. The exclusion holds it at 2,
and `tests/test_depth_ladder.py` pins both readings. Lahaja, IndoNLU, VMLU and DarijaMMLU are all below
3.0, so none of them would move the stage.

## Stage impact

| Category | Main | This change |
|---|---|---|
| `language_specific_datasets` | stage 4, 97 products, gap `resiliency` | stage 3, 75 products, gap `adoption` |
| `language_specific_eval_sets` | not published | stage 2, 22 products, gaps `capability` and `adoption` |

`language_specific_datasets` drops from stage 4 to 3. On main, its one mature fully open product
was FLEURS (overall 4.7, capability 5 on the interim ladder, adoption 4), and one mature open
product is stage 4. FLEURS leaves with the other evaluation sets. The best open corpus left is
Sangraha at 3.7, which is stage 3 with an adoption gap. Every corpus here sits under a size cap and
none reaches 5. No other category's stage, and no product's score outside these two categories,
changes.

Suite/member deduplication carries over. No product on the map declares `lineage.part_of` today, so
the rule groups nothing in the migrated category. `tests/test_depth_ladder.py` tests the counting
on the real roster. It makes AfroBench, Belebele, SIB-200 and INCLUDE mature and fully open:

- With no edges, the four count as four, and the category reaches stage 5.
- With Belebele and SIB-200 declared members of AfroBench, the four count as two units, and the
  category stays at stage 4.
- An edge to a suite in another category groups nothing, and the category reaches stage 5.

## Declaration version

`sources/lineage.yaml` moves from `NON_DECLARATION_INPUTS` into `DECLARATION_INPUTS`, because a band
now depends on it: an edit to the registry can move a computed band. `CANONICALIZATION_VERSION`
goes from 1 to 2, because the classified inventory changed, so a declaration version computed under
the old classification cannot pass for a current one.

The band stays recorded in each score record, even though `build/` computes it. That is how a change
in the method reaches the declaration version. The evaluator's own version is still a sentinel
(#411), so a change to `build/depth_ladder.py` alone changes no digest. But a change that moves a
band fails `build.validate` until the record's score is rewritten, and the rewritten record is a
declaration input.

## Freshness

The 22 records carry no `capability.last_verified`. The evidence-and-freshness rule forbids writing
that date from a computation over recorded values, and a depth band is exactly that. Each coverage
entry stays dated by its sources' `accessed` dates, and the band's freshness falls back to the commit
that last changed the record.

## Comparisons into the departing sets

Five products in `language_specific_datasets` placed their bands against a set that leaves. A
computed band cannot anchor a peer comparison, and a peer must be in the same category. Each edge
was re-judged against the products that remain. An edge was re-pointed only where a cited
comparison holds, and made an explicit root otherwise. No band changes.

| Product | Was | Now | Why |
|---|---|---|---|
| ChrEn (1) | below an evaluation set | `one_below` `iitb-english-hindi` | Both bands come from the parallel-text size cap. IITB holds 1.49 million cited pairs, over the million-pair line for band 2; ChrEn holds about 14,000. OLDI-Seed, SMOL and AfriDocMT already record this edge. |
| Jojajovai (1) | below an evaluation set | `one_below` `iitb-english-hindi` | The same size-cap comparison, at 30,855 pairs. SMOL and OLDI-Seed also cover Guarani, but both are themselves placed below IITB, and SMOL records no Guarani count. |
| AfriHate (3) | below an evaluation set | root | No remaining product is a defensible peer. NCHLT and WURA would tie it to a corpus size cap. It keeps 3 on the narrow single-task rung. Its value now records the three community classifiers its Hub page lists, read 2026-11-08, where the record said one. |
| SOLD (3) | below an evaluation set | `at` `afrihate` | Same kind of resource: hand-labeled abusive tweets, one task, documented in a paper. The note states the difference: AfriHate has community fine-tunes listed on the Hub, and SOLD has none. |
| SEACrowd (3) | below SEA-HELM | root | No other loader hub or suite remains in the category. Glot500-c and SEA-Pile are banded by size caps the recipe says do not apply to the hub, and Cendol is instruction data. The note drops the SEA-HELM contrast. |

Open on these:

- AfriHate at 3 or 4 is a judgment call. The rung for the largest set for its languages with only
  community fine-tunes on the Hub could support 4, but category practice holds such sets at 3
  (Aksharantar, NCHLT). SOLD is unaffected: it would be `one_below` a 4.
- The IITB edges, the two new ones and the three already recorded, will need re-judging when
  R-2026-10-30-k's per-class size yardsticks are applied.
- SOLD's placement as a corpus rather than an evaluation set was a close call in the 2026-10-30
  sweep. If it moves, its edge moves with it.
- SEACrowd's downstream use was checked on its README, which names no outside user. Papers were not
  searched, and they might support a 4.
