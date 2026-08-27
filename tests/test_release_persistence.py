"""GitHub Release persistence — durable home for rollback bytes, with a failure-atomic flow.

`build/release_persistence.py` packages a content-addressed artifact into a GitHub Release
(draft → verify → publish), restores it back, and writes durable append-only occurrence files. The
GitHub API is mocked — these tests create no real Release. The #387 provenance gate is exercised via
a controllable `_adapter`, so an artifact's filename set is enforced without building the full corpus.
"""

import json
import tarfile

import pytest

import build.deployment_archive as DA
import build.release_persistence as RP


def _csv(path, text):
    path.write_text(text, encoding="utf-8")
    return path


def _recompute_tables(adir):
    # Enumerate the CSVs directly (glob), not via SHA256SUMS: restore recomputes the receipt from the
    # EXTRACTED csvs before any archive dir — and its SHA256SUMS — exists.
    return {p.name: {"rows": 1, "sha256": DA.file_sha256(p)} for p in sorted(adir.glob("*.csv"))}


def _recompute_did(adir):
    return "gen-" + DA.file_sha256(sorted(adir.glob("*.csv"))[0])[:8]


@pytest.fixture
def adapter(monkeypatch):
    """A controllable publisher adapter expecting exactly {a.csv, b.csv}."""
    expected = {"a.csv", "b.csv"}
    monkeypatch.setattr(RP, "_adapter", lambda publisher: (expected, _recompute_tables, _recompute_did))
    return expected


def _artifact(tmp_path, names=("a.csv", "b.csv")):
    root = tmp_path / "archive"
    files = {n: _csv(tmp_path / n, f"declaration_version_id,col\nabc,{i}\n") for i, n in enumerate(names)}
    tables = {n: {"rows": 1, "sha256": DA.file_sha256(p)} for n, p in files.items()}
    aid = DA.ensure_artifact(root, files, tables, "gen-" + DA.file_sha256(files[names[0]])[:8])
    return root, aid


class FakeReleases:
    def __init__(self):
        self.releases: dict[int, dict] = {}
        self._next = 1
        self.fail_after: int | None = None
        self._uploads = 0
        self.corrupt_uploads: set[str] = set()  # names to store as same-size, different bytes

    def published_release(self, tag):
        for r in self.releases.values():
            if r["tag"] == tag and not r["draft"]:
                return r
        return None

    def draft_release(self, tag):
        # Mirror the real client: match the intended tag_name AND the tool-owned marker in the body,
        # never the cosmetic display name.
        for r in self.releases.values():
            if r["draft"] and r["tag"] == tag and RP.DRAFT_MARKER in (r.get("body") or ""):
                return r
        return None

    def delete_release(self, release_id):
        self.releases.pop(release_id, None)

    def create_draft(self, tag, name, body, target_commitish=None):
        rid = self._next
        self._next += 1
        self.releases[rid] = {"id": rid, "tag": tag, "name": name, "body": body, "draft": True, "assets": {}}
        return {"id": rid, "upload_url": f"https://uploads.example/{rid}"}

    def list_assets(self, release_id):
        return [{"id": a["id"], "name": a["name"], "size": a["size"]}
                for a in self.releases[release_id]["assets"].values()]

    def upload_asset(self, upload_url, name, path, content_type):
        self._uploads += 1
        if self.fail_after is not None and self._uploads > self.fail_after:
            raise RuntimeError("simulated upload failure")
        rid = int(upload_url.rstrip("/").split("/")[-1])
        data = __import__("pathlib").Path(path).read_bytes()
        if name in self.corrupt_uploads:
            data = bytes((b ^ 0x01) for b in data)  # same length, different bytes — size check can't see it
        self.releases[rid]["assets"][name] = {"id": f"{rid}-{name}", "name": name, "size": len(data), "bytes": data}

    def publish_release(self, release_id):
        self.releases[release_id]["draft"] = False

    def download_asset(self, asset_id, dest):
        for r in self.releases.values():
            for a in r["assets"].values():
                if a["id"] == asset_id:
                    __import__("pathlib").Path(dest).write_bytes(a["bytes"])
                    return
        raise RuntimeError(f"asset {asset_id} not found")


# --- tag naming ----------------------------------------------------------------------------------


def test_release_tag_names_publisher_and_full_artifact_id():
    assert RP.release_tag("scoring-trace", "a" * 64) == f"artifact/scoring-trace/{'a' * 64}"


def test_unknown_publisher_is_rejected():
    with pytest.raises(ValueError):
        RP.release_tag("nope", "a" * 64)


def test_published_release_url_encodes_the_tag_slashes():
    """The tag's slashes must be percent-encoded in the REST path, or GitHub returns a false 404 —
    which would silently break completed-release detection, restore, and occurrence recording."""
    captured = {}
    client = RP.GitHubReleases("tok", "currentai-org/os-ai-map")
    client._request = lambda method, url, **kw: (captured.update(url=url) or (200, {"draft": False}))
    tag = RP.release_tag("evaluation", "a" * 64)
    client.published_release(tag)
    assert f"/releases/tags/artifact%2Fevaluation%2F{'a' * 64}" in captured["url"]
    assert "tags/artifact/evaluation" not in captured["url"]  # no raw slashes survive in the tag path


# --- packaging goes through the provenance gate ---------------------------------------------------


def test_package_assets_gates_then_bundles_exactly_the_expected_csvs(tmp_path, adapter):
    root, aid = _artifact(tmp_path)
    assets = RP.package_assets(root, aid, "evaluation", tmp_path / "work")
    assert set(assets) == {RP.CSV_BUNDLE, DA.RECEIPT, DA.SHA256SUMS}
    with tarfile.open(assets[RP.CSV_BUNDLE], "r:gz") as tar:
        assert sorted(tar.getnames()) == ["a.csv", "b.csv"]


def test_package_assets_rejects_a_wrong_filename_set(tmp_path, adapter):
    # Adapter expects {a.csv, b.csv}; this artifact has only a.csv — the gate must reject it.
    root, aid = _artifact(tmp_path, names=("a.csv",))
    with pytest.raises(RuntimeError):
        RP.package_assets(root, aid, "evaluation", tmp_path / "work")


def test_package_assets_rejects_a_tampered_artifact(tmp_path, adapter):
    root, aid = _artifact(tmp_path)
    (DA.artifact_dir(root, aid) / "a.csv").write_text("declaration_version_id,col\nabc,999\n", encoding="utf-8")
    with pytest.raises(RuntimeError):
        RP.package_assets(root, aid, "evaluation", tmp_path / "work")


# --- failure-atomic persist -----------------------------------------------------------------------


def test_dry_run_makes_no_github_call(tmp_path, adapter):
    root, aid = _artifact(tmp_path)
    summary = RP.persist_artifact(root, aid, "evaluation", client=None, dry_run=True)
    assert summary["created"] is False
    assert summary["tag"] == RP.release_tag("evaluation", aid)


def test_persist_drafts_uploads_verifies_then_publishes(tmp_path, adapter):
    root, aid = _artifact(tmp_path)
    client = FakeReleases()
    summary = RP.persist_artifact(root, aid, "evaluation", client=client)
    assert summary["created"] is True
    rel = client.published_release(RP.release_tag("evaluation", aid))
    assert rel is not None and rel["draft"] is False
    assert set(rel["assets"]) == {RP.CSV_BUNDLE, DA.RECEIPT, DA.SHA256SUMS}


def test_a_failed_upload_leaves_no_completed_release_and_is_retriable(tmp_path, adapter):
    root, aid = _artifact(tmp_path)
    tag = RP.release_tag("evaluation", aid)
    client = FakeReleases()
    client.fail_after = 1  # raise on the second asset upload

    with pytest.raises(RuntimeError):
        RP.persist_artifact(root, aid, "evaluation", client=client)
    assert client.published_release(tag) is None, "a partial upload must not leave a completed release"
    assert client.draft_release(tag) is not None, "the incomplete draft remains (no stranded tag)"

    # Retry succeeds: the incomplete draft is discarded and a fresh one published.
    client.fail_after = None
    summary = RP.persist_artifact(root, aid, "evaluation", client=client)
    assert summary["created"] is True
    assert client.published_release(tag) is not None


def test_persist_refuses_a_completed_release(tmp_path, adapter):
    root, aid = _artifact(tmp_path)
    client = FakeReleases()
    RP.persist_artifact(root, aid, "evaluation", client=client)  # first persist completes
    with pytest.raises(RuntimeError, match="already exists"):
        RP.persist_artifact(root, aid, "evaluation", client=client)


def test_persist_rejects_same_size_remote_corruption(tmp_path, adapter):
    """A remote asset with the RIGHT size but WRONG bytes passes a name+size check and is caught only
    by re-downloading and re-hashing before publish. The draft is never published."""
    root, aid = _artifact(tmp_path)
    tag = RP.release_tag("evaluation", aid)
    client = FakeReleases()
    client.corrupt_uploads = {DA.RECEIPT}  # stored same-size, one bit flipped
    with pytest.raises(RuntimeError, match="sha256"):
        RP.persist_artifact(root, aid, "evaluation", client=client)
    assert client.published_release(tag) is None, "a corrupt upload must not be published"


# --- restore --------------------------------------------------------------------------------------


def test_restore_downloads_rebuilds_and_passes_the_gate(tmp_path, adapter):
    root, aid = _artifact(tmp_path)
    client = FakeReleases()
    RP.persist_artifact(root, aid, "evaluation", client=client)

    # Wipe the local artifact; restore must rebuild it from the Release and pass the gate.
    import shutil
    shutil.rmtree(DA.artifact_dir(root, aid))
    assert not DA.artifact_dir(root, aid).exists()
    assert RP.restore_artifact(root, aid, "evaluation", client=client) == aid
    DA.verify_artifact(root, aid)


def test_restore_rejects_a_missing_asset(tmp_path, adapter):
    root, aid = _artifact(tmp_path)
    client = FakeReleases()
    RP.persist_artifact(root, aid, "evaluation", client=client)
    rel = client.published_release(RP.release_tag("evaluation", aid))
    del rel["assets"][DA.SHA256SUMS]  # drop an asset
    with pytest.raises(RuntimeError, match="assets"):
        RP.restore_artifact(root, aid, "evaluation", client=client)


def test_poisoned_receipt_restore_leaves_no_artifact(tmp_path, adapter):
    """A forged receipt (bytes intact, so it content-addresses correctly, but its `tables` tampered)
    is rejected BEFORE the atomic archive rename, so no poisoned content-addressed directory is left
    behind — restore is the only writer, and it creates nothing."""
    import shutil

    root, aid = _artifact(tmp_path)
    client = FakeReleases()
    RP.persist_artifact(root, aid, "evaluation", client=client)
    rel = client.published_release(RP.release_tag("evaluation", aid))
    doc = json.loads(rel["assets"][DA.RECEIPT]["bytes"].decode())
    doc["tables"] = {"a.csv": {"rows": 999, "sha256": "0" * 64}, "b.csv": {"rows": 1, "sha256": "0" * 64}}
    forged = json.dumps(doc).encode()
    rel["assets"][DA.RECEIPT].update(bytes=forged, size=len(forged))

    shutil.rmtree(DA.artifact_dir(root, aid))  # restore is the only writer now
    with pytest.raises(RuntimeError):
        RP.restore_artifact(root, aid, "evaluation", client=client)
    assert not DA.artifact_dir(root, aid).exists(), "a poisoned receipt must leave no artifact directory"


def test_restore_rejects_a_tampered_sha256sums(tmp_path, adapter):
    """The downloaded SHA256SUMS is CHECKED against the extracted CSVs, not ignored: a flipped hash
    fails the comparison, before any archive dir is created."""
    import shutil

    root, aid = _artifact(tmp_path)
    client = FakeReleases()
    RP.persist_artifact(root, aid, "evaluation", client=client)
    rel = client.published_release(RP.release_tag("evaluation", aid))
    text = rel["assets"][DA.SHA256SUMS]["bytes"].decode()
    tampered = text.replace(text[:64], "0" * 64, 1).encode()  # zero out the first recorded hash
    rel["assets"][DA.SHA256SUMS].update(bytes=tampered, size=len(tampered))

    shutil.rmtree(DA.artifact_dir(root, aid))
    with pytest.raises(RuntimeError, match="SHA256SUMS"):
        RP.restore_artifact(root, aid, "evaluation", client=client)
    assert not DA.artifact_dir(root, aid).exists()


def test_safe_extract_rejects_absolute_parent_and_link_members(tmp_path):
    def _bundle(add):
        p = tmp_path / f"{add}.tar.gz"
        with tarfile.open(p, "w:gz") as tar:
            add(tar)
        return p

    def abs_member(tar):
        f = tmp_path / "x"; f.write_text("x")
        info = tar.gettarinfo(str(f), arcname="/etc/evil"); tar.addfile(info, open(f, "rb"))

    def parent_member(tar):
        f = tmp_path / "y"; f.write_text("y")
        info = tar.gettarinfo(str(f), arcname="../evil"); tar.addfile(info, open(f, "rb"))

    def link_member(tar):
        info = tarfile.TarInfo("link"); info.type = tarfile.SYMTYPE; info.linkname = "/etc/passwd"
        tar.addfile(info)

    for maker in (abs_member, parent_member, link_member):
        with pytest.raises(RuntimeError):
            RP._safe_extract(_bundle(maker), tmp_path / "out")


# --- durable occurrences --------------------------------------------------------------------------


def test_write_repo_occurrence_is_append_only_and_pathed_by_publisher(tmp_path):
    occ = {"operation": "deploy", "deployment_id": "gen-1", "artifact_id": "b" * 64,
           "previous_artifact_id": None, "at": "2026-08-27T10:00:00+00:00"}
    path = RP.write_repo_occurrence(tmp_path, "evaluation", occ)
    assert path.exists() and "evaluation" in path.parts
    assert RP.REPO_OCCURRENCES.parts[:2] == ("warehouse", "deployments")
    with pytest.raises(RuntimeError, match="append-only"):
        RP.write_repo_occurrence(tmp_path, "evaluation", occ)


def _record_occurrence_for(root, aid):
    """Append a local occurrence whose deployment_id matches the artifact's reconstructed identity."""
    did = _recompute_did(DA.artifact_dir(root, aid))
    DA.record_occurrence(root, "deploy", did, aid, None, at="2026-08-27T10:00:00+00:00")


def test_record_local_occurrence_gates_confirms_release_and_stamps_the_tag(tmp_path, adapter):
    root, aid = _artifact(tmp_path)
    client = FakeReleases()
    RP.persist_artifact(root, aid, "evaluation", client=client)  # the completed Release exists + verifies
    _record_occurrence_for(root, aid)
    path = RP.record_local_occurrence(root, tmp_path / "repo", "evaluation", client)
    written = json.loads(path.read_text())
    assert written["artifact_id"] == aid and written["operation"] == "deploy"
    assert written["release_tag"] == RP.release_tag("evaluation", aid)  # bound to its durable home


def test_record_local_occurrence_with_no_occurrence_is_an_error(tmp_path):
    with pytest.raises(RuntimeError, match="nothing to persist"):
        RP.record_local_occurrence(tmp_path / "empty", tmp_path / "repo", "evaluation", FakeReleases())


def test_record_local_occurrence_rejects_a_wrong_publisher_artifact(tmp_path, monkeypatch):
    """An occurrence naming an artifact whose tables are NOT this publisher's (scoring-trace recorded
    under evaluation) is rejected by the gate's exact filename-set check — nothing is written."""
    root, aid = _artifact(tmp_path, names=("a.csv", "b.csv"))
    _record_occurrence_for(root, aid)
    # The named publisher expects a DIFFERENT table set than the artifact carries.
    monkeypatch.setattr(RP, "_adapter",
                        lambda publisher: ({"x.csv", "y.csv", "z.csv"}, _recompute_tables, _recompute_did))
    repo = tmp_path / "repo"
    with pytest.raises(RuntimeError):
        RP.record_local_occurrence(root, repo, "evaluation", FakeReleases())
    assert not repo.exists() or not list(repo.rglob("*.json")), "a rejected record writes no durable file"


def test_record_local_occurrence_requires_a_completed_release(tmp_path, adapter):
    """Even when the local gate passes, an occurrence whose bytes were never published is refused."""
    root, aid = _artifact(tmp_path)
    _record_occurrence_for(root, aid)
    with pytest.raises(RuntimeError, match="no completed release"):
        RP.record_local_occurrence(root, tmp_path / "repo", "evaluation", FakeReleases())


def test_record_local_occurrence_requires_a_complete_release(tmp_path, adapter):
    """A Release missing an asset fails the remote-content confirmation — nothing is recorded."""
    root, aid = _artifact(tmp_path)
    client = FakeReleases()
    RP.persist_artifact(root, aid, "evaluation", client=client)
    _record_occurrence_for(root, aid)
    del client.published_release(RP.release_tag("evaluation", aid))["assets"][DA.SHA256SUMS]
    with pytest.raises(RuntimeError, match="assets"):
        RP.record_local_occurrence(root, tmp_path / "repo", "evaluation", client)
