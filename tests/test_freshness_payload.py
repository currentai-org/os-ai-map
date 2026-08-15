import os
import subprocess
from datetime import date
from pathlib import Path

import pytest
import yaml

import build.freshness_payload as fp
from build.freshness_payload import ShallowRepositoryError, resolve_freshness


def _git(*args: str, cwd: Path, env: dict | None = None) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True, env=env)


def _init_repo_with_one_score(root: Path, slug: str, commit_date: str) -> None:
    """A throwaway git repository, distinct from this checkout, with exactly one score
    file committed on a fabricated date. Used to prove root-scoping is real rather than
    mocked: this slug and this date exist nowhere in os-ai-map's own history."""
    scores = root / "sources" / "scores"
    scores.mkdir(parents=True)
    (scores / f"{slug}.yaml").write_text("openness:\n  score: 3\n")
    _git("init", "-q", cwd=root)
    _git("-c", "user.email=test@example.com", "-c", "user.name=test",
         "add", "sources/scores", cwd=root)
    env = {**os.environ, "GIT_AUTHOR_DATE": f"{commit_date}T00:00:00",
           "GIT_COMMITTER_DATE": f"{commit_date}T00:00:00"}
    _git("-c", "user.email=test@example.com", "-c", "user.name=test",
         "commit", "-q", "-m", "add score", cwd=root, env=env)


def test_refuses_to_emit_dates_in_a_shallow_clone(tmp_path, monkeypatch):
    """Named for the failure it guards: a --depth 1 checkout dates every score file to the
    tip commit, silently, so all 470 products would publish the same freshness date."""
    monkeypatch.setattr("build.freshness_payload._is_shallow", lambda root: True)
    with pytest.raises(ShallowRepositoryError):
        resolve_freshness(tmp_path)


def test_last_verified_outranks_the_commit_date(tmp_path, monkeypatch):
    monkeypatch.setattr("build.freshness_payload._is_shallow", lambda root: False)
    monkeypatch.setattr("build.freshness_payload._commit_dates", lambda root: {"apertus": "2026-08-05"})
    monkeypatch.setattr("build.freshness_payload._axis_dates",
                        lambda root: {"apertus": ({"openness": "2026-07-30"}, [])})
    assert resolve_freshness(tmp_path)["apertus"] == {"date": "2026-07-30", "basis": "verified"}


def test_falls_back_to_the_commit_date_and_says_so(monkeypatch):
    """The basis is what lets the page label the weaker claim honestly.

    Uses monkeypatch (not a bare module-attribute assignment) so the substitution is
    reverted after this test — an unguarded `fp._axis_dates = ...` here previously
    clobbered the real implementation for every test that ran after it in this file.
    """
    monkeypatch.setattr(fp, "_is_shallow", lambda root: False)
    monkeypatch.setattr(fp, "_commit_dates", lambda root: {"vllm": "2026-06-04"})
    monkeypatch.setattr(fp, "_axis_dates", lambda root: {})
    assert fp.resolve_freshness(None)["vllm"] == {"date": "2026-06-04", "basis": "commit"}


def test_axis_dates_reports_both_the_confirmed_and_the_unconfirmed_axes(tmp_path):
    """The three tests above all mock `_axis_dates` away, so none of them exercise its real
    glob-and-aggregate logic.

    Two things it must get right. A product with last_verified on more than one axis reports
    the latest of them, not the first one read or the openness axis specifically. And it must
    return the UNDATED axes too — dropping them is what let a held axis publish as
    `basis: verified`, since a max over the dated ones alone cannot tell that anything is
    missing.
    """
    scores = tmp_path / "sources" / "scores"
    scores.mkdir(parents=True)
    (scores / "multi-axis.yaml").write_text(
        "openness:\n  last_verified: '2026-07-01'\n"
        "adoption:\n  last_verified: '2026-07-15'\n"
        "capability:\n  score: 3\n"
    )
    (scores / "no-verification.yaml").write_text("openness:\n  score: 2\n")
    found = fp._axis_dates(tmp_path)

    dated, undated = found["multi-axis"]
    assert max(dated.values()) == "2026-07-15", "must take the max across dated axes"
    assert undated == ["capability"], "an undated axis must be reported, not dropped"

    dated, undated = found["no-verification"]
    assert dated == {}, "must not invent a date for an unverified product"
    assert undated == ["openness"]


def test_commit_dates_converts_date_objects_to_isoformat_strings(monkeypatch):
    """`check_freshness.commit_dates()` returns real `date` objects; the payload needs JSON-
    serializable strings, and the conversion must preserve every slug it is handed."""
    monkeypatch.setattr(fp, "commit_dates",
                        lambda root=None: {"vllm": date(2026, 6, 4), "olmo": date(2026, 7, 30)})
    assert fp._commit_dates(None) == {"vllm": "2026-06-04", "olmo": "2026-07-30"}


def test_is_shallow_raises_when_root_is_not_a_git_repository(tmp_path):
    """`git rev-parse` exits 128 with empty stdout when `root` is not a git repository at
    all. The old code read that the same as a clean 'false' -- ambiguous or failed
    detection defaulting to the safe-looking branch is the exact failure the guard exists
    to prevent, arriving through a different door."""
    with pytest.raises(ShallowRepositoryError):
        fp._is_shallow(tmp_path)


def test_is_shallow_raises_when_git_binary_is_missing(tmp_path, monkeypatch):
    """git absent from PATH must fail the same way as git failing: loudly, not as 'false'."""
    def _no_git(*args, **kwargs):
        raise FileNotFoundError("git")
    monkeypatch.setattr(fp.subprocess, "run", _no_git)
    with pytest.raises(ShallowRepositoryError):
        fp._is_shallow(tmp_path)


def test_resolve_freshness_raises_when_root_is_not_a_git_repository(tmp_path):
    """The public entry point must surface the same failure, not just the private helper."""
    (tmp_path / "sources" / "scores").mkdir(parents=True)
    with pytest.raises(ShallowRepositoryError):
        resolve_freshness(tmp_path)


def test_commit_dates_are_scoped_to_the_given_root_not_this_repository(tmp_path):
    """`_commit_dates` used to ignore its own `root` argument and read THIS repository's
    history via check_freshness's module-level ROOT constant. Prove root-scoping is real:
    a throwaway repo with one score file, committed on a date that appears nowhere in
    os-ai-map's own history, for a slug that does not exist in os-ai-map at all. If root
    were ignored, this slug would be missing entirely (real history has no such file)."""
    _init_repo_with_one_score(tmp_path, "throwaway-product", "2020-01-01")
    result = resolve_freshness(tmp_path)
    assert set(result) == {"throwaway-product"}, "root must scope which files are read"
    assert result["throwaway-product"]["date"] == "2020-01-01"
    assert result["throwaway-product"]["basis"] == "commit"
    # The record also carries `unconfirmed_axes`, since the fixture's single axis is undated.
    # That is asserted where it is the subject — see
    # test_a_product_with_no_confirmed_axis_still_carries_its_hold. Pinning the whole dict
    # here would make this root-scoping test fail on every unrelated shape change.


def _corpus_with(tmp_path, axes: dict, queue: dict | None = None):
    """A one-product checkout where `axes` maps axis -> last_verified (None = undated)."""
    import subprocess

    (tmp_path / "sources" / "scores").mkdir(parents=True)
    doc = {"product": "widget"}
    for axis, when in axes.items():
        block = {"score": 4}
        if when:
            block["last_verified"] = when
        doc[axis] = block
    (tmp_path / "sources" / "scores" / "widget.yaml").write_text(yaml.safe_dump(doc))
    if queue is not None:
        (tmp_path / "sources" / "verification_queue.yaml").write_text(
            yaml.safe_dump({"version": 1, "held": queue})
        )
    env = {**os.environ, "GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@e.com",
           "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@e.com"}
    for args in (["init", "-q", "-b", "main"], ["add", "-A"], ["commit", "-q", "-m", "c"]):
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True, env=env)
    return tmp_path


def test_an_undated_axis_makes_the_product_partial_not_verified(tmp_path):
    """The bug this replaced: `max()` over the axes that HAD a date, ignoring the ones that
    did not, published `basis: verified` for a product with a deliberately unconfirmed axis.
    `falcon`, `qualcomm-ai-engine-direct` and `aws-neuron` all shipped that way."""
    root = _corpus_with(tmp_path, {"openness": "2026-08-13", "adoption": None,
                                   "capability": "2026-08-13"})
    record = resolve_freshness(root)["widget"]
    assert record["basis"] == "partial"
    assert record["unconfirmed_axes"] == ["adoption"]
    assert record["date"] == "2026-08-13"


def test_all_axes_dated_is_still_verified(tmp_path):
    root = _corpus_with(tmp_path, {"openness": "2026-08-13", "adoption": "2026-08-10",
                                   "capability": "2026-08-13"})
    record = resolve_freshness(root)["widget"]
    assert record["basis"] == "verified"
    assert "unconfirmed_axes" not in record
    assert "verification_holds" not in record


def test_a_held_axis_carries_its_reason_into_the_payload(tmp_path):
    root = _corpus_with(
        tmp_path,
        {"openness": "2026-08-13", "adoption": None, "capability": "2026-08-13"},
        queue={"widget": {"adoption": {"since": "2026-08-15", "because": "no figure published"}}},
    )
    holds = resolve_freshness(root)["widget"]["verification_holds"]
    assert holds == [{"axis": "adoption", "since": "2026-08-15",
                      "reason": "no figure published"}]


def test_an_undated_axis_with_no_queue_entry_is_still_partial(tmp_path):
    """`partial` follows from the axis being unconfirmed, not from the queue. A hold explains
    an unconfirmed axis; its absence does not make one confirmed."""
    root = _corpus_with(tmp_path, {"openness": "2026-08-13", "adoption": None,
                                   "capability": "2026-08-13"}, queue={})
    record = resolve_freshness(root)["widget"]
    assert record["basis"] == "partial"
    assert "verification_holds" not in record


def test_no_axis_dated_falls_back_to_commit(tmp_path):
    root = _corpus_with(tmp_path, {"openness": None, "adoption": None, "capability": None})
    assert resolve_freshness(root)["widget"]["basis"] == "commit"


def test_the_product_date_is_the_oldest_confirmed_axis(tmp_path):
    """`last_verified` means the date EVERYTHING was confirmed. Reduced to one product date,
    "everything" is the constraint, so the oldest confirmed axis is the defensible answer.

    This was max() until 2026-08-15 — the same overstatement as publishing a held axis as
    verified, in a less obvious form, and the common case rather than an edge: 176 of the 472
    products carry differing axis dates.
    """
    root = _corpus_with(tmp_path, {"openness": "2026-08-11", "adoption": "2026-08-09",
                                   "capability": "2026-08-13"})
    record = resolve_freshness(root)["widget"]
    assert record["date"] == "2026-08-09", "the product is current only through its oldest axis"
    assert record["basis"] == "verified"
    assert record["latest_axis_confirmation"] == "2026-08-13"


def test_latest_axis_confirmation_is_omitted_when_it_adds_nothing(tmp_path):
    root = _corpus_with(tmp_path, {"openness": "2026-08-13", "adoption": "2026-08-13",
                                   "capability": "2026-08-13"})
    assert "latest_axis_confirmation" not in resolve_freshness(root)["widget"]


def test_a_partial_product_dates_from_its_oldest_CONFIRMED_axis(tmp_path):
    root = _corpus_with(tmp_path, {"openness": "2026-08-11", "adoption": None,
                                   "capability": "2026-08-13"})
    record = resolve_freshness(root)["widget"]
    assert record["date"] == "2026-08-11"
    assert record["basis"] == "partial"


def test_a_product_with_no_confirmed_axis_still_carries_its_hold(tmp_path):
    """The commit path dropped holds entirely, which recreated this module's own defect for a
    fully unconfirmed product: honest in the repo, invisible outside it."""
    root = _corpus_with(
        tmp_path,
        {"openness": None, "adoption": None, "capability": None},
        queue={"widget": {"adoption": {"since": "2026-08-15", "because": "no figure published"}}},
    )
    record = resolve_freshness(root)["widget"]
    assert record["basis"] == "commit"
    assert record["unconfirmed_axes"] == ["adoption", "capability", "openness"]
    assert record["verification_holds"] == [
        {"axis": "adoption", "since": "2026-08-15", "reason": "no figure published"}
    ]


def test_a_hold_on_a_confirmed_axis_is_not_emitted(tmp_path):
    """A stale queue entry naming an axis that has since been confirmed must not reach the
    payload — `check_payload` rejects that shape, so emitting it would be a hard failure."""
    root = _corpus_with(
        tmp_path,
        {"openness": "2026-08-13", "adoption": "2026-08-13", "capability": None},
        queue={"widget": {"adoption": {"since": "2026-08-01", "because": "stale entry"}}},
    )
    record = resolve_freshness(root)["widget"]
    assert record["unconfirmed_axes"] == ["capability"]
    assert "verification_holds" not in record
