# Handoff: #764 freshness sweep and open follow-ups (2026-09-29)

This directory carries the working state of the coordinating session. It lives on a draft PR
so a new session can read it. **Do not merge it.** Close the PR once the work below is done.

## Files

| file | what it is |
|---|---|
| `playbook.md` | The exact prompt each child session got, with the 20 lessons from #772 and #774. Pass it verbatim, with the category name appended after "## Your category". |
| `sweep_sessions.json` | The roster: `running` maps category to child session id, `queued` is the not-yet-launched categories in launch order, `prs` records PRs seen so far. |
| `recon.json`, `recon.txt` | The 28 Sep adoption reconciliation reading (74 `tier_change` + 73 `route_disagreement` rows, observations materialized by a MANUAL run). This is needed for the 5 Oct re-band. |
| `apply_finetuning_code.py` | The deterministic applier used for #774. It is a reference only: `TODAY` and `ROOT` are hard-coded, and it expects the workflow's packet/evidence/prose JSON shape. |

## State at handoff (2026-09-29 00:35 UTC)

Merged so far for #764: #772 (search_retrieval), #774 (finetuning_code), #776 (embeddings_retrieval).
`main` now carries the Neon `partial` freshness basis, so children no longer need the cherry-pick
(lesson 15 no-ops).

Ten child sessions are running, one per category, each on `claude/refresh-<category-with-dashes>`,
tagged `refresh-sweep-764`, and each opening one draft PR labeled `freshness`:

| category | session | PR / status at handoff |
|---|---|---|
| embeddings_retrieval | session_01Wnh7xbuEToC1BbyN27K6qw | #776, merged |
| storage | session_01Euz9KpdiGYK1E8dBUJdNBn | #777, reviewed LGTM by the user. **Merge once `validate` is green** (squash, mark ready first). Its first `validate` failed only because #776 merged underneath it (see below). `origin/main` was merged in at 0863d50b, fast preflight passed, and CI is re-running. |
| ml_orchestration | session_011PyXi5EfTLDhU8ZzUcKTxM | #778, CI running, not yet reviewed |
| federated_learning | session_011q7aYv22k6RxaRhovEK9CZ | preflight, about to push |
| agent_protocols | session_017HRxWvLtXa5UxRzLB28W1C | pushed, opening PR |
| document_conversion | session_01QwixtKyeQzUAufX8qz5nhf | was blocked on the `partial` fix; merging `origin/main` clears it |
| orchestration_agents | session_016cnhGwn9GCxCy8PnqrohvG | research running |
| ui_api | session_01BZPskJtP38uLwefeZuXZ2o | research running |
| training_synthetic_datasets | session_01FKb7dtkFN4UsuFDXeskjDw | research running |
| finetuned_chat | session_019byzHv3Vp6NPJu5UBE1Fa3 | 37 products, research running (~1h) |

Queued, not launched (11): benchmark_eval_data, base_pretrained, evaluation_code, safeguards,
deployment, telemetry_observability, ml_frameworks, inference_code, dataset_processing_tools,
edge_hardware, agent_tools_connectors.

Launches were held at 00:25 UTC because the children reported the account's **seven-day** rate
limit at `allowed_warning` (`rate_limit_info` in `get_session`). Resume launching only when it
clears. Keep about 10 running at once: they share the account limit.

## How to drive the sweep

- Check each running session with `get_session`. `status_bucket` and `post_turn_summary` say
  where it is. A finished child ends idle with a green draft PR and does not report back.
- For each freed slot, `create_session` with `source_url https://github.com/currentai-org/os-ai-map`,
  `outcome_branch claude/refresh-<category-with-dashes>`, `tags ["refresh-sweep-764"]`, title
  `Refresh <category> (#764)`, prompt = `playbook.md` + the category name. Update the roster.
- Child PRs merge only after the user reviews them. Never merge without the user's go-ahead.
  The user reviews for score moves smuggled into freshness, weak `shows`, and prose that is
  reviewer commentary.
- Do not comment on #764 per category. Post one aggregate comment when the sweep is done.

## Every merge turns the other open sweep PRs red

`validate` runs `build.check_corpus_diff --base origin/main`. Once one sweep PR merges, every other
open sweep PR whose branch predates that merge fails with `silent rewrites of untouched products:
<slug>|<axis> changed but sources/... did not`. The named products are the ones the merged PR
touched. The fix is to merge `origin/main` into the PR branch (a merge commit, never a rebase),
run `build.preflight`, and push. After each merge, do this for every open sweep PR, or tell the
child session to do it. Lesson 21 in `playbook.md` tells new children to do it themselves.

## Other open items

1. **5 Oct adoption re-band: one PR.** On or after 2026-10-05, check that the week's adoption
   reconciliation read a SCHEDULED observations materialization (`binding_status bound`,
   `run_trigger_type SCHEDULED`). Re-band only the products whose `tier_change` disagreement
   appears in both `recon.json` (28 Sep) and this week's reading. Set level and reach to the
   measured band, then run `build.adoption_freshness --live --apply` to bind `derived_from` and
   the dates. Leave the `route_disagreement` rows (the instruments differ) for a separate PR. Run
   `build.preflight` before pushing. Score notes carry no figures or dates. Adoption axes the
   sweep held for this reason get their dates from this PR.
2. **#775:** Mosaic end-of-life follow-up from #774.
3. **#773:** `check_declarations` does not parse raw.githubusercontent.com URLs (why lesson 2 exists).
4. **Tracker artifact** https://claude.ai/artifact/KHTAnLVmA4pkfUgmYzbyRd. Republish when the sweep
   has moved enough to be worth it.
