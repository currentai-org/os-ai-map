"""The shared deployment archive: immutable identity + append-only occurrence log.

`build/deployment_archive.py` is the rollback record shared by the evaluation and scoring-trace
publishers. These tests pin the properties the cutover plan depends on: live state is read from the
occurrence log (never directory mtimes), a rollback is an occurrence rather than a rewrite, and
publishing from an archive never nests a new archive inside the bytes being restored.
"""

import build.deployment_archive as A


def _candidate(tmp_path, name, text="a,b\n1,2\n"):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def _files(tmp_path):
    return {"t.csv": _candidate(tmp_path, "t.csv")}


def test_empty_root_reads_as_no_live_state_and_creates_nothing(tmp_path):
    root = tmp_path / "archive"
    assert A.occurrences(root) == []
    assert A.current_live(root) is None
    assert A.current_live_archive(root) is None
    assert not root.exists(), "reading live state must not create the archive root"


def test_a_fresh_identity_is_a_deploy_and_becomes_live(tmp_path):
    root = tmp_path / "archive"
    target, kind = A.store(root, "id-A", _files(tmp_path), {"t": {"rows": 1}}, at="2026-01-01T00:00:00+00:00")
    assert kind == "deploy"
    assert target == A.archive_path(root, "id-A")
    assert (target / "t.csv").exists() and (target / "receipt.json").exists()
    assert A.current_live(root) == "id-A"


def test_a_new_identity_advances_live_and_both_are_deploys(tmp_path):
    root = tmp_path / "archive"
    A.store(root, "id-A", _files(tmp_path), {}, at="2026-01-01T00:00:00+00:00")
    A.store(root, "id-B", _files(tmp_path), {}, at="2026-01-02T00:00:00+00:00")
    assert [o["kind"] for o in A.occurrences(root)] == ["deploy", "deploy"]
    assert [o["deployment_id"] for o in A.occurrences(root)] == ["id-A", "id-B"]
    assert A.current_live(root) == "id-B"


def test_rollback_to_a_prior_identity_is_an_occurrence_not_a_rewrite(tmp_path):
    root = tmp_path / "archive"
    a_target, _ = A.store(root, "id-A", _files(tmp_path), {}, at="2026-01-01T00:00:00+00:00")
    A.store(root, "id-B", _files(tmp_path), {}, at="2026-01-02T00:00:00+00:00")
    a_written = a_target.stat().st_mtime_ns

    target, kind = A.store(root, "id-A", _files(tmp_path), {}, at="2026-01-03T00:00:00+00:00")
    assert kind == "rollback"
    assert target == a_target
    assert a_target.stat().st_mtime_ns == a_written, "the immutable archive was rewritten on rollback"
    assert [o["kind"] for o in A.occurrences(root)] == ["deploy", "deploy", "rollback"]
    assert A.current_live(root) == "id-A", "rollback re-points live at the restored identity"


def test_live_state_comes_from_occurrences_not_directory_mtime(tmp_path):
    root = tmp_path / "archive"
    a_target, _ = A.store(root, "id-A", _files(tmp_path), {}, at="2026-01-01T00:00:00+00:00")
    A.store(root, "id-B", _files(tmp_path), {}, at="2026-01-02T00:00:00+00:00")
    # Make id-A the newest directory by mtime; the occurrence log still says id-B is live.
    (a_target / "touch").write_text("x", encoding="utf-8")
    assert A.current_live(root) == "id-B"
    assert A.current_live_archive(root) == A.archive_path(root, "id-B")


def test_publishing_from_an_archive_never_nests(tmp_path):
    """Republishing a prior archive's bytes writes its occurrence to the fixed root, not inside the
    archive directory it is reading from."""
    root = tmp_path / "archive"
    a_target, _ = A.store(root, "id-A", _files(tmp_path), {}, at="2026-01-01T00:00:00+00:00")
    A.store(root, "id-B", _files(tmp_path), {}, at="2026-01-02T00:00:00+00:00")

    # "Publish from the archive": the candidate files are read from inside id-A's archive dir, but
    # the archive root is the fixed canonical root — so id-A is restored as a rollback occurrence and
    # nothing is written inside a_target.
    before = set(a_target.iterdir())
    _, kind = A.store(root, "id-A", {"t.csv": a_target / "t.csv"}, {}, at="2026-01-03T00:00:00+00:00")
    assert kind == "rollback"
    assert set(a_target.iterdir()) == before, "an archive was nested inside the bytes being restored"
    assert not A.archive_path(a_target, "id-A").exists()
    assert not (a_target / A.OCCURRENCES).exists()
    assert A.current_live(root) == "id-A"


def test_bad_occurrence_kind_is_rejected(tmp_path):
    root = tmp_path / "archive"
    try:
        A.record_occurrence(root, "sideways", "id-A")
    except ValueError as exc:
        assert "deploy" in str(exc)
    else:
        raise AssertionError("record_occurrence must reject an unknown kind")
