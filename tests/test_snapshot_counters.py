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
    increment step clamps and flags the window; the history must not smooth it away."""
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


def test_the_same_reading_with_different_values_is_an_error():
    import pytest

    first = {"github_release": [_gh("x", "o/x", "2026-09-28 00:00:00", 500, 4)], "docker": []}
    rows, _ = SC.merge([], first, "2026-09-28")
    changed = {"github_release": [_gh("x", "o/x", "2026-09-28 00:00:00", 501, 4)], "docker": []}
    with pytest.raises(SC.ConflictingReading):
        SC.merge(rows, changed, "2026-09-29")


def test_union_keeps_rows_from_both_sides_and_their_capture_dates():
    main_rows, _ = SC.merge([], {"github_release": [_gh("a", "o/a", "2026-09-28 00:00:00", 1, 1)], "docker": []}, "2026-09-28")
    pending, _ = SC.merge([], {"github_release": [_gh("b", "o/b", "2026-10-04 00:00:00", 2, 1)], "docker": []}, "2026-10-05")
    rows, added = SC.union(main_rows, pending)
    assert added == 1 and {r["product_slug"] for r in rows} == {"a", "b"}
    assert {r["captured_on"] for r in rows} == {"2026-09-28", "2026-10-05"}
    again, added_again = SC.union(rows, pending)
    assert added_again == 0 and again == rows


def _series(slug, repo, *readings):
    rows, _ = SC.merge([], {"github_release": [
        _gh(slug, repo, observed, counter, 1) for observed, counter in readings], "docker": []}, "2026-10-05")
    return rows


def test_a_rising_counter_gives_its_difference_unflagged():
    (window,) = SC.increments(_series("ollama", "ollama/ollama",
                                      ("2026-09-28 00:00:00", 100), ("2026-10-04 00:00:00", 160)))
    assert window["increment"] == 60 and window["reset"] is False


def test_the_three_falling_counters_from_issue_850_clamp_to_zero_and_flag_a_reset():
    """The 28 Sep and 4 Oct readings of the three artifacts whose lifetime totals fell (#850)."""
    rows = (_series("openpipe", "OpenPipe/ART", ("2026-09-28 16:59:59", 2573), ("2026-10-04 03:04:10", 1249))
            + _series("tenstorrent-blackhole", "tenstorrent/tt-metal",
                      ("2026-09-28 16:59:59", 64902), ("2026-10-04 03:04:10", 64720))
            + _series("mlflow", "mlflow/mlflow", ("2026-09-28 16:59:59", 4), ("2026-10-04 03:04:10", 0)))
    windows = {w["artifact_id"]: w for w in SC.increments(rows)}
    assert set(windows) == {"OpenPipe/ART", "tenstorrent/tt-metal", "mlflow/mlflow"}
    for w in windows.values():
        assert w["increment"] == 0 and w["reset"] is True
    assert (windows["OpenPipe/ART"]["from_counter"], windows["OpenPipe/ART"]["to_counter"]) == (2573, 1249)


def test_after_a_reset_the_baseline_restarts_from_the_lower_reading():
    """The next window is measured from 1,249, not from the old high of 2,573: 1,249 -> 1,400 is
    151 real downloads, where a carried-forward high-water mark would report 0."""
    windows = SC.increments(_series("openpipe", "OpenPipe/ART",
                                    ("2026-09-28 16:59:59", 2573), ("2026-10-04 03:04:10", 1249),
                                    ("2026-10-11 03:00:00", 1400)))
    assert [(w["increment"], w["reset"]) for w in windows] == [(0, True), (151, False)]
    assert windows[1]["from_counter"] == 1249


def test_increments_pair_readings_in_time_order_and_never_across_series():
    rows = _series("a", "o/a", ("2026-10-04 00:00:00", 30), ("2026-09-28 00:00:00", 10)) \
        + _series("b", "o/b", ("2026-09-28 00:00:00", 5))
    windows = SC.increments(rows)
    assert len(windows) == 1 and windows[0]["artifact_id"] == "o/a"
    assert (windows[0]["from_counter"], windows[0]["increment"], windows[0]["reset"]) == (10, 20, False)


def test_no_window_in_the_committed_history_is_negative():
    windows = SC.increments(SC.read_history())
    assert all(w["increment"] >= 0 for w in windows)
    assert all(w["reset"] == (w["to_counter"] < w["from_counter"]) for w in windows)
