from build.serialize import build_payload, _stage_and_gaps


def _p(cls, adoption, capability):
    return {"openness": {"class": cls}, "adoption": {"level": adoption},
            "capability": {"score": capability}}


def test_stage5_mature_open_ecosystem():
    rows = [_p("open_source", 5, 5) for _ in range(4)]  # 4 mature fully-open
    sg = _stage_and_gaps(rows, {"adopt": 0.5, "cap": 0.5})
    assert sg["num"] == 5 and sg["gaps"] == []


def test_openness_gap_when_mature_options_are_open_ish():
    rows = [_p("open_weights", 5, 5) for _ in range(3)]  # mature but open-ish, none fully open
    sg = _stage_and_gaps(rows, {"adopt": 0.5, "cap": 0.5})
    assert sg["num"] < 5 and "maturity" in sg["gaps"] and "openness" in sg["gaps"]


def test_missing_adoption_yields_null_maturity_and_is_excluded_from_stage():
    # A product with null adoption has no maturity score (not 0.0) and must not drag
    # the category's stage down — here a mature open product should still reach stage 4.
    rows = [_p("open_source", 5, 5), _p("open_source", None, None)]
    sg = _stage_and_gaps(rows, {"adopt": 0.5, "cap": 0.5})
    assert sg["num"] == 4  # the null-adoption product is ignored, the mature one stands


def test_void_when_no_open_option():
    sg = _stage_and_gaps([_p("closed", 1, 1)], {"adopt": 0.5, "cap": 0.5})
    assert sg["num"] == 0 and sg["gaps"] == ["void"]


def test_capability_gap_when_nothing_mature_and_weak():
    rows = [_p("open_source", 2, 2)]  # fully open but weak on both axes
    sg = _stage_and_gaps(rows, {"adopt": 0.5, "cap": 0.5})
    assert "maturity" in sg["gaps"] and "capability" in sg["gaps"]


def _sources():
    return {
        "organizations": {"meta": {"name": "meta", "display_name": "Meta",
                                   "type": "unknown", "products": ["llama-4"]}},
        "taxonomy": {"arcs": [{"name": "Model components", "layer": "model_components",
                               "categories": ["base_pretrained"]}]},
        "categories": {
            "base_pretrained": {"name": "base_pretrained",
                                "display_name": "Base / pretrained models",
                                "products": ["llama-4"], "comments": ""}
        },
        "products": {"llama-4": {"name": "llama-4", "display_name": "Llama 4",
                                 "type": "model", "description": "desc",
                                 "comments": "note text"}},
        "scores": {"llama-4": {"product": "llama-4",
                               "openness": {"score": 2, "class": "restricted"},
                               "adoption": {"level": 4, "signal_type": "usage_volume"},
                               "capability": {"score": None, "basis": "n/a"}}},
    }


def test_build_payload_shape_and_order():
    payload = build_payload(_sources(), frozen_long_tail={"counts": {}, "top": []},
                            generated="2026-06-10")
    assert payload["order"] == ["base_pretrained"]
    assert payload["n_total"] == 1
    assert payload["generated"] == "2026-06-10"
    cat = payload["categories"]["base_pretrained"]
    assert cat["label"] == "Base / pretrained models"
    assert cat["arc"] == "Model components"
    assert cat["layer"] == "model_components"
    row = cat["products"][0]
    assert row["product"] == "Llama 4"
    assert row["org"] == "Meta"
    # comments field is carried under the legacy payload key version_note
    assert row["version_note"] == "note text"
    # llama-4 has no capability score, so maturity falls back to adoption (4) alone
    assert row["maturity"] == 4.0


def test_null_adoption_serializes_maturity_null():
    src = _sources()
    src["scores"]["llama-4"]["adoption"] = {"level": None, "signal_type": "unknown"}
    payload = build_payload(src, frozen_long_tail={}, generated="2026-06-10")
    assert payload["categories"]["base_pretrained"]["products"][0]["maturity"] is None


def test_maturity_is_weighted_blend_rounded_2dp():
    # adoption 4, capability 5 with default 0.5/0.5 weights -> 4.5; cap-heavy 0.25/0.75 -> 4.75
    src = _sources()
    src["scores"]["llama-4"]["capability"] = {"score": 5, "basis": "x"}
    payload = build_payload(src, frozen_long_tail={}, generated="2026-06-10")
    assert payload["categories"]["base_pretrained"]["products"][0]["maturity"] == 4.5

    src["categories"]["base_pretrained"]["weights"] = {"adopt": 0.25, "cap": 0.75}
    payload = build_payload(src, frozen_long_tail={}, generated="2026-06-10")
    assert payload["categories"]["base_pretrained"]["products"][0]["maturity"] == 4.75


def test_long_tail_drops_now_categorized_products():
    # llama-4 carries github.com/meta-llama/llama; a frozen long-tail sample row for
    # that same repo must be filtered out (it is no longer uncategorized), while an
    # unrelated row survives.
    src = _sources()
    src["products"]["llama-4"]["github"] = [{"url": "https://github.com/meta-llama/llama"}]
    frozen = {"counts": {}, "top": [
        {"name": "meta-llama/llama", "type": "repo", "usage_label": "", "description": ""},
        {"name": "someone/uncategorized", "type": "repo", "usage_label": "", "description": ""},
    ]}
    payload = build_payload(src, frozen_long_tail=frozen, generated="2026-06-10")
    names = [t["name"] for t in payload["long_tail"]["top"]]
    assert "meta-llama/llama" not in names
    assert "someone/uncategorized" in names


def test_descriptions_block_present_and_sourced():
    src = _sources()
    src["categories"]["base_pretrained"]["description"] = "Foundation models trained from scratch."
    payload = build_payload(src, frozen_long_tail={}, generated="2026-06-10")
    d = payload["descriptions"]
    # stages keyed 0-5, gaps keyed by name, categories keyed by slug from the source yaml
    assert set(d["stages"]) == {"0", "1", "2", "3", "4", "5"}
    assert "void" in d["gaps"] and "openness" in d["gaps"]
    assert d["categories"]["base_pretrained"] == "Foundation models trained from scratch."
    # descriptions ships first so it reads as a header
    assert list(payload)[0] == "descriptions"


def test_openness_bucket_assigned_per_product():
    # restricted collapses to the closed bucket; the raw class is preserved alongside it
    payload = build_payload(_sources(), frozen_long_tail={}, generated="2026-06-10")
    op = payload["categories"]["base_pretrained"]["products"][0]["openness"]
    assert op["class"] == "restricted"
    assert op["bucket"] == "closed"


def test_openness_bucket_covers_open_and_open_ish():
    src = _sources()
    src["scores"]["llama-4"]["openness"] = {"score": 5, "class": "open_source"}
    payload = build_payload(src, frozen_long_tail={}, generated="2026-06-10")
    assert payload["categories"]["base_pretrained"]["products"][0]["openness"]["bucket"] == "open"
    src["scores"]["llama-4"]["openness"] = {"score": 3, "class": "open_weights"}
    payload = build_payload(src, frozen_long_tail={}, generated="2026-06-10")
    assert payload["categories"]["base_pretrained"]["products"][0]["openness"]["bucket"] == "open-ish"


def _mature_flag(cls, adoption, capability, weights=None):
    src = _sources()
    src["scores"]["llama-4"]["openness"] = {"score": 5, "class": cls}
    src["scores"]["llama-4"]["adoption"] = {"level": adoption, "signal_type": "usage_volume"}
    src["scores"]["llama-4"]["capability"] = {"score": capability, "basis": "x"}
    if weights is not None:
        src["categories"]["base_pretrained"]["weights"] = weights
    payload = build_payload(src, frozen_long_tail={}, generated="2026-06-10")
    return payload["categories"]["base_pretrained"]["products"][0]["mature"]


def test_mature_flag_matches_stage_engine_rule():
    # Rule: maturity is not None AND maturity >= 4.5 AND bucket == "open".
    # Fully open, blended 5.0 -> mature.
    assert _mature_flag("open_source", 5, 5) is True
    # Fully open but blended 4.0 (< 4.5 bar) -> not mature.
    assert _mature_flag("open_source", 4, 4) is False
    # Open-weights (open-ish bucket), blended 5.0 -> NOT mature: the bucket gate fails.
    assert _mature_flag("open_weights", 5, 5) is False
    # Closed, blended 5.0 -> not mature.
    assert _mature_flag("closed", 5, 5) is False
    # Exactly at the 4.5 bar, fully open -> mature (>= is inclusive).
    assert _mature_flag("open_source", 4, 5) is True


def test_mature_flag_false_when_maturity_null():
    src = _sources()
    src["scores"]["llama-4"]["openness"] = {"score": 5, "class": "open_source"}
    src["scores"]["llama-4"]["adoption"] = {"level": None, "signal_type": "unknown"}
    payload = build_payload(src, frozen_long_tail={}, generated="2026-06-10")
    row = payload["categories"]["base_pretrained"]["products"][0]
    assert row["maturity"] is None
    assert row["mature"] is False


def test_unknown_org_renders_empty_string():
    s = _sources()
    s["organizations"] = {"unknown": {"name": "unknown", "display_name": "Unknown",
                                      "type": "unknown", "products": ["llama-4"]}}
    payload = build_payload(s, frozen_long_tail={}, generated="2026-06-10")
    assert payload["categories"]["base_pretrained"]["products"][0]["org"] == ""
