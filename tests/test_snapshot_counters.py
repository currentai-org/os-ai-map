"""The interim counter history: append-only, keyed on the platform's fetch time, raw values only."""

from build import snapshot_counters as SC


def _gh(slug, repo, observed, counter, count):
    return {"product_slug": slug, "artifact_id": repo, "observed_at": observed,
            "counter": counter, "asset_count": count}


def test_a_rerun_inside_the_same_refresh_appends_nothing():
    fresh = {"github_release": [_gh("ollama", "ollama/ollama", "2026-09-28 12:56:19", 219236965, 2628)],
             "docker": []}
    rows, added = SC.merge([], fresh, "2026-09-28")
    assert added == 1
    again, added_again = SC.merge(rows, fresh, "2026-09-29")
    assert added_again == 0 and again == rows


def test_a_new_refresh_is_a_new_row_and_the_old_one_stays():
    week0 = {"github_release": [_gh("ollama", "ollama/ollama", "2026-09-28 12:56:19", 100, 5)], "docker": []}
    week1 = {"github_release": [_gh("ollama", "ollama/ollama", "2026-10-04 03:01:00", 160, 6)], "docker": []}
    rows, _ = SC.merge([], week0, "2026-09-28")
    rows, added = SC.merge(rows, week1, "2026-10-05")
    assert added == 1
    assert [r["counter"] for r in rows] == ["100", "160"]


def test_docker_rows_carry_no_asset_count():
    fresh = {"github_release": [], "docker": [
        {"product_slug": "n8n", "artifact_id": "n8nio/n8n", "observed_at": "2026-09-28T13:00:00",
         "counter": 265105563, "asset_count": None}]}
    rows, _ = SC.merge([], fresh, "2026-09-28")
    assert rows[0]["asset_count"] == "" and rows[0]["observed_at"] == "2026-09-28 13:00:00"
    assert SC.problems(rows) == []


def test_a_falling_counter_is_kept_not_hidden():
    """A deleted or replaced asset lowers the lifetime total. That is an observation, and the
    increment step must void the window; the history must not smooth it away."""
    rows, _ = SC.merge([], {"github_release": [
        _gh("x", "o/x", "2026-09-28 00:00:00", 500, 4),
        _gh("x", "o/x", "2026-10-04 00:00:00", 300, 3)], "docker": []}, "2026-10-05")
    assert [r["counter"] for r in rows] == ["500", "300"]
    assert SC.problems(rows) == []


def test_problems_catches_duplicates_unknown_sources_and_bad_dates():
    good = SC._normalize("github_release", _gh("x", "o/x", "2026-09-28 00:00:00", 1, 1), "2026-09-28")
    assert SC.problems([good]) == []
    assert any("duplicate" in p for p in SC.problems([good, dict(good)]))
    assert any("unknown source" in p for p in SC.problems([{**good, "source": "npm"}]))
    assert SC.problems([{**good, "observed_at": "not a date"}])


def test_the_committed_history_is_well_formed():
    assert SC.problems(SC.read_history()) == []
