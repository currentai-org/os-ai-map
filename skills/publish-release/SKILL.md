---
name: publish-release
description: Use when cutting a versioned release of os-ai-map — deciding the version bump, moving the changelog's Unreleased notes into a dated release, tagging it, and pushing. Maintainer step. For adding a single changelog line, just edit the Unreleased section in your PR.
---

# Publish a release

Cut a versioned release of the repository: turn the accumulated `## [Unreleased]` changelog
notes into a dated, numbered release, bump the version, tag it, and push. This is a
**maintainer step** — it writes a git tag and pushes to `main`. Editors do not run it; they
add one line to the Unreleased section in their PR and stop.

This skill versions **the `os-ai-map` repository** — its source YAML, schemas, build
pipeline, and docs. It does **not** publish the live notebook or the warehouse models; those
are separate maintainer runbooks (`docs/operations/publish-map.md`,
`docs/operations/deploy-models.md`). A repo release and a notebook publish are different acts.

## What tracks a release

- **`CHANGELOG.md`** — the human record, in [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
  format. One `## [Unreleased]` section collects changes as they land; a release freezes it
  into a `## [X.Y.Z] - YYYY-MM-DD` section.
- **`pyproject.toml` `version`** — the machine record. It must equal the latest released
  version at all times.
- **An annotated git tag `vX.Y.Z`** — the immutable marker. The tag and the two files above
  always agree.

## Decide the version bump

Read the Unreleased notes and pick the largest applicable step. This project follows
[Semantic Versioning](https://semver.org/), read for a data-and-schema repo:

| Bump | When | Examples in this repo |
|------|------|-----------------------|
| **MAJOR** (`X`) | A breaking change to a published contract — anything a downstream consumer (e.g. `aipotluck.org`) must adapt to. | Renaming or removing a schema field; changing a slug convention; restructuring an openness/adoption/capability axis (a `migrate-axis` run); removing a category. |
| **MINOR** (`Y`) | A backward-compatible addition. | New products, categories, or data sources; a new optional schema field; a new skill or workflow. |
| **PATCH** (`Z`) | A correction that changes no structure. | Score-value corrections; prose or doc fixes; evidence refreshes; build-helper bug fixes. |

If the Unreleased section is empty, there is nothing to release — stop. Before `1.0.0`, a
MAJOR-worthy change bumps the MINOR instead (`0.y` may break); say so in the changelog.

## Steps

1. **Confirm a clean tree on `main`.** `git status` is clean and `git pull` is current. Cut
   releases from `main` so the tag matches the published history.
2. **Choose the version** with the table above. Call it `X.Y.Z`.
3. **Freeze the changelog.** In `CHANGELOG.md`:
   - Rename `## [Unreleased]` to `## [X.Y.Z] - YYYY-MM-DD` (today's date, ISO 8601).
   - Drop any now-empty subsections (keep only the headings that have entries).
   - Add a fresh, empty `## [Unreleased]` above it.
   - Update the link definitions at the bottom:
     ```
     [unreleased]: https://github.com/currentai-org/os-ai-map/compare/vX.Y.Z...HEAD
     [X.Y.Z]: https://github.com/currentai-org/os-ai-map/releases/tag/vX.Y.Z
     ```
     (On the first release only, replace the seed `[unreleased]: .../commits/main` line.)
4. **Bump the version.** Set `version = "X.Y.Z"` in `pyproject.toml`. It must match the tag.
5. **Commit** the changelog and version bump together:
   ```bash
   git commit -am "chore(release): v X.Y.Z"   # write the version without the space
   ```
6. **Tag**, annotated, with the changelog section as the message body:
   ```bash
   git tag -a vX.Y.Z -m "vX.Y.Z"
   ```
7. **Push the branch and the tag:**
   ```bash
   git push -u origin <branch> && git push origin vX.Y.Z
   ```
8. **(Optional) GitHub Release.** Create a release from tag `vX.Y.Z`, pasting that version's
   changelog section as the body. Use the GitHub MCP tools; do not invent release notes —
   copy the changelog verbatim.

## Rules

- **The three records agree.** Tag `vX.Y.Z`, `pyproject.toml` version, and the newest
  `CHANGELOG.md` heading are always the same string. A mismatch is a release bug.
- **Never edit a released section.** Once `## [X.Y.Z]` is dated and tagged, it is history.
  Corrections go in a new release.
- **Tags are immutable.** Never move or delete a pushed tag. A mistake is fixed forward with
  the next PATCH.
- **One line per change, in plain English.** Past tense, user-facing effect first, PR linked.
  No AI tells, American English (per `CLAUDE.md`).
- **Do not commit** `build/notebook_data.json` or `notebooks/` — the bot owns them, and CI
  blocks hand edits.

## Validation

```bash
# The three records must name the same version:
grep '^version' pyproject.toml
grep -m1 '^## \[' CHANGELOG.md
git describe --tags --abbrev=0        # after tagging

# The changelog parses as Keep a Changelog (Unreleased present, headings well-formed):
grep -q '^## \[Unreleased\]' CHANGELOG.md && echo "Unreleased section present"
```
