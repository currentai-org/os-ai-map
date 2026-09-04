"""The replay eval, and the rules pinned as tests rather than metrics.

Fixtures only, except the ledger/truth-related tests, which exercise the pure functions
directly (`_equivalence_from_ledger`, `_membership_from_ledger`) rather than going through
`build.resolution.load()`, precisely so a scenario the CURRENT loader could not itself
produce without raising (two rulings against one artifact, two different products) can still
be tested here -- see `test_membership_truth_keeps_two_products_for_one_artifact_distinct`.

All seven `currentai.identity.*` models are deployed, but nothing here touches the warehouse;
the F2 tests stub `build.warehouse.query` directly rather than hitting a real endpoint.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

import build.identity_eval as identity_eval_module
import build.warehouse as warehouse_module
from build.identity_eval import (
    KNOWN_NEGATIVES,
    EdgeColumnMissing,
    EdgeValueInvalid,
    KnownNegativeDeclaredError,
    Truth,
    WarehouseQueryFailed,
    WarehouseTableMissing,
    _equivalence_from_ledger,
    _identity_dataset_contracted,
    _identity_dataset_deployed,
    _is_table_not_found,
    _membership_from_ledger,
    candidate_key,
    digest_items,
    emits,
    emitted_at_threshold,
    floor_failures,
    floor_status,
    load_edges_from_warehouse,
    load_truth,
    main,
    org_handle_coverage,
    replay,
    validate_columns,
)

ROOT = Path(__file__).resolve().parent.parent
REAL_TRUTH = load_truth()


# ---------------------------------------------------------------------------
# method: array-typed, fail-closed, name-match-only never emits
# ---------------------------------------------------------------------------


def test_name_match_never_auto_emits_array_method():
    """The deployed shape: `method` is `ARRAY(VARCHAR)`, not a bare string."""
    edges = {
        "membership": [
            {"artifact_kind": "pypi", "artifact_id": "foo", "product_slug": "foo",
             "confidence": 0.99, "method": ["name_match"], "scoring_bearing": False}
        ]
    }
    assert emitted_at_threshold(edges)["membership"] == []
    assert digest_items(edges)[0]["artifact_id"] == "foo"


def test_name_match_never_auto_emits_bare_string_method():
    """Still accepted for fixture convenience, and still suppressed."""
    edge = {"confidence": 1.0, "method": "name_match"}
    assert emits(edge, "equivalence") is False


def test_missing_method_never_emits_fail_closed():
    edge = {"artifact_kind": "github", "artifact_id": "a/b", "confidence": 1.0}
    assert emits(edge, "artifact_identity") is False


def test_empty_method_array_never_emits():
    edge = {"confidence": 1.0, "method": []}
    assert emits(edge, "org") is False


def test_method_with_name_match_plus_another_emits_if_confidence_clears():
    """A compound method array -- `['declared', 'name_match']` -- has an element other than
    `name_match`, so it is not suppressed by the name-match rule; ordinary confidence gating
    still applies."""
    edge = {"artifact_kind": "pypi", "artifact_id": "x", "product_slug": "y",
            "confidence": 0.95, "method": ["declared", "name_match"], "scoring_bearing": False}
    assert emits(edge, "membership") is True


def test_name_match_never_emits_regardless_of_confidence_on_any_relation():
    for relation in ("equivalence", "artifact_identity", "org"):
        edge = {"confidence": 1.0, "method": ["name_match"]}
        assert emits(edge, relation) is False, relation


# ---------------------------------------------------------------------------
# scoring_bearing: unconditional, string-safe, cannot be bypassed by relation name
# ---------------------------------------------------------------------------


def test_scoring_bearing_never_auto_emits_even_at_confidence_one():
    edge = {"artifact_kind": "pypi", "artifact_id": "elasticsearch", "product_slug": "elasticsearch",
            "confidence": 1.0, "method": ["declared"], "scoring_bearing": True}
    assert emits(edge, "membership") is False


def test_scoring_bearing_string_true_counts_as_bearing():
    edge = {"artifact_kind": "pypi", "artifact_id": "x", "product_slug": "y",
            "confidence": 1.0, "method": ["declared"], "scoring_bearing": "true"}
    assert emits(edge, "membership") is False


def test_scoring_bearing_string_false_does_not_count_as_bearing():
    edge = {"artifact_kind": "pypi", "artifact_id": "x", "product_slug": "y",
            "confidence": 1.0, "method": ["declared"], "scoring_bearing": "false"}
    assert emits(edge, "membership") is True


def test_emits_rejects_a_metric_name_instead_of_an_edge_table_name():
    """The M6 fix: `emits` used to accept `membership_non_scoring` (a metric name printed in
    its own output table) and silently skip the scoring_bearing check for it. Now it raises."""
    edge = {"artifact_kind": "pypi", "artifact_id": "x", "product_slug": "y",
            "confidence": 1.0, "method": ["declared"], "scoring_bearing": True}
    with pytest.raises(ValueError):
        emits(edge, "membership_non_scoring")


# ---------------------------------------------------------------------------
# F3: an unrecognized relation name raises, in both validate_columns and replay
# ---------------------------------------------------------------------------


def test_validate_columns_raises_on_unknown_relation_name():
    with pytest.raises(ValueError):
        validate_columns({"orgs": []})  # typo for "org"


def test_replay_raises_on_unknown_relation_name():
    with pytest.raises(ValueError):
        replay({"orgs": []}, REAL_TRUTH)


def test_emitted_at_threshold_raises_on_unknown_relation_name_via_emits():
    with pytest.raises(ValueError):
        emitted_at_threshold({"orgs": [{"confidence": 1.0, "method": ["x"]}]})


# ---------------------------------------------------------------------------
# F1: the declared/pool tier split -- precision/recall over head/tail, n_emitted over pool
# ---------------------------------------------------------------------------


def test_precision_recall_computed_over_declared_tier_only():
    """A `pool`-tier edge, even a perfectly correct-looking one, must not count toward
    precision or recall -- truth is built from declared (head/tail) artifacts only, so a pool
    edge is out of population by construction (F1)."""
    truth = Truth(equivalence={"github:a/b": "p"})
    edges = {"equivalence": [
        {"candidate_key": "github:a/b", "candidate_tier": "pool", "product_slug": "p",
         "confidence": 1.0, "method": ["resolution_ledger"]},
    ]}
    m = replay(edges, truth)["equivalence"]
    assert m.precision is None
    assert m.recall == 0.0


def test_n_emitted_at_threshold_computed_over_pool_tier_only():
    """A `head`-tier edge, however many of them pass `emits`, must not inflate
    `n_emitted_at_threshold` -- that field answers "how many NEW things would launch",
    and a declared artifact has nothing to discover (F1)."""
    truth = Truth(equivalence={"github:a/b": "p"})
    edges = {"equivalence": [
        {"candidate_key": "github:a/b", "candidate_tier": "head", "product_slug": "p",
         "confidence": 1.0, "method": ["resolution_ledger"]},
        {"candidate_key": "github:c/d", "candidate_tier": "pool", "product_slug": "q",
         "confidence": 1.0, "method": ["resolution_ledger"]},
    ]}
    m = replay(edges, truth)["equivalence"]
    assert m.precision == 1.0  # the one declared edge, correct
    assert m.n_emitted_at_threshold == 1  # the one pool edge, regardless of correctness


def test_digest_items_excludes_declared_tier_and_includes_pool_tier():
    edges = {"equivalence": [
        {"candidate_key": "github:a/b", "candidate_tier": "head", "product_slug": "p",
         "confidence": 0.1, "method": ["model_family"]},  # below threshold, declared -> not a digest item
        {"candidate_key": "github:c/d", "candidate_tier": "pool", "product_slug": "q",
         "confidence": 0.1, "method": ["model_family"]},  # below threshold, pool -> a digest item
    ]}
    items = digest_items(edges)
    assert len(items) == 1
    assert items[0]["candidate_key"] == "github:c/d"


def test_membership_unaffected_by_tier_split_no_candidate_tier_column():
    """membership's SQL is declared-only already, so it has no candidate_tier and both
    precision/recall AND n_emitted_at_threshold draw from the same emitted set, unlike the
    three tiered relations."""
    truth = Truth(membership={(("pypi", "x"), "p"): True})
    edges = {"membership": [
        {"artifact_kind": "pypi", "artifact_id": "x", "product_slug": "p",
         "confidence": 1.0, "method": ["declared"], "scoring_bearing": False},
    ]}
    m = replay(edges, truth)["membership_non_scoring"]
    assert m.precision == 1.0
    assert m.n_emitted_at_threshold == 1


# ---------------------------------------------------------------------------
# precision/recall math, dedup, recall clamp (declared-tier edges throughout)
# ---------------------------------------------------------------------------


def test_precision_recall_math():
    truth = Truth(equivalence={"github:a2aproject/a2a": "agent2agent-protocol"})
    edges = {
        "equivalence": [
            {"candidate_key": "github:a2aproject/a2a", "candidate_tier": "head",
             "product_slug": "agent2agent-protocol", "confidence": 1.0, "method": ["resolution_ledger"]},
            {"candidate_key": "github:x/y", "candidate_tier": "head", "product_slug": "wrong",
             "confidence": 1.0, "method": ["resolution_ledger"]},
        ]
    }
    m = replay(edges, truth)["equivalence"]
    assert m.precision == 0.5
    assert m.recall == 1.0
    assert m.n_truth == 1


def test_duplicate_head_tail_edges_collapse_in_precision_and_recall():
    """M7: two rows for one logical edge (a head/tail `product_tier` duplicate) must count
    once in both precision's denominator and recall's numerator, not inflate recall past 1.0."""
    truth = Truth(equivalence={"github:a/b": "p"})
    edges = {
        "equivalence": [
            {"candidate_key": "github:a/b", "candidate_tier": "head", "product_tier": "head",
             "product_slug": "p", "confidence": 1.0, "method": ["resolution_ledger"]},
            {"candidate_key": "github:a/b", "candidate_tier": "head", "product_tier": "tail",
             "product_slug": "p", "confidence": 1.0, "method": ["resolution_ledger"]},
        ]
    }
    m = replay(edges, truth)["equivalence"]
    assert m.precision == 1.0
    assert m.recall == 1.0


def test_recall_cannot_exceed_one():
    truth = Truth(org={"github:a/b": {"acme"}}, recoverable_orgs=frozenset({"acme"}))
    edges = {
        "org": [
            {"candidate_key": "github:a/b", "candidate_tier": "head", "org_slug": "acme",
             "confidence": 1.0, "method": ["org_handle"]},
        ]
    }
    m = replay(edges, truth)["org"]
    assert m.recall == 1.0


def test_wrong_target_counts_as_both_false_positive_and_miss():
    truth = Truth(equivalence={"github:a/b": "p"})
    edges = {"equivalence": [{"candidate_key": "github:a/b", "candidate_tier": "head",
                               "product_slug": "wrong", "confidence": 1.0, "method": ["resolution_ledger"]}]}
    m = replay(edges, truth)["equivalence"]
    assert m.precision == 0.0
    assert m.recall == 0.0


def test_equivalence_negative_scored_as_false_positive_not_just_excluded():
    truth = Truth(equivalence_negatives={"github:a/b"})
    edges = {"equivalence": [{"candidate_key": "github:a/b", "candidate_tier": "head",
                               "product_slug": "anything", "confidence": 1.0, "method": ["resolution_ledger"]}]}
    m = replay(edges, truth)["equivalence"]
    assert m.precision == 0.0


# ---------------------------------------------------------------------------
# F5: org truth is a SET of orgs per candidate key
# ---------------------------------------------------------------------------


def test_org_truth_holds_more_than_one_org_per_candidate_key_in_the_real_corpus():
    multi = {ck: orgs for ck, orgs in REAL_TRUTH.org.items() if len(orgs) > 1}
    assert "github:swe-bench/swe-bench" in multi
    assert multi["github:swe-bench/swe-bench"] == {"princeton-nlp", "princeton-nlp-openai"}


def test_second_org_for_a_shared_candidate_key_scores_correct_not_a_false_positive():
    """The F5 bug: `dict.setdefault` kept only the first org read and scored the second,
    equally correct org as a false positive. Both must score correct now."""
    truth = Truth(org={"github:a/b": {"org-one", "org-two"}}, recoverable_orgs=frozenset({"org-one", "org-two"}))
    edges = {"org": [
        {"candidate_key": "github:a/b", "candidate_tier": "head", "org_slug": "org-one",
         "confidence": 1.0, "method": ["org_handle"]},
        {"candidate_key": "github:a/b", "candidate_tier": "head", "org_slug": "org-two",
         "confidence": 1.0, "method": ["org_handle"]},
    ]}
    m = replay(edges, truth)["org"]
    assert m.precision == 1.0
    assert m.n_truth == 2  # two distinct (candidate_key, org_slug) pairs
    assert m.recall == 1.0


def test_org_n_truth_counts_pairs_not_candidate_keys():
    assert sum(len(orgs) for orgs in REAL_TRUTH.org.values()) > len(REAL_TRUTH.org)


# ---------------------------------------------------------------------------
# org recall is measured against recoverable truth (an org must declare a handle)
# ---------------------------------------------------------------------------


def test_org_without_a_handle_drops_out_of_recall_truth():
    """An org with no declared handle can never be recovered by the graph, so it must not
    inflate `org`'s recall denominator -- `n_truth` counts only pairs whose org is
    recoverable."""
    truth = Truth(
        org={"github:a/b": {"has-handle"}, "github:c/d": {"no-handle"}},
        recoverable_orgs=frozenset({"has-handle"}),
        orgs_rostered=frozenset({"has-handle", "no-handle"}),
    )
    m = replay({"org": []}, truth)["org"]
    assert m.n_truth == 1
    assert m.n_truth_unrecoverable == 1


def test_emitted_edge_to_a_handle_less_org_still_counts_toward_precision():
    """Precision truth is unchanged: an edge correctly naming an org with no declared handle
    is still a correct edge, and must not be scored as a false positive just because that org
    cannot contribute to recall."""
    truth = Truth(
        org={"github:a/b": {"no-handle"}},
        recoverable_orgs=frozenset(),
        orgs_rostered=frozenset({"no-handle"}),
    )
    edges = {"org": [
        {"candidate_key": "github:a/b", "candidate_tier": "head", "org_slug": "no-handle",
         "confidence": 1.0, "method": ["org_handle"]},
    ]}
    m = replay(edges, truth)["org"]
    assert m.precision == 1.0  # still counted correct for precision
    assert m.n_truth == 0  # but excluded from the recall denominator
    assert m.recall is None  # no recoverable truth at all -- nothing to have recalled
    assert m.n_truth_unrecoverable == 1


def test_handle_coverage_computed_correctly_on_a_fixture():
    truth = Truth(
        recoverable_orgs=frozenset({"a", "b"}),
        orgs_rostered=frozenset({"a", "b", "c", "d"}),
    )
    assert org_handle_coverage(truth) == (2, 4)


def test_org_handle_coverage_against_the_real_corpus_matches_recoverable_orgs():
    n_with_handle, n_rostered = org_handle_coverage(REAL_TRUTH)
    assert n_with_handle == len(REAL_TRUTH.recoverable_orgs)
    assert n_rostered == len(REAL_TRUTH.orgs_rostered)
    assert 0 < n_with_handle <= n_rostered


def test_non_org_relations_carry_zero_n_truth_unrecoverable():
    truth = Truth(equivalence={"github:a/b": "p"})
    edges = {"equivalence": [{"candidate_key": "github:a/b", "candidate_tier": "head",
                              "product_slug": "p", "confidence": 1.0, "method": ["m"]}]}
    m = replay(edges, truth)["equivalence"]
    assert m.n_truth_unrecoverable == 0


# ---------------------------------------------------------------------------
# candidate_key format
# ---------------------------------------------------------------------------


def test_candidate_key_is_kind_prefixed_and_folded():
    assert candidate_key("github", "Foo/Bar") == "github:foo/bar"
    assert candidate_key("pypi", "Scikit_Learn") == "pypi:scikit-learn"


def test_org_and_equivalence_truth_use_candidate_key_format():
    for ck in list(REAL_TRUTH.org)[:20]:
        _kind, _, rest = ck.partition(":")
        assert rest, ck
    for ck in list(REAL_TRUTH.equivalence)[:20]:
        _kind, _, rest = ck.partition(":")
        assert rest, ck


# ---------------------------------------------------------------------------
# membership: keyed on (kind, folded id, product_slug); two products, one artifact, distinct
# ---------------------------------------------------------------------------


def test_membership_truth_keeps_two_products_for_one_artifact_distinct():
    """`_membership_from_ledger` takes raw ledger ENTRY dicts (e.g.
    `resolution.load().values()`), not the loader's dict-key identity -- #478 widened
    `build.resolution.load()`'s own key to `(artifact, relation, resolves_to)` for
    `product_membership`, so its dict can now legitimately hold both a `member_of` and a
    `not_member_of` ruling for the same artifact against two different products. This
    function groups on `(resolution.artifact_of(entry), resolves_to)` itself, independent of
    whatever the loader's key shape is or becomes next."""
    entries = [
        {"artifact": {"kind": "pypi", "id": "x"}, "relation": "product_membership",
         "verdict": "member_of", "resolves_to": "product-a"},
        {"artifact": {"kind": "pypi", "id": "x"}, "relation": "product_membership",
         "verdict": "not_member_of", "resolves_to": "product-b"},
    ]
    truth = _membership_from_ledger(entries)
    key = ("pypi", "x")
    assert truth[(key, "product-a")] is True
    assert truth[(key, "product-b")] is False


def test_membership_key_includes_product_slug():
    entries = [{"artifact": {"kind": "github", "id": "a/b"}, "relation": "product_membership",
                "verdict": "member_of", "resolves_to": "p"}]
    truth = _membership_from_ledger(entries)
    assert truth == {(("github", "a/b"), "p"): True}


def test_membership_truth_via_the_real_loader_now_that_478_landed(tmp_path):
    """End-to-end through `build.resolution.load()` itself, on a temp ledger file -- proves
    the loader's own widened key (#478) and this module's consumption of it agree, not just
    the pure function in isolation."""
    from build import resolution as _resolution

    ledger_doc = {
        "resolutions": [
            {"artifact": {"kind": "pypi", "id": "y"}, "relation": "product_membership",
             "verdict": "member_of", "resolves_to": "product-a", "decided_in": "#test",
             "decided_on": "2026-09-04", "note": "test fixture, not a real ruling"},
            {"artifact": {"kind": "pypi", "id": "y"}, "relation": "product_membership",
             "verdict": "not_member_of", "resolves_to": "product-b", "decided_in": "#test",
             "decided_on": "2026-09-04", "note": "test fixture, not a real ruling"},
        ]
    }
    ledger_path = tmp_path / "resolution_ledger.yaml"
    ledger_path.write_text(yaml.dump(ledger_doc))
    ledger = _resolution.load(ledger_path)

    truth = _membership_from_ledger(ledger.values())
    key = ("pypi", "y")
    assert truth[(key, "product-a")] is True
    assert truth[(key, "product-b")] is False


# ---------------------------------------------------------------------------
# membership_scoring / membership_non_scoring split, and the M8 fix
# ---------------------------------------------------------------------------


def test_membership_split_by_route_kinds_not_by_edge_scoring_bearing():
    truth = Truth(
        membership={(("pypi", "x"), "p"): True, (("homepage", "y"), "q"): True},
        route_kinds=frozenset({"pypi"}),
    )
    edges = {
        "membership": [
            {"artifact_kind": "homepage", "artifact_id": "y", "product_slug": "q",
             "confidence": 0.95, "method": ["declared"], "scoring_bearing": False},
        ]
    }
    m = replay(edges, truth)
    assert m["membership_non_scoring"].n_truth == 1  # only the homepage (non-route) truth item
    assert m["membership_non_scoring"].n_emitted_at_threshold == 1
    assert m["membership_non_scoring"].precision == 1.0
    assert m["membership_scoring"].n_truth == 1  # only the pypi (routed) truth item
    assert m["membership_scoring"].n_emitted_at_threshold == 0  # nothing scoring-bearing can ever emit


def test_membership_non_scoring_truth_is_zero_against_the_real_corpus():
    """Every declared kind in today's corpus has an adoption route, so
    `membership_non_scoring`'s truth is 0 -- `floor_status` must report "insufficient truth",
    not attempt an unsatisfiable floor (the review's M8)."""
    assert sum(
        1 for (key, _slug), is_member in REAL_TRUTH.membership.items()
        if is_member and key[0] not in REAL_TRUTH.route_kinds
    ) == 0


# ---------------------------------------------------------------------------
# artifact_identity: unordered folded pair, empty in the corpus today
# ---------------------------------------------------------------------------


def test_artifact_identity_truth_is_empty_today():
    assert REAL_TRUTH.identity_pairs == set()


def test_artifact_identity_pair_scoring_folds_both_sides():
    truth = Truth(identity_pairs={("github", "a/b", "a/b")})
    edges = {"artifact_identity": [
        {"artifact_kind": "github", "artifact_id_a": "A/B", "artifact_id_b": "a/b",
         "candidate_tier": "head", "confidence": 1.0, "method": ["fold_collapse"]},
    ]}
    m = replay(edges, truth)["artifact_identity"]
    assert m.precision == 1.0
    assert m.recall == 1.0


# ---------------------------------------------------------------------------
# KNOWN_NEGATIVES: no longer wrong, and the guard test now actually catches a wrong one
# ---------------------------------------------------------------------------


def test_known_negatives_no_longer_includes_declared_artifacts():
    """load_truth() over the real corpus must not raise -- this is the load-bearing assertion;
    a failure here means a KNOWN_NEGATIVES entry is factually wrong again."""
    load_truth()  # would raise KnownNegativeDeclaredError if any entry were declared


def test_known_negative_declared_as_real_artifact_raises():
    """The exact historical bug: pymilvus really is declared under milvus
    (`sources/products/milvus.yaml`, with an explicit `artifact_exceptions.pypi_repo_mismatch`),
    so a KNOWN_NEGATIVES entry claiming otherwise must raise, not silently overwrite the truth."""
    bad = ({"kind": "pypi", "artifact_id": "pymilvus", "product_slug": "milvus"},)
    with pytest.raises(KnownNegativeDeclaredError):
        load_truth(known_negatives=bad)


# `test_known_negatives_are_all_undeclared_in_truth` (round-1 M9 partial fix) is dropped: it
# asserted `truth.membership[(key, slug)] is False`, a value `load_truth` writes
# unconditionally for every KNOWN_NEGATIVES entry regardless of whether the entry is actually
# correct -- a tautology, not a check. `test_known_negatives_no_longer_includes_declared_artifacts`
# and `test_known_negative_declared_as_real_artifact_raises` are the real guard (F4).


# ---------------------------------------------------------------------------
# floors: insufficient truth, no floor, checked
# ---------------------------------------------------------------------------


def test_floor_status_insufficient_truth_below_min():
    truth = Truth(equivalence={f"github:{i}/x": "p" for i in range(5)})
    edges = {"equivalence": [
        {"candidate_key": f"github:{i}/x", "candidate_tier": "head", "product_slug": "p",
         "confidence": 1.0, "method": ["resolution_ledger"]}
        for i in range(5)
    ]}
    metrics = replay(edges, truth)
    assert floor_status("equivalence", metrics).startswith("insufficient truth")
    assert floor_failures(metrics) == []


def test_floor_status_no_floor_for_membership_scoring():
    metrics = replay({"membership": []}, REAL_TRUTH)
    assert floor_status("membership_scoring", metrics) == "no floor (never automated)"


def test_floor_status_not_evaluated_when_relation_absent():
    metrics = replay({}, REAL_TRUTH)
    assert floor_status("org", metrics) == "not evaluated (edge table absent from input)"


def test_floor_status_checked_and_failing():
    truth = Truth(org={f"github:{i}/x": {"acme"} for i in range(30)}, recoverable_orgs=frozenset({"acme"}))
    edges = {"org": [
        {"candidate_key": f"github:{i}/x", "candidate_tier": "head", "org_slug": "wrong",
         "confidence": 1.0, "method": ["org_handle"]}
        for i in range(30)
    ]}
    metrics = replay(edges, truth)
    assert floor_status("org", metrics) == "checked (FAIL)"
    assert any("org" in f for f in floor_failures(metrics))


def test_floor_status_checked_and_passing():
    truth = Truth(org={f"github:{i}/x": {"acme"} for i in range(30)}, recoverable_orgs=frozenset({"acme"}))
    edges = {"org": [
        {"candidate_key": f"github:{i}/x", "candidate_tier": "head", "org_slug": "acme",
         "confidence": 1.0, "method": ["org_handle"]}
        for i in range(30)
    ]}
    metrics = replay(edges, truth)
    assert floor_status("org", metrics) == "checked (pass)"
    assert floor_failures(metrics) == []


def test_floor_status_abstains_on_precision_when_nothing_emitted():
    """SF2: `precision is None` (the declared slice emitted nothing at all) must not read as
    0.0 and fail a precision floor for a reason that is not a precision problem -- only
    recall's real 0.0 should fail here."""
    truth = Truth(org={f"github:{i}/x": {"acme"} for i in range(30)}, recoverable_orgs=frozenset({"acme"}))
    edges = {"org": []}  # nothing emitted at all
    metrics = replay(edges, truth)
    assert metrics["org"].precision is None
    assert metrics["org"].recall == 0.0
    assert floor_status("org", metrics) == "checked (FAIL)"  # recall 0.0 still fails
    failures = floor_failures(metrics)
    assert not any("precision" in f for f in failures)
    assert any("recall" in f for f in failures)


def test_floor_status_passes_when_precision_abstains_and_recall_clears():
    """Constructed `Metrics` directly: `precision is None` with `recall` clearing its floor
    must read as a pass -- the abstention logic must not force a FAIL just because precision
    has nothing to say."""
    metrics = {"org": identity_eval_module.Metrics(precision=None, recall=1.0, n_truth=30, n_emitted_at_threshold=0)}
    assert floor_status("org", metrics) == "checked (pass)"
    assert floor_failures(metrics) == []


# ---------------------------------------------------------------------------
# column validation: exit-2-worthy, not a KeyError
# ---------------------------------------------------------------------------


def test_validate_columns_raises_on_missing_required_column():
    edges = {"equivalence": [{"product_slug": "p", "confidence": 1.0}]}  # no candidate_key
    with pytest.raises(EdgeColumnMissing) as exc_info:
        validate_columns(edges)
    assert exc_info.value.relation == "equivalence"
    assert exc_info.value.column == "candidate_key"


def test_validate_columns_raises_on_null_value_not_just_absent_key():
    edges = {"org": [{"candidate_key": "github:a/b", "org_slug": None, "confidence": 1.0}]}
    with pytest.raises(EdgeColumnMissing) as exc_info:
        validate_columns(edges)
    assert exc_info.value.column == "org_slug"


def test_validate_columns_raises_on_missing_candidate_tier():
    edges = {"org": [{"candidate_key": "github:a/b", "org_slug": "acme", "confidence": 1.0}]}
    with pytest.raises(EdgeColumnMissing) as exc_info:
        validate_columns(edges)
    assert exc_info.value.column == "candidate_tier"


def test_validate_columns_raises_on_unrecognized_candidate_tier_value():
    """SF1: a redeployed SQL that changes the tier vocabulary or its casing (`'Head'`, or a
    fourth tier) must not pass validation and then silently zero out a metric."""
    edges = {"org": [{"candidate_key": "github:a/b", "org_slug": "acme", "confidence": 1.0,
                      "candidate_tier": "Head"}]}
    with pytest.raises(EdgeValueInvalid) as exc_info:
        validate_columns(edges)
    assert exc_info.value.relation == "org"
    assert exc_info.value.column == "candidate_tier"
    assert exc_info.value.value == "Head"


def test_validate_columns_raises_on_unrecognized_product_tier_value():
    edges = {"equivalence": [{"candidate_key": "github:a/b", "product_slug": "p",
                               "candidate_tier": "head", "product_tier": "bogus"}]}
    with pytest.raises(EdgeValueInvalid) as exc_info:
        validate_columns(edges)
    assert exc_info.value.column == "product_tier"


def test_main_exits_2_on_unrecognized_tier_value(tmp_path):
    fixture = tmp_path / "edges.json"
    fixture.write_text(
        '{"org": [{"candidate_key": "github:a/b", "org_slug": "acme", "confidence": 1.0, '
        '"candidate_tier": "pooled"}]}'
    )
    rc = main(["--edges", str(fixture)])
    assert rc == 2


def test_validate_columns_passes_on_rows_shaped_exactly_like_each_sql():
    """F3: at least one head/tail (declared) row and one pool row per tiered relation, in the
    exact `WAREHOUSE_COLUMNS` shape -- this is the same fixture committed at
    `tests/fixtures/identity_edges_pass.json`, exercised here via `validate_columns` +
    `replay` end to end without a crash."""
    edges = {
        "artifact_identity": [
            {"artifact_kind": "github", "artifact_id_a": "a/b", "artifact_id_b": "a/c",
             "candidate_tier": "head", "confidence": 0.9, "method": ["github_redirect"], "penalties": []},
            {"artifact_kind": "github", "artifact_id_a": "x/y", "artifact_id_b": "x/z",
             "candidate_tier": "pool", "confidence": 0.9, "method": ["github_redirect"], "penalties": []},
        ],
        "membership": [
            {"artifact_kind": "pypi", "artifact_id": "foo", "product_tier": "head",
             "product_slug": "foo", "confidence": 1.0, "method": ["declared"], "penalties": [],
             "scoring_bearing": True},
            {"artifact_kind": "homepage", "artifact_id": "example.com", "product_tier": "tail",
             "product_slug": "bar", "confidence": 0.95, "method": ["declared"], "penalties": [],
             "scoring_bearing": False},
        ],
        "equivalence": [
            {"artifact_kind": "github", "candidate_key": "github:a/b", "candidate_tier": "head",
             "product_tier": "head", "product_slug": "p", "confidence": 1.0,
             "method": ["resolution_ledger"], "penalties": []},
            {"artifact_kind": "pypi", "candidate_key": "pypi:x", "candidate_tier": "pool",
             "product_tier": "tail", "product_slug": "q", "confidence": 0.8,
             "method": ["model_family"], "penalties": []},
        ],
        "org": [
            {"artifact_kind": "github", "candidate_key": "github:a/b", "candidate_tier": "head",
             "org_slug": "acme", "confidence": 0.85, "method": ["org_handle"], "penalties": []},
            {"artifact_kind": "github", "candidate_key": "github:x/y", "candidate_tier": "pool",
             "org_slug": "acme", "confidence": 0.85, "method": ["org_handle"], "penalties": []},
        ],
    }
    validate_columns(edges)  # must not raise
    metrics = replay(edges, REAL_TRUTH)  # must not raise
    # sanity: the pool rows must not have leaked into any declared-only scoring, and every
    # relation is present in the output.
    assert set(metrics) == {"artifact_identity", "membership_scoring", "membership_non_scoring", "equivalence", "org"}


# ---------------------------------------------------------------------------
# F2: --allow-unprovisioned swallows table-not-found only, never another exception class
# ---------------------------------------------------------------------------


# The REAL error text, verified live (2026-09-03) against currentai.identity.equivalence_edges
# and org_edges while both were undeployed: a 400/404 OsoHTTPError wrapping this Trino message.
# A round-1 marker list ("does not exist" singular, "table_not_found" underscored) missed this
# entirely -- it is plural and camel-case -- which is MF1. Pinned verbatim, not paraphrased, so
# a future edit to the marker list is checked against the actual production string.
REAL_TRINO_TABLE_NOT_FOUND = (
    "USER_ERROR: TablesNotFound - Tables do not exist or are inaccessible: "
    "currentai.identity.equivalence_edges"
)


def test_is_table_not_found_matches_the_real_trino_error_verbatim():
    assert _is_table_not_found(Exception(REAL_TRINO_TABLE_NOT_FOUND))


def test_is_table_not_found_matches_other_trino_wordings_too():
    assert _is_table_not_found(Exception("line 1:15: Table 'currentai.identity.org_edges' does not exist"))
    assert _is_table_not_found(Exception("TABLE_NOT_FOUND: no such table"))
    assert _is_table_not_found(Exception("Table not found: foo"))


def test_is_table_not_found_does_not_match_other_failures():
    assert not _is_table_not_found(Exception("401 Unauthorized"))
    assert not _is_table_not_found(Exception("Column 'artifact_kind' cannot be resolved"))
    assert not _is_table_not_found(Exception("Read timed out"))


def test_load_edges_from_warehouse_table_not_found_raises_typed(monkeypatch):
    def fake_query(sql):
        raise Exception(REAL_TRINO_TABLE_NOT_FOUND)

    monkeypatch.setattr(warehouse_module, "query", fake_query)
    with pytest.raises(WarehouseTableMissing) as exc_info:
        load_edges_from_warehouse()
    assert "artifact_identity_edges" in exc_info.value.table


def test_load_edges_from_warehouse_other_failure_raises_query_failed_not_missing(monkeypatch):
    def fake_query(sql):
        raise Exception("401 Unauthorized: invalid API key")

    monkeypatch.setattr(warehouse_module, "query", fake_query)
    with pytest.raises(WarehouseQueryFailed):
        load_edges_from_warehouse()


@pytest.fixture
def unrecorded_deploy(monkeypatch, tmp_path):
    """Point both provisioning records at empty files.

    The F2 tests below are about which EXCEPTION CLASS `--allow-unprovisioned` may swallow, not
    about the refusal. The committed tree now records the identity dataset as deployed (seven
    mirror-bound contracts), so the flag is refused before any query runs unless the fixture
    withdraws that record first.
    """
    assets = tmp_path / "assets.yaml"
    assets.write_text(yaml.dump({"assets": []}))
    deps = tmp_path / "dependencies.yaml"
    deps.write_text(yaml.dump({"dependencies": []}))
    monkeypatch.setattr(identity_eval_module, "ASSETS_PATH", assets)
    monkeypatch.setattr(identity_eval_module, "DEPENDENCIES_PATH", deps)


def test_main_allow_unprovisioned_exits_0_on_genuine_table_not_found(monkeypatch, unrecorded_deploy):
    def fake_query(sql):
        raise Exception(REAL_TRINO_TABLE_NOT_FOUND)

    monkeypatch.setattr(warehouse_module, "query", fake_query)
    rc = main(["--from-warehouse", "--allow-unprovisioned"])
    assert rc == 0


def test_main_allow_unprovisioned_still_exits_2_on_a_non_missing_table_failure(monkeypatch, unrecorded_deploy):
    """F2: the flag exists to cover exactly one signal. An auth failure, a timeout, or a
    missing column on a table that DOES exist must exit 2 even with the flag set -- otherwise
    a rotated API key or a broken deployed schema reports "skipped" and stays green forever."""
    def fake_query(sql):
        raise Exception("401 Unauthorized: invalid API key")

    monkeypatch.setattr(warehouse_module, "query", fake_query)
    rc = main(["--from-warehouse", "--allow-unprovisioned"])
    assert rc == 2


def test_main_without_allow_unprovisioned_exits_2_on_table_not_found_too(monkeypatch):
    def fake_query(sql):
        raise Exception("does not exist")

    monkeypatch.setattr(warehouse_module, "query", fake_query)
    rc = main(["--from-warehouse"])
    assert rc == 2


# ---------------------------------------------------------------------------
# --allow-unprovisioned: refused once the identity dataset is marked deployed
# ---------------------------------------------------------------------------


def test_identity_dataset_deployed_true_when_materialized(tmp_path):
    p = tmp_path / "assets.yaml"
    p.write_text(yaml.dump({"assets": [{"id": "identity.membership_edges", "materialized": True}]}))
    assert _identity_dataset_deployed(p) == ["identity.membership_edges"]


def test_identity_dataset_deployed_false_when_not_materialized(tmp_path):
    p = tmp_path / "assets.yaml"
    p.write_text(yaml.dump({"assets": [{"id": "identity.membership_edges", "materialized": False}]}))
    assert _identity_dataset_deployed(p) == []


def test_identity_dataset_deployed_ignores_non_identity_assets(tmp_path):
    p = tmp_path / "assets.yaml"
    p.write_text(yaml.dump({"assets": [{"id": "evaluation.adoption_reconciliation", "materialized": True}]}))
    assert _identity_dataset_deployed(p) == []


def test_main_rejects_allow_unprovisioned_when_dataset_deployed(tmp_path, monkeypatch):
    p = tmp_path / "assets.yaml"
    p.write_text(yaml.dump({"assets": [{"id": "identity.equivalence_edges", "materialized": True}]}))
    monkeypatch.setattr(identity_eval_module, "ASSETS_PATH", p)
    rc = main(["--from-warehouse", "--allow-unprovisioned"])
    assert rc == 2


def test_identity_dataset_contracted_reads_mirror_bound_contracts(tmp_path):
    p = tmp_path / "dependencies.yaml"
    p.write_text(yaml.dump({"dependencies": [
        {"table": "currentai.identity.digest", "mirror": {"revision": 4, "model_id": "x"}},
    ]}))
    assert _identity_dataset_contracted(p) == ["currentai.identity.digest"]


def test_identity_dataset_contracted_ignores_a_contract_with_no_mirror(tmp_path):
    p = tmp_path / "dependencies.yaml"
    p.write_text(yaml.dump({"dependencies": [{"table": "currentai.identity.digest"}]}))
    assert _identity_dataset_contracted(p) == []


def test_identity_dataset_contracted_ignores_non_identity_tables(tmp_path):
    p = tmp_path / "dependencies.yaml"
    p.write_text(yaml.dump({"dependencies": [
        {"table": "currentai.signal_hfhub.model_universe", "mirror": {"revision": 3}},
    ]}))
    assert _identity_dataset_contracted(p) == []


def test_main_rejects_allow_unprovisioned_when_the_dataset_is_contracted(tmp_path, monkeypatch):
    """A contract with a mirror block is the platform-owned equivalent of a materialized asset.

    identity.* tables are never governed assets under ADR-003, so `_identity_dataset_deployed`
    stays empty however deployed the dataset is -- the contract is the only record, and the
    refusal has to read it or the flag would outlive the deploy forever.
    """
    assets = tmp_path / "assets.yaml"
    assets.write_text(yaml.dump({"assets": []}))
    deps = tmp_path / "dependencies.yaml"
    deps.write_text(yaml.dump({"dependencies": [
        {"table": "currentai.identity.membership_edges", "mirror": {"revision": 2, "model_id": "x"}},
    ]}))
    monkeypatch.setattr(identity_eval_module, "ASSETS_PATH", assets)
    monkeypatch.setattr(identity_eval_module, "DEPENDENCIES_PATH", deps)
    rc = main(["--from-warehouse", "--allow-unprovisioned"])
    assert rc == 2


def test_the_committed_tree_refuses_allow_unprovisioned():
    """The real repo state, not a fixture: the dataset is contracted, so the flag is dead."""
    assert _identity_dataset_contracted() != []
    assert main(["--from-warehouse", "--allow-unprovisioned"]) == 2


def test_the_eval_workflow_does_not_pass_allow_unprovisioned():
    """The flag cannot come back while the contracts stand.

    `main` refuses it, so a workflow that still passed it would fail every scheduled run -- this
    catches that at review time instead, and pins the two facts together.
    """
    wf = (ROOT / ".github" / "workflows" / "identity-eval.yml").read_text()
    for line in wf.splitlines():
        if line.lstrip().startswith("#"):
            continue
        assert "--allow-unprovisioned" not in line, (
            "identity-eval.yml passes --allow-unprovisioned, but the identity dataset is "
            "contracted in warehouse/dependencies.yaml and build.identity_eval refuses the flag"
        )


def test_main_rejects_allow_unprovisioned_without_from_warehouse(tmp_path):
    fixture = tmp_path / "edges.json"
    fixture.write_text("{}")
    rc = main(["--edges", str(fixture), "--allow-unprovisioned"])
    assert rc == 2
