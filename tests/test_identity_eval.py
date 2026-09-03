"""The replay eval, and the rules pinned as tests rather than metrics.

Fixtures only, except the ledger/truth-related tests, which exercise the pure functions
directly (`_equivalence_from_ledger`, `_membership_from_ledger`) rather than going through
`build.resolution.load()`, precisely so a scenario the CURRENT loader could not itself
produce without raising (two rulings against one artifact, two different products) can still
be tested here -- see `test_membership_truth_keeps_two_products_for_one_artifact_distinct`.

The `currentai.identity.*` dataset has not deployed, so nothing here touches the warehouse.
"""

from __future__ import annotations

import yaml

from build.identity_eval import (
    KNOWN_NEGATIVES,
    EdgeColumnMissing,
    KnownNegativeDeclaredError,
    Truth,
    _equivalence_from_ledger,
    _identity_dataset_deployed,
    _membership_from_ledger,
    candidate_key,
    digest_items,
    emits,
    emitted_at_threshold,
    floor_failures,
    floor_status,
    load_truth,
    main,
    replay,
    validate_columns,
)

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
    try:
        emits(edge, "membership_non_scoring")
        assert False, "expected ValueError"
    except ValueError:
        pass


# ---------------------------------------------------------------------------
# precision/recall math, dedup, recall clamp
# ---------------------------------------------------------------------------


def test_precision_recall_math():
    truth = Truth(equivalence={"github:a2aproject/a2a": "agent2agent-protocol"})
    edges = {
        "equivalence": [
            {"candidate_key": "github:a2aproject/a2a", "product_slug": "agent2agent-protocol",
             "confidence": 1.0, "method": ["resolution_ledger"]},
            {"candidate_key": "github:x/y", "product_slug": "wrong",
             "confidence": 1.0, "method": ["resolution_ledger"]},
        ]
    }
    m = replay(edges, truth)["equivalence"]
    assert m.precision == 0.5
    assert m.recall == 1.0
    assert m.n_truth == 1
    assert m.n_emitted_at_threshold == 2


def test_duplicate_head_tail_edges_collapse_in_precision_and_recall():
    """M7: two rows for one logical edge (a head/tail `product_tier` duplicate) must count
    once in both precision's denominator and recall's numerator, not inflate recall past 1.0."""
    truth = Truth(equivalence={"github:a/b": "p"})
    edges = {
        "equivalence": [
            {"candidate_key": "github:a/b", "product_tier": "head", "product_slug": "p",
             "confidence": 1.0, "method": ["resolution_ledger"]},
            {"candidate_key": "github:a/b", "product_tier": "tail", "product_slug": "p",
             "confidence": 1.0, "method": ["resolution_ledger"]},
        ]
    }
    m = replay(edges, truth)["equivalence"]
    assert m.n_emitted_at_threshold == 1
    assert m.precision == 1.0
    assert m.recall == 1.0


def test_recall_cannot_exceed_one():
    truth = Truth(org={"github:a/b": "acme"})
    edges = {
        "org": [
            {"candidate_key": "github:a/b", "org_slug": "acme", "confidence": 1.0, "method": ["org_handle"]},
        ]
    }
    m = replay(edges, truth)["org"]
    assert m.recall == 1.0


def test_wrong_target_counts_as_both_false_positive_and_miss():
    truth = Truth(equivalence={"github:a/b": "p"})
    edges = {"equivalence": [{"candidate_key": "github:a/b", "product_slug": "wrong",
                               "confidence": 1.0, "method": ["resolution_ledger"]}]}
    m = replay(edges, truth)["equivalence"]
    assert m.precision == 0.0
    assert m.recall == 0.0


def test_equivalence_negative_scored_as_false_positive_not_just_excluded():
    truth = Truth(equivalence_negatives={"github:a/b"})
    edges = {"equivalence": [{"candidate_key": "github:a/b", "product_slug": "anything",
                               "confidence": 1.0, "method": ["resolution_ledger"]}]}
    m = replay(edges, truth)["equivalence"]
    assert m.precision == 0.0


# ---------------------------------------------------------------------------
# candidate_key format
# ---------------------------------------------------------------------------


def test_candidate_key_is_kind_prefixed_and_folded():
    assert candidate_key("github", "Foo/Bar") == "github:foo/bar"
    assert candidate_key("pypi", "Scikit_Learn") == "pypi:scikit-learn"


def test_org_and_equivalence_truth_use_candidate_key_format():
    for ck in list(REAL_TRUTH.org)[:20]:
        kind, _, rest = ck.partition(":")
        assert rest, ck
    for ck in list(REAL_TRUTH.equivalence)[:20]:
        kind, _, rest = ck.partition(":")
        assert rest, ck


# ---------------------------------------------------------------------------
# membership: keyed on (kind, folded id, product_slug); two products, one artifact, distinct
# ---------------------------------------------------------------------------


def test_membership_truth_keeps_two_products_for_one_artifact_distinct():
    """Cannot be built through `build.resolution.load()` today -- its dict is keyed on
    `(artifact, relation)` alone, so two entries sharing that composite would raise
    `DuplicateResolution` before this function ever saw them. Feeding `_membership_from_ledger`
    a plain LIST (rather than a dict) proves the grouping logic itself is correct for the
    finer grain a parallel PR is expected to give the loader."""
    key = ("pypi", "x")
    entries = [
        ((key, "product_membership"), {"verdict": "member_of", "resolves_to": "product-a"}),
        ((key, "product_membership"), {"verdict": "not_member_of", "resolves_to": "product-b"}),
    ]
    truth = _membership_from_ledger(entries)
    assert truth[(key, "product-a")] is True
    assert truth[(key, "product-b")] is False


def test_membership_key_includes_product_slug():
    key = ("github", "a/b")
    entries = [((key, "product_membership"), {"verdict": "member_of", "resolves_to": "p"})]
    truth = _membership_from_ledger(entries)
    assert truth == {(key, "p"): True}


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
         "confidence": 1.0, "method": ["fold_collapse"]},
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
    try:
        load_truth(known_negatives=bad)
        assert False, "expected KnownNegativeDeclaredError"
    except KnownNegativeDeclaredError:
        pass


def test_known_negatives_are_all_undeclared_in_truth():
    for neg in KNOWN_NEGATIVES:
        key = (neg["kind"], neg["artifact_id"])
        assert REAL_TRUTH.membership.get((key, neg["product_slug"])) is False, neg


# ---------------------------------------------------------------------------
# floors: insufficient truth, no floor, checked
# ---------------------------------------------------------------------------


def test_floor_status_insufficient_truth_below_min():
    truth = Truth(equivalence={f"github:{i}/x": "p" for i in range(5)})
    edges = {"equivalence": [
        {"candidate_key": f"github:{i}/x", "product_slug": "p", "confidence": 1.0, "method": ["resolution_ledger"]}
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
    truth = Truth(org={f"github:{i}/x": "acme" for i in range(30)})
    edges = {"org": [
        {"candidate_key": f"github:{i}/x", "org_slug": "wrong", "confidence": 1.0, "method": ["org_handle"]}
        for i in range(30)
    ]}
    metrics = replay(edges, truth)
    assert floor_status("org", metrics) == "checked (FAIL)"
    assert any("org" in f for f in floor_failures(metrics))


def test_floor_status_checked_and_passing():
    truth = Truth(org={f"github:{i}/x": "acme" for i in range(30)})
    edges = {"org": [
        {"candidate_key": f"github:{i}/x", "org_slug": "acme", "confidence": 1.0, "method": ["org_handle"]}
        for i in range(30)
    ]}
    metrics = replay(edges, truth)
    assert floor_status("org", metrics) == "checked (pass)"
    assert floor_failures(metrics) == []


# ---------------------------------------------------------------------------
# column validation: exit-2-worthy, not a KeyError
# ---------------------------------------------------------------------------


def test_validate_columns_raises_on_missing_required_column():
    edges = {"equivalence": [{"product_slug": "p", "confidence": 1.0}]}  # no candidate_key
    try:
        validate_columns(edges)
        assert False, "expected EdgeColumnMissing"
    except EdgeColumnMissing as exc:
        assert exc.relation == "equivalence"
        assert exc.column == "candidate_key"


def test_validate_columns_raises_on_null_value_not_just_absent_key():
    edges = {"org": [{"candidate_key": "github:a/b", "org_slug": None, "confidence": 1.0}]}
    try:
        validate_columns(edges)
        assert False, "expected EdgeColumnMissing"
    except EdgeColumnMissing as exc:
        assert exc.column == "org_slug"


def test_validate_columns_passes_on_a_row_shaped_exactly_like_each_sql():
    """Fixture rows shaped exactly like `WAREHOUSE_COLUMNS` for each relation -- the review's
    M2/M3 asked for a fixture in the real column shape; this is that fixture, run through
    `validate_columns` and `replay` end to end without a crash."""
    edges = {
        "artifact_identity": [
            {"artifact_kind": "github", "artifact_id_a": "a/b", "artifact_id_b": "a/c",
             "confidence": 0.9, "method": ["github_redirect"], "penalties": 0},
        ],
        "membership": [
            {"artifact_kind": "pypi", "artifact_id": "foo", "product_tier": "head",
             "product_slug": "foo", "confidence": 1.0, "method": ["declared"], "penalties": 0,
             "scoring_bearing": True},
        ],
        "equivalence": [
            {"artifact_kind": "github", "candidate_key": "github:a/b", "product_tier": "head",
             "product_slug": "p", "confidence": 1.0, "method": ["resolution_ledger"], "penalties": 0},
        ],
        "org": [
            {"artifact_kind": "github", "candidate_key": "github:a/b", "org_slug": "acme",
             "confidence": 0.85, "method": ["org_handle"], "penalties": 0},
        ],
    }
    validate_columns(edges)  # must not raise
    replay(edges, REAL_TRUTH)  # must not raise


# ---------------------------------------------------------------------------
# --allow-unprovisioned
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
    import build.identity_eval as identity_eval_module

    monkeypatch.setattr(identity_eval_module, "ASSETS_PATH", p)
    rc = main(["--from-warehouse", "--allow-unprovisioned"])
    assert rc == 2


def test_main_rejects_allow_unprovisioned_without_from_warehouse(tmp_path):
    fixture = tmp_path / "edges.json"
    fixture.write_text("{}")
    rc = main(["--edges", str(fixture), "--allow-unprovisioned"])
    assert rc == 2
