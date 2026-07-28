"""Push the serialized registry and rubric CSVs to OSO as static models.

This is the "config in" half of the bridge: the repo declares what exists and how
to score it, CI pushes that declaration outward. Nothing is pulled back in here,
and no generated CSV is committed — the repo stays YAML, and OSO gets a flat mirror
of it.

Two serializers feed this. `serialize_registry` emits identity; `serialize_rubric`
emits each category's scoring rules plus the evidence currently on record. Layer-2
cannot compute a score without both, so they publish together.

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
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from build.serialize_registry import OUT_DIR
from build.serialize_registry import TABLES as REGISTRY_TABLES
from build.serialize_rubric import TABLES as RUBRIC_TABLES

# One dataset, two serializers. `serialize_registry` declares what exists;
# `serialize_rubric` declares how to score it and what evidence is on record.
# Both are configuration flowing outward, so they share the `registry` dataset
# and this publisher. Order is stable so the materialization run is reproducible.
TABLES: tuple[str, ...] = tuple(REGISTRY_TABLES) + tuple(RUBRIC_TABLES)

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
    with urllib.request.urlopen(request, timeout=60) as response:
        body = json.load(response)
    if body.get("errors"):
        raise RuntimeError(f"GraphQL error: {json.dumps(body['errors'])[:500]}")
    return body["data"]


Q_DATASETS = """query($where: JSON){ datasets(where:$where){ edges{ node{ id name type } } } }"""
Q_STATIC = """query($where: JSON){ staticModels(where:$where){ edges{ node{ id name } } } }"""
M_DATASET = """mutation($input: CreateDatasetInput!){
  createDataset(input:$input){ success dataset{ id name } } }"""
M_STATIC = """mutation($input: CreateStaticModelInput!){
  createStaticModel(input:$input){ success staticModel{ id name } } }"""
M_URL = """mutation($staticModelId: ID!){ createStaticModelUploadUrl(staticModelId:$staticModelId) }"""
M_RUN = """mutation($input: CreateStaticModelRunRequestInput!){
  createStaticModelRunRequest(input:$input){ success run{ id status } } }"""


def resolve_dataset(name: str, org_id: str, token: str) -> str:
    found = graphql(Q_DATASETS, {"where": {"org_id": {"eq": org_id}, "name": {"eq": name}}}, token)
    edges = found["datasets"]["edges"]
    if edges:
        return edges[0]["node"]["id"]
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
                    "Declarative only — scores are computed downstream, not mirrored here."
                ),
            }
        },
        token,
    )
    return created["createDataset"]["dataset"]["id"]


def resolve_static_models(dataset_id: str, org_id: str, token: str) -> dict[str, str]:
    found = graphql(Q_STATIC, {"where": {"dataset_id": {"eq": dataset_id}}}, token)
    existing = {n["node"]["name"]: n["node"]["id"] for n in found["staticModels"]["edges"]}
    for table in TABLES:
        if table not in existing:
            created = graphql(
                M_STATIC, {"input": {"orgId": org_id, "datasetId": dataset_id, "name": table}}, token
            )
            existing[table] = created["createStaticModel"]["staticModel"]["id"]
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
            f"missing CSVs: {missing}. Run build.serialize_registry and "
            f"build.serialize_rubric first.",
            file=sys.stderr,
        )
        return 2

    dataset_id = resolve_dataset(dataset_name, org_id, token)
    models = resolve_static_models(dataset_id, org_id, token)
    print(f"dataset {dataset_name} = {dataset_id}")

    if args.dry_run:
        for table in TABLES:
            print(f"  would upload {table}.csv -> {models[table]}")
        return 0

    for table in TABLES:
        path = args.dir / f"{table}.csv"
        url = graphql(M_URL, {"staticModelId": models[table]}, token)["createStaticModelUploadUrl"]
        upload(path, url)
        print(f"  uploaded {table}.csv ({path.stat().st_size:,} bytes)")

    run = graphql(
        M_RUN,
        {"input": {"datasetId": dataset_id, "selectedModels": [models[t] for t in TABLES]}},
        token,
    )["createStaticModelRunRequest"]["run"]
    print(f"materialization run {run['id']} ({run['status']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
