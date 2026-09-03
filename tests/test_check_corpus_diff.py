from build import check_corpus_diff as ccd


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
