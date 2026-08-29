"""Audit every deployed model definition in the org and emit a reproducible receipt.

Phase 0b closed `consumer_checks.platform_models`: the repo-derived graph cannot see a
deployed model that has no repository source, so a table only such a model reads looks
unread. The only way to know is to read every deployed model definition. This module does
that read-only, and -- crucially -- writes a *receipt* so the conclusion can be reproduced
and reviewed rather than trusted as 57 authored booleans.

The receipt (`warehouse/audits/platform_models.json`) records, for every deployed model:
its fully-qualified table, model id, the platform revision hash, a sha256 of the source
(never the source body), the language, and the internal `currentai.*` tables it reads --
including an explicit empty list. From it, `consumers_from_receipt` derives the
platform-only consumer edges that `warehouse/assets.yaml` carries, and
`tests/test_assets_inventory.py` gates the inventory against the receipt rather than the
other way round.

Extraction reuses `build.assets.refs_in_source`, the same code the repo-derived graph runs,
so the file-based and platform-based passes cannot drift.

Environment:
    OSO_API_KEY   required to fetch (regenerate); reading the committed receipt needs nothing.

Usage:
    uv run python -m build.audit_platform_models              # regenerate the receipt
    uv run python -m build.audit_platform_models --check      # fetch and diff vs committed
    uv run python -m build.audit_platform_models --as-of 2026-08-22
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from build import assets as A
from build.publish_registry import graphql
from build.vocabulary import is_iso_date

ORG_ID = "ad7f4c1c-dd2f-430e-a831-e7f1f16e6d9e"
ORG = "currentai"
RECEIPT = A.ROOT / "warehouse" / "audits" / "platform_models.json"

# latestRevision.code is fetched to extract references and to digest, but is NEVER written to
# the receipt -- provenance is the platform `hash` plus a sha256 of the source.
Q_MODELS = """query($where: JSON){ dataModels(where:$where){ edges{ node{
  id name dataset{ id name }
  latestRevision{ code language hash }
} } } }"""


def fetch_models(token: str) -> list[dict]:
    data = graphql(Q_MODELS, {"where": {"org_id": {"eq": ORG_ID}}}, token)
    return [e["node"] for e in data["dataModels"]["edges"]]


def _producer_tables() -> set[str]:
    """Inventory tables that have a repository model file -- i.e. a repo source."""
    return {t for t, a in A.by_table().items() if (a.get("files") or {}).get("model")}


def build_receipt(models: list[dict], as_of: str) -> dict:
    """Turn fetched model nodes into the committed receipt shape.

    Deterministic: models sorted by table, reference lists sorted, so a re-run diffs cleanly.
    """
    # In-scope = a governed asset OR a currentai.* dependency contract (ADR-003): both are
    # tracked repository scope, so a deployed model reading either is an in-scope read.
    in_scope = set(A.by_table())
    in_scope |= {d["table"].removeprefix("currentai.") for d in A.dependencies()
                 if d["table"].startswith("currentai.")}
    producers = _producer_tables()
    rows = []
    for node in models:
        ds = node["dataset"]["name"]
        name = node["name"]
        table = f"currentai.{ds}.{name}"
        rev = node.get("latestRevision") or {}
        code = rev.get("code") or ""
        refs = A.refs_in_source(code, rev.get("language") or "")
        internal = sorted(r for r in refs if r.startswith("currentai."))
        in_scope_reads = sorted(r for r in internal if r.removeprefix("currentai.") in in_scope)
        rows.append({
            "table": table,
            "dataset": ds,
            "name": name,
            "model_id": node["id"],
            "revision_hash": rev.get("hash"),
            "source_sha256": hashlib.sha256(code.encode("utf-8")).hexdigest(),
            "language": rev.get("language"),
            "internal_reads": internal,
            "in_scope_reads": in_scope_reads,
            "has_repository_source": table.removeprefix("currentai.") in producers,
        })
    rows.sort(key=lambda r: r["table"])
    return {
        "audited_at": as_of,
        "org": ORG,
        "org_id": ORG_ID,
        "model_count": len(rows),
        "models": rows,
    }


_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
RECOGNIZED_LANGUAGES = {"sql", "python"}  # matched case-insensitively; the platform emits both cases


def validate_receipt(receipt: dict) -> list[str]:
    """Every part of the receipt contract, so a committed receipt cannot lie by omission.

    Shape only -- the online `--check` is the authoritative comparison against the live
    platform. This guards the committed bytes: an impossible `audited_at`, a duplicated or
    dropped model, a missing revision hash, an unrecognized language or a field of the wrong
    type must all fail here, not slip through a nonempty-list check.
    """
    problems: list[str] = []
    for key in ("audited_at", "org", "org_id", "model_count", "models"):
        if key not in receipt:
            problems.append(f"missing top-level field {key}")
    if not is_iso_date(str(receipt.get("audited_at"))):
        problems.append(f"audited_at {receipt.get('audited_at')!r} is not a real calendar date")
    # The org is not a free parameter: a receipt for a different org is not this audit.
    if receipt.get("org") != ORG:
        problems.append(f"org is {receipt.get('org')!r}, expected {ORG!r}")
    if receipt.get("org_id") != ORG_ID:
        problems.append(f"org_id is {receipt.get('org_id')!r}, expected {ORG_ID!r}")

    models = receipt.get("models")
    if not isinstance(models, list) or not models:
        problems.append("models is empty or not a list")
        return problems
    if not all(isinstance(m, dict) for m in models):
        problems.append("every model entry must be a mapping")
        return problems  # the per-model checks below would raise on a non-mapping
    if receipt.get("model_count") != len(models):
        problems.append(f"model_count {receipt.get('model_count')} != {len(models)} listed")

    tables = [m.get("table") for m in models]
    if all(isinstance(t, str) for t in tables) and tables != sorted(tables):
        problems.append("models are not in deterministic (table-sorted) order")
    for field, seen in (("table", tables), ("model_id", [m.get("model_id") for m in models])):
        dupes = sorted({v for v in seen if seen.count(v) > 1}, key=str)
        if dupes:
            problems.append(f"duplicate {field}: {dupes}")

    for m in models:
        t = m.get("table")
        where = t if isinstance(t, str) else "<no table>"
        ds, name = m.get("dataset"), m.get("name")
        if not (isinstance(ds, str) and ds):
            problems.append(f"{where}: dataset is not a nonempty string")
        if not (isinstance(name, str) and name):
            problems.append(f"{where}: name is not a nonempty string")
        if not (isinstance(t, str) and t.startswith("currentai.")):
            problems.append(f"{where}: table is not a currentai.* string")
        elif isinstance(ds, str) and isinstance(name, str) and t != f"currentai.{ds}.{name}":
            problems.append(f"{where}: table disagrees with dataset/name {ds}.{name}")
        if not (isinstance(m.get("model_id"), str) and _UUID.match(m.get("model_id") or "")):
            problems.append(f"{where}: model_id is not a UUID")
        if not _HEX64.match(m.get("revision_hash") or ""):
            problems.append(f"{where}: revision_hash is not a 64-hex digest")
        if not _HEX64.match(m.get("source_sha256") or ""):
            problems.append(f"{where}: source_sha256 is not a 64-hex digest")
        if str(m.get("language") or "").lower() not in RECOGNIZED_LANGUAGES:
            problems.append(f"{where}: unrecognized language {m.get('language')!r}")
        for key in ("internal_reads", "in_scope_reads"):
            if not isinstance(m.get(key), list) or not all(isinstance(x, str) for x in m.get(key) or []):
                problems.append(f"{where}: {key} is not a list of strings")
        if isinstance(m.get("internal_reads"), list) and isinstance(m.get("in_scope_reads"), list):
            if not set(m["in_scope_reads"]) <= set(m["internal_reads"]):
                problems.append(f"{where}: in_scope_reads is not a subset of internal_reads")
        if not isinstance(m.get("has_repository_source"), bool):
            problems.append(f"{where}: has_repository_source is not a boolean")
    return problems


def consumers_from_receipt(receipt: dict) -> dict[str, list[str]]:
    """Platform-ONLY model consumers per in-scope asset, derived from the receipt.

    Only models with no repository source count: a repo-sourced deployed model that reads an
    asset already appears in that asset's `read_by`, derived from the tree. This is exactly
    the `platform_model_consumers` field in the inventory, and gating that field against this
    map is what makes the audit reproducible instead of authored.
    """
    out: dict[str, set[str]] = {}
    for m in receipt["models"]:
        if m["has_repository_source"]:
            continue
        for ref in m["in_scope_reads"]:
            out.setdefault(ref.removeprefix("currentai."), set()).add(m["table"])
    return {k: sorted(v) for k, v in out.items()}


def load_receipt() -> dict:
    return json.loads(RECEIPT.read_text(encoding="utf-8"))


def write_receipt(receipt: dict) -> None:
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(receipt, indent=1, sort_keys=False) + "\n", encoding="utf-8")


def _census(receipt: dict) -> dict:
    """The parts a re-run must reproduce byte-for-byte, audited_at excluded."""
    return {"models": receipt["models"], "model_count": receipt["model_count"],
            "org_id": receipt["org_id"]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="fetch and diff against the committed receipt (census only)")
    ap.add_argument("--as-of", default=None, help="audit date stamp (default: today, UTC)")
    args = ap.parse_args(argv)

    token = os.environ.get("OSO_API_KEY")
    if not token:
        print("OSO_API_KEY is required to fetch deployed model definitions", file=sys.stderr)
        return 2

    as_of = args.as_of or datetime.now(timezone.utc).date().isoformat()
    fresh = build_receipt(fetch_models(token), as_of)

    if args.check:
        if not RECEIPT.exists():
            print("no committed receipt to check against", file=sys.stderr)
            return 1
        committed = load_receipt()
        if _census(fresh) != _census(committed):
            print("RECEIPT DRIFT: committed platform_models.json disagrees with the platform.",
                  file=sys.stderr)
            return 1
        print(f"receipt matches the platform ({fresh['model_count']} models)")
        return 0

    write_receipt(fresh)
    blind = sum(1 for m in fresh["models"] if not m["has_repository_source"])
    print(f"wrote {RECEIPT.relative_to(A.ROOT)}: {fresh['model_count']} models "
          f"({blind} with no repository source)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
