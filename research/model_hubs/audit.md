# Audit: model_hubs sweep, 2026-09-26

Independent auditor. Live re-fetches are in `audit-fetch-log.tsv` with bodies in `audit-raw/`. That
log restarts at F0001, so this file writes its ids as **AFnnnn** so they can't be confused with the
sweep's Fnnnn. All AF rows were fetched 2026-09-26T20:16–20:18Z. WebFetch/WebSearch checks made
by the auditor are marked "WF (auditor)".

## Check 1: live re-fetch of 15+ claims: PASS

Sampled rows 2, 3, 4, 6, 8, 9, 10, 11, 12, 13, 14, 16, 17 and 18 of §6b, plus parked rows 1, 4, 11,
13, 17 and 23 of §7.

| # | row | claim (sweep) | live value | result |
|---|---|---|---|---|
| 1 | modelscope | 259,500 models; Qwen/Qwen-Image-2.1 28,631 dl (F0115) | 259,500; 28,632 (AF0011) | ok |
| 2 | modelscope | PyPI client 3,465,915/mo (F0070) | 3,465,915 (AF0009) | ok |
| 3 | ollama-library | llama3.1 119.9M, deepseek-r1 93.2M, nomic-embed-text 87.2M (W0018) | same (WF auditor, ollama.com/library) | ok |
| 4 | civitai | Apache-2.0; push 2026-09-21; 7,252 stars; Realistic Vision 2,330,029 (F0052/F0009/F0127) | Apache-2.0 text (AF0028); apache-2.0, push 2026-09-21, 7,252, not archived (AF0007); 2,330,029 (AF0019) | ok |
| 5 | nvidia-ngc-catalog | 903 models, 1,233 containers, 301 Helm (W0023) | Model (903), Container (1233), Helm Chart (301) (WF auditor) | ok |
| 6 | azure-ai-foundry-models | "over 10,000 models", doc 2026-07-28 (W0036) | verbatim, ms.date 2026-07-28 (WF auditor) | ok. Homepage now redirects to `/azure/foundry-classic/...` (AF0029) |
| 7 | sagemaker-jumpstart | "On 3/13/2026, we delisted a few models"; SageMakerPublicHub, Private/Curated Hubs (W0068) | verbatim (WF auditor) | ok |
| 8 | csghub | owner OpenCSGs; Apache-2.0; push 2026-09-19; v2.5.0-ce 2026-09-16; 4,111 stars | same, not archived (AF0003, AF0026) | ok |
| 9 | matrixhub | CNCF Sandbox submission by Shanghai DaoCloud, 2026-07-30, in voting (W0057) | same, labels gitvote/open, "In voting" (WF auditor); push 2026-09-22, 352 stars (AF0008) | ok |
| 10 | kubeflow-hub | Apache-2.0; push 2026-09-22; v0.3.17 2026-09-21; 184 stars; renamed from model-registry | same; previous_names [kubeflow/model-registry] (AF0001, AF0023) | ok |
| 11 | qualcomm-ai-hub-models | BSD-3; push 2026-09-19; PyPI 31,663/mo; 235 models / 541 variants; last release v0.62.2 2026-09-11 | bsd-3-clause, push 2026-09-19 (AF0015); 31,663 (AF0002); "541 model variants (235 models)" (WF auditor). PyPI now has **0.63.0 uploaded 2026-09-23** (AF0039) | ok (release column stale, drift only; see fix 9) |
| 12 | pytorch-hub | no LICENSE; license null; push 2024-04-15; 1,435 stars; page 2025-01-16 "beta release" | LICENSE 404 (AF0027); null, 2024-04-15, 1,435, not archived (AF0006); page verbatim (WF auditor) | ok |
| 13 | bioimage-model-zoo | no LICENSE; push 2026-09-13; 12 stars | LICENSE 404 (AF0021); null, 2026-09-13, 12 (AF0012) | ok |
| 14 | kipoi | MIT; push 2025-12-17; 173 stars | mit, 2025-12-17, 173 (AF0024) | ok |
| 15 | openml | BSD-3 text; push 2026-08-06; 751 stars | "BSD 3-Clause License" (AF0017); bsd-3-clause, 2026-08-06, 751 (AF0013) | ok |
| 16 | huggingface-hub-platform (§2) | 3,097,949 models (F0063); huggingface-hub 225.5M/mo (F0069) | numTotalItems 3,097,966 (AF0018); 225,502,059 (AF0014) | ok |
| P1 | Docker Hub `ai/` | 110 repos, gemma4 1M+ (W0038) | "1 to 30 of 110", gemma4 "1M+" (WF auditor) | ok |
| P4 | OpenXLab | PyPI openxlab 4,780,663/mo, repo github.com/xxx/xxxx | same (AF0022) | ok |
| P11 | GitHub Models | retired 2026-07-30 (W0067) | "As of July 30, 2026, GitHub Models is now retired." (WF auditor) | ok |
| P13 | TensorFlow Hub | last push 2025-01-17 (F0018) | 2025-01-17, not archived (AF0005) | ok |
| P17 | PaddleHub | ecosyste.ms: created 2025-06-25, 82 stars (F0040) | same (AF0010) | ok |
| P23 | Harbor | Apache-2.0 (F0062) | apache-2.0, not archived (AF0020) | ok |

No wrong license, no wrong owner, no archived repo reported active, and no figure off by more than 25%.

## Check 2: unsourced facts and log integrity: FAIL

Every cited id exists in the logs. Every cited non-200 F row is used as evidence of absence or of
an access limit (F0001/F0036 OpenCSG 404, F0024–F0035 ungh 403/429, and the LICENSE 404s F0058,
F0060, F0117, F0119, F0122–F0125), and the text says so. F0033 and F0034 (http 000) have no body
file, but neither is cited. The problems:

1. **modelscope row, W0003:** the claim is `Third-party figure "80,000+" (W0003)`. The W0003
   excerpt has no 80,000 figure (it reads "ModelScope (Alibaba) is the dominant Chinese
   alternative ... OpenDataLab CLI ..."). Nothing in the logs supports it.
2. **§3 exclusions and parked row "Eden AI", W0001:** the claims are "Together, Modal and
   Northflank appear as alternatives in W0001" and "Eden AI ... (W0001)". The W0001 excerpt names
   only DagsHub, ModelScope and the result sites relevanceai, eesel, northflank and infrabase.ai.
   Together, Modal and Eden AI are not in it.
3. **§8 self-dedup, W0008:** the claim is "satellite of mapped `aimet`: quic/aimet-model-zoo
   (W0008)". The W0008 excerpt doesn't mention aimet-model-zoo, and no F fetch of that repo exists.
4. **§8 forks (W0002, W0004, W0015):** the claims are "6 matrixhub forks", "2 kitops forks" and
   "2 csghub forks". None of the three excerpts mentions forks or a fork count. All 10 duplicates
   are unsourced.
5. **pytorch-hub and bioimage-model-zoo, "last release: none":** no releases endpoint was fetched
   for pytorch/hub or bioimage-io/bioimage.io. There are no F rows for them, unlike kipoi, which
   honestly says "none fetched".
6. **License cells with no id:** ollama-library ("registry server not published"),
   nvidia-ngc-catalog, vertex-ai-model-garden, azure-ai-foundry-models and sagemaker-jumpstart
   ("not published") carry no id. For huggingface-hub-platform, modelscope and kaggle-models the
   id supports only the client. These are absence claims with no search logged behind them. Mark
   them "not checked" or cite a fetch.
7. **§3 contested table:** "#601 comment 2026-09-24 ruled it the client" carries no id. The brief
   (research-prompt.md, Brief 4) supports the ruling but not the date or the comment.

W-id spot check, 12 checked. W0012, W0016, W0018, W0023, W0036, W0045, W0046, W0056, W0057,
W0063, W0066 and W0068 each support the claim they are cited for. The failures are W0003, W0001
and W0008 above.

## Check 3: artifacts resolve live: PASS

- github, via ecosyste.ms: civitai/civitai, OpenCSGs/csghub, matrixhub-ai/matrixhub,
  kubeflow/hub, qualcomm/ai-hub-models, pytorch/hub, Project-MONAI/model-zoo,
  bioimage-io/bioimage.io, kipoi/models and openml/OpenML all return 200 with archived=false and
  fork=false (AF0001, 0003, 0004, 0006, 0007, 0008, 0012, 0013, 0015, 0024). pytorch/hub is
  dormant, and the sweep says so.
- pypi: `https://pypi.org/pypi/qai-hub-models/json` returns 200, version 0.63.0 (AF0039).
- homepages: all 14 return 200 (AF0029–AF0043). Two notes: the azure homepage 301s to
  `learn.microsoft.com/en-us/azure/foundry-classic/concepts/foundry-models-overview`, and
  catalog.ngc.nvidia.com/models redirects to its search view.
- Q8 is already answered by the sweep's own data. qualcomm/ai-hub-models `previous_names` includes
  `quic/ai-hub-models` (F0015 and AF0015), so the PyPI repository URL is the renamed repo. The
  sweep says "a redirect is likely but not fetched", but F0015 shows it.

## Check 4: schema and dedup: PASS

- `jsonschema.validate(rows.yaml, registry.schema.json)` prints `ok`.
- No slug in rows.yaml matches a `slug` or `retired_aliases` entry in corpus-index.tsv (1,055
  rows). No github or pypi artifact collides, and rows.yaml declares no huggingface artifacts.
  The near matches are all intentional and documented: `huggingface-hub-platform` next to
  `huggingface-hub`, `ollama-library` next to `ollama`, and `pytorch-hub` next to `pytorch`.

## Check 5: counts reconcile: FAIL

- Both equations are arithmetically balanced (44+49=93 and 18+31=49). The parked table has
  **31** rows, which matches. rows.yaml has **18** products, which matches accepted.
- **The itemized self-dedup sums to 36, not 35.** It lists 10 forks (6+2+2), 25 second artifacts
  and 1 satellite. With the 9 already-mapped, duplicates come to 45, not 44, so raw_signals would
  be 94. Either one item is double-listed or the totals are wrong.
- **"18 independent organizations" is wrong.** `kaggle` and `google-cloud` share a parent:
  Kaggle has been part of Google Cloud since its 2017 acquisition (WF auditor, TechCrunch
  2017-03-08, "Kaggle is now part of Google's Cloud AI team"). That makes 17 independent parents,
  with Google holding 2 of 18 rows (11.1%), not 5.6%. By distinct org slug the count is 18 and
  1/18, but the text claims independence.
- Possible double count: `lm-studio` appears among the 9 already-mapped duplicates, and "LM Studio
  catalog / Hub" is also a parked unique candidate. Its satellites (lmstudio-ai/lms, the lmstudio
  PyPI package, the lmstudio-community HF org) sit in self-dedup. State whether the catalog is a
  separate signal.
- These section-2 metrics are correct against §6b: the open/closed split (8/0/2/8, all slugs match
  §6b), active 17/18 (only pytorch-hub is outside the window; vertex rests on a search snippet
  only, W0043), the one declared-artifact instrument, the 5 platform-native counters and the 8
  client proxies. The usage breakdown overlaps rows rather than partitioning them (hf, modelscope
  and ngc appear in two buckets). It still covers all 18.

## Check 6: recency, breadth and recall: FAIL (minor)

- Recency: all 127 fetch-log rows and 71 web-log rows are dated 2026-09-26. PASS.
- Breadth: these candidates are not in the brief's lead list and came from search: MatrixHub
  (W0002), Harbor-as-model-registry (W0004, W0053, W0056), Docker Hub `ai/` (W0009), Jozu Hub
  (W0044), DagsHub/Northflank (W0001), SeaArt/LiblibAI (W0005), GitHub Models' retirement (W0007),
  hf-mirror.com (W0030), Moark (W0054) and Melious/EULLM (W0052). Eden AI and aimet-model-zoo
  don't count, because their excerpts don't show them (check 2). Kubeflow Hub, SageMaker
  JumpStart, Qualcomm, MONAI, BioImage, Kipoi, OpenVINO, Unity Catalog, ORAS and PaddleHub were
  added by the sweeper by name, and the sweep discloses this honestly. PASS.
- Claims that read like recall:
  - §3: "ClearML and ZenML are the same" has no fetch.
  - §3: the "#601 comment 2026-09-24" date (see check 2 item 7).
  - Q5: "client counts differ by 4 orders of magnitude (F0069 vs F0073)". The real ratio is
    225,502,059 / 1,046 ≈ 2.2×10^5, which is 5 orders. The arithmetic is wrong.
  - §6b modelscope "last release v1.38.0, 2026-07-03 (F0103)" is the first GitHub release entry.
    The sweep's own F0070 shows a PyPI release on 2026-09-15, so the column understates activity.
    Qualcomm is similar: PyPI has 0.63.0 from 2026-09-23 (AF0039).
  - §6b modelscope surfaces: "modelscope.ai international (W0020, title only)". The excerpt gives
    only the title "Home - ModelScope", so "international" is inferred.

## Overall: FAIL

Fixes required:
1. Remove the modelscope "80,000+" (W0003) sentence, or re-run the search and log an excerpt that
   contains the figure.
2. Drop Together, Modal and Eden AI from the W0001 attributions, or log searches that show them.
   Re-cite or remove the parked row "Eden AI".
3. Fetch quic/aimet-model-zoo (ecosyste.ms) and cite it, or remove it from §8 self-dedup.
4. Source the 10 fork duplicates (for example, the ecosyste.ms forks endpoint per repo), or remove
   them from the count.
5. Fetch the releases endpoints for pytorch/hub and bioimage-io/bioimage.io, or change their
   "last release" cells to "none fetched".
6. Hosted rows' license cells (ollama-library, ngc, vertex, azure, sagemaker, and the platform
   side of hf, modelscope and kaggle): add a cited fetch or write "server source not checked".
7. Cite the #601 ruling (issue comment URL in web-log) or drop the date.
8. Reconcile §8: the itemized self-dedup totals 36, not 35. Fix the list or the totals, so that
   raw_signals = duplicates + unique still balances, and state how LM Studio (mapped plus parked)
   is counted.
9. §1/§2: change "18 independent organizations" to account for Kaggle under Google (17
   independent parents, largest share 2/18 = 11.1%), or explicitly define the count as distinct
   org slugs.
10. Q5: correct "4 orders of magnitude" to about 5.
11. Q8 and the qualcomm row: F0015 `previous_names` already shows quic/ai-hub-models →
    qualcomm/ai-hub-models. Record it as resolved. Optionally update the "last release" column
    for qualcomm (PyPI 0.63.0, 2026-09-23) and modelscope (PyPI 2026-09-15).
12. Minor: add a fetch for "ClearML and ZenML are the same", or drop the clause. Qualify
    "modelscope.ai international" as inferred.

## Re-check of fixes (second auditor)

Second, independent auditor, 2026-09-26. I checked only the 12 fixes above against the revised
`sweep.md`, `rows.yaml`, `fetch-log.tsv` with `raw/`, and `web-log.tsv`. Every F and W id cited
in sweep.md §1–§9 exists in the logs. `jsonschema.validate(rows.yaml, registry.schema.json)`
prints `ok`.

| # | fix | result | reason |
|---|---|---|---|
| 1 | modelscope "80,000+" (W0003) | PASS | The figure and W0003 are both gone from sweep.md. The modelscope row cites only F0115, F0070 and F0056. |
| 2 | Together/Modal/Eden AI from W0001 | PASS | W0001 is now cited only for DagsHub, which its excerpt names. The Eden AI parked row is removed, and §8 lists these signals as dropped. Minor: §8 says Northflank's excerpt doesn't name it, but W0001 lists northflank as a result site. Dropping it is conservative either way. |
| 3 | aimet-model-zoo fetch | PASS | F0128 (ecosyste.ms quic/aimet-model-zoo, 200) body shows `archived: true`, `pushed_at 2026-02-12`, fork false, which matches §8. It is now listed as added by name, not found by search. |
| 4 | 10 fork duplicates | PASS | Forks are removed from the counts, and §8 says so. |
| 5 | pytorch/hub and bioimage.io releases | PASS | F0129 and F0130 (releases?per_page=1, 200) both have the body `[]` (2 bytes, the same sha256), which supports "none: releases endpoint returns []". |
| 6 | hosted license cells | PASS | All eight hosted rows (hf, modelscope, ollama-library, kaggle, ngc, vertex, azure, sagemaker) now say "server/platform source not checked". Clients are cited as satellites. Leftover: §5 still says the openness read is "no server source published". That describes a ladder reading, not a table cell. Consider "not checked" there too. |
| 7 | #601 ruling | PASS | W0073 is `issue_read(get_comments)` on issues/601#issuecomment-5819306219, `created_at 2026-09-24T17:53:56Z`. Its excerpt says the huggingface-hub record is the client and the Hub platform is a new product. That supports both the date and the ruling. |
| 8 | §8 reconciliation | PASS | Self-dedup lists 25 second artifacts plus 1 satellite, which is 26. Already-mapped is 5, so duplicates = 31. Parked table has 29 rows, and accepted = 18. The equations hold: 31 + 47 = 78 and 18 + 29 = 47. LM Studio is explained as two signals: the app is a mapped duplicate and the catalog is parked. |
| 9 | 18 independent orgs | PASS | §1 and §2 say "18 distinct org slugs, 17 independent parents" and give Google 2/18 = 11.1% (W0072 excerpt: TechCrunch 2017-03-08, Kaggle "within the large umbrella of Google Cloud"). rows.yaml has 18 distinct org slugs, including kaggle and google-cloud. |
| 10 | Q5 orders of magnitude | PASS | Q5 now says "about 5 orders". 225,502,059 / 1,046 ≈ 2.16×10^5 (F0069, F0073 bodies). |
| 11 | Q8 and release columns | PASS | F0015 `previous_names` = [quic/ai-stack-models, quic/ai-hub-models, qualcomm/ai-hub-models], which matches the qualcomm row and Q8 (now "resolved by evidence"). F0131 PyPI qai-hub-models is version 0.63.0, uploaded 2026-09-23T21:59:31. The modelscope row cites F0070 `latest_release_published_at` 2026-09-15. |
| 12 | ClearML/ZenML; modelscope.ai | PASS | The ClearML/ZenML clause is gone. The modelscope row now says "international edition is inferred from the title, not fetched" (W0020). |

Other checks: rows.yaml has 18 products. The §2 open/closed split (8/0/2/8) and the Google
share agree with §6b and rows.yaml.

**Overall: PASS** (all 12 fixes verified, with two wording nits in fixes 2 and 6 that don't block).
