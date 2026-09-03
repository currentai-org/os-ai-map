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
                        weight_adopt, weight_cap, arc_name, layer, status
  tail_products          slug, display_name, product_type, org_slug,
                        category_slug, artifact_kind, artifact_id, artifact_url
  product_artifacts     product_slug, product_type, artifact_kind, artifact_id, artifact_url
                        (kinds: github, huggingface_model, huggingface_dataset,
                         pypi, npm, crates, arxiv)
  product_categories    product_slug, category_slug
  product_organizations product_slug, org_slug
  product_lineage       product_slug, relation, target
  resolution_ledger     artifact_kind, artifact_id, relation, verdict, resolves_to,
                        boundary, decided_in, decided_on, note
                        (grain: one row per (artifact_kind, artifact_id, relation,
                         resolves_to) -- a product_membership ruling names the product
                         it is about, so the same artifact may carry a separate row per
                         product it has been weighed against)
  product_aliases       alias, product_slug

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
import sys
from pathlib import Path

from build.identity import ARXIV_ID, canonical, homepage_canonical_url, id_from_url
from build.resolution import artifact_of as _ledger_artifact_of
from build.resolution import load as load_resolution_ledger
from build.resolution import relation_of as _ledger_relation_of
from build.serialize import _aliases
from build.taxonomy import arc_categories, category_statuses
from build.validate import load_sources, published_products

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
        "status",
    ),
    "tail_products": (
        "slug",
        "display_name",
        "product_type",
        "org_slug",
        "category_slug",
        "artifact_kind",
        "artifact_id",
        "artifact_url",
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
    "resolution_ledger": (
        "artifact_kind",
        "artifact_id",
        "relation",
        "verdict",
        "resolves_to",
        "boundary",
        "decided_in",
        "decided_on",
        "note",
    ),
    "product_aliases": ("alias", "product_slug"),
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
    """Reduce a URL to the canonical identifier the relevant API expects.

    Returns None when the URL is not addressable as that artifact kind — an
    org-level GitHub link, for instance, which names no repo. Delegates the
    pattern and the canonical form to `build.identity`, except arXiv also
    accepts a bare id with no `arxiv:` wrapper (`id_from_url` requires one),
    since that is the form a tail registry row and this module's own callers
    sometimes carry.
    """
    trimmed = (url or "").rstrip("/")
    if not trimmed:
        return None
    ident = id_from_url(kind, trimmed)
    if ident is not None:
        return canonical(kind, ident)
    if kind == "arxiv":
        bare = trimmed.removeprefix("arxiv:").removeprefix("ARXIV:")
        match = ARXIV_ID.match(bare)
        return match.group(1).lower() if match else None
    return None


def category_layers(taxonomy: dict) -> dict[str, tuple[str, str]]:
    """Map category slug -> (arc name, layer slug), derived from the arcs."""
    out: dict[str, tuple[str, str]] = {}
    for arc in taxonomy.get("arcs") or []:
        if not isinstance(arc, dict):
            continue
        name = arc.get("name")
        layer = arc.get("layer")
        for slug, _status in arc_categories(arc):
            if isinstance(name, str) and isinstance(layer, str):
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
    registry: dict = sources.get("registry") or {}
    layers = category_layers(sources.get("taxonomy") or {})
    statuses = category_statuses(sources.get("taxonomy") or {})

    tables: dict[str, list[dict]] = {name: [] for name in TABLES}
    errors: list[str] = []
    warnings: list[str] = []

    # Two products sharing a display_name render as two identically labeled entries,
    # so a reader cannot tell them apart and cannot tell whether the map is double
    # counting. Slugs are unique by construction — they are filenames — so nothing
    # caught this, and four collisions accumulated: 'Nemotron 3', 'GPT-4.1',
    # 'Gemini 3.5 Flash' and 'GitHub Copilot'.
    #
    # A warning rather than an error, because the collisions are not one defect. Some
    # are genuinely two product surfaces needing distinct labels (Copilot's agent mode
    # vs its IDE assistant); others are one product entered twice and the fix is a
    # deletion, which is a curation decision. Failing the build would force whoever
    # hits it next to pick under time pressure.
    by_display_name: dict[str, list[str]] = {}
    for slug, product in sorted(products.items()):
        name = (product.get("display_name") or "").strip()
        if name:
            by_display_name.setdefault(name, []).append(slug)
    for name, slugs in sorted(by_display_name.items()):
        if len(slugs) > 1:
            where = ", ".join(
                f"{slug} ({', '.join(c for c, spec in sorted(categories.items()) if slug in (spec.get('products') or [])) or 'no category'})"
                for slug in slugs
            )
            warnings.append(f"display_name {name!r} is shared by {len(slugs)} products: {where}")

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
                "status": statuses.get(slug, ""),
            }
        )
        for product_slug in category.get("products") or []:
            if product_slug not in products:
                errors.append(f"category '{slug}' lists unknown product '{product_slug}'")
                continue
            tables["product_categories"].append(
                {"product_slug": product_slug, "category_slug": slug}
            )

    # Appended (crates, arxiv, homepage) rather than inserted, so existing per-kind ordering
    # in any downstream diff or fixture is undisturbed -- #365 added crates/arxiv as tail row
    # fields but they were still absent here, so a crates- or arxiv-only tail row validated
    # and then silently produced no `tail_products` row at all. `homepage` had the identical
    # bug: a homepage-only tail row satisfies the `anyOf` in the schema and validates, but
    # emitted zero `tail_products` rows because this list never carried it. Unlike the other
    # kinds, a tail row's `homepage` field is already a full URI (see
    # docs/schemas/registry.schema.json), so it is reduced with `canonical`/
    # `homepage_canonical_url` directly rather than through the URL-templating below.
    # `artifact_id` carries the full canonical URL (host + path), not the bare domain --
    # a homepage is evidence, not identity, and two products sharing a company's domain
    # at different paths are not a collision (see docs/reference/identity.md). SQL that
    # wants the domain alone derives it from this URL rather than reading a separate
    # column; `homepage_domain` stays available for that derivation but is not stored
    # here.
    tail_artifact_kinds = (
        "github", "pypi", "npm", "huggingface_model", "huggingface_dataset",
        "crates", "arxiv", "homepage",
    )
    for category_slug, record in sorted(registry.items()):
        for product in record.get("products") or []:
            for kind in tail_artifact_kinds:
                identifier = product.get(kind)
                if not identifier:
                    continue
                if kind == "homepage":
                    row_artifact_id = canonical("homepage", identifier)
                    url = homepage_canonical_url(identifier)
                else:
                    row_artifact_id = identifier
                    if kind == "github":
                        url = f"https://github.com/{identifier}"
                    elif kind == "pypi":
                        url = f"https://pypi.org/project/{identifier}/"
                    elif kind == "npm":
                        url = f"https://www.npmjs.com/package/{identifier}"
                    elif kind == "huggingface_model":
                        url = f"https://huggingface.co/{identifier}"
                    elif kind == "huggingface_dataset":
                        url = f"https://huggingface.co/datasets/{identifier}"
                    elif kind == "crates":
                        url = f"https://crates.io/crates/{identifier}"
                    else:
                        url = f"https://arxiv.org/abs/{identifier}"
                tables["tail_products"].append(
                    {
                        "slug": product.get("slug", ""),
                        "display_name": product.get("display_name", ""),
                        "product_type": product.get("type", ""),
                        "org_slug": product.get("org", ""),
                        "category_slug": category_slug,
                        "artifact_kind": kind,
                        "artifact_id": row_artifact_id,
                        "artifact_url": url,
                    }
                )

    # The decision memory: one row per (artifact, relation, resolves_to) ruling, exactly the
    # grain `build.resolution.load` keys on -- a `product_membership` ruling is a statement
    # about ONE product, so the same artifact may carry a separate `member_of`/`not_member_of`
    # row per product it has been weighed against. Sorted for determinism, since this feeds the
    # same daily automated PR the other tables do.
    ledger = load_resolution_ledger()
    for entry in sorted(
        ledger.values(),
        key=lambda e: (*_ledger_artifact_of(e), _ledger_relation_of(e), e.get("resolves_to") or ""),
    ):
        kind, canonical_id = _ledger_artifact_of(entry)
        relation = _ledger_relation_of(entry)
        tables["resolution_ledger"].append(
            {
                "artifact_kind": kind,
                "artifact_id": canonical_id,
                "relation": relation,
                "verdict": entry.get("verdict", ""),
                "resolves_to": entry.get("resolves_to") or entry.get("product") or "",
                "boundary": entry.get("boundary") or "",
                "decided_in": entry.get("decided_in") or "",
                "decided_on": entry.get("decided_on") or "",
                "note": entry.get("note") or "",
            }
        )

    # Aliases, published products only -- must match build.serialize._aliases exactly
    # (same helper, same "published" set) so the table and the notebook payload can never
    # disagree about which redirects exist.
    published = published_products(sources.get("taxonomy") or {}, categories)
    product_aliases = _aliases(products, organizations, published, set())["products"]
    for alias, product_slug in sorted(product_aliases.items()):
        tables["product_aliases"].append({"alias": alias, "product_slug": product_slug})

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
