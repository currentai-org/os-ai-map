"""Bind a live read of a deployed model to the materialization (and run) that produced it.

## What this is

`observations.product_adoption_current` carries no row-level run lineage (#355): the fetcher
tables expose no run id, so `source_run_id` is NULL and the reconciliation report classifies
every measured row `source_unavailable`. That gap is the platform's to close. What CAN be
established repo-side, without timestamp inference, is a narrower fact: **which materialization
of the current table a given read was served from** — and through it, that materialization's
`run_id`.

The platform makes this possible because a data-model run never rewrites a table in place: each
run CTAS-es a fresh physical table and repoints the logical name at the new materialization, and
the control plane records one materialization row per run (`id`, `runId`, `createdAt`). So at any
instant the logical table IS exactly one materialization, and the only uncertainty is a race: a
run could complete between our row read and our control-plane lookup.

## The bracket

The race is closed by bracketing, not by timestamps:

  1. read the model's newest materialization id (control plane, before);
  2. read the rows (pyoso; the query text is nonce-salted by `build.warehouse.query`, so the
     result cannot be a cached answer from before an earlier materialization);
  3. read the newest materialization id again (after).

If the two control-plane reads name the SAME materialization, no run completed across the row
read, so the rows were served by that materialization and are bound to its `run_id`. If they
differ, a refresh landed mid-bracket and the read is honestly `unstable`: both ids are recorded
and NO run id is claimed. An unstable bracket is a report, never an error — the caller decides
whether to re-read.

## The trigger is part of the binding

A materialization names the run that produced it, and the run says how it was started. That
matters here because adoption's date is supposed to come from the weekly cadence rather than
from somebody pressing a button: a `MANUAL` run is a person refreshing a table, and a date
earned from one would be a person's date wearing a run id. So the binding carries the run's
`triggerType`, `status` and `startedAt` alongside the ids, and the caller decides what to
require of them. Looking the run up is a second control-plane read; when it fails, the binding
says so and names no trigger, which is the same posture as an unstable bracket.

## What this is NOT

  * Not row-to-run binding for the observations themselves. The bound run is the run of
    `product_adoption_current`'s own materialization — the model evaluation that read the fetcher
    tables — not the fetcher runs that measured the artifacts. Reconciliation's
    `source_unavailable` posture is unchanged by this module (#355 remains open).
  * Not inference. A bracket either proves the binding or reports that it could not; there is no
    "probably this run" outcome, and `createdAt` ordering is used only to pick the newest
    materialization within one control-plane response, never to correlate with row timestamps.

Usage:
    from build.read_binding import bound_read
    result = bound_read(load_current_observations)
    rows, binding = result.rows, result.binding
"""

from __future__ import annotations

import dataclasses
import os
from collections.abc import Callable, Mapping, Sequence

GRAPHQL_QUERY = """query($w: JSON) {
  dataModels(where: $w, first: 10) {
    edges { node {
      id
      name
      dataset { name }
      materializations(first: 50) {
        edges { node { id runId createdAt } }
      }
    } }
  }
}"""

RUN_QUERY = """query($w: JSON) {
  runs(where: $w, first: 2) {
    edges { node { id triggerType runType status startedAt } }
  }
}"""

MODEL_NAME = "product_adoption_current"
DATASET_NAME = "observations"


class BindingLookupError(RuntimeError):
    """The control plane could not name the model's newest materialization."""


@dataclasses.dataclass(frozen=True)
class Materialization:
    """One control-plane materialization row, as much of it as the binding needs."""

    materialization_id: str
    run_id: str
    created_at: str
    model_id: str


@dataclasses.dataclass(frozen=True)
class Run:
    """How the run that produced a materialization was started, and how it ended."""

    run_id: str
    trigger_type: str | None
    status: str | None
    started_at: str | None


@dataclasses.dataclass(frozen=True)
class BoundRead:
    """The rows of one read plus the binding verdict for that read."""

    rows: list[dict]
    binding: dict


def _control_plane(graphql: Callable[..., Mapping] | None) -> tuple[Callable[..., Mapping], str]:
    """The reader to issue control-plane queries with, and the token to issue them under."""
    if graphql is None:
        from build.publish_registry import graphql as live_graphql

        def graphql(query: str, variables: Mapping, token: str) -> Mapping:  # type: ignore[misc]
            return live_graphql(query, dict(variables), token)

    token = os.environ.get("OSO_API_KEY", "")
    if not token:
        raise BindingLookupError("OSO_API_KEY must be set to read the control plane")
    return graphql, token


def run_record(run_id: str, graphql: Callable[..., Mapping] | None = None) -> Run:
    """How the run behind a materialization was started, from the control plane.

    Raises `BindingLookupError` when the id names no run or names more than one. A run id came
    out of the materialization the bracket already proved, so a control plane that cannot resolve
    it is a control plane disagreeing with itself — reporting that as "trigger unknown" would let
    the caller treat a contradiction as a missing optional field.
    """
    reader, token = _control_plane(graphql)
    response = reader(RUN_QUERY, {"w": {"id": {"eq": run_id}}}, token)
    nodes = [edge["node"] for edge in response["runs"]["edges"]]
    if not nodes:
        raise BindingLookupError(f"the control plane names no run {run_id}")
    if len(nodes) > 1:
        raise BindingLookupError(f"{len(nodes)} runs answer to id {run_id}; refusing to guess")
    node = nodes[0]
    return Run(
        run_id=node["id"],
        trigger_type=node.get("triggerType"),
        status=node.get("status"),
        started_at=node.get("startedAt"),
    )


def latest_materialization(
    model_name: str = MODEL_NAME,
    dataset_name: str = DATASET_NAME,
    graphql: Callable[..., Mapping] | None = None,
) -> Materialization:
    """The newest materialization of one deployed model, from the control plane.

    Newest within one response, by (createdAt, id) — a tiebreak inside a single authoritative
    listing, not a cross-source timestamp correlation. Raises `BindingLookupError` when the model
    is missing, ambiguous, or has no materialization: a caller asking to bind a read of a model
    that the control plane cannot name has a configuration problem, not an unstable bracket.
    """
    reader, token = _control_plane(graphql)
    response = reader(GRAPHQL_QUERY, {"w": {"name": {"eq": model_name}}}, token)
    nodes = [edge["node"] for edge in response["dataModels"]["edges"]]
    matches = [node for node in nodes if (node.get("dataset") or {}).get("name") == dataset_name]
    if not matches:
        raise BindingLookupError(
            f"no deployed model {dataset_name}.{model_name} visible to this token"
        )
    if len(matches) > 1:
        raise BindingLookupError(
            f"{len(matches)} deployed models named {dataset_name}.{model_name}; refusing to guess"
        )
    node = matches[0]
    materializations = [edge["node"] for edge in node["materializations"]["edges"]]
    if not materializations:
        raise BindingLookupError(f"{dataset_name}.{model_name} has no materialization to bind to")
    newest = max(materializations, key=lambda m: (m["createdAt"], m["id"]))
    return Materialization(
        materialization_id=newest["id"],
        run_id=newest["runId"],
        created_at=newest["createdAt"],
        model_id=node["id"],
    )


def bound_read(
    reader: Callable[[], Sequence[Mapping]],
    model_name: str = MODEL_NAME,
    dataset_name: str = DATASET_NAME,
    graphql: Callable[..., Mapping] | None = None,
) -> BoundRead:
    """Run `reader` inside a materialization bracket and report what the read was bound to.

    The binding dict always carries `binding_status` (`bound` | `unstable`) and the model
    coordinates. `bound` adds the proven `materialization_id` / `run_id` / `materialized_at`,
    and how that run was started and ended — `run_trigger_type`, `run_status`, `run_started_at`.
    `unstable` records both bracket ends and claims nothing.
    """
    before = latest_materialization(model_name, dataset_name, graphql=graphql)
    rows = [dict(row) for row in reader()]
    after = latest_materialization(model_name, dataset_name, graphql=graphql)

    coordinates = {
        "model": f"{dataset_name}.{model_name}",
        "model_id": before.model_id,
    }
    if before.materialization_id == after.materialization_id:
        run = run_record(before.run_id, graphql=graphql)
        binding = {
            **coordinates,
            "binding_status": "bound",
            "materialization_id": before.materialization_id,
            "run_id": before.run_id,
            "materialized_at": before.created_at,
            "run_trigger_type": run.trigger_type,
            "run_status": run.status,
            "run_started_at": run.started_at,
        }
    else:
        binding = {
            **coordinates,
            "binding_status": "unstable",
            "materialization_id_before": before.materialization_id,
            "materialization_id_after": after.materialization_id,
        }
    return BoundRead(rows=rows, binding=binding)
