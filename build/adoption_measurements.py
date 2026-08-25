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
them.

## Route selection is by DECLARED ARTIFACTS, and never falls through

The winning route is the first route, in precedence order (`route_order`), that the product's
DECLARATIONS make applicable — it names an artifact kind the product declares
(`registry.product_artifacts`) and is in scope for the product's category
(`registry.adoption_route_scopes`). Applicability is a fact about declarations, NOT about which
observations happened to arrive. Once that winning route is fixed, the builder looks for an
observation on THAT route only. If the authoritative route's observation is missing, the product
is simply not measured — the builder does NOT fall through to a weaker route. Falling through is
the silent substitution `signal_routing.yaml` exists to prevent: a product that declares a PyPI
package must never be scored on GitHub stars merely because its PyPI download was not collected
this run. A product whose winning route was not observed produces no measurement row here; its
unmeasured outcome is recorded in `evaluation.adoption_reconciliation`, which covers every
recorded assessment.

## Aggregation

The winning route's contributing observations (all of the product's observations matching the
route's `(artifact_kind, metric_type)`) are combined by the aggregation rule bound to the route's
instrument (`registry.adoption_aggregation_rules`): both `usage_volume` and `stars_fallback` sum
across a family's artifacts, since the map's unit is the family. A route whose instrument declares
no rule and has exactly one contributing observation uses that value directly; a rule-less route
with more than one contributing observation would be an undefined aggregation and abstains rather
than invent one (no route reaches this today — both routable instruments with a machine table
declare a sum rule).

Numbers are preserved, never truncated: a `raw_value` is a finite `int` or `float` (bool and
non-finite rejected), carried through the sum and the band comparison as-is, so `1000.9` bands on
its real magnitude rather than a floored `1000`.

## Banding

The aggregate value is banded by the band set the winning route resolves to for the product's
type (`registry.adoption_route_band_sets` -> `registry.adoption_bands`): the highest level whose
exclusive lower bound `above` is below the value. A `(route, product_type)` pair with no band set
row abstains (null level) — hardware declares no usage ladder, and that absence IS the abstention
(§4.4). The stars cap is baked into its band set (levels stop at 3), so no separate cap logic here.

## Freshness

`measurement_as_of` is the MINIMUM `observed_at` across the contributing observations: an aggregate
is only as current as its stalest input.

## Identities, atomicity, and the live path

The grain keys on `declaration_version_id` and `observation_snapshot_id`, both derived at run time
(`build/declaration_version.py`, `build/observation_snapshot.py`) and NOT stored. They are inputs
to the pure `measurements(...)` so the aggregation/banding logic stays a pure function and the
goldens pin it with fixed test identities. The observation rows are read ONCE per run and the same
rows derive `observation_snapshot_id` and this table — the snapshot id and the rollup are one
atomic set, never two reads that could straddle a refresh. `load_current_observations()` reads the
deployed `observations.product_adoption_current` via `pyoso`; `resolve_over_baseline()` reads the
immutable Phase-2 baseline for in-repo tests. Serialization to a publishable static model and the
OSO upload are `build/serialize_evaluation.py` and a maintainer runbook (`docs/operations/`).

Usage:
    uv run python -m build.adoption_measurements            # over the committed baseline
    uv run python -m build.adoption_measurements --live     # over the deployed current table
    uv run python -m build.adoption_measurements --json     # emit the rows
"""

from __future__ import annotations

import argparse
import datetime
import json
import math
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


def _numeric(value: object, column: str) -> int | float:
    """A finite int or float, preserved (never truncated); bool and non-finite are rejected."""
    if type(value) is bool or not isinstance(value, (int, float)):
        raise TypeError(f"{column} must be a finite int or float, got {type(value).__name__!r} ({value!r})")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"non-finite number in column {column!r}: {value!r}")
    return value


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


def _band_for(index: Mapping[str, list[tuple[int, int, str]]], band_set_id: str, value: int | float):
    """The highest (level, reach) whose exclusive lower bound is below value, or (None, None)."""
    best: tuple[int | None, str | None] = (None, None)
    for above, level, reach in index.get(band_set_id, []):
        if value > above:
            best = (level, reach)
    return best


def machine_routes(routing_tables: Mapping[str, Sequence[Mapping]]) -> list[dict]:
    """The routes that read a machine source, in precedence order. The two hand-authored routes
    (`active_users`, `reported_traction`) name no artifact and can never be selected here."""
    return [
        dict(r)
        for r in sorted(routing_tables["adoption_routes"], key=lambda r: r["route_order"])
        if r["source"]
    ]


def route_scopes(routing_tables: Mapping[str, Sequence[Mapping]]) -> dict[str, set[str]]:
    scopes: dict[str, set[str]] = {}
    for row in routing_tables["adoption_route_scopes"]:
        scopes.setdefault(row["route_id"], set()).add(row["scope_value"])
    return scopes


def select_route(
    declared_kinds: set[str],
    category_slug: str | None,
    routes: Sequence[Mapping],
    scopes: Mapping[str, set[str]],
) -> dict | None:
    """The first applicable machine route by precedence — declared artifact kind + category scope —
    independent of whether any observation exists for it. None when the product declares no artifact
    that any in-scope machine route reads."""
    for route in routes:
        if route["artifact_kind"] not in declared_kinds:
            continue
        scope = scopes.get(route["route_id"])
        if scope is not None and category_slug not in scope:
            continue
        return dict(route)
    return None


def measurements(
    observation_rows: Iterable[Mapping],
    routing_tables: Mapping[str, Sequence[Mapping]],
    band_rows: Iterable[Mapping],
    category_of: Mapping[str, str],
    declared_artifacts: Mapping[str, set[str]],
    *,
    declaration_version_id: str,
    observation_snapshot_id: str,
) -> list[dict]:
    """The product-level rollup as a pure function of its inputs (identities passed in).

    ``routing_tables`` is ``build.serialize_routing.build_routing``'s output; ``band_rows`` is
    ``adoption_bands`` + ``route_bands``; ``declared_artifacts`` maps product slug -> the artifact
    kinds it declares (``registry.product_artifacts``). A row is emitted only where the product's
    winning applicable route (by declarations) actually has an observation — never a fallthrough.
    """
    routes = machine_routes(routing_tables)
    scopes = route_scopes(routing_tables)
    method_by_rule = {
        r["aggregation_rule_id"]: r["method"] for r in routing_tables["adoption_aggregation_rules"]
    }
    band_set_of: dict[tuple[str, str], str] = {
        (row["route_id"], row["product_type"]): row["band_set_id"]
        for row in routing_tables["adoption_route_band_sets"]
    }
    band_index = _band_index(band_rows)

    by_product: dict[str, list[Mapping]] = {}
    for obs in observation_rows:
        by_product.setdefault(obs["product_slug"], []).append(obs)

    rows: list[dict] = []
    for product_slug in sorted(declared_artifacts):
        category_slug = category_of.get(product_slug)
        route = select_route(declared_artifacts[product_slug], category_slug, routes, scopes)
        if route is None:
            continue

        product_obs = by_product.get(product_slug, [])
        contributing = [
            o
            for o in product_obs
            if o["artifact_kind"] == route["artifact_kind"] and o["metric_type"] == route["metric_type"]
        ]
        if not contributing:
            # The winning route was not observed. Do NOT fall through to a weaker route; the
            # unmeasured outcome is reconciliation's to record.
            continue

        product_type = contributing[0]["product_type"]
        method = method_by_rule.get(route["aggregation_rule_id"], "")
        values = [_numeric(o["raw_value"], "raw_value") for o in contributing]
        if method == "sum":
            raw_value: int | float | None = sum(values)
        elif method == "max":
            raw_value = max(values)
        elif len(values) == 1:
            raw_value = values[0]
        else:
            raw_value = None  # rule-less route, several artifacts: undefined aggregation, abstain

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

    rows.sort(key=lambda r: (r["product_slug"], r["category_slug"] or "", r["route_id"]))
    return rows


def canonical_row(row: Mapping) -> str:
    """A flat, deterministic serialization of one measurement row for digesting."""
    flat = dict(row)
    flat["contributing_observation_ids"] = "|".join(row["contributing_observation_ids"])
    if isinstance(flat.get("measurement_as_of"), datetime.datetime):
        flat["measurement_as_of"] = flat["measurement_as_of"].isoformat()
    return json.dumps({k: flat.get(k) for k in COLUMNS}, separators=(",", ":"), sort_keys=True)


# --- inputs, the live read, and atomic resolution -------------------------------


def load_inputs(root: Path | None = None):
    """Return (routing_tables, band_rows, category_of, declared_artifacts) from committed sources."""
    from build.serialize_registry import build_registry
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
    declared: dict[str, set[str]] = {}
    for row in build_registry(src)[0]["product_artifacts"]:
        declared.setdefault(row["product_slug"], set()).add(row["artifact_kind"])
    return tables, band_rows, _category_of(src["categories"]), declared


def _native(value: object) -> object:
    """Coerce a pyoso/pandas scalar to a native Python value.

    `build.warehouse.query` returns rows via pandas `to_dict`, so numbers arrive as numpy scalars
    and timestamps as pandas `Timestamp` — types the strict digest (`observation_snapshot._canonical_
    row`) and `_numeric` here reject on purpose. A `Timestamp` becomes a `datetime`; a numpy scalar
    becomes its Python equivalent via `.item()`; a null (`None`/NaN/NaT) becomes `None`. Native
    values pass through untouched.
    """
    if value is None:
        return None
    to_pydatetime = getattr(value, "to_pydatetime", None)
    if callable(to_pydatetime):  # pandas Timestamp
        return None if _is_na(value) else to_pydatetime()
    if _is_na(value):  # NaN / NaT / pandas.NA
        return None
    item = getattr(value, "item", None)
    if callable(item) and not isinstance(value, (str, bytes)):  # numpy scalar
        return item()
    return value


def _is_na(value: object) -> bool:
    try:
        import pandas as pd

        result = pd.isna(value)
        return bool(result) if not hasattr(result, "__len__") else False
    except Exception:
        return False


def load_current_observations() -> list[dict]:
    """The deployed observations.product_adoption_current, read live via pyoso (needs OSO_API_KEY).

    Values are coerced to native Python types so the strict digest and banding accept them.
    """
    from build.warehouse import query

    rows = query(
        "SELECT observation_id, product_slug, product_type, artifact_kind, artifact_id, channel, "
        "metric_type, raw_value, unit, measurement_window_days, observed_at "
        "FROM currentai.observations.product_adoption_current"
    )
    return [{key: _native(value) for key, value in row.items()} for row in rows]


def resolve(observation_rows: Sequence[Mapping], root: Path | None = None, allow_dirty: bool = False) -> list[dict]:
    """Build measurements from an already-read observation set — the atomic entry point.

    The SAME rows derive ``observation_snapshot_id`` and the rollup, so the snapshot id and the
    table are one set of rows, never two reads.
    """
    from build.declaration_version import resolve as resolve_declaration
    from build.observation_snapshot import observation_snapshot_id

    base = root or ROOT
    tables, band_rows, category_of, declared = load_inputs(base)
    return measurements(
        observation_rows,
        tables,
        band_rows,
        category_of,
        declared,
        declaration_version_id=resolve_declaration(base, allow_dirty=allow_dirty)["declaration_version_id"],
        observation_snapshot_id=observation_snapshot_id(observation_rows),
    )


def resolve_over_baseline(root: Path | None = None, allow_dirty: bool = False) -> list[dict]:
    """Build measurements over the immutable Phase-2 baseline (one read feeds id + rollup)."""
    from build.observation_snapshot import rows_from_parquet

    return resolve(rows_from_parquet(), root=root, allow_dirty=allow_dirty)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit the measurement rows as JSON")
    parser.add_argument("--live", action="store_true", help="read the deployed current table via pyoso")
    parser.add_argument("--allow-dirty", action="store_true",
                        help="stamp a diagnostic declaration_version_id over a dirty worktree")
    args = parser.parse_args()

    observation_rows = load_current_observations() if args.live else None
    rows = (
        resolve(observation_rows, allow_dirty=args.allow_dirty)
        if observation_rows is not None
        else resolve_over_baseline(allow_dirty=args.allow_dirty)
    )
    if args.json:
        print("\n".join(canonical_row(row) for row in rows))
        return 0

    banded = sum(1 for r in rows if r["measured_level"] is not None)
    print(f"measurement rows        {len(rows)}")
    print(f"  banded                {banded}")
    print(f"  abstained (null level){len(rows) - banded:>6}")
    by_route: dict[str, int] = {}
    for row in rows:
        by_route[row["route_id"]] = by_route.get(row["route_id"], 0) + 1
    print("by winning route:")
    for route_id in sorted(by_route):
        print(f"  {route_id:<32}{by_route[route_id]:>5}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
