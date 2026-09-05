---
name: publish-release
description: Use when cutting a versioned release of os-ai-map — deciding the version bump, moving the changelog's Unreleased notes into a dated release through a review PR, then tagging the merged commit. Maintainer step. For adding a single changelog line, just edit the Unreleased section in your PR.
---

# Publish a release

Cut a versioned release of the repository: turn the accumulated `## [Unreleased]` changelog
notes into a dated, numbered release. This is a **maintainer step**. The release goes in
through a normal review PR like any other change; the git tag is applied afterward, to the
commit that actually landed on `main`. Editors do not run it — they add one line to the
Unreleased section in their own PR and stop.

This skill versions **the `os-ai-map` repository** — its source YAML, schemas, build
pipeline, and docs. It does **not** publish the live notebook or the warehouse models; those
are separate maintainer runbooks (`docs/operations/publish-map.md`,
`docs/operations/deploy-models.md`). A repo release and a notebook publish are different acts.

## What tracks a release

A release's version is written in **four** places. They must all read the same string, or the
release lies about itself:

1. **`CHANGELOG.md`** — the newest dated heading, `## [X.Y.Z] - YYYY-MM-DD`
   (the undated `## [Unreleased]` section does not count).
2. **`pyproject.toml`** — `[project].version`.
3. **`uv.lock`** — the root package (`source = { virtual = "." }`). Bumping `pyproject.toml`
   without re-locking leaves this stale, so re-lock in the same commit.
4. **The annotated git tag** — `vX.Y.Z`, on the merged `main` commit.

`tests/test_release_metadata.py` enforces this. It checks the three in-tree records (1–3) on
every PR, and the tag (4) as well when run in a tag context. Do not hand-eyeball the numbers;
run the gate.

## Decide the version bump

Read the Unreleased notes and pick the largest applicable step. This project follows
[Semantic Versioning](https://semver.org/), read for a data-and-schema repo:

| Bump | When | Examples in this repo |
|------|------|-----------------------|
| **MAJOR** (`X`) | A breaking change to a published contract — anything a downstream consumer (e.g. `aipotluck.org`) must adapt to. | Renaming or removing a schema field; changing a slug convention; restructuring an openness/adoption/capability axis (a `migrate-axis` run); removing a category. |
| **MINOR** (`Y`) | A backward-compatible addition. | New products, categories, or data sources; a new optional schema field; a new skill or workflow. |
| **PATCH** (`Z`) | A correction that changes no structure. | Score-value corrections; prose or doc fixes; evidence refreshes; build-helper bug fixes. |

If the Unreleased section is empty, there is nothing to release — stop.

Before `1.0.0` the repository is in rapid iteration and `0.y` may break, so a MAJOR-worthy
change is simply a MINOR bump. Do not annotate it in the changelog and do not raise it as a
decision at release time — pick the number from the table and move on. If a *named* downstream
consumer has to act, tell them directly instead. Revisit at 1.0.0.

## Steps

The tag must point at reviewed, merged history — never at a branch tip that has not landed.
So the file changes go through a PR first, and only then does the tag get cut.

1. **Start from current `main`.** `git checkout main && git pull --ff-only`; `git status`
   clean. Choose the version `X.Y.Z` with the table above.
2. **Branch:** `git checkout -b release/vX.Y.Z`.
3. **Freeze the changelog.** In `CHANGELOG.md`:
   - Rename `## [Unreleased]` to `## [X.Y.Z] - YYYY-MM-DD` (today's date, ISO 8601).
   - Drop any now-empty subsections (keep only the headings that have entries).
   - Add a fresh, empty `## [Unreleased]` above it.
   - Update the link definitions at the bottom to **comparison links between consecutive
     versions** (a release compares against the one before it):
     ```
     [unreleased]: https://github.com/currentai-org/os-ai-map/compare/vX.Y.Z...HEAD
     [X.Y.Z]:      https://github.com/currentai-org/os-ai-map/compare/vPREV...vX.Y.Z
     ```
     The very first release has no predecessor, so it links to `releases/tag/vX.Y.Z` instead.
4. **Bump and re-lock.** Set `version = "X.Y.Z"` in `pyproject.toml`, then run `uv lock` so
   `uv.lock`'s root package matches. Both files are part of the commit.
5. **Validate locally** before opening the PR:
   ```bash
   uv run python -m build.validate            # sources clean
   uv run pytest -q                           # full suite, incl. test_release_metadata
   ```
6. **Commit and push the release branch:**
   ```bash
   git add CHANGELOG.md pyproject.toml uv.lock
   git commit -m "chore(release): vX.Y.Z"
   git push -u origin release/vX.Y.Z
   ```
7. **Open the release PR** (`release/vX.Y.Z` → `main`) and get it reviewed and merged like any
   other change. Do not tag yet.
8. **Verify the merged commit.** After merge:
   ```bash
   git fetch origin main
   git checkout main && git pull --ff-only
   git rev-parse HEAD                          # the exact SHA the tag will point at
   uv run pytest tests/test_release_metadata.py -q
   ```
   Confirm the three in-tree records all read `X.Y.Z` before going further.
9. **Tag the merged commit,** annotated, using that version's changelog section as the message
   body (not a bare `-m "vX.Y.Z"`):
   ```bash
   VERSION=X.Y.Z
   awk -v v="$VERSION" '
     $0 ~ "^## \\[" v "\\]" {f=1; print; next}
     f && /^## \[/ {exit}
     f {print}
   ' CHANGELOG.md | git tag -a "v$VERSION" -F -
   ```
10. **Push the tag,** and confirm the metadata gate passes in a tag context:
   ```bash
   git push origin "v$VERSION"
   RELEASE_TAG="v$VERSION" uv run pytest tests/test_release_metadata.py -q
   ```
11. **(Optional) GitHub Release.** Create a release from tag `vX.Y.Z`, pasting that version's
    changelog section (the same text the tag carries) as the body. Do not invent release notes.

## Rules

- **The four records agree.** The tag, `pyproject.toml`, the `uv.lock` root package, and the
  newest dated `CHANGELOG.md` heading are all the same string. `tests/test_release_metadata.py`
  is the gate; a mismatch is a release bug, not a formatting nit.
- **A tag points only at merged `main` history.** Never tag a release-branch commit before it
  merges — the merged SHA differs, and the tag would mark history that never shipped.
- **Never edit a released section.** Once `## [X.Y.Z]` is dated and tagged, it is history.
  Corrections go in a new release.
- **Tags are immutable.** Never move or delete a pushed tag. A mistake is fixed forward with
  the next PATCH.
- **One line per change, in plain English.** Past tense, user-facing effect first, PR linked.
  Only notable, user-facing changes earn an entry — not bot regenerations, dependency bumps,
  internal refactors, or routine evidence refreshes. No AI tells, American English (per
  `CLAUDE.md`).
- **Do not commit** `build/notebook_data.json` or `notebooks/` — the bot owns them, and CI
  blocks hand edits.

## Validation

```bash
uv run pytest tests/test_release_metadata.py -q   # the four-record gate (three in-tree, +tag)
uv run python -m build.validate                   # sources still clean
uv run pytest -q                                   # full suite
```
