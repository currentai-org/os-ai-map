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
                     "openness", "adoption", "capability", "version_note"]

# --- Gap analysis (category-level stage + gaps) -----------------------------
# Mirrors the open / open-ish / closed verdict in docs/openness-class-map.json
# (the canonical map). Kept inline here so serialize is self-contained; if these
# diverge from the JSON, the JSON is source of truth.
_GAP_OPEN = {"open_source", "open", "open_core", "open_hardware"}
_GAP_OPENISH = {"open_weights", "source_available", "gated", "open_toolchain"}
_MATURE_MIN = 4.5          # blended adoption/capability score to count as "mature"
_STAGE5_MIN_MATURE = 4     # mature fully-open products needed for Stage 5
_STAGE5_MIN_TOTAL = 3      # total fully-open products needed for Stage 5
_STAGE_NAMES = {0: "Void", 1: "Open Experiments", 2: "Emerging Alternatives",
                3: "Viable Alternatives", 4: "Competitive Open Ecosystem",
                5: "Mature Open Ecosystem"}


def _gap_bucket(cls: str) -> str:
    if cls in _GAP_OPEN:
        return "open"
    if cls in _GAP_OPENISH:
        return "open-ish"
    return "closed"


def _maturity_score(row: dict, w: dict) -> float:
    # Per-category linear formula over the 1-5 axes; datasets have no capability
    # score, so they are graded on adoption alone.
    adoption = (row.get("adoption") or {}).get("level") or 0
    capability = (row.get("capability") or {}).get("score")
    if capability is None:
        return float(adoption)
    return w["adopt"] * adoption + w["cap"] * capability


def _stage_and_gaps(rows: list[dict], weights: dict) -> dict:
    """Assign a maturity stage (0-5) and the set of gaps for one category.

    Strict open-only: only fully-open products count toward maturity/stage;
    open-ish only serves to detect the openness gap. See docs/guides/gap-analysis.md.
    """
    w = weights or {"adopt": 0.5, "cap": 0.5}
    enr = [(_gap_bucket((r.get("openness") or {}).get("class")), _maturity_score(r, w)) for r in rows]
    open_scores = [s for b, s in enr if b == "open"]
    total_open = len(open_scores)
    mature_open = sum(1 for s in open_scores if s >= _MATURE_MIN)
    best_open = max(open_scores, default=0.0)
    mature_any = any(s >= _MATURE_MIN for _, s in enr)

    if mature_open >= _STAGE5_MIN_MATURE and total_open >= _STAGE5_MIN_TOTAL:
        stage = 5
    elif mature_open >= 1:
        stage = 4
    elif best_open < 2 and not mature_any:
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
        if mature_any:                       # capable mature options exist, but none fully open
            gaps.append("openness")
        else:                                # nothing mature anywhere -> diagnose the limiting axis
            best = max(rows, key=lambda r: _maturity_score(r, w), default=None)
            bcap = (best or {}).get("capability", {}) or {}
            cap = bcap.get("score")
            gaps.append("capability" if (cap is not None and cap < 4) else "adoption")

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


def _row(prod: dict, org_name: str, score: dict) -> dict:
    row = {
        "product": prod["display_name"],
        "org": org_name,
        "type": prod["type"],
        "description": prod.get("description", ""),
        "openness": score["openness"],
        "adoption": score["adoption"],
        "capability": score["capability"],
    }
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
            rows.append(_row(p, org_name, scores[slug]))
            n += 1
        sg = _stage_and_gaps(rows, cat.get("weights"))
        out_cats[cid] = {"label": cat["display_name"], "arc": cid_arc[cid],
                         "layer": cid_layer[cid], "stage": {"num": sg["num"], "name": sg["name"]},
                         "gaps": sg["gaps"], "products": rows}
    return {"categories": out_cats, "order": order, "n_total": n,
            "generated": generated, "long_tail": _filter_long_tail(frozen_long_tail, prods)}


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
