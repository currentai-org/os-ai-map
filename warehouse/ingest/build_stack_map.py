"""
Build the stack-map taxonomy bridge CSV from curated sources/.

Unlike the other fetchers (which pull from external APIs), this derives a CSV
purely from the curated YAML in sources/: it maps every scored product's GitHub
repo to its stack-map taxonomy (category, layer, openness). The OSO warehouse
entities/repos catalog carries goodailist categories, NOT the curated
sources/categories taxonomy, so this bridge is what lets warehouse models
(e.g. currentai.scores.stack_contributors) roll up by stack-map category.

Output: warehouse/catalog/stack_map/repos.csv  (one row per scored repo)
Upload as the currentai.catalog.stack_map static model (see warehouse/models/README.md).

Usage:
    uv run python warehouse/ingest/build_stack_map.py
"""

import csv
import glob
import os
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
SOURCES = ROOT / "sources"
OUTPUT_CSV = ROOT / "warehouse" / "catalog" / "stack_map" / "repos.csv"

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


def build_rows() -> list[list[str]]:
    # category -> layer (taxonomy arcs ARE the Columbia layers)
    tax = yaml.safe_load((SOURCES / "taxonomy.yaml").read_text())
    cat_layer = {cs: arc["layer"] for arc in tax["arcs"] for cs in arc["categories"]}

    # product slug -> category (category rosters own the assignment)
    prod_cat = {}
    for f in glob.glob(str(SOURCES / "categories" / "*.yaml")):
        cat = yaml.safe_load(open(f)) or {}
        cslug = _slug(cat, f)
        for ps in cat.get("products") or []:
            prod_cat[ps] = cslug

    # product slug -> org display name (org rosters own membership)
    prod_org = {}
    for f in glob.glob(str(SOURCES / "organizations" / "*.yaml")):
        o = yaml.safe_load(open(f)) or {}
        disp = o.get("display_name") or _slug(o, f)
        for ps in o.get("products") or []:
            prod_org[ps] = disp

    # product slug -> openness class/bucket
    prod_open = {}
    for f in glob.glob(str(SOURCES / "scores" / "*.yaml")):
        s = yaml.safe_load(open(f)) or {}
        cls = (s.get("openness") or {}).get("class")
        prod_open[_slug(s, f)] = (cls, _bucket(cls))

    # product -> repos, joined to the above
    seen: dict[str, list[str]] = {}
    for f in glob.glob(str(SOURCES / "products" / "*.yaml")):
        p = yaml.safe_load(open(f)) or {}
        slug = _slug(p, f)
        disp = p.get("display_name", slug)
        cat = prod_cat.get(slug)
        layer = cat_layer.get(cat)
        cls, buck = prod_open.get(slug, (None, "closed"))
        org = prod_org.get(slug, "")
        for u in p.get("github", []) or []:
            m = re.search(r"github\.com/([^/]+/[^/]+?)(?:\.git)?/?$", u["url"])
            if m and cat:
                repo = m.group(1).lower()
                if repo not in seen:
                    seen[repo] = [repo, slug, disp, org, cat, layer, cls or "unknown", buck]
    return sorted(seen.values())


def main() -> None:
    rows = build_rows()
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["repo", "product_slug", "product_name", "org",
                    "category", "layer", "openness_class", "openness_bucket"])
        w.writerows(rows)
    print(f"wrote {OUTPUT_CSV.relative_to(ROOT)}: {len(rows)} rows")


if __name__ == "__main__":
    main()
