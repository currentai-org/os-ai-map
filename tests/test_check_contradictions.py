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


def _score(license_name="MIT"):
    return {"openness": {"components": {"license": [{"name": license_name, "detail": "OSI"}]}}}


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


# ---------------------------------------------------------------------------
# license: what it raises
# ---------------------------------------------------------------------------


def test_a_software_repo_whose_spdx_differs_is_raised():
    found = cc.license_findings(
        [_row(license_spdx_id="CC-BY-4.0")], {"widget": _product()}, {"widget": _score("MIT")}
    )
    assert len(found) == 1
    assert (found[0].recorded, found[0].observed) == ("MIT", "CC-BY-4.0")


# ---------------------------------------------------------------------------
# license: what it abstains on
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("product_type", ["model", "dataset", "hardware"])
def test_a_non_software_product_is_never_compared(product_type):
    """The repository's SPDX id describes CODE. A model's openness license describes weights, a
    different artifact that may legitimately carry a different license, so comparing them
    measures nothing. This is the filter that took the raw finding count down by an order of
    magnitude, and without it the leg reports mostly category errors.
    """
    found = cc.license_findings(
        [_row(license_spdx_id="Apache-2.0")],
        {"widget": _product(type=product_type)},
        {"widget": _score("Llama-3.1-Community")},
    )
    assert found == []


@pytest.mark.parametrize("spdx", ["NOASSERTION", "other", "", "NONE", "noassertion"])
def test_an_spdx_id_that_declines_to_answer_is_not_a_contradiction(spdx):
    found = cc.license_findings(
        [_row(license_spdx_id=spdx)], {"widget": _product()}, {"widget": _score("MIT")}
    )
    assert found == []


def test_the_noassertion_flag_abstains_even_when_an_id_is_present():
    found = cc.license_findings(
        [_row(license_spdx_id="Apache-2.0", license_is_noassertion=True)],
        {"widget": _product()},
        {"widget": _score("MIT")},
    )
    assert found == []


def test_a_detail_naming_a_specific_license_file_abstains():
    """GitHub classifies ONE repository-level file. A record that deliberately reads a different
    one is not contradicted when the classifier reports the file it did read -- the case that
    made this sweep's first run report a product whose own note already explained the difference.
    """
    score = {"openness": {"components": {"license": [{"name": "MIT", "detail": "code,via LICENSE-CODE"}]}}}
    found = cc.license_findings(
        [_row(license_spdx_id="CC-BY-4.0")], {"widget": _product()}, {"widget": score}
    )
    assert found == []


def test_a_detail_that_qualifies_the_license_abstains():
    """A bespoke license built from a standard one: the classifier reporting the base license is
    expected, and the record's own detail says so.
    """
    score = {"openness": {"components": {"license": [
        {"name": "Widget-Attribution-License", "detail": "Apache-2.0 text plus an appended condition"}]}}}
    found = cc.license_findings(
        [_row(license_spdx_id="Apache-2.0")], {"widget": _product()}, {"widget": score}
    )
    assert found == []


@pytest.mark.parametrize("detail", ["", "OSI", "OSI, copyleft", "permissive non-OSI"])
def test_a_plain_detail_stays_comparable(detail):
    """The abstentions must not swallow the ordinary case, or the leg checks nothing."""
    score = {"openness": {"components": {"license": [{"name": "MIT", "detail": detail}]}}}
    found = cc.license_findings(
        [_row(license_spdx_id="CC-BY-4.0")], {"widget": _product()}, {"widget": score}
    )
    assert len(found) == 1, detail


def test_a_code_scoped_part_is_compared_even_on_a_dataset():
    """The product type is a proxy for 'does the repository license the product'. Where a part
    says outright that it covers the code, it is a claim about the same artifact the SPDX id
    describes, and excluding it by type would hide a real repository-license contradiction.
    """
    score = {"openness": {"components": {"license": [{"name": "MIT", "detail": "code"}]}}}
    found = cc.license_findings(
        [_row(license_spdx_id="GPL-3.0")], {"widget": _product(type="dataset")}, {"widget": score}
    )
    assert len(found) == 1


def test_a_compound_recorded_license_abstains():
    """Two recorded parts and there is no single thing for one SPDX id to disagree with."""
    score = {"openness": {"components": {"license": [{"name": "MIT"}, {"name": "Apache-2.0"}]}}}
    found = cc.license_findings([_row(license_spdx_id="GPL-3.0")], {"widget": _product()}, {"widget": score})
    assert found == []


def test_a_product_with_no_recorded_license_abstains():
    found = cc.license_findings(
        [_row()], {"widget": _product()}, {"widget": {"openness": {"components": {}}}}
    )
    assert found == []


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
    assert cc.sweep([_row(is_archived=True)], {"widget": _product()}, {}, settled) == []


def test_a_settlement_with_no_reason_is_ignored():
    """A ruling with no reason is indistinguishable from a finding somebody wanted to stop
    seeing, and honouring it would make the ledger the place a real contradiction hides.
    """
    settled = [{"leg": cc.RETIREMENT, "product_slug": "widget", "artifact": "acme/widget",
                "settles": "archived", "note": "  "}]
    assert len(cc.sweep([_row(is_archived=True)], {"widget": _product()}, {}, settled)) == 1


def test_a_settlement_does_not_cover_a_different_observation():
    """Bound to what was observed, so it expires when the world says something different --
    the difference between settling a question and silencing it.
    """
    score = {"openness": {"components": {"license": [{"name": "MIT", "detail": "OSI"}]}}}
    settled = [{"leg": cc.LICENSE, "product_slug": "widget", "artifact": "acme/widget",
                "settles": "CC-BY-4.0", "note": "docs license, code is MIT"}]
    quiet = cc.sweep([_row(license_spdx_id="CC-BY-4.0")], {"widget": _product()}, {"widget": score}, settled)
    assert quiet == []
    moved = cc.sweep([_row(license_spdx_id="GPL-3.0")], {"widget": _product()}, {"widget": score}, settled)
    assert len(moved) == 1


# ---------------------------------------------------------------------------
# same_license: the comparisons that must not read as disagreement
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "recorded,spdx",
    [
        ("mit", "MIT"),                    # normalize_license does not fold case
        ("apache-2.0", "Apache-2.0"),
        ("GPLv3", "GPL-3.0"),              # one license, two spellings, covered by no alias
        ("AGPLv3", "AGPL-3.0"),
        ("LGPLv2.1", "LGPL-2.1"),
        ("LGPL-3.0/GPL-3.0", "LGPL-3.0"),  # one declared name offering alternatives
        ("LGPL-3.0/GPL-3.0", "GPL-3.0"),
    ],
)
def test_these_are_the_same_license(recorded, spdx):
    assert cc.same_license(recorded, spdx), f"{recorded!r} vs {spdx!r}"


@pytest.mark.parametrize("recorded,spdx", [("MIT", "CC-BY-4.0"), ("Apache-2.0", "GPL-3.0"),
                                           ("MIT", "Apache-2.0")])
def test_these_are_not(recorded, spdx):
    """The gate has to be able to fail, or the parametrized agreements above prove nothing."""
    assert not cc.same_license(recorded, spdx)


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
