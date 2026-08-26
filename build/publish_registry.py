"""Push the serialized registry and rubric CSVs to OSO as static models.

This is the "config in" half of the bridge: the repo declares what exists and how
to score it, CI pushes that declaration outward. Nothing is pulled back in here,
and no generated CSV is committed — the repo stays YAML, and OSO gets a flat mirror
of it.

Four serializers feed this. `serialize_registry` emits identity; `serialize_rubric`
emits each category's scoring rules plus the evidence currently on record;
`serialize_routing` compiles the adoption routing semantics so evaluation never reinterprets
signal_routing.yaml; and `serialize_scores` emits the recorded scores themselves, every
product and axis in one row. Layer-2 cannot compute a score without the first two, so they
publish together, and the last is what lets a reader query adoption and capability at all —
those axes are recomputed nowhere, so before this the warehouse held their sources and not
their values.

Idempotent. Static models are created on first run and reused after, so this can
run on every push to sources/.

Environment:
    OSO_API_KEY   required
    OSO_ORG_ID    required
    OSO_DATASET   optional, defaults to "registry"

Usage:
    uv run python -m build.publish_registry
    uv run python -m build.publish_registry --dry-run
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from build.serialize_registry import OUT_DIR
from build.serialize_registry import TABLES as REGISTRY_TABLES
from build.serialize_routing import TABLES as ROUTING_TABLES
from build.serialize_rubric import TABLES as RUBRIC_TABLES
from build.serialize_scores import TABLES as SCORES_TABLES

# One dataset, four serializers. `serialize_registry` declares what exists;
# `serialize_rubric` declares how to score it and what evidence is on record;
# `serialize_routing` compiles the adoption routing semantics; and `serialize_scores` carries
# the recorded scores themselves. All are the repo's own declarations flowing outward, so they
# share the `registry` dataset and this publisher. Order is stable so the materialization run
# is reproducible.
TABLES: tuple[str, ...] = (
    tuple(REGISTRY_TABLES) + tuple(RUBRIC_TABLES) + tuple(ROUTING_TABLES) + tuple(SCORES_TABLES)
)

API = "https://api.oso.xyz/v1/graphql"
USER_AGENT = "os-ai-map-registry-publisher/1.0"
DEFAULT_DATASET = "registry"


def graphql(query: str, variables: dict, token: str) -> dict:
    request = urllib.request.Request(
        API,
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            # The default Python-urllib agent is rejected with a blanket 403.
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.load(response)
    except urllib.error.HTTPError as error:
        # A malformed query is a GraphQL VALIDATION error served with a 4xx, and the reason is
        # in the body urlopen never reads. Without this, `deleteStaticModel` returning
        # SimplePayload! rather than a scalar surfaced as a bare "HTTP Error 400: Bad Request"
        # with no hint that the mutation was missing its selection set (2026-08-19).
        detail = error.read().decode("utf-8", "replace")[:500]
        raise RuntimeError(f"HTTP {error.code} from the API: {detail}") from error
    if body.get("errors"):
        raise RuntimeError(f"GraphQL error: {json.dumps(body['errors'])[:500]}")
    return body["data"]


Q_DATASETS = """query($where: JSON){ datasets(where:$where){ edges{ node{ id name type } } } }"""
Q_STATIC = """query($where: JSON){ staticModels(where:$where){
  edges{ node{ id name materializations(first:1){ totalCount } } } } }"""
M_DATASET = """mutation($input: CreateDatasetInput!){
  createDataset(input:$input){ success dataset{ id name } } }"""
M_STATIC = """mutation($input: CreateStaticModelInput!){
  createStaticModel(input:$input){ success staticModel{ id name } } }"""
M_URL = """mutation($staticModelId: ID!){ createStaticModelUploadUrl(staticModelId:$staticModelId) }"""
M_RUN = """mutation($input: CreateStaticModelRunRequestInput!){
  createStaticModelRunRequest(input:$input){ success runGroup{ id status } } }"""
M_DELETE = """mutation($id: ID!){ deleteStaticModel(id:$id){ success message } }"""
Q_MODEL_RUN = """query($where: JSON){ staticModels(where:$where){
  edges{ node{ runs(first:1){ edges{ node{ id status } } } } } } }"""

RUN_SUCCESS = "SUCCESS"
RUN_TERMINAL = frozenset({"SUCCESS", "FAILED", "CANCELED", "CANCELLED", "ERROR", "TIMEOUT", "ABORTED"})


def latest_run_status(model_id: str, token: str) -> str | None:
    """The status of a static model's most recent run, or None if it has none yet."""
    edges = graphql(Q_MODEL_RUN, {"where": {"id": {"eq": model_id}}}, token)["staticModels"]["edges"]
    runs = edges[0]["node"]["runs"]["edges"] if edges else []
    return runs[0]["node"]["status"] if runs else None


def poll_model_run(model_id: str, token: str, timeout: float = 600.0, interval: float = 5.0) -> str:
    """Block until the model's latest run reaches a terminal state, or the timeout elapses.

    A non-terminal status at timeout (e.g. RUNNING/QUEUED) is returned as-is, which the caller
    treats as not-SUCCESS — a hung run never certifies as materialized.
    """
    import time

    deadline = time.time() + timeout
    status = latest_run_status(model_id, token)
    while status not in RUN_TERMINAL:
        if time.time() >= deadline:
            return status or "UNKNOWN"
        time.sleep(interval)
        status = latest_run_status(model_id, token)
    return status


def resolve_dataset(name: str, org_id: str, token: str, create: bool = True) -> str | None:
    """The registry dataset's id, creating it when absent.

    `create` gates the one mutation this resolver performs, mirroring `resolve_static_models`.
    A `--dry-run` publish calls it False so that resolving the dataset reads the platform but
    never writes to it: an absent dataset returns `None` and is left for the caller to report
    as a would-create, rather than being created via `M_DATASET` before the dry-run returns.
    """
    found = graphql(Q_DATASETS, {"where": {"org_id": {"eq": org_id}, "name": {"eq": name}}}, token)
    edges = found["datasets"]["edges"]
    if edges:
        return edges[0]["node"]["id"]
    if not create:
        return None
    created = graphql(
        M_DATASET,
        {
            "input": {
                "orgId": org_id,
                "name": name,
                "displayName": "Registry",
                "type": "STATIC_MODEL",
                "description": (
                    "The os-ai-map registry: which products, organizations and categories "
                    "exist and how they relate. Pushed by CI on every change to sources/. "
                    "Declarative only. Openness is COMPUTED downstream in "
                    "currentai.scores and graded against this by check_parity; the recorded "
                    "scores for all three axes are mirrored here as product_scores, which is "
                    "a copy of what the repo says rather than a computation over it."
                ),
            }
        },
        token,
    )
    return created["createDataset"]["dataset"]["id"]


def data_rows(path: Path) -> int:
    """Rows in a serialized CSV, not counting the header.

    A serializer emits a header for every table it declares, whether or not anything
    filled it, so file existence says nothing about content. `tail_products.csv` is 94
    bytes of header on a push where every tail row was promoted or rejected.
    """
    with path.open(newline="", encoding="utf-8") as handle:
        return max(0, sum(1 for _ in csv.reader(handle)) - 1)


def resolve_static_models(
    dataset_id: str, org_id: str, token: str, wanted: tuple[str, ...], create: bool = True
) -> dict[str, tuple[str | None, bool]]:
    """Model id and whether it has ever materialized a table, per wanted table.

    Only `wanted` tables get created. A model created for a table with no rows is a
    model that cannot succeed: dlt infers a schema from records, so zero records
    produces zero tables, and the runner fails the whole materialization on
    "No tables found after processing static model". That is what turned run
    7cd22391 red on 2026-08-19 after all 16 populated tables had already loaded.

    `create` gates the one mutation this resolver performs. A `--dry-run` publish calls
    it False so that resolving ids reads the platform but never writes to it: a missing
    model is recorded as `(None, False)` and left for the caller to report as a
    would-create, rather than being created before the dry-run's early return.
    """
    found = graphql(Q_STATIC, {"where": {"dataset_id": {"eq": dataset_id}}}, token)
    existing: dict[str, tuple[str | None, bool]] = {
        n["node"]["name"]: (
            n["node"]["id"],
            bool((n["node"].get("materializations") or {}).get("totalCount")),
        )
        for n in found["staticModels"]["edges"]
    }
    for table in wanted:
        if table not in existing:
            if not create:
                existing[table] = (None, False)
                continue
            created = graphql(
                M_STATIC, {"input": {"orgId": org_id, "datasetId": dataset_id, "name": table}}, token
            )
            existing[table] = (created["createStaticModel"]["staticModel"]["id"], False)
    return existing


def upload(path: Path, url: str) -> None:
    """Bare PUT. Extra headers are not in the signature and cause a mismatch."""
    request = urllib.request.Request(
        url, data=path.read_bytes(), method="PUT", headers={"User-Agent": USER_AGENT}
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        if response.status not in (200, 201):
            raise RuntimeError(f"upload of {path.name} returned {response.status}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="resolve ids, upload nothing")
    parser.add_argument("--dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()

    token = os.environ.get("OSO_API_KEY")
    org_id = os.environ.get("OSO_ORG_ID")
    if not token or not org_id:
        print("OSO_API_KEY and OSO_ORG_ID must both be set", file=sys.stderr)
        return 2
    dataset_name = os.environ.get("OSO_DATASET", DEFAULT_DATASET)

    missing = [t for t in TABLES if not (args.dir / f"{t}.csv").exists()]
    if missing:
        print(
            f"missing CSVs: {missing}. Run build.serialize_registry, build.serialize_rubric, "
            f"build.serialize_routing and build.serialize_scores first.",
            file=sys.stderr,
        )
        return 2

    counts = {t: data_rows(args.dir / f"{t}.csv") for t in TABLES}
    populated = tuple(t for t in TABLES if counts[t])
    empty = tuple(t for t in TABLES if not counts[t])

    # A dry-run reads ids but must not write: `create=not args.dry_run` keeps the resolver from
    # firing `M_DATASET` when the dataset is absent. It then returns None, and there is no
    # dataset to resolve static models against — so the plan reports every populated table as a
    # would-create and returns without a single mutation.
    dataset_id = resolve_dataset(dataset_name, org_id, token, create=not args.dry_run)
    if dataset_id is None:
        print(f"would create dataset {dataset_name}")
        for table in populated:
            print(f"  would create {table} and upload {table}.csv ({counts[table]:,} rows)")
        return 0

    # `create=False` on a dry-run records a missing model as a would-create rather than
    # creating it before the early return below.
    models = resolve_static_models(dataset_id, org_id, token, populated, create=not args.dry_run)
    print(f"dataset {dataset_name} = {dataset_id}")

    # An empty table is a real state, not an error: a category whose tail registry has been
    # fully triaged declares `products: []` and keeps the file so the next discovery batch has
    # somewhere to land. What must not happen is publishing nothing and leaving whatever was
    # there before, which would serve rows the repo no longer declares. So the model is
    # removed, and the table's absence is the honest reading of "no rows". A later push with
    # rows recreates it, because resolve_static_models creates whatever is missing.
    #
    # Dropping a table that HOLDS rows is not something to do unattended, though. That shape
    # means a serializer regressed or a filter went wrong, and the loud stop is the point.
    stale = []
    for table in empty:
        model = models.get(table)
        if model is None:
            print(f"  skipped {table}.csv (no rows, no model to publish to)")
            continue
        model_id, materialized = model
        if materialized:
            stale.append(table)
            continue
        if args.dry_run:
            print(f"  would delete empty {table} ({model_id})")
            continue
        # Best effort, and deliberately not fatal. The delete is tidying: the model is already
        # excluded from the run below, so the publish is correct whether or not it goes. Making
        # it fatal would mean a token without delete permission cannot publish the registry at
        # all, which is a far worse failure than an empty model sitting in the dataset.
        try:
            graphql(M_DELETE, {"id": model_id}, token)
            print(f"  deleted empty {table} ({model_id}); it had never materialized")
        except (RuntimeError, urllib.error.URLError) as error:
            print(
                f"  WARNING could not delete empty {table} ({model_id}): {error}. "
                f"It is excluded from this run, so the publish is unaffected, but the dataset "
                f"will keep showing it as broken until it is removed.",
                file=sys.stderr,
            )

    if stale:
        print(
            f"refusing to publish: {stale} serialized zero rows but already hold a "
            f"materialized table. Publishing nothing would leave the old rows in place, and "
            f"dropping a populated table is a human's call. Check the serializer before "
            f"re-running.",
            file=sys.stderr,
        )
        return 2

    if args.dry_run:
        for table in populated:
            model_id = models[table][0]
            if model_id is None:
                print(f"  would create {table} and upload {table}.csv ({counts[table]:,} rows)")
            else:
                print(f"  would upload {table}.csv ({counts[table]:,} rows) -> {model_id}")
        return 0

    for table in populated:
        path = args.dir / f"{table}.csv"
        model_id = models[table][0]
        url = graphql(M_URL, {"staticModelId": model_id}, token)["createStaticModelUploadUrl"]
        upload(path, url)
        print(f"  uploaded {table}.csv ({path.stat().st_size:,} bytes, {counts[table]:,} rows)")

    # The run request is per static model: CreateStaticModelRunRequestInput takes
    # (datasetId, staticModelId), not a selectedModels list. Materialize ONE model at a time,
    # awaiting each run to a terminal state before requesting the next. A run request only
    # QUEUES a run; the loads then execute asynchronously, and firing them all at once makes
    # their loads collide on the destination — a transient "Failed to query OPA backend"
    # (DatabaseTransientException) that fails a nondeterministic subset. Serializing keeps each
    # load alone, and polling to terminal is what certifies the table actually materialized
    # (an accepted request is not a finished one).
    failures: list[tuple[str, str]] = []
    for table in populated:
        model_id = models[table][0]
        run_group = graphql(
            M_RUN,
            {"input": {"datasetId": dataset_id, "staticModelId": model_id}},
            token,
        )["createStaticModelRunRequest"]["runGroup"]
        status = poll_model_run(model_id, token)
        print(f"  {table}: run group {run_group['id']} finished {status}")
        if status != RUN_SUCCESS:
            failures.append((table, status))

    if failures:
        print("materialization did not succeed for every model:", file=sys.stderr)
        for table, status in failures:
            print(f"  ! {table}: {status}", file=sys.stderr)
        return 1
    print(f"materialized {len(populated)} models")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
