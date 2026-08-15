"""Report how much of the map `sources/signal_routing.yaml` can actually answer.

The routing table declares which machine signal is authoritative for which
scoring dimension. This measures what that buys: for every product, which
dimensions have a usable route, and which fall through to research.

Two things it protects against:

  * **Overstating automation.** A routing table looks comprehensive until you
    count coverage. Capability has two declared anchors and neither is joinable,
    so on paper it is routed and in practice it is not. This prints that.
  * **Silent drift.** A route naming a table or column that no longer exists
    should fail here, not halfway through a research run.

Coverage is computed from the registry's artifacts rather than from the signal
tables directly, so it runs offline against the repo and answers "what could be
routed" — the live tables then determine what actually resolves.

Usage:
    uv run python -m build.check_routing
    uv run python -m build.check_routing --category base_pretrained
    uv run python -m build.check_routing --unrouted     # list products with no route at all
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

# Which artifact key in a product YAML satisfies which routing source.
SOURCE_ARTIFACT = {
    "github": "github",
    "huggingface_model": "huggingface_model",
    "huggingface_dataset": "huggingface_dataset",
    "pypi": "pypi",
    "semanticscholar": "arxiv",  # citations are reached via the paper id
}


def artifacts_of(product: dict) -> set[str]:
    """Which artifact kinds this product declares."""
    found: set[str] = set()
    for key in ("github", "huggingface_model", "huggingface_dataset", "pypi", "npm", "crates", "arxiv"):
        value = product.get(key)
        if value:
            found.add(key)
    return found


def load() -> tuple[dict, dict, dict, dict]:
    routing = yaml.safe_load((ROOT / "sources" / "signal_routing.yaml").read_text())
    products = {
        p.stem: yaml.safe_load(p.read_text())
        for p in sorted((ROOT / "sources" / "products").glob("*.yaml"))
    }
    categories = {
        p.stem: yaml.safe_load(p.read_text())
        for p in sorted((ROOT / "sources" / "categories").glob("*.yaml"))
    }
    category_of = {}
    for name, cat in categories.items():
        for slug in cat.get("products") or []:
            category_of[slug] = cat["name"]
    return routing, products, categories, category_of


def hand_authored(route: dict) -> bool:
    """Does this route declare that no machine source produces it?

    `source: null` is a DECLARATION, not an omission. Two adoption routes carry it:
    `reported_traction`, the instrument defined by having no count behind it, and
    `active_users`, a vendor-disclosed figure no endpoint serves. Both set
    `hand_authored: true` beside the null, which is what tells a reader the absence was
    chosen. Reading them as "unknown source" made this checker exit 1 on every run, so
    the two routes the table is most careful about were the two it called broken.
    """
    return route.get("source") is None and route.get("hand_authored") is True


def route_usable(route: dict, sources: dict) -> tuple[bool, str]:
    """Is this route executable at all, before considering any product?"""
    if hand_authored(route):
        return False, "hand-authored"
    source = sources.get(route.get("source")) or {}
    if route.get("blocked_by") == "bridge" or source.get("bridged") is False:
        return False, "unbridged"
    if not source:
        return False, "unknown source"
    return True, ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--category", help="limit to one category slug")
    parser.add_argument("--unrouted", action="store_true", help="list products with no route")
    args = parser.parse_args(argv)

    routing, products, _, category_of = load()
    sources = routing.get("sources") or {}
    dimensions = routing.get("dimensions") or {}

    # Structural check first: a route pointing at nothing is a bug in the table.
    problems: list[str] = []
    hand_authored_routes: dict[str, list[str]] = defaultdict(list)
    for dim, spec in dimensions.items():
        for route in spec.get("routes") or []:
            name = route.get("source")
            if hand_authored(route):
                hand_authored_routes[dim].append(route.get("signal_type") or "unnamed")
                continue
            if name not in sources:
                problems.append(f"{dim}: route names unknown source {name!r}")
                continue
            # An unbridged source can never resolve to a product, so it needs no
            # artifact mapping. Only a source claiming to be usable must have one.
            if sources[name].get("bridged") and name not in SOURCE_ARTIFACT:
                problems.append(f"{dim}: bridged source {name!r} has no artifact mapping in this checker")
    if problems:
        print("ROUTING TABLE PROBLEMS")
        for p in problems:
            print(f"  ! {p}")
        return 1

    slugs = [s for s in products if not args.category or category_of.get(s) == args.category]

    covered: dict[str, int] = defaultdict(int)
    blocked: dict[str, int] = defaultdict(int)
    per_product_routed: dict[str, int] = {}

    for slug in slugs:
        arts = artifacts_of(products[slug])
        cat = category_of.get(slug)
        n_routed = 0
        for dim, spec in dimensions.items():
            hit = False
            was_blocked = False
            for route in spec.get("routes") or []:
                only = route.get("applies_to_categories")
                if only and cat not in only:
                    continue
                usable, why = route_usable(route, sources)
                if not usable:
                    # A hand-authored route is not "blocked": nothing is waiting on a
                    # bridge, and counting it as blocked would overstate how much of the
                    # map a bridge could still buy.
                    was_blocked = was_blocked or why == "unbridged"
                    continue
                if SOURCE_ARTIFACT.get(route["source"]) in arts:
                    hit = True
                    break
            if hit:
                covered[dim] += 1
                n_routed += 1
            elif was_blocked:
                blocked[dim] += 1
        per_product_routed[slug] = n_routed

    total = len(slugs)
    print(f"{total} products\n")
    print(f"{'dimension':<14}{'routed':>8}{'':>3}{'blocked by bridge':>19}{'':>3}{'research':>10}")
    for dim in dimensions:
        c = covered[dim]
        b = blocked[dim]
        print(f"{dim:<14}{c:>8}{'':>3}{b:>19}{'':>3}{total - c:>10}")

    if hand_authored_routes:
        print()
        for dim, kinds in sorted(hand_authored_routes.items()):
            print(
                f"{dim}: {len(kinds)} hand-authored route(s) by declaration "
                f"({', '.join(sorted(kinds))}) — no machine source, so no coverage to count"
            )

    research_only = routing.get("research_only") or {}
    if research_only:
        print(f"\nresearch-only by declaration: {', '.join(research_only)}")

    none_routed = [s for s, n in per_product_routed.items() if n == 0]
    print(f"\n{len(none_routed)} of {total} products have NO routable dimension at all")
    if args.unrouted:
        for slug in sorted(none_routed):
            print(f"  {slug:<34}{category_of.get(slug, '?')}")
    elif none_routed:
        print(f"  e.g. {', '.join(sorted(none_routed)[:8])} ...  (--unrouted for the full list)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
