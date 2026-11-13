# Web-crawl corpora and full data openness, 2026-11-13

This brief prepares the follow-up ruling that review of #1049 asked for: when a pretrained model's
corpus is a web crawl released under an open compilation license, does it count as openly
reusable for `data: open`? It inventories the products the answer touches, sets out what each
crawl release says about its own terms, and proposes a test for the maintainer to rule on. It
changes no score, value, recipe or rubric. Like the other records in `docs/briefs/`, it describes
the state on the date above and gets refreshed by a new brief, not edited.

Map-side claims cite files in `sources/` on `main` at `1a75d914`. The policy it builds on is on
the #1049 branch, `cc/openness-corpus-license-policy` at `1c90a7ad`, which is not merged. Outside
claims cite the sources listed under [Sources](#sources), all fetched today.

## The short answer

Seven products hold 5/open_source with `data: open` on a corpus that is wholly or mostly web
crawl: `olmo`, `t5`, `smollm`, `marin`, `apertus` and `luciole` in `base_pretrained`, and
`openclip` in `embeddings_retrieval`. None of their records says anything about the rights in the
crawled pages. Each one reads the compilation license (ODC-BY or CC-BY-4.0) or, for `apertus`, the
existence of reconstruction scripts.

The crawl releases themselves are more careful than the records. Nearly every one fetched today
grants an open license over the compilation and, in the same paragraph or through the Common Crawl
terms it binds the reuser to, says the pages keep their own rights. DCLM-Baseline and CulturaX are
the exceptions: their cards say nothing about page rights. The releases differ on everything after
that: opt-out handling, PII treatment and a route for having content removed range from detailed
(FineWeb-2, Luciole, Apertus, HPLT) to absent (C4, DCLM-Baseline).

The recommended rule is option C below. A web-crawl corpus keeps `data: open` when its terms
permit open reuse and the release documents where the pages came from, that they keep their
authors' rights, and how publisher opt-outs were honored. Under that rule no score moves today.
Six records need their `data` evidence extended to show it, and `openclip` needs a primary read
that the sources fetched for this brief did not supply.

## Why R-2026-11-13-b leaves this open

R-2026-11-13-b (`docs/rulings/log.yaml` on the #1049 branch) makes full `data: open` require "a
released or reproducible corpus with terms permitting open reuse, not merely download
availability". It names two cases. A corpus that is non-commercial as a whole is
`released-restricted`. A declared openly licensed compilation whose constituents keep mixed terms
stays `open` after disclosure and a materiality assessment that weighs "the legal restriction,
whether the affected data can be identified and excluded, and coverage".

A web crawl fits neither case cleanly. Its compilation license is open, so it is not the
non-commercial case. And its constituents are not a handful of named subsets with stated licenses:
they are billions of pages, most of them under their authors' copyright and few with any license
stated. Read literally, the materiality test would sink every crawl: the unlicensed share is most of
the corpus, and no reuser can identify and exclude it. The #1049 survey assumed the opposite ("The survey
assumes it does, and so did the #1046 audit. The ruling does not say") and listed this as its
second open question.

The reviewer of #1049 answered it without ruling, in review notes passed to the session that prepared this brief rather than in a comment on the PR: "For C4 and FineWeb, I'd retain their existing
treatment provisionally. Open compilation terms should not automatically establish that every
crawled webpage permits redistribution or commercial reuse, but neither should ordinary unresolved
web copyright force a blanket downgrade of every web-trained model. The relevant test is whether
the release offers a credible, documented basis for lawful reuse and discloses material
limitations. This is best recorded as a specific follow-up ruling rather than broadening #1049."

## Inventory

### Products in scope

The pretrained openness ladder (`sources/rubrics/pretrained.yaml`) is extended by three
categories: `base_pretrained`, `embeddings_retrieval` and `scientific_ai_models`. Twenty-nine of
their products record `data: open`. Seven of them train on a corpus that is wholly or mostly web
crawl. All seven sit at 5/open_source, which is the only rung that needs `data: open`, so the
answer to this question can move each of them.

| Product | Corpus | Web share, from the source | What the record says about the crawl's terms |
|---|---|---|---|
| `olmo` | Dolma 3 | The pool card lists Common Crawl at 8.14T of 9.31T tokens [S9]. The 6T mix card: "The majority of this dataset comes from Common Crawl" [S8] | Dolma tagged `license:odc-by`, and the mix card quoted for "licensed under ... (ODC-By)". Nothing on page rights |
| `t5` | C4 | Wholly Common Crawl [S1] | `allenai/c4` tagged `license:odc-by`, plus the T5 README's Beam build from Common Crawl. Nothing on page rights or the Common Crawl terms |
| `smollm` | SmolLM3 mixture, about 11T tokens | Stage 1: "Web: 85% (12% multilingual) - FineWeb-Edu, DCLM, FineWeb2 and FineWeb2-HQ" [S20] | "public data mixtures"; the collection lists `dclm-baseline-1.0` among others [S21]. No license read |
| `marin` | DCLM-Baseline, OLMo 2 mix, Dolmino and others | The OLMo 2 mix card puts DCLM-Baseline at 3.70T of its 3.90T tokens [S11] | "documented mixtures"; the card's dataset list. No license read |
| `apertus` | Reconstructed by `swiss-ai/pretrain-data` | The pipeline rebuilds FineWeb-HQ, FineWeb2-HQ, FineWeb-Edu, DCLM-Edu and FineMath [S16] | The scripts' existence and Apache-2.0 license. Nothing on the corpus's terms |
| `luciole` | Luciole-Training-Dataset | Not quantified. The card lists FineWeb2, FineWeb-Edu, FineWeb-HQ, DCLM, CulturaX, HPLT 2, FineMath and MegaMath Web among its sources [S18] | CC-BY-SA-4.0 for the compilation, the non-commercial Claire subset and unlicensed small subsets. Nothing on the crawled portion |
| `openclip` | DataComp-1B (and LAION-2B) | Wholly Common Crawl: "a new candidate pool of 12.8 billion image-text pairs from Common Crawl" [S25] | DataComp-1B "published ungated under CC-BY-4.0". Nothing on the images' rights |

`luciole` was ruled provisionally `open` under R-2026-11-13-b on its mixed constituents. That ruling
did not address its web portion, so it is in scope here too.

### Products left out, and why

- **`lucie-7b`** has a web-heavy corpus, but #1049 moves it to `released-restricted` because the
  corpus is CC-BY-NC-SA-4.0 as a whole. Its web portion cannot change that.
- **`pythia`** trains on the Pile, which has a web component (Pile-CC) but is a mixed compilation
  with no compilation license (`sources/scores/the-pile.yaml`: `mixed-per-subset`). The #1049
  survey treats it as a constituent-materiality case, with Books3 the material question.
- **`comma`** trains on the Common Pile, which selects documents by their own open license rather
  than placing an open license over crawled pages. It stays 5 under every option below and is the
  useful contrast: it is what a crawl-free answer looks like.
- **`colbert`, `ms-marco-cross-encoder`, `all-minilm`, `nomic-embed` and `modernvbert`** train on
  curated pair or passage sets, not general crawls. MS MARCO's passages come from web pages, but
  its terms are the binding question: "intended for non-commercial research purposes only ... and
  is made available free of charge without extending any license" [S22]. That is the
  non-commercial case #1049 already covers, and its survey lists the MS MARCO pair for a follow-up.
- **`bge` and `colpali`** record `data: open`, but a use-bounded weights license caps both at 3,
  whatever their corpora's terms.
- **`eurollm`** released its EuroWeb subset but records `documented-not-released`, so a
  `data: open` rule does not reach it.

### The dataset ladder already reads these corpora as open

The same corpora are products in their own right, scored on `sources/rubrics/dataset.yaml`. That
ladder lists `ODC-BY`, `CC-BY-4.0`, `cc0-1.0` and `CommonCrawl-ToU` among its `open_data`
examples. On it, `c4`, `fineweb`, `fineweb-2`, `fineweb-edu`, `dclm-baseline`, `dolma`, `dolma-3`,
`refinedweb`, `madlad-400` and `redpajama-data-v2` all score 5/open on their compilation license.
Whatever the follow-up ruling decides for a model's `data` dimension, it either applies to these
records too or says why a corpus can be open as a dataset and not open as a model's training data.

## What the crawl releases say

Read from each release's own card or terms today. "Via Common Crawl terms" means the card binds
the reuser to the Common Crawl Terms of Use and does not restate the point itself.

| Release | Compilation license | Underlying page rights | Opt-out | PII | Removal route | Use statements |
|---|---|---|---|---|---|---|
| C4 (`allenai/c4`) [S1] | ODC-BY | Via Common Crawl terms: "you are also bound by the Common Crawl terms of use in respect of the content contained in the dataset" | Not on the card | Not on the card | Not on the card | None |
| FineWeb [S4, S24], FineWeb-Edu [S5] | ODC-By 1.0 | Via Common Crawl terms: "also subject to CommonCrawl's Terms of Use" | Not on the FineWeb card | Emails and public IP addresses anonymized | PII removal form; v1.3.0 "removed specific domains in response to a C&D notice" | None |
| FineWeb-2 [S6] | ODC-By 1.0 | Via Common Crawl terms | "CommonCrawl respects robots.txt at crawl time", and webmasters may use the removal form | Emails and IPs anonymized | "PII removal/opt out form" | None |
| DCLM-Baseline [S7, S26] | CC-BY-4.0 | Not stated. The source is "the raw Common Crawl data (DCLM-Pool)" | Not on the card | "[More Information Needed]" | Not on the card | "the dataset is intended for research use only", in its intended-uses section |
| Dolma 3 [S8, S9] | ODC-By | Not on the Dolma 3 cards. The original Dolma card says users are "bound any license agreements and terms of use of the original data sources" [S10] | Not on the cards | Original Dolma card: a PII removal form [S10] | Same form | "intended for research and educational use", with Ai2's Responsible Use Guidelines |
| OLMo 2 mix (`olmo-mix-1124`) [S11] | ODC-By 1.0 for the "collection" | Via Common Crawl terms | Not on the card | Not on the card | Not on the card | None |
| RefinedWeb [S12] | ODC-By 1.0 | Via Common Crawl terms: "users should also abide to the CommonCrawl ToU" | "Their crawler honors opt-out requests in the robots.txt" | Warns PII may remain | Not on the card | None |
| CulturaX [S13, S14] | "strictly follows those of mC4 and OSCAR" | Not stated | Not stated | Warns PII may remain | Not stated | Gated: the user confirms "downloading CulturaX is legal in the country/region where I am located", agrees not to identify individuals and not to use it for harmful purposes |
| HPLT 2 [S15] | CC0 on "the actual packaging" | "We do not own any of the text from which these text data has been extracted" | Not on the card | Not stated on the card | Notice and takedown; affected sources removed "from the next release" | "It is your responsibility that any use of the data complies with any applicable legal framework, such as ... the EU Copyright Directive 2019/790 and the General Data Protection Regulation" |
| Apertus pipeline [S16, S17] | Rebuilds from the open-licensed releases above | Inherits the upstream cards | Retroactive: "retroactively respecting `robots.txt` exclusions"; the scripts carry `filterrobots` steps | Filters "personally identifiable content" | Not stated | None |
| Luciole-Training-Dataset [S18] | CC-BY-SA-4.0; "Each source corpus remains under its original licence" | "it is possible that individual documents in those corpora are copyrighted" | Retroactive robots.txt from the CC-MAIN-2025-26 dump; sites absent from that dump excluded | Emails, IPs and phone numbers replaced | Opt-out form for copyrighted works and personal details | None |
| DataComp-1B [S19] | CC-BY-4.0 on "the image url-text samples and metadata" | "The individual images are under their own copyrights" | Not on the card | Not on the card | Not on the card | "a research artifact, is provided as is"; use at own risk |

Three points stand behind the table.

1. **Common Crawl's terms are the shared floor** [S2]. Most cards bind the reuser to them, and
   the terms say that "your use of the Crawled Content signifies your binding acceptance". They
   grant "a limited ... license to access and use the Service", say crawled content "may be subject
   to separate terms of use or terms of service from the owners", and require users to respect the
   copyrights and other rights of third parties in the material. They contain no commercial-use or
   field-of-use bar. They do recommend "the advice of legal counsel before making any use,
   including commercial use", and the indemnity clause names training AI systems among the uses a
   user answers for. The crawler checks robots.txt before fetching and stops for
   `User-agent: CCBot` / `Disallow: /` [S3].
2. **No release claims to license the pages.** Where a release states an open license, it covers
   the selection, cleaning and packaging. HPLT, DataComp and Luciole say so in their own words; C4,
   FineWeb, RefinedWeb and the OLMo 2 mix say it by deferring to Common Crawl's terms. DCLM-Baseline
   and CulturaX do not address it. None asserts a fair-use or text-and-data-mining basis for
   redistributing page text. HPLT's card is the only one that names a legal framework,
   and it places compliance on the user.
3. **Research-use statements are advisory where the license is open.** DCLM-Baseline, Dolma 3 and
   DataComp describe themselves as research artifacts or "intended for research" use, but their
   license grants carry no such limit. MS MARCO is the contrast: there the non-commercial line is
   the terms themselves.

On the legal background, Article 4 of Directive 2019/790 requires member states to provide an
exception for "reproductions and extractions of lawfully accessible works ... for the purposes of
text and data mining", on condition that use "has not been expressly reserved by their rightholders
in an appropriate manner, such as machine-readable means in the case of content made publicly
available online" [S23].
Copies made under it "may be retained for as long as is necessary for the purposes of text and data
mining". That is why opt-out handling is the part of a crawl release that bears most directly on a
lawful-reuse basis. It also shows the limit: the exception covers mining, not general
redistribution of the text. The map does not decide whether any release is lawful. It can record
whether the release documents a basis and discloses its limits.

## Options for a ruling

### A. Open compilation terms suffice, with a general disclosure duty

A web crawl under an open compilation license counts as `open` once the record notes in prose that
the pages keep their own rights. There is no checklist. Each record is judged on whether the
release looks credible.

- **Inventory:** all seven stay 5. Each record adds a sentence and a source.
- **For:** smallest change, consistent with the dataset ladder as it stands.
- **Against:** close to the reading the reviewer rejected ("Open compilation terms should not
  automatically establish ..."). With no named elements, two editors can reach different answers on
  the same corpus, and the record cannot show why one crawl passed and another would not.

### B. A web crawl is always `released-restricted`

Unlicensed page content is a restriction on reuse, so a corpus that is mostly crawled pages cannot
be `open`, whatever its compilation license.

- **Inventory:** all seven move 5 → 4/open_weights through the `{data: released-restricted, code:
  open}` rung #1049 adds. With `lucie-7b` already moving, `base_pretrained` would keep only `comma`
  at 5, plus `pythia` until its own assessment.
- **For:** simple, and it never overstates reuse rights.
- **Against:** the "blanket downgrade of every web-trained model" the reviewer ruled out. It treats
  the most carefully documented releases (Luciole, Apertus, FineWeb-2) the same as an undocumented
  crawl, so it gives publishers no reason to document. It contradicts the dataset ladder, which
  scores the same corpora 5/open, unless that ladder changes too.

### C. A named documentation test (recommended)

A web-crawl corpus is `open` when its record shows the release meets a short list of documented
conditions. The ruling names them, so a record either cites each one or does not.

- **Inventory:** no score moves. Six records pass on sources fetched today and need their `data`
  evidence extended. Three of them (`olmo`, `t5`, `marin`) pass only if a release may rely on its
  named crawl's documentation (decision 2). `openclip` does not yet pass on the evidence read: DataComp-1B's card and paper
  establish the license, the crawl source and the image rights, but not opt-out handling.
- **For:** follows the reviewer's direction ("a credible, documented basis for lawful reuse and
  discloses material limitations") in a form an editor can apply and a reviewer can check. It
  separates binding terms from advisory statements, as #1049 does. It rewards releases that
  document.
- **Against:** it reads documentation, not legality. A crawl can meet every element and still
  carry legal risk in some jurisdictions, and the record should not imply otherwise.

## Recommended test

A corpus that is wholly or mostly web crawl earns `data: open` when the release, or the named crawl
whose terms the release binds the reuser to, documents all four of the following. The record cites
a source for each.

1. **Open terms.** The compilation, or the output of the published reconstruction scripts, is
   licensed for redistribution and commercial use. No binding term on the corpus or its crawl
   source bars commercial use or a field of use. Conduct terms (comply with the law, respect
   third-party rights, do not identify individuals) and advisory intended-use statements do not
   fail this element, but the record quotes them.
2. **Named provenance.** The release names the crawl it came from (Common Crawl snapshots, the
   Internet Archive, its own crawler) and publishes the processing, so a rights holder can tell
   whether a page is in it.
3. **Disclosed page rights.** The release states that the underlying pages keep their own rights or
   terms, in its own words or by binding the reuser to crawl terms that say so.
4. **Opt-out handling.** The release documents how publisher opt-outs were honored: robots.txt at
   crawl time, documented by the crawler it names, or retroactive filtering.

A fifth element is recorded but not required: **a removal route** for rights holders or data
subjects (a takedown process, an opt-out or PII form). It supports `high` confidence on the `data`
dimension and its absence lowers it, but it does not change the value.

How the outcomes map:

- All four elements documented → `open`.
- A binding term fails element 1 → `released-restricted`, as #1049 already provides.
- Element 1 holds but one of elements 2 to 4 is not documented in what was read → hold the
  dimension in `sources/verification_queue.yaml` with the missing element named. If research
  finds the release supplies no basis, the value becomes `released-restricted`. A documentation
  gap is an evidence question first, not a finding that the terms bar reuse.

Applied to the inventory on today's sources:

| Product | 1. Terms | 2. Provenance | 3. Page rights | 4. Opt-out | Removal route | Result |
|---|---|---|---|---|---|---|
| `olmo` | ODC-BY; research-use statement advisory | Common Crawl | Original Dolma card; Common Crawl terms | CCBot robots.txt | Dolma PII form | `open` |
| `t5` | ODC-BY | Common Crawl | C4 card binds Common Crawl terms | CCBot robots.txt | None found | `open`, confidence not `high` |
| `smollm` | ODC-BY, CC-BY-4.0 | Common Crawl | FineWeb cards bind Common Crawl terms | FineWeb-2 card; CCBot | FineWeb forms | `open` |
| `marin` | CC-BY-4.0, ODC-BY; DCLM research-use statement advisory | Common Crawl | OLMo 2 mix card binds Common Crawl terms | CCBot robots.txt | None found for DCLM | `open`, confidence not `high` |
| `apertus` | ODC-BY upstream | Named upstream releases | Upstream cards | Retroactive robots.txt | Upstream forms | `open` |
| `luciole` | CC-BY-SA-4.0 | Named sources | Card states it | Retroactive robots.txt | Opt-out form | `open` |
| `openclip` | CC-BY-4.0 on the URL-text index | Common Crawl | Card states it | Not found | None found | Hold until opt-out handling is read |

`openclip` raises one more point. DataComp-1B releases URLs and captions, not images, so a reuser
fetches the images from the live web. Whether a URL index counts as a released corpus at all, or as
a listing closer to `components-listed`, is a question for the same ruling.

The dataset ladder's `open_data` tier would apply the same four elements to the same corpora. On
today's sources, C4, FineWeb, FineWeb-2, FineWeb-Edu, DCLM-Baseline, Dolma, Dolma 3 and RefinedWeb
all meet them through their cards plus the Common Crawl terms and crawler documentation. HPLT 2
meets elements 1 to 3 and states no opt-out handling on its card.

## Decisions requested

1. **Choose the rule:** A, B or C. The recommendation is C with the four required elements above.
2. **Inherited documentation.** Under C, may elements 3 and 4 be met through the published terms
   and crawler documentation of the crawl a release names (the Common Crawl terms and CCBot
   documentation), or must the release state them itself? The recommendation is to accept the
   named crawl's documentation. Without that, the C4, DCLM-Baseline and Dolma 3 cards fail element
   4 (and DCLM-Baseline element 3 as well), so `t5`, `marin` and `olmo` would be held.
3. **The removal route.** Recorded and tied to confidence, as recommended, or required?
4. **A documentation gap.** Hold first and downgrade only after research, as recommended, or record
   `released-restricted` immediately? If the latter, the `released-restricted` definition in
   `docs/reference/openness.md` needs to cover "no documented basis for open reuse" as well as
   "terms bar open reuse".
5. **Advisory research-use statements.** Confirm that "intended for research use" language outside
   the license grant (DCLM-Baseline, Dolma 3, DataComp) does not fail element 1.
6. **URL-index releases.** Whether DataComp-1B's URL-and-caption release counts as a released
   corpus for `openclip`.
7. **The dataset ladder.** Apply the same test to the `open_data` tier in
   `sources/rubrics/dataset.yaml`, or scope the ruling to the pretrained ladder and say why.
8. **Order of work once ruled:** record the ruling and the evidence lines in
   `sources/rubrics/pretrained.yaml` and `docs/reference/openness.md` after #1049 merges, then
   extend the seven records' `data` evidence in one refresh PR, with `openclip` first because it
   is the one that may need a hold.

Nothing in this brief moves a score. Each record change lands in its own PR with its evidence.

## Sources

Map files are on `main` at `1a75d914`: `sources/rubrics/pretrained.yaml`,
`sources/rubrics/dataset.yaml`, `sources/categories/base_pretrained.yaml`,
`sources/categories/embeddings_retrieval.yaml`, `sources/categories/scientific_ai_models.yaml`,
and the score files `sources/scores/{olmo,t5,smollm,marin,apertus,luciole,openclip,comma,pythia,lucie-7b,the-pile,c4,fineweb,fineweb-2,fineweb-edu,dclm-baseline,dolma,dolma-3,refinedweb,madlad-400,redpajama-data-v2}.yaml`.
The policy text is on `cc/openness-corpus-license-policy` at `1c90a7ad` (#1049):
`docs/rulings/log.yaml` (R-2026-11-13-b), `sources/rubrics/pretrained.yaml` and
`docs/reference/openness.md`, "A released corpus is open only if its own terms permit open
reuse".

All outside sources were fetched 2026-11-13 with `uv run python -m build.fetch_source`. Digests are
of the bodies the quotes were read from.

| # | URL | Status | content_sha256 | What it gave |
|---|---|---|---|---|
| S1 | https://huggingface.co/datasets/allenai/c4/raw/main/README.md | 200 | `bfa4b9d8af6f9d2955d39b7cb617d580763aad7fb9024e425be60738b69ea140` | "A colossal, cleaned version of Common Crawl's web crawl corpus"; ODC-BY; "you are also bound by the Common Crawl terms of use in respect of the content contained in the dataset" |
| S2 | https://commoncrawl.org/terms-of-use | 200 | `2ffa806b46ea97481beac2d16b556603fb122d6763850a2fbe575a4177191072` | Last updated March 7, 2024. Limited license to the Service; crawled content "may be subject to separate terms"; "you agree to respect the copyrights"; counsel "before making any use, including commercial use"; indemnity naming AI training |
| S3 | https://commoncrawl.org/faq | 200 | `6cb85bf9331e700a551fadd5ef373376c36141e263d6403c8f379fa30f068ffa` | CCBot checks robots.txt before fetching; `User-agent: CCBot` / `Disallow: /` stops crawling; an opt-out registry |
| S4 | https://huggingface.co/datasets/HuggingFaceFW/fineweb/raw/main/README.md | 200 | `2fb3e49e8aa62a7429b07b557cc49d578292174843fb6aa561b5fbe6afbff01c` | ODC-By 1.0 and "subject to CommonCrawl's Terms of Use"; email and IP anonymization; PII removal form; v1.3.0 domains removed after a C&D notice |
| S5 | https://huggingface.co/datasets/HuggingFaceFW/fineweb-edu/raw/main/README.md | 200 | `a0cc8998a20499432b28b6575f3046b714938eb8e11b8d59a1d25ddf3716061e` | ODC-By 1.0 and "subject to CommonCrawl's Terms of Use" |
| S6 | https://huggingface.co/datasets/HuggingFaceFW/fineweb-2/raw/main/README.md | 200 | `08d38a7e5cb7aae4b6fcc284fec4dd636ea653e4e5e74ef66a60d9616005b090` | 96 Common Crawl snapshots; ODC-By 1.0 and Common Crawl terms; "CommonCrawl respects robots.txt at crawl time"; "PII removal/opt out form" |
| S7 | https://huggingface.co/datasets/mlfoundations/dclm-baseline-1.0/raw/main/README.md | 200 | `7836ae55a3a8decc25e1d5c15900f3b40e91a4d20f4d2bf4f048d86f1db2c4ff` | CC-BY-4.0; "derived from Common Crawl"; personal information "[More Information Needed]"; "intended for research use only" |
| S8 | https://huggingface.co/datasets/allenai/dolma3_mix-6T/raw/main/README.md | 200 | `901a231cdcae33ea8ce765d1bdef7606555780c4a108b0bcf046a65fa5d5adf9` | "The majority of this dataset comes from Common Crawl"; ODC-By; "intended for research and educational use" |
| S9 | https://huggingface.co/datasets/allenai/dolma3_pool/raw/main/README.md | 200 | `7a43fb286ca2d57f6e44fbc109b7208a778d59a7f6e3c8a52ccd4f172d4e0ab1` | Common Crawl 8.14T of 9.31T pool tokens; ODC-By |
| S10 | https://huggingface.co/datasets/allenai/dolma/raw/main/README.md | 200 | `5379c6cbd2b567c0630578a27e0061346b6b89489e71039d9b2b1d176d414635` | ODC-BY; "bound any license agreements and terms of use of the original data sources"; PII removal form |
| S11 | https://huggingface.co/datasets/allenai/olmo-mix-1124/raw/main/README.md | 200 | `8a0a0c243be08a014bb85062f1117c4fbe97d6caeb22a69545ffdf58c3a49ae5` | DCLM-Baseline 3.70T of 3.90T tokens; the "collection" is ODC-By and "subject to CommonCrawl's Terms of Use" |
| S12 | https://huggingface.co/datasets/tiiuae/falcon-refinedweb/raw/main/README.md | 200 | `9fb48c193e133dba64734ad6b432d713fcbe7440a654f8153faa33c0421fda26` | ODC-By 1.0; "users should also abide to the CommonCrawl ToU"; the crawler "honors opt-out requests in the robots.txt" |
| S13 | https://huggingface.co/datasets/uonlp/CulturaX | 200 | `ea0b22d6c15497b26022a293840aa1b1b4a7f78342186dbdb702af540fb26807` | "The licence terms for CulturaX strictly follows those of mC4 and OSCAR". The raw README returns 401 because the dataset is gated |
| S14 | https://huggingface.co/api/datasets/uonlp/CulturaX | 200 | `efa8daece1f826dd88f198c62e869f61287cc30f3dde100144ae3674bf329ff7` | `gated: auto`; the gate prompt and the jurisdiction and no-identification checkboxes |
| S15 | https://huggingface.co/datasets/HPLT/HPLT2.0_cleaned/raw/main/README.md | 200 | `8c38b823150d89ca031bee43c835bda1bfff05886a84e00353557555c6336232` | "We do not own any of the text"; CC0 on "the actual packaging"; notice and takedown; user responsible under Directive 2019/790 and the GDPR |
| S16 | https://raw.githubusercontent.com/swiss-ai/pretrain-data/main/README.md | 200 | `43a39083f999ee55f606abb45859f2e0c47542015cafb8037ed9d0a36a1ab8ee` | Pipelines for FineWeb-HQ, FineWeb2-HQ, FineWeb-Edu, DCLM-Edu and FineMath, each with `filterrobots` steps |
| S17 | https://arxiv.org/abs/2509.14233 | 200 | `708c422a40898842cec08532b4f86917f8648837d96e5a3149aca899b6168d2a` | Apertus: "retroactively respecting `robots.txt` exclusions and filtering for non-permissive, toxic, and personally identifiable content" |
| S18 | https://huggingface.co/datasets/OpenLLM-France/Luciole-Training-Dataset/raw/main/README.md | 200 | `10eac1a67b32a8f83a488ca56f71a5e8df8ebd2ceadbf1017205d95a0cd69238` | Web sources listed; retroactive robots.txt from CC-MAIN-2025-26; email, IP and phone anonymization; "possible that individual documents in those corpora are copyrighted"; opt-out form |
| S19 | https://huggingface.co/datasets/mlfoundations/datacomp_1b/raw/main/README.md | 200 | `3634b8386979b95b4fd54da43eb3eb0b038d24afc0df07f3c6ba2f8d52830082` | CC-BY-4.0 on "the image url-text samples and metadata"; "The individual images are under their own copyrights"; "a research artifact" |
| S20 | https://huggingface.co/blog/smollm3 | 200 | `a40769484642661c94bf8a033e43536d00bb25017573bc0e95056c334cb39bf6` | Stage 1 "Web: 85% (12% multilingual) - FineWeb-Edu, DCLM, FineWeb2 and FineWeb2-HQ" |
| S21 | https://huggingface.co/api/collections/HuggingFaceTB/smollm3-pretraining-datasets-685a7353fdc01aecde51b1d9 | 200 | `214fe901da0f737bb030fdd22ee5224cc484d70cc5e4dbab7eaa93297b688768` | Collection items include `HuggingFaceFW/fineweb-edu`, `mlfoundations/dclm-baseline-1.0`, `epfml/FineWeb2-HQ`, `HuggingFaceFW/fineweb-2` |
| S22 | https://microsoft.github.io/msmarco/ | 200 | `ab69d6410caaa38b13c395e6d4e0d6b77bab27f2545185c5518d8597acc624c2` | "intended for non-commercial research purposes only ... without extending any license"; "we may not own the underlying rights in the documents" |
| S23 | https://www.legislation.gov.uk/eudr/2019/790/article/4 | 200 | `2b7211b844155d12e134ab3f92fb09613e19326bb91657dcf7f6696a9da9020d` | Article 4 of Directive 2019/790, as adopted: the text-and-data-mining exception, retention "as long as is necessary", and the machine-readable reservation condition |
| S24 | https://arxiv.org/abs/2406.17557 | 200 | `f3f78cf59a8df5dfd2463f82c8926a39c2790606c239d84a5191bc674b8d9232` | FineWeb: "15-trillion token dataset derived from 96 Common Crawl snapshots" |
| S25 | https://arxiv.org/abs/2304.14108 | 200 | `375b0ef60324855c424aea813daaf29cca6adad9853f9d551292b9fbf942235c` | DataComp: "a new candidate pool of 12.8 billion image-text pairs from Common Crawl" |
| S26 | https://arxiv.org/abs/2406.11794 | 200 | `5308d5f1dce96fb2ccc661e397fe3828c2ddd4b14fc0896640923bc30b398df3` | DCLM: "a standardized corpus of 240T tokens extracted from Common Crawl" |

Not available today: the EUR-Lex copy of Directive 2019/790
(`https://eur-lex.europa.eu/eli/dir/2019/790/oj/eng`) returned HTTP 403 after six attempts, so S23
uses the legislation.gov.uk copy of the text as adopted. The CulturaX raw card returned 401 because
the dataset is gated; S13 and S14 read the public page and the API record instead.
