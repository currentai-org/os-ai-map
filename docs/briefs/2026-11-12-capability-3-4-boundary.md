# Capability calibration: the boundary between 3 and 4 in base_pretrained, 2026-11-12

This brief prepares the next scoring step that ruling R-2026-11-12-n names: "a focused calibration
of the 3/4 boundary on genuinely comparable evaluations spanning general capability and language
coverage" (#1022). It inventories what the category's settled bands rest on, shows why the
current instruments cannot place the boundary on their own, and proposes a method for the
maintainer to rule on. It changes no score, basis, category or recipe. Like the other records in
`docs/briefs/`, it describes the state on the date above and gets refreshed by a new brief, not
edited.

It makes no new outside claims. Every figure below is quoted from a score file in `sources/scores/`
on `main` at `cf4100f1`, where each carries its own source, access date and digest.

## The short answer

The boundary cannot be fitted on the Artificial Analysis index, the category's primary anchor:
no product the category has settled at 3 has a v5.0.1 score, and only one settled 4 does. It can
be located with reference products read on shared evaluation tables, but the tables that exist
compare base checkpoints while several settled 4s are read on post-trained releases. So the
calibration needs two things the rules do not yet say: which models serve as the reference
points on each side, and which release and training stage a comparison must use.

The recommended method, revised after review of this brief, scores each family on its strongest
eligible release and prefers comparisons between releases at the same training stage. It asks for
adequate independent corroboration rather than a fixed count of evaluation families, counts
language capability only where it is measured, and treats reference models as provisional examples
rather than thresholds. It is set out under [Recommended method](#recommended-method), with what
remains to rule under [Decisions requested](#decisions-requested). Adopting the method does not
calibrate the boundary: the recipe keeps its "NOT YET CALIBRATED" status until the method has been
applied successfully to several boundary cases.

## What the settled bands rest on

"Settled" means the capability axis is not held in `sources/verification_queue.yaml`. Held
products are left out of the reference pool on purpose: a reference that is itself under review
cannot place anything.

| Band | Settled products and what each is read on | Held |
|---|---|---|
| 5 | deepseek, glm, mimo-pro, kimi, minimax: all Artificial Analysis Intelligence Index v5.0.1 (29 to 46) | ernie |
| 4 | mistral-large: AA v5.0.1, Mistral Large 4 (High) 26, `one_below mimo-pro`. olmo: OLMo 3.1 Think 32B on its card against Qwen3-32B (AIME 2025 78.1 vs 70.9, GPQA 57.5 vs 67.3, MMLU 86.4 vs 88.8). seed-oss: Seed-OSS-36B-Instruct card tables, `at olmo`. hunyuan: vendor blind expert evaluations, `one_below glm`, low confidence. ernie-flash: Baidu's same-pipeline base-model table, `at hunyuan`, low confidence | gemma, inkling, qwen |
| 3 | phi: Phi-4 card, GPQA 56.1, MATH 80.4. gpt-4o: the Phi-4 report's same-harness table, `at phi`. marin: Marin 32B Base 19-task average 65.2, against OLMo 2 32B Base 63.2 and Qwen 2.5 32B Base 68.1, `one_below olmo`. smollm: card claims against 3B and 4B peers. minicpm: card comparisons at the 8B class, `at smollm` | llama, granite, apertus, eurollm |

Three things stand out.

1. **The two sides are read on different instruments.** Every settled 5 and the one AA-read 4 sit
   on the v5.0.1 index. Every settled 3 sits on a model card or a vendor table, and none has a
   v5.0.1 score: `phi.yaml` records that "Artificial Analysis Intelligence Index v5.0.1 does not
   score Phi-4", and `gpt-4o.yaml` records the same for GPT-4o. The index therefore has a top half
   and no bottom half in this category, which is why the recipe's plan to fit thresholds "against
   the Artificial Analysis index" (`base_pretrained.yaml`, `bands_status`) cannot be carried out
   for this boundary today.
2. **Only one settled comparison crosses the boundary.** The settled edges among 3s and 4s are
   `seed-oss at olmo` and `ernie-flash at hunyuan` inside 4, `gpt-4o at phi` and `minicpm at
   smollm` inside 3, and `mistral-large` and `hunyuan` one below a 5. `marin one_below olmo` is the
   only one that spans 3 and 4. The roots themselves are read against outside models: olmo
   against Qwen3-32B, marin against OLMo 2 and Qwen 2.5 bases, phi against GPT-4.
3. **Several 4s are read on vendor evaluations at low confidence.** hunyuan and ernie-flash are
   placed by their vendors' own tables. They are weaker references than products read on an
   independent instrument.

## The tables that cross the boundary

A calibration table needs a settled 4 and a settled 3 on the same benchmarks, shots and metric.
The corpus records three such tables, all for base checkpoints.

| Table (cited in) | Settled 4 side | Settled 3 side | Held products on it |
|---|---|---|---|
| Olmo 3 32B base card (`llama.yaml`) | Olmo 3 32B base: math 61.6, code 40.0, MC STEM 74.5 | Marin 32B: 49.3, 30.8, 75.9 | Llama 3.1 70B base: 62.0, 36.3, 80.1 |
| Apertus-70B card, six-task average (`llama.yaml`) | none (OLMo 2 32B 67.7 is the previous olmo generation) | SmolLM3-3B 61.6 | Llama 4 Scout base 67.9, Apertus-70B 67.5 |
| Phi-4 technical report, OpenAI simple-evals (`gpt-4o.yaml`) | none | Phi-4 and GPT-4o | none |

Only the first table puts a settled 4 and a settled 3 side by side, and it shows the difficulty.
On base checkpoints olmo leads marin clearly on math and code and trails it slightly on MC STEM. But olmo's
4 is read on OLMo 3.1 Think 32B, a reasoning-tuned release, not on the base checkpoint in this
table. So the table tells us how far apart the two families' bases sit, not how far apart the
two releases that set their bands sit.

The same mismatch blocked llama under R-2026-11-12-n: Llama 3.1 70B base is level with Olmo 3
32B base on that table, but olmo's 4 rests on a post-trained release Llama has no counterpart
for.

## What the held products need

| Held | Score | Nearest usable evidence | What the boundary rule would have to decide |
|---|---|---|---|
| gemma | 4 | AA v5.0.1: 4.4, behind Inkling 12.5 and Mistral Large 4 26.1; model card MMLU Pro 85.2, GPQA Diamond 84.3 | Whether a small model scored low on an agentic index, with strong knowledge results, reaches the bottom of 4 |
| inkling | 4 | AA v5.0.1: 12 against Mistral Large 4 26 on all nine evaluations; vendor SWE-bench Verified 77.6 | Whether the gap to the lowest settled 4 on one instrument crosses the boundary when another instrument disagrees |
| granite | 3 | AA v5.0.1: Granite 4.2 8B 5.1; IBM cards compare Granite only with Granite | Needs a settled 3 on the same instrument, which does not exist on AA |
| llama | 3 | Olmo 3 32B base table, level with Olmo 3 base | Whether base-to-base parity with a 4 family moves a family whose best release is not reasoning-tuned |
| apertus, eurollm | 3 | Apertus and EuroLLM reports, against Llama 3.x and Scout | Same as llama, plus how multilingual coverage counts |

## Recommended method

This section was revised after a first review of the brief. The original proposal offered "like
for like" and "best release" as alternatives, required two evaluation families to agree before a
band moved, and named olmo's base and marin as the 3/4 reference pair. The review kept the
direction and changed all three.

**1. Score the family on its strongest eligible release.** A band describes what the family can
do, which is set by its strongest eligible release, not necessarily its newest (`identity.md`:
capability is the max across a tier's releases). Which releases are eligible is an identity
question settled on the product record before any comparison is read.

**2. Prefer comparisons at the same training stage.** Base against base, instruct against
instruct, reasoning against reasoning. A cross-stage comparison can contribute to a judgment but
cannot by itself establish parity. A family is not penalized for shipping no reasoning release,
and it is not assumed to perform as well as one either. For example, Llama 3.1 70B base matching
Olmo 3 32B base does not establish parity between the two families' strongest releases, because
olmo's 4 is read on its reasoning release.

**3. Require adequate independent corroboration, not a fixed count.** Two weak or correlated
benchmarks are not better than one strong independent evaluation, and one decisive, well-designed
evaluation can justify a move. A band moves when the evidence is sufficient and reproducible
across the capabilities that matter for the category, judged on independence, comparability,
breadth and uncertainty. Results that share one evaluation method count as one line of evidence,
however many languages or tasks they cover.

**4. Count language capability only where it is measured.** Multilingual performance counts
through multilingual evaluations (for example MMMLU, INCLUDE, Global-MMLU or EuroEval), read on the
same table as the comparison. The number of languages a card lists is descriptive metadata, not
evidence of quality in those languages.

**5. Treat reference models as provisional examples, not thresholds.**

- AA v5.0.1: mistral-large (26) is accepted as a provisional reference for 4. No settled 3 has a
  v5.0.1 score, so the index can support a 4 or a 5 but cannot by itself place a product at 3.
- Base-model suites: the olmo base / marin pair is useful for comparative analysis, but it does not
  inherit olmo's 4, which is read on its reasoning release. Formalizing it would create a separate,
  uncalibrated ladder for base models.
- Post-trained suites: phi (Phi-4) remains a usable top-of-3 example, already the root of the gpt-4o
  comparison.
- Vendor-placed 4s read at low confidence (hunyuan, ernie-flash) are not references until an
  independent reading exists.

**6. Keep evidence confidence apart from scoring confidence.** A source can document a benchmark
result exactly while the reading of that result as a band stays uncertain. A capability record's
`confidence` should describe the band, so precise evidence on an uncalibrated boundary does not by
itself justify `high`.

**7. Keep the bands uncalibrated until the method has been applied.** The recipe's `bands_status`
stays "NOT YET CALIBRATED". The method is recorded as a ruling and in the recipe beside
`version_rule` once it is adopted, and the calibration is declared only after the method has
settled several boundary cases.

## Decisions requested

1. **Adopt the method above** as a ruling, or amend it.
2. **Order of work once adopted:** gemma and inkling first, since both have AA readings beside
   mistral-large; then llama, apertus, eurollm and granite.
3. **Confidence wording** (step 6): whether the separation of evidence confidence from scoring
   confidence should become a field change in the score schema, or stay a rule for how
   `confidence` is set.

Nothing in this brief moves a score. Each held product is re-read against the adopted method in
its own PR, and any tier change still comes to the maintainer with its evidence first
(R-2026-11-12-l).
