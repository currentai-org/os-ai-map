"""The contradiction sweep: what it raises, and everything it deliberately does not.

The abstention rules carry this module. A sweep that fires on every difference between a record
and a signal is not a falsification check, it is a noise generator, and the first week of one
teaches everybody to stop reading the queue. So most of what follows pins a case where the two
sides differ and the sweep is required to stay quiet.
"""

from __future__ import annotations

import pytest

from build import check_contradictions as cc


def _row(**over):
    row = {
        "product_slug": "widget",
        "repo": "acme/widget",
        "license_spdx_id": "MIT",
        "license_is_noassertion": False,
        "is_archived": False,
        "http_status": 200,
        "pushed_at": "2026-01-02 03:04:05",
        "fetched_at": "2026-09-20 03:01:08",
    }
    row.update(over)
    return row


def _product(**over):
    product = {"type": "software"}
    product.update(over)
    return product


def _score():
    return {"openness": {"components": {}}}


def _licensed(*parts):
    """A score recording one license entry, as the structured list of parts the ladder reads."""
    return {"openness": {"components": {"license": list(parts)}}}


def _part(name, detail=None):
    part = {"name": name}
    if detail:
        part["detail"] = detail
    return part


def _sweep(rows, products, settled=(), scores=None):
    """`sweep` without its abstention tally, for the tests that only care about findings.

    `sweep` returns `(findings, abstained)` because the license leg refuses far more often than
    it fires and a run has to be able to show it looked. Most tests here predate that and read
    better without it.
    """
    findings, _ = cc.sweep(rows, products, scores or {}, settled)
    return findings


# ---------------------------------------------------------------------------
# retirement
# ---------------------------------------------------------------------------


def test_an_archived_repo_with_no_end_of_life_is_raised():
    found = cc.retirement_findings([_row(is_archived=True)], {"widget": _product()})
    assert len(found) == 1
    assert found[0].leg == cc.RETIREMENT
    assert found[0].product_slug == "widget"
    assert "archived" in found[0].observed


def test_an_archived_repo_whose_product_records_an_end_of_life_is_not_raised():
    """The finding is self-clearing: acting on it removes it. That is what keeps the queue
    honest without an acknowledgement ledger that could drift from the corpus.
    """
    products = {"widget": _product(end_of_life={"date": "2026-01-01"})}
    assert cc.retirement_findings([_row(is_archived=True)], products) == []


def test_a_live_repo_is_not_raised():
    assert cc.retirement_findings([_row(is_archived=False)], {"widget": _product()}) == []


def test_retirement_does_not_depend_on_product_type():
    """Unlike the license leg. `is_archived` is a fact about the same artifact whatever the
    product is, so a model whose repository was archived is as raisable as a tool.
    """
    found = cc.retirement_findings([_row(is_archived=True)], {"widget": _product(type="model")})
    assert len(found) == 1


def test_a_missing_archived_flag_is_not_a_finding():
    """`warehouse.query` converts through pandas and a null boolean arrives as `nan`, for which
    `bool(nan)` is True. Read naively, a product whose flag was never populated reports as
    archived. A missing observation is not a contradiction.
    """
    assert cc.retirement_findings([_row(is_archived=float("nan"))], {"widget": _product()}) == []
    assert cc.retirement_findings([_row(is_archived=None)], {"widget": _product()}) == []
    assert len(cc.retirement_findings([_row(is_archived=True)], {"widget": _product()})) == 1


# ---------------------------------------------------------------------------
# settlement
# ---------------------------------------------------------------------------


def test_a_settled_observation_stops_being_raised():
    settled = [{"leg": cc.RETIREMENT, "product_slug": "widget", "artifact": "acme/widget",
                "settles": "archived", "note": "the models outlived the repository"}]
    assert _sweep([_row(is_archived=True)], {"widget": _product()}, settled) == []


def test_a_settlement_with_no_reason_is_ignored():
    """A ruling with no reason is indistinguishable from a finding somebody wanted to stop
    seeing, and honouring it would make the ledger the place a real contradiction hides.
    """
    settled = [{"leg": cc.RETIREMENT, "product_slug": "widget", "artifact": "acme/widget",
                "settles": "archived", "note": "  "}]
    assert len(_sweep([_row(is_archived=True)], {"widget": _product()}, settled)) == 1


def test_a_settlement_does_not_cover_a_different_observation():
    """Bound to what was observed, so it expires when the world says something different --
    the difference between settling a question and silencing it. Here the ruling covers one
    repository; a second archived repository under the same product is a separate question.
    """
    settled = [{"leg": cc.RETIREMENT, "product_slug": "widget", "artifact": "acme/widget",
                "settles": "archived", "note": "the published models outlived the repository"}]
    assert _sweep([_row(is_archived=True)], {"widget": _product()}, settled) == []
    other = _row(is_archived=True, repo="acme/widget-tools")
    assert len(_sweep([other], {"widget": _product()}, settled)) == 1


# ---------------------------------------------------------------------------
# the CLI contract
# ---------------------------------------------------------------------------


def test_main_returns_zero_with_findings_because_it_raises_rather_than_blocks(capsys, tmp_path):
    """Default exit 0. A check that blocks the branch on a question nobody has answered yet
    stops being read and starts being worked around, and every finding here is a question.
    """
    rows = [_row(is_archived=True)]
    code = cc.main([], root=_corpus_root(tmp_path), rows=rows)
    assert code == 0
    assert "retirement" in capsys.readouterr().out


def test_strict_exits_one_so_the_same_sweep_can_gate_once_a_queue_is_empty(tmp_path):
    rows = [_row(is_archived=True)]
    assert cc.main(["--strict"], root=_corpus_root(tmp_path), rows=rows) == 1
    assert cc.main(["--strict"], root=_corpus_root(tmp_path), rows=[_row()]) == 0


def test_the_queue_names_what_to_do_about_each_leg(tmp_path):
    out = tmp_path / "queue.md"
    cc.main(["--queue", str(out)], root=_corpus_root(tmp_path), rows=[_row(is_archived=True)])
    text = out.read_text()
    assert "end_of_life" in text
    assert "`widget`" in text


def test_an_empty_queue_says_so_rather_than_writing_a_bare_heading(tmp_path):
    out = tmp_path / "queue.md"
    cc.main(["--queue", str(out)], root=_corpus_root(tmp_path), rows=[_row()])
    text = out.read_text()
    assert "No contradiction within this sweep's coverage" in text
    # It must not read as "everything was checked": the sweep covers two signals, not the corpus.
    assert "not a statement that every record was checked" in text


def _corpus_root(tmp_path):
    import yaml

    (tmp_path / "sources" / "products").mkdir(parents=True, exist_ok=True)
    (tmp_path / "sources" / "scores").mkdir(parents=True, exist_ok=True)
    (tmp_path / "sources" / "products" / "widget.yaml").write_text(yaml.safe_dump(_product()))
    (tmp_path / "sources" / "scores" / "widget.yaml").write_text(yaml.safe_dump(_score()))
    return tmp_path


# ---------------------------------------------------------------------------
# the license leg
#
# The observation is one thing: the license GitHub classifies at a repository root. That is a
# statement about CODE, and almost every abstention below is the same sentence in a different
# costume -- the recorded license is about something else, or it is qualified in a way the
# observation cannot speak to.
#
# Every case here is drawn from a real record. The earlier attempts at this leg were withdrawn
# twice because each one reported a record that was already right and already explained in its
# own file, so the bar is not "does it find things" but "does it stay quiet where it should".
# ---------------------------------------------------------------------------


def test_a_relicensed_repository_is_raised():
    """The finding this leg exists for: a software product whose repository now classifies as
    something other than what the score records."""
    findings = _sweep(
        [_row(license_spdx_id="AGPL-3.0")],
        {"widget": _product()},
        scores={"widget": _licensed(_part("MIT", "OSI"))},
    )
    assert len(findings) == 1
    assert findings[0].leg == cc.LICENSE
    assert "MIT" in findings[0].recorded
    assert "AGPL-3.0" in findings[0].observed
    assert findings[0].settles == "AGPL-3.0"


def test_an_agreeing_license_is_not_raised():
    assert _sweep([_row(license_spdx_id="MIT")], {"widget": _product()},
                  scores={"widget": _licensed(_part("MIT", "OSI"))}) == []


def test_the_comparison_folds_case():
    """`normalize_license` returns its input unchanged when no alias matches, so a recorded
    `mit` and an observed `MIT` come back different from it. The leg folds case at the point of
    comparison rather than changing that function, which also feeds tier matching."""
    assert cc.normalize_license("mit") != cc.normalize_license("MIT")
    assert _sweep([_row(license_spdx_id="MIT")], {"widget": _product()},
                  scores={"widget": _licensed(_part("mit"))}) == []


def test_a_models_own_license_is_not_contradicted_by_its_repository():
    """The false positive that sank the earlier attempts, and the most common one in the corpus.

    A model product records the license of its WEIGHTS. The repository beside it holds training
    or inference code under a license of its own, and the two disagreeing is the normal case
    rather than a contradiction. Drawn from `prithvi-eo` and `zephyr`.
    """
    assert _sweep([_row(license_spdx_id="Apache-2.0")], {"widget": _product(type="model")},
                  scores={"widget": _licensed(_part("MIT", "OSI"))}) == []


def test_a_datasets_own_license_is_not_contradicted_by_its_repository():
    """`dolma` records ODC-BY for the data; `allenai/dolma` is Apache-2.0 because that is the
    code that built it."""
    assert _sweep([_row(license_spdx_id="Apache-2.0")], {"widget": _product(type="dataset")},
                  scores={"widget": _licensed(_part("ODC-BY"))}) == []


def test_an_explicitly_code_scoped_part_is_compared_whatever_the_product_is():
    """Scope decides, not product type. `redpajama-data-v2` and `internlm` each carry exactly one
    explicitly code-scoped part, and that part IS comparable to a repository license even though
    the product is a dataset and a model."""
    findings = _sweep(
        [_row(license_spdx_id="AGPL-3.0")],
        {"widget": _product(type="dataset")},
        scores={"widget": _licensed(_part("CommonCrawl-ToU"), _part("Apache-2.0", "code, OSI"))},
    )
    assert len(findings) == 1
    assert "Apache-2.0" in findings[0].recorded


def test_a_compound_with_no_code_scoped_part_abstains():
    assert _sweep(
        [_row(license_spdx_id="MIT")],
        {"widget": _product(type="model")},
        scores={"widget": _licensed(_part("Llama-3-Community"), _part("Apache-2.0", "weights"))},
    ) == []


def test_a_qualification_after_the_grade_abstains():
    """`braintrust` records `Apache-2.0`, detail `OSI, client SDKs only, Python/TS/Go/Ruby/C#`.
    The grade is comparable; what follows it is a carve-out the observation cannot see."""
    assert _sweep([_row(license_spdx_id="MIT")], {"widget": _product()},
                  scores={"widget": _licensed(_part("Apache-2.0", "OSI, client SDKs only"))}) == []


def test_a_named_license_file_abstains():
    """`autogen` records `MIT`, detail `code,via LICENSE-CODE`, and GitHub classifies the docs
    license at the repository root. The record says which file it read; a classifier reading a
    different one does not contradict it."""
    assert _sweep([_row(license_spdx_id="CC-BY-4.0")], {"widget": _product()},
                  scores={"widget": _licensed(_part("MIT", "code,via LICENSE-CODE"))}) == []


def test_a_qualification_inside_the_name_abstains():
    """`cuda-tile` records `Apache-2.0-WITH-LLVM-exception` with a detail of merely `OSI`, so
    nothing in the detail gives the qualification away."""
    assert _sweep([_row(license_spdx_id="Apache-2.0")], {"widget": _product()},
                  scores={"widget": _licensed(_part("Apache-2.0-WITH-LLVM-exception", "OSI"))}) == []


def test_a_semicolon_does_not_split_a_qualification_into_allowed_tokens():
    """Only a comma separates detail tokens. `OSI; covers the code` is one clause a person wrote,
    and splitting on the semicolon would produce two tokens that both look allowed."""
    assert _sweep([_row(license_spdx_id="MIT")], {"widget": _product()},
                  scores={"widget": _licensed(_part("Apache-2.0", "OSI; covers the code"))}) == []


def test_noassertion_is_an_absence_rather_than_a_contradiction():
    """GitHub returns NOASSERTION for a repository whose LICENSE it cannot classify. `pytorch`
    reads this way and its recorded BSD-3-Clause is correct."""
    for spdx in ("NOASSERTION", "", None, "other"):
        assert _sweep([_row(license_spdx_id=spdx)], {"widget": _product()},
                      scores={"widget": _licensed(_part("BSD-3-Clause", "OSI"))}) == []


def test_more_than_one_repository_row_abstains():
    """Nothing here says which repository the recorded license was read off, so binding the
    observation to the record is impossible."""
    rows = [_row(license_spdx_id="AGPL-3.0"), _row(license_spdx_id="AGPL-3.0", repo="acme/widget-cli")]
    assert _sweep(rows, {"widget": _product()},
                  scores={"widget": _licensed(_part("MIT", "OSI"))}) == []


def test_more_than_one_recorded_license_key_abstains():
    scores = {"widget": {"openness": {"components": {
        "license": [_part("MIT", "OSI")],
        "model-license": [_part("Llama-3-Community")],
    }}}}
    assert _sweep([_row(license_spdx_id="AGPL-3.0")], {"widget": _product()}, scores=scores) == []


def test_hardware_abstains_because_the_repository_is_not_the_product():
    """The repository under a hardware product is a driver or an SDK. `google-coral-dev-board`
    points at `google-coral/libedgetpu`."""
    assert _sweep([_row(license_spdx_id="Apache-2.0")], {"widget": _product(type="hardware")},
                  scores={"widget": _licensed(_part("MIT"))}) == []


def test_a_settled_license_observation_stops_being_raised_until_the_license_moves():
    settled = [{"leg": cc.LICENSE, "product_slug": "widget", "artifact": "acme/widget",
                "settles": "AGPL-3.0", "note": "the SDK was relicensed, the core was not"}]
    scores = {"widget": _licensed(_part("MIT", "OSI"))}
    assert _sweep([_row(license_spdx_id="AGPL-3.0")], {"widget": _product()}, settled, scores) == []
    # a DIFFERENT observed license is a different question, and comes back
    assert len(_sweep([_row(license_spdx_id="GPL-3.0")], {"widget": _product()}, settled, scores)) == 1


def test_the_abstention_tally_is_returned_so_a_quiet_run_can_show_it_looked():
    """A leg this conservative reports nothing most weeks. Without the tally, that is
    indistinguishable from a comparison that silently stopped working."""
    _, abstained = cc.sweep(
        [_row(license_spdx_id="Apache-2.0")],
        {"widget": _product(type="model")},
        {"widget": _licensed(_part("MIT", "OSI"))},
    )
    assert sum(abstained.values()) == 1
    assert any("not about the repository" in reason for reason in abstained)


def test_a_code_prefixed_name_is_compared_rather_than_rejected_for_its_prefix():
    """`part_scope` reads a `code ` prefix on the name as the scope marker, so the bare-id test
    after it has to strip the same prefix. Otherwise the leg refuses a record for saying exactly
    what the leg asked it to say, and the refusal lands on the records that state their scope
    most explicitly. Nothing in the corpus is spelled this way today; `part_scope` accepts it, so
    the rest of the leg has to.
    """
    findings = _sweep(
        [_row(license_spdx_id="MIT")],
        {"widget": _product(type="model")},
        scores={"widget": _licensed(_part("code Apache-2.0", "OSI"))},
    )
    assert len(findings) == 1
    assert "Apache-2.0" in findings[0].recorded


def test_only_the_scope_prefix_is_stripped_not_the_whole_alias_table():
    """`normalize_license` also resolves aliases, and an alias can turn a prose name into a
    bare-looking one -- `custom weights license` becomes `InternLM-Free-Commercial-License`.
    Running it before the bare-id test would let a comparison start on a record that never
    carried a license id at all.
    """
    assert _sweep(
        [_row(license_spdx_id="MIT")],
        {"widget": _product()},
        scores={"widget": _licensed(_part("custom weights license", "code"))},
    ) == []


def test_a_settlement_covers_the_same_license_spelled_differently():
    """The comparison folds case, so the settlement binding has to as well. Otherwise a change
    in how GitHub spells an spdx id reopens a question a person already answered, while the
    comparison that raised it treats the two spellings as identical."""
    settled = [{"leg": cc.LICENSE, "product_slug": "widget", "artifact": "acme/widget",
                "settles": "AGPL-3.0", "note": "the SDK was relicensed, the core was not"}]
    scores = {"widget": _licensed(_part("MIT", "OSI"))}
    assert _sweep([_row(license_spdx_id="agpl-3.0")], {"widget": _product()}, settled, scores) == []


def test_rows_with_no_product_slug_are_counted_individually():
    """They all group under the empty key, so without their own branch N malformed rows report
    as one product with more than one repository row."""
    rows = [_row(product_slug=None), _row(product_slug=""), _row(product_slug="   ")]
    findings, abstained = cc.sweep(rows, {}, {})
    assert findings == []
    assert abstained["the row carries no product slug"] == 3


def test_a_representation_gap_is_reported_rather_than_silently_suppressed():
    """The distinction the ledger turns on. Most settlements say the record was right; a few say
    the finding is real and no field can record the answer. Filed as an ordinary settlement, the
    second kind leaves the queue looking exactly like a vindicated record.
    """
    settled = [
        {"leg": cc.RETIREMENT, "product_slug": "widget", "artifact": "acme/widget",
         "settles": "archived", "note": "the product outlived the repository"},
        {"leg": cc.RETIREMENT, "product_slug": "gadget", "artifact": "acme/gadget",
         "settles": "archived", "class": "representation-gap",
         "note": "it ended, and the announcement gives a year where the field wants a day"},
    ]
    gaps = cc.representation_gaps(settled)
    assert [g["product_slug"] for g in gaps] == ["gadget"]


def test_a_representation_gap_still_suppresses_its_finding():
    """Reported is not the same as raised. It stays out of the queue; it does not stay out of
    sight."""
    settled = [{"leg": cc.RETIREMENT, "product_slug": "widget", "artifact": "acme/widget",
                "settles": "archived", "class": "representation-gap",
                "note": "the schema cannot record the answer"}]
    assert _sweep([_row(is_archived=True)], {"widget": _product()}, settled) == []
