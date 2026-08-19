from build.validate import validate_sources

# `llama` is the product the tests reach for; the other nine exist because a PUBLISHED
# category owes ten scored products, and a scalar taxonomy entry means published. Padded
# programmatically rather than by hand so the roster stays one fact in one place.
# Letters rather than numbers in the filler slugs: a model slug carrying a digit reads as a
# version or size token and validate rejects it, which is a rule worth not tripping in a fixture.
FIXTURE_PRODUCTS = ["llama"] + [f"filler-{c}" for c in "abcdefghi"]


def _fixture():
    def product(slug):
        return {"name": slug, "display_name": slug.title(), "type": "model",
                "github": [{"url": f"https://github.com/meta-llama/{slug}"}], "comments": ""}

    def score(slug):
        cite = [{"url": "https://x", "shows": "y", "accessed": "2026-06-09"}]
        return {"product": slug,
                "openness": {"score": 2, "class": "restricted", "sources": cite},
                "adoption": {"level": 4, "signal_type": "usage_volume", "sources": cite},
                "capability": {"score": None, "basis": "n/a"}}

    return {
        "organizations": {"meta": {"name": "meta", "display_name": "Meta",
                                   "products": list(FIXTURE_PRODUCTS)}},
        "taxonomy": {"arcs": [{"name": "Model components", "layer": "model_components",
                               "categories": ["base_pretrained"]}]},
        "categories": {
            "base_pretrained": {"name": "base_pretrained", "display_name": "Base",
                                "description": "Base / pretrained models.",
                                "strapline": "The layer everything else is trained from.",
                                "weights": {"adopt": 0.6, "cap": 0.4},
                                "scoring_recipe": {"version": 1, "extends": "model"},
                                "products": list(FIXTURE_PRODUCTS), "comments": ""}
        },
        "products": {slug: product(slug) for slug in FIXTURE_PRODUCTS},
        "scores": {slug: score(slug) for slug in FIXTURE_PRODUCTS},
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
    d = _fixture()
    d["long_tail"] = {"counts": {"scored": 999}}
    errs = validate_sources(d)
    assert any("counts.scored" in e for e in errs)
    d["long_tail"]["counts"]["scored"] = len(FIXTURE_PRODUCTS)  # now matches the roster
    assert not any("counts.scored" in e for e in validate_sources(d))


def test_long_tail_scored_counts_published_categories_only():
    """Reproduces the review finding on the compilers/storage promotion.

    A preliminary category may hold fully scored head products — that is the state a
    category is in while it is being built. `serialize.py` omits them from the payload, so
    counting them here let `counts.scored` exceed `n_total`, and the notebook's "of the N
    products scored above" then named products the reader could not see. The check passed
    the whole time, which is why it is worth a test rather than a comment.
    """
    d = _fixture()
    d["taxonomy"]["arcs"][0]["categories"] = [{"name": "base_pretrained", "status": "preliminary"}]
    d["long_tail"] = {"counts": {"scored": len(FIXTURE_PRODUCTS)}}  # the files, now unpublished
    errs = validate_sources(d)
    assert any("counts.scored" in e and "published categories (0)" in e for e in errs)
    d["long_tail"]["counts"]["scored"] = 0  # nothing is published, so nothing is scored above
    assert not any("counts.scored" in e for e in validate_sources(d))


def test_head_products_in_a_preliminary_category_are_not_an_error():
    """The other resolution considered for the same finding, and rejected.

    Prohibiting head products in a preliminary category would make the promotion workflow
    impossible: a roster is filled in, checked, and only then published. So the products are
    allowed and the count follows the published roster instead.
    """
    d = _fixture()
    d["taxonomy"]["arcs"][0]["categories"] = [{"name": "base_pretrained", "status": "preliminary"}]
    # A preliminary category still owes a description, weights and a ladder; only the strapline
    # and the ten-product floor wait for publication, so a thinner roster would pass here too.
    d["long_tail"] = {"counts": {"scored": 0}}
    assert validate_sources(d) == []


def test_a_scalar_taxonomy_entry_is_held_to_the_published_contract():
    """The compatibility shim for the historical spelling is not an exemption.

    A scalar entry means published, and a published category owes a description, weights, a
    ladder, a strapline and ten scored products. Skipping the checks for anything not declared
    as a mapping let a bare category file pass with none of them and ship publicly empty. Found
    in review of the compilers/storage promotion; measured before the fix, every one of the
    sixteen scalar entries in the corpus already satisfies the contract.
    """
    d = _fixture()
    d["categories"]["empty_new"] = {"name": "empty_new", "display_name": "Empty New",
                                    "products": []}
    d["taxonomy"]["arcs"][0]["categories"].append("empty_new")  # scalar, so published
    errs = [e for e in validate_sources(d) if "empty_new" in e]
    for owed in ("needs a description", "needs axis weights", "needs a scoring_recipe",
                 "needs a strapline", "at least 10 scored products"):
        assert any(owed in e for e in errs), owed


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
    # Trimmed back to one product and stripped of its strapline, since the shared fixture now
    # satisfies the published contract - which is the point of the test one level up.
    d = _fixture()
    d["taxonomy"]["arcs"][0]["categories"] = [
        {"name": "base_pretrained", "status": "published"}
    ]
    d["categories"]["base_pretrained"].pop("strapline")
    d["categories"]["base_pretrained"]["products"] = ["llama"]
    d["organizations"]["meta"]["products"] = ["llama"]
    for key in ("products", "scores"):
        d[key] = {"llama": d[key]["llama"]}
    errs = validate_sources(d)
    assert any("needs a strapline" in e for e in errs)
    assert any("at least 10 scored products" in e for e in errs)
    assert not any("description" in e or "axis weights" in e or "scoring_recipe" in e
                   for e in errs), "the fixture supplies those three; only the two above are owed"


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
