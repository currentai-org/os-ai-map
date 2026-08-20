"""Compile sources/ (+ frozen long-tail) into the notebook_data.json payload.

Reproduces the exact structure the live notebook consumes:
  { descriptions, layer_order[], categories: {cid: {label, arc, layer, products[]}},
    order[], n_total, generated, version, released, long_tail }
"""
from datetime import date
from pathlib import Path
import json
import re
import tomllib
import yaml

from build.check_rubric import components_string
from build.taxonomy import arc_categories

ROOT = Path(__file__).resolve().parents[1]

PRODUCT_KEY_ORDER = ["slug", "product", "org_slug", "org", "type", "description",
                     "openness", "adoption", "capability", "overall_score", "tier",
                     "maturity", "mature",
                     "freshness", "version_note", "lineage"]

# --- Gap analysis (category-level stage + gaps) -----------------------------
# Mirrors the open / open-ish / closed verdict in docs/openness-class-map.json
# (the canonical map). Kept inline here so serialize is self-contained; if these
# diverge from the JSON, the JSON is source of truth.
_GAP_OPEN = {"open_source", "open", "open_core", "open_hardware"}
_GAP_OPENISH = {"open_weights", "source_available", "gated", "open_toolchain"}
_MATURE_MIN = 4.5          # blended adoption/capability score for a product to be "mature"
_STAGE5_MIN_MATURE = 4     # mature fully-open products needed for Stage 5 (Mature Open Ecosystem)
_CAPABLE_MIN = 4           # raw capability below which an open option is "not capable yet"
_ADOPTED_MIN = 4           # raw adoption below which an open option is "not adopted yet"
# Product-level score tiers, banded on the overall score -- the adoption/capability blend, or
# adoption alone where capability is unmeasured. Leading is 4.5+, Strong is 4.0 <= score < 4.5.
# The bands are honest about how the number was reached: they name a score over the product's
# available measured axes, not a claim about both. Where both axes are measured they are whole
# numbers 1-5, so clearing 4.5 always needs a 5 on at least one axis -- but whether the partner
# axis can be a 4 or must also be a 5 depends on the category weights (an even split clears at
# 5-and-4; a lopsided split may not). An adoption-only product reaches Leading only at adoption
# 5. Scored across all openness buckets -- the tier
# describes the product -- while `mature` gates the same 4.5 bar on the fully-open bucket,
# because only fully-open products advance a category's stage.
_LEADING_MIN = _MATURE_MIN     # 4.5
_STRONG_MIN = 4.0
_STAGE_NAMES = {0: "Void", 1: "Open Experiments", 2: "Emerging Alternatives",
                3: "Viable Alternatives", 4: "Competitive Open Ecosystem",
                5: "Mature Open Ecosystem"}
# Plain-language definitions of each stage, gap and score tier, emitted into the payload's
# top-level `descriptions` block so downstream consumers render a legend without re-deriving the
# methodology. The stage and gap sentences are the definitions, full stop: gap-analysis.md and
# methodology.md quote them VERBATIM and carry the mechanism -- thresholds, which rung fires what,
# derived vs declared -- around them rather than restating them in other words. Edit here and copy
# across; test_descriptions_match_the_reference_doc pins all four lists. The tier descriptions
# below are not quoted in either doc and are not covered by that test.
# Stage and gap text render together in the category drawer, so they divide the work rather than
# describe the same fact twice: a STAGE says where the category stands, a GAP says what it needs.
# Written in one mood they were redundant -- `resiliency` fires if and only if the stage is 4, so
# "at least one product has reached the leading tier, but the field is thin" and "products have
# reached the leading tier, but there are too few" were one sentence printed twice. The needs mood
# makes that impossible. Gap text also renders in the legend with no stage beside it, so each one
# still has to stand alone.
#
# The wording avoids the bare words "leading" and "strong" except where the tier is genuinely
# meant: both are tier names, and a category can sit on a rung with no product in either tier
# (safeguards is Stage 3 with a best fully-open score of 3.5, below the strong floor).
# The exact thresholds are the constants above and the table in docs/reference/gap-analysis.md.
_STAGE_DESC = {
    0: "The category is still nascent overall, with no category-leading products and no "
       "meaningful fully open options.",
    1: "Fully open products are absent or remain substantially limited in adoption, "
       "capability, or both.",
    2: "Fully open products are becoming credible, but remain limited in adoption or "
       "capability.",
    3: "Fully open options are proven in real use, but none leads the category.",
    4: "A small number of fully open products lead the category.",
    5: "Several fully open products lead the category, so no single project carries it.",
}

# One sentence each, in the reader's terms. These render in the site legend and the category
# drawer, so they carry no implementation detail (which rung a gap fires on, whether it is
# derived or declared) and no repo paths -- that reasoning lives in the two prose docs below.
_GAP_DESC = {
    "void": "Needs a usable fully open option at all.",
    "capability": "Needs a more capable fully open option.",
    "adoption": "Needs broader adoption of its fully open options.",
    "resiliency": "Needs more fully open products at the leading tier to be resilient.",
    "openness": "Needs its category-leading products to be fully open.",
    "disclosure": "Needs the closed alternatives to disclose their data and training recipes.",
}

# The "available measured axes" qualification is deliberate: a product with no capability
# grade is scored on adoption alone, so a tier names the score over whatever axes exist for that
# product rather than asserting a judgment on both.
_TIER_DESC = {
    "leading": "an overall score of 4.5 or higher, calculated from the product's available "
               "measured axes.",
    "strong": "an overall score of at least 4.0 but below 4.5 (4.0 ≤ score < 4.5), calculated "
              "from the product's available measured axes.",
}


def _gap_bucket(cls: str) -> str:
    if cls in _GAP_OPEN:
        return "open"
    if cls in _GAP_OPENISH:
        return "open-ish"
    return "closed"


def _maturity_score(row: dict, w: dict) -> float | None:
    # Per-category linear blend of the 1-5 axes, normalized by the weight sum so the
    # result stays on the 1-5 scale for any weights (identity when they sum to 1).
    # Maturity is anchored on adoption: a product with no adoption signal has no
    # maturity score (None) rather than a spurious zero. Capability may be legitimately
    # null for some product types (e.g. datasets), which are graded on adoption alone.
    # Rounded to 2dp so the stage thresholds compare the same value we display, and so
    # float noise (e.g. 0.3*3 + 0.7*3 = 2.9999999999999996) can't push a product across
    # a stage boundary.
    adoption = (row.get("adoption") or {}).get("level")
    if adoption is None:
        return None
    capability = (row.get("capability") or {}).get("score")
    if capability is None:
        return round(float(adoption), 2)
    wa, wc = w.get("adopt", 0.5), w.get("cap", 0.5)
    return round((wa * adoption + wc * capability) / ((wa + wc) or 1.0), 2)


def _stage_and_gaps(rows: list[dict], weights: dict, disclosure: bool = False) -> dict:
    """Assign a maturity stage (0-5) and the set of gaps for one category.

    Strict open-only: only fully-open products count toward maturity/stage;
    open-ish only serves to detect the openness gap. See docs/reference/gap-analysis.md.
    `disclosure` is a declared per-category attribute (not inferred): set it where the
    closed frontier's equivalent to these open products is structurally undisclosed.
    """
    w = weights or {"adopt": 0.5, "cap": 0.5}
    # Products with no maturity score (missing adoption) are excluded from the stage
    # computation — we can't judge what we can't measure, so they neither advance nor
    # depress the category's stage.
    enr = [(r, _gap_bucket((r.get("openness") or {}).get("class")), _maturity_score(r, w)) for r in rows]
    open_rows = [(r, s) for r, b, s in enr if b == "open" and s is not None]
    mature_open = sum(1 for _, s in open_rows if s >= _MATURE_MIN)
    best_open = max((s for _, s in open_rows), default=0.0)
    mature_anywhere = any(s >= _MATURE_MIN for _, _, s in enr if s is not None)

    if mature_open >= _STAGE5_MIN_MATURE:
        stage = 5
    elif mature_open >= 1:
        stage = 4
    elif best_open < 2 and not mature_anywhere:
        stage = 0
    elif best_open < 3:
        stage = 1
    elif best_open < 3.5:
        stage = 2
    else:
        stage = 3

    if stage == 5:
        gaps: list[str] = []
    elif stage == 0:
        gaps = ["void"]
    elif stage == 4:
        # Count, not quality: the category has proven top-tier (Leading) open options but not
        # enough of them. Deliberately fires at Stage 4 only -- defining resiliency as "no Leading
        # open product at all" would spread it over the weaker categories and rebuild the
        # near-ubiquitous chip this taxonomy replaced.
        gaps = ["resiliency"]
    else:
        # Stages 1-3: no fully-open product clears the maturity bar, so name the driver(s)
        # holding the best one back rather than the umbrella. Both fire where both apply --
        # there is no longer a one-diagnostic-per-category rule, which is what kept
        # `capability` unreachable behind `openness` and hid the edge_hardware case.
        #
        # A driver gap fires only when its axis is measured and below its cutoff. If both
        # measured axes clear their cutoffs yet the blend still misses the bar (adoption 4
        # with a null capability blends to 4.0, which is benchmark_eval_data's shape), the
        # category carries no driver gap: the stage number already says it has not reached the
        # leading-product threshold, and asserting an adoption shortfall where adoption clears
        # its cutoff would be a knowingly false label. When measurement gaps like this become
        # common enough to name, introduce a gap for them deliberately.
        best = max(open_rows, key=lambda rs: rs[1])[0] if open_rows else None
        cap = ((best or {}).get("capability") or {}).get("score")
        adopt = ((best or {}).get("adoption") or {}).get("level")
        gaps = []
        if cap is not None and cap < _CAPABLE_MIN:
            gaps.append("capability")
        if adopt is not None and adopt < _ADOPTED_MIN:
            gaps.append("adoption")
        if mature_anywhere:                  # capable mature options exist, but none fully open
            gaps.append("openness")

    # Disclosure flag (orthogonal, any stage): a declared category attribute, set where
    # the closed frontier's equivalent to these open products is structurally undisclosed
    # (its proprietary data and recipe). Declared rather than inferred so it can't silently
    # toggle on a curation change, and so training data (declared) and benchmark data (not
    # declared -- open benchmarks are the shared public standard) are treated deliberately.
    # See docs/reference/gap-analysis.md.
    if disclosure:
        gaps.append("disclosure")

    return {"num": stage, "name": _STAGE_NAMES[stage], "gaps": gaps}


def _catalog_ids(prods: dict) -> dict:
    """Artifact ids now claimed by a categorized product, keyed by long-tail entry
    type, so the frozen 'uncategorized' sample can self-heal as products are added."""
    ids = {"repo": set(), "package": set(), "dataset": set(), "model": set()}
    for p in prods.values():
        for u in p.get("github", []):
            m = re.search(r"github\.com/([^/]+/[^/]+?)(?:\.git)?/?$", u["url"])
            if m:
                ids["repo"].add(m.group(1).lower())
        for key in ("pypi", "npm"):
            for u in p.get(key, []):
                m = re.search(r"/([^/]+?)/?$", u["url"])
                if m:
                    ids["package"].add(m.group(1).lower())
        for u in p.get("huggingface_dataset", []):
            m = re.search(r"huggingface\.co/datasets/([^/]+/[^/]+?)/?$", u["url"])
            if m:
                ids["dataset"].add(m.group(1).lower())
        for u in p.get("huggingface_model", []):
            m = re.search(r"huggingface\.co/([^/]+/[^/]+?)/?$", u["url"])
            if m:
                ids["model"].add(m.group(1).lower())
    return ids


def _filter_long_tail(frozen: dict, prods: dict) -> dict:
    """Drop frozen 'top' sample rows that are now categorized products. The frozen
    counts stay as the point-in-time warehouse snapshot (synced by hand after a
    batch); only the visible sample is derived so it never lists a scored product.

    `prods` must be the PUBLISHED products, not every product file. A product in a
    preliminary category is absent from the payload's categories, so dropping its row from
    the long-tail sample too would delete it from the map in both directions: not scored
    above, and no longer listed below. Its caller passes the published subset.
    """
    ids = _catalog_ids(prods)
    lt = dict(frozen)
    lt["top"] = [t for t in frozen.get("top", [])
                 if t.get("name", "").lower() not in ids.get(t.get("type"), set())]
    return lt


def _row(slug: str, prod: dict, org_slug: str, org_name: str, score: dict,
         weights: dict | None, name_map: dict | None = None,
         freshness: dict | None = None) -> dict:
    # Pre-compute the open / open-ish / closed bucket alongside the raw class, so
    # consumers get a stable 3-way verdict that survives changes to the openness.class
    # vocabulary. Same collapse the category gap logic uses (_gap_bucket).
    # The payload's `components` stays a flat string whatever shape the record carries, and
    # `raw` never ships. The front end's contract with this payload is undocumented and
    # untested, and build/render.py plus the rendered notebook both do `row('Components',
    # o.components)` on it — so a mapping here would render as [object Object] in the product
    # detail panel and force a regeneration of a bot-owned file. Keeping the key a string
    # means the structured-dimensions migration is invisible downstream, which is also what
    # makes "zero published scores moved" a byte comparison rather than a judgment.
    block = score["openness"] or {}
    openness = {**block, "bucket": _gap_bucket(block.get("class"))}
    openness.pop("raw", None)
    if block.get("components"):
        openness["components"] = components_string(block)
    row = {
        "slug": slug,
        "product": prod["display_name"],
        "org_slug": org_slug,
        "org": org_name,
        "type": prod["type"],
        "description": prod.get("description", ""),
        "openness": openness,
        "adoption": score["adoption"],
        "capability": score["capability"],
    }
    # The weighted product maturity score (per-category blend of adoption/capability),
    # already rounded to 2dp by _maturity_score, or null when adoption is missing. The
    # category stage thresholds in _stage_and_gaps compare this same 2dp value.
    m = _maturity_score(row, weights or {"adopt": 0.5, "cap": 0.5})
    # `overall_score` is the new name for this number and `maturity` the old one. Both ship for
    # one release so the front end and the warehouse can move over before the old key goes away:
    # a routine data sync must not be able to break the map halfway through. Same value, and the
    # rename is the point -- the number blends capability and adoption, which "maturity" implies
    # age for, and it is not the category-level Maturity Stage that shares the old word.
    row["overall_score"] = m
    row["maturity"] = m
    # Leading / Strong / null, derived from the score alone (see _LEADING_MIN). Emitted rather
    # than left to each consumer so the two tier boundaries stay methodology constants.
    row["tier"] = (None if m is None else
                   "leading" if m >= _LEADING_MIN else
                   "strong" if m >= _STRONG_MIN else None)
    # Canonical `mature` flag: the SAME rule the category stage engine uses
    # (_stage_and_gaps) — a fully-open product whose blended maturity clears
    # _MATURE_MIN. Emitted here so downstream consumers stop recomputing it with a
    # looser threshold. Uses the unrounded score `m` to match the stage logic.
    row["mature"] = (
        m is not None and m >= _MATURE_MIN and openness["bucket"] == "open"
    )
    # Bridge: the source field is now `comments` (a string), but the payload key
    # the notebook consumes is still `version_note`. Same value, renamed at rest.
    if prod.get("comments"):
        row["version_note"] = prod["comments"]
    # Lineage is a display-only provenance block (derived_from / curated_with /
    # trains). It feeds no score. On-map references are resolved to display names
    # via name_map; anything not on the map (curation tools, external corpora like
    # Common Crawl) passes through verbatim. Empty edges are dropped; the whole key
    # is omitted when a product has no lineage.
    lineage = prod.get("lineage")
    if lineage:
        nm = name_map or {}
        resolved = {}
        for edge in ("derived_from", "curated_with", "trains"):
            refs = lineage.get(edge) or []
            if refs:
                resolved[edge] = [nm.get(r, r) for r in refs]
        if resolved:
            row["lineage"] = resolved
    # Optional so the unit tests can call build_payload with no repo context. Task 5
    # computes it in __main__ and threads it through.
    if freshness:
        row["freshness"] = freshness
    return {k: row[k] for k in PRODUCT_KEY_ORDER if k in row}


def _organizations(orgs: dict, product_org: dict, published: set[str]) -> dict:
    """The organization roster, emitted for the app's /map/org/<slug> pages.

    Sourced from sources/organizations/*.yaml rather than build/registry/organizations.csv:
    the registry is gitignored, so it never reaches a consumer, and its github column is a
    stringified Python repr. Here github is a list of {url: ...} mappings, flattened to URLs.

    Everything is sorted. A curator reordering a YAML roster must not produce a payload diff,
    because a payload diff is a daily bot PR in the app repo.

    `published` is the set of product slugs the payload's categories carry, and this index is
    built from it rather than from every org file. Two things follow, and both were leaks found
    in review of the compilers/storage promotion: a roster never lists a product the categories
    do not, and an organization all of whose products sit in preliminary categories does not
    appear at all. Otherwise marking a category preliminary hid its products from /map while
    leaving them addressable at /map/org/<slug>, and shipped orgs - openxla, mlc-ai - that
    exist on the map nowhere else.
    """
    by_org: dict[str, list[str]] = {}
    for prod_slug, org_slug in product_org.items():
        if prod_slug in published:
            by_org.setdefault(org_slug, []).append(prod_slug)
    return {
        slug: {
            "slug": slug,
            "display_name": orgs[slug].get("display_name", ""),
            "type": orgs[slug].get("type", "unknown"),
            "homepage": orgs[slug].get("homepage", ""),
            "github": sorted(e["url"] for e in (orgs[slug].get("github") or [])
                             if isinstance(e, dict) and e.get("url")),
            "country": orgs[slug].get("country", ""),
            "products": sorted(by_org[slug]),
        }
        for slug in sorted(by_org)
    }


def _aliases(prods: dict, orgs: dict, published: set[str], org_slugs: set[str]) -> dict:
    """Retired slug -> live slug, for the app's redirects.

    Gathered from the records rather than from one mapping, which is where these lived
    until 2026-08-08. The mapping had a silent failure mode - PyYAML keeps only the last
    of two duplicate keys - and it held four other top-level keys that looked like alias
    maps and were not. Two of those are now fields on the records they describe
    (`version_in_identity` on the product, `governing_release` on the openness score);
    the third, `renamed_before_links`, is gone, and its absence is the point.

    A rename made before anything linked to the slug owes no redirect, and treating one
    as an alias is actively wrong: `grok` was renamed to `grok-app` and has since been
    REUSED for a different live product, so a redirect would 308 that live page onto
    another one. build/validate.py now rejects an alias that collides with a live slug,
    which is the mechanism that used to be this docstring. See docs/reference/identity.md.

    Sorted, because this payload feeds a daily automated PR in another repo and
    unsorted keys would show up there as a phantom diff.

    Scoped to what the payload serves, same as `_organizations` and for the same reason: a
    redirect to a page the payload does not carry is a 404 with extra steps. `published` is the
    product slugs in published categories, `org_slugs` the organizations that own at least one
    of them.
    """
    return {
        "products": dict(sorted(
            (alias, slug) for slug, p in prods.items() if slug in published
            for alias in (p.get("aliases") or [])
        )),
        "organizations": dict(sorted(
            (alias, slug) for slug, o in orgs.items() if slug in org_slugs
            for alias in (o.get("aliases") or [])
        )),
    }


def repo_version(root: Path | None = None) -> str:
    """The release version this payload was built from, read from ``pyproject.toml``.

    Consumers show it as the map's version, so it has to be the same string the release
    carries. ``pyproject.toml`` is one of the records ``tests/test_release_metadata.py``
    holds in agreement with the changelog and the git tag, so reading it here means the
    payload cannot name a version the repo never released.
    """
    data = tomllib.loads(((root or ROOT) / "pyproject.toml").read_text(encoding="utf-8"))
    return data["project"]["version"]


def release_date(version: str, root: Path | None = None) -> str:
    """The date ``version`` was released, from its dated heading in ``CHANGELOG.md``.

    This is the date the release was cut, which is not the date the payload was built —
    a rebuild between releases keeps the release date and moves ``generated``. Looking the
    date up *by version* rather than taking the newest heading means a payload can never
    pair one release's number with another's date; a version with no dated heading is an
    error rather than a silent fallback.
    """
    text = ((root or ROOT) / "CHANGELOG.md").read_text(encoding="utf-8")
    m = re.search(rf"^## \[{re.escape(version)}\]\s+-\s+(\d{{4}}-\d{{2}}-\d{{2}})\s*$",
                  text, re.M)
    if not m:
        raise ValueError(f"CHANGELOG.md has no dated heading for release {version}")
    return m.group(1)


def build_payload(sources: dict, frozen_long_tail: dict, generated: str | None = None,
                  freshness: dict | None = None, version: str | None = None,
                  released: str | None = None) -> dict:
    if generated is None:
        generated = date.today().isoformat()
    if version is None:
        version = repo_version()
    if released is None:
        released = release_date(version)
    orgs, cats, prods, scores = (sources["organizations"], sources["categories"],
                                 sources["products"], sources["scores"])
    taxonomy = sources["taxonomy"]
    # Global slug -> display name map, used to resolve lineage references (which
    # point at other on-map products by slug) into readable names at serialize time.
    name_map = {slug: p["display_name"] for slug, p in prods.items()}
    # Products no longer carry an `org` field; the organization owns the roster.
    # Build the reverse map (product_slug -> org_slug) by walking every org roster.
    product_org: dict[str, str] = {}
    for org_slug, org in orgs.items():
        for prod_slug in org.get("products", []):
            product_org[prod_slug] = org_slug
    # The curated display order + arc grouping live in sources/taxonomy.yaml.
    # Arcs are the Columbia ontology layers; each arc carries a `layer` slug.
    # Flatten arcs[].categories in sequence to get the global `order` list, and
    # build {category_slug: arc_name} + {category_slug: layer_slug} maps so both
    # the display arc and the machine layer are derived from the same source.
    order: list[str] = []
    cid_arc: dict[str, str] = {}
    cid_layer: dict[str, str] = {}
    # layer_order is the Columbia layers in stacking order, taken from the arc
    # sequence in sources/taxonomy.yaml (one layer per arc). Consumers use it to
    # render layers in order without re-deriving it from the per-category `layer`.
    layer_order: list[str] = []
    for arc in taxonomy["arcs"]:
        lyr = arc.get("layer")
        if lyr and lyr not in layer_order:
            layer_order.append(lyr)
        for cid, status in arc_categories(arc):
            if status != "published":
                continue
            order.append(cid)
            cid_arc[cid] = arc["name"]
            cid_layer[cid] = lyr
    out_cats = {}
    n = 0
    published_slugs: set[str] = set()
    for cid in order:
        cat = cats[cid]
        rows = []
        for slug in cat["products"]:
            published_slugs.add(slug)
            p = prods[slug]
            # The `unknown` sentinel org is the registry placeholder for products
            # that had an empty org string in the source. Reconstruct that empty
            # string so the round-trip is lossless (the registry keeps the display
            # name "Unknown", which is schema-valid; the overlay carries "").
            org_slug = product_org[slug]
            org_name = "" if org_slug == "unknown" else orgs[org_slug]["display_name"]
            rows.append(_row(slug, p, org_slug, org_name, scores[slug],
                             cat.get("weights"), name_map,
                             (freshness or {}).get(slug)))
            n += 1
        sg = _stage_and_gaps(rows, cat.get("weights"), disclosure=cat.get("disclosure_gap", False))
        out_cats[cid] = {"label": cat["display_name"], "arc": cid_arc[cid],
                         "layer": cid_layer[cid], "stage": {"num": sg["num"], "name": sg["name"]},
                         "gaps": sg["gaps"], "products": rows}
    # Editable legend for the derived attributes, carried at the top of the payload.
    # Stage/gap text are methodology constants (above); the per-category one-liner is
    # the neutral `description` from sources/categories/<cid>.yaml ("what it is", as
    # opposed to the editorial strapline). Edit at the source; it flows here on build.
    # Built before the payload literal because the alias index is scoped to the organizations
    # this leaves standing, and both are scoped to the published products.
    organizations = _organizations(orgs, product_org, published_slugs)
    descriptions = {
        "stages": {str(k): v for k, v in _STAGE_DESC.items()},
        "gaps": dict(_GAP_DESC),
        "tiers": dict(_TIER_DESC),
        "categories": {cid: cats[cid].get("description", "") for cid in order},
    }
    return {"descriptions": descriptions, "layer_order": layer_order,
            "categories": out_cats, "order": order,
            "organizations": organizations,
            "aliases": _aliases(prods, orgs, published_slugs, set(organizations)),
            "n_total": n, "generated": generated,
            "version": version, "released": released,
            # Published products only: see _filter_long_tail. A preliminary category's
            # products are not shown above, so their tail rows stay visible below.
            "long_tail": _filter_long_tail(
                frozen_long_tail, {s: prods[s] for s in published_slugs})}


if __name__ == "__main__":
    import argparse
    from build.validate import load_sources
    from build.freshness_payload import resolve_freshness
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=None,
                        help="value for the payload 'generated' field (default: today)")
    parser.add_argument("--version", default=None,
                        help="value for the payload 'version' field (default: pyproject.toml)")
    parser.add_argument("--released", default=None,
                        help="value for the payload 'released' field (default: CHANGELOG.md)")
    args = parser.parse_args()
    sources = load_sources(ROOT)
    frozen = json.load(open(ROOT / "sources" / "snapshots" / "long_tail.json"))
    payload = build_payload(sources, frozen, generated=args.date,
                            freshness=resolve_freshness(ROOT), version=args.version,
                            released=args.released)
    (ROOT / "build" / "notebook_data.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"wrote build/notebook_data.json "
          f"({payload['n_total']} products, v{payload['version']} "
          f"released {payload['released']}, built {payload['generated']})")
