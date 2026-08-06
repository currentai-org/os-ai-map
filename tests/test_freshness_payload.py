from datetime import date

import pytest

import build.freshness_payload as fp
from build.freshness_payload import ShallowRepositoryError, resolve_freshness


def test_refuses_to_emit_dates_in_a_shallow_clone(tmp_path, monkeypatch):
    """Named for the failure it guards: a --depth 1 checkout dates every score file to the
    tip commit, silently, so all 470 products would publish the same freshness date."""
    monkeypatch.setattr("build.freshness_payload._is_shallow", lambda root: True)
    with pytest.raises(ShallowRepositoryError):
        resolve_freshness(tmp_path)


def test_last_verified_outranks_the_commit_date(tmp_path, monkeypatch):
    monkeypatch.setattr("build.freshness_payload._is_shallow", lambda root: False)
    monkeypatch.setattr("build.freshness_payload._commit_dates", lambda root: {"apertus": "2026-08-05"})
    monkeypatch.setattr("build.freshness_payload._last_verified", lambda root: {"apertus": "2026-07-30"})
    assert resolve_freshness(tmp_path)["apertus"] == {"date": "2026-07-30", "basis": "verified"}


def test_falls_back_to_the_commit_date_and_says_so(monkeypatch):
    """The basis is what lets the page label the weaker claim honestly.

    Uses monkeypatch (not a bare module-attribute assignment) so the substitution is
    reverted after this test — an unguarded `fp._last_verified = ...` here previously
    clobbered the real implementation for every test that ran after it in this file.
    """
    monkeypatch.setattr(fp, "_is_shallow", lambda root: False)
    monkeypatch.setattr(fp, "_commit_dates", lambda root: {"vllm": "2026-06-04"})
    monkeypatch.setattr(fp, "_last_verified", lambda root: {})
    assert fp.resolve_freshness(None)["vllm"] == {"date": "2026-06-04", "basis": "commit"}


def test_last_verified_takes_the_most_recent_date_across_axes(tmp_path):
    """The three tests above all mock `_last_verified` away, so none of them exercise its
    real glob-and-aggregate logic. A product with last_verified on more than one axis must
    report the latest of them, not the first one read or the openness axis specifically."""
    scores = tmp_path / "sources" / "scores"
    scores.mkdir(parents=True)
    (scores / "multi-axis.yaml").write_text(
        "openness:\n  last_verified: '2026-07-01'\n"
        "adoption:\n  last_verified: '2026-07-15'\n"
        "capability:\n  score: 3\n"
    )
    (scores / "no-verification.yaml").write_text("openness:\n  score: 2\n")
    found = fp._last_verified(tmp_path)
    assert found == {"multi-axis": "2026-07-15"}, \
        "must take the max across axes, and must not invent a date for an unverified product"


def test_commit_dates_converts_date_objects_to_isoformat_strings(monkeypatch):
    """`check_freshness.commit_dates()` returns real `date` objects; the payload needs JSON-
    serializable strings, and the conversion must preserve every slug it is handed."""
    monkeypatch.setattr(fp, "commit_dates", lambda: {"vllm": date(2026, 6, 4), "olmo": date(2026, 7, 30)})
    assert fp._commit_dates(None) == {"vllm": "2026-06-04", "olmo": "2026-07-30"}
