"""Compile the adoption routing semantics from signal_routing.yaml to flat CSVs.

`sources/signal_routing.yaml` declares, per scoring dimension, which machine signal is
authoritative and how a value read off that signal becomes a band. `serialize_rubric.py`
already exports the two banded scales that live on their own routes; everything else about
adoption routing — route order, artifact applicability, authority, fallback status, caps,
required evidence and the abstention rule — was declared in the YAML and exported nowhere.

That is an AD-1 violation waiting to happen: any evaluation SQL that needs to know which
route is authoritative would have to reinterpret the YAML independently, which is a second
implementation of routing semantics living in the warehouse. This module is the one
implementation. It reads the YAML, derives the normalized facts below, and evaluation reads
those and never reinterprets the source. A route this compiler cannot express is a compiler
bug to fix, not a case for evaluation to special-case.

Emitted tables (CSVs into build/registry/, alongside the registry's and rubric's own):

  adoption_routes            one row per route, in precedence order
  adoption_route_scopes      route -> the category/product type it is scoped to
  adoption_aggregation_rules the dimension-level aggregation (sum_across_artifacts)

The bands themselves stay in `registry.adoption_bands`, produced by `serialize_rubric.py`;
`adoption_routes.band_set_id` points at the band rows a route resolves to. The two modules
share the id logic here (`band_set_id`) so they cannot spell that link two different ways.

Usage:
    uv run python -m build.serialize_routing            # write CSVs
    uv run python -m build.serialize_routing --check    # validate, write nothing
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from build.serialize_registry import write_tables

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "build" / "registry"

TABLES: dict[str, tuple[str, ...]] = {
    # One row per route, carrying everything evaluation needs to route a signal without
    # reopening the YAML. Each column's derivation is documented in `adoption_routes` below;
    # that function IS the compiler's contract.
    "adoption_routes": (
        "declaration_version_id",
        "route_id",
        "route_order",
        "source",
        "source_column",
        "artifact_kind",
        "metric_type",
        "instrument_type",
        "authority",
        "hand_authored",
        "confidence",
        "unit",
        "aggregation_method",
        "band_set_id",
        "cap",
        "requires_evidence",
        "freshness_days",
        "abstain_rule",
        "vocabulary",
        "policy_version",
    ),
    # A route with no scope row applies to every category; a scope row narrows it. Only
    # `semanticscholar.citation_count` declares one today (citations measure a benchmark's
    # reach better than downloads do), so it is the one route restricted to a category.
    "adoption_route_scopes": ("route_id", "scope_type", "scope_value"),
    # The dimension-level aggregation. `sum_across_artifacts: true` means a family's several
    # SKUs sum rather than the largest winning, because the map's unit is the family.
    "adoption_aggregation_rules": ("dimension", "aggregation_method", "scope"),
}

# The YAML's `signal_type` compiles to `instrument_type`; `artifact_kind` and `metric_type`
# are DERIVED from source and column. That derivation is part of the compiler's contract, not
# something evaluation infers — so the maps live here and a source or column the maps do not
# cover raises a warning rather than emitting a silent blank.
_ARTIFACT_KIND = {
    "huggingface_model": "model",
    "huggingface_dataset": "dataset",
    "pypi": "package",
    "github": "repo",
    "semanticscholar": "paper",
}
_METRIC_TYPE = {
    "downloads_30d": "downloads",
    "citation_count": "citations",
    "stargazers_count": "stars",
}
# Authority is a property of the instrument. `usage_volume` counts real use and is
# authoritative; `active_users` is a hand-read disclosure standing in for a count, so
# secondary; `stars_fallback` and `reported_traction` are the last resorts before abstention.
_AUTHORITY = {
    "usage_volume": "authoritative",
    "stars_fallback": "fallback",
    "active_users": "secondary",
    "reported_traction": "fallback",
}

# The dimension's declared abstention: when the authoritative signal is missing or unusable,
# produce NO evidence rather than fall through to a weaker source. Constant per route because
# the YAML states it once for the dimension, not per route.
_ABSTAIN_RULE = "produce_no_evidence"


def band_set_id(scope: str, value: str) -> str:
    """Compose the id that links a route to its band rows in `registry.adoption_bands`.

    `scope` is 'route' for a scale declared on its own route — stars and active users, whose
    scale is a property of the INSTRUMENT and so is emitted once — and 'type' for the
    per-product-type usage_volume ladders. Defined here and imported by `serialize_rubric`,
    which emits the band rows, so the two modules cannot disagree about how the link is spelled.
    """
    return f"{scope}:{value}"


def load_routing(root: Path) -> dict:
    return yaml.safe_load((root / "sources" / "signal_routing.yaml").read_text()) or {}


def adoption_routes(routing: dict) -> tuple[list[dict], list[str], list[str]]:
    """One row per adoption route, in the YAML's precedence order.

    The derivation of every column is documented inline; this is the compiler's contract.
    Warnings flag a source or instrument the derivation maps do not cover — a coverage gap
    rather than a broken score — and errors flag a route with no signal_type, which cannot
    be routed at all.
    """
    dimension = ((routing.get("dimensions") or {}).get("adoption")) or {}
    routes = dimension.get("routes") or []
    version = str(routing.get("version", ""))

    rows: list[dict] = []
    errors: list[str] = []
    warnings: list[str] = []

    for index, route in enumerate(routes):
        # `source` is nullable: two routes are hand-authored and read no machine source, and
        # a null there compiles to the empty string rather than the literal 'None'.
        source = route.get("source") or ""
        column = route.get("column") or ""
        signal_type = route.get("signal_type") or ""

        if not signal_type:
            errors.append(f"adoption route {index} declares no signal_type and cannot be routed")
            continue

        # `route_id` is a stable slug. A sourced route is identified by source.column, its
        # natural join key; a null-source route has neither, so it is identified by the
        # instrument it declares — `active_users`, `reported_traction`.
        route_id = f"{source}.{column}" if source else signal_type

        # `artifact_kind` and `metric_type` are derived, not read. A hand-authored route reads
        # no column, so `metric_type` is empty; a null-source route names no artifact, so
        # `artifact_kind` is empty. A non-null source or a column the maps do not cover is a
        # coverage warning, so a new source declares its mapping here rather than shipping blank.
        artifact_kind = _ARTIFACT_KIND.get(source, "")
        if source and not artifact_kind:
            warnings.append(f"route {route_id!r}: source {source!r} has no artifact_kind mapping")
        metric_type = _METRIC_TYPE.get(column, "")
        if column and not metric_type:
            warnings.append(f"route {route_id!r}: column {column!r} has no metric_type mapping")

        authority = _AUTHORITY.get(signal_type, "")
        if not authority:
            warnings.append(f"route {route_id!r}: instrument {signal_type!r} has no declared authority")

        # A usage_volume route sums across a family's artifacts (the dimension's rule); every
        # other instrument reads one figure and does not aggregate.
        aggregation_method = "sum" if signal_type == "usage_volume" else "none"

        # `band_set_id` points at the band rows the route resolves to. A route with inline
        # bands owns a per-INSTRUMENT scale, addressed `route:<signal_type>`. A usage_volume
        # route resolves its bands per PRODUCT TYPE at evaluation, so it points at the `type:*`
        # sentinel rather than any one type. An instrument with a vocabulary and no bands
        # (reported_traction) points at nothing.
        if route.get("bands"):
            band_set = band_set_id("route", signal_type)
        elif signal_type == "usage_volume":
            band_set = band_set_id("type", "*")
        else:
            band_set = ""

        rows.append(
            {
                "declaration_version_id": version,
                "route_id": route_id,
                "route_order": index + 1,
                "source": source,
                "source_column": column,
                "artifact_kind": artifact_kind,
                "metric_type": metric_type,
                "instrument_type": signal_type,
                "authority": authority,
                "hand_authored": bool(route.get("hand_authored", False)),
                "confidence": route.get("confidence", ""),
                "unit": route.get("unit") or "",
                "aggregation_method": aggregation_method,
                "band_set_id": band_set,
                # `cap`, `requires_evidence` and `vocabulary` are semantic and compile; the
                # prose that explains each — cap_because, note, attribution_note,
                # vocabulary_note — is documentation-only and does not.
                "cap": route.get("cap") if route.get("cap") is not None else "",
                "requires_evidence": "|".join(route.get("requires_evidence") or []),
                # Not declared per route in the YAML today; kept as a column so a per-route
                # freshness threshold has somewhere to land without a schema change.
                "freshness_days": "",
                "abstain_rule": _ABSTAIN_RULE,
                "vocabulary": "|".join(route.get("vocabulary") or []),
                "policy_version": version,
            }
        )
    return rows, errors, warnings


def adoption_route_scopes(routing: dict) -> list[dict]:
    """Route -> the category it is scoped to, from `applies_to_categories`.

    A route with no `applies_to_categories` emits no rows and applies to every category; a
    scope row narrows it. Emitted one row per category so a join never splits a string.
    """
    routes = (((routing.get("dimensions") or {}).get("adoption")) or {}).get("routes") or []
    rows: list[dict] = []
    for route in routes:
        signal_type = route.get("signal_type") or ""
        source = route.get("source") or ""
        column = route.get("column") or ""
        route_id = f"{source}.{column}" if source else signal_type
        for category in route.get("applies_to_categories") or []:
            rows.append(
                {"route_id": route_id, "scope_type": "category", "scope_value": category}
            )
    return rows


def adoption_aggregation_rules(routing: dict) -> list[dict]:
    """The dimension-level aggregation, from `sum_across_artifacts`.

    `scope: artifacts` records what the sum is over: a family's several artifacts, not its
    categories or sources. Emitted only when the flag is set, so the table's presence is the
    declaration.
    """
    dimension = ((routing.get("dimensions") or {}).get("adoption")) or {}
    if not dimension.get("sum_across_artifacts"):
        return []
    return [{"dimension": "adoption", "aggregation_method": "sum", "scope": "artifacts"}]


def build_routing(routing: dict) -> tuple[dict[str, list[dict]], list[str], list[str]]:
    """Return (tables, errors, warnings), a pure function of the parsed routing YAML.

    Errors would make routing wrong — a route with no instrument. Warnings are coverage
    facts — a source or instrument whose derivation the maps do not yet cover.
    """
    tables: dict[str, list[dict]] = {name: [] for name in TABLES}

    routes, errors, warnings = adoption_routes(routing)
    tables["adoption_routes"] = routes
    tables["adoption_route_scopes"] = adoption_route_scopes(routing)
    tables["adoption_aggregation_rules"] = adoption_aggregation_rules(routing)

    if not routes:
        errors.append("signal_routing.yaml declares no adoption routes, so there is nothing to route with")

    return tables, errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate only, write nothing")
    parser.add_argument("--out", type=Path, default=OUT_DIR, help="output directory")
    args = parser.parse_args()

    tables, errors, warnings = build_routing(load_routing(ROOT))

    for name in TABLES:
        print(f"  {name:<27} {len(tables[name]):>5} rows")

    if warnings:
        print(f"\n{len(warnings)} warning(s) — coverage, nothing broken:")
        for warning in warnings:
            print(f"  - {warning}")

    if errors:
        print(f"\n{len(errors)} error(s) — these would make routing wrong:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    if args.check:
        print("\ncheck only: nothing written")
        return 0

    write_tables(tables, args.out, TABLES)
    print(f"\nwrote {len(TABLES)} CSVs to {args.out.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
