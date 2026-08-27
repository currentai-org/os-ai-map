"""GitHub Release persistence — the durable home for rollback bytes.

`build/release_persistence.py` packages a content-addressed deployment artifact into a GitHub Release
(CSV bundle + receipt.json + SHA256SUMS, tagged by publisher + artifact_id, refusing to replace an
existing tag), and writes durable append-only occurrence files for the reconciliation PR to commit.
The GitHub API is mocked here — these tests create no real Release.
"""

import tarfile

import build.deployment_archive as DA
import build.release_persistence as RP


def _csv(path, text):
    path.write_text(text, encoding="utf-8")
    return path


def _artifact(tmp_path):
    root = tmp_path / "archive"
    files = {
        "axis_facts.csv": _csv(tmp_path / "axis_facts.csv", "declaration_version_id,y\nabc,2\n"),
        "axis_results.csv": _csv(tmp_path / "axis_results.csv", "declaration_version_id,x\nabc,1\n"),
    }
    tables = {n: {"rows": 1, "sha256": DA.file_sha256(p)} for n, p in files.items()}
    aid = DA.ensure_artifact(root, files, tables, "gen-1")
    return root, aid


class _FakeReleases:
    def __init__(self, existing_tags=()):
        self.existing = set(existing_tags)
        self.created: list[str] = []
        self.uploaded: list[tuple[str, str]] = []

    def tag_exists(self, tag):
        return tag in self.existing

    def create_release(self, tag, name, body, target_commitish):
        self.created.append(tag)
        return "https://uploads.example/repos/x/releases/1/assets"

    def upload_asset(self, upload_url, name, path, content_type):
        self.uploaded.append((name, content_type))


# --- tag naming ----------------------------------------------------------------------------------


def test_release_tag_names_publisher_and_full_artifact_id():
    assert RP.release_tag("scoring-trace", "a" * 64) == f"artifact/scoring-trace/{'a' * 64}"


def test_unknown_publisher_is_rejected():
    try:
        RP.release_tag("nope", "a" * 64)
    except ValueError as exc:
        assert "publisher" in str(exc)
    else:
        raise AssertionError("release_tag must reject an unknown publisher")


# --- packaging -----------------------------------------------------------------------------------


def test_package_assets_bundles_the_csvs_and_includes_receipt_and_sums(tmp_path):
    root, aid = _artifact(tmp_path)
    assets = RP.package_assets(root, aid, tmp_path / "work")
    assert set(assets) == {RP.CSV_BUNDLE, DA.RECEIPT, DA.SHA256SUMS}
    with tarfile.open(assets[RP.CSV_BUNDLE], "r:gz") as tar:
        assert sorted(tar.getnames()) == ["axis_facts.csv", "axis_results.csv"]
    assert assets[DA.RECEIPT].name == "receipt.json"
    assert assets[DA.SHA256SUMS].name == "SHA256SUMS"


def test_package_assets_rejects_a_tampered_artifact(tmp_path):
    root, aid = _artifact(tmp_path)
    (DA.artifact_dir(root, aid) / "axis_results.csv").write_text("declaration_version_id,x\nabc,999\n", encoding="utf-8")
    try:
        RP.package_assets(root, aid, tmp_path / "work")
    except RuntimeError as exc:
        assert "hash mismatch" in str(exc)
    else:
        raise AssertionError("package_assets must verify the artifact before bundling")


# --- persist -------------------------------------------------------------------------------------


def test_dry_run_makes_no_github_call(tmp_path):
    root, aid = _artifact(tmp_path)
    summary = RP.persist_artifact(root, aid, "scoring-trace", client=None, dry_run=True)
    assert summary["created"] is False
    assert summary["tag"] == RP.release_tag("scoring-trace", aid)
    assert set(summary["assets"]) == {RP.CSV_BUNDLE, DA.RECEIPT, DA.SHA256SUMS}


def test_persist_creates_the_release_and_uploads_every_asset(tmp_path):
    root, aid = _artifact(tmp_path)
    client = _FakeReleases()
    summary = RP.persist_artifact(root, aid, "scoring-trace", client=client)
    assert summary["created"] is True
    assert client.created == [RP.release_tag("scoring-trace", aid)]
    assert {name for name, _ct in client.uploaded} == {RP.CSV_BUNDLE, DA.RECEIPT, DA.SHA256SUMS}


def test_persist_refuses_to_replace_an_existing_tag(tmp_path):
    root, aid = _artifact(tmp_path)
    client = _FakeReleases(existing_tags={RP.release_tag("scoring-trace", aid)})
    try:
        RP.persist_artifact(root, aid, "scoring-trace", client=client)
    except RuntimeError as exc:
        assert "already exists" in str(exc)
    else:
        raise AssertionError("persist_artifact must refuse to replace an existing tag")
    assert client.created == [] and client.uploaded == []  # nothing created/uploaded


# --- durable occurrence files --------------------------------------------------------------------


def test_write_repo_occurrence_is_append_only_and_pathed_by_publisher(tmp_path):
    occ = {"operation": "deploy", "deployment_id": "gen-1", "artifact_id": "b" * 64,
           "previous_artifact_id": None, "at": "2026-08-27T10:00:00+00:00"}
    path = RP.write_repo_occurrence(tmp_path, "evaluation", occ)
    assert path.exists()
    assert RP.REPO_OCCURRENCES.parts[:2] == ("warehouse", "deployments")
    assert "evaluation" in path.parts and path.read_text().strip().endswith("}")
    # Append-only: a second write of the same occurrence is refused.
    try:
        RP.write_repo_occurrence(tmp_path, "evaluation", occ)
    except RuntimeError as exc:
        assert "append-only" in str(exc)
    else:
        raise AssertionError("write_repo_occurrence must refuse to overwrite an existing occurrence file")
