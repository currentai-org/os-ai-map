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

## Organizations

Organizations carry aliases for the same reason and under the same rule. Two exist, both
consolidations rather than renames: `google-deepmind` into `google`, `alibaba` into
`alibaba-cloud`. `org_slug` is emitted into the payload and joined in the registry, so a rename
with no forwarding address breaks a join rather than a link.

## Related

- `docs/reference/evidence-and-freshness.md` — how a score earns `last_verified`, and the gates
- `docs/reference/openness.md` — the ladders, and the multi-SKU rule the rubric applies
- `docs/reference/product-copy.md` — the prose fields, and why a curation rationale is not a
  description
- `docs/schemas/product.schema.json` — `aliases` and `version_in_identity`
- `docs/schemas/score.schema.json` — `openness.governing_release`
