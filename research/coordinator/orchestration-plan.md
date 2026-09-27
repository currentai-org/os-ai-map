# Plan: seed and populate the proposed categories with a fleet of subagents

Status as of 2026-09-26: the corpus holds 862 head products and 193 tail rows across 25
categories. None of the products named in the 11 proposal issues is on the map. The repo's own
procedure is already a pipeline: `discover-candidates` → `edit-category` + `build-rubric` →
seed (`sources/registry/<slug>.yaml`) → `promote-category` → publish. This plan runs that
pipeline across roughly nine categories at once without the categories colliding.

## 1. Where each proposal stands

| Issue | Proposed slug | Already ruled | Still open | Wave |
|---|---|---|---|---|
| #602 | `speech_audio` | Shape `{model, software}`, weights 0.4/0.6, models and engines as separate rows, CC-BY → `permissive_non_osi`, 4 custom licenses deferred | nothing blocking | **0 (start now, no research)** |
| #600 | `classic_ml_cv` | Owns timm and vision backbones | New category vs broadening `ml_frameworks` | 1 |
| #603 | `media_generation` | Music and SFX land here | Tooling here vs `ui_api`; own category vs arm of #9 | 1 |
| #9 | `multimodal_models` | Stays "models"; backbones → #600 | Understanding-only vs any-to-any; VL line vs SKU of an existing family | 1 |
| #574 | `federated_learning` | Narrow scope; ray settled | FedML/Substra; Flower one or two; the insight | 1 |
| #599 | `datacenter_accelerators` | ADR-005 applies; chipset rung reusable | Sibling vs rename `edge_hardware` | 2 |
| #12 + #99 | `robotics_embodied` (+ `world_models`) | GR00T → #12 | In scope at all? New arc? World models revisit late Oct | 2 |
| #93 | `assurance_evidence` | Owns governance and documentation tooling | nvtrust in, EZKL on hold; model-card scope | 2 |
| #30 | `responsible_ai_measurement` | Narrowed to carbon, fairness and watermarking | Close as out of scope, or keep | 3 (likely park) |
| #601 | `model_hubs` | Hub platform would be a new product; ADR-005 surfaces | Approve at all | 3 (likely too sparse) |

I placed the waves by how much governance each proposal still needs, not by how interesting it is.
The two "likely" calls in wave 3 are my expectation. The research is what settles them.

Out of scope for this plan: the model-serving gap (KServe/BentoML/Triton), which has no issue
yet, and every `[dependency]`/methodology issue.

## 2. Fit criteria, fixed before research comes back

The repo forbids inventing a legitimacy rule mid-sweep, so the go/no-go test has to be adopted
**now**, before anyone sees the counts. Proposed:

1. **Supply:** at least 15 accepted candidates, all with a live addressable artifact. Publication
   needs 10 promoted products, and promotions historically lose about 10–30% to boundary
   rejections, so 15 leaves room for that.
2. **Diversity:** at least 6 independent organizations, and no single org above 30% of rows.
   #99 failed at 4 lines from 2 vendors; #533 shipped at 34 from 24.
3. **One capability quantity:** a single quantity orders the set. A per-type ladder map
   (`extends: {model, software}`) is fine; two unrelated capability ladders are not.
4. **MECE:** every candidate passes exactly one category's litmus, and every contested existing
   product has an explicit move or stay.

A proposal that fails 1 or 2 is parked with a revisit date. One that fails 3 is split or
closed. One that fails 4 goes back to the boundary step. **These thresholds are my proposal, not
existing policy.** They need your or Carl's sign-off before phase B.

## 3. Pipeline

```
A Research (external, parallel)  →  B Rulings (human)  →  C Boundary matrix (1 agent, serial)
   →  D Skeleton PR (serial, 1 PR)  →  E Seed PRs (parallel, 1 per category)
   →  F Promotion PRs (parallel, 1 per category, fanned out inside)  →  G Publish flip
```

### A. Research (outside this session)
Use `research-prompt.md` with `corpus-index.tsv` attached, one agent per brief. Each returns a
document in the exact shape of a `docs/sweeps/` record, so it can later be committed unchanged as
the seed PR's sweep record. Save the outputs where this session can read them (paste them in, or
drop them in the repo under `research/`, uncommitted).

### B. Rulings (you or Carl; I prepare the sheet)
I merge every brief's §1 verdict, §2 metrics and §9 questions into **one decision sheet**:
the fit criteria applied per category, each open question with a recommendation, and the
cross-category conflicts. The rulings get recorded as comments on each issue, the same way the
2026-09-25 rulings were. No agent makes a governance call.

### C. Boundary matrix (one agent, serial, read-only plus one file)
This step is the most important one for MECE, and it can't run in parallel. The modality cluster
(#602/#603/#9/#600) and the governance pair (#93/#30) each carve up the same territory, and
`validate` enforces one slug in one category.
- Input: every GO category's accepted list, contested-products table and the rulings.
- Output: `research/boundary-matrix.md`, which gives every contested product exactly one owner
  category and one owning PR, plus every existing head or tail product that moves (for example
  `pysyft` and `syfthub` → `federated_learning`, and `synthid-text` from the `safeguards` tail →
  the watermarking owner).
- Gate: the union of all seed lists has zero duplicate slugs and zero duplicate artifacts, checked
  by a script against `corpus-index.tsv`, not by eye.

### D. Skeleton PR (serial, one PR, on the designated branch)
`sources/taxonomy.yaml` is the one file every category touches, so one PR creates all of them:
- `sources/categories/<slug>.yaml` for each GO category: `description`, `weights`, `comments`
  (boundary and exclusions), and `scoring_recipe` with `extends:` pointing at the shared ladders.
  The capability note stays a stub; promotion writes it.
- One taxonomy line per category, `{name: <slug>, status: preliminary}`, in the ruled group or
  arc. A new arc or group for robotics, if ruled, lands here.
- `edit-category` and `build-rubric` skills; `preflight` clean; merged before E starts.
- Speech exception: `speech_audio` can go first as its own skeleton + seed PR in wave 0. The
  skeleton PR then merges main on top of it.

### E. Seed PRs (parallel, one per category)
Each seed agent follows `discover-candidates` and `edit-category` §5 and touches only:
- `sources/registry/<slug>.yaml`, which is new: the paste-ready §6a rows, re-triaged (step 1 of
  promote-category: canonical `full_name`, not archived, not a fork, org correct).
- `sources/org_handles.yaml`, so `tests/test_identity_eval.py` doesn't trip on new orgs.
- `sources/resolution_ledger.yaml` for the parked candidates that have a ruling.
- `docs/sweeps/<date>-<slug>.md`, the research document with counts reconciled.
- Tail-row moves assigned to this category by the boundary matrix.

These are cheap, about an hour of agent time each. They're good for a single Workflow run in this
container, one agent per category with worktree isolation.

### F. Promotion (parallel across categories, fanned out inside each)
The skill's own advice is that promotion "parallelizes badly on judgment and well on fetching."
So each category is one team:

| Role | Count | Does | Never does |
|---|---|---|---|
| **Lead** | 1 | promote-category steps 1–4 (triage, boundary, replacements, cross-category moves), step 6 capability matrix and anchors, strapline, roster order, org rosters, preflight, the PR | delegate a judgment call |
| **Fetchers** | ⌈N/6⌉ | harvest evidence per candidate into `research/<slug>/evidence/<product>.json`: repo record, LICENSE body + sha256, README head, package metadata, HF downloads, source URLs with dates | interpret or score |
| **Writers** | ⌈N/8⌉ | write `sources/products/<p>.yaml` + `sources/scores/<p>.yaml` per add-product, against the lead's matrix and the cached evidence only | touch rosters, org files, rubrics, the category file |
| **Verifier** | 1 | re-derive every score read-only from sources (the scientific_ai_models precedent) and return a diff | write to `sources/` |

The sequence inside a team: lead triage → fetchers, in parallel → lead writes the capability
matrix → writers, in parallel → lead integrates rosters → verifier → lead fixes →
`preflight` (full, with pytest) → PR.

**Execution vehicle (recommended): one remote child session per category** (`create_session`),
each on its own branch, running the team as a Workflow inside its own container. Promotion is
multi-hour to multi-day per category, which is too long and too disk-heavy for one shared
container. This session stays the coordinator: it tracks the children, subscribes to their PRs,
and does the merge-order bookkeeping.

**Scale:** about 9 categories × (1 lead + 3–7 fetchers + 2–5 writers + 1 verifier) ≈ 70–110 agent
runs, staggered by wave. This session's workflow size guideline is currently *medium, under 10
agents per workflow*. Per-category workflows of 8–14 agents fit that if you raise it slightly
("Dynamic workflow size" in /config).

### G. Publish
In the promotion PR, flip the taxonomy entry to `published` only when promote-category step 8
holds: an evidence-based strapline, ≥10 scored products, coherent anchors, and no open dispute.
Otherwise it stays preliminary, and the PR says exactly what blocks it. The speech ruling asked
for seed and promotion as **separate** PRs. I'd keep that split everywhere, because it keeps each
review small.

## 4. Collision control (what breaks when you run this in parallel)

| Hotspot | Rule |
|---|---|
| `sources/taxonomy.yaml` | Only the skeleton PR (and speech's) touches it. Promotion PRs change only the `status` on their own line. |
| Shared ladders `sources/rubrics/*.yaml` (license tiers) | **Never in a category PR.** New license strings get collected across all categories into one "license rulings" PR for a maintainer. Products defer until the ruling lands (promote-category step 7). scientific_ai_models broke this rule once and had to get sign-off after the fact. |
| Shared org files (`nvidia`, `google`, `meta`, `alibaba`, `microsoft`, `tencent`, `huggingface`…) and `org_handles.yaml`, `resolution_ledger.yaml` | Append-only list edits. Each PR merges main right before pushing, and the coordinator merges in a queue, one at a time. Never rebase. |
| Cross-category moves of head products | Only the PR the boundary matrix names may move a given product. It rebands that product and edits the source category's roster. |
| Pinned census tests (`test_serialize_rubric` per-category rows) | The lead updates the pin and records in the comment what moved the number. |
| `build/notebook_data.json`, `notebooks/`, `tests/goldens/corpus.json` | Never committed. The bot regenerates them. |
| GitHub API | `GITHUB_TOKEN` is set in this environment, which gives 5,000 requests/hr **shared by every fetcher on the token**. About 250 candidates × 4 is fine, but stagger the fetcher waves and check the token with one call first, since a stale token 401s silently. |

## 5. Scale and review load

Expected output, if wave 3 parks: about 7–8 new categories and roughly 200–280 promoted products.
That grows the corpus by about a quarter. Every PR is human-merged (ADR-004), so the real
bottleneck is review, not agents. I'd release at most 2–3 promotion PRs at a time, attach the
`build.check_corpus_diff` review sheet to each, and put the `stage-move` label on any that shifts
a stage.

## 6. What I need from you to start

1. **Adopt the fit criteria in §2**, or change the numbers.
2. **Branch permission.** I'm limited to `claude/great-meitner-y7gj79`. This plan needs one branch
   per seed PR and per promotion PR (for example `claude/cat-<slug>-seed` and
   `claude/cat-<slug>-promote`). May the child sessions push those and open PRs?
3. **Execution vehicle and scale:** remote child sessions per category, plus a Workflow for the
   seed phase and the fan-out inside each promotion. Say "use a workflow" and raise the size
   guideline if you want that.
4. **Who rules in phase B:** you, or Carl on the issues?
5. **Start `speech_audio` now?** It needs no research. The seed agent can build the registry file
   from the 41-row list in #602 while the research agents run.
