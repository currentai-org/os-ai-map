# Handoff: new-category rollout for os-ai-map (state at 2026-09-27 ~02:25 UTC)

You are taking over as coordinator of a multi-session rollout in `currentai-org/os-ai-map` (the
Open Source AI Gap Map data repo). The previous coordinator session may run out of tokens, and
everything it had is pushed. Read `CLAUDE.md` and `AGENTS.md` first, then this file.

## What was done

1. **Research:** live web sweeps (no training-data recall; every fact carries an F/W fetch id plus
   a raw body) for 11 open category-proposal issues. Evidence lives on branches
   `claude/research-<dir>` (not for merging). The kit (runbook, prompts, fetch helper) and all
   coordinator state are on branch **`claude/research-kit`**, under `research/` and
   `research/coordinator/`.
2. **Decisions:** `docs/sweeps/2026-09-26-new-categories-decisions.md` (on main). The maintainer
   reviewed and confirmed these calls:
   - `world_models` stays preliminary, with a late-October promotion gate.
   - `responsible_ai_measurement` (#30) is PARKED.
   - New group "Embodied & world models".
   - `classic_ml_cv` sits under Infrastructure.
   - Datacenter weights are 0.2/0.8.
   - Org consolidations: fedlearner → bytedance-seed-volcano-engine, mmdetection → open-mmlab.

   The maintainer AMENDED the fit test (15/6/30%) to a provisional screening heuristic. The
   maintainer REVERSED media Q10: the current release governs openness. `wan`, `hunyuan3d` and
   `qwen-image` (closed flagship over an older distributed release) are DEFERRED with evidence for
   both releases, and the availability-vs-openness modeling ruling is still open.
3. **Seed:** PR #720 (squash-merged 2026-09-27 01:39) created 10 preliminary categories with 459
   registry rows.
4. **Promotion:** 9 cloud sessions, one per category, each promoting a first tranche of 10–30
   products as a DRAFT PR against `main`. Each ran an independent read-only verifier subagent
   before opening its PR.

## Promotion PRs (all drafts, base main, labeled `promotion`)

| PR | Category | Products | Publishes? | Session |
|---|---|---|---|---|
| #729 | datacenter_accelerators | 12 | no (stays preliminary) | session_01ESTcatUZdC13oRhJEoVnmS |
| #730 | assurance_evidence | 21 | yes | session_01CN3eeCScJPEtqMEA5MJfFg |
| #731 | robotics_embodied | 22 | yes | session_01LUJGffkhWF31oUKX2vj4W4 |
| #732 | classic_ml_cv | 16 | yes | session_01FnXrwFaXvFbNq9Ez7xkf2v |
| #733 | speech_audio | 22 | yes | session_01BufxZxDJspWy9DC9NbP8hq |
| #734 | multimodal_models | 22 | yes | session_01AUQU8W8bUg16e5qy99QAz1 |
| #735 | federated_learning | 15 (+pysyft, syfthub moved in) | yes | session_01SjxjVa5R3TsZtkgeNcqGAA |
| #736 | model_hubs | 14 | yes | session_01WkXGv8xAQCtt7TVPzHqGVx |
| (not open) | media_generation | 30 | yes | session_01GgaZpNtY3zCz9upUqzgCbH |

## Open items, in priority order

1. **Stage-move label (#730–#736).** Every PR that flips a category to `status: published` fails
   validate's `check_corpus_diff` with "stage moved without the stage-move label". That's expected.
   The label `stage-move` is now on #730–#736. The workflow triggers only on pull_request
   opened/synchronize/reopened and reads `github.event.pull_request.labels`, so runs from before
   the label still fail. A re-run of #733's failed job (run 36287119404, attempt 2) was in
   progress at handoff; it tests whether re-runs see the new label.
   - If it passes: re-run the failed jobs on #730, #731, #732, #734, #735 and #736
     (`actions_run_trigger` rerun_failed_jobs).
   - If it fails with the same message: the label takes effect on each PR's next genuine push.
     The main merges in item 3 provide that. **Never push an empty commit to kick CI.**

   On every one of those PRs, the only failure was this label. The tests passed.
2. **media_generation PR not open.** Its branch `claude/promote-media_generation` has NOT merged
   main yet, so its diff drags in #720's files. It received the merge recipe and the Q10 reversal.
   - If the session is idle with no PR, apply the recipe yourself in a local worktree (below),
     run preflight, push, and open the draft PR (base main, labels `promotion` + `stage-move`).
   - Verify that wan, hunyuan3d and qwen-image are in `scoring_recipe.deferred`, not scored from
     the older release.
3. **Keeping PRs mergeable as they land.** The maintainer merges them one at a time (usually
   squash). After each merge, every remaining promotion branch conflicts on shared files:
   `sources/org_handles.yaml`, the identity fixtures, pinned census tests
   (`test_check_parity`, `test_adoption_evaluation`, `test_serialize_registry`,
   `test_serialize_rubric`, `test_goldens`), and shared org rosters (nvidia, google, meta,
   alibaba-cloud, ...). For each remaining branch:
   - `git merge origin/main` (a merge commit; never rebase or force-push these branches).
   - `org_handles.yaml`: rebuild it as a blockwise union with the logic of
     `research/coordinator/tools/rebuild_org_handles.py`. Never hand-union the hunks, which split
     an entry once already.
   - Org roster `products:` lists: take the union.
   - Regenerate the fixtures: `uv run python -m build.identity_eval --write-fixture
     tests/fixtures/identity_edges_pass.json` and `--write-coverage-baseline`. If a coverage pin
     goes DOWN, add a `lowered_because` string to `tests/fixtures/identity_coverage_baseline.json`
     explaining it. Usually a promoted homepage-only closed row leaves the homepage route, as with
     credo-ai on #730.
   - Update pinned census tests the way their comments instruct.
   - Run `uv run python -m build.preflight` (full), then push.
4. **Review and report.** Once all 9 are open and green, review each PR body: products and why,
   capability rungs and anchors, the verifier's summary, deferrals, published or not. Give the user
   one summary and flag anything that looks wrong.
5. **License-rulings issue.** Not filed yet. Collect every new or custom license string from the
   promotion PR bodies (and §5 of each sweep record) into ONE maintainer issue. Promotions deferred
   those products; `sources/rubrics/` must never be edited in a category PR.
6. **Follow-ups (not started):**
   - Diffusion trainers (kohya sd-scripts, musubi-tuner, SimpleTuner, diffusion-pipe) → the
     `finetuning_code` registry.
   - OCR-first VLMs → `document_conversion`.
   - Embodied-reasoning VLMs (RynnBrain, Hy-Embodied VLM, UnifoLM-ER) → `multimodal_models`.
   - Matrix-3D and Marble → `media_generation`.
   - `dstack` → `deployment`.
   - Axelera Europa → `edge_hardware`.
   - The `world_models` promotion in late October.
   - #30 fairness (10) and carbon (9) lists, recorded in `docs/sweeps/2026-09-26-assurance-evidence.md`.
   - The maintainer ruling on availability vs openness (media Q10).
   - Promotion of the remaining registry rows in each category via `add-product`.

## The merge recipe (squash-merge fallout; tested, zero conflicts)

For a promotion branch that has not yet merged main since #720 landed:

```
git fetch origin main pull/720/head:refs/remotes/origin/pr720
git merge --no-edit origin/pr720
git merge --no-edit -X ours origin/main
git diff --stat origin/main HEAD   # must list only that category's promotion files
```

## Environment facts (they bit before)

- **GitHub API access:** `api.github.com` and curl to `github.com` return 403 for repos outside the
  session. Use repos.ecosyste.ms, ungh.cc, raw.githubusercontent.com, the HF, PyPI and npm APIs,
  WebFetch and WebSearch. The GitHub MCP tools work for this repo.
- **Cloud sessions can't be messaged directly.** To deliver a turn into one, use
  `create_trigger` with `persistent_session_id` and a one-shot `run_once_at` a minute out.
- **Shared usage limit:** all sessions share the account's five-hour limit. All 8 promotions hit
  it once and stopped before pushing. Keep "push WIP at every milestone" in any prompt you send.
- **Session state:** `get_session` shows `status_bucket`, `rate_limit_info` and `task_summary`.
  `list_sessions` output is large, so save it and parse the JSON under `{"ccr":{"data":[...]}}`.
- **This environment:** 4 CPUs, so an in-session Workflow runs only 2 agents at a time. Prefer
  cloud sessions for heavy work.
- **Stale check-ins:** the previous coordinator's check-in routines (e.g. `trig_01RNCXTc8RS4sxkwRKk7zQsG`)
  fire into ITS session. Run `list_triggers`, and delete the stale ones if that session is gone.
  Schedule your own check-ins (15-minute cadence worked).
- **Per-branch table:** `research/coordinator/tools/promo_status.sh` prints last commit and
  products added vs origin/main for each promotion branch.
- **Tracking:** `research/coordinator/sessions.tsv` lists every session (research, seed, promote)
  with its branch.

## Rules that stay in force

- Humans merge. Never approve or merge.
- Never force-push or rewrite history on these branches. Never push empty commits, and never
  close and reopen a PR to kick CI. Never skip or disable tests.
- Never commit `build/notebook_data.json`, `notebooks/` or `tests/goldens/corpus.json`.
- Never edit `sources/rubrics/` in a category PR.
- Never load-modify-dump a file in `sources/`: use surgical edits or `build/components.py`.
- Commit trailer: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. American English, and
  no AI tells in commits, PRs or prose.
