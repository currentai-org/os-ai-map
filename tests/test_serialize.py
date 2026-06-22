from build.serialize import build_payload


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


def test_unknown_org_renders_empty_string():
    s = _sources()
    s["organizations"] = {"unknown": {"name": "unknown", "display_name": "Unknown",
                                      "type": "unknown", "products": ["llama-4"]}}
    payload = build_payload(s, frozen_long_tail={}, generated="2026-06-10")
    assert payload["categories"]["base_pretrained"]["products"][0]["org"] == ""
