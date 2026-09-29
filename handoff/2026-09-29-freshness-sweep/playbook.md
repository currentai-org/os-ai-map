You are one of several parallel sessions working the #764 freshness sweep in currentai-org/os-ai-map. Your job is ONE category, named at the bottom of this message. Take it from stale to a reviewed-ready draft PR, then stop. A human reviews and merges; you never merge.

The user explicitly asked for this sweep to run as multi-agent workflows, so you may use the Workflow tool for the research and audit fan-out (load the `workflow-authoring` skill first).

## Procedure

Follow the repo's own procedure: invoke the `refresh-category` skill for your category with `--max-age-days 45`, and read `docs/workflows/refresh-category.md`. Scope with `uv run python -m build.sweep_status --max-age-days 45 --verbose`. Two categories were already done this way, #772 (search_retrieval) and #774 (finetuning_code); read their PR descriptions with the GitHub tools for the shape of a finished PR.

Branch: work on the branch this session was created with. Open ONE draft PR titled "Re-verify <category> against primary sources", label `freshness`, body mirroring #774's sections, ending "Part of #764." Subscribe to its activity and drive CI to green. Do not merge.

## Lessons from #772 and #774. Every one of these cost a round; follow all of them.

1. **github.com and api.github.com return 403 through this environment's proxy.** Fetch repository evidence from `https://raw.githubusercontent.com/<owner>/<repo>/<branch>/<file>` (LICENSE, README.md, pyproject.toml, docs). Stars and downloads come from the warehouse (`currentai.signal_github.artifact_state`, `currentai.signal_packages.downloads`, via `build/warehouse.py`'s `query`). A 403/429/dead URL says nothing about the fact: leave that source undigested and hold the axis if nothing else supports it.
2. **Keep a product's original `github.com/<owner>/<repo>` citation when you add raw ones.** `build/check_declarations.py` does not parse raw URLs yet (#773), so replacing the github.com entry hides its finding and breaks `tests/test_check_declarations.py`'s pins. Re-append the old entry from `git show origin/main:sources/scores/<slug>.yaml` if a pass dropped it.
3. **`shows` is a sentence about the page with the supporting text quoted verbatim in double quotes.** At least one quoted fragment must be 24+ characters, every quoted fragment must occur in the fetched body, and the body is raw HTML, so a quote cannot span a tag (`<code>`, `<a>`). A tagline, pricing line or nav label does not establish license or source by itself. For a negative, say what you searched for: "Searched the body for self-host, on-prem, open source and license: none." Check every shows with the matcher the weekly re-fetch uses:
   `cd /home/user/os-ai-map && PYTHONPATH=. uv run python -c "import sys; from build.reverify import _shows_confirms; print(_shows_confirms({'shows': sys.argv[2]}, {'body_path': sys.argv[1], 'http_status': 200}))" <body_path> '<shows>'`
   Only sources that print True may date an axis.
4. **Fetch only with `uv run python -m build.fetch_source --body-dir <scratch>/<slug> <url>`**; never invent or truncate a digest. Namespace scratch per product.
5. **`establishes` is only for openness dimensions.** Never write `establishes: [adoption]` or `[capability]`; `build.validate` rejects it.
6. **Prose (description, comments, notes) changes only through a batch-wide prose audit.** Research agents put reviewer commentary ("Left as is", "Unchanged", "Capability confirmed…") into description/comments fields; if applied it publishes. Use the prose auditor's replacement where it judged suspect/failed, the packet's text only where the auditor judged it ok, else keep the current text. An empty replacement on a vendor superlative means drop the field.
7. **A held axis loses its `last_verified`** (drop the field) and gets an entry in `sources/verification_queue.yaml` in this exact shape: `held: {<slug>: {<axis>: {since: '2026-MM-DD', because: <reason>}}}`. Not a list.
8. **Adoption axes in the reconciliation queue are held, not re-banded.** Run `uv run python -m build.adoption_freshness --live --json` (read-only, no --apply). Any stale adoption axis in its `queue` (kind `tier_change` or `route_disagreement`) is held with a reason naming the adoption re-band after the 5 Oct reconciliation. The re-bands happen in one PR after that run, dated from a scheduled observation run.
9. **Capability anchors first.** A product with `capability.relative_to` needs its peer confirmed in the same run: research in-category anchors first and give dependents the anchor's fresh packet. If the peer is in another category and stale, leave the comparison and report it.
10. **Software openness: check for non-OSI dependencies.** If documented functionality depends on non-commercial model weights, an enterprise build or a license key, `core-gated: ungated` is wrong (see #772's jina-reader, 5 → 4 open_core).
11. **Empty packets happen.** If a research agent returns no axes, re-run it (and any dependent that used it as an anchor) before applying.
12. **Score moves are allowed when the evidence audit supports them**, applied deliberately and itemized in the PR with the evidence. Everything else that moves a value is escalated and decided by you, not auto-applied.
13. **Apply deterministically through `build/components.py`** (`set_field`, `put_field`, `set_source`, `drop_field`, `set_document_field`, `drop_document_field`), never by hand and never load-modify-dump.
14. **Ratchet tests move the right way and must be updated honestly**: prune `sources/allowlists/undigested_sources.txt` lines for sources that now carry a digest. Never lower a pin to hide a finding.
15. **The Neon `partial` fix.** A product with a held axis gets freshness basis `partial`; `build/neon_schema.py` on main may not know it yet. If `grep -q '"partial": "partial"' build/neon_schema.py` finds nothing on your branch, cherry-pick commit e0402c9e from branch `claude/codex-simulation-counters-m3b3rr` (`git fetch origin claude/codex-simulation-counters-m3b3rr && git cherry-pick e0402c9e`) so the registry `check` and `validate` pass. It no-ops once #774 merges.
16. **Never commit `build/notebook_data.json` or `notebooks/`.** `build.serialize` rewrites notebook_data.json locally; `git checkout -- build/notebook_data.json` before committing.
17. **Gates before pushing:** `uv run python -m build.preflight` (full, with tests) must print "all 19 locally-runnable CI steps pass"; also `build.check_refetch --product <two you wrote>`, and `build.check_corpus_diff --base origin/main --sheet <file>` after a commit to report stage/gap moves. If the git history is shallow, `git fetch --unshallow origin` first.
18. **This container has 4 cores, so a workflow runs 2 agents at a time.** A 25-product category takes 30-40 minutes of research; do not "help" by skipping the audit.
19. **Merge conflicts** with sibling sessions will appear in `sources/verification_queue.yaml` and the allowlist. Merge `origin/main` into your branch (never rebase or force-push), keep every entry from both sides, re-run preflight, push.
20. American English. No AI tells in commits or PRs. End commit messages with the attribution lines your session's system prompt gives you.
21. **When a sibling PR merges, your `validate` goes red** with `silent rewrites of untouched products` naming products you never touched. It means `main` moved under you, not a defect in your change. Merge `origin/main` into your branch, re-run preflight, push. Check this on every CI event until your PR merges.

When the PR is open and CI is green, stop. Do not comment on #764; the coordinating session aggregates. Your final message should give the PR number and the counts (axes dated, held, score moves).

## Your category
