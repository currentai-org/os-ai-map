# Independent audit: assurance_evidence (6a) + responsible_ai_measurement (6b) sweep

Auditor run: 2026-09-26 (UTC). I re-fetched everything below live with curl (plus one WebFetch of a
github.com page where ecosyste.ms returned 404), and did not rely on the sweep's conclusions. Re-fetch bodies are in
`/tmp/claude-0/-home-user-os-ai-map/e16fc3b8-d9ca-5654-96cc-681e1bf0a192/scratchpad/audit/`.
Integrity pre-check: all 188 `raw/Fnnnn.body` files exist, and each one's size and sha256 match `fetch-log.tsv`.

## Verdicts

| # | check | verdict |
|---|---|---|
| 1 | Re-fetch 15+ claims live | **FAIL**: 1 of 16 sampled claims is wrong (langfair's last release). The out-of-sample issues are 3 more wrong last-release values and 1 wrong canonical repo. |
| 2 | Unsourced facts | **FAIL**: 3 claims cite a W/F id that does not contain the fact. Closed-row license cells carry no id. The push and archived columns carry no id throughout. |
| 3 | Every artifact resolves live | **FAIL**: `regula-ai` on PyPI has no distributions (JSON 404). `lfwa/carbontracker` is not canonical. |
| 4 | Schema + dedup | **PASS** |
| 5 | Counts reconcile, §2 recomputable | **FAIL**: the 6a usage-instrument count (13) contradicts its own 14-item list. The equations balance. |
| 6 | Recency and breadth | **PASS with issues**: every timestamp is 2026-09-26. 7 of the 25 names listed as "found by search" have no search entry, and 3 claims read like recall. |

## Check 1: live re-fetch (every third row across both §6b tables)

The sample is rows 1, 4, 7, … 46 of the 47 concatenated rows, which gives 16 claims.

| # | row | claim | sweep value | live value (source) | verdict |
|---|---|---|---|---|---|
| 1 | compliance-trestle | adoption | PyPI 63,201/mo | 63,201/mo (packages.ecosyste.ms) | PASS |
| 2 | model-signing | license | Apache-2.0 | Apache License 2.0 text (raw LICENSE) | PASS |
| 3 | c2pa-sdk | adoption | crates 90-day 1,150,875; total 10,397,885 | 1,150,875 / 10,397,885, max 0.91.0 (crates.io) | PASS |
| 4 | validmind-library | license | AGPL-3.0 OR ValidMind Commercial | dual AGPL-3.0 / commercial text (raw LICENSE; PyPI) | PASS |
| 5 | air-blackbox | last release | 1.15.0, 2026-08-29 | 1.16.0 uploaded 2026-09-26T19:45Z (PyPI JSON), minutes before the sweep's fetch | PASS (same-day drift) |
| 6 | halo-record | identity + activity | bkuan001/halo-record, push 2026-09-15 | same; PyPI repository_url matches; 0.2.45 on 2026-09-14 | PASS |
| 7 | data-provenance-collection | activity | not archived, push 2025-03-26 | archived=false, push 2025-03-26 (ecosyste.ms) | PASS |
| 8 | verifyml | activity + license | push 2022-02-07; Apache-2.0 | push 2022-02-07, not archived; Apache text | PASS |
| 9 | codecarbon | adoption | PyPI 142,686/mo | 142,686/mo | PASS |
| 10 | ecologits | identity + license | mlco2/ecologits; MPL-2.0 | full_name mlco2/ecologits; MPL-2.0 text | PASS |
| 11 | ml-co2-impact | license | MIT | MIT text (raw LICENSE) | PASS |
| 12 | fairlearn | adoption | PyPI 154,164/mo | 154,164/mo | PASS |
| 13 | what-if-tool | last release | witwidget 1.8.1, 2021-10-12 | 1.8.1, 2021-10-12 (PyPI JSON) | PASS |
| 14 | langfair | last release | 1.0.0, 2024-10-21 | **0.8.0, 2026-01-09**. No 1.0.0 exists in PyPI's release list. | **FAIL** |
| 15 | fairlens | license | BSD-3-Clause | BSD 3-Clause text (LICENSE.md) | PASS |
| 16 | trustmark | license | MIT with Adobe notice | Adobe notice + MIT text | PASS |

Extra spot checks, all PASS: the deepprove LICENSE is the Lagrange proprietary license, not Apache;
audioseal is 127,614/mo on PyPI and 46,580 on HF; ezkl still has no LICENSE; every other stars, push and
downloads figure in both files matched its live value.

## Issues

1. **rows.responsible_ai_measurement.yaml, `langfair`; sweep.md §6b langfair row, "last release".** The sweep
   has `1.0.0, 2024-10-21 (F0123)`, but PyPI's latest release is `0.8.0`, uploaded 2026-01-09, and 1.0.0 is not in its release list.
   It should read `0.8.0, 2026-01-09 (PyPI JSON)`. Cause: packages.ecosyste.ms `latest_release_number` is
   unreliable, so last-release values should come from pypi.org JSON.
2. **sweep.md §6b mlte row, "last release".** The sweep has `2.6.0, 2026-04-27`, but PyPI has `2.7.0`, uploaded 2026-08-21, before
   this run. It should read `2.7.0, 2026-08-21`.
3. **sweep.md §6b markllm row, "last release".** The sweep has `0.2.0, 2024-07-31`, but PyPI's releases are 0.1.3–0.1.5 and
   0.2.0 does not exist. It should read `0.1.5, 2024-10-21`.
4. **sweep.md §6b carbontracker row, "last release".** The sweep has `2.4.5, 2026-05-16`, but PyPI has `2.4.7`, uploaded 2026-08-27.
   It should read `2.4.7, 2026-08-27`.
5. **rows.responsible_ai_measurement.yaml, `carbontracker`: `github: lfwa/carbontracker`, `org: lfwa`.** Not
   canonical. github.com redirects to **`saintslab/carbontracker`** (WebFetch). ecosyste.ms returns 200 for
   `saintslab/carbontracker` (MIT, not archived, not a fork, push 2026-08-27, 483★), and PyPI's live
   project_urls point there too. It should read `github: saintslab/carbontracker`, `org: saintslab`, and the §6b row should read
   "no/no, push 2026-08-27, 483★" instead of "fetch did not complete". The org then holds one row, so §2 is unchanged. No
   index collision.
6. **rows.assurance_evidence.yaml, `regula`: `pypi: regula-ai`.** It does not resolve. `https://pypi.org/pypi/regula-ai/json`
   returns 404 on repeated tries, and the PyPI simple index lists **no files**. The repo README (fetched live) says "PyPI
   distribution is currently unavailable" and installs via `pipx install git+https://github.com/kuzivaai/getregula.git@main`.
   The sweep only checked packages.ecosyste.ms (F0135, which last synced 2026-09-04). The `pypi` field should be dropped, and the §6b row
   should read "no installable PyPI distribution (README)". The regula row's 384/mo is not a usable instrument. That leaves
   Regula at 4★ with no package, **below the sweep's own retrieval cutoff**. The cutoff was not used to reject found
   candidates, so the row can stay, but §2's sentence "Regula (4 stars, 384/mo) clear[s] it through [its] package" is
   false and should be corrected.
7. **sweep.md §2 (6a), "candidates with a usage instrument: 13".** The parenthetical lists 13 PyPI rows plus
   c2pa-sdk on crates, which is **14**, and it matches the rows file (13 `pypi` + 1 `crates`). The same figure appears in
   §1 ("13 carry a download instrument"). After fix 6 (regula removed) the true count is **13**, but the list must then drop
   regula: 12 PyPI + 1 crates.
8. **sweep.md §6b c2pa-sdk row, notes "spec 2.4 (W0009)".** W0009's excerpt says nothing about a spec version, and no
   F body contains it. This reads as recall. Either fetch the C2PA spec page and cite it, or delete it.
9. **sweep.md §6b air-blackbox row, members "11 PyPI packages (W0001)".** W0001's excerpt doesn't mention the
   number, and neither does F0151 or F0136. Unsourced. Either fetch it and cite it, or delete it.
10. **sweep.md §6b halo-record row, members "halo-record-ts (W0019)", and §7 #40.** W0019 doesn't mention
    halo-record-ts, and no F body does. Unsourced. Either fetch the npm package or repo and cite it, or delete it.
11. **sweep.md §6b ibm-watsonx-governance and credo-ai rows, license cell "proprietary".** No id is cited. It should
    cite F0156 and F0157 (both are already in the log).
12. **sweep.md §6b, both tables, the "archived/fork" and "last push" columns (and stars in several rows).** Most cells
    carry no F id. The §6b header covers them implicitly ("Stars and pushes come from ecosyste.ms"), and every value
    matches the row's logged ecosyste.ms body, but check 2 needs an id per cell. The fix is to add the row's
    ecosyste.ms F id (for example `2026-08-11 (F0003)`). This is mechanical and does not change any value.
13. **sweep.md §8, "Found by search, not named in either brief".** Seven of these have no WebSearch or WebFetch entry in
    `web-log.tsv`: **VerifyWise, AICert, Data Provenance Collection, eco2AI, perun, Responsible AI Toolbox, LiFT**. Their
    facts were fetched (F0019, F0025, F0024, F0038, F0040, F0050, F0051), so nothing about them is unsourced, but the
    "found by search" provenance is not shown. Either log the search that surfaced them or relabel them "added from
    prior knowledge, then verified by fetch". Holistic AI Library and Content Seal are borderline: the brief names
    Holistic AI as a closed comparator and AudioSeal, VideoSeal and Stable Signature as members.
14. **sweep.md §5, header "License strings met (text read, not label)".** For most open rows the only cited source is the
    ecosyste.ms label (for example mlte F0003, codecarbon F0031, ml-co2-impact F0035). Text was read only where the
    label was `other` or null. The texts I sampled (6 of them) all agree with the labels, so no value is wrong. The header
    should read "text read where the label was other/null; label elsewhere", or the remaining texts should be fetched.
15. **Minor: sweep.md §6b halo-record "last release".** The cell gives a date only. It should read `0.2.45, 2026-09-14`.

## Check 2: sourcing detail

- Every F and W id cited in sweep.md exists in the logs, and all 188 F rows and 20 W rows are cited.
- The cited non-200 F rows are each used as evidence of absence, or as "did not complete", and the sweep says so: ezkl
  LICENSE 404s, ml-energy-leaderboard LICENSE 404s, regula LICENSE 404 (F0183), compl-ai PyPI 404 (F0138),
  carbontracker ecosyste.ms 404 and ungh 429 (F0033, F0095, F0061), and the genai-impact 404s (F0037, F0152), where the
  move is backed by W0017. F0069–F0072 (the c2pa-rs `LICENSE*` 404s) are superseded by F0091 and F0092. That handling is acceptable.
- Every package declaration passes the package-trap rule on the logged evidence: either the repository_url matches
  the declared repo, or the README or project_urls install path is cited. Verified for nv-attestation-sdk (F0159 PyPI badge),
  mlcroissant (F0158), witwidget (F0170), ezkl (F0094), ecologits (packages.ecosyste.ms install command, W0017),
  opencomplai (the repo and PyPI share the homepage opencomplai.com; the PyPI description gives `pip install opencomplai`) and
  raiwidgets (F0169).
- Failures: issues 8–12.

## Check 3: live resolution of all artifacts

- 45 GitHub repos: 44 resolve on ecosyste.ms with `full_name` equal to the declared value. None is archived and none is a fork.
  The four dormant repos are reported as dormant, which is correct. `lfwa/carbontracker` gets a 404 on ecosyste.ms and redirects on github.com, so it is not canonical
  (issue 5).
- 31 PyPI packages: 30 resolve on pypi.org JSON. `regula-ai` does not (issue 6).
- 1 crate (`c2pa`): it resolves, and its repository is `contentauth/c2pa-rs`.
- 3 homepages (IBM, Credo AI, mlco2 impact): all return HTTP 200.

## Check 4: schema and dedup

- `rows.assurance_evidence.yaml` validates as `ok`, and so does `rows.responsible_ai_measurement.yaml`.
- No slug, retired alias, GitHub repo or PyPI package in either file matches `research/corpus-index.tsv`. The corrected
  `saintslab/carbontracker` doesn't collide either. Reused org slugs match the index (`nvidia`, `ibm`, `hugging-face`,
  `google`, `microsoft`, `linkedin`, `meta`, `adobe`). The three index duplicates named in §8
  (agent-governance-toolkit, synthid-text, huggingface-hub) are present in the index as described.

## Check 5: counts

- §8: 99 = 9 + 90 and 90 = 47 + 43 both balance. The 9 duplicates are enumerated, §7 has exactly 43 parked rows, and the rows files hold 24 + 23 = 47.
  `raw_signals` itself is not independently recomputable, because no signal list is kept, so it is only the sum.
- The 6a figures recompute from §6b: open 19, source-available 3, closed 2. IV 8 and SA 16. 24 distinct orgs, so the largest share is 1/24 = 4.2%. 18 of the 22
  artifact-backed rows pushed on or after 2025-09-26. **The usage-instrument count is wrong** (issue 7).
- The 6b figures recompute: open 22, source-available 1. Sub-areas 9 / 10 / 4. 19 orgs, with mlco2 largest at 3/23 = 13.0%. 21 rows are active:
  carbontracker's live push of 2026-08-27 confirms its active status. 18 rows have a usage instrument.

## Check 6: recency and breadth

- Every `fetch-log.tsv` and `web-log.tsv` timestamp is 2026-09-26 (between 20:00 and 20:08 UTC), so all are from this run.
- Candidates surfaced by a logged search and not named in the briefs: ValidMind Library (W0012); Venturalitica, AIR
  Blackbox, Regula, OpenComplAI, COMPL-AI (W0001, W0016); Halo Record (W0011, W0019); DeepProve and ZKML (W0003);
  OWASP AIBOM Generator (W0002; the brief names only the AIBOM class); IBM watsonx.governance (W0014); EcoLogits (W0004);
  ML.ENERGY Leaderboard (W0015); LangFair, FairLens and Holistic AI Library (W0006); Content Seal (W0018); MarkLLM
  (W0005). Parked ones: dstack, sek8s and Tinfoil (W0007); encypher-c2pa (W0009); SAI Platform and ModelRiskOps (W0008); VeriTrace
  (W0011); GreenBench and LLMCO2 (W0004); DocML and CardGen (W0013); mcp-eu-ai-act (W0001).
- Claimed as found by search but with no logged search: see issue 13.
- Recall-like claims with no fetch behind them: issues 8, 9 and 10. Beyond those, the stale registry-derived release
  values in issues 1–4 were fetched, but from a stale mirror. A spot check against pypi.org JSON would have caught them.

## Summary

Fix issues 1–7 (data errors: 4 wrong last-release values, 1 non-canonical repo, 1 dead package declaration, and 1
metric that contradicts its list) and 8–11 (unsourced claims). Issues 12–15 are presentation fixes that change no value.
Neither verdict (6a GO-WITH-CHANGES, 6b PARK) depends on any of these issues.

## Re-check (second auditor)

Re-check run: 2026-09-26 (UTC). I checked only the items fixed in response to issues 1–15. Every fact was re-fetched live with curl
(pypi.org JSON, repos.ecosyste.ms), and I recomputed every count from `sweep.md` §6/§7 and the two rows files with a script.
Integrity: all 223 `raw/Fnnnn.body` files exist, and each one's size and sha256 match `fetch-log.tsv`. That includes the new F0189–F0223.

### Per-issue

| # | issue | status | evidence |
|---|---|---|---|
| 1 | langfair last release | **PASS** | §6b `0.8.0, 2026-01-09 (F0214)`. Live pypi.org: 0.8.0, 2026-01-09T14:23Z. F0214 body agrees. |
| 2 | mlte last release | **PASS** | `2.7.0, 2026-08-21 (F0190)`. Live: 2.7.0, 2026-08-21T13:37Z. |
| 3 | markllm last release | **PASS** | `0.1.5, 2024-10-21 (F0219)`. Live: 0.1.5, 2024-10-21T10:30Z. |
| 4 | carbontracker last release | **PASS** | `2.4.7, 2026-08-27 (F0204)`. Live: 2.4.7, 2026-08-27T07:54Z. |
| 5 | carbontracker canonical repo | **PASS** | The rows file has `github: saintslab/carbontracker` and `org: saintslab`. Live ecosyste.ms returns saintslab/carbontracker: archived=false, fork=false, push 2026-08-27, 483★, MIT. That matches F0220 and §6b. |
| 6 | regula `pypi: regula-ai` | **PASS** | Regula is gone from `rows.assurance_evidence.yaml` (23 rows) and parked as §7 #44 with the reason: F0197 404, F0222 simple index with no files, F0223 README "PyPI distribution is currently unavailable". All three bodies say what is claimed. Live `https://pypi.org/pypi/regula-ai/json` returns **404**. The false §2 sentence was rewritten. |
| 7 | 6a usage-instrument count | **PASS** | §2 says 13 and lists 12 PyPI + 1 crates. The rows file has 12 `pypi` + 1 `crates` = 13. §1 says 13. |
| 8 | c2pa "spec 2.4" | **PASS** | Removed. There is no "spec 2.x" string left in sweep.md. |
| 9 | air-blackbox "11 PyPI packages" | **PASS** | Removed. The members cell is "—". |
| 10 | halo-record-ts via W0019 | **FAIL (partial)** | Fixed in the §6b members cell, which now cites F0221 (ecosyste.ms `bkuan001/halo-record-ts`, a 200 whose description says it is the TypeScript recorder of the same chain format as halo-record, so it supports the claim). **§7 #40 still cites only W0019**, and W0019's excerpt does not mention halo-record-ts. Fix: change the §7 #40 source to F0221. |
| 11 | closed-product license cells | **PASS** | They now cite F0156 and F0157, both HTTP 200 in the log. The bodies are commercial product pages (demo/trial/pricing and "platform" copy, "compliance evidence capture", "audit-ready evidence") and offer no license or source. That supports "proprietary SaaS; no license offered" as evidence of absence. |
| 12 | archived/fork, push and stars ids | **PASS** | Every artifact-backed cell in both tables now carries an F id. I spot-checked 14 cells against their bodies: F0001, F0003, F0009, F0013, F0021, F0024, F0031, F0039, F0049, F0058, F0060, F0151, F0176, F0177. All are HTTP 200, and archived/fork/push/stars match in every case. |
| 13 | "found by search" provenance | **PASS** | Every W id in the §8 list exists (W0001–W0006, W0011, W0012, W0014–W0016, W0018, W0019). The seven entries with no logged search are now in a separate list labeled "added from the sweeper's own lead list, with no discovery search logged". |
| 14 | §5 license header | **PASS** | It now says that label-only rows rest on the GitHub label, spot-checked for six rows, and that a maintainer should read the text before promotion. It no longer claims the text was read. |
| 15 | halo-record last release | **PASS** | `0.2.45, 2026-09-14 (F0199)`. Live: 0.2.45, 2026-09-14T04:42Z. |

Other last-release values checked live on pypi.org JSON, all matching §6b: air-blackbox 1.16.0 (2026-09-26), opencomplai 0.8.0
(2026-09-24) and ezkl 23.0.5 (2026-02-20). The F0196, F0198 and F0200 bodies agree with those values.

### Recomputed metrics (§2, §8)

- **6a**: 23 rows, split open 18 / source-available 3 / closed 2. IV 8 and SA 15. There are 23 orgs, each holding one row, so the largest share is 4.3%. 21 rows carry
  a GitHub repo, and 17 of them pushed on or after 2025-09-26; the 4 inactive ones are data-provenance-collection, aicert, zkml and verifyml. The usage
  instrument count is 13. All of these match §1 and §2.
- **6b**: 23 rows, split open 22 / source-available 1. Sub-areas are 9 / 10 / 4. There are 19 orgs, and mlco2 is the largest at 3/23 = 13.0%. 21 rows are active (the inactive ones are eco2ai and
  invisible-watermark). All 18 usage instruments are PyPI. All of these match.
- **§8**: accepted is 23 + 23 = 46. §7 has **44** numbered rows. The duplicates list has 9 entries. So 90 = 46 + 44 and 99 = 9 + 90 both balance.

### Schema and dedup

Both rows files validate as `ok` against `docs/schemas/registry.schema.json`. No slug, retired alias, GitHub repo or PyPI
package in either file collides with `research/corpus-index.tsv`, and that includes `saintslab/carbontracker`.

### New issues

- **Minor (N1), sweep.md §2 6a retrieval-cutoff bullet.** It says "Four already-surfaced candidates fell under it" but now
  lists five: model-card-generator, sai-platform, ModelRiskOps, eu-ai-act-toolkit and Regula. It should read "Five". No metric changes.
- **Cosmetic, not a defect.** For the opencomplai license, §5 cites F0137 and §6b cites F0147. Both bodies say AGPL-3.0-only.

### Final status per check

| # | check | final |
|---|---|---|
| 1 | Re-fetch claims live | **PASS** |
| 2 | Unsourced facts | **FAIL (one residual)**: §7 #40 halo-record-ts still cites W0019 (a one-cell fix: cite F0221) |
| 3 | Every artifact resolves live | **PASS** |
| 4 | Schema + dedup | **PASS** |
| 5 | Counts reconcile | **PASS** (wording nit N1: "Four" should be "Five") |
| 6 | Recency and breadth | **PASS** |

## Residual fixes (sweep author, after the second re-check)

- Issue 10 (residual): §7 #40 halo-record-ts now cites F0221 (ecosyste.ms record for bkuan001/halo-record-ts, HTTP 200) instead of W0019. The check 2 residual is resolved.
- New minor issue: the §2 6a cutoff bullet now says "Five already-surfaced candidates", which matches the five it lists.
- The opencomplai license citation difference (F0137 vs F0147) is cosmetic. Both bodies say AGPL-3.0-only, so it is left as is.

Final status after these edits: checks 1–6 PASS.
