# Handoff: new-category rollout for os-ai-map (state at 2026-09-27 ~14:30 UTC)

You are taking over as coordinator of the new-category rollout in `currentai-org/os-ai-map`.
Read `CLAUDE.md` and `AGENTS.md` first, then this file. Everything referenced here is pushed.
This branch (`claude/research-kit`) is coordination state only: never merge it, and keep
`research/` out of every PR commit.

## Where round 1 stands

Round 1 promoted a first tranche in each of nine categories (174 head products). It lands
through ONE integration PR rather than nine sequential merges:

- **#738** `claude/promote-round1`: merges all nine category branches, with the shared
  fixtures regenerated once. Green on `9828e22c`, mergeable, still a DRAFT. The maintainer
  marks it ready and merges it; nobody else does.
- **#729 to #737**: the per-category review surfaces. Each carries a comment pointing at
  #738. When #738 merges, the maintainer closes them. Red `validate` on #730, #732, #733
  (older runs) and #736 is only the stage-move label predating that branch's last push.
  #738 runs with the label.
- **#739**: the license-rulings issue (label `needs-ruling`). Six grouped rulings plus
  single-product ones, and a look-ahead at strings on registry rows.

If a category PR merges directly instead of via #738, #738 needs a re-sync: `git merge
origin/main` on `claude/promote-round1`, then resolve with the tools below.

### Corrections made after a Codex review of #738 (already in #738)

Two blocking findings were real and fixed on the category branches, then re-merged:

- **The current release governs openness** (maintainer's #720 ruling, docs/reference/identity.md).
  The API-only exclusion works within a release, never across releases. `qwen-omni` (#734) is
  now deferred as "closed frontier on an open line", like wan and qwen-image.
- **Most-restrictive applies only within the governing release.** canary and moshi (#733) went
  from 2/restricted to 3/open_weights. gr00t (#731) went to 3/open_weights and left the deferred list.
- The deferred census in `tests/test_check_parity.py` is 32 on #738.

**Root cause still open:** `sources/rubrics/model.yaml` `multi_sku_rule` (and the pretrained
twin) does not say "within the governing release", so speech_audio read it literally. That
wording is a one-line rubric PR of its own. It needs the maintainer's go-ahead, and a category
PR must never touch `sources/rubrics/`.

## Maintainer decisions made in this session

- **Merge path:** one integration PR per round. The per-category PRs are review surfaces.
- **Round 2 bar:** triage first. The maintainer approves the promote list before any writer starts.
- **Round 2 compute:** batched writers (2 to 3 at a time on a 4-CPU box), researchers in parallel.

## Open items, in order

1. **Wait for #738 to merge.** Then confirm that main has the nine categories, and that the
   bot regeneration commit landed after it.
2. **Round 2 triage approval (maintainer).** `research/coordinator/round2-triage/<cat>.tsv`
   has one row per remaining registry row, from live fetches on 2026-09-27: verdict
   (PROMOTE / TAIL_OK / MOVE), primary signal, band estimate, gap note, confidence and reason.
   - PROMOTE totals: classic_ml_cv 42, speech_audio 18, media_generation 6, robotics_embodied 6,
     multimodal_models 6, datacenter_accelerators 2, federated_learning 1, assurance_evidence 1,
     model_hubs 1. That's 83. MOVE: openml to benchmark_eval_data.
   - The bar used: at least 100K downloads a month (at least 10K stars as a capped fallback)
     for band 3, or a gap fill, or a flagship closed comparator (ADR-005).
   - Flags: several strong rows carry licenses no tier names (xtts's Coqui license, voxtral,
     several classic_ml_cv model licenses). They'll be deferred until #739 rulings land.
     Some PROMOTEs are thin gap fills: Open-Sora, MMAudio, zkml, p2pfl. Wan2GP is a fork.
     tencent-ailab/SongGeneration 404s. Newton's PyPI package doesn't link its repo.
3. **Round 2 execution (after approval and after #738 merges).** For each category, one writer
   on `claude/promote2-<cat>` off the new main, following `docs/workflows/promote-category.md`
   (skill `promote-category`), with an independent read-only verifier before the PR opens.
   Open draft PRs labeled `promotion` (plus `stage-move` if the stage moves). Then build one
   integration branch `claude/promote-round2` and PR, the same way as #738.
   - Brief every writer on the current-release rule above. It was the one cross-category
     inconsistency in round 1.
   - Tell every agent to push WIP at each milestone, because of the shared usage limit.
4. **Follow-ups, each its own small PR (propose first, don't start without a go-ahead):**
   diffusion trainers (kohya sd-scripts, musubi-tuner, SimpleTuner, diffusion-pipe) to
   finetuning_code; OCR-first VLMs to document_conversion; embodied-reasoning VLMs (RynnBrain,
   Hy-Embodied VLM, UnifoLM-ER) to multimodal_models; Matrix-3D and Marble to media_generation;
   dstack to deployment; Axelera Europa to edge_hardware; openml to benchmark_eval_data; the
   world_models promotion gate in late October; the #30 fairness and carbon lists
   (docs/sweeps/2026-09-26-assurance-evidence.md); the availability-vs-openness ruling
   (wan, qwen-image, hunyuan-3d, qwen-omni).
5. **Other review flags awaiting the maintainer** (in `review/review.md`): validmind-library
   scored instead of deferred (#730 Q4); rent-only silicon scored 3/documented (#729 Q2); thin
   `ungated` evidence on a handful of products (#730, #733); spaced-hyphen dash splices in
   #732 and #737 prose, for a prose pass; tabpfn cites no source for three of its license bodies.

## How the integration branch is built (tested on #738)

```
git switch -c claude/promote-roundN origin/main
for each category branch, in order:
  git merge --no-edit origin/claude/promote2-<cat>
  on conflict: uv run python research/coordinator/tools/resolve_integration.py
    (identity fixtures: ours; org rosters: union of products:, reports any non-roster diff)
  if tests/test_check_parity.py conflicts: uv run python research/coordinator/tools/census_merge.py
    (keeps both comment blocks and sums the deltas; it parses "# N -> M [on DATE] with" and
     needs a hand fix when a block is phrased differently, as "7 -> 8 the same day" was)
  other census tests (test_adoption_evaluation.py, test_serialize_registry.py): resolve by hand,
    keeping every side's assertions
then: uv run python -m build.identity_eval --write-fixture tests/fixtures/identity_edges_pass.json
      uv run python -m build.identity_eval --write-coverage-baseline
      (this drops lowered_because; re-add ONE combined note naming every org that left the route,
       and derive it by diffing homepage-bearing registry orgs between origin/main and HEAD)
      add one CHANGELOG line under Unreleased/Added citing the integration PR
      uv run python -m build.preflight   (full; ~18 min on 4 CPUs)
```

No round-1 branch touched `sources/org_handles.yaml`. If a round-2 branch does,
`tools/rebuild_org_handles.py REF...` rebuilds it as a blockwise union, run from the repo root.

## Environment facts that bit this session

- **The shell may be zsh.** `"$B:path"` hits zsh modifiers (`:s`, `:t`, `:h`), so write `"${B}:path"`.
  **Never** write `gate | tail && git push`: the pipeline's status is tail's, and this pushed red
  CI twice. Use `set -o pipefail`, or redirect to a log and test the gate's own exit code.
- `pkill -f <pattern>` kills your own shell when the pattern appears in the command line.
- `gh pr diff` fails on #738 (the diff is too large). For a reviewer, build a scoped diff: a
  worktree at origin/main, then `git checkout <branch> -- <paths>`.
- A CI re-run does NOT pick up a label added after the push. Only a new push does.
- The previous cloud promotion sessions and their triggers were not visible from the local
  session (the trigger API and session lookups returned 404). Track work by branch activity.
- `build.identity_eval --write-coverage-baseline` rewrites the file without `lowered_because`.

## Rules that stay in force

Humans merge; never approve or merge. Never force-push or rewrite pushed history, never push empty
commits, never close and reopen a PR to kick CI, never skip or disable tests. Never commit
`build/notebook_data.json`, `notebooks/` or `tests/goldens/corpus.json`. Never edit
`sources/rubrics/` in a category PR. Never load-modify-dump a `sources/` file; use
`build/components.py` and surgical single-field edits. American English. No AI tells in commits,
PRs or prose. No Co-Authored-By or tool trailers, and no Linear ids or internal company names in
repo text.
