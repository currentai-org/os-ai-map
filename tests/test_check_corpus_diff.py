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
