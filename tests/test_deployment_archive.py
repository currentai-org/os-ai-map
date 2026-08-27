"""The shared deployment archive: content addressing, explicit operations, atomic staging.

`build/deployment_archive.py` is the rollback record shared by the evaluation and scoring-trace
publishers. These pin the integrity properties: a byte identity distinct from the semantic
generation, hash-verified artifacts, an atomic archive that survives interruption, and live-state
from an append-only occurrence log rather than directory mtimes.
"""

import build.deployment_archive as A


def _csv(path, text):
    path.write_text(text, encoding="utf-8")
    return path


def _files(tmp_path, text="declaration_version_id,x\nabc,1\n"):
    return {"t.csv": _csv(tmp_path / "t.csv", text)}


# --- content addressing: artifact_id is a byte identity, not the semantic generation --------------


def test_same_generation_different_bytes_are_different_artifacts(tmp_path):
    """The core of review point 1: identical declaration/observation ids but different bytes (a
    regenerated evaluated_at) must yield different artifact_ids — never mistaken for the same."""
    a = {"t.csv": _csv(tmp_path / "a.csv", "declaration_version_id,evaluated_at\nabc,2026-08-27T10:00:00\n")}
    b = {"t.csv": _csv(tmp_path / "b.csv", "declaration_version_id,evaluated_at\nabc,2026-08-27T11:00:00\n")}
    assert A.artifact_id(a) != A.artifact_id(b)
    # ...and identical bytes are the same artifact.
    c = {"t.csv": _csv(tmp_path / "c.csv", "declaration_version_id,evaluated_at\nabc,2026-08-27T10:00:00\n")}
    assert A.artifact_id(a) == A.artifact_id(c)


def test_ensure_artifact_is_content_addressed_and_idempotent(tmp_path):
    root = tmp_path / "archive"
    aid = A.ensure_artifact(root, _files(tmp_path), {"t.csv": {"rows": 1}}, "gen-1")
    adir = A.artifact_dir(root, aid)
    assert adir.name == aid and (adir / "t.csv").exists()
    assert (adir / A.RECEIPT).exists() and (adir / A.SHA256SUMS).exists()
    written = adir.stat().st_mtime_ns
    # Re-ensuring the same bytes verifies and returns the same id without rewriting.
    assert A.ensure_artifact(root, _files(tmp_path), {"t.csv": {"rows": 1}}, "gen-1") == aid
    assert adir.stat().st_mtime_ns == written


# --- exact hash verification ----------------------------------------------------------------------


def test_verify_artifact_passes_for_intact_and_raises_for_tampered(tmp_path):
    root = tmp_path / "archive"
    aid = A.ensure_artifact(root, _files(tmp_path), {}, "gen-1")
    A.verify_artifact(root, aid)  # intact: no raise

    # Tamper with an archived byte; verification must catch it (rollback-with-altered-bytes rejected).
    (A.artifact_dir(root, aid) / "t.csv").write_text("declaration_version_id,x\nabc,999\n", encoding="utf-8")
    try:
        A.verify_artifact(root, aid)
    except RuntimeError as exc:
        assert "hash mismatch" in str(exc)
    else:
        raise AssertionError("verify_artifact must reject an artifact whose bytes were altered")


def test_verify_artifact_raises_for_absent(tmp_path):
    try:
        A.verify_artifact(tmp_path / "archive", "0" * 64)
    except RuntimeError as exc:
        assert "not archived" in str(exc)
    else:
        raise AssertionError("verify_artifact must reject an id that is not archived")


# --- atomic staging: an interrupted write leaves no valid artifact and no occurrence --------------


def test_interrupted_archive_creation_leaves_no_valid_artifact(tmp_path):
    root = tmp_path / "archive"
    aid = A.artifact_id(_files(tmp_path))
    # Simulate an interrupted write: a partial staging directory under the eventual artifact id.
    staging = A.artifacts_root(root) / f"{A._STAGING_PREFIX}{aid}"
    staging.mkdir(parents=True)
    (staging / "t.csv").write_text("partial", encoding="utf-8")  # no receipt, no SHA256SUMS

    # The real artifact does not exist, verification refuses it, and nothing is live.
    assert not A.artifact_dir(root, aid).exists()
    try:
        A.verify_artifact(root, aid)
    except RuntimeError:
        pass
    else:
        raise AssertionError("a partial staging dir must not verify as an artifact")
    assert A.current_live(root) is None

    # A subsequent ensure discards the stale staging and completes atomically.
    assert A.ensure_artifact(root, _files(tmp_path), {}, "gen-1") == aid
    A.verify_artifact(root, aid)


# --- the append-only occurrence log ---------------------------------------------------------------


def test_empty_root_reads_as_no_live_state_and_creates_nothing(tmp_path):
    root = tmp_path / "archive"
    assert A.occurrences(root) == []
    assert A.current_live(root) is None
    assert A.current_live_artifact_id(root) is None
    assert not root.exists()


def test_occurrences_record_operation_ids_and_previous(tmp_path):
    root = tmp_path / "archive"
    A.record_occurrence(root, "deploy", "gen-1", "aid-1", None, at="2026-01-01T00:00:00+00:00")
    A.record_occurrence(root, "deploy", "gen-2", "aid-2", "aid-1", at="2026-01-02T00:00:00+00:00")
    A.record_occurrence(root, "rollback", "gen-1", "aid-1", "aid-2", at="2026-01-03T00:00:00+00:00")
    occ = A.occurrences(root)
    assert [o["operation"] for o in occ] == ["deploy", "deploy", "rollback"]
    assert [o["artifact_id"] for o in occ] == ["aid-1", "aid-2", "aid-1"]
    assert [o["previous_artifact_id"] for o in occ] == [None, "aid-1", "aid-2"]
    assert A.current_live_artifact_id(root) == "aid-1"  # the rollback re-pointed live


def test_live_state_is_from_occurrences_not_directory_mtime(tmp_path):
    root = tmp_path / "archive"
    a1 = A.ensure_artifact(root, {"t.csv": _csv(tmp_path / "a.csv", "declaration_version_id,x\nabc,1\n")}, {}, "gen-1")
    a2 = A.ensure_artifact(root, {"t.csv": _csv(tmp_path / "b.csv", "declaration_version_id,x\nabc,2\n")}, {}, "gen-2")
    A.record_occurrence(root, "deploy", "gen-1", a1, None, at="2026-01-01T00:00:00+00:00")
    A.record_occurrence(root, "deploy", "gen-2", a2, a1, at="2026-01-02T00:00:00+00:00")
    # Make a1 the newest directory by mtime; the occurrence log still says a2 is live.
    (A.artifact_dir(root, a1) / "touch").write_text("x", encoding="utf-8")
    assert A.current_live_artifact_id(root) == a2


def test_bad_operation_is_rejected(tmp_path):
    try:
        A.record_occurrence(tmp_path / "archive", "sideways", "gen", "aid", None)
    except ValueError as exc:
        assert "deploy" in str(exc)
    else:
        raise AssertionError("record_occurrence must reject an unknown operation")
