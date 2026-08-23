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
  adoption_route_band_sets   route x product type -> the band set that resolves it
  adoption_aggregation_rules the named aggregation rules, one row per rule

The bands themselves stay in `registry.adoption_bands`, produced by `serialize_rubric.py`.
`adoption_route_band_sets` is the join that says which of those band sets a given route
resolves to for a given product type — so evaluation does an ordinary join and abstains when
no row exists, rather than reading a `type:*` sentinel and reinterpreting it. The two modules
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
from build.vocabulary import ROUTABLE_INSTRUMENTS

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "build" / "registry"

TABLES: dict[str, tuple[str, ...]] = {
    # One row per route, carrying everything evaluation needs to route a signal without
    # reopening the YAML. Each column's derivation is documented in `adoption_routes` below;
    # that function IS the compiler's contract. The band set a route resolves to is NOT a
    # column here — it varies by product type, so it lives in `adoption_route_band_sets`.
    "adoption_routes": (
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
        "aggregation_rule_id",
        "cap",
        "cap_reason",
        "requires_evidence",
        "freshness_days",
        "abstain_rule",
        "vocabulary",
        "routing_policy_version",
    ),
    # A route with no scope row applies to every category; a scope row narrows it. Only
    # `semanticscholar.citation_count` declares one today (citations measure a benchmark's
    # reach better than downloads do), so it is the one route restricted to a category.
    "adoption_route_scopes": ("route_id", "scope_type", "scope_value"),
    # One row per valid route x product type combination, naming the band set that resolves
    # it. Evaluation joins this table and abstains when no row exists — hardware usage_volume
    # has no row because hardware is qualitative, which is the abstention, not a sentinel to
    # reinterpret. Every band_set_id here must resolve to an `adoption_bands` row.
    "adoption_route_band_sets": ("route_id", "product_type", "band_set_id"),
    # The named aggregation rules. `applies_to_instrument` is what binds a rule to a route:
    # a route's `aggregation_rule_id` is the rule whose instrument it matches, so the method
    # string is declared once here rather than copied onto every route it governs.
    "adoption_aggregation_rules": (
        "aggregation_rule_id",
        "method",
        "scope",
        "applies_to_instrument",
    ),
}

# The YAML's `signal_type` compiles to `instrument_type`; `metric_type` is DERIVED from the
# column. That derivation is part of the compiler's contract, not something evaluation
# infers — so the map lives here and a column the map does not cover is a hard error rather
# than a silent blank. `artifact_kind` is NOT hardcoded: it is read from the source's declared
# `artifact_key` in the `sources:` block, so `semanticscholar` compiles to its `arxiv` key and
# matches `registry.product_artifacts.artifact_kind` rather than a guessed `paper`.
_METRIC_TYPE = {
    "downloads_30d": "downloads",
    "citation_count": "citations",
    "stargazers_count": "stars",
}

# The authority values a route may declare. Authority is read from the route, not inferred:
# it is a routing decision and not a property the instrument name can be trusted to carry.
_AUTHORITIES = {"authoritative", "secondary", "fallback"}

# The dimension's declared abstention: when the authoritative signal is missing or unusable,
# produce NO evidence rather than fall through to a weaker source. Constant per route because
# the YAML states it once for the dimension, not per route.
_ABSTAIN_RULE = "produce_no_evidence"

# The recognized aggregation vocabulary. A rule combines a family's several artifacts, so
# `method` is how the per-artifact figures collapse to one and `scope` is what they are
# collapsed over. Both are validated against these sets rather than trusted: an unknown
# `method` or `scope` would publish a rule evaluation could not act on. `sum` is today's only
# declared method; `max` is admitted because it is the obvious alternative (the largest SKU
# rather than the total) and naming it keeps the check from reading as a one-value enum.
_AGG_METHODS = {"sum", "max"}
_AGG_SCOPES = {"artifacts"}


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


def _routes(routing: dict) -> list[dict]:
    return (((routing.get("dimensions") or {}).get("adoption")) or {}).get("routes") or []


def _route_id(route: dict) -> str:
    """A stable slug. A sourced route is identified by source.column, its natural join key;
    a null-source route has neither, so it is identified by the instrument it declares."""
    source = route.get("source") or ""
    column = route.get("column") or ""
    signal_type = route.get("signal_type") or ""
    return f"{source}.{column}" if source else signal_type


def adoption_aggregation_rules(routing: dict) -> tuple[list[dict], list[str]]:
    """The named aggregation rules, from the dimension's `aggregation` block.

    One row per declared rule. `scope` records what the aggregation is over — a family's
    several artifacts, not its categories or sources — and `applies_to_instrument` is what a
    route joins on to pick up its `aggregation_rule_id`, so the method lives here once.

    Everything that would make an aggregation wrong is an error, not a silent row: a rule with
    no id, a duplicate id, an unrecognized method or scope, an instrument outside the canonical
    vocabulary, or a second rule for one instrument. The last mattered most — the code that
    binds rules to routes builds a `{instrument: rule_id}` map, so a second `usage_volume` rule
    silently overwrote the first and pointed every usage route at whichever came last.
    """
    dimension = ((routing.get("dimensions") or {}).get("adoption")) or {}
    rows: list[dict] = []
    errors: list[str] = []
    seen_ids: set[str] = set()
    seen_instruments: set[str] = set()
    for index, rule in enumerate(dimension.get("aggregation") or []):
        rule_id = rule.get("rule_id", "")
        method = rule.get("method", "")
        scope = rule.get("scope", "")
        instrument = rule.get("applies_to_instrument", "")

        if not isinstance(rule_id, str) or not rule_id:
            errors.append(f"aggregation rule {index} declares no rule_id")
        elif rule_id in seen_ids:
            errors.append(f"aggregation rule {index} has a duplicate rule_id {rule_id!r}")
        else:
            seen_ids.add(rule_id)

        if method not in _AGG_METHODS:
            errors.append(
                f"aggregation rule {rule_id!r}: method {method!r} is not one of "
                f"{sorted(_AGG_METHODS)}"
            )
        if scope not in _AGG_SCOPES:
            errors.append(
                f"aggregation rule {rule_id!r}: scope {scope!r} is not one of "
                f"{sorted(_AGG_SCOPES)}"
            )
        if instrument not in ROUTABLE_INSTRUMENTS:
            errors.append(
                f"aggregation rule {rule_id!r}: applies_to_instrument {instrument!r} is not "
                f"one of {sorted(ROUTABLE_INSTRUMENTS)}"
            )
        elif instrument in seen_instruments:
            errors.append(
                f"aggregation rule {rule_id!r}: a second rule for instrument {instrument!r}; "
                f"an instrument may be governed by at most one rule"
            )
        else:
            seen_instruments.add(instrument)

        rows.append(
            {
                "aggregation_rule_id": rule_id,
                "method": method,
                "scope": scope,
                "applies_to_instrument": instrument,
            }
        )
    return rows, errors


def adoption_routes(routing: dict, aggregation_by_instrument: dict[str, str]) -> tuple[list[dict], list[str]]:
    """One row per adoption route, in the YAML's precedence order.

    The derivation of every column is documented inline; this is the compiler's contract.
    Everything here that would make routing wrong is an error, not a warning: a route with no
    instrument, a source the `sources:` block does not declare, a column with no metric_type,
    a missing or invalid authority, or a duplicate route_id.
    """
    routes = _routes(routing)
    sources = routing.get("sources") or {}
    version = str(routing.get("version", ""))

    rows: list[dict] = []
    errors: list[str] = []
    seen_ids: set[str] = set()

    for index, route in enumerate(routes):
        # `source` is nullable: two routes are hand-authored and read no machine source, and
        # a null there compiles to the empty string rather than the literal 'None'.
        source = route.get("source") or ""
        column = route.get("column") or ""
        signal_type = route.get("signal_type") or ""

        if not signal_type:
            errors.append(f"adoption route {index} declares no signal_type and cannot be routed")
            continue

        route_id = _route_id(route)
        if route_id in seen_ids:
            errors.append(f"adoption route {index} has a duplicate route_id {route_id!r}")
            continue
        seen_ids.add(route_id)

        # The instrument must be one the corpus recognizes AND can route. `signal_type` is
        # declared on the route and is not derivable from anything else, so a typo like `mystery`
        # would compile an eighth route with no error until it is checked against the canonical
        # vocabulary build/vocabulary.py owns. `unknown` is in that vocabulary — a recorded score
        # with no routable instrument — but it is not a routable instrument, so routes are gated
        # against the narrower ROUTABLE_INSTRUMENTS, not the full SIGNAL_TYPES validate.py uses.
        if signal_type not in ROUTABLE_INSTRUMENTS:
            errors.append(
                f"route {route_id!r}: signal_type {signal_type!r} is not one of "
                f"{sorted(ROUTABLE_INSTRUMENTS)}"
            )

        # A route's source, column and hand_authored flag are not independent: a sourced route
        # reads a machine column and is fetched, so it must name a nonempty column and must not
        # claim to be hand-authored; a source-less route is hand-read, so it must declare
        # `hand_authored: true` and name no column. A `huggingface_model.` route id with an empty
        # column, or a hand_authored flag on a fetched source, is a contradiction, not a blank.
        if source:
            if not column:
                errors.append(
                    f"route {route_id!r}: a sourced route must declare a nonempty column"
                )
            if route.get("hand_authored"):
                errors.append(
                    f"route {route_id!r}: a sourced route must not be hand_authored"
                )
        else:
            if not route.get("hand_authored"):
                errors.append(
                    f"route {route_id!r}: a route with no source must be hand_authored"
                )
            if column:
                errors.append(
                    f"route {route_id!r}: a route with no source must not declare a column"
                )

        # `artifact_kind` is READ from the source's declared `artifact_key`, not guessed from a
        # hardcoded map — so `semanticscholar` compiles to `arxiv` and matches the registry. A
        # null-source route names no artifact, so it is empty; a non-null source the `sources:`
        # block does not declare, or one with no `artifact_key`, is an error, not a blank.
        artifact_kind = ""
        if source:
            source_spec = sources.get(source)
            if source_spec is None:
                errors.append(
                    f"route {route_id!r}: source {source!r} is not declared in the `sources:` block"
                )
            elif not source_spec.get("artifact_key"):
                errors.append(
                    f"route {route_id!r}: source {source!r} declares no `artifact_key`"
                )
            else:
                artifact_kind = source_spec["artifact_key"]

        # `metric_type` is derived from the column. A hand-authored route reads no column, so
        # it is empty; a column the map does not cover is an error rather than a silent blank.
        metric_type = ""
        if column:
            metric_type = _METRIC_TYPE.get(column, "")
            if not metric_type:
                errors.append(f"route {route_id!r}: column {column!r} has no metric_type mapping")

        # `authority` is declared on the route and compiled, not inferred from the instrument.
        authority = route.get("authority") or ""
        if authority not in _AUTHORITIES:
            errors.append(
                f"route {route_id!r}: authority {authority!r} is missing or not one of "
                f"{sorted(_AUTHORITIES)}"
            )

        rows.append(
            {
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
                # The rule whose `applies_to_instrument` matches this route's instrument; the
                # method string is not copied here, only its rule id. Empty when no rule governs
                # the instrument (everything but usage_volume today).
                "aggregation_rule_id": aggregation_by_instrument.get(signal_type, ""),
                # `cap`, `cap_reason`, `requires_evidence` and `vocabulary` are semantic and
                # compile; the prose that explains the rest — note, attribution_note,
                # vocabulary_note — is documentation-only and does not.
                "cap": route.get("cap") if route.get("cap") is not None else "",
                "cap_reason": " ".join(str(route.get("cap_because", "")).split()),
                "requires_evidence": "|".join(route.get("requires_evidence") or []),
                # Not declared per route in the YAML today; kept as a column so a per-route
                # freshness threshold has somewhere to land without a schema change.
                "freshness_days": "",
                "abstain_rule": _ABSTAIN_RULE,
                "vocabulary": "|".join(route.get("vocabulary") or []),
                "routing_policy_version": version,
            }
        )
    return rows, errors


def adoption_route_scopes(routing: dict, categories: dict) -> tuple[list[dict], list[str]]:
    """Route -> the category it is scoped to, from `applies_to_categories`.

    A route with no `applies_to_categories` emits no rows and applies to every category; a
    scope row narrows it. Emitted one row per category so a join never splits a string.

    `categories` is required, not optional: skipping it would silently skip the dangling-scope
    check, so the declared slugs are always threaded in (from `main()` or a test). A scope names
    a category by slug, so a slug no `sources/categories/` file declares is a dangling reference
    — the scope would narrow the route to a category that does not exist — and is a hard error.
    Duplicate `(route_id, category)` pairs are also an error: the table's grain is
    `(route_id, scope_type, scope_value)`, so a repeated category would publish two identical
    rows the grain forbids.
    """
    valid = set(categories)
    rows: list[dict] = []
    errors: list[str] = []
    seen: set[tuple[str, str, str]] = set()
    for route in _routes(routing):
        route_id = _route_id(route)
        for category in route.get("applies_to_categories") or []:
            if category not in valid:
                errors.append(
                    f"route {route_id!r}: applies_to_categories {category!r} is not a declared "
                    f"category (no sources/categories/{category}.yaml)"
                )
            key = (route_id, "category", category)
            if key in seen:
                errors.append(
                    f"route {route_id!r}: duplicate applies_to_categories scope {category!r}; "
                    f"the (route_id, scope_type, scope_value) grain forbids repeats"
                )
                continue
            seen.add(key)
            rows.append(
                {"route_id": route_id, "scope_type": "category", "scope_value": category}
            )
    return rows, errors


def adoption_route_band_sets(routing: dict, rubrics: dict) -> tuple[list[dict], list[str]]:
    """One row per valid route x product type, naming the band set that resolves it.

    This is what replaces the `type:*` sentinel `adoption_routes` used to carry: evaluation
    joins this table and abstains when no row exists, rather than reading a sentinel and
    resolving bands itself. The derivation runs off the shared rubrics:

      - a `usage_volume` route resolves per product type, so it emits `type:<P>` for each type
        whose rubric declares usage_volume bands. Hardware is qualitative and declares none, so
        it gets no row — and its absence IS the abstention, correctly.
      - `stars_fallback` and `active_users` carry a scale that is a property of the INSTRUMENT
        and type-independent, so each emits `route:<signal_type>` for EVERY product type.
      - `reported_traction` has a vocabulary and no bands, so it resolves to nothing and emits
        no row.

    Referential integrity is enforced here rather than trusted: every band_set_id emitted must
    resolve to an `adoption_bands` row, so a scale renamed on one side without the other fails
    the serializer instead of publishing a dangling join.
    """
    # Deferred import: serialize_rubric imports band_set_id from this module, so importing it at
    # module scope would be a cycle. By call time both modules are fully loaded.
    from build.serialize_rubric import adoption_bands, route_bands

    band_rows, _ = adoption_bands(rubrics)
    route_scale_rows, _ = route_bands(routing)
    valid_band_ids = {b["band_set_id"] for b in band_rows + route_scale_rows}

    all_types = sorted(rubrics.keys())
    banded_types = sorted(
        t for t, r in rubrics.items() if ((r or {}).get("adoption") or {}).get("bands")
    )

    rows: list[dict] = []
    errors: list[str] = []
    for route in _routes(routing):
        signal_type = route.get("signal_type") or ""
        route_id = _route_id(route)
        if signal_type == "usage_volume":
            pairs = [(p, band_set_id("type", p)) for p in banded_types]
        elif signal_type in ("stars_fallback", "active_users"):
            pairs = [(p, band_set_id("route", signal_type)) for p in all_types]
        else:
            pairs = []
        for product_type, band_set in pairs:
            if band_set not in valid_band_ids:
                errors.append(
                    f"route {route_id!r}: band_set_id {band_set!r} for product type "
                    f"{product_type!r} resolves to no adoption_bands row"
                )
            rows.append(
                {"route_id": route_id, "product_type": product_type, "band_set_id": band_set}
            )
    return rows, errors


def build_routing(
    routing: dict, rubrics: dict, categories: dict
) -> tuple[dict[str, list[dict]], list[str], list[str]]:
    """Return (tables, errors, warnings), a pure function of the parsed routing YAML, the
    shared rubrics and the declared categories.

    `rubrics` and `categories` are threaded in rather than read here so the function stays pure
    and the tests can pass them inline. All three are required: making `categories` optional
    would let a caller silently skip the dangling-scope check, so it is a positional argument
    with no default. Errors would make routing wrong — an unroutable route, an unknown
    derivation, a duplicate id, a dangling band-set join, a scope naming a category that does
    not exist, a duplicate scope; warnings are genuine coverage facts.
    """
    tables: dict[str, list[dict]] = {name: [] for name in TABLES}

    aggregation_rows, aggregation_errors = adoption_aggregation_rules(routing)
    aggregation_by_instrument = {
        r["applies_to_instrument"]: r["aggregation_rule_id"]
        for r in aggregation_rows
        if r["applies_to_instrument"]
    }

    routes, route_errors = adoption_routes(routing, aggregation_by_instrument)
    scope_rows, scope_errors = adoption_route_scopes(routing, categories)
    band_set_rows, band_set_errors = adoption_route_band_sets(routing, rubrics)

    tables["adoption_routes"] = routes
    tables["adoption_route_scopes"] = scope_rows
    tables["adoption_route_band_sets"] = band_set_rows
    tables["adoption_aggregation_rules"] = aggregation_rows

    errors = aggregation_errors + route_errors + scope_errors + band_set_errors
    warnings: list[str] = []

    # Referential integrity holds by construction — a route's aggregation_rule_id comes from
    # the {instrument: rule_id} map built off these same rows — but guarded anyway so a future
    # change to how the id is assigned cannot publish a route pointing at a rule that is gone.
    rule_ids = {r["aggregation_rule_id"] for r in aggregation_rows}
    for route in routes:
        rule_id = route["aggregation_rule_id"]
        if rule_id and rule_id not in rule_ids:
            errors.append(
                f"route {route['route_id']!r}: aggregation_rule_id {rule_id!r} references no "
                f"aggregation rule"
            )

    if not routes:
        errors.append("signal_routing.yaml declares no adoption routes, so there is nothing to route with")

    return tables, errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate only, write nothing")
    parser.add_argument("--out", type=Path, default=OUT_DIR, help="output directory")
    args = parser.parse_args()

    # The shared rubrics carry the usage_volume band sets each product type declares, which the
    # route x product-type table is derived against. Loaded the same way serialize_rubric does.
    from build.validate import load_sources

    sources = load_sources(ROOT)
    rubrics = sources.get("rubrics") or {}
    # The declared category slugs, so a route's `applies_to_categories` scope naming a category
    # no file declares is a hard error rather than a scope row nothing joins to.
    categories = sources.get("categories") or {}
    tables, errors, warnings = build_routing(load_routing(ROOT), rubrics, categories)

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
