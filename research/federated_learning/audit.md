# Federated learning sweep: independent audit (2026-09-26)

Auditor: fresh subagent, given only the paths. Scope: `sweep.md`, `rows.yaml`, `fetch-log.tsv`,
`web-log.tsv` and `raw/` in `research/federated_learning/`. The audit re-fetches are logged in
`fetch-log.tsv` as F0167–F0248 (label prefix `audit:`), all on 2026-09-26 between 20:17Z and 20:19Z.
Nothing in `sweep.md` or `rows.yaml` was edited.

## Verdicts

| # | check | result |
|---|---|---|
| 1 | Re-fetch 15+ claims live across §6b | **PASS**. 16 rows sampled (every second row), 0 failures |
| 2 | Unsourced facts | **FAIL**. Every §6b cell carries a logged id, but 10 license cells rest on a label, not the text, and several §3/§4/§7/§8 claims go beyond what their cited excerpt says |
| 3 | Every rows.yaml artifact resolves live | **FAIL**. `pypi: federatedscope` returns 404 on pypi.org |
| 4 | Schema and dedup | **PASS**. The schema validates and nothing collides with the index (one org-slug reuse question) |
| 5 | Counts reconcile, §2 recomputes | **FAIL**. rows.yaml has 30 distinct orgs, not 31. Everything else recomputes |
| 6 | Recency and breadth | **PASS**, with notes. All timestamps are from this run. One search-reachable candidate was missed (FLGo) |

## Check 1: live re-fetch sample (16 of 33 §6b rows, every second row)

Tolerances: a date may drift one day. A wrong license, a wrong owner, an archived repo reported
active, or a figure off by more than 25% fails.

| §6b row | canonical id (live) | archived/fork | last push | license (live, text where re-read) | adoption (live) | release (live) | result |
|---|---|---|---|---|---|---|---|
| flower | flwrlabs/flower F0167 | no/no | 2026-09-21 | apache-2.0 F0167 | flwr 74,715/mo F0218; pypistats 74,715 F0229; 7,140 stars | flwr 1.38.0, 2026-09-22 F0198 | match |
| fedml | FedML-AI/FedML F0168 | no/no | 2025-10-28 | apache-2.0; PyPI "Apache 2.0" F0200 | 2,132/mo F0219 | 0.9.6, 2025-02-24 F0200 | match |
| substra | Substra/substra F0169 | no/no | 2024-10-14 | apache-2.0 | 750/mo F0220 | 1.0.0, 2024-10-14 F0202 | match |
| tensorflow-federated | google-parfait/tensorflow-federated F0170 | no/no | 2026-09-19 | apache-2.0 | 2,230/mo F0221 | 0.87.0, 2024-09-17 F0203 | match |
| fedjax | google/fedjax F0171 | no/no | 2026-08-06 | apache-2.0 | 69/mo F0222 | 0.0.17, 2023-07-12 F0204 | match |
| fed-biomed | fedbiomed/fedbiomed F0172 | no/no | 2026-09-22 | label "other"; text Apache-2.0 behind Inria/UCA notice F0230 | 375/mo F0223 | 6.4.1, 2026-08-06 F0206 | match |
| secretflow | secretflow/secretflow F0173 | no/no | 2026-04-24 | Apache-2.0 text F0234 | 435/mo F0224 | 1.14.0b0, 2025-09-26 F0208 | match |
| pfl-research | apple/pfl-research F0174 | no/no | 2026-09-16 | Apache-2.0 text F0239 | pfl 64/mo F0225 | 0.5.2, 2026-09-16 F0210 | match |
| fedlab | SMILELab-FL/FedLab F0175 | no/no | 2025-10-20 | apache-2.0 | 497/mo F0226 | 1.3.0, 2022-10-26 F0211 | match |
| fedlearner | bytedance/fedlearner F0176 | no/no | 2026-07-06 | Apache-2.0 text F0237 | 900 stars | GH v1.5, 2021-03-22 F0240 | match |
| flame-fl | cisco-open/flame F0177 | no/no | 2025-11-06 | Apache-2.0 text F0238 | 59 stars | GH v0.4.0, 2023-12-15 F0241 | match |
| p2pfl | p2pfl/p2pfl F0178 | no/no | 2026-05-09 | GPL-3.0 text F0233; PyPI GPL-3.0-only F0214 | 66/mo F0227 | 0.4.4, 2025-09-30 F0214 | match |
| fedtree | Xtra-Computing/FedTree F0179 | no/no | 2025-01-20 | Apache-2.0 text F0235 | 153 stars | sweep says "not fetched"; live GH v1.0.5, 2023-01-26 F0242 | match (gap, see issue 9) |
| metisfl | bioint/MetisFL F0180 | no/no | 2024-06-27 | Clear BSD (USC) text, "NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS" F0231 | 523 stars | none | match |
| xfl | paritybit-ai/XFL F0181 | no/no | 2026-03-17 | Apache-2.0 text F0236 | 43 stars | sweep says "not fetched"; live GH v1.4.1, 2024-02-27 F0243 | match (gap, see issue 9) |
| fl4health | VectorInstitute/FL4Health F0182 | no/no | 2026-09-21 | Vector Institute License, last updated 12-08-2025, academic/sponsor/partner only, "not permitted to ... Sell the Work" F0232 | 56 stars | not re-fetched | match |

The first ecosyste.ms re-fetches returned the same byte counts as the sweep's own, so they may be
cached server-side for the day. The PyPI JSON and the LICENSE texts are independent reads, and they
agree.

## Check 2: unsourced facts

Mechanical pass over §6b: every evidence cell carries at least one `F`/`W` id. Every id exists in
the logs, and every cited `F` row is HTTP 200 except F0012, a 404 cited on purpose as the absence of
`tensorflow/federated` on ecosyste.ms (acceptable, see issue 12). Every cited `W` row has an excerpt.
The §6c list matches the §6b ids exactly, in both directions. Issues 4–8 and 10–11 come from the
spot-check of §1–§5, §7, §8 and §9.

## Check 3: artifacts resolve

- **GitHub (31 repos):** all 31 resolve on repos.ecosyste.ms with the declared `owner/repo` as
  `full_name`, and none is archived or a fork (F0167–F0197).
- **PyPI (18 packages declared, not 17):** 17 resolve on pypi.org JSON (F0198–F0215), and each one's
  `project_urls`/`home_page` points back to the declared repo, with one exception. vantage6 lists
  no project URLs, but its install doc is cited (W0023), so it passes. openfl points to
  `securefederatedai/openfl`, which redirects to the declared repo (W0027).
  **`federatedscope` returns 404** on `pypi.org/pypi/federatedscope/json`, and also on the
  `FederatedScope` spelling and the `/simple/` index (F0205, F0216, F0217). Only the stale
  ecosyste.ms record exists (0 downloads, null period, F0058/F0228). See issue 1.
- The closed rows (apheris-networks, rhino-fcp) have homepages only. The sweep fetched both
  (W0018, W0019). They were not re-fetched.

## Check 4: schema and dedup

- `jsonschema.validate(rows.yaml, docs/schemas/registry.schema.json)` prints `ok`.
- No slug, retired alias, GitHub repo or PyPI package collides with `research/corpus-index.tsv`.
  Checked: exact matches on slug, alias, github and pypi, plus a fuzzy slug scan. The fuzzy scan
  hit only `tensorflow` vs `tensorflow-federated` and `paddle` vs `paddlefl`, which are distinct
  products. `pysyft` (`OpenMined/PySyft`, `syft`) and `syfthub` (`OpenMined/syft-hub-sdk`) are
  correctly held out of rows.yaml as contested moves.
- Org reuse: `google`, `apple`, `nvidia`, `paddlepaddle`, `alibaba-cloud` and `lf-ai-and-data` reuse
  index slugs. `bytedance` is new, yet the index carries `bytedance-seed-volcano-engine`. See issue 13.

## Check 5: counts and §2 metrics

Recomputed from the §6b table and rows.yaml:

| metric | sweep says | recomputed | ok? |
|---|---|---|---|
| accepted, by status | 33 (30 open, 0 open-weights, 1 source-available, 2 closed) | 33 (30/0/1/2) | yes |
| distinct orgs in rows.yaml | **31** (§1 line 9, §2 line 33) | **30** (google 3, lf-ai-and-data 2, 28 singletons) | **no** |
| largest org share | 9.1% (google, 3/33) | 3/33 = 9.1% | yes |
| with the moves | google 3/35 = 8.6% | 8.6% | yes |
| active in 12 months (push ≥ 2025-09-26) | 22 of the 31 with a repo; 9 named below the line | 22; the same 9 | yes |
| usage instrument | 17 | 17 rows with a fetched monthly PyPI figure (18 declare a package; federatedscope has none) | yes |
| active and with an instrument (§1) | "at least 14" | 14 | yes |
| declared PyPI total; Flower share; Flower + FLARE | 111,216; 67.2%; 89.1% | 111,216; 67.2%; 89.1% | yes |
| Flower/FLARE ratio; issue ratio; Flower drop | 3.1x; 4.5x; -38% | 3.06x; 4.53x; -38.1% | yes |
| §8 equations | 78 = 6 + 72; 72 = 33 + 39 | arithmetic holds; §7 has 39 rows | yes, but see issue 3 |

## Check 6: recency and breadth

- **Recency:** all 166 sweep fetches and all 28 web-log entries are timestamped 2026-09-26. W0028
  quotes 2026-09-14 figures from issue #574 and is labeled as such.
- **Candidates surfaced by search that Brief 7 did not name:** the sweep lists them at §2 lines
  49–52, and the list checks out against W0005, W0006, W0007, W0008, W0010, W0024 and W0025.
  Accepted from outside the brief: secretflow, pfl-research, pfllib, vantage6,
  federated-compute-platform, fedjax, fedlab, fedlearner, plato-fl, flame-fl, nebula-dfl, p2pfl,
  primihub, fedtree, featurecloud, metisfl, xfl, galaxy-federated-learning, fl4health. Parked from
  outside the brief: Scaleout Edge/FEDn, HPE Swarm Learning, Photon, OpenFedLLM, FL-bench, blades,
  VFLAIR, HeFlwr, FractalAndroid, RIS-FL, FedCLS, NErlNet, FLSim, hivemind, ReFedEz, Fedstellar,
  FedLess, OpenFed, FedCampus, WebFed, and the two tutorial repos.
- **Breadth probe by the auditor:** FLGo (`WwZzz/easyFL`, 634 stars, Apache-2.0, pushed 2025-06-04,
  PyPI `flgo` 331/mo, F0245/F0248) appears nowhere in the sweep. It would likely sit past the first
  20 topic-page results, the declared cutoff. EasyFL (`EasyFL-AI/EasyFL`, 26 stars, F0244) and
  iQua/flsim (206 stars, last push 2022, F0247) are minor. See issue 14.
- Claims that read like recall are listed as issues 4–8 and 10.

## Issues (numbered, with location)

1. **rows.yaml line 60, and sweep.md §6a line 209 and §6b line 355 (`federatedscope`):**
   `pypi: federatedscope` is declared, but the package does not exist on pypi.org (404: F0205,
   F0216, F0217). The sweep never fetched pypi.org JSON for it. Only the stale ecosyste.ms record
   was read (F0058). It also cites no install doc for the package trap. Fix: drop `pypi` from the
   row, and note in §6b "PyPI package no longer on pypi.org (F0205)". The §2 usage count is
   unaffected, because it already excludes this row.
2. **sweep.md §1 line 9 ("33 new candidates from 31 organizations") and §2 line 33
   ("independent organizations: 31"):** rows.yaml has **30** distinct org slugs. Fix both to 30.
3. **sweep.md §8 lines 558–573:** raw_signals is defined as "the distinct names surfaced across the
   brief and every discovery source". Yet three names in Brief 7 (Prime Intellect, Gensyn,
   Bittensor, all mentioned again in §3 line 65) are neither accepted, parked nor listed as
   duplicates. Either count them (they would be parked as boundary → out, which makes parked 42,
   unique 75 and raw 81), or say in §8 that brief-named exclusions are not counted. Also: W0015
   names FLaaS, FS-REAL and FLINT, which are not in the signal count either (see issue 5).
4. **sweep.md §8 line 564 ("PyGrid = part of PySyft (W0014)") and line 565 ("FlowerLLM = Photon
   ... (W0010)"):** neither name appears in the cited excerpt. W0014 names NVIDIA FLARE, PySyft,
   TFF, FATE, FedLess, FedScale, OpenFed and ReFedEz. W0010 covers Photon only. These read like
   recall. Fix: cite a fetch that names them, or drop the two duplicates and adjust raw_signals.
5. **sweep.md §7 lines 552–553 (Felicitas, FLaME cited to W0015) and line 554 (WebFed "arXiv
   2110.11646"):** the W0015 excerpt names FLaaS 2206.10963, FS-REAL, FLINT, WebFed and FedCampus.
   It does not name Felicitas or FLaME, and it gives no arXiv id for WebFed. Fix: re-source or
   drop them. Separately, FLaaS, FS-REAL and FLINT *are* in the excerpt but are absent from §7.
6. **sweep.md §4 line 105 ("Photon pre-trains up to 7B federated (W0010)"):** the W0010 excerpt
   has no model size. Re-source (for example, fetch arXiv 2411.02908) or drop "up to 7B".
7. **sweep.md §4 lines 106–107 (NVIDIA FLARE "ships Docker, Kubernetes and Slurm launchers" and the
   quote "hardening large-model training ... for production deployments", W0026):** the W0026
   excerpt supports only "a new HPC job launcher" and Slurm support. Docker, Kubernetes and the
   quoted phrase are not in any logged excerpt. Fetch the 2.9.0 release notes (for example the
   nvflare PyPI description or readthedocs release notes) or trim the claim. This is the top-rung
   anchor, so it matters.
8. **sweep.md §3 line 81 (pysyft quote "Perform data science on data that remains in someone else's
   server" cited to W0005):** the quote comes from the ecosyste.ms description in F0002, not
   W0005. The W0005 excerpt is a star list. Fix the id.
9. **sweep.md §6b lines 370, 374 (fedtree, xfl) and 371, 375 (featurecloud,
   galaxy-federated-learning), last release "not fetched":** it is honest, but fillable. FedTree
   v1.0.5 (2023-01-26, F0242) and XFL v1.4.1 (2024-02-27, F0243) exist. Fetch the other two as
   well.
10. **sweep.md §1 line 14 ("#533's 'uniformly open' objection") and §3 line 66 ("#428's
    general-infrastructure exclusion, per the brief"):** neither issue was fetched (W0028 covers
    #574 only), and Brief 7 mentions neither #428 nor #533. That makes both claims unsourced. Cite a
    fetch of those issues or remove the attribution.
11. **sweep.md §6b license cells at lines 353, 360, 361, 364, 366, 369, 370, 371, 374, 375
    (federated-compute-platform, pfl-research, pfllib, fedlearner, flame-fl, primihub, fedtree,
    featurecloud, xfl, galaxy-federated-learning), "LICENSE not read":** these break the preamble's
    hard rule "Read the license text, not the label". The auditor read five of them (pfl-research
    F0239, fedlearner F0237, flame-fl F0238, fedtree F0235, xfl F0236), and all five are Apache-2.0
    text, so no value is wrong. Five remain label-only: federated-compute-platform, pfllib,
    primihub, featurecloud and galaxy-federated-learning. Fetch their LICENSE files.
12. **sweep.md §6b line 352 (tensorflow-federated, "ecosyste.ms has no tensorflow/federated
    (F0012)"):** F0012 is a 404, which the sweep uses as a measured absence. For a repository lookup
    that is defensible, since the canonical identity comes from the PyPI project_urls (F0085), but
    it is the only non-200 id in §6b. Phrase it as "old name does not resolve", or rely on F0085
    alone.
13. **rows.yaml line 108 onward (`fedlearner`, `org: bytedance`):** the index already carries the
    ByteDance org as `bytedance-seed-volcano-engine` (`sources/organizations/bytedance-seed-volcano-engine.yaml`).
    The preamble says to reuse the index slug when the org is already on the map. Either reuse it or
    add the choice to §9 Q7. This is a question, not a schema error.
14. **Breadth (sweep.md §2 lines 44–52):** FLGo (`WwZzz/easyFL`, 634 stars, PyPI `flgo` 331/mo,
    Apache-2.0, pushed 2025-06-04; F0245, F0248) is missing from both §6 and §7. It is within reach of
    a second topic page. Add it as a candidate (it would likely be accepted as a research-grade
    framework) or record it as past the cutoff.
15. **Minor provenance mislabels:**
    - §6b line 373 (fedscale) calls the license "apache-2.0 (PyPI F0063 ...)", but F0063 is
      packages.ecosyste.ms, and the PyPI JSON license field is empty (F0215).
    - §5 line 126 and §9 Q8 (vantage6) say "ecosyste.ms say MIT (F0067)". That is true of the
      packages.ecosyste.ms record, but repos.ecosyste.ms reports apache-2.0 (F0024, F0189). Say
      "PyPI metadata (on pypi.org and packages.ecosyste.ms) says MIT".
    - The §6b header (lines 339–342) says a release date is "the upload time of the current version
      in PyPI JSON". For fedlab, paddlefl, plato-fl, p2pfl, fedscale and fedjax, the sweep took it
      from packages.ecosyste.ms instead. The values agree with live PyPI, except plato-learn:
      PyPI's `info.version` is 1.41 (uploaded 2025-10-20), while 1.4.3 (the sweep's figure,
      2025-10-25) is the latest upload (F0213). The sweep's date is defensible, but say which rule
      was used.

## Summary

Nothing in the 16-row live sample failed. Every license, owner, archive flag, push date and download
figure matched. The data is sound. The failures are one dead artifact (`pypi: federatedscope`), one
metric miscount (30 organizations, not 31), and provenance gaps: ten license cells rest on a label,
and claims in §1, §3, §4, §7 and §8 are not supported by their cited excerpts (issues 4–8, 10).
Fix issues 1–11 and 14 before pushing. Issues 12, 13 and 15 are clarifications.

## Re-check (2026-09-26, after the coordinator's fixes in commit c917396)

This section re-checks only the items the coordinator fixed. The auditor compared the diff
`e6b4992..c917396` on `sweep.md` and `rows.yaml` against the logs, and re-read the new fetch bodies
F0249–F0272 and W0029–W0030. New live fetches by the auditor: F0273–F0277 (label `audit recheck:`).
Nothing in `sweep.md` or `rows.yaml` was edited.

### Per original issue

| # | result | evidence |
|---|---|---|
| 1 | **PASS** | `pypi: federatedscope` is gone from rows.yaml and the §6a block. §6b line for federatedscope notes the 404 (F0205, F0216). Still 404 live (F0276). |
| 2 | **PASS** | §1 and §2 now say 33 organizations. rows.yaml has 36 rows and 33 distinct orgs (google 3, lf-ai-and-data 2, 31 singletons). |
| 3 | **PASS** | §8 now defines raw signals and says the brief's own out-of-scope examples (Prime Intellect, Gensyn, Bittensor, compute marketplaces) are not counted. FLaaS, FS-REAL and FLINT are now §7 rows 38–40, and all three appear in the W0015 excerpt. |
| 4 | **PASS** | PyGrid and FlowerLLM are removed. The arithmetic checks out from the original counts: raw 78 − 2 duplicates + 4 net new unique names = 80. Unique 72 − 2 (Felicitas, FLaME) + 3 (FLaaS, FS-REAL, FLINT) + 3 (FLGo, EasyFL, iQua FLSim) = 76. 80 = 4 + 76 and 76 = 36 + 40. §7 has 40 rows and §6b has 36. |
| 5 | **PASS** | Felicitas and FLaME are removed. WebFed no longer carries an arXiv id. The FLaaS arXiv id 2206.10963 is in the W0015 excerpt. |
| 6 | **PASS** | The quote "can train model sizes up to 7B in a federated fashion" appears verbatim in F0264 (export.arxiv.org abstract 2411.02908, HTTP 200). |
| 7 | **PASS** | The W0029 excerpt (WebFetch of the NVFlare 2.9.0 release page) contains both quoted phrases: "Slurm job launcher: a new HPC execution target alongside process, Docker, and Kubernetes" and "validated up to a 72-billion-parameter model". The unsupported "hardening ..." quote is gone. |
| 8 | **PASS** | The pysyft quote now cites F0002, whose ecosyste.ms `description` is that exact string. |
| 9 | **PASS** | fedtree has v1.0.5, 2023-01-26 (F0242) and xfl has v1.4.1, 2024-02-27 (F0243). featurecloud (F0257) and galaxy-federated-learning (F0258) have "no GitHub releases", and both bodies are `[]` with HTTP 200. |
| 10 | **PASS** | #533 and #428 are gone. The §1 claim now cites W0030, a github-mcp read of the #574 comment, and the excerpt contains the quoted "no openness variation" line. §3 now quotes Brief 7's "Out:" sentence verbatim. |
| 11 | **PASS** | Every open row's §6b license cell now cites a LICENSE-text fetch. The auditor spot-read each new body: F0249–F0256 and F0266–F0272 all begin with Apache License 2.0 text, and F0253 carries a "Copyright 2020 The GFL Authors" line above it. F0266 (FederatedScope, 33 KB) is Apache-2.0 followed by third-party notices, mostly MIT (pytorch_geometric, tf_gpu_manager, dlg) plus Apache-2.0 notices for code adapted from Ray. The project license is Apache-2.0, which is correct, but the scorer may want to know about the bundled MIT code. substra still cites the license text embedded in the PyPI metadata (F0052), which is a text read and acceptable. |
| 12 | **PASS** | The TFF note now reads "Canonical repo from PyPI project_urls F0085; the old name tensorflow/federated does not resolve on ecosyste.ms (F0012, 404)". |
| 13 | **PASS** | §9 Q7 now carries the fedlearner/`bytedance` vs `bytedance-seed-volcano-engine` question with a recommendation (F0027). |
| 14 | **PASS** | FLGo, EasyFL and iQua FLSim are accepted, with ids for every cell. Live: `WwZzz/easyFL`, `EasyFL-AI/EasyFL` and `iQua/flsim` all resolve, and none is archived or a fork (F0244, F0245, F0247). PyPI `flgo` 0.4.4 was uploaded 2025-06-04, and its project_urls Bug Tracker points to WwZzz/easyFL (F0273). PyPI `easyfl` 0.1.2 was uploaded 2022-04-10, with home_page EasyFL-AI/EasyFL (F0274), 30/mo (F0275). The package trap is cleared for both. |
| 15 | **PARTIAL** | fedscale's license cell is fixed (LICENSE text F0267), and so is the vantage6 wording ("PyPI license field 'MIT' F0088 (ecosyste.ms package record also MIT F0067)"). The third bullet is **not** addressed: the §6b header (lines 362–363) still says release dates come from PyPI JSON, but fedlab, paddlefl, plato-fl, p2pfl, fedscale and fedjax still cite packages.ecosyste.ms ids for the release. The plato-learn 1.41 vs 1.4.3 rule is still unstated. The values are correct, so this is a wording fix only. |

### Schema, dedup and §2 metrics after the fixes

- Schema: `jsonschema.validate(...)` prints `ok` on the 36-row rows.yaml.
- Dedup: there are no slug, alias, GitHub or PyPI collisions with `research/corpus-index.tsv` (exact
  match on all four keys) and no duplicate slugs within rows.yaml. The new slugs `flgo`, `easyfl`
  and `flsim-iqua` have no fuzzy near-match in the index. The new orgs `wwzzz`, `easyfl-ai` and
  `iqua` are not in the index, so they are new slugs, as expected.
- §6b and rows.yaml list the same 36 slugs in the same order.
- The §2 metrics recompute from §6b and rows.yaml:
  - Status: 36 accepted (33 open / 0 open-weights / 1 source-available / 2 closed).
  - Organizations: 33. Google holds 3/36 = 8.3%, and 3/38 = 7.9% with the moves.
  - Activity: 22 of the 34 repositories were pushed on or after 2025-09-26. The 12 below the line
    match the sweep's list.
  - Usage instrument: 19 rows (19 declare a package).
  - Downloads: the declared PyPI total is 111,577. Flower is 67.0%, and Flower plus NVIDIA FLARE is
    88.9% (the §1 figure is also updated to 88.9%).
  - Active and with a PyPI figure: 14 (the §1 "at least 14" still holds).
- Ids: every id in the document exists in the logs. The only non-200 `F` ids are the three
  intentional 404s (F0012, F0205, F0216). The §6b and §6c id sets match exactly.

### New issues introduced by the fixes

16. **sweep.md §5 lines 124–126:** "`Apache-2.0` (all read as LICENSE text, cited per row in §6b)"
    lists the move `syfthub`. The sweep only has the ecosyste.ms label for syfthub (F0003), and the
    move rows are not in §6b. The claim is true in substance, because the auditor fetched the
    `OpenMined/syft-hub-sdk` LICENSE and it is Apache-2.0 text (F0277), but the sweep should cite
    F0277 (and F0127 for pysyft) or drop "all" for the moves. Minor.
17. **sweep.md §6b `flsim-iqua` row (and §2 line 101 "All three are triaged and accepted"):**
    this is a judgment call, not an error. iQua FLSim has 206 stars, a last push on 2022-04-09, no
    releases (F0261), no package, and describes itself as "a simulation framework". That profile is
    close to rows the sweep parked as research code (RIS-FL, FedCLS, OpenFedLLM). Accepting it is
    defensible, since it is a framework rather than a single paper's code, but the maintainer
    should see the asymmetry. Suggest noting it in §9 or parking it for consistency. It does not
    affect any gate.

### Re-check verdict

Issues 1–14 are fixed. Issue 15 is partially fixed (a wording-only remainder). There are two new
minor items (16, 17). All six original checks now pass on the fixed items:

| # | check | re-check result |
|---|---|---|
| 1 | Live re-fetch | PASS (unchanged; the new rows were also verified live) |
| 2 | Unsourced facts | **PASS** (with issue 16's minor wording note) |
| 3 | Artifacts resolve | **PASS** |
| 4 | Schema and dedup | PASS |
| 5 | Counts and §2 | **PASS** |
| 6 | Recency and breadth | PASS |

None of the remaining items (15c, 16, 17) blocks the push. They are wording or curator-judgment
notes.

## Author response to the re-check (items 15–17)

- 15: the §6b header now states the source order for release dates (PyPI JSON, then the ecosyste.ms
  package record, then the GitHub release), and it explains the plato-learn 1.4.3 choice.
- 16: §5 now cites F0277 for syfthub and F0127 for pysyft.
- 17: kept accepted, and added as §9 Q11 with park as the alternative. The FederatedScope notices
  from F0266 are recorded as §9 Q12.
