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

The recommendation is a **reference-pair rule**: name the settled products that stand for the
bottom of 4 and the top of 3, require a candidate to be read beside one of them on the same
evaluations, and require agreement between at least two evaluation families before a band moves.
It is set out under [Proposed method](#proposed-method), with the decisions it needs under
[Decisions requested](#decisions-requested).

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

## Proposed method

**1. Name the reference products, per instrument.** For each instrument the category uses, the
maintainer names which settled products stand for the bottom of 4 and the top of 3. Candidates
on today's corpus:

- AA v5.0.1: bottom of 4, mistral-large (26). Top of 3: none exists, so the index can confirm a
  4 or a 5 but cannot by itself place a product at 3.
- Base-model suites: bottom of 4, olmo's base (Olmo 3 32B). Top of 3, marin (Marin 32B). This
  pair is only usable if the rule in step 2 allows a base table to place a family.
- Post-trained suites: top of 3, phi (Phi-4), already the root of the gpt-4o comparison. Bottom of
  4, olmo (OLMo 3.1 Think 32B), if a table that reads it beside a candidate can be found.

Low-confidence vendor-placed 4s (hunyuan, ernie-flash) are left out of the reference set until
an independent reading exists.

**2. Fix the release and training stage a comparison uses.** A band describes the family's best
release (`identity.md`: capability is the max across a tier's releases). Two readings of that are
possible, and the maintainer needs to choose:

- *Like for like:* a base table can place a family only against references read on their bases,
  and a post-trained table only against post-trained references. A family with no reasoning-tuned
  release is compared on what it has, and a missing release type is not a penalty.
- *Best release:* every comparison uses each family's best release, base or post-trained. Base
  tables then serve only as supporting evidence, never to place a family.

The first unblocks llama, apertus and eurollm on the tables that already exist. The second keeps
them held until a post-trained comparison appears.

**3. Require two evaluation families to agree before a band moves.** Following R-2026-11-12-n
("different benchmark families answer different questions"), a candidate moves across the
boundary only when at least two of these agree: an independent index (AA v5.0.1), a same-pipeline
general suite (knowledge, reasoning, math, code), and a same-pipeline language-coverage suite.
One family alone records an ordering in the value and note, and the band stays where it is.

**4. Count language coverage only as measured coverage.** Multilingual capability counts through
multilingual evaluations read on the same table (for example MMMLU, INCLUDE or Global-MMLU,
which some of the cited cards already carry), not through the number of languages a card lists.
This keeps the European models' main strength in the comparison without turning a coverage claim
into a band.

**5. Record the result as a ruling and in the recipe.** The reference products and the two rules
above go in `base_pretrained.yaml` beside the existing `version_rule`, so a later pass reads them
from the recipe rather than from this brief.

## Decisions requested

1. **Reference products.** Accept, amend or replace the candidates in step 1. In particular: is
   mistral-large the right bottom-of-4 reference on AA, and is the olmo/marin pair usable at all
   given that olmo's 4 is read on its Think release?
2. **Like for like or best release** (step 2).
3. **Two-family agreement** (step 3), and which families count.
4. **Measured language coverage** (step 4).
5. **Order of work once ruled.** Suggested: re-read gemma and inkling first, since both have AA
   readings beside mistral-large; then llama, apertus and eurollm if like for like is chosen;
   granite last, since it needs a settled 3 on the same instrument.

Nothing in this brief moves a score. Each held product is re-read against the ruled method in its
own PR, and any tier change still comes to the maintainer with its evidence first
(R-2026-11-12-l).
