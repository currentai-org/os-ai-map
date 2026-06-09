from build.validate import validate_sources

def _fixture():
    return {
        "organizations": {"meta": {"slug": "meta", "name": "Meta"}},
        "taxonomy": {"arcs": [{"name": "Models", "categories": ["base_pretrained"]}]},
        "categories": {
            "base_pretrained": {"slug": "base_pretrained", "name": "Base",
                                "products": ["llama-4"]}
        },
        "products": {"llama-4": {"slug": "llama-4", "name": "Llama 4", "org": "meta", "type": "model"}},
        "scores": {"llama-4": {"product": "llama-4",
                               "openness": {"score": 2, "class": "restricted",
                                            "sources": [{"url": "https://x", "shows": "y", "accessed": "2026-06-09"}]},
                               "adoption": {"level": 4, "signal_type": "usage_volume",
                                            "sources": [{"url": "https://x", "shows": "y", "accessed": "2026-06-09"}]},
                               "capability": {"score": None, "basis": "n/a"}}},
    }

def test_valid_fixture_passes():
    assert validate_sources(_fixture()) == []

def test_orphan_product_not_in_roster_fails():
    d = _fixture()
    d["products"]["ghost"] = {"slug": "ghost", "name": "Ghost", "org": "meta", "type": "model"}
    errs = validate_sources(d)
    assert any("exactly one category" in e for e in errs)

def test_category_missing_from_taxonomy_fails():
    d = _fixture()
    d["taxonomy"]["arcs"] = []  # base_pretrained no longer listed in any arc
    errs = validate_sources(d)
    assert any("exactly one taxonomy arc" in e for e in errs)

def test_category_listed_in_two_arcs_fails():
    d = _fixture()
    d["taxonomy"]["arcs"].append({"name": "Other", "categories": ["base_pretrained"]})
    errs = validate_sources(d)
    assert any("exactly one taxonomy arc" in e for e in errs)

def test_roster_pointing_at_missing_product_fails():
    d = _fixture()
    d["categories"]["base_pretrained"]["products"].append("does-not-exist")
    errs = validate_sources(d)
    assert any("does-not-exist" in e for e in errs)

def test_bad_org_ref_fails():
    d = _fixture()
    d["products"]["llama-4"]["org"] = "nope"
    errs = validate_sources(d)
    assert any("org" in e and "nope" in e for e in errs)

def test_openness_class_invalid_for_type_fails():
    d = _fixture()
    d["scores"]["llama-4"]["openness"]["class"] = "open_core"  # software-only class on a model
    errs = validate_sources(d)
    assert any("class" in e for e in errs)

def test_stars_fallback_cannot_exceed_level_3():
    d = _fixture()
    d["scores"]["llama-4"]["adoption"] = {"level": 5, "signal_type": "stars_fallback",
                                          "sources": [{"url": "https://x", "shows": "y", "accessed": "2026-06-09"}]}
    errs = validate_sources(d)
    assert any("stars_fallback" in e for e in errs)
