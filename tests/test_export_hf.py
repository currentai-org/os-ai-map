"""The Hugging Face export publishes what the map publishes, and publishes it safely.

Real-corpus tests assert invariants, never a census: no row count here is typed in. The history
rebuild (one worktree per release tag) is exercised by the export itself, in the release workflow
and in a rehearsal; here the corpus fixture skips it and the verification rule is tested on its
own, with payloads built to fail it.
"""
import copy
import json
import re
from types import SimpleNamespace

import pytest

from build import export_hf
from build.serialize import ROOT, build_payload
from build.validate import load_sources
from build.vocabulary import axes


@pytest.fixture(scope="module")
def built():
    sources = load_sources(ROOT)
    frozen = json.load(open(ROOT / "sources" / "snapshots" / "long_tail.json"))
    payload = build_payload(sources, frozen, generated="2026-01-01")
    head = export_hf._git("rev-parse", "HEAD").strip()
    history, provenance = export_hf.history_tables(payload, payload["version"], head,
                                                   verify=False)
    tables = export_hf.current_tables(sources, payload) | history
    return sources, payload, tables, head, provenance


# --- current-state tables ----------------------------------------------------------------------

def test_products_are_the_published_rows(built):
    _, payload, tables, _, _ = built
    site = {r["slug"]: r for c in payload["categories"].values() for r in c["products"]}
    rows = tables["products"].to_pylist()
    assert len(rows) == payload["n_total"] == len(site)
    for r in rows:
        s = site[r["slug"]]
        assert (r["openness_score"], r["adoption_level"], r["capability_score"],
                r["overall_score"], r["overall_basis"], r["tier"], r["mature"]) == (
            s["openness"].get("score"), s["adoption"].get("level"), s["capability"].get("score"),
            s.get("overall_score"), s.get("overall_basis"), s.get("tier"), s.get("mature"))


def test_categories_carry_the_published_stage_and_gaps(built):
    _, payload, tables, _, _ = built
    for r in tables["categories"].to_pylist():
        cat = payload["categories"][r["slug"]]
        assert (r["stage_num"], r["gaps"], r["product_count"]) == (
            cat["stage"]["num"], cat["gaps"], len(cat["products"]))


def test_citations_are_every_source_of_every_published_product(built):
    sources, _, tables, _, _ = built
    published = set(tables["products"].column("slug").to_pylist())
    expected = sum(len((sources["scores"][s].get(ax) or {}).get("sources") or [])
                   for s in published for ax in axes())
    cites = tables["citations"]
    assert cites.num_rows == expected
    assert set(cites.column("product_slug").to_pylist()) <= published
    assert sum(tables["products"].column("citation_count").to_pylist()) == expected


def test_keys_join(built):
    _, _, t, _, _ = built
    orgs = set(t["organizations"].column("slug").to_pylist())
    cats = set(t["categories"].column("slug").to_pylist())
    slugs = t["products"].column("slug").to_pylist()
    assert len(slugs) == len(set(slugs))
    assert set(t["products"].column("organization_slug").to_pylist()) <= orgs
    assert set(t["products"].column("category_slug").to_pylist()) <= cats
    assert set(t["product_history"].column("current_slug").drop_null().to_pylist()) <= set(slugs)


# --- history -----------------------------------------------------------------------------------

def test_history_has_one_snapshot_per_release_tag_and_names_every_product(built):
    _, _, t, head, provenance = built
    tagged = [v for v, sha in export_hf.release_tags() if _has_payload(sha)]
    versions = list(dict.fromkeys(t["product_history"].column("version").to_pylist()))
    assert versions[:len(tagged)] == tagged
    assert [p["version"] for p in provenance] == versions
    assert t["product_history"].column("product_slug").null_count == 0
    # The live tree joins the series only as a labelled pre-release.
    assert all(v in tagged or v.endswith(f"+{head[:8]}") for v in versions)


def test_history_rows_name_the_commit_that_wrote_their_payload(built):
    _, _, t, _, provenance = built
    for p in provenance:
        if p["tag_commit"] is None:
            continue
        # The payload commit is the tag itself or an ancestor of it.
        export_hf._git("merge-base", "--is-ancestor", p["payload_commit"], p["tag_commit"])
        assert export_hf._git("diff", "--quiet", p["payload_commit"], p["tag_commit"], "--",
                              "build/notebook_data.json") == ""
    rows = t["product_history"].to_pylist()
    assert all(r["payload_commit"] for r in rows if r["released"] is not None)


def _has_payload(sha: str) -> bool:
    try:
        export_hf._git("cat-file", "-e", f"{sha}:build/notebook_data.json")
        return True
    except Exception:
        return False


def _payload(version=None, tier="leading", generated="2026-01-01"):
    p = {"generated": generated, "order": ["c"], "aliases": {"products": {}},
         "categories": {"c": {"label": "C", "stage": {"num": 3, "name": "x"}, "gaps": [],
                              "products": [{"slug": "p", "product": "P", "tier": tier,
                                            "freshness": {"as_of": generated}}]}}}
    if version:
        p["version"] = version
    return p


def test_a_payload_labelled_as_another_release_is_rejected():
    with pytest.raises(export_hf.HistoryError, match="labels itself"):
        export_hf.verify_snapshot("0.5.0", "0.4.0", _payload("0.3.0"), _payload("0.5.0"))
    with pytest.raises(export_hf.HistoryError, match="labels itself"):
        export_hf.verify_snapshot("0.5.0", "0.4.0", _payload("0.6.0"), _payload("0.5.0"))


def test_a_lagging_label_is_accepted_only_when_the_content_is_the_tags():
    # Labelled with the previous release, content identical to the tag's rebuild: accepted, and
    # recorded as lagging rather than relabelled silently.
    how = export_hf.verify_snapshot("0.5.0", "0.4.0", _payload("0.4.0"),
                                    _payload("0.5.0", generated="2000-01-01"))
    assert how == "rebuilt-identical; version label lags the tag"
    # Same label, but the content is a step behind the tag: rejected.
    with pytest.raises(export_hf.HistoryError, match="differs from a rebuild"):
        export_hf.verify_snapshot("0.5.0", "0.4.0", _payload("0.4.0", tier="strong"),
                                  _payload("0.5.0"))


def test_content_must_match_the_rebuild_even_when_the_label_matches():
    with pytest.raises(export_hf.HistoryError, match="differs from a rebuild"):
        export_hf.verify_snapshot("0.5.0", "0.4.0", _payload("0.5.0", tier=None),
                                  _payload("0.5.0"))
    assert export_hf.verify_snapshot("0.5.0", "0.4.0", _payload("0.5.0"),
                                     _payload("0.5.0")) == "rebuilt-identical"


def test_an_unverified_snapshot_says_so():
    assert export_hf.verify_snapshot("0.1.0", None, _payload(), None) == "unverified"


# --- card and manifest -------------------------------------------------------------------------

@pytest.mark.parametrize("release_tag", ["v9.9.9", None, "rehearsal-0123abcd"])
def test_card_and_manifest_render_completely(built, tmp_path, release_tag):
    _, payload, tables, head, provenance = built
    manifest = export_hf.write(tmp_path, tables, payload, head, release_tag, "org/name",
                               provenance)
    card = (tmp_path / "README.md").read_text()
    assert not re.search(r"\$\w", card), "unfilled template placeholder in the card"
    configs = re.findall(r"data_files: (\S+)", card)
    assert sorted(configs) == sorted(manifest["files"])
    for path in configs:
        assert (tmp_path / path).exists()
    assert manifest["release_tag"] == release_tag
    assert manifest["source_commit"] == head
    assert manifest["history_verified"] is False  # the fixture skipped the rebuild
    assert ("do not publish" in card) is (release_tag != "v9.9.9")


def test_content_digest_ignores_the_parquet_writer(built, tmp_path):
    _, payload, tables, head, provenance = built
    a = export_hf.write(tmp_path / "a", tables, payload, head, None, "org/name", provenance)
    b = export_hf.write(tmp_path / "b", tables, {**payload, "generated": "2099-01-01"}, head,
                        None, "org/name", provenance)
    assert export_hf.same_release(a, b)


# --- push --------------------------------------------------------------------------------------

class FakeHub:
    """Just enough of HfApi to drive push(): one dataset repo, its commits, tags and manifests."""

    def __init__(self, private=False, exists=True):
        self.private, self.exists = private, exists
        self.commits: list[dict] = []          # manifest per commit, oldest first
        self.tags: dict[str, int] = {}         # tag -> commit index
        self.uploads = 0
        self.fail_create_tag = False
        self.writer_before_upload = False      # another writer commits after repo_info, before us
        self.writer_after_upload = False       # another writer commits right after our upload

    def _head(self):
        return f"c{len(self.commits) - 1}" if self.commits else None

    def _other_writer(self):
        self.commits.append({"source_commit": "someone-else"})

    def repo_info(self, repo_id, repo_type):
        if not self.exists:
            raise RuntimeError("404")
        return SimpleNamespace(private=self.private, sha=self._head())

    def list_repo_refs(self, repo_id, repo_type):
        return SimpleNamespace(tags=[SimpleNamespace(name=t) for t in self.tags])

    def hf_hub_download(self, repo_id, filename, repo_type, revision):
        idx = self.tags[revision] if revision in self.tags else int(revision[1:])
        path = self.tmp / f"manifest-{idx}.json"
        path.write_text(json.dumps(self.commits[idx]))
        return str(path)

    def upload_folder(self, repo_id, repo_type, folder_path, commit_message, delete_patterns,
                      parent_commit):
        self.uploads += 1
        if self.writer_before_upload:
            self._other_writer()
        # As the Hub does: a commit whose parent is no longer the head is rejected.
        if parent_commit != self._head():
            raise RuntimeError("412: parent commit is not the head")
        manifest = json.loads((export_hf.Path(folder_path) / "manifest.json").read_text())
        # As huggingface_hub does: an upload that changes nothing makes no commit and returns
        # the head as it stands.
        if not (self.commits and self.commits[-1] == manifest):
            self.commits.append(manifest)
        oid = self._head()
        if self.writer_after_upload:
            self._other_writer()
        return SimpleNamespace(oid=oid)

    def create_tag(self, repo_id, repo_type, tag, revision, tag_message):
        if self.fail_create_tag:
            raise RuntimeError("network")
        assert tag not in self.tags
        self.tags[tag] = int(revision[1:])


@pytest.fixture
def export_dir(built, tmp_path):
    _, payload, tables, head, provenance = built
    out = tmp_path / "out"
    export_hf.write(out, tables, payload, head, "v9.9.9", "org/name", provenance)
    return out


def _hub(tmp_path, **kw):
    hub = FakeHub(**kw)
    hub.tmp = tmp_path
    return hub


def test_first_push_uploads_then_tags_the_verified_revision(export_dir, tmp_path):
    hub = _hub(tmp_path)
    assert export_hf.push(export_dir, "org/name", "v9.9.9", private=False, api=hub) == "published"
    assert hub.uploads == 1 and hub.tags == {"v9.9.9": 0}


def test_a_retry_of_a_published_release_changes_nothing(export_dir, tmp_path):
    hub = _hub(tmp_path)
    export_hf.push(export_dir, "org/name", "v9.9.9", private=False, api=hub)
    assert export_hf.push(export_dir, "org/name", "v9.9.9", private=False, api=hub) == "unchanged"
    assert hub.uploads == 1


def test_a_retry_after_the_tag_step_failed_completes_the_release(export_dir, tmp_path):
    hub = _hub(tmp_path)
    hub.fail_create_tag = True
    with pytest.raises(RuntimeError):
        export_hf.push(export_dir, "org/name", "v9.9.9", private=False, api=hub)
    hub.fail_create_tag = False
    assert export_hf.push(export_dir, "org/name", "v9.9.9", private=False, api=hub) == "published"
    assert hub.tags["v9.9.9"] == len(hub.commits) - 1


def test_the_tag_points_at_the_uploaded_commit_even_when_the_branch_moves_on(export_dir,
                                                                             tmp_path):
    hub = _hub(tmp_path)
    hub.writer_after_upload = True
    assert export_hf.push(export_dir, "org/name", "v9.9.9", private=False, api=hub) == "published"
    ours = next(i for i, m in enumerate(hub.commits) if m.get("release_tag") == "v9.9.9")
    assert hub.tags["v9.9.9"] == ours
    assert len(hub.commits) - 1 != ours  # the head moved past the release, the tag did not


def test_an_upload_racing_another_writer_is_refused_and_nothing_is_tagged(export_dir, tmp_path):
    hub = _hub(tmp_path)
    hub.writer_before_upload = True
    with pytest.raises(RuntimeError, match="parent commit"):
        export_hf.push(export_dir, "org/name", "v9.9.9", private=False, api=hub)
    assert hub.tags == {}


def test_a_retry_whose_upload_changes_nothing_still_tags_the_release(export_dir, tmp_path):
    # The upload landed, the tag step failed, and the retry's upload is skipped as empty: the
    # library hands back the head, which here is still the release commit.
    hub = _hub(tmp_path)
    hub.fail_create_tag = True
    with pytest.raises(RuntimeError):
        export_hf.push(export_dir, "org/name", "v9.9.9", private=False, api=hub)
    hub.fail_create_tag = False
    export_hf.push(export_dir, "org/name", "v9.9.9", private=False, api=hub)
    assert len(hub.commits) == 1 and hub.tags == {"v9.9.9": 0}


@pytest.fixture
def rehearsal_dir(built, tmp_path):
    _, payload, tables, head, provenance = built
    tag = export_hf.rehearsal_tag(head, export_hf.datetime(2026, 1, 2, 3, 4, 5))
    out = tmp_path / "rehearsal"
    export_hf.write(out, tables, payload, head, tag, "org/test", provenance)
    return out, tag


def test_a_rehearsal_publishes_fresh_then_retries_as_a_no_op(rehearsal_dir, tmp_path):
    out, tag = rehearsal_dir
    hub = _hub(tmp_path, private=True)
    export_hf.rehearse(out, "org/test", tag, api=hub)
    assert hub.uploads == 1 and tag in hub.tags


def test_a_rehearsal_cannot_pass_on_an_earlier_runs_tag(rehearsal_dir, tmp_path):
    out, tag = rehearsal_dir
    hub = _hub(tmp_path, private=True)
    export_hf.rehearse(out, "org/test", tag, api=hub)
    with pytest.raises(SystemExit, match="fresh upload"):
        export_hf.rehearse(out, "org/test", tag, api=hub)
    assert hub.uploads == 1


def test_rehearsal_tags_do_not_repeat():
    t = export_hf.datetime(2026, 1, 2, 3, 4, 5)
    a = export_hf.rehearsal_tag("0123456789abcdef", t)
    b = export_hf.rehearsal_tag("0123456789abcdef", t.replace(second=6))
    assert a != b and a.startswith("rehearsal-01234567-")


def test_a_tag_holding_different_content_is_never_moved(export_dir, tmp_path):
    hub = _hub(tmp_path)
    other = json.loads((export_dir / "manifest.json").read_text())
    other = copy.deepcopy(other)
    other["files"]["data/products.parquet"]["content_sha256"] = "0" * 64
    hub.commits.append(other)
    hub.tags["v9.9.9"] = 0
    with pytest.raises(SystemExit, match="different content"):
        export_hf.push(export_dir, "org/name", "v9.9.9", private=False, api=hub)
    assert hub.uploads == 0 and hub.tags == {"v9.9.9": 0}


@pytest.mark.parametrize("kw, private, match", [
    ({"private": True}, False, "must be public"),
    ({"private": False}, True, "must be private"),
    ({"exists": False}, False, "not reachable"),
])
def test_push_checks_the_target_before_writing(export_dir, tmp_path, kw, private, match):
    hub = _hub(tmp_path, **kw)
    with pytest.raises(SystemExit, match=match):
        export_hf.push(export_dir, "org/name", "v9.9.9", private=private, api=hub)
    assert hub.uploads == 0


def test_push_refuses_an_export_built_for_another_tag(export_dir, tmp_path):
    with pytest.raises(SystemExit, match="was built for"):
        export_hf.push(export_dir, "org/name", "v1.0.0", private=False, api=_hub(tmp_path))


@pytest.mark.parametrize("argv, match", [
    (["--push"], "is not the v"),
    (["--push", "--repo-id", "someone/else"], "releases go to"),
    (["--rehearse"], "against the release dataset"),
    (["--rehearse", "--repo-id", "org/test", "--no-verify-history"], "not verified"),
])
def test_publishing_is_refused_before_anything_is_built(monkeypatch, tmp_path, argv, match):
    monkeypatch.setattr(export_hf, "release_tags", lambda: [])
    monkeypatch.setattr(export_hf, "push", lambda *a, **k: pytest.fail("push must not be reached"))
    monkeypatch.setattr(export_hf, "history_tables",
                        lambda *a, **k: pytest.fail("nothing should be built"))
    monkeypatch.setattr("sys.argv", ["export_hf", "--out", str(tmp_path), *argv])
    with pytest.raises(SystemExit, match=match):
        export_hf.main()


class _WhoamiHub(FakeHub):
    def __init__(self, me, **kw):
        super().__init__(exists=False, **kw)
        self.me = me

    def whoami(self):
        if self.me is None:
            raise RuntimeError("no token")
        return self.me


@pytest.mark.parametrize("me, expect", [
    (None, "none accepted"),
    ({"name": "someone", "orgs": [], "auth": {"accessToken": {"role": "write"}}},
     "NOT a member of org"),
    ({"name": "someone", "orgs": [{"name": "org"}],
      "auth": {"accessToken": {"role": "fineGrained", "fineGrained": {"scoped": [
          {"entity": {"type": "dataset", "name": "org/name"}, "permissions": ["repo.write"]},
          {"entity": {"type": "user", "name": "someone"}, "permissions": ["repo.content.read"]},
      ]}}}},
     "scoped to dataset org/name (repo.write) (+1 other grants)"),
])
def test_an_unreachable_target_explains_the_token_without_naming_anyone(export_dir, tmp_path,
                                                                        me, expect):
    hub = _WhoamiHub(me)
    hub.tmp = tmp_path
    with pytest.raises(SystemExit) as e:
        export_hf.push(export_dir, "org/name", "v9.9.9", private=False, api=hub)
    assert expect in str(e.value)
    assert "someone" not in str(e.value)
