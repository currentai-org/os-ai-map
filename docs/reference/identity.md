# Identity Guide

What a product's slug is, how far to collapse it, and what happens to scores when releases
merge. Normative. When a rule here changes, change the guide first and make the code follow.

> Companion to `docs/reference/evidence-and-freshness.md`, which owns how a score earns its date, and
> `docs/reference/openness.md`, which owns the ladders. This guide owns identity: the slug,
> its aliases, and the combine rules that apply when one slug covers several releases.

## The slug is the identity

A product's slug is its filename stem, its key in every roster, its join to
`sources/scores/<slug>.yaml`, and what deep links are built on. So it has to be stable, and the
rule that makes it stable is mechanical: **a slug may leave `sources/products/` only by
appearing as an alias on the product that replaced it.** `build/validate.py` enforces both
directions — an alias may not collide with a live slug, and no two products may claim the same
one.

Aliases live on the record they describe:

```yaml
name: claude-opus
display_name: Claude Opus 4.x
type: model
aliases:
- claude-opus-4-7
- claude-opus-4-x
```

They were held in a single `sources/slug_aliases.yaml` until 2026-08-08. Two things were wrong
with that. A duplicate key kept only the last value, silently, because PyYAML does not error on
one — so a second rename of the same retired slug disappeared. And the file had accumulated four
other top-level keys that looked like alias maps and were not, three of which are now fields on
the records they actually describe.

## How far to collapse: what the vendor sells

Pitch the slug at **the level the vendor markets as the product**, not at a release.

Google sells "Gemma" and 2/3/4 are versions of it, so the slug is `gemma`. OpenAI sells GPT-4o,
GPT-4.1 and GPT-5 as distinct lines, so those stay apart. Anthropic sells Opus, Sonnet and Haiku,
so `claude-opus` covers 4.5 through 4.8.

A slug that bakes in a version goes stale the day the next release ships, and then costs an alias
forever. `build/validate.py` rejects a version or size token in a `base_pretrained` or
`finetuned_chat` slug unless the product declares why:

```yaml
version_in_identity: OpenAI markets GPT-4o as a distinct product, not a version of GPT
```

The presence of the field is the exemption and the value is the reason — the same shape a
category's `deferred` block uses. Six products carry one today. Datasets and hardware are not
checked, because there the version genuinely is the identity: `oscar-2301` is a specific crawl,
`raspberry-pi-5` is a specific board, and the next one is a different product rather than an
update.

### The 2026-07-29 collapse was a one-off

Slugs had been recorded at release level and churned with every point release. They were
collapsed to tier level before deep linking shipped, which was the only moment it was free — the
front end keyed links on display names, so nothing pointed at a product slug yet. **After links
exist, a rename costs an alias forever.** Sixty-three aliases date from that batch.

### A rename made before anything linked owes no redirect

Two renames happened while it was still free, and neither carries an alias. That is not an
oversight, and re-adding them would be a bug: **`grok` was renamed to `grok-app` and the slug has
since been reused** for a different live product, xAI's Grok 4.20 model tier. An alias would
redirect a live page onto an unrelated one. `github-copilot-github-microsoft` → `github-copilot-ide`
is the other, and its target sits beside a still-live `github-copilot`.

The rule: an alias is a promise to anyone holding an old link. Where no such link could exist,
make no promise, and leave the slug free to be reused.

## When one slug covers several releases

Collapsing releases into a tier means one score describes several things. The combine rules:

| axis | rule |
|---|---|
| adoption, capability | **max** across the tier's releases |
| openness | **the current release governs** |

Openness differs because it is a claim about what you can obtain, and what you can obtain is what
ships now. A family whose previous release was Apache-2.0 and whose current one is not is not an
open family, and taking the max would say it was.

The governing release is recorded on the score, beside the axis it governs:

```yaml
openness:
  score: 3
  class: open_weights
  governing_release: gemma-4
```

It is **declared rather than derived**, and the reason is worth keeping: 6 of the 15 products
carrying one are closed or API-only, with no artifact to date. A derivation would cover some
products and not others, and a reader could not tell which kind they were looking at.

Confirming it still points at the current release is a re-read's job, which is why it sits inside
the axis a `last_verified` covers. Held outside the score, as it was until 2026-08-08, no
freshness mechanism reached it: a vendor could ship a new release and nothing would notice.

### Most-restrictive across SKUs, and where it stops

Within the governing release, openness resolves **most-restrictive across that release's
distributed SKUs**. API-only tiers and unshipped previews are excluded, and absence of evidence
never lowers a tier — the warehouse guard is `skus_mapped = skus_reachable AND tiers_seen <= 1`,
which abstains rather than reporting a most-restrictive verdict over a subset it could not fully
read.

**Most-restrictive applies only across SKUs a user cannot substitute away from** — sizes and
quantizations of one model, where the flagship governs.

It does **not** apply across independent alternatives that fully substitute. Hermes 4 is the
case: Nous ships one recipe on four bases, two Apache-licensed and two Llama-licensed, and anyone
wanting Apache takes the Seed-OSS or Qwen build and gets it. Treating those as SKUs would have
published the family as restricted while open weights were freely available.

Measured 2026-08-08, three products have SKUs under genuinely different named licenses — `gemma`
(Gemma and Apache-2.0), `hermes` (Apache-2.0 and Llama-3), `zephyr` (Apache-2.0 and MIT). Another
four differ only because one SKU records the Hub's `other`, which `signal_routing.yaml` treats as
an abstention rather than a license.

## A declared artifact is a measurement identity

The `github`, `pypi`, `npm`, `crates`, `huggingface` and `arxiv` arrays on a product are not a
list of related links. `build/adoption_measurements.py:select_route` picks the
highest-precedence declared artifact and bands adoption from it, and `signal_routing.yaml`
routes the license and weights dimensions by artifact kind. So declaring an artifact asserts
**this thing's numbers are this product's numbers**, and getting it wrong produces a score that
is internally consistent, passes every gate, and is false.

Nothing checks this. Uniqueness, ladder replay, digest and delta checks all verify that the
recorded values reproduce the recorded score; none can verify that the artifact belongs to the
product. That makes it the one identity question a reviewer has to settle by reading, and the
three shapes below are how it has actually gone wrong.

### Homepage is evidence, not identity

`homepage` is on the artifact-kind list, but it is not a measurement identity like the others -
nothing bands adoption or routes license/weights off it. It is corroborating evidence: mainly
who owns a product, sometimes that two records are the same thing when other evidence already
points that way. The artifact id is the full canonical URL (host and path; see
`build/identity.py`'s `canonical("homepage", ...)`), not the bare domain, because one company's
domain routinely hosts several distinct products at different paths - `acme.com/widgets` and
`acme.com/gadgets` are two products, not a collision. A shared `homepage_domain` alone must never
establish equivalence between two candidates or suppress a second one from being proposed; it is
a fact to weigh alongside the rest, never a verdict by itself.

### An open satellite around a closed core

A vendor ships an open repository *for* a closed product: a recipe library, a client, a
frontend. Declaring it lets an externally-open artifact lift a closed product's openness score.

`thinking-machines-lab/tinker-cookbook` is Apache-2.0 and is the training-loop library for
Tinker, a closed managed API scored openness 1; it is recorded as `existing_product` in the
ledger with an explicit note that it must not be declared as `tinker`'s artifact.
`NVIDIA/cudnn-frontend` is Apache-2.0 and wraps a closed binary. Its stars and downloads are
likewise not the core product's adoption.

### A package whose name matches and whose project does not

Registry names collide, and the collision is usually silent — the package exists, installs, and
reports downloads for something else entirely. Five cases in twelve candidates during the
2026-08-31 passes: PyPI `miles` is version 0.1 with no summary and no project URL and is not
`radixark/miles`; `privategpt` belongs to `vietanhdev/pautobot`; `pgpt` to
`hackedbyagirl/programengineergpt`; npm `airi` is a 0.0.1 stub with no repository field. The
check is cheap and mandatory: does the package's `project_urls` or `home_page` point back at the
repository being declared?

### A real binding whose usage is not the head product's usage

Here the artifact genuinely relates to the product and still measures the wrong population. A
third-party language binding, a client SDK for a server, a platform wrapper: its downloads count
its own users, not the product's.

`abetlen/llama-cpp-python` and `software-mansion/react-native-executorch` were un-declared for
this reason in #424 and kept as ledger entries instead. The client-SDK form closed PR #425,
where five records had been re-banded off packages that were all clients — and two of the notes
being overwritten already said so, which is the warning that this shape is easy to re-introduce
while reading quickly.

### Discovery may be automated; promotion may not

Candidate association scales: a sweep can propose repo, package, model and dataset links for
thousands of artifacts. Verifying that an association is a *measurement* identity does not
scale, because it is a judgment about what a number means.

So automation over this step should optimize for surfacing evidence and contradictions — a
package whose backlink is missing, a licence that disagrees between two artifacts of one
product, a download count wildly out of step with a star count — and never for declaring the
artifact. An identity edge stays provisional until a person has read it.

### Rulings are typed by relation

The resolution ledger (`sources/resolution_ledger.yaml`) is not only about GitHub repositories,
and not only about whether a candidate is a new product. Every entry names an artifact - `repo`,
or `artifact: {kind, id}` for a Hugging Face model or dataset, a PyPI, npm or crates package, an
arXiv paper, or a homepage - and answers one typed question, its `relation`:

- **`product_equivalence`** - is this artifact a new product, or does it already belong to one?
  Verdicts: `existing_product`, `sku_of`, `excluded_boundary`, `excluded_maintenance`,
  `unresolved`. Every entry written before 2026-09 answered this question, and `relation` may be
  omitted for it - absent reads as `product_equivalence`.
- **`product_membership`** - does this artifact's measurement belong to `resolves_to`'s adoption
  number? Verdicts: `member_of`, `not_member_of`. A `resolves_to` is required.

A ruling answers only its own relation. `not_member_of` on `elasticsearch-py`'s PyPI package
says its downloads are not `elasticsearch`'s adoption - it says nothing about whether
`elasticsearch-py` is itself a new product, which is a separate question a person may still have
to rule on. The schema at `docs/schemas/resolution_ledger.schema.json` is normative for the
shape; `build/resolution.py` is the reader.

Membership is a relation between an artifact and a *product*, not a fact about the artifact
alone, so `resolves_to` is part of the ledger key for `product_membership` rulings - one PyPI
package may legitimately be `member_of` one product's measurement and `not_member_of` another's.
`product_equivalence` has no such second axis: an artifact either is a new product or belongs to
exactly one, so its key stays `(artifact, relation)`.

## Organizations

Organizations carry aliases for the same reason and under the same rule. Two exist, both
consolidations rather than renames: `google-deepmind` into `google`, `alibaba` into
`alibaba-cloud`. `org_slug` is emitted into the payload and joined in the registry, so a rename
with no forwarding address breaks a join rather than a link.

### Handles are ownership evidence, not adoption evidence

`sources/org_handles.yaml` (`registry.org_handles` when published) records which platform
accounts and domains an organization publishes under — `github`, `huggingface`, `homepage_domain`
— one row per `{org, platform, handle}`. It lives outside `sources/organizations/*.yaml`
deliberately: an organization's own file is a declaration and folds into
`declaration_version_id`, but who owns which account is evidence established independently of
that declaration, revisable without re-keying it. `build/declaration_version.py` classifies
`org_handles.yaml` as a non-declaration input for the same reason `resolution_ledger.yaml` is one
— see there for the ruling.

Seeded from what each org file already declares: the account segment of an *org-level*
`github[].url` (a repo-level URL such as `github.com/keirp/OpenWebMath` is parsed too, but
recorded with a `note` flagging the weaker provenance, since the owner segment of a repo URL is
still a real account); the domain of `homepage`, except on a known multi-tenant host
(`github.com`, `huggingface.co`, …) where a bare hostname identifies no single org; and
`handles.huggingface` only where a `homepage` is itself a `huggingface.co/<account>` URL, never
invented. A `github.com/<account>` homepage is read the same way — it is exactly the
`huggingface.co/<account>` case, one platform over.

A handle is never joined for scores: it says who owns an account, not how much that account is
used, and a download or star count still has to come from the artifact-level signal tables. One
`(platform, handle)` pair belongs to one organization; `build/validate.py` enforces that as a hard
error, folded the same way any other identity comparison is (case-insensitive, and a leading
`www.` stripped for a domain). Where two org files genuinely share an account or domain —
`openai` / `openai-internal`, `anthropic` / `anthropic-internal`, `ai2` /
`allen-institute-for-ai`, `mistral-ai` / `mistral-ai-api`, `princeton-nlp` /
`princeton-nlp-openai` — the handle is assigned to the public or canonical org, and the row's
`note` names the sibling; the sibling org file is untouched.

A handle is also the graph's only route from an artifact to an org, which is why
`build/identity_eval.py` measures `org` recall against **recoverable** truth rather than every
declared `(candidate_key, org_slug)` pair: an org with no handle can never be recovered no matter
how good the graph is, so including it would bound recall at the coverage fraction and read as a
graph defect instead of the curation gap it actually is. Precision truth is unaffected — every
emitted org edge is still judged against the full truth set. The eval prints a `handle coverage:
<orgs with a handle>/<orgs rostered> (<pct>)` line so the gap stays visible as its own number
rather than disappearing into a passing recall score.

### Model families bridge a release name to a tier-level slug

Vendors ship version-numbered releases under one product line — `grok-3`, `grok-4` — but the map
scores the tier-level slug a vendor sells (`grok`), not each release (see "How far to collapse:
what the vendor sells" above). `sources/model_families.yaml` records the bridge: a lowercase
glob `pattern` (`grok-*`, always the product slug plus `-*`) that matches a release name, the
`product` slug it resolves to, and `decided_in`, the pull request where a person ruled it. Each
family is one human ruling, not a mechanical inference — a discovery sweep can propose a match,
but a bridge is only real once it is in this file. `build/validate.py` rejects two families
naming the same `pattern` with different products, and requires `pattern` to equal
`<product>-*` exactly. `registry.model_families` is the published form; it is identity evidence,
not a scoring declaration, so it changes no product's `openness`, `adoption` or `capability` and
is excluded from `declaration_version_id`'s digest (`build/declaration_version.py`).

The initial 25 families were derived mechanically — every `type: model` product whose `aliases`
already carry a version-token variant of its own slug — and then reviewed and confirmed by a
person in #474 before merge, which is what `decided_in` records for each. A mechanical
derivation is a candidate list, not a ruling on its own; a future addition follows the same
path, proposed and then confirmed in the PR that adds it.

**Overlapping patterns: the longest match wins.** Two families can legitimately overlap —
`deepseek-*` → `deepseek` and `deepseek-coder-*` → `deepseek-coder` are both real, because
`deepseek-coder` is its own tier-level slug, not a release of `deepseek` — and a release name
like `deepseek-coder-v2-instruct` matches both patterns. When that happens, **the longest
matching pattern wins**: a consumer resolving a release name must try every pattern and keep the
one with the most characters, never the first one it happens to read. `build/validate.py` flags
this shape as a warning (not an error, since it is a legitimate case) whenever one family's
pattern is a literal prefix of another's and the two name different products.

## Related

- `docs/reference/evidence-and-freshness.md` — how a score earns `last_verified`, and the gates
- `docs/reference/openness.md` — the ladders, and the multi-SKU rule the rubric applies
- `docs/reference/product-copy.md` — the prose fields, and why a curation rationale is not a
  description
- `docs/schemas/product.schema.json` — `aliases` and `version_in_identity`
- `docs/reference/adoption.md` — the instruments a declared artifact routes to, and the
  precedence order `select_route` applies
- `sources/resolution_ledger.yaml` — where a rejected or reassigned identity is recorded, so
  the next sweep can read the decision
- `docs/schemas/score.schema.json` — `openness.governing_release`
- `sources/org_handles.yaml`, `docs/schemas/org_handles.schema.json` — which accounts and
  domains an organization publishes under
- `sources/model_families.yaml`, `docs/schemas/model_families.schema.json` — which release
  patterns bridge to which tier-level product
