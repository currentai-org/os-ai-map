import subprocess
from pathlib import Path

import yaml

from build import check_corpus_diff as ccd

ROOT = Path(__file__).resolve().parents[1]


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def _clone(dest: Path) -> Path:
    """A local clone of the repo the tests run in, so a synthetic commit is isolated from it."""
    subprocess.run(["git", "clone", "--local", "--no-hardlinks", "--quiet", str(ROOT), str(dest)],
                   check=True, capture_output=True, text=True)
    _git(dest, "config", "user.email", "ccd-test@example.invalid")
    _git(dest, "config", "user.name", "ccd test")
    return dest


def _pick_editable_non_leading(repo: Path) -> tuple[str, str]:
    """A (category, slug) whose score file carries an integer adoption.level and whose tier is
    not already 'leading', so forcing the axes to 5 lands it in the leading tier for sure."""
    payload = ccd._payload_at(repo)
    for cid, cat in payload["categories"].items():
        for prod in cat.get("products", []):
            if prod.get("tier") == "leading":
                continue
            slug = prod["slug"]
            doc = yaml.safe_load((repo / "sources" / "scores" / f"{slug}.yaml").read_text())
            if isinstance((doc.get("adoption") or {}).get("level"), int):
                return cid, slug
    raise AssertionError("no editable non-leading product found in the corpus")


def test_reports_a_tier_move_from_source_with_notebook_data_untouched(tmp_path):
    """The #497 regression guard. A source change that alters a product's tier, with
    build/notebook_data.json deliberately left untouched (as the contributor checklist
    requires), must be reported. The old gate compared the committed payload against itself
    and printed an empty sheet here; reserializing from source makes the delta real."""
    repo = _clone(tmp_path / "repo")
    base = _git(repo, "rev-parse", "HEAD").strip()

    _cid, slug = _pick_editable_non_leading(repo)
    score = repo / "sources" / "scores" / f"{slug}.yaml"
    doc = yaml.safe_load(score.read_text())
    doc["adoption"]["level"] = 5
    doc.setdefault("capability", {})["score"] = 5
    score.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True))
    _git(repo, "add", f"sources/scores/{slug}.yaml")
    _git(repo, "commit", "-m", "synthetic: force a leading tier")

    changed = _git(repo, "diff", "--name-only", f"{base}...HEAD").split()
    assert changed == [f"sources/scores/{slug}.yaml"]  # notebook_data.json really is untouched

    sheet_path = tmp_path / "sheet.md"
    rc = ccd.main(["--base", base, "--sheet", str(sheet_path)], root=repo)
    sheet = sheet_path.read_text()
    assert f"{slug}:" in sheet and "-> leading" in sheet, sheet
    assert rc == 0  # a tier move alone is reported but does not fail the gate


def test_no_source_change_reports_nothing(tmp_path):
    """The symmetric half: serializing both sides from source must not manufacture a delta.
    A commit that touches no source file leaves the sheet empty and the gate green."""
    repo = _clone(tmp_path / "repo")
    base = _git(repo, "rev-parse", "HEAD").strip()

    (repo / "docs" / "_ccd_probe.md").write_text("not a source file\n")
    _git(repo, "add", "docs/_ccd_probe.md")
    _git(repo, "commit", "-m", "docs-only change")

    sheet_path = tmp_path / "sheet.md"
    rc = ccd.main(["--base", base, "--sheet", str(sheet_path)], root=repo)
    sheet = sheet_path.read_text()
    assert "stage moves: none" in sheet
    assert "untouched-product row changes: none" in sheet
    assert rc == 0


def _payload(categories):
    return {"categories": categories}


def _cat(stage, gaps, products):
    return {"stage": {"num": stage, "name": "x"}, "gaps": gaps,
            "products": [{"slug": s, "tier": t} for s, t in products]}


def test_added_product_without_stage_move_is_clean():
    before = _payload({"c": _cat(2, ["adoption"], [("a", None)])})
    after = _payload({"c": _cat(2, ["adoption"], [("a", None), ("b", None)])})
    diff = ccd.diff_payloads(before, after)
    assert diff.categories["c"].products_added == ["b"]
    assert diff.stage_moves == []


def test_stage_move_is_reported_by_category():
    before = _payload({"c": _cat(2, ["adoption"], [("a", None)])})
    after = _payload({"c": _cat(3, [], [("a", None), ("b", "strong")])})
    diff = ccd.diff_payloads(before, after)
    assert diff.stage_moves == ["c: 2 -> 3, gaps ['adoption'] -> []"]
    assert diff.categories["c"].tier_changes == []


def test_tier_change_on_existing_product_is_reported():
    before = _payload({"c": _cat(2, [], [("a", None)])})
    after = _payload({"c": _cat(2, [], [("a", "leading")])})
    diff = ccd.diff_payloads(before, after)
    assert diff.categories["c"].tier_changes == [("a", None, "leading")]


def test_touched_products_reads_score_and_product_paths():
    names = ["sources/scores/aider.yaml", "sources/products/llama.yaml", "docs/x.md",
             "sources/categories/ui_api.yaml"]
    assert ccd.products_from_paths(names) == {"aider", "llama"}


def test_a_changed_hold_touches_only_its_own_axis():
    before = "held:\n  a:\n    adoption:\n      because: x\n      since: '2026-09-29'\n    capability:\n      because: q\n      since: '2026-09-29'\n  b:\n    openness:\n      because: y\n      since: '2026-09-29'\n"
    after = "held:\n  a:\n    adoption:\n      because: z\n      since: '2026-10-07'\n    capability:\n      because: q\n      since: '2026-09-29'\n  b:\n    openness:\n      because: y\n      since: '2026-09-29'\n  c:\n    adoption:\n      because: w\n      since: '2026-10-07'\n"
    assert ccd.held_axes_changed(before, after) == {"a|adoption", "c|adoption"}


def test_a_released_hold_touches_its_axis():
    before = "held:\n  a:\n    adoption:\n      because: x\n      since: '2026-09-29'\n"
    assert ccd.held_axes_changed(before, "held: {}\n") == {"a|adoption"}


def test_a_whole_product_hold_touches_every_axis():
    before = "held:\n  a:\n    because: x\n    since: '2026-09-29'\n"
    after = "held:\n  a:\n    because: y\n    since: '2026-09-29'\n"
    assert ccd.held_axes_changed(before, after) == {"a|*"}
    rows_before = {"a|adoption": "1", "a|openness": "1"}
    rows_after = {"a|adoption": "2", "a|openness": "2"}
    assert ccd.compare_rows(rows_before, rows_after, touched=set(), touched_axes={"a|*"}) == []


def test_a_hold_edit_does_not_exempt_the_products_other_axes():
    before = {"p|adoption": "1", "p|openness": "1", "q|adoption": "1"}
    after = {"p|adoption": "2", "p|openness": "2", "q|adoption": "1"}
    changes = ccd.compare_rows(before, after, touched=set(), touched_axes={"p|adoption"})
    assert changes == ["p|openness changed but sources/{scores,products}/p.yaml did not"]
    assert ccd.compare_rows(before, after, touched={"p"}, touched_axes=set()) == []


def test_untouched_row_change_fails_the_gate():
    before_rows = {"p1|openness": "row-v1", "p2|openness": "row-v1"}
    after_rows = {"p1|openness": "row-v2", "p2|openness": "row-v1"}
    changes = ccd.compare_rows(before_rows, after_rows, touched={"p2"})
    assert changes == ["p1|openness changed but sources/{scores,products}/p1.yaml did not"]


def test_untouched_row_appearance_fails_the_gate():
    before_rows = {"p1|openness": "row-v1"}
    after_rows = {"p1|openness": "row-v1", "p1|capability": "row-v1"}
    changes = ccd.compare_rows(before_rows, after_rows, touched={"p2"})
    assert changes == ["p1|capability appeared but sources/{scores,products}/p1.yaml did not change"]


def test_untouched_row_disappearance_fails_the_gate():
    before_rows = {"p1|openness": "row-v1", "p1|capability": "row-v1"}
    after_rows = {"p1|openness": "row-v1"}
    changes = ccd.compare_rows(before_rows, after_rows, touched={"p2"})
    assert changes == ["p1|capability disappeared but sources/{scores,products}/p1.yaml did not change"]


def test_content_row_ignores_declaration_identity():
    """PR #461: two rows identical except declaration_version_id/source_git_sha - which
    differ between the base ref and HEAD by construction, since they are commit-scoped -
    must compare equal via content_row, or every axis row on every PR reads as changed."""
    base_row = {
        "declaration_version_id": "dv-base", "source_git_sha": "sha-base",
        "product_slug": "whylabs", "category_slug": "telemetry_observability",
        "product_type": "software", "axis": "openness", "status": "confirmed",
        "recorded_value": 3, "recorded_class": "open_weights", "basis": "osi",
        "basis_detail": None, "instrument_type": None, "confidence": "high",
        "last_verified": "2026-08-01", "hold_reason": None, "held_since": None,
        "decision_note": None, "source_count": 2,
    }
    head_row = {**base_row, "declaration_version_id": "dv-head", "source_git_sha": "sha-head"}
    assert base_row != head_row  # the fixtures really do differ, or this test proves nothing
    assert ccd.content_row(base_row) == ccd.content_row(head_row)


def test_content_row_still_catches_a_real_content_change():
    base_row = {"declaration_version_id": "dv-base", "source_git_sha": "sha-base",
                "product_slug": "whylabs", "axis": "openness", "recorded_value": 3}
    head_row = {**base_row, "declaration_version_id": "dv-head", "source_git_sha": "sha-head",
                "recorded_value": 5}
    assert ccd.content_row(base_row) != ccd.content_row(head_row)


def test_compare_rows_via_content_row_projection_ignores_identity_only_differences():
    base_row = {"declaration_version_id": "dv-base", "source_git_sha": "sha-base",
                "product_slug": "whylabs", "axis": "openness", "recorded_value": 3}
    head_row = {**base_row, "declaration_version_id": "dv-head", "source_git_sha": "sha-head"}
    before = {"whylabs|openness": ccd.content_row(base_row)}
    after = {"whylabs|openness": ccd.content_row(head_row)}
    assert ccd.compare_rows(before, after, touched=set()) == []


def test_sheet_mentions_every_category_delta():
    before = _payload({"c": _cat(2, ["adoption"], [("a", None)])})
    after = _payload({"c": _cat(2, ["adoption"], [("a", None), ("b", None)])})
    sheet = ccd.render_sheet(ccd.diff_payloads(before, after), row_changes=[])
    assert "| c |" in sheet and "+1" in sheet and "stage moves: none" in sheet


# --- a category rename is not a silent rewrite ------------------------------------------
#
# Added 2026-09-17 with agent_tools_protocols -> agent_tools_connectors. The rename moves
# `category_slug` on every row of that category while touching none of those products' files,
# which is this gate's definition of a silent rewrite and is not one: the products did not
# change, their category's name did. The exemption is scoped to the renamed slugs and to that
# one column, so everything else about those products is still compared exactly.

def _row(**kw):
    import json
    base = {"product_slug": "p1", "axis": "openness", "category_slug": "old_name", "score": 4}
    base.update(kw)
    return json.dumps(base, separators=(",", ":"), sort_keys=True)


def test_a_renamed_category_alone_is_not_flagged():
    import build.check_corpus_diff as ccd

    before = {"p1|openness": _row(category_slug="old_name")}
    after = {"p1|openness": _row(category_slug="new_name")}
    assert ccd.compare_rows(before, after, touched=set(),
                            renamed={"old_name", "new_name"}) == []


def test_a_real_change_inside_a_renamed_category_is_still_flagged():
    """The exemption covers one column, not the product."""
    import build.check_corpus_diff as ccd

    before = {"p1|openness": _row(category_slug="old_name", score=4)}
    after = {"p1|openness": _row(category_slug="new_name", score=5)}
    changes = ccd.compare_rows(before, after, touched=set(), renamed={"old_name", "new_name"})
    assert changes and "p1|openness changed" in changes[0]


def test_a_category_move_without_a_rename_is_still_flagged():
    """A product moving between two categories that both still exist is the case to catch."""
    import build.check_corpus_diff as ccd

    before = {"p1|openness": _row(category_slug="cat_a")}
    after = {"p1|openness": _row(category_slug="cat_b")}
    assert ccd.compare_rows(before, after, touched=set(), renamed=set())
    assert ccd.compare_rows(before, after, touched=set(), renamed={"other", "unrelated"})


# --- publishing a preliminary category is not a silent rewrite ---------------------------
#
# Added 2026-10-08 with data_hubs, the first category whose products were researched in an
# earlier PR while it was preliminary. Publishing it makes every one of their rows appear while
# touching none of their files. The exemption holds only when all of these are true: the
# category's taxonomy status moved from preliminary to published, the row appears (it did not
# change or disappear), and the product was on the category's roster at the base. Stage, gap and
# tier reporting is untouched by it.

def test_rows_appearing_in_a_published_category_are_not_flagged():
    after = {"p1|openness": _row(category_slug="hubs"),
             "p1|adoption": _row(axis="adoption", category_slug="hubs")}
    assert ccd.compare_rows({}, after, touched=set(), published={"hubs": {"p1"}},
                            as_published=dict(after)) == []


def test_an_appearing_row_that_differs_from_the_base_record_is_still_flagged():
    """The publish exempts the category's visibility, not a change to the product's record: an
    appearing row must equal what the base yields for it once the category is published."""
    after = {"p1|openness": _row(category_slug="hubs", score=5)}
    as_published = {"p1|openness": _row(category_slug="hubs", score=4)}
    changes = ccd.compare_rows({}, after, touched=set(), published={"hubs": {"p1"}},
                               as_published=as_published)
    assert changes == ["p1|openness appeared with the publication of hubs but differs from its "
                       "record at the base, and sources/{scores,products}/p1.yaml did not change"]
    # A product whose files the PR touched may change freely, as everywhere else in the gate.
    assert ccd.compare_rows({}, after, touched={"p1"}, published={"hubs": {"p1"}},
                            as_published=as_published) == []


def test_a_published_to_published_appearance_is_still_flagged():
    """`published` only ever names categories that were preliminary at the base, so a row
    appearing in a category that was already published gets no exemption."""
    after = {"p1|openness": _row(category_slug="other")}
    changes = ccd.compare_rows({}, after, touched=set(), published={"hubs": {"p1"}},
                               as_published=dict(after))
    assert changes == ["p1|openness appeared but sources/{scores,products}/p1.yaml did not change"]


def test_a_changed_row_in_a_newly_published_category_is_still_flagged():
    before = {"p1|openness": _row(category_slug="hubs", score=4)}
    after = {"p1|openness": _row(category_slug="hubs", score=5)}
    changes = ccd.compare_rows(before, after, touched=set(), published={"hubs": {"p1"}},
                               as_published=dict(after))
    assert changes == ["p1|openness changed but sources/{scores,products}/p1.yaml did not"]


def test_a_vanished_row_in_a_newly_published_category_is_still_flagged():
    before = {"p1|openness": _row(category_slug="hubs")}
    changes = ccd.compare_rows(before, {}, touched=set(), published={"hubs": {"p1"}},
                               as_published=dict(before))
    assert changes == ["p1|openness disappeared but sources/{scores,products}/p1.yaml did not change"]


def test_a_product_not_on_the_base_roster_is_still_flagged():
    after = {"p1|openness": _row(category_slug="hubs"),
             "p2|openness": _row(product_slug="p2", category_slug="hubs")}
    changes = ccd.compare_rows({}, after, touched=set(), published={"hubs": {"p1"}},
                               as_published=dict(after))
    assert changes == ["p2|openness appeared but sources/{scores,products}/p2.yaml did not change"]


def _taxonomy_repo(repo, base_statuses, head_statuses, base_rosters, head_rosters):
    """A throwaway repo with a `base` tag and a HEAD commit, each carrying a taxonomy and
    category files, for exercising `published_categories` against real git refs. A status of
    None writes the scalar spelling, which reads as published."""
    def write(statuses, rosters):
        (repo / "sources" / "categories").mkdir(parents=True, exist_ok=True)
        entries = "".join(f"    - {cid}\n" if status is None
                          else f"    - name: {cid}\n      status: {status}\n"
                          for cid, status in statuses.items())
        (repo / "sources" / "taxonomy.yaml").write_text(
            "arcs:\n- name: A\n  layer: infrastructure\n  groups:\n  - name: G\n    slug: g\n"
            "    categories:\n" + entries)
        for cid, roster in rosters.items():
            (repo / "sources" / "categories" / f"{cid}.yaml").write_text(
                yaml.safe_dump({"name": cid, "products": roster}))

    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "ccd-test@example.invalid")
    _git(repo, "config", "user.name", "ccd test")
    write(base_statuses, base_rosters)
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "base")
    _git(repo, "tag", "base")
    write(head_statuses, head_rosters)
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "head")
    return repo


def test_published_categories_reads_the_status_move_and_base_roster_from_git(tmp_path):
    repo = _taxonomy_repo(
        tmp_path / "repo",
        base_statuses={"stays": None, "hubs": "preliminary", "later": "preliminary"},
        head_statuses={"stays": None, "hubs": "published", "later": "preliminary",
                       "fresh": "published"},
        base_rosters={"stays": ["s1"], "hubs": ["p1", "p2"], "later": ["l1"]},
        head_rosters={"stays": ["s1"], "hubs": ["p1", "p2", "p3"], "later": ["l1"],
                      "fresh": ["f1"]},
    )
    # `stays` was published at both refs, `later` is still preliminary, and `fresh` did not
    # exist at the base, so only `hubs` qualifies; p3 joined its roster in the PR and is left out.
    assert ccd.published_categories(repo, "base") == {"hubs": {"p1", "p2"}}


def test_published_categories_ignores_a_published_to_published_category(tmp_path):
    repo = _taxonomy_repo(
        tmp_path / "repo",
        base_statuses={"hubs": "published"}, head_statuses={"hubs": None},
        base_rosters={"hubs": ["p1"]}, head_rosters={"hubs": ["p1", "p2"]},
    )
    assert ccd.published_categories(repo, "base") == {}


def test_a_publish_leaves_stage_gap_and_tier_checks_in_force(tmp_path, monkeypatch):
    """The exemption reaches only the untouched-row comparison. A stage move that comes with the
    publish still needs the label, and a tier change is still on the sheet."""
    before_payload = _payload({"hubs": _cat(1, ["adoption"], [("p1", None)])})
    after_payload = _payload({"hubs": _cat(2, [], [("p1", "strong")])})
    after_rows = {"p1|openness": _row(category_slug="hubs")}
    monkeypatch.setattr(ccd, "_snapshot_at", lambda root, ref: (
        (before_payload, {}) if ref is not None else (after_payload, after_rows)))
    monkeypatch.setattr(ccd, "touched_products", lambda root, base: set())
    monkeypatch.setattr(ccd, "touched_axes", lambda root, base: set())
    monkeypatch.setattr(ccd, "renamed_categories", lambda root, base: set())
    monkeypatch.setattr(ccd, "published_categories", lambda root, base: {"hubs": {"p1"}})
    monkeypatch.setattr(ccd, "as_published_rows", lambda root, base, cids: dict(after_rows))

    sheet_path = tmp_path / "sheet.md"
    assert ccd.main(["--base", "base", "--sheet", str(sheet_path)], root=tmp_path) == 1
    sheet = sheet_path.read_text()
    assert "| hubs | 1 -> 2 | ['adoption'] -> [] |" in sheet and "p1: None -> strong" in sheet
    assert "untouched-product row changes: none" in sheet
    assert ccd.main(["--base", "base", "--allow-stage-move", "--sheet", str(sheet_path)],
                    root=tmp_path) == 0


def _preliminary_with_scored_roster(repo):
    """A preliminary category whose roster products all carry score files, or None."""
    from build.taxonomy import category_statuses

    statuses = category_statuses(yaml.safe_load((repo / "sources" / "taxonomy.yaml").read_text()))
    for cid, status in statuses.items():
        if status != "preliminary":
            continue
        path = repo / "sources" / "categories" / f"{cid}.yaml"
        roster = (yaml.safe_load(path.read_text()) or {}).get("products") or [] if path.exists() else []
        if roster and all((repo / "sources" / "scores" / f"{s}.yaml").exists() for s in roster):
            return cid, roster
    return None


def test_publishing_a_researched_category_passes_and_an_edit_inside_it_does_not(tmp_path):
    """End to end on the real corpus: flipping one preliminary category to published, and
    touching nothing else, makes its products' rows appear and the gate pass. An uncommitted
    edit to one of those products' scores, read from the working tree, still fails it."""
    import pytest

    repo = _clone(tmp_path / "repo")
    found = _preliminary_with_scored_roster(repo)
    if found is None:
        pytest.skip("no preliminary category with a researched roster in the corpus")
    cid, roster = found
    base = _git(repo, "rev-parse", "HEAD").strip()

    tax = repo / "sources" / "taxonomy.yaml"
    text = tax.read_text()
    flipped = text.replace(f"- name: {cid}\n      status: preliminary",
                           f"- name: {cid}\n      status: published")
    assert flipped != text
    tax.write_text(flipped)
    _git(repo, "commit", "-qam", f"synthetic: publish {cid}")

    sheet_path = tmp_path / "sheet.md"
    assert ccd.main(["--base", base, "--allow-stage-move", "--sheet", str(sheet_path)],
                    root=repo) == 0, sheet_path.read_text()
    assert "untouched-product row changes: none" in sheet_path.read_text()

    slug = roster[0]
    score = repo / "sources" / "scores" / f"{slug}.yaml"
    doc = yaml.safe_load(score.read_text())
    axis = next(a for a in ("capability", "openness") if isinstance((doc.get(a) or {}).get("score"), int))
    doc[axis]["score"] = 1 if doc[axis]["score"] != 1 else 2
    score.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True))
    assert ccd.main(["--base", base, "--allow-stage-move", "--sheet", str(sheet_path)],
                    root=repo) == 1
    assert f"{slug}|{axis} appeared with the publication of {cid}" in sheet_path.read_text()
