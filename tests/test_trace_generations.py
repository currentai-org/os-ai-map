"""The scoring-trace generation report: what counts as a complete generation, and what never does.

`build/trace_generations.py` reads the generations `currentai.evaluation.axis_results` holds and
says which of them can count toward the agreement ADR-001 asks for before the warehouse's duplicate
openness computation is retired (ruling R-2026-11-08-t). A generation that counts by mistake is the
failure that matters here, so most of these tests are about the ones that must not.
"""

import subprocess

import pytest

import build.trace_generations as T

DVID_A = "a" * 64
DVID_B = "b" * 64


def _row(dvid, sha, product, status="scored", reproduces="True", category="c"):
    return {"declaration_version_id": dvid, "source_git_sha": sha, "product_slug": product,
            "category_slug": category, "status": status, "reproduces_recorded": reproduces}


def _reachable(sha):
    return {"identity": "reachable", "committed_at": f"2026-11-{int(sha[-2:], 16) % 28 + 1:02d}T00:00:00+00:00"}


def test_a_generation_scoring_and_reproducing_every_row_is_complete():
    rows = [_row(DVID_A, "aaaaaa01", "p"), _row(DVID_A, "aaaaaa01", "q", reproduces=True)]
    (gen,) = T.assess(T.summarize(rows), _reachable)
    assert (gen["rows"], gen["scored"], gen["agreeing"]) == (2, 2, 2)
    assert gen["complete"]


def test_a_deferred_row_keeps_its_generation_incomplete_and_is_named():
    """R-2026-11-08-t: 1,117 of 1,118 is not complete agreement."""
    rows = [_row(DVID_A, "aaaaaa01", "p"), _row(DVID_A, "aaaaaa01", "held-one", status="deferred", reproduces=None)]
    (gen,) = T.assess(T.summarize(rows), _reachable)
    assert not gen["complete"]
    assert gen["unscored"] == ["held-one [c]: deferred"]
    assert gen["disagreeing"] == []


def test_a_scored_row_that_does_not_reproduce_is_a_disagreement():
    rows = [_row(DVID_A, "aaaaaa01", "p"), _row(DVID_A, "aaaaaa01", "drifted", reproduces="False")]
    (gen,) = T.assess(T.summarize(rows), _reachable)
    assert gen["disagreeing"] == ["drifted [c]"] and not gen["complete"]


@pytest.mark.parametrize("identity", ["unreachable", "unknown"])
def test_a_generation_from_a_commit_this_history_cannot_vouch_for_does_not_count(identity):
    rows = [_row(DVID_A, "aaaaaa01", "p")]
    (gen,) = T.assess(T.summarize(rows), lambda sha: {"identity": identity, "committed_at": None})
    assert not gen["complete"]


def test_generations_are_ordered_by_commit_date_with_undatable_ones_last():
    rows = [_row(DVID_A, "aaaaaa09", "p"), _row(DVID_B, "bbbbbb02", "p"), _row("c" * 64, "cccccc05", "p")]

    def facts(sha):
        if sha == "cccccc05":
            return {"identity": "unknown", "committed_at": None}
        return _reachable(sha)

    ordered = [g["source_git_sha"] for g in T.assess(T.summarize(rows), facts)]
    assert ordered == ["bbbbbb02", "aaaaaa09", "cccccc05"]


def test_the_report_counts_complete_generations_and_lists_every_unscored_row():
    rows = [
        _row(DVID_A, "aaaaaa01", "p"),
        _row(DVID_B, "bbbbbb02", "p"),
        _row(DVID_B, "bbbbbb02", "waiting", status="blocked_on_tier", reproduces=None),
    ]
    text = T.render(T.assess(T.summarize(rows), _reachable))
    assert "2 generation(s), 1 complete." in text
    assert "~ bbbbbb02: waiting [c]: blocked_on_tier" in text
    assert f"accepts {T.REQUIRED_GENERATIONS} complete generations" in text


def test_an_empty_table_reports_no_generation_instead_of_zero_of_zero():
    assert "~ none" in T.render([])


def test_a_table_the_catalog_does_not_know_holds_no_generation():
    def missing(sql):
        raise RuntimeError("TablesNotFound: currentai.evaluation.axis_results")

    assert T.read_generations(run_query=missing) == []
    assert T.deployed_generations("evaluation", "axis_results", run_query=missing) == {}


def test_a_read_failure_is_one_line_of_report_and_never_an_exception():
    def refused(sql):
        raise RuntimeError("401 Unauthorized")

    assert T.report(run_query=refused).startswith("  ~ scoring-trace generations could not be read")
    with pytest.raises(RuntimeError):
        T.deployed_generations("evaluation", "axis_results", run_query=refused)


def test_deployed_generations_keys_rows_by_declaration():
    rows = [{"declaration_version_id": DVID_A, "source_git_sha": "aaaaaa01", "n": 12},
            {"declaration_version_id": DVID_B, "source_git_sha": "bbbbbb02", "n": 15}]
    held = T.deployed_generations("evaluation", "axis_facts", run_query=lambda sql: rows)
    assert held == {DVID_A: {"source_git_sha": "aaaaaa01", "rows": 12},
                    DVID_B: {"source_git_sha": "bbbbbb02", "rows": 15}}


def test_one_declaration_under_two_commits_is_an_error_not_one_generation():
    rows = [{"declaration_version_id": DVID_A, "source_git_sha": "aaaaaa01", "n": 12},
            {"declaration_version_id": DVID_A, "source_git_sha": "bbbbbb02", "n": 3}]
    with pytest.raises(RuntimeError, match="more than one source_git_sha"):
        T.deployed_generations("evaluation", "axis_facts", run_query=lambda sql: rows)


def test_only_the_three_trace_tables_can_be_asked_about():
    with pytest.raises(ValueError):
        T.deployed_generations("evaluation", "product_scores; DROP", run_query=lambda sql: [])


def test_the_loaders_boolean_and_the_csvs_string_both_read_as_reproducing():
    rows = [_row(DVID_A, "aaaaaa01", "p", reproduces=True), _row(DVID_A, "aaaaaa01", "q", reproduces="true"),
            _row(DVID_A, "aaaaaa01", "r", reproduces="")]
    (gen,) = T.summarize(rows)
    assert gen["agreeing"] == 2 and gen["disagreeing"] == ["r [c]"]


def test_commit_facts_reads_this_checkouts_own_head():
    head = subprocess.run(["git", "-C", str(T.ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    facts = T.commit_facts(head)
    assert facts["identity"] == "reachable" and facts["committed_at"]


def test_commit_facts_never_calls_a_commit_it_cannot_find_reachable():
    facts = T.commit_facts("0" * 40)
    assert facts["identity"] in {"unreachable", "unknown"} and facts["committed_at"] is None
    assert T.commit_facts("not-a-sha; rm -rf")["identity"] == "unreachable"
