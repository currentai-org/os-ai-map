---
name: audit-repo-accuracy
description: Use when checking that os-ai-map's own instructions still describe the system — skills, workflows, reference docs, AGENTS.md and CLAUDE.md, tests, allowlists and fixtures, and the rulings log — against what the code and corpus actually do. Read-only; it files findings for a person in one living issue and fixes nothing. Run on a schedule, or before a release.
---

# Audit repo accuracy

Agents follow what the docs say. When a doc drifts from the code, every agent that reads it
implements the drift, and none of them fails loudly: the defects in `AGENTS.md`'s "one fact, one
owner" section each reported success over a narrower question than the one they claimed to
answer. The gates catch the drift someone anticipated. This audit reads for the drift nobody
wrote a gate for, and turns each instance into either a fix a person approves or a new gate.

It is **read-only**. It never commits, and it never opens a PR. A finding is a question for a
person, and the answer may be that the doc is right and the code is wrong.

## Checks

Work through them in order. Record every check, including the ones that found nothing, because
a report that lists only failures cannot be told apart from one that skipped half its checks.

### 1. Skills and workflows
- Every command a `SKILL.md` or `docs/workflows/*.md` tells an agent to run exists and answers
  `--help`. Run each one.
- Every gate a workflow's validation section lists is one `build.preflight` or CI actually runs,
  and every gate CI runs on that surface is listed.
- A skill that says it wraps a workflow does not restate the workflow's procedure. A restated
  step drifts, so find it and name the line.
- `skills/registry.yaml` still matches each skill's role: a skill described as read-only does
  not write, and an internal skill is not on the editorial path.

### 2. Claims in prose
- **Hand-typed counts.** `docs/README.md` forbids a count a person must remember to update. Grep
  `AGENTS.md`, `CLAUDE.md`, `README.md`, `CONTRIBUTING.md`, `docs/` and `skills/` for numbers
  that describe a mutable set (products, categories, assets, contracts, tests), and compare
  each with the value computed from the repo. A mismatch is a finding. A match is also a
  finding, of lower severity, because the sentence should be structural.
- **Module maps.** `AGENTS.md`'s `build/` stage map names modules that exist, and each module is
  in the family its docstring says it belongs to.
- **Paths and names.** Tests cover paths that do not resolve. This check covers names that do
  resolve but mean something else now: a table, a field or a label a doc describes differently
  than the schema, `warehouse/assets.yaml` or `warehouse/dependencies.yaml` does.

### 3. Tests, allowlists and fixtures
- A `skip`, `xfail` or allowlist entry whose stated reason no longer holds.
- The draining allowlists under `sources/allowlists/` and the backlogs in
  `tests/test_doc_chronology.py` and `tests/test_build_docstrings.py`: entries that could now
  be removed, and whether each list is shrinking.
- Goldens and baselines that bind on `main` (ADR-004): whether the last regenerate on `main` was
  green, and whether any fixture is edited by hand in a way its regenerator would overwrite.

### 4. The rulings log
- An `in-force` ruling that changes a rule but has no `lands_in`: the rule was decided and never
  written into its normative home.
- A `lands_in` home that no longer states what the ruling says.
- A `deferred` ruling older than thirty days, and whether the reason it was deferred still holds.
- An `executor: agent` ruling with no `applied_in`, older than fourteen days.

### 5. OSO copies
Where skills are mirrored to OSO as memories, list each memory whose content differs from the
repo file it was copied from. The repo is the source of truth. A difference is either a sync
that did not run, or someone editing the copy.

## Report

One living GitHub issue in `currentai-org/os-ai-map`, titled `Repo accuracy audit`. Create it
the first time, then add one comment per run. Never open a second issue. Each comment has, in
this order:

1. A one-line verdict: the finding count and the worst severity.
2. The findings, most severe first. Each one gives `file:line`, what the doc says, what is true,
   the evidence (the command and its output, or the computed value), and a proposed fix. Where
   the fix is "add a gate", name the test file it belongs in.
3. The checks that found nothing, one line each.
4. Anything the audit could not check, and why. An unreachable warehouse or a denied tool call
   is recorded as unverified, never skipped silently.

Severity: **high** when an agent following the doc would change the corpus wrongly; **medium**
when it would waste a run or fail a gate; **low** when only a reader is misled.

When a finding is accepted, the fix lands through an ordinary PR, and a finding accepted as a
class ("hand-typed counts in CLAUDE.md are not allowed") becomes a ruling in
`docs/rulings/log.yaml`.
