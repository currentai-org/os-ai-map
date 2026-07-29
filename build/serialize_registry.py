"""Serialize the registry — what exists — to flat CSVs for downstream consumers.

This is deliberately NOT `serialize.py`. That module builds the scored payload the
notebooks render. This one emits only the *declarative* layer: which products,
organizations and categories exist, and how they relate. Scores are excluded on
purpose, because scoring is computed downstream and flows back out; if scores
appeared here the registry would become a scoreboard and the dependency would
point the wrong way.

Emitted tables (one CSV each, written to build/registry/):

  products              slug, display_name, type, description, comments
  organizations         slug, display_name, type, homepage, github, country
  categories            slug, display_name, description, strapline,
                        weight_adopt, weight_cap, arc_name, layer
  product_artifacts     product_slug, product_type, artifact_kind, artifact_id, artifact_url
                        (kinds: github, huggingface_model, huggingface_dataset,
                         pypi, npm, crates, arxiv)
  product_categories    product_slug, category_slug
  product_organizations product_slug, org_slug
  product_lineage       product_slug, relation, target

`arxiv` exists so citation lookups join on an exact identifier. Matching papers
by product name was measured at 2 correct out of 10 — APPS resolved to a medical
software paper with 25k citations and MATH to a psychology paper with 3.4k, both
of which would have looked entirely credible in a table.

Two structural notes:

  * Membership is declared on the parent — categories and organizations each list
    their products — so it is inverted here into join tables.
  * A category's `layer` is never stored on the category. It is derived from
    whichever arc contains it in taxonomy.yaml, matching the comment in that file.
    Storing it twice is how the two drift apart.

Usage:
    uv run python -m build.serialize_registry            # write CSVs
    uv run python -m build.serialize_registry --check    # verify, write nothing
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

from build.validate import load_sources

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "build" / "registry"

ARTIFACT_KINDS = (
    "github",
    "huggingface_model",
    "huggingface_dataset",
    "pypi",
    "npm",
    "crates",
    "arxiv",
)
LINEAGE_RELATIONS = ("derived_from", "curated_with", "trains")

TABLES: dict[str, tuple[str, ...]] = {
    "products": ("slug", "display_name", "type", "description", "comments"),
    "organizations": ("slug", "display_name", "type", "homepage", "github", "country"),
    "categories": (
        "slug",
        "display_name",
        "description",
        "strapline",
        "weight_adopt",
        "weight_cap",
        "arc_name",
        "layer",
    ),
    "product_artifacts": (
        "product_slug",
        "product_type",
        "artifact_kind",
        "artifact_id",
        "artifact_url",
    ),
    "product_categories": ("product_slug", "category_slug"),
    "product_organizations": ("product_slug", "org_slug"),
    "product_lineage": ("product_slug", "relation", "target"),
}

_ID_PATTERNS = {
    "github": r"github\.com/([^/]+/[^/]+)",
    "huggingface_model": r"huggingface\.co/(?!datasets/)(.+)",
    "huggingface_dataset": r"huggingface\.co/datasets/(.+)",
    "pypi": r"pypi\.org/project/([^/]+)",
    "npm": r"npmjs\.com/package/(.+)",
    # Accept an abs/pdf URL or a bare id, and normalize to the bare id so the
    # DOI is derivable as 10.48550/arXiv.<id> without further parsing.
    "arxiv": r"(?:arxiv\.org/(?:abs|pdf)/)?(\d{4}\.\d{4,5})(?:v\d+)?",
}


def _urls(value: object) -> list[str]:
    """Artifact values are lists of {url: ...}; tolerate a bare string too."""
    if isinstance(value, str):
        return [value]
    out: list[str] = []
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict) and isinstance(item.get("url"), str):
                out.append(item["url"])
            elif isinstance(item, str):
                out.append(item)
    return out


def artifact_id(kind: str, url: str) -> str | None:
    """Reduce a URL to the identifier the relevant API expects.

    Returns None when the URL is not addressable as that artifact kind — an
    org-level GitHub link, for instance, which names no repo.
    """
    trimmed = url.rstrip("/")
    pattern = _ID_PATTERNS.get(kind)
    if pattern is None:
        return trimmed or None
    match = re.search(pattern, trimmed)
    if match is None:
        return None
    # The github pattern already requires owner/repo, so an org-level link fails
    # to match above and is reported rather than silently reduced.
    return match.group(1) or None


def category_layers(taxonomy: dict) -> dict[str, tuple[str, str]]:
    """Map category slug -> (arc name, layer slug), derived from the arcs."""
    out: dict[str, tuple[str, str]] = {}
    for arc in taxonomy.get("arcs") or []:
        if not isinstance(arc, dict):
            continue
        name = arc.get("name")
        layer = arc.get("layer")
        for slug in arc.get("categories") or []:
            if isinstance(slug, str) and isinstance(name, str) and isinstance(layer, str):
                out[slug] = (name, layer)
    return out


def build_registry(sources: dict) -> tuple[dict[str, list[dict]], list[str], list[str]]:
    """Return (tables, errors, warnings).

    Errors are structural — a reference that points at nothing, a product with no
    category or no organization. Those break any downstream join, so they fail.

    Warnings are data-quality: an artifact URL that names no addressable resource,
    such as a GitHub org rather than a repo. Those cost coverage but break nothing,
    and choosing the right replacement is a curation decision, so they do not fail.
    """
    products: dict = sources["products"]
    organizations: dict = sources["organizations"]
    categories: dict = sources["categories"]
    layers = category_layers(sources.get("taxonomy") or {})

    tables: dict[str, list[dict]] = {name: [] for name in TABLES}
    errors: list[str] = []
    warnings: list[str] = []

    for slug, product in sorted(products.items()):
        tables["products"].append(
            {
                "slug": slug,
                "display_name": product.get("display_name", ""),
                "type": product.get("type", ""),
                "description": product.get("description", ""),
                "comments": product.get("comments", ""),
            }
        )
        for kind in ARTIFACT_KINDS:
            for url in _urls(product.get(kind)):
                identifier = artifact_id(kind, url)
                if identifier is None:
                    warnings.append(f"product '{slug}': {kind} url names no repo: {url}")
                    continue
                tables["product_artifacts"].append(
                    {
                        "product_slug": slug,
                        "product_type": product.get("type", ""),
                        "artifact_kind": kind,
                        "artifact_id": identifier,
                        "artifact_url": url,
                    }
                )
        lineage = product.get("lineage")
        if isinstance(lineage, dict):
            for relation in LINEAGE_RELATIONS:
                for target in lineage.get(relation) or []:
                    if isinstance(target, str):
                        tables["product_lineage"].append(
                            {"product_slug": slug, "relation": relation, "target": target}
                        )

    for slug, org in sorted(organizations.items()):
        tables["organizations"].append(
            {
                "slug": slug,
                "display_name": org.get("display_name", ""),
                "type": org.get("type", ""),
                "homepage": org.get("homepage", ""),
                "github": org.get("github", ""),
                "country": org.get("country", ""),
            }
        )
        for product_slug in org.get("products") or []:
            if product_slug not in products:
                errors.append(f"organization '{slug}' lists unknown product '{product_slug}'")
                continue
            tables["product_organizations"].append(
                {"product_slug": product_slug, "org_slug": slug}
            )

    for slug, category in sorted(categories.items()):
        arc_name, layer = layers.get(slug, ("", ""))
        if not layer:
            errors.append(f"category '{slug}' sits in no arc in taxonomy.yaml")
        weights = category.get("weights") or {}
        tables["categories"].append(
            {
                "slug": slug,
                "display_name": category.get("display_name", ""),
                "description": category.get("description", ""),
                "strapline": category.get("strapline", ""),
                "weight_adopt": weights.get("adopt", ""),
                "weight_cap": weights.get("cap", ""),
                "arc_name": arc_name,
                "layer": layer,
            }
        )
        for product_slug in category.get("products") or []:
            if product_slug not in products:
                errors.append(f"category '{slug}' lists unknown product '{product_slug}'")
                continue
            tables["product_categories"].append(
                {"product_slug": product_slug, "category_slug": slug}
            )

    placed = {row["product_slug"] for row in tables["product_categories"]}
    owned = {row["product_slug"] for row in tables["product_organizations"]}
    for slug in sorted(set(products) - placed):
        errors.append(f"product '{slug}' is in no category")
    for slug in sorted(set(products) - owned):
        errors.append(f"product '{slug}' has no organization")

    return tables, errors, warnings


def write_tables(
    tables: dict[str, list[dict]],
    out_dir: Path,
    spec: dict[str, tuple[str, ...]] | None = None,
) -> None:
    """Write one CSV per declared table. `spec` defaults to the registry's own.

    Shared with build/serialize_rubric.py, which emits a different table set into
    the same directory, so the column order comes from the caller's spec rather
    than from this module's TABLES.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, columns in (spec or TABLES).items():
        path = out_dir / f"{name}.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(columns))
            writer.writeheader()
            writer.writerows(tables[name])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate only, write nothing")
    parser.add_argument("--out", type=Path, default=OUT_DIR, help="output directory")
    args = parser.parse_args()

    sources = load_sources(ROOT)
    tables, errors, warnings = build_registry(sources)

    for name in TABLES:
        print(f"  {name:<22} {len(tables[name]):>5} rows")

    if warnings:
        print(f"\n{len(warnings)} warning(s) - coverage lost, nothing broken:")
        for warning in warnings:
            print(f"  - {warning}")

    if errors:
        print(f"\n{len(errors)} error(s) - these break downstream joins:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    if args.check:
        print("\ncheck only: nothing written")
        return 0

    write_tables(tables, args.out)
    print(f"\nwrote {len(TABLES)} CSVs to {args.out.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
