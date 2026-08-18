from build.validate import validate_sources

def _fixture():
    return {
        "organizations": {"meta": {"name": "meta", "display_name": "Meta", "products": ["llama"]}},
        "taxonomy": {"arcs": [{"name": "Model components", "layer": "model_components",
                               "categories": ["base_pretrained"]}]},
        "categories": {
            "base_pretrained": {"name": "base_pretrained", "display_name": "Base",
                                "products": ["llama"], "comments": ""}
        },
        "products": {"llama": {"name": "llama", "display_name": "Llama",
                                 "type": "model", "github": [{"url": "https://github.com/meta-llama/llama"}],
                                 "comments": ""}},
        "scores": {"llama": {"product": "llama",
                               "openness": {"score": 2, "class": "restricted",
                                            "sources": [{"url": "https://x", "shows": "y", "accessed": "2026-06-09"}]},
                               "adoption": {"level": 4, "signal_type": "usage_volume",
                                            "sources": [{"url": "https://x", "shows": "y", "accessed": "2026-06-09"}]},
                               "capability": {"score": None, "basis": "n/a"}}},
    }

def test_valid_fixture_passes():
    assert validate_sources(_fixture()) == []

def test_stem_must_equal_the_inner_name():
    """The filename stem is the identity every join uses.

    A copied or renamed file with a stale inner name passes schema and roster checks and
    then corrupts joins silently: the roster resolves by stem while anything reading the
    field resolves elsewhere. Nothing checked this until the slug migration renamed 60
    files at once and made the risk obvious."""
    d = _fixture()
    d["products"]["llama"]["name"] = "llama-stale"
    errs = validate_sources(d)
    assert any("does not match the filename stem" in e and "llama" in e for e in errs)


def test_score_stem_must_equal_its_product_key():
    """Scores name their slug `product`, not `name`, so the check has to know that."""
    d = _fixture()
    d["scores"]["llama"]["product"] = "something-else"
    errs = validate_sources(d)
    assert any("does not match the filename stem" in e for e in errs)


def test_matching_stems_produce_no_identity_error():
    d = _fixture()
    assert not any("does not match the filename stem" in e for e in validate_sources(d))


def test_long_tail_scored_must_match_product_count():
    d = _fixture()  # exactly one product
    d["long_tail"] = {"counts": {"scored": 999}}
    errs = validate_sources(d)
    assert any("counts.scored" in e for e in errs)
    d["long_tail"]["counts"]["scored"] = 1  # now matches the single product
    assert not any("counts.scored" in e for e in validate_sources(d))


def test_orphan_product_not_in_roster_fails():
    d = _fixture()
    d["products"]["ghost"] = {"name": "ghost", "display_name": "Ghost", "type": "model"}
    errs = validate_sources(d)
    assert any("exactly one category" in e for e in errs)

def test_category_missing_from_taxonomy_fails():
    d = _fixture()
    d["taxonomy"]["arcs"] = []  # base_pretrained no longer listed in any arc
    errs = validate_sources(d)
    assert any("exactly one taxonomy arc" in e for e in errs)

def test_category_listed_in_two_arcs_fails():
    d = _fixture()
    d["taxonomy"]["arcs"].append({"name": "Other", "layer": "infrastructure",
                                  "categories": ["base_pretrained"]})
    errs = validate_sources(d)
    assert any("exactly one taxonomy arc" in e for e in errs)


def test_preliminary_category_may_have_no_head_products_but_needs_business_logic():
    d = _fixture()
    d["taxonomy"]["arcs"][0]["categories"].append(
        {"name": "storage", "status": "preliminary"}
    )
    d["categories"]["storage"] = {
        "name": "storage",
        "display_name": "Storage",
        "description": "AI storage and retrieval systems.",
        "weights": {"adopt": 0.6, "cap": 0.4},
        "products": [],
        "scoring_recipe": {"version": 1},
    }
    assert validate_sources(d) == []
    d["categories"]["storage"].pop("scoring_recipe")
    assert any("storage" in e and "scoring_recipe" in e for e in validate_sources(d))


def test_explicitly_published_category_requires_publication_fields_and_head_depth():
    d = _fixture()
    d["taxonomy"]["arcs"][0]["categories"] = [
        {"name": "base_pretrained", "status": "published"}
    ]
    d["categories"]["base_pretrained"].update(
        {
            "description": "Base models.",
            "weights": {"adopt": 0.3, "cap": 0.7},
            "scoring_recipe": {"version": 1},
        }
    )
    errs = validate_sources(d)
    assert any("needs a strapline" in e for e in errs)
    assert any("at least 10 scored products" in e for e in errs)


def test_tail_registry_cannot_duplicate_a_head_product_or_artifact():
    d = _fixture()
    d["registry"] = {
        "storage": {
            "category": "storage",
            "products": [
                {
                    "slug": "llama",
                    "display_name": "Duplicate",
                    "type": "software",
                    "org": "meta",
                    "github": "meta-llama/llama",
                }
            ],
        }
    }
    errs = validate_sources(d)
    assert any("already exists as a head product" in e for e in errs)
    assert any("already belongs to head product" in e for e in errs)

def test_roster_pointing_at_missing_product_fails():
    d = _fixture()
    d["categories"]["base_pretrained"]["products"].append("does-not-exist")
    errs = validate_sources(d)
    assert any("does-not-exist" in e for e in errs)

def test_product_in_zero_org_rosters_fails():
    d = _fixture()
    d["organizations"]["meta"]["products"] = []  # llama now in no org roster
    errs = validate_sources(d)
    assert any("exactly one org roster" in e and "llama" in e for e in errs)

def test_product_in_two_org_rosters_fails():
    d = _fixture()
    # a second org also claims llama -> appears in two rosters
    d["organizations"]["other"] = {"name": "other", "display_name": "Other", "products": ["llama"]}
    errs = validate_sources(d)
    assert any("exactly one org roster" in e and "llama" in e for e in errs)

def test_org_roster_pointing_at_missing_product_fails():
    d = _fixture()
    d["organizations"]["meta"]["products"].append("does-not-exist")
    errs = validate_sources(d)
    assert any("does-not-exist" in e for e in errs)

def test_openness_class_invalid_for_type_fails():
    d = _fixture()
    d["scores"]["llama"]["openness"]["class"] = "open_core"  # software-only class on a model
    errs = validate_sources(d)
    assert any("class" in e for e in errs)

def test_adoption_without_sources_fails():
    d = _fixture()
    d["scores"]["llama"]["adoption"].pop("sources", None)
    errs = validate_sources(d)
    assert any("adoption" in e and "source" in e for e in errs)

def test_capability_without_sources_fails():
    d = _fixture()
    d["scores"]["llama"]["capability"] = {"score": 3, "basis": "benchmark:X"}
    errs = validate_sources(d)
    assert any("capability" in e and "source" in e for e in errs)

def test_stars_fallback_cannot_exceed_level_3():
    d = _fixture()
    d["scores"]["llama"]["adoption"] = {"level": 5, "signal_type": "stars_fallback",
                                          "sources": [{"url": "https://x", "shows": "y", "accessed": "2026-06-09"}]}
    errs = validate_sources(d)
    assert any("stars_fallback" in e for e in errs)

def test_schema_violation_bad_product_type_caught():
    d = _fixture()
    d["products"]["llama"]["type"] = "not-a-real-type"  # outside the enum
    errs = validate_sources(d)
    assert any("schema" in e and "llama" in e for e in errs)

def test_schema_violation_negative_openness_score_caught():
    d = _fixture()
    d["scores"]["llama"]["openness"]["score"] = -1  # below schema minimum of 0
    errs = validate_sources(d)
    assert any("schema" in e and "llama" in e for e in errs)

def test_product_without_score_file_caught_not_raised():
    d = _fixture()
    # rostered product present in products + roster but absent from scores
    d["products"]["mistral"] = {"name": "mistral", "display_name": "Mistral", "type": "model"}
    d["categories"]["base_pretrained"]["products"].append("mistral")
    d["organizations"]["meta"]["products"].append("mistral")
    errs = validate_sources(d)  # must not raise
    assert any(e == "product 'mistral': no scores/mistral.yaml" for e in errs)


def test_unknown_signal_type_still_fails():
    d = _fixture()
    d["scores"]["llama"]["adoption"]["signal_type"] = "vibes"
    assert any("signal_type" in e for e in validate_sources(d))


def test_product_lineage_block_validates():
    d = _fixture()
    d["products"]["llama"]["lineage"] = {
        "derived_from": ["Common Crawl"],
        "curated_with": ["datatrove"],
        "trains": ["llama"],
    }
    assert validate_sources(d) == []


def test_product_lineage_rejects_unknown_keys():
    d = _fixture()
    d["products"]["llama"]["lineage"] = {"forked_from": ["x"]}
    errs = validate_sources(d)
    assert any("lineage" in e or "forked_from" in e or "additional" in e.lower() for e in errs)


def _with_recipe(d):
    """Give the fixture a category recipe, so `establishes` has a vocabulary to check.

    Without one the cross-file check has nothing to check against and skips, which is the
    correct behavior for a hand-built fixture but makes it useless for these tests.
    """
    d["categories"]["base_pretrained"]["scoring_recipe"] = {
        "openness": {
            "dimensions": {
                "weights": {"values": ["open", "closed"]},
                "data": {"values": ["open", "closed"], "reads": ["data", "post-training-data"]},
            },
            "formula": [{"when": {"weights": "closed"}, "then": {"score": 1, "class": "closed"}}],
        }
    }
    return d


def test_establishes_accepts_a_declared_dimension():
    d = _with_recipe(_fixture())
    d["scores"]["llama"]["openness"]["sources"][0]["establishes"] = ["weights"]
    assert validate_sources(d) == []


def test_establishes_accepts_a_recorded_key_a_dimension_reads():
    """`post-training-data` is not a dimension name, but it is declared vocabulary."""
    d = _with_recipe(_fixture())
    d["scores"]["llama"]["openness"]["sources"][0]["establishes"] = ["post-training-data"]
    assert validate_sources(d) == []


def test_establishes_accepts_license_though_it_is_a_derived_tier():
    """A source establishes the license; the recipe derives the tier from it."""
    d = _with_recipe(_fixture())
    d["scores"]["llama"]["openness"]["sources"][0]["establishes"] = ["license"]
    assert validate_sources(d) == []


def test_establishes_rejects_a_typo():
    """The whole point: a misspelled dimension establishes nothing while looking like it does."""
    d = _with_recipe(_fixture())
    d["scores"]["llama"]["openness"]["sources"][0]["establishes"] = ["weight"]
    errs = validate_sources(d)
    assert any("establish 'weight'" in e for e in errs)


def test_establishes_rejects_a_british_spelling_of_license():
    d = _with_recipe(_fixture())
    d["scores"]["llama"]["openness"]["sources"][0]["establishes"] = ["licence"]
    assert any("establish 'licence'" in e for e in validate_sources(d))


def test_establishes_checked_on_adoption_and_capability_too():
    d = _with_recipe(_fixture())
    d["scores"]["llama"]["adoption"]["sources"][0]["establishes"] = ["nonsense"]
    assert any("adoption source" in e and "nonsense" in e for e in validate_sources(d))


def test_establishes_skipped_when_no_recipe_declares_anything():
    """No vocabulary means no basis to reject a name, so the check abstains rather than
    failing every source in a repo whose categories have no recipes yet."""
    d = _fixture()  # deliberately no scoring_recipe
    d["scores"]["llama"]["openness"]["sources"][0]["establishes"] = ["weight"]
    assert not any("establish" in e for e in validate_sources(d))


def test_digest_must_be_a_sha256():
    d = _fixture()
    d["scores"]["llama"]["openness"]["sources"][0]["content_sha256"] = "deadbeef"
    assert any("schema" in e for e in validate_sources(d))


def test_http_status_must_be_a_real_status_code():
    d = _fixture()
    d["scores"]["llama"]["openness"]["sources"][0]["http_status"] = 20
    assert any("schema" in e for e in validate_sources(d))


def test_a_fetched_source_with_status_and_digest_validates():
    d = _fixture()
    d["scores"]["llama"]["openness"]["sources"][0].update(
        {"http_status": 200, "content_sha256": "a" * 64}
    )
    assert validate_sources(d) == []
