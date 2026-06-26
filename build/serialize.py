"""Compile sources/ (+ frozen long-tail) into the notebook_data.json payload.

Reproduces the exact structure the live notebook consumes:
  { categories: {cid: {label, arc, products[]}}, order[], n_total, generated, long_tail }
"""
from datetime import date
from pathlib import Path
import json
import re
import yaml

ROOT = Path(__file__).resolve().parents[1]

PRODUCT_KEY_ORDER = ["product", "org", "type", "description",
                     "openness", "adoption", "capability", "maturity", "mature",
                     "version_note"]

# --- Gap analysis (category-level stage + gaps) -----------------------------
# Mirrors the open / open-ish / closed verdict in docs/openness-class-map.json
# (the canonical map). Kept inline here so serialize is self-contained; if these
# diverge from the JSON, the JSON is source of truth.
_GAP_OPEN = {"open_source", "open", "open_core", "open_hardware"}
_GAP_OPENISH = {"open_weights", "source_available", "gated", "open_toolchain"}
_MATURE_MIN = 4.5          # blended adoption/capability score for a product to be "mature"
_STAGE5_MIN_MATURE = 4     # mature fully-open products needed for Stage 5 (Mature Open Ecosystem)
_CAPABLE_MIN = 4           # raw capability below which an open option is "not capable yet"
_STAGE_NAMES = {0: "Void", 1: "Open Experiments", 2: "Emerging Alternatives",
                3: "Viable Alternatives", 4: "Competitive Open Ecosystem",
                5: "Mature Open Ecosystem"}
# Plain-language definitions of each stage and gap, emitted into the payload's
# top-level `descriptions` block so downstream consumers render a legend without
# re-deriving the methodology. Kept verbatim from docs/guides/gap-analysis.md
# (the prose source of truth); edit both together.
_STAGE_DESC = {
    0: "no usable open option exists (and nothing is mature anywhere)",
    1: "fully-open options exist but are weak on both axes",
    2: "no mature fully-open product; the best fully-open option is promising but limited",
    3: "no mature fully-open product, but the best fully-open option is strong",
    4: "at least one mature fully-open product, but not yet enough for depth",
    5: "enough mature fully-open products to be redundant/resilient",
}
_GAP_DESC = {
    "void": "no usable open option at all.",
    "capability": "the best fully-open option isn't capable enough to be useful.",
    "adoption": "a capable fully-open option exists but is under-adopted.",
    "maturity": "open options exist and at least one may be mature, but the ecosystem lacks "
                "the depth/redundancy of a mature ecosystem (too few mature fully-open products).",
    "openness": "capable, adopted options exist, but the mature ones are not fully open "
                "(open-ish or closed). This is the orthogonal flag; it can co-occur with the others.",
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


def _stage_and_gaps(rows: list[dict], weights: dict) -> dict:
    """Assign a maturity stage (0-5) and the set of gaps for one category.

    Strict open-only: only fully-open products count toward maturity/stage;
    open-ish only serves to detect the openness gap. See docs/guides/gap-analysis.md.
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
        gaps = ["maturity"]
    else:
        gaps = ["maturity"]
        if mature_anywhere:                  # capable mature options exist, but none fully open
            gaps.append("openness")
        else:                                # the open ecosystem itself is immature -> which axis?
            best = max(open_rows, key=lambda rs: rs[1])[0] if open_rows else None
            cap = ((best or {}).get("capability") or {}).get("score")
            gaps.append("capability" if (cap is not None and cap < _CAPABLE_MIN) else "adoption")

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
    batch); only the visible sample is derived so it never lists a scored product."""
    ids = _catalog_ids(prods)
    lt = dict(frozen)
    lt["top"] = [t for t in frozen.get("top", [])
                 if t.get("name", "").lower() not in ids.get(t.get("type"), set())]
    return lt


def _row(prod: dict, org_name: str, score: dict, weights: dict | None) -> dict:
    # Pre-compute the open / open-ish / closed bucket alongside the raw class, so
    # consumers get a stable 3-way verdict that survives changes to the openness.class
    # vocabulary. Same collapse the category gap logic uses (_gap_bucket).
    openness = {**score["openness"], "bucket": _gap_bucket((score["openness"] or {}).get("class"))}
    row = {
        "product": prod["display_name"],
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
    row["maturity"] = m
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
    return {k: row[k] for k in PRODUCT_KEY_ORDER if k in row}


def build_payload(sources: dict, frozen_long_tail: dict, generated: str | None = None) -> dict:
    if generated is None:
        generated = date.today().isoformat()
    orgs, cats, prods, scores = (sources["organizations"], sources["categories"],
                                 sources["products"], sources["scores"])
    taxonomy = sources["taxonomy"]
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
    for arc in taxonomy["arcs"]:
        for cid in arc["categories"]:
            order.append(cid)
            cid_arc[cid] = arc["name"]
            cid_layer[cid] = arc.get("layer")
    out_cats = {}
    n = 0
    for cid in order:
        cat = cats[cid]
        rows = []
        for slug in cat["products"]:
            p = prods[slug]
            # The `unknown` sentinel org is the registry placeholder for products
            # that had an empty org string in the source. Reconstruct that empty
            # string so the round-trip is lossless (the registry keeps the display
            # name "Unknown", which is schema-valid; the overlay carries "").
            org_slug = product_org[slug]
            org_name = "" if org_slug == "unknown" else orgs[org_slug]["display_name"]
            rows.append(_row(p, org_name, scores[slug], cat.get("weights")))
            n += 1
        sg = _stage_and_gaps(rows, cat.get("weights"))
        out_cats[cid] = {"label": cat["display_name"], "arc": cid_arc[cid],
                         "layer": cid_layer[cid], "stage": {"num": sg["num"], "name": sg["name"]},
                         "gaps": sg["gaps"], "products": rows}
    # Editable legend for the derived attributes, carried at the top of the payload.
    # Stage/gap text are methodology constants (above); the per-category one-liner is
    # the neutral `description` from sources/categories/<cid>.yaml ("what it is", as
    # opposed to the editorial strapline). Edit at the source; it flows here on build.
    descriptions = {
        "stages": {str(k): v for k, v in _STAGE_DESC.items()},
        "gaps": dict(_GAP_DESC),
        "categories": {cid: cats[cid].get("description", "") for cid in order},
    }
    return {"descriptions": descriptions, "categories": out_cats, "order": order,
            "n_total": n, "generated": generated,
            "long_tail": _filter_long_tail(frozen_long_tail, prods)}


if __name__ == "__main__":
    import argparse
    from build.validate import load_sources
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=None,
                        help="value for the payload 'generated' field (default: today)")
    args = parser.parse_args()
    sources = load_sources(ROOT)
    frozen = json.load(open(ROOT / "build" / "_frozen_long_tail.json"))
    payload = build_payload(sources, frozen, generated=args.date)
    (ROOT / "build" / "notebook_data.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"wrote build/notebook_data.json ({payload['n_total']} products)")
