"""The frozen Phase-2 baseline is a contract, not just a file on disk.

`warehouse/data/observations/product_adoption_baseline.parquet` is the single preserved
baseline snapshot §18 requires for the temporary full-refresh period (data-architecture.md
§4.3, "The baseline is bytes, not a query"). Once captured it is immutable: every later
full-refresh of `product_adoption_current` overwrites the state these bytes record, so if they
are ever altered the first observations state is lost and unrecoverable.

`test_every_tracked_managed_file_is_declared` proves the file is *inventoried*. It does not
prove the bytes are *what they claim to be*, or that they cannot be quietly swapped. This module
does: it recomputes the digests, re-derives the schema/counts/coverage against the bytes
themselves, holds the receipt and the asset entry in agreement, and ratchets the bytes against
the merge base so a later PR cannot replace them — even while updating the receipt to match.
"""

import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path

import pyarrow.parquet as pq
import pytest
import yaml

from build.serialize_registry import build_registry
from build.validate import load_sources

ROOT = Path(__file__).resolve().parents[1]
PARQUET = ROOT / "warehouse/data/observations/product_adoption_baseline.parquet"
RECEIPT = ROOT / "warehouse/audits/product_adoption_baseline.json"
ASSET_ID = "observations.product_adoption_baseline"


# --- fixtures --------------------------------------------------------------------


@pytest.fixture(scope="module")
def receipt() -> dict:
    return json.loads(RECEIPT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def asset() -> dict:
    inv = yaml.safe_load((ROOT / "warehouse/assets.yaml").read_text(encoding="utf-8"))
    assets = inv["assets"] if isinstance(inv, dict) else inv
    for a in assets:
        if a["id"] == ASSET_ID:
            return a
    raise AssertionError(f"{ASSET_ID} not in the inventory")


@pytest.fixture(scope="module")
def table():
    return pq.read_table(PARQUET)


@pytest.fixture(scope="module")
def rows(table):
    return table.to_pylist()


# --- the writer-independent content digest, re-derived from the receipt's definition ----


def _content_digest(rows: list[dict], columns: list[str]) -> str:
    """sha256 over UTF-8 newline-joined compact JSON arrays, one per row, columns in schema
    order, rows ordered by observation_id, timestamps ISO-8601, nulls as null. This is the
    receipt's `content_digest_definition` executed independently — it must reproduce the
    recorded value, and it survives a parquet-library upgrade the file digest does not."""
    ordered = sorted(rows, key=lambda r: r["observation_id"])

    def enc(v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v

    lines = [
        json.dumps([enc(r[c]) for c in columns], separators=(",", ":"), ensure_ascii=False)
        for r in ordered
    ]
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


# --- digests -------------------------------------------------------------------------------


def test_file_digest_matches_receipt_and_asset(receipt, asset):
    """sha256 of the parquet bytes equals the recorded file digest in both places."""
    actual = hashlib.sha256(PARQUET.read_bytes()).hexdigest()
    assert actual == receipt["file_sha256"], "parquet bytes changed but file_sha256 did not"
    assert actual == asset["capture"]["file_sha256"]
    assert PARQUET.stat().st_size == receipt["file_bytes"]


def test_content_digest_is_reproducible(receipt, asset, rows):
    """The writer-independent content digest re-derives to the recorded value."""
    columns = [f["name"] for f in receipt["schema"]]
    actual = _content_digest(rows, columns)
    assert actual == receipt["content_sha256"], "content digest drifted from the frozen bytes"
    assert actual == asset["capture"]["content_sha256"]


# --- schema, counts, identity --------------------------------------------------------------


def test_schema_matches_receipt(table, receipt, asset):
    """Column names and types match the receipt, and the asset lists the same columns."""
    actual = [{"name": f.name, "type": str(f.type)} for f in table.schema]
    assert actual == receipt["schema"], "parquet schema drifted from the receipt"
    assert [f["name"] for f in receipt["schema"]] == asset["capture"]["columns"]


def test_row_and_product_counts_match(rows, receipt, asset):
    assert len(rows) == receipt["row_count"] == asset["capture"]["row_count"] == 654
    products = {r["product_slug"] for r in rows}
    assert len(products) == receipt["product_count"] == asset["capture"]["product_count"] == 392


def test_observation_ids_are_unique(rows, receipt):
    ids = [r["observation_id"] for r in rows]
    assert len(ids) == len(set(ids)) == receipt["row_count"], "duplicate observation_id"


def test_product_type_is_never_null(rows):
    """The identity-enforced current-state model resolves product_type on every row; the frozen
    baseline must carry that guarantee forward."""
    assert all(r["product_type"] is not None for r in rows)


# A declaration the corpus has since WITHDRAWN, with the reason. The baseline is frozen bytes
# from 2026-08-24 and the corpus moves on; an artifact undeclared after the freeze leaves rows
# behind that nothing can or should rewrite. Listed rather than tolerated in general, because
# the ordinary meaning of an undeclared baseline row is still a defect, and each entry here is
# a decision somebody made on purpose.
WITHDRAWN_SINCE_THE_BASELINE = {
    # `cohere` is Cohere's whole client SDK - chat, embed, classify and rerank behind one
    # client - so its downloads were never this product's. A declaration asserts that its
    # numbers ARE the product's numbers (identity.md), so it was removed rather than flagged
    # (#448). The baseline row is a true record of what was declared on 2026-08-24.
    ("cohere-rerank-api", "pypi", "cohere"),
}


def test_every_row_matches_a_declared_artifact(rows):
    """Declared-artifact coverage, re-checked against the frozen bytes: every observation's
    (product_slug, artifact_kind, artifact_id) is a declared artifact in registry.product_artifacts
    — the same guarantee the current-state model's coverage guard enforces at materialization.

    The exception is a declaration deliberately withdrawn after the freeze. The baseline cannot be
    rewritten, so those rows persist; they are named in `WITHDRAWN_SINCE_THE_BASELINE` with why,
    rather than the assertion being softened to let any undeclared row through.
    """
    tables, _errors, _warnings = build_registry(load_sources(ROOT))
    declared = {
        (r["product_slug"], r["artifact_kind"], r["artifact_id"])
        for r in tables["product_artifacts"]
    }
    undeclared = sorted(
        {
            (r["product_slug"], r["artifact_kind"], r["artifact_id"])
            for r in rows
            if (r["product_slug"], r["artifact_kind"], r["artifact_id"]) not in declared
        }
        - WITHDRAWN_SINCE_THE_BASELINE
    )
    assert not undeclared, f"baseline rows for undeclared artifacts: {undeclared[:5]}"


def test_the_withdrawn_list_has_not_gone_stale(rows):
    """An entry here must still describe a baseline row whose artifact is no longer declared.

    Without this the list rots into a permanent exemption: a declaration could be restored, or an
    entry could be added for a row the baseline never held, and the first test would keep passing.
    """
    tables, _errors, _warnings = build_registry(load_sources(ROOT))
    declared = {
        (r["product_slug"], r["artifact_kind"], r["artifact_id"])
        for r in tables["product_artifacts"]
    }
    in_baseline = {(r["product_slug"], r["artifact_kind"], r["artifact_id"]) for r in rows}
    stale = sorted(
        entry for entry in WITHDRAWN_SINCE_THE_BASELINE
        if entry not in in_baseline or entry in declared
    )
    assert not stale, (
        "WITHDRAWN_SINCE_THE_BASELINE entries that no longer describe a withdrawn baseline row "
        f"— delete them: {stale}"
    )


# --- receipt <-> asset agreement, and the honest run-binding record ------------------------


def test_receipt_and_asset_agree(receipt, asset):
    cap = asset["capture"]
    assert asset["files"]["data"] == receipt["file"]
    assert asset["table"] == receipt["table"]
    for key in ("captured_at", "row_count", "product_count", "file_sha256", "content_sha256"):
        assert cap[key] == receipt[key], f"receipt/asset disagree on {key}"
    assert cap["columns"] == [f["name"] for f in receipt["schema"]]
    assert cap["receipt"] == "warehouse/audits/product_adoption_baseline.json"


def test_no_run_binding_is_asserted_honestly(rows, receipt, asset):
    """The baseline must not invent a row-to-run binding the platform never provided (#355)."""
    assert receipt["source_run_ids"] == []
    assert asset["capture"]["source_run_ids"] == []
    assert receipt["rows_with_null_source_run_id"] == receipt["row_count"]
    assert all(r["source_run_id"] is None for r in rows)


# --- the immutability ratchet --------------------------------------------------------------


def _merge_base_bytes(path: str, base: str = "origin/main") -> bytes | None:
    """The committed bytes of `path` at the merge base with `base`, or None if absent there."""
    try:
        merge_base = subprocess.run(
            ["git", "-C", str(ROOT), "merge-base", "HEAD", base],
            capture_output=True, check=True,
        ).stdout.decode().strip()
        return subprocess.run(
            ["git", "-C", str(ROOT), "show", f"{merge_base}:{path}"],
            capture_output=True, check=True,
        ).stdout
    except subprocess.CalledProcessError:
        return None


def _assert_immutable(prior: bytes | None, receipt: dict) -> None:
    current = PARQUET.read_bytes()
    if prior is None:
        # First install: the file does not exist at the merge base, so there is no prior to
        # ratchet against. Rather than skip, establish the frozen reference the ratchet will
        # guard once this lands — assert the committed bytes match the digest the receipt
        # records, so a bytes/receipt mismatch fails at introduction too.
        assert hashlib.sha256(current).hexdigest() == receipt["file_sha256"], (
            "baseline bytes do not match the receipt's recorded file digest at introduction"
        )
        return
    assert prior == current, (
        "the frozen baseline bytes changed against the merge base — the single preserved "
        "snapshot is immutable and must never be rewritten, refreshed, or relabeled"
    )


def test_baseline_bytes_are_immutable_against_the_merge_base(receipt):
    """Once the baseline exists on the base branch, its bytes are frozen forever. A later PR
    that alters them — even while updating file_sha256 in the receipt to match — fails here,
    because the check compares the actual bytes across the merge base, not the recorded digest.

    On the introducing PR the file does not yet exist at the merge base, so there is nothing to
    ratchet against; the check instead verifies the committed bytes match the receipt digest,
    establishing the reference the byte-identity ratchet guards the moment this lands on the base
    branch. Either way the test asserts and passes — no skip.
    """
    _assert_immutable(
        _merge_base_bytes("warehouse/data/observations/product_adoption_baseline.parquet"),
        receipt,
    )


def test_ratchet_fires_on_a_byte_swap(receipt):
    """Prove the gate is real: any difference from the merge-base bytes fails, so a later PR
    cannot swap the bytes (even with a matching receipt update)."""
    with pytest.raises(AssertionError):
        _assert_immutable(PARQUET.read_bytes() + b"\x00", receipt)
