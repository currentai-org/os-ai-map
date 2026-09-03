"""The replay eval, and the two rules pinned as tests rather than metrics.

Fixtures only. The `currentai.identity.*` dataset has not deployed, so nothing here touches
the warehouse -- `Truth` is built from repo sources (`build.resolution`, `sources/products/`,
`sources/organizations/`) exactly as `build.identity_eval.load_truth` does for real, and the
edge sets are hand-built dicts shaped like the future edge tables.
"""

from __future__ import annotations

from build.identity_eval import (
    KNOWN_NEGATIVES,
    Truth,
    digest_items,
    emits,
    emitted_at_threshold,
    floor_failures,
    load_truth,
    replay,
)


def test_precision_recall_math():
    truth = Truth(equivalence={("github", "a2aproject/a2a"): "agent2agent-protocol"})
    edges = {
        "equivalence": [
            {"artifact_kind": "github", "artifact_id": "a2aproject/a2a",
             "product_slug": "agent2agent-protocol", "confidence": 1.0},
            {"artifact_kind": "github", "artifact_id": "x/y",
             "product_slug": "wrong", "confidence": 1.0},
        ]
    }
    m = replay(edges, truth)["equivalence"]
    assert m.precision == 0.5
    assert m.recall == 1.0
    assert m.n_truth == 1
    assert m.n_emitted_at_threshold == 2


def test_name_match_never_auto_emits():
    edges = {
        "membership": [
            {"artifact_kind": "pypi", "artifact_id": "foo", "product_slug": "foo",
             "confidence": 0.5, "method": "name_match", "scoring_bearing": False}
        ]
    }
    assert emitted_at_threshold(edges)["membership"] == []
    assert digest_items(edges)[0]["artifact_id"] == "foo"


def test_scoring_bearing_membership_never_auto_emits():
    edges = {
        "membership": [
            {"artifact_kind": "pypi", "artifact_id": "elasticsearch", "product_slug": "elasticsearch",
             "confidence": 0.95, "method": "backlink", "scoring_bearing": True}
        ]
    }
    assert emitted_at_threshold(edges)["membership"] == []
    assert digest_items(edges)[0]["artifact_id"] == "elasticsearch"


def test_scoring_bearing_never_emits_even_at_confidence_one():
    """The exclusion is unconditional -- no confidence clears it, unlike every other rule
    here which is a threshold that a high enough confidence satisfies."""
    edge = {"artifact_kind": "pypi", "artifact_id": "x", "product_slug": "y",
            "confidence": 1.0, "method": "backlink", "scoring_bearing": True}
    assert emits(edge, "membership") is False


def test_name_match_never_emits_on_any_relation():
    for relation, extra in (
        ("equivalence", {}),
        ("artifact_identity", {}),
        ("org", {}),
    ):
        edge = {"confidence": 1.0, "method": "name_match", **extra}
        assert emits(edge, relation) is False, relation


def test_non_scoring_membership_emits_above_its_threshold():
    edge = {"artifact_kind": "pypi", "artifact_id": "foo", "product_slug": "foo",
            "confidence": 0.95, "method": "backlink", "scoring_bearing": False}
    assert emits(edge, "membership") is True


def test_non_scoring_membership_does_not_emit_below_its_threshold():
    edge = {"artifact_kind": "pypi", "artifact_id": "foo", "product_slug": "foo",
            "confidence": 0.5, "method": "backlink", "scoring_bearing": False}
    assert emits(edge, "membership") is False


def test_membership_split_into_scoring_and_non_scoring_relations():
    edges = {
        "membership": [
            {"artifact_kind": "pypi", "artifact_id": "elasticsearch", "product_slug": "elasticsearch",
             "confidence": 0.99, "method": "backlink", "scoring_bearing": True},
            {"artifact_kind": "github", "artifact_id": "elastic/elasticsearch", "product_slug": "elasticsearch",
             "confidence": 0.99, "method": "backlink", "scoring_bearing": False},
        ]
    }
    truth = Truth(membership={
        (("pypi", "elasticsearch"), "elasticsearch"): True,
        (("github", "elastic/elasticsearch"), "elasticsearch"): True,
    })
    m = replay(edges, truth)
    assert "membership_scoring" in m and "membership_non_scoring" in m
    # Scoring-bearing can never pass `emits`, so nothing is emitted for it, regardless of
    # how many scoring-bearing truths exist.
    assert m["membership_scoring"].n_emitted_at_threshold == 0
    assert m["membership_non_scoring"].n_emitted_at_threshold == 1
    assert m["membership_non_scoring"].precision == 1.0


def test_known_negative_caught_by_membership_truth():
    """A KNOWN_NEGATIVES entry, if it somehow emitted, would score as a false positive --
    the mechanism `KNOWN_NEGATIVES` exists to catch. (It cannot actually emit here because
    `method` is absent from these edges only by omission in this test; the real protection
    against it emitting via a real signal is `emits`, tested above.)"""
    neg = KNOWN_NEGATIVES[0]
    truth = load_truth()
    key = (neg["kind"], neg["artifact_id"])
    assert truth.membership.get((key, neg["product_slug"])) is False


def test_load_truth_has_no_known_negative_declared_as_a_real_artifact():
    """Every `KNOWN_NEGATIVES` package must genuinely be undeclared in
    `sources/products/<slug>.yaml` -- if a future edit declared one, the negative would be
    lying about the repo's own state."""
    truth = load_truth()
    for neg in KNOWN_NEGATIVES:
        key = (neg["kind"], neg["artifact_id"])
        assert truth.membership.get((key, neg["product_slug"])) is False, neg


def test_floor_failures_flags_relation_under_floor():
    truth = Truth(equivalence={("github", "a/b"): "p"})
    edges = {
        "equivalence": [
            {"artifact_kind": "github", "artifact_id": "a/b", "product_slug": "wrong", "confidence": 1.0},
        ]
    }
    metrics = replay(edges, truth)
    failures = floor_failures(metrics)
    assert any("equivalence" in f for f in failures)


def test_floor_failures_empty_when_every_relation_clears_its_floor():
    truth = Truth(equivalence={("github", "a/b"): "p"})
    edges = {
        "equivalence": [
            {"artifact_kind": "github", "artifact_id": "a/b", "product_slug": "p", "confidence": 1.0},
        ]
    }
    metrics = replay(edges, truth)
    assert floor_failures(metrics) == []


def test_membership_scoring_never_floored():
    """`membership_scoring` carries no entry in FLOORS, so it can never appear in
    `floor_failures` no matter how empty or wrong its metrics are -- unlike
    `membership_non_scoring`, which is floored and legitimately fails here on zero
    emissions against real truth."""
    edges = {
        "membership": [
            {"artifact_kind": "pypi", "artifact_id": "x", "product_slug": "y",
             "confidence": 1.0, "method": "backlink", "scoring_bearing": True},
        ]
    }
    metrics = replay(edges, load_truth())
    assert "membership_scoring" not in metrics or metrics["membership_scoring"].n_emitted_at_threshold == 0
    assert not any(f.startswith("membership_scoring") for f in floor_failures(metrics))


def test_zero_truth_relation_reports_rather_than_fails():
    """A relation with no truth to check against is not a floor failure -- there is
    nothing to have gotten wrong."""
    truth = Truth()
    edges = {"org": [{"candidate_key": "github:a/b", "org_slug": "acme", "confidence": 1.0}]}
    metrics = replay(edges, truth)
    assert metrics["org"].n_truth == 0
    assert floor_failures(metrics) == []
