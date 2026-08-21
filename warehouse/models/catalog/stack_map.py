"""
Build the stack-map taxonomy bridge CSV from curated sources/.

Unlike the other fetchers (which pull from external APIs), this derives a CSV
purely from the curated YAML in sources/: it maps every scored product's GitHub
repo to its stack-map taxonomy (category, layer, openness). The OSO warehouse
entities/repos catalog carries goodailist categories, NOT the curated
sources/categories taxonomy, so this bridge is what lets warehouse models
(e.g. currentai.scores.stack_contributors) roll up by stack-map category.

Output: warehouse/data/catalog/stack_map.csv  (one row per scored repo)
Upload as the currentai.catalog.stack_map static model (see docs/architecture/data-architecture.md).

Usage:
    uv run python warehouse/models/catalog/stack_map.py
"""

import csv
import glob
import os
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent.parent
SOURCES = ROOT / "sources"
OUTPUT_CSV = ROOT / "warehouse" / "data" / "catalog" / "stack_map.csv"

OPEN = {"open_source", "open", "open_core", "open_hardware"}
OPENISH = {"open_weights", "source_available", "gated", "open_toolchain"}


def _bucket(cls: str) -> str:
    if cls in OPEN:
        return "open"
    if cls in OPENISH:
        return "open-ish"
    return "closed"


def _slug(doc: dict, path: str) -> str:
    return (doc or {}).get("name") or os.path.splitext(os.path.basename(path))[0]


def _maturity(adoption, capability, w):
    # Mirror build/serialize.py _maturity_score: per-category adoption/capability blend,
    # rounded to 2dp; adoption-only when capability is null; null when adoption is missing.
    if adoption is None:
        return ""
    if capability is None:
        return round(float(adoption), 2)
    wa, wc = (w or {}).get("adopt", 0.5), (w or {}).get("cap", 0.5)
    return round((wa * adoption + wc * capability) / ((wa + wc) or 1.0), 2)


def build_rows() -> list[list[str]]:
    # category -> layer (taxonomy arcs ARE the Columbia layers)
    tax = yaml.safe_load((SOURCES / "taxonomy.yaml").read_text())
    cat_layer = {cs: arc["layer"] for arc in tax["arcs"] for cs in arc["categories"]}

    # product slug -> category (category rosters own the assignment); category -> weights
    prod_cat = {}
    cat_weights = {}
    for f in glob.glob(str(SOURCES / "categories" / "*.yaml")):
        cat = yaml.safe_load(open(f)) or {}
        cslug = _slug(cat, f)
        cat_weights[cslug] = cat.get("weights") or {"adopt": 0.5, "cap": 0.5}
        for ps in cat.get("products") or []:
            prod_cat[ps] = cslug

    # product slug -> org display name (org rosters own membership)
    prod_org = {}
    for f in glob.glob(str(SOURCES / "organizations" / "*.yaml")):
        o = yaml.safe_load(open(f)) or {}
        disp = o.get("display_name") or _slug(o, f)
        for ps in o.get("products") or []:
            prod_org[ps] = disp

    # product slug -> (openness class/bucket, adoption level, capability score)
    prod_score = {}
    for f in glob.glob(str(SOURCES / "scores" / "*.yaml")):
        s = yaml.safe_load(open(f)) or {}
        cls = (s.get("openness") or {}).get("class")
        adoption = (s.get("adoption") or {}).get("level")
        capability = (s.get("capability") or {}).get("score")
        prod_score[_slug(s, f)] = (cls, _bucket(cls), adoption, capability)

    # product -> repos, joined to the above
    seen: dict[str, list[str]] = {}
    for f in glob.glob(str(SOURCES / "products" / "*.yaml")):
        p = yaml.safe_load(open(f)) or {}
        slug = _slug(p, f)
        disp = p.get("display_name", slug)
        cat = prod_cat.get(slug)
        layer = cat_layer.get(cat)
        cls, buck, adoption, capability = prod_score.get(slug, (None, "closed", None, None))
        maturity = _maturity(adoption, capability, cat_weights.get(cat))
        org = prod_org.get(slug, "")
        for u in p.get("github", []) or []:
            m = re.search(r"github\.com/([^/]+/[^/]+?)(?:\.git)?/?$", u["url"])
            if m and cat:
                repo = m.group(1).lower()
                if repo not in seen:
                    seen[repo] = [repo, slug, disp, org, cat, layer, cls or "unknown", buck,
                                  "" if adoption is None else adoption,
                                  "" if capability is None else capability, maturity]
    return sorted(seen.values())


def main() -> None:
    rows = build_rows()
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["repo", "product_slug", "product_name", "org",
                    "category", "layer", "openness_class", "openness_bucket",
                    "adoption", "capability", "maturity"])
        w.writerows(rows)
    print(f"wrote {OUTPUT_CSV.relative_to(ROOT)}: {len(rows)} rows")


if __name__ == "__main__":
    main()
