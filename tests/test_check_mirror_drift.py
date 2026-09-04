"""The mirror-drift sentinel must separate five findings from each other, and from silence.

Written against a stub client rather than the platform, because the whole value of the gate
is the distinction it draws between "the mirror is stale", "the same revision number now
means different bytes", "the numbers agree and the code does not", "the numbers moved and the
code did not", and "we could not tell". Those are five different things a maintainer does five
different things about; only the fourth is not a resync, and only the last must never be
reported as a pass.

The stub returns platform nodes in the shape `GetDataModel` actually returns -- a
`latestRevision` carrying `revisionNumber`, `hash`, `code` and `createdAt` -- so the
comparison being tested is the real one.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from build.check_mirror_drift import (
    check,
    compare,
    main,
    mirror_contracts,
    strip_mirror_banner,
)
from build.oso_mcp import MCPCallFailed, MCPUnreachable

ROOT = Path(__file__).resolve().parent.parent

SQL_BANNER = (
    "-- ────── PLATFORM MIRROR (read-only) ──────\n"
    "-- A snapshot of a model that runs on the OSO platform.\n"
    "-- The platform is the source of truth.\n"
    "-- Nothing deploys from this copy.\n"
    "\n"
)
PY_BANNER = SQL_BANNER.replace("-- ", "# ").replace("--", "#")
DEPLOYED = "SELECT 1 AS answer\n"


def build_tree(tmp_path: Path, body: str = DEPLOYED, banner: str = SQL_BANNER) -> dict:
    """A one-contract repo on disk, and the contract dict that describes it."""
    model = tmp_path / "warehouse/models/scores/thing.sql"
    model.parent.mkdir(parents=True, exist_ok=True)
    model.write_text(banner + body)
    return {
        "table": "currentai.scores.thing",
        "files": {"model": "warehouse/models/scores/thing.sql"},
        "mirror": {
            "model_id": "a-model-id",
            "revision": 4,
            "hash": "platformhash",
            "local_sha256": "irrelevant here -- dependency_violations owns that check",
        },
    }


def node(revision: int = 4, hash_: str = "platformhash", code: str = DEPLOYED) -> dict:
    return {"latestRevision": {"revisionNumber": revision, "hash": hash_, "code": code,
                               "createdAt": "2026-09-01T00:00:00.000Z"}}


class StubClient:
    """Returns a canned node, or raises, per `data_model` call."""

    def __init__(self, result):
        self.result = result
        self.calls: list[str] = []

    def data_model(self, model_id: str):
        self.calls.append(model_id)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


# --- the banner, which is why a naive comparison fails on every contract ---------------

def test_the_banner_is_stripped_in_both_comment_forms():
    """SQL mirrors comment with `--` and Python mirrors with `#`; both carry the header."""
    assert strip_mirror_banner(SQL_BANNER + DEPLOYED) == DEPLOYED
    assert strip_mirror_banner(PY_BANNER + DEPLOYED) == DEPLOYED


def test_a_file_with_no_banner_is_compared_as_it_stands():
    """Not an error. A mirror that lost its header is code drift and is reported as such."""
    assert strip_mirror_banner(DEPLOYED) == DEPLOYED


# --- the four findings ------------------------------------------------------------------

def test_a_matching_contract_is_ok(tmp_path):
    row = compare(build_tree(tmp_path), node(), tmp_path)
    assert row.status == "ok"
    assert not row.drifted
    assert (row.hash_match, row.code_match) == (True, True)
    assert row.platform_revision == row.contract_revision == 4


def test_a_newer_platform_revision_over_different_code_is_revision_drift(tmp_path):
    row = compare(build_tree(tmp_path), node(revision=5, hash_="newhash", code="SELECT 2\n"),
                  tmp_path)
    assert row.status == "revision"
    assert row.drifted
    assert (row.contract_revision, row.platform_revision) == (4, 5)
    assert "latest revision is 5" in row.detail
    assert "does not match" in row.detail


def test_the_same_revision_with_a_different_hash_over_different_code_is_hash_drift(tmp_path):
    """The worst of the three: the number the repo pins now denotes different content."""
    row = compare(build_tree(tmp_path), node(hash_="rewritten", code="SELECT 2\n"), tmp_path)
    assert row.status == "hash"
    assert row.drifted
    assert row.hash_match is False
    assert "rewritten" in row.detail


# --- the revision the platform minted over code it did not touch -------------------------

def test_a_newer_platform_revision_over_identical_code_is_metadata_only(tmp_path):
    """A cron cleared or a description added. The contract is behind by a number and by
    nothing else, so sending a maintainer to resync would be sending them to copy a file
    onto itself. A NEW revision is required, which is what separates this from the hash case
    below."""
    row = compare(build_tree(tmp_path), node(revision=5, hash_="newhash"), tmp_path)
    assert row.status == "metadata-only"
    assert not row.drifted
    assert row.metadata_only
    assert (row.hash_match, row.code_match) == (False, True)
    assert "byte-identical" in row.detail


def test_a_hash_change_with_no_new_revision_stays_hash_drift(tmp_path):
    """Identical code does NOT make this metadata-only. There is no new revision to record, the
    coherence gate rejects a marker whose revision does not advance, and so calling it
    metadata-only would tell a maintainer to make a commit the repo's own gate refuses. It is a
    mis-pinned hash or an in-place rewrite, and it stays loud."""
    row = compare(build_tree(tmp_path), node(hash_="rewritten"), tmp_path)
    assert row.status == "hash"
    assert row.drifted
    assert row.code_match is True
    assert "mis-pin" in row.detail


def test_a_metadata_only_sweep_exits_zero_and_names_the_marker(tmp_path, capsys):
    """Exit 0, because there is no stale mirror -- but the run still says what to record."""
    write_dependencies(tmp_path, [build_tree(tmp_path)])
    code = main([], root=tmp_path, client=StubClient(node(revision=5, hash_="newhash")))
    out = capsys.readouterr().out
    assert code == 0
    assert "0 drifted" in out
    assert "1 of them over a metadata-only revision" in out
    assert "code_unchanged_from" in out
    assert "Mirror resync" not in out


def test_a_metadata_only_row_is_counted_apart_in_the_report(tmp_path):
    write_dependencies(tmp_path, [build_tree(tmp_path)])
    report = tmp_path / "drift.json"
    code = main(["--report", str(report)], root=tmp_path,
                client=StubClient(node(revision=5, hash_="newhash")))
    assert code == 0
    payload = json.loads(report.read_text())
    assert (payload["checked"], payload["drifted"], payload["metadata_only"]) == (1, 0, 1)
    assert payload["rows"][0]["status"] == "metadata-only"


def test_matching_numbers_over_different_source_is_code_drift(tmp_path):
    """The check that a hand-edited mirror with a refreshed local_sha256 cannot defeat."""
    row = compare(build_tree(tmp_path, body="SELECT 2 AS answer\n"), node(), tmp_path)
    assert row.status == "code"
    assert (row.hash_match, row.code_match) == (True, False)


def test_a_model_id_the_platform_does_not_serve_is_missing(tmp_path):
    row = compare(build_tree(tmp_path), None, tmp_path)
    assert row.status == "missing"
    assert row.platform_revision is None
    assert "a-model-id" in row.detail


def test_a_mirror_file_that_is_gone_is_reported_not_raised(tmp_path):
    contract = build_tree(tmp_path)
    (tmp_path / contract["files"]["model"]).unlink()
    row = compare(contract, node(), tmp_path)
    assert row.status == "code"
    assert "is missing" in row.detail


# --- the sweep and the exit codes -------------------------------------------------------

def write_dependencies(tmp_path: Path, contracts: list[dict]) -> None:
    path = tmp_path / "warehouse/dependencies.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump({"version": 1, "dependencies": contracts}))


def test_a_clean_sweep_exits_zero_and_writes_the_report(tmp_path, capsys):
    contract = build_tree(tmp_path)
    write_dependencies(tmp_path, [contract])
    report = tmp_path / "drift.json"
    code = main(["--report", str(report)], root=tmp_path, client=StubClient(node()))
    assert code == 0
    assert "[OK]" in capsys.readouterr().out
    payload = json.loads(report.read_text())
    assert (payload["checked"], payload["drifted"]) == (1, 0)
    assert payload["rows"][0]["status"] == "ok"


def test_any_drift_exits_one_and_names_the_runbook(tmp_path, capsys):
    write_dependencies(tmp_path, [build_tree(tmp_path)])
    code = main([], root=tmp_path,
                client=StubClient(node(revision=9, hash_="h9", code="SELECT 2\n")))
    assert code == 1
    out = capsys.readouterr().out
    assert "1 drifted" in out
    assert "Mirror resync" in out


@pytest.mark.parametrize("failure, cause", [
    (MCPUnreachable("403 from the edge"), "could not be reached"),
    # A 200 carrying isError -- what an expired or rotated OSO_API_KEY looks like. This one
    # used to escape as a traceback and exit 1, the drift code, which would have sent a
    # maintainer to diff seventeen mirror files against a platform nobody can read.
    (MCPCallFailed("GetDataModel failed: UNAUTHENTICATED: User is not authenticated"),
     "refused the call"),
])
def test_anything_that_prevents_checking_exits_two_and_names_the_cause(
        tmp_path, capsys, failure, cause):
    """Exit 2, never 1 and never 0. See the module docstring on why the line matters."""
    write_dependencies(tmp_path, [build_tree(tmp_path)])
    code = main([], root=tmp_path, client=StubClient(failure))
    assert code == 2
    captured = capsys.readouterr()
    assert "[CANNOT CHECK]" in captured.err
    assert cause in captured.err
    assert "This is not a pass" in captured.err
    assert "it is not drift" in captured.err
    assert "[OK]" not in captured.out


def test_a_report_is_not_written_when_nothing_could_be_checked(tmp_path):
    """A stale report read as a fresh one is the failure mode a --report file invites."""
    write_dependencies(tmp_path, [build_tree(tmp_path)])
    report = tmp_path / "drift.json"
    code = main(["--report", str(report)], root=tmp_path,
                client=StubClient(MCPCallFailed("UNAUTHENTICATED")))
    assert code == 2
    assert not report.exists()


def test_a_transport_failure_mid_sweep_is_not_a_partial_result(tmp_path):
    """Half a sweep is not a result, so the exception propagates out of `check`."""
    write_dependencies(tmp_path, [build_tree(tmp_path)])
    with pytest.raises(MCPUnreachable):
        check([build_tree(tmp_path)], StubClient(MCPUnreachable("timeout")), tmp_path)


# --- the real contracts -----------------------------------------------------------------

def test_every_real_mirror_contract_is_in_scope():
    """The sweep must cover every mirror-bearing contract, and only those.

    An `oso.*` upstream anchors on a content contract and has no revision to compare, so it
    is out of scope. This asserts the split rather than a count, so adding a contract does
    not need this test edited -- but dropping mirrors out of the sweep fails it.
    """
    contracts = mirror_contracts(ROOT)
    assert contracts, "no mirror contracts found; the sweep would pass vacuously"
    doc = yaml.safe_load((ROOT / "warehouse/dependencies.yaml").read_text())
    expected = [d for d in doc["dependencies"] if d.get("mirror")]
    assert [c["table"] for c in contracts] == [d["table"] for d in expected]
    for contract in contracts:
        assert contract["table"].startswith("currentai."), contract["table"]
        assert contract["mirror"].get("model_id"), contract["table"]
        assert (ROOT / contract["files"]["model"]).exists(), contract["table"]
