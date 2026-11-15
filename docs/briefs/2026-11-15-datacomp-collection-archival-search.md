# DataComp CommonPool collection: archival search, 2026-11-15

This brief follows `docs/briefs/2026-11-14-datacomp-download-provenance.md`, which left one point
open on `openclip.openness`: which img2dataset version and which `disallowed_header_directives`
value fetched CommonPool's images between December 2022 and March 2023, and whether anything checked
image-host robots.txt or an opt-out list. It records one bounded search for direct evidence of those
settings in three places: the contributors' public repositories, archived run configurations and
logs, and public statements by the contributors. It also checks an account of
mlfoundations/datacomp issue #67 that the maintainer received. It does not repeat what the
2026-11-14 brief established. It changes no score, hold, rubric or ruling and proposes none. Like
the other records in `docs/briefs/`, it describes what its sources said on the date above and gets
refreshed by a new brief, not edited.

Map-side claims cite `main` at `632c0612`. Outside sources are listed under [Sources](#sources),
all read today. No dataset image was fetched. Nothing was posted to any outside site.

## The short answer

1. **One contemporaneous artifact from a data-collection lead.** Vaishaal Shankar's img2dataset
   pull request #272, opened 2023-01-17, carried a Ray example whose original commit (`6183e5ae`,
   committed 2023-01-21) holds a full `download()` call and the cluster setup that ran it. The setup
   installs his fork at commit `7aadba42` (2023-01-14), which is release 1.41.0 plus a Ray
   distributor. The call passes no `disallowed_header_directives` and no `user_agent_token`. At that
   commit, an unset list becomes `["noai", "noimageai", "noindex", "noimageindex"]`. Its settings
   match the paper's description of the collection: AWS, 512-pixel largest-side resize, sha256
   hashes, a `uid` column. Its readme says it reached "220,000 images/second on a cluster of 100
   m5.24xlarge", and the PR description says "consistently for 24 hours". **It never names DataComp
   or CommonPool.** It is direct evidence of a configuration Shankar published and reported running
   at scale in January 2023. It is not evidence that this configuration processed CommonPool: the
   match is strong circumstantial evidence, not confirmed collection provenance. If it is the
   collection's configuration, it covers the collection from mid-January 2023 on, not December 2022.
2. **One logged run in the window, not tied to CommonPool.** Romain Beaumont's public Weights &
   Biases project holds a run from 2022-12-12 to 2022-12-15 that fed a Common Crawl URL list
   (cc2dataset output in LAION's S3 bucket) into img2dataset and wrote to `s3://s-laion/rawcc400M`.
   It attempted 877,328,096 URLs. Its logged `disallowed_header_directives` is `None` and its
   command line passes no such flag, so it did not honor X-Robots-Tag. Its resize settings (384
   pixels, `keep_ratio`) do not match Appendix H, and nothing ties it to CommonPool.
3. **No collection scripts, logs or statistics found anywhere else.** All branches and pull-request
   refs of mlfoundations/datacomp start at 2023-04-27. The DataComp Hugging Face repositories,
   including their February and March 2023 revisions, hold only `.parquet` and `.npz` index files.
   No `_stats.json`, config or log was ever committed there. datacomp.ai has participant
   instructions only. The Wayback Machine could not be reached.
4. **No contributor has stated the version, commit or opt-out flags.** In issue #67 a user asked
   for "the version (commit ID) and commandline of img2dataset that you used". Beaumont replied that
   Gabriel Ilharco "should be able to say who ran this hash computation and what commit was used".
   No one answered with a commit, version or command.
5. **The #67 account is mostly supported.** Shankar did say the hash "was computed during
   commonpool download and then passed around to the dc1b parquet". Beaumont did say "the hashes
   were computed with img2dataset", but he pointed the original-computation question at Ilharco by
   name, not at "the team". Ilharco did report visually similar images with mismatched hashes and
   suggested checking "our metadata features (e.g. CLIP features)". The request for the commit and
   command line is in the thread, unanswered. Section 4 has the detail.
6. **robots.txt and opt-out lists: nothing new.** cc2dataset, which turns Common Crawl into URL
   lists, has no robots.txt, `noai` or opt-out logic in any revision. No source in the search ties
   the collection to Spawning or any other list.

The search stopped there. The three kinds of evidence produced the two artifacts above and no
direct statement of the collection's settings.

## 1. Scripts in contributors' public repositories

### mlfoundations/datacomp, every branch and pull request

The clone holds 10 branches and 22 pull-request heads, 100 commits in all. The earliest is
2023-04-27 ("Initial commit"), a month after the collection window closed. A search of every
revision for `disallowed_header`, `robots`, `x-robots`, `noai`, `user_agent_token`, `opt-out` and
`spawning` found two things, both in unmerged pull requests from after the window:

- PR #29, by Padge91 (commit `983250e3`, 2023-07-05): "Updated img2dataset to pull from the
  Spawning-Inc fork, which uses the datadiligence package to remove opt-outs of various means." It
  is open, with no maintainer comment (page read through the summarizing fetcher).
- PR #58, by 0x2b3bfa0 (commit `482628b7`, 2023-09-15): "Expose img2dataset distributor", which
  bumps the pin to `img2dataset==1.42.0`. It is open.

Every other revision, on any branch, pins `img2dataset==1.40.0`, as the earlier brief recorded for
`main`. No branch holds
collection code.

### rom1504/img2dataset, every branch and pull request

The clone holds 24 branches and 190 pull-request heads. Between November 2022 and March 2023 the
DataComp authors' commits are the ones the earlier brief listed (Gadre, Ilharco, Smyrnis), plus two
by Shankar that it did not: "added ray as a distributor" (2023-01-13) and "add block size for fs
open" (2023-01-26). Both sit on PR #272 and were squash-merged on 2023-08-20 as `171e3cd6`,
released in 1.42.0 the same day ("ray distibutor (thanks @Vaishaal)", HISTORY.md).

The `dataset_examples/` CommonPool page arrived on 2023-04-28 (#306, Ilharco) and the DataComp-1B
page on 2023-07-12 (#328, Ilharco). Both point to the DataComp repository's `download_upstream.py`
and say nothing about the original collection. A search of every revision for `datacomp`,
`commonpool` and Shankar's name found nothing else from the window.

### PR #272: the January 2023 Ray example

The original commit `6183e5ae` (author date 2023-01-13, committed 2023-01-21) adds
`examples/ray_example/`. Its `ray_example.py` calls, verbatim apart from indentation:

```python
download(
    processes_count=1,
    thread_count=32,
    retries=0,
    timeout=10,
    url_list=args.url_list,
    image_size=512,
    resize_only_if_bigger=True,
    resize_mode="keep_ratio_largest",
    skip_reencode=True,
    output_folder=args.out_folder,
    output_format="webdataset",
    input_format="parquet",
    url_col="url",
    caption_col="alt",
    enable_wandb=True,
    subjob_size=48*120*2,
    number_sample_per_shard=10000,
    distributor="ray",
    oom_shard_count=8,
    compute_hash="sha256",
    save_additional_columns=["uid"]
)
```

Its `cluster_minimal.yaml` puts up to 500 spot `m5.24xlarge` workers in AWS `us-east-1` and runs:

```
- pip uninstall -y img2dataset
- pip install git+https://github.com/vaishaal/img2dataset.git@7aadba42f8008106bd38475e06e78e79dfe4bbeb
```

followed by a `wandb login` with a literal credential, not reproduced here. Its `readme.md` says
"The tooling to set up a Ray cluster on AWS is slightly better at the time of writing this document
(Jan 2023)" and "Using the above code I was able to achieve a maximum download rate of 220,000
images/second on a cluster of 100 m5.24xlarge (9600 cores)." The PR description, read through the
summarizing fetcher, says "For running large jobs on AWS I found a couple problems with the spark
backend" and "Using this I was able to get over 200k/images second on a cluster of 100 m5.24xlarges
consistently for 24 hours."

Beaumont's edits before the merge (`39098c9`, `7632938`, 2023-08-20) replaced the fork pin with
`pip install img2dataset`, the credential with `KEY`, and the readme's Jan 2023 paragraph and rate
with a link to Ray's documentation. The merged example on `main` keeps the same `download()` call.
So the January configuration survives only in the PR's pre-merge history and in the fork.

**The pinned fork commit.** `git clone https://github.com/vaishaal/img2dataset` worked. Commit
`7aadba42` ("remove some print", 2023-01-14 14:36 -0800) is on the fork's `ray` branch and
describes as `1.41.0-11-g7aadba4`. `setup.py` there reads `version="1.41.0"`. The 11 commits over
the 1.41.0 tag touch only `distributor.py`, `main.py` (the Ray option and a `max_jobs` argument) and
`writer.py`. The opt-out code is 1.41.0's, unchanged (`main.py` lines 106-113 at `7aadba42`):

```python
    disallowed_header_directives: Optional[List[str]] = None,
    ...
    if disallowed_header_directives is None:
        disallowed_header_directives = ["noai", "noimageai", "noindex", "noimageindex"]
    if len(disallowed_header_directives) == 0:
        disallowed_header_directives = None
```

Run as written, that example drops any image whose response carries an un-scoped `noai`,
`noimageai`, `noindex` or `noimageindex` X-Robots-Tag directive. With no `user_agent_token`, a
directive scoped to a named agent does not apply. Nothing in it reads robots.txt.

**How it lines up with the paper.** Each row compares the example with the DataComp paper as the
2026-11-14 brief quoted it.

| Paper | Ray example |
|---|---|
| "100s of AWS CPU nodes for Common Crawl parsing and data download" (Q23) | AWS `us-east-1`, up to 500 `m5.24xlarge` workers; 100 in the stated run |
| Downloaded December 2022 to March 2023 (Q26) | Written January 2023; fork commit 2023-01-14 |
| Largest dimension capped at 512 pixels (Appendix H) | `image_size=512`, `resize_mode="keep_ratio_largest"`, `resize_only_if_bigger=True` |
| `sha256` and `uid` fields in the metadata (Table 8) | `compute_hash="sha256"`, `save_additional_columns=["uid"]` |
| About 40B samples attempted (Section 3.2) | Over 200,000 images a second for 24 hours, which is about 17B attempts a day (arithmetic from the PR's own figures) |
| URL lists parsed from Common Crawl | Parquet input with `url` and `alt` columns, the columns cc2dataset writes (below) |

The match is close, and the author is the paper's "Candidate pool lead". It is still a match, not
a statement. The example names no dataset, its `url_list` is an argument, and the published pool's
caption column is `text`, not `alt`. A renaming step after download would explain that, but none is
documented.

### rom1504/cc2dataset

The clone (5 branches, 2022-11-29 to 2023-12-09) is the tool that turns Common Crawl WAT files into
URL and caption lists. Beaumont wrote nearly all of it in the run-up to the collection: release
1.0.0 on 2022-11-30, 1.4.0 on 2022-12-06. Its README at 1.4.0 thanks "[Vaishaal] for providing the
initial CC parsing code with efficient libraries". At 1.4.0, `extract_documents_from_wat` sets
`link["uid"] = str(hashlib.md5((link["alt"] + link["url"]).encode()).hexdigest())` and the output
frame is `df = output.toDF(["uid", "url", "alt"])`. Those are the input columns the Ray example
reads. No revision on any branch mentions robots.txt, `noai`, `noindex`, `nofollow`, opt-outs,
Spawning, DataComp or CommonPool.

### Contributors' other public repositories

The GitHub API is limited to this session's own repositories, so the contributors' repository lists
could not be read. Forks and repositories under likely names were checked directly:

- `gabrielilharco/img2dataset`: branches `bump_wds`, `fsspec`, `resizer`, `v1.40` (his 1.40.0
  release branch) and `datacomp`. The `datacomp` branch is the July 2023 documentation PR #328.
  None holds a collection config.
- `GeorgiosSmyrnis/img2dataset`: branches for blurring, hashing and `write_check`. `write_check`
  (2023-03-05 and 2023-03-14, "Writing improvements" and "Edits to saving format") adds a shard-name
  prefix and moves the temporary directory to `/tmp`. It does not touch the opt-out code.
- `sagadre/img2dataset`: `main` only, at a 2022-12-19 upstream commit.
- `Vaishaal/cc2dataset`, `Vaishaal/datacomp`, `gabrielilharco/datacomp`: GitHub asked for
  credentials, which it does for a repository that is missing or private. Not read.

## 2. Archived configurations and logs

### Weights & Biases

img2dataset's wandb logger records the call's `config_parameters`. From 1.39.0 on, that dict is
taken after the default list is filled in (`main.py` at the 1.39.0 tag, lines 94-99; at 1.40.0,
lines 100-105). So from 1.39.0 a logged list is what ran, and a logged `None` means the caller
passed `'[]'`. Before 1.39.0, `None` meant no filtering.

W&B's public GraphQL API answers anonymous reads of public projects. Results:

- `rom1504/img2dataset` is public: 562 runs from 2021-09 to 2024-01. In the window: 111 runs in
  December 2022, 32 in January 2023, none in February or March. Nearly all are benchmarks on local
  test files (`/media/hd/testing/...`, LAION and SBU captions at 256 pixels). The runs from
  2022-12-19 on that log the list show `['noai', 'noimageai', 'noindex', 'noimageindex']`. Some
  runs on 2022-12-21 and 2022-12-24 log `None`. No run has the CommonPool shape: 512 pixels,
  `keep_ratio_largest`, `sha256`, `uid`.
- Two runs there read Common Crawl output. `ylj2nunh` (2022-12-12 03:17 UTC, finished) downloaded
  one part file of `s3://s-laion/cc-proc-test/outputs/2022-12-02-15-10-58/merged`: 1,665,125
  samples, 47.4% success. `3nxu4hnn` (2022-12-12 03:41 UTC to its last heartbeat 2022-12-15 20:23,
  crashed) read the whole directory and wrote to `s3://s-laion/rawcc400M`. Its logged command line
  is `img2dataset --url_list s3://s-laion/cc-proc-test/outputs/2022-12-02-15-10-58/merged
  --input_format parquet --url_col url --caption_col alt --output_format webdataset --output_folder
  s3://s-laion/rawcc400M --processes_count 96 --thread_count 64 --image_size 384 --resize_mode
  keep_ratio --resize_only_if_bigger True --enable_wandb True --distributor multiprocessing`, on an
  AWS kernel (`Linux-5.15.0-1023-aws`). Its summary records 877,328,096 samples at 47.4% success.
  The logged `disallowed_header_directives` is `None`, with no flag passed. That pins the installed
  release between 1.34.0 and 1.38.x, or a checkout from before 1.39.0, and means the X-Robots-Tag
  check was off.
- `vaishaal`, `mlfoundations`, `laion`, `laion-ai`, `gabrielilharco`, `sagadre`, `gsmyrnis`,
  `georgiossmyrnis`, `datacomp` and `romainbeaumont`: no public project named `img2dataset` (and
  none named `datacomp` under `vaishaal` or `mlfoundations`). The Ray example logged to wandb under
  whichever account its credential belongs to, in img2dataset's default project `img2dataset`. No
  such project is publicly visible.

The `rawcc400M` run is the one logged download of Common Crawl URLs in the window. It is Beaumont's,
in LAION's bucket, and four days before 1.39.0 changed the default. Its 384-pixel `keep_ratio`
resize sets the shorter side, which would leave many images wider than Appendix H's 512-pixel cap,
and it computes no hash and keeps no `uid`. These sources do not show whether its images fed
CommonPool, were a trial, or served another LAION dataset.

### Hugging Face

The `mlfoundations` account has six DataComp repositories. `datacomp_pools` is the oldest: created
2023-02-01 by gsmyrnis, with 6,494 commits, 6,461 of them in February 2023. Its trees at `203ab3f4`
(2023-02-28) and `80c9c207` (2023-03-22) hold only `.parquet` and `.npz` shards and
`.gitattributes`, under `small`, `medium`, `large`, `xlarge` and `xlarge_npzs`. Today it adds a
README and `datacomp_1b/datacomp_1b_inds.npy`. `datacomp_xlarge`, `datacomp_large`,
`datacomp_medium`, `datacomp_small` and `datacomp_1b` hold shards, `.gitattributes` and a README.
No repository holds or ever held, in the revisions checked, a `_stats.json`, a config, a log or a
download report. The commit titles are "Upload files", folder deletions and README edits.

### datacomp.ai and its archives

The live site (`index.html`, `dcclip/`, `getting_started.html`, `people.html`, `workshop.html`) tells
participants to run `download_upstream.py`. It says nothing about the original collection,
img2dataset versions, robots.txt or opt-outs. The Wayback Machine's CDX endpoint reset the
connection on five attempts, and the web fetcher refused web.archive.org. Archived copies were not
read.

## 3. Public statements by contributors

GitHub issue and PR pages return 403 to `fetch_source`, so these were read through the summarizing
web fetcher. Its quotes are unverified by digest and capped at 125 characters each.

- **mlfoundations/datacomp issues.** A search for "img2dataset OR version OR robots OR opt-out OR
  commit" returned 28 items. Read in full: #67 (section 4), #68 (2023-10-04, success rate; Beaumont
  asked "Can you share a wandb of your img2dataset download?"), #59 (2023-09-16, Ray on AWS; no
  maintainer described the original download) and #29 (above). #71 was read for the earlier brief.
  None states the original version or flags.
- **rom1504/img2dataset.** A search for "datacomp OR commonpool" returned 8 items, among them #306,
  #328, #323 (Beaumont, 2023-06-24, "Add instructions to get datacomp1B") and #455 (2025, a user
  with broken links, no replies). In #293 ("Please make this tool 'opt-in' by default",
  2023-04-23), Beaumont's comments discuss the header opt-out in general, for example "Headers will
  however only affect this specific tool". They do not say what DataComp or LAION ran. #272 is
  above.
- **Hacker News**, item 35681085 (2023-04-23, the #293 discussion, read through the Algolia API):
  no comment by a DataComp author about DataComp's collection.
- **Web searches** for the Ray rate, DataComp with X-Robots-Tag or `noai`, and LAION posts on the
  collection found nothing beyond the paper, the img2dataset README, LAION's FAQ and the two 2025
  papers the earlier brief cites.

## 4. Issue #67: checking the account

The issue is "14% of SHA256 hashes not matching", opened 2023-10-04 by pfischer-nvidia, open today.
It was read through the summarizing fetcher in several passes. The page hides "2 remaining items"
between mranzinger's and Ilharco's comments of 2023-10-10, and those were not read. Every quote
below comes from that fetcher, under its 125-character limit, and is not digest-verified.

| Part of the account | What the thread shows | Verdict |
|---|---|---|
| Shankar confirmed the hashes were computed during the original CommonPool download and carried into DataComp-1B | Vaishaal, 2023-10-06, by email reply: "Yeah the original hash was computed during commonpool download and then passed around to the dc1b parquet". The fetcher reports that the sentence goes on to suggest a possible bug in the processing pipeline. On 2023-10-09 he listed hypotheses, including "Hash was corrupted somehow when subsetting CommonPool-12.8B -> DataComp-1B." and "Incomplete stream during downloading that lead to wrong hash.", and added "my money is on 2." | Supported. He states it as fact, and the same message allows that the pipeline may have broken it |
| Beaumont confirmed img2dataset was used | rom1504, 2023-10-04: "the hashes were computed with img2dataset did you also use img2dataset for verification ?" | Supported, for the hash computation |
| Beaumont directed questions about the original computation to the team | rom1504, 2023-10-05: "@gabrielilharco should be able to say who ran this hash computation and what commit was used" | Partly. He pointed to Ilharco by name, not to the team. His wording implies he did not know who ran it or on which commit |
| Ilharco took part and investigated visually similar mismatches | gabrielilharco, 2023-10-10: "We were able to find some images where the sha256 we have on file doesn't match the one if we re-download the image" and "They are very similar visually, but there's a small difference." 2023-10-11: "the images we have locally look very similar to the ones we download again." The fetcher reports he reviewed 100 mismatches by hand | Supported |
| He attributed them to download conditions | 2023-10-10: "This could be because of CDNs and how aggressive we were when downloading." 2023-10-11: "The fact that we were doing so many queries in parallel when downloading might have played a role too." | Supported (not part of the account, recorded because it describes the download) |
| He recommended comparing published CLIP features | 2023-10-10: "you could look at our metadata features (e.g. CLIP features) to check if they are roughly the same". He also said "The safest thing to do if there is concern about poison attacks is to only trust the hashes that match and ignore all else." | Supported, alongside the stricter hash-only advice |
| The thread asks for the original img2dataset commit and command line | pfischer-nvidia, 2023-10-05: "Can you provide the version (commit ID) and commandline of img2dataset that you used?" | Supported |
| With or without an answer | No commit, version or command for the original run appears. On 2023-10-09 Vaishaal wrote "So the download code that computes the hash is right here:" and linked `rom1504/img2dataset/blob/main/img2dataset/downloader.py#L203-L318C6`, the `main` branch in October 2023, not a commit | Unanswered, in the visible thread |

No comment in the visible thread mentions `disallowed_header_directives`, X-Robots-Tag, robots.txt
or opt-outs.

## Established, inferred and not found

**Established**

- A collection lead's January 2023 download configuration exists in public history: PR #272's
  original commit `6183e5ae` and fork commit `7aadba42`. It runs img2dataset 1.41.0 plus a Ray
  distributor, passes no `disallowed_header_directives` or `user_agent_token`, and so drops images
  with an un-scoped `noai`, `noimageai`, `noindex` or `noimageindex` header. Its resize, hash, `uid`
  and AWS settings match the paper's description of the collection. Its author reports running it
  at over 200,000 images a second for 24 hours on 100 `m5.24xlarge` nodes. Nothing in it identifies
  what it downloaded, so what is established is the published configuration and its reported use,
  not that it processed CommonPool.
- A LAION Common Crawl download by Beaumont from 2022-12-12 to 2022-12-15 attempted 877M URLs with
  the X-Robots-Tag check off. Its resize settings do not match Appendix H.
- cc2dataset, which produced the URL lists, writes `uid`, `url` and `alt`, with `uid` an md5 of
  caption plus URL. It has no robots.txt or opt-out logic in any revision.
- No DataComp Hugging Face repository holds a `_stats.json`, config or log. No DataComp repository
  branch or pull request predates 2023-04-27.
- In #67, Shankar said the hashes were computed during the CommonPool download and Beaumont said
  they were computed with img2dataset. A request for the original commit and command line got no
  commit, version or command.

**Inferred, not established**

- That the PR #272 configuration is the one that downloaded CommonPool. It rests on matching
  settings, the author's role, the date and the scale, not on any statement.
- That, if so, the part of the collection run with it honored X-Robots-Tag `noai` and its siblings
  by default. The 2026-11-14 brief inferred 1.37.0 or later from the resize mode. This artifact puts
  one configuration at 1.41.0 plus the Ray patch, but only from mid-January 2023.
- That the `rawcc400M` run had anything to do with CommonPool. Nothing ties them together.

**Not found**

- Any record of the img2dataset version, commit or `disallowed_header_directives` value for the
  December 2022 part of the window, or a statement that one configuration covered the whole run.
- The original run's wandb logs or `_stats.json` counts of "Use of image disallowed by X-Robots-Tag
  directive". The Ray example's wandb project is not public.
- Any image-host robots.txt check, or any opt-out list (Spawning or other) applied during or after
  the collection.
- Any public statement by Shankar, Beaumont, Ilharco or another author giving the version, commit or
  opt-out flags.
- Archived copies of datacomp.ai (the Wayback Machine was unreachable).
- The two hidden items in #67.

## What this bears on

This section draws no scoring conclusion and proposes no hold change. The open point on
`openclip.openness` was whether the original collection honored the one image-level opt-out its tool
could honor. The search found a January 2023 configuration, published by the collection's lead and
reported run at scale, that would have honored it by default, and a December 2022 LAION run that did
not. Neither source says it is the CommonPool collection, and the original collection may have run
different configurations across phases or workers. What would settle the point is a production
artifact that links CommonPool output to a configuration: a run identifier, output path, original
download manifest or contemporaneous log tying a CommonPool shard or sample to the January Ray
configuration (or to another), the original run's per-shard statistics, or a statement from the
DataComp maintainers. Nothing in this brief asks them for it.

## Sources

Map files are on `main` at `632c0612`: `docs/briefs/2026-11-14-datacomp-download-provenance.md` and
`sources/verification_queue.yaml` (`openclip.openness`).

Everything below was read 2026-11-15. GitHub primary text was read from local clones at the commits
named. `raw.githubusercontent.com` returned 404 to `fetch_source` for every URL tried today,
including one that returned 200 on 2026-11-14 (the initial `environment.yml`, S3 in the earlier
brief), so GitHub files carry commit hashes and no digest. Anyone can re-read them with
`git clone` and `git show <commit>:<path>`. W&B data came from anonymous POST queries to
`https://api.wandb.ai/graphql`, which `fetch_source` cannot repeat, so those rows have no digest.
GitHub issue and PR pages were read through the summarizing fetcher (403 to `fetch_source`). Treat
their quotes as leads to re-read.

| # | Source | Status | content_sha256 | What it gave |
|---|---|---|---|---|
| A1 | `git clone https://github.com/mlfoundations/datacomp`, all `refs/heads` and `refs/pull/*/head` | clone | n/a | 100 commits, earliest 2023-04-27; PR #29 commit `983250e357b9db1787eba8e6e66ccc84d658c409`; PR #58 commit `482628b79a15e6f3506f4c60232a791765540d6f` |
| A2 | `git clone https://github.com/rom1504/img2dataset`, all `refs/heads` and `refs/pull/*/head` | clone | n/a | PR #272 original commit `6183e5ae257adf89857967298e30141817620dc1` (`examples/ray_example/ray_example.py`, `cluster_minimal.yaml`, `readme.md`); `abd4b02b8a93cc47a577401e8fd31fd3d21a5779`; merge `171e3cd6482bb160b0366bfa2d80239fcbc5cd89`; Beaumont's edits `39098c9`, `7632938`; `main.py` at tags 1.39.0 and 1.40.0 (config capture after defaulting); #306 `21c297b089cf7bc30480825af83bf1859862f70d` |
| A3 | `git clone https://github.com/vaishaal/img2dataset` | clone | n/a | `7aadba42f8008106bd38475e06e78e79dfe4bbeb` on branch `ray`, `1.41.0-11-g7aadba4`; `setup.py` `version="1.41.0"`; `main.py` lines 106-113 |
| A4 | `git clone https://github.com/rom1504/cc2dataset` | clone | n/a | Release 1.4.0 `273dbc96fcd02155c4c788260a69506519db3a22`: `uid` md5 of `alt` + `url`, output columns `uid`, `url`, `alt`; README thanks to Vaishaal |
| A5 | `git clone` of `gabrielilharco/img2dataset` and `GeorgiosSmyrnis/img2dataset`; `git ls-remote` of `sagadre/img2dataset` | clone | n/a | Branch lists; `datacomp` branch is #328; `write_check` `8a11b1d4b611873b6fb0e2523b43f28c7b331a2d` leaves the opt-out code alone |
| W1 | W&B GraphQL, project `rom1504/img2dataset`, all runs (name, createdAt, state, config, summaryMetrics) | 200 | none (POST) | 562 runs; window counts; runs `ylj2nunh` and `3nxu4hnn` with configs and totals |
| W2 | W&B GraphQL, runs `3nxu4hnn` and `ylj2nunh` (`runInfo`) | 200 | none (POST) | Command lines, AWS kernel, heartbeat to 2022-12-15 20:23 |
| W3 | W&B GraphQL, `img2dataset` under 10 other entities, `datacomp` under 2 | 200 | none (POST) | `project: null` for each |
| H1 | https://huggingface.co/api/datasets/mlfoundations/datacomp_pools | 200 | `7ed132ade0c5e561429f3f71121b32bc9ab8558a4ea1b18d946e83cf1518251e` | Repository record, created 2023-02-01 |
| H2 | https://huggingface.co/api/datasets/mlfoundations/datacomp_pools/tree/80c9c207?recursive=false | 200 | `8654b6c038f7e8fd22bfbd74e2c787847f3258c7a0415d09e82a6b81a0a854b0` | Top level on 2023-03-22: five shard folders and `.gitattributes` |
| H3 | Hugging Face tree and commit APIs for the six `mlfoundations/datacomp_*` repositories, paginated | 200 | none (paginated) | File-type counts; 6,494 `datacomp_pools` commits by title; recursive trees at `203ab3f4` and `80c9c207` |
| D1 | https://www.datacomp.ai/dcclip/getting_started.html | 200 | `36091b53944db75f41038c562bab77327741929b5d9cf02f7be394a1d720df09` | Participant download instructions only; other site pages read without digest |
| D2 | https://web.archive.org/cdx/search/cdx?url=datacomp.ai | connection reset (5 tries) | none | Not read |
| N1 | https://hn.algolia.com/api/v1/items/35681085 | 200 | `90d0bcbd527802e1319fac704b552f5e23074a77ce5e56916220052464c4e35b` | Hacker News thread on #293; no DataComp author on DataComp's collection |
| G1 | https://github.com/mlfoundations/datacomp/issues/67 | 403 to `fetch_source`; summarizing fetcher | none | Section 4 quotes |
| G2 | https://github.com/rom1504/img2dataset/pull/272 | 403 to `fetch_source`; summarizing fetcher | none | Opened 2023-01-17 by Vaishaal, merged 2023-08-20 by rom1504; description quotes |
| G3 | https://github.com/mlfoundations/datacomp/pull/29, /issues/59, /issues/68 | 403 to `fetch_source`; summarizing fetcher | none | No maintainer statement on the original download |
| G4 | https://github.com/rom1504/img2dataset/issues/293, /issues/455; issue searches in both repositories | 403 to `fetch_source`; summarizing fetcher | none | Result lists; no statement of the original settings |
