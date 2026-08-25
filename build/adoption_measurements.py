"""Aggregate artifact-level adoption observations to the product level — the evaluation rollup.

`observations.product_adoption_current` is ARTIFACT-level and band-free (§4.3): one row per
`(product_slug, artifact_kind, artifact_id, channel, metric_type, measurement_window_days)`,
carrying only the raw fact. Recorded assessments are PRODUCT-level. Something must aggregate one
into the other, and reconciliation must not do it implicitly — that would put aggregation
semantics inside the gate that is supposed to check them (§4.4). This module is that step:
`currentai.evaluation.product_adoption_measurements`.

## The flow this owns (§4.4)

    artifact observations  ->  route selection      (registry.adoption_routes, precedence)
                           ->  product aggregation  (this table)
                           ->  banding              (registry.adoption_bands)

Route selection, aggregation and banding are all read from the compiled routing tables
(`build/serialize_routing.py` and `build/serialize_rubric.py`); this module reinterprets none of
them. A routing fact this builder needs but cannot read is a compiler bug to fix at the source,
not a special case here — the same contract `serialize_routing` states for evaluation SQL.

## Grain and identities

One row per `(declaration_version_id, observation_snapshot_id, product_slug, category_slug,
route_id)`. It keys on BOTH release identities because a rollup depends on WHICH declarations
selected the route (the category roster, the product type) and on WHICH measurements it summed.
Both are derived at run time (`build/declaration_version.py`, `build/observation_snapshot.py`)
and are NOT stored — a full-refresh table's content changes every run, so a frozen value goes
stale. They are inputs to the pure builder here so the aggregation/banding logic stays a pure
function of (observations, routing, bands) and the goldens can pin it with fixed test identities;
the CLI wires in the real run-time values.

## Route selection

For each product, the winning route is the FIRST route in precedence order (`route_order`) that
is (a) a usable machine route — it names a source with a real table; the two hand-authored routes
(`active_users`, `reported_traction`) read no machine signal and never win here — (b) in scope
for the product's category (`registry.adoption_route_scopes`; a route with no scope row applies to
every category), and (c) has at least one observation for the product matching the route's
`(artifact_kind, metric_type)`. Higher-precedence routes with no observation are skipped, exactly
as `build/check_routing.py` selects a route by declared artifact — here by an observed one.

## Aggregation

The winning route's contributing observations (all of the product's observations matching the
route's `(artifact_kind, metric_type)`) are combined by the aggregation rule bound to the route's
instrument (`registry.adoption_aggregation_rules`): `usage_volume` sums across a family's
artifacts, since the map's unit is the family. A route whose instrument declares NO rule and has
exactly one contributing observation uses that value directly. A rule-less route with MORE than
one contributing observation is an UNDEFINED aggregation — today only `stars_fallback` can reach
this, for the handful of products declaring several GitHub repositories — and the builder ABSTAINS
(null value, null level) rather than invent a sum or a max the routing source never declared. The
row is still emitted, carrying the contributing ids and `aggregation_method = ''`, so the gap is
visible rather than papered over. Declaring a stars aggregation rule in `signal_routing.yaml`
would resolve it; that is a routing-semantics decision for the source, not a default to guess here.

## Banding

The aggregate value is banded by the band set the winning route resolves to for the product's
type (`registry.adoption_route_band_sets` -> `registry.adoption_bands`): the highest level whose
exclusive lower bound `above` is below the value. A `(route, product_type)` pair with no band set
row abstains (null level) — hardware declares no usage ladder, and that absence IS the abstention
(§4.4). The stars cap is already baked into its band set (levels stop at 3), so no separate cap
logic lives here.

## Freshness

`measurement_as_of` is the MINIMUM `observed_at` across the contributing observations: an aggregate
is only as current as its stalest input, so the conservative bound is the honest one. Run binding
is blocked on #355, so these observations carry no `source_run_id`; that is reconciliation's
concern (an unbound measurement is `source_unavailable`, §4.3), not this table's.

Usage:
    uv run python -m build.adoption_measurements            # over the committed baseline
    uv run python -m build.adoption_measurements --json     # same, machine-readable rows
"""

from __future__ import annotations

import argparse
import datetime
import json
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# The measurement columns in table order. contributing_observation_ids is a list in the Python
# row; a flat serialization joins it with '|' (see canonical_row).
COLUMNS: tuple[str, ...] = (
    "declaration_version_id",
    "observation_snapshot_id",
    "product_slug",
    "category_slug",
    "product_type",
    "route_id",
    "channel",
    "metric_type",
    "instrument_type",
    "aggregation_method",
    "contributing_observation_ids",
    "raw_value",
    "unit",
    "measurement_window_days",
    "band_set_id",
    "measured_level",
    "measured_reach",
    "route_authority",
    "measurement_as_of",
)


def _category_of(categories: Mapping[str, dict]) -> dict[str, str]:
    """product slug -> the one category whose roster lists it (a product is in exactly one)."""
    out: dict[str, str] = {}
    for cat in categories.values():
        slug = cat.get("name")
        for product in cat.get("products") or []:
            out[product] = slug
    return out


def _band_index(band_rows: Iterable[Mapping]) -> dict[str, list[tuple[int, int, str]]]:
    """band_set_id -> [(above, level, reach)] sorted by level ascending."""
    index: dict[str, list[tuple[int, int, str]]] = {}
    for row in band_rows:
        index.setdefault(row["band_set_id"], []).append(
            (int(row["above"]), int(row["level"]), str(row.get("reach") or ""))
        )
    for rows in index.values():
        rows.sort(key=lambda item: item[1])
    return index


def _band_for(index: Mapping[str, list[tuple[int, int, str]]], band_set_id: str, value: int):
    """The highest (level, reach) whose exclusive lower bound is below value, or (None, None)."""
    best: tuple[int | None, str | None] = (None, None)
    for above, level, reach in index.get(band_set_id, []):
        if value > above:
            best = (level, reach)
    return best


def measurements(
    observation_rows: Iterable[Mapping],
    routing_tables: Mapping[str, Sequence[Mapping]],
    band_rows: Iterable[Mapping],
    category_of: Mapping[str, str],
    *,
    declaration_version_id: str,
    observation_snapshot_id: str,
) -> list[dict]:
    """The product-level rollup as a pure function of its inputs (identities passed in).

    ``routing_tables`` is the output of ``build.serialize_routing.build_routing`` —
    ``adoption_routes``, ``adoption_route_scopes``, ``adoption_route_band_sets`` and
    ``adoption_aggregation_rules``. ``band_rows`` is ``adoption_bands`` + ``route_bands``.
    """
    routes = sorted(routing_tables["adoption_routes"], key=lambda r: r["route_order"])
    method_by_rule = {
        r["aggregation_rule_id"]: r["method"] for r in routing_tables["adoption_aggregation_rules"]
    }
    scopes: dict[str, set[str]] = {}
    for row in routing_tables["adoption_route_scopes"]:
        scopes.setdefault(row["route_id"], set()).add(row["scope_value"])
    band_set_of: dict[tuple[str, str], str] = {
        (row["route_id"], row["product_type"]): row["band_set_id"]
        for row in routing_tables["adoption_route_band_sets"]
    }
    band_index = _band_index(band_rows)

    # Only machine routes with a real source can win on an observation; the hand-authored routes
    # read no machine signal. This mirrors build/check_routing.route_usable without the bridge
    # cases, which no adoption source route hits.
    machine_routes = [r for r in routes if r["source"]]

    by_product: dict[str, list[Mapping]] = {}
    for obs in observation_rows:
        by_product.setdefault(obs["product_slug"], []).append(obs)

    rows: list[dict] = []
    for product_slug in sorted(by_product):
        product_obs = by_product[product_slug]
        product_type = product_obs[0]["product_type"]
        category_slug = category_of.get(product_slug)

        for route in machine_routes:
            scope = scopes.get(route["route_id"])
            if scope is not None and category_slug not in scope:
                continue
            contributing = [
                o
                for o in product_obs
                if o["artifact_kind"] == route["artifact_kind"]
                and o["metric_type"] == route["metric_type"]
            ]
            if not contributing:
                continue

            # This route wins. Aggregate its contributing observations.
            method = method_by_rule.get(route["aggregation_rule_id"], "")
            values = [int(o["raw_value"]) for o in contributing]
            if method == "sum":
                raw_value: int | None = sum(values)
            elif method == "max":
                raw_value = max(values)
            elif len(contributing) == 1:
                raw_value = values[0]
            else:
                # A rule-less route with several contributing artifacts: aggregation is undefined
                # by the routing source, so abstain rather than fabricate one (see module doc).
                raw_value = None

            band_set_id = band_set_of.get((route["route_id"], product_type), "")
            if raw_value is None or not band_set_id:
                measured_level, measured_reach = None, None
            else:
                measured_level, measured_reach = _band_for(band_index, band_set_id, raw_value)

            observed = [o["observed_at"] for o in contributing]
            rows.append(
                {
                    "declaration_version_id": declaration_version_id,
                    "observation_snapshot_id": observation_snapshot_id,
                    "product_slug": product_slug,
                    "category_slug": category_slug,
                    "product_type": product_type,
                    "route_id": route["route_id"],
                    "channel": contributing[0]["channel"],
                    "metric_type": route["metric_type"],
                    "instrument_type": route["instrument_type"],
                    "aggregation_method": method,
                    "contributing_observation_ids": sorted(o["observation_id"] for o in contributing),
                    "raw_value": raw_value,
                    "unit": contributing[0]["unit"],
                    "measurement_window_days": contributing[0]["measurement_window_days"],
                    "band_set_id": band_set_id,
                    "measured_level": measured_level,
                    "measured_reach": measured_reach,
                    "route_authority": route["authority"],
                    "measurement_as_of": min(observed) if observed else None,
                }
            )
            break  # winner found; do not consider lower-precedence routes

    rows.sort(key=lambda r: (r["product_slug"], r["category_slug"] or "", r["route_id"]))
    return rows


def canonical_row(row: Mapping) -> str:
    """A flat, deterministic serialization of one measurement row for digesting/emitting."""
    flat = dict(row)
    flat["contributing_observation_ids"] = "|".join(row["contributing_observation_ids"])
    if isinstance(flat.get("measurement_as_of"), datetime.datetime):
        flat["measurement_as_of"] = flat["measurement_as_of"].isoformat()
    return json.dumps({k: flat.get(k) for k in COLUMNS}, separators=(",", ":"), sort_keys=True)


# --- inputs assembled over the committed baseline -------------------------------


def load_inputs(root: Path | None = None):
    """Return (routing_tables, band_rows, category_of) from the committed sources."""
    from build.serialize_routing import build_routing, load_routing
    from build.serialize_rubric import adoption_bands, route_bands
    from build.validate import load_sources

    base = root or ROOT
    src = load_sources(base)
    routing = load_routing(base)
    tables, errors, _ = build_routing(routing, src["rubrics"], src["categories"])
    if errors:
        raise RuntimeError("routing compiler errors: " + "; ".join(errors))
    band_rows = adoption_bands(src["rubrics"])[0] + route_bands(routing)[0]
    return tables, band_rows, _category_of(src["categories"])


def resolve_over_baseline(root: Path | None = None, allow_dirty: bool = False) -> list[dict]:
    """Build the measurements over the immutable Phase-2 baseline, stamped with real identities."""
    from build.declaration_version import resolve as resolve_declaration
    from build.observation_snapshot import observation_snapshot_id, rows_from_parquet

    base = root or ROOT
    observation_rows = rows_from_parquet()
    tables, band_rows, category_of = load_inputs(base)
    return measurements(
        observation_rows,
        tables,
        band_rows,
        category_of,
        declaration_version_id=resolve_declaration(base, allow_dirty=allow_dirty)[
            "declaration_version_id"
        ],
        observation_snapshot_id=observation_snapshot_id(observation_rows),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit the measurement rows as JSON")
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="stamp a diagnostic declaration_version_id over a dirty worktree",
    )
    args = parser.parse_args()

    rows = resolve_over_baseline(allow_dirty=args.allow_dirty)
    if args.json:
        print("\n".join(canonical_row(row) for row in rows))
        return 0

    banded = sum(1 for r in rows if r["measured_level"] is not None)
    abstained = len(rows) - banded
    print(f"measurement rows        {len(rows)}")
    print(f"  banded                {banded}")
    print(f"  abstained (null level){abstained:>6}")
    by_route: dict[str, int] = {}
    for row in rows:
        by_route[row["route_id"]] = by_route.get(row["route_id"], 0) + 1
    print("by winning route:")
    for route_id in sorted(by_route):
        print(f"  {route_id:<32}{by_route[route_id]:>5}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
