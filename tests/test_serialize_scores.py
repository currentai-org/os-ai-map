"""The fat table transcribes the payload; it does not recompute it.

`overall_score`, `maturity`, `mature` and `tier` are derived by `serialize._maturity_score`
against each category's weights. A second implementation of that blend — here, or in SQL —
is the repo/warehouse split `check_parity` exists to catch, one axis over. Openness had
exactly that shape and it published seven wrong scores.

So the contract these tests hold is equality with the payload, not plausibility.
"""

from __future__ import annotations

from build.serialize_scores import TABLES, build_scores

COLUMNS = TABLES["product_scores"]


def _payload(**products) -> dict:
    return {
        "categories": {
            "cat_a": {
                "products": [
                    {
                        "slug": "prod-one",
                        "type": "software",
                        "org_slug": "org-one",
                        "openness": {"score": "5", "class": "open_source", "bucket": "open",
                                     "components": "license:MIT(OSI)", "confidence": "high",
                                     "last_verified": "2026-08-01"},
                        "adoption": {"level": "4", "reach": "1M-10M",
                                     "signal_type": "usage_volume", "confidence": "high",
                                     "last_verified": "2026-08-02"},
                        "capability": {"score": "3", "basis": "feature_matrix",
                                       "value": "does the thing", "confidence": "medium",
                                       "last_verified": "2026-08-03"},
                        "overall_score": "3.5", "maturity": "3.5", "mature": "False",
                        "tier": "None",
                        "freshness": {"date": "2026-08-03", "basis": "verified"},
                        **products,
                    }
                ]
            }
        }
    }


def test_every_declared_column_is_emitted():
    rows = build_scores(_payload())["product_scores"]
    assert len(rows) == 1
    assert set(rows[0]) == set(COLUMNS)


def test_derived_numbers_are_transcribed_not_recomputed():
    """The payload's number wins, whatever it is.

    Deliberately feeds an overall_score that no blend of 4 and 3 would produce. If this
    module ever starts deriving instead of copying, this is the test that goes red.
    """
    rows = build_scores(_payload(overall_score="1.25", maturity="1.25", tier="Leading",
                                mature="True"))["product_scores"]
    assert rows[0]["overall_score"] == "1.25"
    assert rows[0]["maturity"] == "1.25"
    assert rows[0]["score_tier"] == "Leading"
    assert rows[0]["is_mature"] == "True"


def test_all_three_axes_travel_with_their_own_provenance():
    row = build_scores(_payload())["product_scores"][0]
    assert (row["openness_score"], row["openness_last_verified"]) == ("5", "2026-08-01")
    assert (row["adoption_level"], row["adoption_last_verified"]) == ("4", "2026-08-02")
    assert (row["capability_score"], row["capability_last_verified"]) == ("3", "2026-08-03")
    # signal_type decides what an adoption level may be compared to, so it must not be
    # dropped: a stars band and a downloads band are different scales.
    assert row["adoption_signal_type"] == "usage_volume"


def test_a_missing_axis_is_empty_rather_than_absent():
    """An unmeasured axis must still leave a column, or a reader cannot tell 'not measured'
    from 'column does not exist'."""
    payload = _payload()
    del payload["categories"]["cat_a"]["products"][0]["capability"]
    row = build_scores(payload)["product_scores"][0]
    assert row["capability_score"] == ""
    assert set(row) == set(COLUMNS)


def test_the_grain_is_product_times_category():
    payload = _payload()
    second = dict(payload["categories"]["cat_a"]["products"][0])
    payload["categories"]["cat_b"] = {"products": [second]}
    rows = build_scores(payload)["product_scores"]
    assert len(rows) == 2
    assert {r["category_slug"] for r in rows} == {"cat_a", "cat_b"}


def test_preliminary_categories_are_out_of_scope_by_construction():
    """The table mirrors the payload, and the payload excludes preliminary categories.

    Pinned as intended rather than left to be rediscovered: every row here is a row a
    visitor to /map could see. `currentai.registry.categories` is wider — it carries a
    `status` column and will list a preliminary category whose products have no row in this
    table. Covering them too would need a second path through `build_payload`, and a second
    implementation of the score derivation is the one thing worth avoiding.
    """
    payload = _payload()
    # What a preliminary category looks like from here: absent. serialize.build_payload has
    # already dropped it before this module ever sees the object.
    assert "cat_preliminary" not in payload["categories"]
    rows = build_scores(payload)["product_scores"]
    assert {r["category_slug"] for r in rows} == {"cat_a"}


def test_no_category_key_is_invented_for_a_category_the_payload_omits():
    """A guard on the guard above: if this module ever read the taxonomy directly instead of
    the payload, it could resurrect a preliminary category and the test above would not see
    it. build_scores takes the payload as its only input, so this asserts the signature."""
    import inspect

    from build import serialize_scores

    params = list(inspect.signature(serialize_scores.build_scores).parameters)
    assert params == ["payload"], (
        f"build_scores takes {params}; taking anything but the payload would let a preliminary "
        f"category back in through a second source of truth"
    )
