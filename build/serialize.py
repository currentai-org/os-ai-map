"""Compile sources/ (+ frozen long-tail) into the notebook_data.json payload.

Reproduces the exact structure the live notebook consumes:
  { categories: {cid: {label, arc, products[]}}, order[], n_total, generated, long_tail }
"""
from datetime import date
from pathlib import Path
import json
import yaml

ROOT = Path(__file__).resolve().parents[1]

PRODUCT_KEY_ORDER = ["product", "org", "type", "description",
                     "openness", "adoption", "capability", "version_note"]


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
    # Flatten arcs[].categories in sequence to get the global `order` list, and
    # build a {category_slug: arc_name} map for per-category arc tagging.
    order: list[str] = []
    cid_arc: dict[str, str] = {}
    for arc in taxonomy["arcs"]:
        for cid in arc["categories"]:
            order.append(cid)
            cid_arc[cid] = arc["name"]
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
        out_cats[cid] = {"label": cat["display_name"], "arc": cid_arc[cid], "products": rows}
    return {"categories": out_cats, "order": order, "n_total": n,
            "generated": generated, "long_tail": frozen_long_tail}


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
