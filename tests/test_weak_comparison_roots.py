"""A comparison root has to be evidenced, not merely present.

`check_capability` already proves the arithmetic: a `one_below` against a 4 is a 3. It said
nothing about whether the 4 meant anything. On 2026-08-31 `langfuse` (22 dependents) and
`openhands` (25) were both named as `relative_to` with an empty capability `value`, and the gate
was green across all 47 bands. Consistent is not correct.
"""
from pathlib import Path

from build.check_capability import load, weak_roots

ROOT = Path(__file__).resolve().parents[1]


def _score(value=None, score=4, sources=True, basis="feature_matrix"):
    block = {"score": score, "basis": basis}
    if value is not None:
        block["value"] = value
    if sources:
        block["sources"] = [{"url": "https://example.invalid", "shows": "x"}]
    return {"capability": block}


GOOD = ("A substantive description of what the product does, long enough to be read as a claim "
        "rather than a placeholder.")


def test_a_root_with_score_value_and_sources_is_not_weak():
    scores = {"peer": _score(GOOD), "dep": {"capability": {"score": 3, "relative_to": "peer",
                                                           "relation": "one_below"}}}
    assert weak_roots(scores) == []


def test_an_empty_value_is_weak():
    """The langfuse and openhands case, which the arithmetic gate could not see."""
    scores = {"peer": _score(None), "dep": {"capability": {"score": 3, "relative_to": "peer",
                                                          "relation": "one_below"}}}
    roots = weak_roots(scores)
    assert [(p, n) for p, n, _ in roots] == [("peer", 1)]
    assert any("no capability value" in d for d in roots[0][2])


def test_a_placeholder_value_is_weak_too():
    """Guarding the mutation: the defect must not be able to become `value: "TBD"`."""
    roots = weak_roots({"peer": _score("TBD"),
                        "dep": {"capability": {"score": 3, "relative_to": "peer",
                                               "relation": "one_below"}}})
    assert roots and any("placeholder" in d for d in roots[0][2])


def test_a_short_benchmark_value_is_not_weak():
    """The false-positive path. `capability.md` allows `value` to be an exact observation, and
    `SWE-bench Verified: 74.9` is complete at 24 characters. 63 records already record a
    benchmark basis, so a blanket length floor would manufacture weak roots as those fill in."""
    peer = {"capability": {"score": 5, "basis": "benchmark", "value": "SWE-bench Verified: 74.9",
                           "sources": [{"url": "https://example.invalid", "shows": "x"}]}}
    scores = {"peer": peer, "dep": {"capability": {"score": 4, "relative_to": "peer",
                                                   "relation": "one_below"}}}
    assert weak_roots(scores) == []


def test_a_short_feature_matrix_value_is_weak():
    """The prose floor still applies where the value IS a description."""
    peer = {"capability": {"score": 4, "basis": "feature_matrix", "value": "does stuff",
                           "sources": [{"url": "https://example.invalid", "shows": "x"}]}}
    roots = weak_roots({"peer": peer, "dep": {"capability": {"score": 3, "relative_to": "peer",
                                                             "relation": "one_below"}}})
    assert roots and any("prose floor" in d for d in roots[0][2])


def test_a_null_score_is_weak():
    roots = weak_roots({"peer": _score(GOOD, score=None),
                        "dep": {"capability": {"score": 3, "relative_to": "peer",
                                               "relation": "one_below"}}})
    assert roots and any("no capability score" in d for d in roots[0][2])


def test_an_unsourced_capability_is_weak():
    """A value nobody can re-open is an assertion, not evidence."""
    roots = weak_roots({"peer": _score(GOOD, sources=False),
                        "dep": {"capability": {"score": 3, "relative_to": "peer",
                                               "relation": "one_below"}}})
    assert roots and any("carries no sources" in d for d in roots[0][2])


def test_a_product_nobody_compares_against_is_not_a_root():
    """The check is about roots, not about coverage - an unreferenced null value is a
    curation backlog item, which `--candidates` already reports."""
    assert weak_roots({"lonely": _score(None)}) == []


def test_roots_are_ordered_by_fan_out():
    """Remediation order is the point: fix what carries the most bands first."""
    scores = {"small": _score(None), "big": _score(None)}
    for i in range(3):
        scores[f"d{i}"] = {"capability": {"score": 3, "relative_to": "big", "relation": "one_below"}}
    scores["d9"] = {"capability": {"score": 3, "relative_to": "small", "relation": "one_below"}}
    assert [p for p, _, _ in weak_roots(scores)] == ["big", "small"]


def test_the_real_corpus_is_reported_not_gated():
    """Report-only today: 12 roots carry 18 bands, so failing the build would block every
    scoring change until an unrelated backlog is cleared. Lower this as they are fixed.

    Ten of the twelve are datasets, where a capability value has to say what the corpus
    covers rather than how a tool performs; that is a different piece of work from the
    engine roots this cap started with."""
    roots = weak_roots(load()[0])
    assert len(roots) <= 12, [p for p, _, _ in roots]
