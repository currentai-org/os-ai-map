# Audit: classic_ml_cv sweep (2026-09-26)

Independent audit of `research/classic_ml_cv/` (sweep.md, rows.yaml, fetch-log.tsv, web-log.tsv,
raw/) against the six checks in `research/RUNBOOK.md` ("Finishing: independent audit, then push").
Live re-fetches ran on 2026-09-26 between 20:18Z and 20:21Z via `research/rfetch.sh
classic_ml_cv_audit ...`. That scratch directory has been deleted, so the issues below cite URLs.

| # | check | verdict |
|---|---|---|
| 1 | Re-fetch 15 claims live | **FAIL** (14 of 15 rows match; depth-pro has the wrong owner and is wrongly reported as undatable) |
| 2 | Every evidence cell cites an existing F/W id with HTTP 200 or excerpt | **PASS** (minor notes) |
| 3 | Every artifact in rows.yaml resolves live | **FAIL** (depth-pro `github` is a pre-transfer name; the other 155 resolve) |
| 4 | Schema validation and dedup against corpus-index.tsv | **PASS** |
| 5 | Section 8 equations and section 2 metrics reconcile | **PASS** (internally consistent; one metric changes once check 1 is fixed; one prose slip) |
| 6 | Recency, breadth and recall | **PASS with flags** |

## Check 1: live re-fetch of 15 claims (FAIL)

Rows sampled every 5th across section 6b: statsmodels (5), cuml (10), ngboost (15), nltk (20),
textblob (25), detectron2 (30), scikit-image (35), lightly-train (40), sktime (45),
pmdarima (50), tpot (55), depth-pro (60), birefnet (65), cotracker (70), tabfm (75). For each
row the audit checked the license text (raw LICENSE), canonical owner, archived flag, last push
(repos.ecosyste.ms), the adoption figure (packages.ecosyste.ms last-month, or the HF API) and the
latest release (PyPI JSON).

Matches, all exact or within a day: statsmodels (BSD-3, 2026-09-24, 31,358,911), cuml
(Apache-2.0, NVIDIA/cuml, 2026-09-24, 418,656, 26.8.0 on 2026-08-06), ngboost (Apache-2.0,
2026-09-02, 180,490, release 2026-06-26), nltk (Apache-2.0, 2026-09-23, 42,263,867, 3.10.3 on
2026-08-12), textblob (MIT, sloria/TextBlob, 2026-09-22, 3,735,355, 0.20.1 on 2026-07-18),
detectron2 (Apache-2.0, 2026-08-19, 34,729 stars), scikit-image (BSD-3 DEP-5 file, GitHub label
`other`, 2026-09-19, 23,581,656, 0.26.0 on 2025-12-20), lightly-train (AGPL-3.0, 2026-09-14,
5,377, 0.17.0 on 2026-07-28), sktime (BSD-3, 2026-09-20, 1,126,565, 1.2.0 on 2026-09-22 per PyPI),
pmdarima (MIT, 2025-11-17, 1,607,451), tpot (LGPL-3.0, pushed 2025-09-11 so correctly inactive,
14,887, 1.1.0 on 2025-07-03), birefnet (MIT, 2026-09-02, HF author ZhengPeng7 1,279,955 / 30d over
16 models), cotracker (CC-BY-NC-4.0, 2026-03-03, facebook/cotracker3 17,576), tabfm (code
Apache-2.0, weights "TabFM Non-Commercial License v1.0", 2026-09-18, pytorch 32,632 + jax 1,264 =
33,896 / 30d). No row in the sample is archived.

### Issue 1.1: depth-pro has the wrong owner and a push date the sweep says it could not get
- **Row:** 6b `depth-pro`, and rows.yaml `depth-pro` (`github: apple/ml-depth-pro`).
- **Sweep says:** owner `github apple`; last push "fetch did not complete"; "Activity date not
  measured"; section 2 says "depth-pro could not be dated (F0489, W0020)".
- **Found:** ungh resolves `apple/ml-depth-pro` to **`apple-aiml-research/ml-depth-pro`**
  (repo id 847933360, created 2024-08-26, pushedAt 2026-09-11T15:56:05Z, 5,731 stars). The
  sweep's own two ungh calls got 403 (F0524, F0526); the audit's retry returned 200.
  repos.ecosyste.ms knows the repo under its new name: `archived: false`, `fork: false`,
  `pushed_at` 2026-09-11, license label `other`, 5,728 stars. The LICENSE text is byte-identical
  to the sweep's F0495 (sha256 21a6551d...), so the license claim holds.
- **Consequence:** the ecosyste.ms 404 (F0489) is a repo transfer, the same pattern the sweep
  caught for lightgbm, cuml, torchgeo and limix. depth-pro is active, so section 2's "74 of 78"
  should read **75 of 78**, and the "could not be dated" sentence should go. The org slug `apple`
  can stay (apple-aiml-research is Apple's research org), but the github value should be
  `apple-aiml-research/ml-depth-pro`, with the 6b org handle and notes updated to match.
- **URLs:** https://ungh.cc/repos/apple/ml-depth-pro ;
  https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/apple-aiml-research%2Fml-depth-pro ;
  https://raw.githubusercontent.com/apple-aiml-research/ml-depth-pro/HEAD/LICENSE

### Issue 1.2 (minor, not a fail): release dates taken from the last wheel upload
- **statsmodels:** the sweep says 0.15.0 was released 2026-08-30 (F0021). PyPI's first file for
  0.15.0 was uploaded 2026-08-27T10:34:19, and its last file 2026-08-30T16:06:08. ecosyste.ms also
  gives 2026-08-27. https://pypi.org/pypi/statsmodels/json
- **mlpack:** the sweep says 4.8.0 was released 2026-06-19 (F0045). The first PyPI upload was
  2026-06-17. https://pypi.org/pypi/mlpack/json
- The drift is 2 to 3 days, which is a method difference rather than a wrong fact. Prefer the
  first upload time for "release date".

## Check 2: evidence cells cite existing ids (PASS)

- All 81 rows of 6b were parsed. Every license, archived/fork, last-push, last-release and
  adoption cell carries at least one F or W id. Every cited id exists in fetch-log.tsv or
  web-log.tsv, and every one of the 404 cited ids appears in section 6c with the logged HTTP code,
  timestamp and URL, with no mismatches. All 20 W rows have excerpts.
- The non-200 ids cited in 6b are all labeled as failures or renames in the cell: F0014
  (microsoft/LightGBM 404), F0035 (rapidsai/cuml 404), F0141 (microsoft/torchgeo 404), F0180
  (limix-ldm 404), F0489/F0524/F0526 (depth-pro 404/403, see issue 1.1), and F0519 (RMBG README
  401 gate).
- Automated relevance check: every cited F URL names the row's repo, package or HF id, or is the
  HF task list or the homepage the row says it came from.
- The sha256 of every non-truncated raw body matches its log row. F0244 (ungh microsoft/torchgeo)
  has http `000000` and no raw body, but it is not cited anywhere.

Minor notes. These are factual assertions in the member-checkpoints and notes columns with no
id behind them. The audit confirmed the four package claims live, so they are true but unsourced
in the sweep:
- cuml: "cuml-cu13 wheels" (live: https://pypi.org/pypi/cuml-cu13/json, 200).
- darts: "u8darts is a second PyPI name" (live: https://pypi.org/pypi/u8darts/json, 200).
- opencv: "opencv-contrib-python, opencv-python-headless wheels" (live: both PyPI JSON 200).
- cotracker: "CoTracker, CoTracker3". Only cotracker3 is fetched (F0413).

## Check 3: every artifact resolves live (PASS for 155 of 156; FAIL overall)

Every artifact in rows.yaml was fetched: 75 github (repos.ecosyste.ms), 20 huggingface_model
(HF API), 58 pypi (PyPI JSON) and 3 homepages.
- All 58 PyPI names return 200 with the declared name (e.g. `umap-learn`, `h2o`, `cuml-cu12`,
  `albumentationsx`, `synthefy-nori`, `tabstar`, `depth-anything-3`).
- All 20 HF ids return 200, and each downloads figure matches 6b where 6b quotes that single
  checkpoint (for example RMBG-2.0 547,561; DepthPro-hf 26,401; segformer-b0 368,469;
  sap-rpt-1-oss 94,516; LimiX-2 8,391; TabSTAR 91,172; EXAONE-Tabular 67,150).
- 73 of 75 github repos return 200 from ecosyste.ms with a matching `full_name`,
  `archived: false` and `fork: false`. The two 404s:
  - `LGAI-Research/EXAONE-Tabular`: ecosyste.ms 404, ungh 200 (pushedAt 2026-08-27, matching 6b).
    It resolves. The archive flag is not available from ungh, and 6b already says so.
  - **`apple/ml-depth-pro`: ecosyste.ms 404.** It resolves only as a redirect to
    `apple-aiml-research/ml-depth-pro` (issue 1.1). The declared value is stale and should be
    replaced.
- All 3 homepages (cloud.google.com/vision, aws.amazon.com/rekognition/, the DataRobot URL)
  return 200.
- Minor, pre-existing and already documented: packages.ecosyste.ms still reports
  `repository_url` rapidsai/cuml for cuml-cu12, while the repo is NVIDIA/cuml.

## Check 4: schema and dedup (PASS)

- `jsonschema.validate(rows.yaml, docs/schemas/registry.schema.json)` prints `ok`.
- There are 81 slugs, none duplicated. The audit compared every slug, github, huggingface_model
  and pypi value, case-insensitively, against every slug, retired_alias, github, huggingface and
  pypi token in corpus-index.tsv (split on `;` and `,`). There are no collisions. A bare
  repo-name match found nothing either.
- `segment-anything` and `sam2` (index tail, scientific_ai_models) are handled correctly: they are
  proposed as moves in section 3 and are not duplicated in rows.yaml.
- The rows.yaml embedded in 6a is byte-identical to `rows.yaml`.

## Check 5: counts and metrics (PASS)

Recomputed from 6b and rows.yaml:
- Rows: 81. Status: open 64, open-weights 13, source-available 1, closed 3. This matches.
- Type: software 59, model 22. This matches, and the 22 are the 14 vision model lines plus the 8
  tabular FMs.
- Sub-areas: 18+19+14+8+7+7+5+3 = 81. The split totals (45 + 33 + 3 closed) match section 1 and
  Q1.
- Orgs: 68 distinct `org` values. The largest is meta with 5 (detectron2, prophet, dino, sapiens,
  cotracker), so 5/81 = 6.2%. Next is nvidia with 3. This matches.
- Active in 12 months: 74 of 78 non-closed rows by the sweep's own data. The inactive rows are
  mmdetection, segformer, tpot and depth-pro (undated). This matches the text, **but** it becomes
  75 of 78 once issue 1.1 is fixed.
- Usage instrument: 73 rows. The 8 without one are ml-net, corenlp, detectron2, paddledetection,
  deim and the 3 closed rows. This matches.
- Section 8: 14 duplicate signals are itemized (6 + 8), so 14 + 123 = 137. Section 7 has 42
  parked rows, so 81 + 42 = 123. Both equations hold.

Issues:
- **5.1 (prose):** section 1 says "22 model rows: timm and backbones by ruling, plus the tabular
  foundation models". timm is `type: software` in rows.yaml, and the 22 model rows do not include
  it. Reword to "vision backbones and model lines by ruling".
- **5.2 (note):** "68 independent organizations" counts `google` (mediapipe), `google-research`
  (tabfm) and `google-cloud` (google-cloud-vision) as three orgs, and `amazon-web-services` holds
  gluonts and amazon-rekognition. These slugs follow the index convention, and the largest-org
  share does not change. "Independent" slightly overstates it.

## Check 6: recency, breadth, recall (PASS with flags)

- **Recency:** all 526 fetch-log rows are timestamped 2026-09-26 (20:00:54Z to 20:13:07Z), and all
  20 web-log rows are 2026-09-26. This passes.
- **Candidates the brief did not name.** Brief 3's leads cover 25 accepted rows (scikit-learn,
  xgboost, lightgbm, catboost, statsmodels, spacy, nltk, gensim, stanza, timm, torchvision,
  ultralytics, detectron2, mmdetection, opencv, kornia, albumentations, supervision, fastai,
  prophet, sktime, darts, pyod, imbalanced-learn, dino). The other **56 accepted rows** are not
  named in the brief:
  - Surfaced by WebSearch: ngboost, perpetual (W0014); ml-net, dask-ml (W0008); rf-detr, d-fine
    (W0002); tabpfn, tabicl, limix (W0003); tabfm (W0011); radio (W0012); statsforecast (W0006);
    autogluon, flaml (W0010).
  - Surfaced from the HF top-40 lists: depth-anything, depth-pro (F0005); birefnet, rmbg,
    segformer, sapiens, eomt (F0003); rt-detr (F0002); sap-rpt-1, nori, tabstar, exaone-tabular
    (F0007).
  - Added by the sweeper and then verified by fetch, with no discovery search behind the name:
    lightly-train, deim, cotracker, cuml, river, skrub, h2o-3, mlpack, corenlp, textblob, dlib,
    insightface, torchgeo, monai, lightly, mediapipe, paddledetection, pmdarima, gluonts,
    neuralforecast, tpot, auto-sklearn, pycaret, umap, hdbscan, flair, scikit-image.
  - Closed comparators: google-cloud-vision, amazon-rekognition, datarobot.
- **Flag 6.1:** section 2's list of unnamed candidates omits 8 of the 56: umap, hdbscan, flair,
  scikit-image, statsforecast, google-cloud-vision, amazon-rekognition and datarobot.
- **Flag 6.2:** about 27 accepted names came from the sweeper's own knowledge ("sweep additions
  checked against ecosyste.ms/PyPI"), not from a search that surfaced them. Every fact about them
  is fetched, so the evidence is sound, but the breadth claim rests mostly on the HF lists and 14
  WebSearch hits.
- **Flag 6.3:** these claims read like recall and have no fetch behind them:
  - hdbscan note: "scikit-learn also ships an HDBSCAN estimator".
  - rt-detr note: "Also shipped inside transformers".
  - h2o-3 note: "H2O-3 is how H2O.ai names the open product".
  - mlpack adoption cell: "C++ library; PyPI is a binding".
  - torchvision note: "Installed alongside torch", which is judgment, not a sourced figure.
  - The four member-column package claims under check 2. These were verified true by the audit
    but are unsourced in the sweep.
  - W0020 (WebFetch of the GitHub page) says "7 Commits" for depth-pro. The audit could not
    check this and it is not load-bearing. It is superseded by the real push date in issue 1.1.

## Fix list for the sweep author
1. depth-pro:
   - Change rows.yaml `github` to `apple-aiml-research/ml-depth-pro`.
   - Update the 6b cells: org handle; archived (no / no); last push 2026-09-11.
   - Re-fetch through the new name so the evidence has fetch ids.
   - In section 2, change active to 75 of 78 and remove "could not be dated".
2. Section 1: reword "timm and backbones" (issue 5.1).
3. Section 2: complete the list of unnamed candidates (flag 6.1).
4. Optional:
   - Cite fetches for the member-column package claims and the recall notes (flag 6.3), or cut
     them.
   - Use the first-upload date for statsmodels and mlpack releases.

## Re-check (2026-09-26, after fixes)

Only the flagged items were re-checked. There was one live re-fetch at about 20:25Z. The scratch
directory has been deleted, so the entry below cites its URL.

| item | verdict | finding |
|---|---|---|
| 1. depth-pro identity and activity | **PASS** | rows.yaml and the 6a copy now say `github: apple-aiml-research/ml-depth-pro`. A live fetch of https://repos.ecosyste.ms/api/v1/hosts/GitHub/repositories/apple-aiml-research%2Fml-depth-pro returns `full_name` apple-aiml-research/ml-depth-pro, `archived` false, `fork` false, `pushed_at` 2026-09-11, and 5,728 stars. This matches the 6b cells, which now cite F0527 (HTTP 200, logged 20:23:57Z, raw body agrees). The org handle cell records the move from `apple/` (F0489). |
| 2. Release dates | **PASS** | The statsmodels row gives 0.15.0 on 2026-08-27, citing F0022 (`latest_release_published_at` 2026-08-27T10:34:19), and notes the last file upload of 2026-08-30 (F0021). The mlpack row gives 4.8.0 on 2026-06-17, citing F0046 (2026-06-17T22:29:10), and notes the 2026-06-19 last upload (F0045). |
| 3. Section 1 wording on timm | **PASS** | It now reads "59 software rows (timm among them, by ruling) and 22 model rows: vision backbones and perception model lines, plus the tabular foundation models". This is consistent with rows.yaml. |
| 4. Org-count caveat | **PASS** | Section 2 now says there are 68 org slugs, and that google, google-research and google-cloud count as three, following the index's slugs. |
| 5. Unnamed-candidate list | **PASS** | It lists 56 rows in four groups: search 14, HF lists 12, sweeper-added 27, closed 3. 14+12+27+3 = 56. A set comparison against rows.yaml minus the 25 brief leads finds nothing missing and nothing extra. |
| 6. Recall-sounding notes | **PASS** (one note) | The hdbscan, rt-detr, h2o-3 and mlpack notes are removed or reworded. The h2o-3 note now cites the repo name (F0047). The sibling wheels cite F0529 (cuml-cu13), F0530 (u8darts), F0531 (opencv-contrib-python) and F0532 (opencv-python-headless). All four are HTTP 200 and each body names the package. The cotracker members cell is limited to CoTracker3 (F0413). "7 Commits" no longer appears in sweep.md. Remaining note: the torchvision note "Installed alongside torch; downloads partly reflect that pairing" is still present. It is an interpretive caveat, not a sourced figure, so it does not block. |
| Section 2 active count | **PASS** | It reads **75 of 78**. The inactive rows listed are mmdetection, segformer and tpot, and the "could not be dated" sentence is gone. |
| Schema | **PASS** | `jsonschema.validate(rows.yaml, registry.schema.json)` prints `ok`. The 6a copy is byte-identical to rows.yaml. Every F and W id cited anywhere in sweep.md exists in the logs. |

Housekeeping: F0528 is a new malformed fetch (http `000000`, URL
`https://raw.githubusercontent.com/cuml?`, label `x`). Nothing cites it. It is disclosed in the
sweep's header and listed in 6c.

**Final overall status: PASS.** All six checks now pass. The earlier check 1 and check 3
failures (depth-pro) are resolved.
