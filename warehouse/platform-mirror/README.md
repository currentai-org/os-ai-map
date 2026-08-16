# warehouse/platform-mirror — read-only copy of the platform models

These files are a **committed copy of the models that run on the OSO platform to build the gap
map's data** (the openness scores, the evidence behind them, and the adoption/capability
signals). They live here so anyone reading the repo can see how the data is produced, without
needing platform access.

**The platform is the source of truth, not this folder.** Do not edit these files to change how
anything is computed — nothing here is deployed. The real editing/deploy happens on the platform
(the working copies you push from live in `currentai-org/{tools,udms}/`, outside this repo). A
copy can only drift from what's live, so treat any mismatch as "this copy is stale" and re-sync.

**Provenance is in [`manifest.yaml`](manifest.yaml)** — for each file, the deployed model it
mirrors, the revision it reflects, and a hash of the checked-in bytes, plus the sync date. That's
what makes this a checkable snapshot rather than just a copy. `tests/test_platform_mirror.py`
keeps the manifest and the files in step; a credentialed job that compares against the live
platform to catch drift is a planned follow-up.

## What each file is

| File | Platform table |
|---|---|
| `evidence_product_evidence.sql` | `currentai.evidence.product_evidence` — the evidence behind each scoring dimension |
| `scores_openness_facts.sql` | `currentai.scores.openness_facts` — resolves each dimension per product |
| `scores_openness_computed.sql` | `currentai.scores.openness_computed` — walks each openness ladder in SQL |
| `github_repo_state.py` | `currentai.signal_github.repo_state` — the fetcher, at repo grain |
| `github_product_adoption.sql` | `currentai.signal_github.product_adoption` — bands stars, the last-resort adoption route |
| `huggingface_hub_state.py` | `currentai.signal_huggingface.hub_state` — the fetcher, at artifact grain |
| `huggingface_product_adoption.sql` | `currentai.signal_huggingface.product_adoption` — bands Hub downloads per product |
| `pypi_package_downloads.sql` | `currentai.signal_pypi.package_downloads` |
| `artificialanalysis_models.py` | `currentai.signal_artificialanalysis.model_evaluations` |
| `lmarena_leaderboard.py` | `currentai.signal_lmarena.text_leaderboard` |
| `semanticscholar_paper_citations.py` | `currentai.signal_semanticscholar.paper_citations` |
| `goodailist_repos.py` | `currentai.signal_goodailist.repo_catalog` |
| `packages_*.{sql,py}` | `currentai.signal_packages.*` — package-adoption successor (all three staged, see #314) |
| `*.schema.json` | the output columns each model declares |

Each fetcher is paired with a derivation: the `*_state` model holds a secret and calls an API
at artifact grain, and the `*_product_adoption` model bands it at product grain, so a rubric
change re-bands without re-fetching. The three `product_adoption` models are separate tables
reading separate signals — stars, Hub downloads, package-registry downloads — and one of them
was mirrored against the other two's names until 2026-08-16. Read the header of a `.sql` file
rather than its filename to know what it builds; `tests/test_platform_mirror.py` now checks
that header against this manifest.

The `check_parity` gate is what actually enforces that `scores_openness_computed.sql` and
`build/check_rubric.py` agree — this copy is for reading, that gate is for correctness. See
`docs/operations/deploy-models.md`.
