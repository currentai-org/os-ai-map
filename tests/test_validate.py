from pathlib import Path

import pytest
import yaml

from build.resolution import DuplicateResolution
from build.validate import load_sources, validate_sources

ROOT = Path(__file__).resolve().parents[1]

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
        "model_families": {"version": 1, "families": []},
        "org_handles": {"version": 1, "handles": []},
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


def test_long_tail_scored_is_derived_not_gated():
    """A product addition must not require editing sources/snapshots/long_tail.json.

    `counts.scored` used to be a hand-synced number, gated here against the published
    roster. It is now derived at serialize time (build.serialize.derived_long_tail_counts)
    and no longer read from the file at all, so nothing here should ever flag it — not a
    stale value, not a missing one, not one that disagrees with a preliminary category's
    unpublished roster.
    """
    d = _fixture()
    d["long_tail"] = {"counts": {"scored": 999}}  # would have failed the old gate
    assert not [e for e in validate_sources(d) if "counts.scored" in e]
    d["long_tail"]["counts"].pop("scored")  # missing entirely is fine too
    assert not [e for e in validate_sources(d) if "counts.scored" in e]


def test_derived_long_tail_counts():
    from build.serialize import derived_long_tail_counts

    frozen = {"counts": {"repos": 10, "models": 5, "packages": 5,
                         "total": 20, "overlap": 3, "universe": 22}}
    out = derived_long_tail_counts(frozen, published={"a", "b", "c", "d"})
    assert out["scored"] == 4
    assert out["scored_outside"] == 1
    assert out["uncategorized"] == 17
    assert out["total"] == 20


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

def test_tail_slug_cannot_be_a_retired_alias():
    """A retired slug disqualifies a candidate exactly as a live slug does.

    The discover-candidates workflow makes "dedup against retired aliases" its second
    dedup rule and its Validation section claimed this check existed. It did not: the tail
    block tested `slug in prods` and nothing else, so amazon-nova-pro -- an alias of
    amazon-nova in the real corpus -- passed as a brand-new candidate. An advisory dedup
    rule that validation does not enforce is a rule that fails silently."""
    d = _fixture()
    d["products"]["llama"]["aliases"] = ["llama-70b-chat"]
    d["registry"] = {
        "storage": {
            "category": "storage",
            "products": [
                {
                    "slug": "llama-70b-chat",
                    "display_name": "Llama 70B Chat",
                    "type": "software",
                    "org": "meta",
                    "github": "meta-llama/some-other-repo",
                }
            ],
        }
    }
    errs = validate_sources(d)
    assert any("is a retired alias of head product 'llama'" in e for e in errs), errs


def test_a_tail_slug_that_is_no_alias_passes():
    """The mirror of the above: the check must be able to pass, or it proves nothing."""
    d = _fixture()
    d["products"]["llama"]["aliases"] = ["llama-70b-chat"]
    d["registry"] = {
        "storage": {
            "category": "storage",
            "products": [
                {
                    "slug": "some-new-thing",
                    "display_name": "Some New Thing",
                    "type": "software",
                    "org": "meta",
                    "github": "acme/some-new-thing",
                }
            ],
        }
    }
    assert not any("retired alias" in e for e in validate_sources(d))


def test_tail_row_with_only_huggingface_validates():
    """#365: a row needs at least one addressable artifact, not `github` specifically."""
    d = _fixture()
    d["registry"] = {
        "base_pretrained": {
            "category": "base_pretrained",
            "products": [
                {
                    "slug": "some-hf-thing",
                    "display_name": "Some HF Thing",
                    "type": "model",
                    "org": "meta",
                    "huggingface_model": "acme/some-hf-thing",
                }
            ],
        }
    }
    assert validate_sources(d) == []


def test_tail_row_with_only_arxiv_validates():
    d = _fixture()
    d["registry"] = {
        "base_pretrained": {
            "category": "base_pretrained",
            "products": [
                {
                    "slug": "some-paper-thing",
                    "display_name": "Some Paper Thing",
                    "type": "software",
                    "org": "meta",
                    "arxiv": "2401.12345",
                }
            ],
        }
    }
    assert validate_sources(d) == []


def test_tail_row_with_only_homepage_validates():
    """`homepage` alone is enough to satisfy `has_artifact`, same as any other kind."""
    d = _fixture()
    d["registry"] = {
        "base_pretrained": {
            "category": "base_pretrained",
            "products": [
                {
                    "slug": "some-homepage-thing",
                    "display_name": "Some Homepage Thing",
                    "type": "software",
                    "org": "meta",
                    "homepage": "https://example.com",
                }
            ],
        }
    }
    assert validate_sources(d) == []


def test_tail_rows_sharing_a_homepage_url_fail():
    """`homepage` is a dedup-gated identity key, not just an addressability check (#472
    review, corrected in #365): two tail rows declaring the same comparison URL are the
    same duplicate identity a github or pypi collision would be, even across categories
    and even when the URLs differ by scheme, `www.`, trailing slash or query."""
    d = _fixture()
    d["registry"] = {
        "base_pretrained": {
            "category": "base_pretrained",
            "products": [
                {
                    "slug": "site-one",
                    "display_name": "Site One",
                    "type": "software",
                    "org": "meta",
                    "homepage": "https://www.Example.com/",
                },
            ],
        },
        "storage": {
            "category": "storage",
            "products": [
                {
                    "slug": "site-two",
                    "display_name": "Site Two",
                    "type": "software",
                    "org": "meta",
                    "homepage": "http://example.com?utm=1",
                },
            ],
        },
    }
    errs = validate_sources(d)
    assert any(
        "homepage artifact" in e and "already belongs to tail product 'site-one'" in e for e in errs
    ), errs


def test_tail_rows_sharing_a_homepage_domain_at_different_paths_do_not_collide():
    """A homepage is evidence, not identity (#365): one company's domain routinely hosts
    more than one distinct product, so two tail rows at different paths on the same
    domain are legitimately different artifacts, not a duplicate-identity collision."""
    d = _fixture()
    d["registry"] = {
        "base_pretrained": {
            "category": "base_pretrained",
            "products": [
                {
                    "slug": "acme-widgets",
                    "display_name": "Acme Widgets",
                    "type": "software",
                    "org": "meta",
                    "homepage": "https://acme.com/widgets",
                },
            ],
        },
        "storage": {
            "category": "storage",
            "products": [
                {
                    "slug": "acme-gadgets",
                    "display_name": "Acme Gadgets",
                    "type": "software",
                    "org": "meta",
                    "homepage": "https://acme.com/gadgets",
                },
            ],
        },
    }
    errs = validate_sources(d)
    assert not any("homepage artifact" in e for e in errs), errs


def test_tail_row_with_no_artifact_fails_with_a_clear_message():
    d = _fixture()
    d["registry"] = {
        "storage": {
            "category": "storage",
            "products": [
                {
                    "slug": "no-artifact-thing",
                    "display_name": "No Artifact Thing",
                    "type": "software",
                    "org": "meta",
                }
            ],
        }
    }
    errs = validate_sources(d)
    assert any("no addressable artifact" in e for e in errs), errs


def test_tail_rows_sharing_a_normalized_pypi_name_fail():
    """PEP 503: runs of -, _, . fold to -, and comparison is case-insensitive."""
    d = _fixture()
    d["registry"] = {
        "storage": {
            "category": "storage",
            "products": [
                {
                    "slug": "pkg-one",
                    "display_name": "Pkg One",
                    "type": "software",
                    "org": "meta",
                    "pypi": "My-Cool_Package",
                },
                {
                    "slug": "pkg-two",
                    "display_name": "Pkg Two",
                    "type": "software",
                    "org": "meta",
                    "pypi": "my.cool.package",
                },
            ],
        }
    }
    errs = validate_sources(d)
    assert any("pypi artifact" in e and "already belongs to tail product 'pkg-one'" in e for e in errs), errs


def test_tail_row_github_matching_head_product_fails_case_insensitively():
    """Existing behavior, extended: the tail/head collision check must not care about case."""
    d = _fixture()
    d["registry"] = {
        "storage": {
            "category": "storage",
            "products": [
                {
                    "slug": "duplicate-of-llama",
                    "display_name": "Duplicate",
                    "type": "software",
                    "org": "meta",
                    "github": "Meta-Llama/LLAMA",
                }
            ],
        }
    }
    errs = validate_sources(d)
    assert any("already belongs to head product" in e for e in errs), errs


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


def _membership_entry(product_slug, verdict, decided_in, note):
    return {
        "artifact": {"kind": "pypi", "id": "widget"}, "verdict": verdict,
        "relation": "product_membership", "resolves_to": product_slug,
        "decided_in": decided_in, "decided_on": "2026-09-03", "note": note,
    }


def _write_ledger(tmp_path, resolutions):
    path = tmp_path / "resolution_ledger.yaml"
    path.write_text(yaml.safe_dump({"version": 1, "resolutions": resolutions}))
    return path


def test_a_member_of_and_not_member_of_for_the_same_artifact_and_product_is_a_duplicate(tmp_path):
    """`resolves_to` is part of the ledger key `build/resolution.py` enforces uniqueness on, but
    the key is still enforced: a member_of and a not_member_of naming the SAME product are the
    same question answered twice, not two legitimate rulings."""
    path = _write_ledger(tmp_path, [
        _membership_entry("llama", "member_of", "#1", "widget's downloads are llama's own usage"),
        _membership_entry("llama", "not_member_of", "#2", "reversed on reconsideration, later sweep"),
    ])
    with pytest.raises(DuplicateResolution):
        validate_sources(_fixture(), ledger_path=path)


def test_a_membership_ruling_naming_an_unknown_product_is_a_hard_error(tmp_path):
    """resolves_to is part of the ledger key, so a retired, renamed, or mistyped slug never
    matches the product the ruling was meant to name - it silently forks the key instead of
    raising, which is worse than a build failure."""
    path = _write_ledger(tmp_path, [
        _membership_entry(
            "not-a-real-product", "not_member_of", "#1",
            "widget looks related to this product but its downloads are not its own",
        ),
    ])
    errs = validate_sources(_fixture(), ledger_path=path)
    assert any("not-a-real-product" in e and "not a product slug" in e for e in errs)


# --- org handles (sources/org_handles.yaml) -----------------------------------------

def _with_second_org(d):
    """A fixture with a second, product-less organization to collide handles against."""
    d["organizations"]["acme"] = {"name": "acme", "display_name": "Acme", "products": []}
    return d


def test_org_handle_is_fine_when_it_belongs_to_one_org():
    d = _with_second_org(_fixture())
    d["org_handles"]["handles"] = [
        {"org": "meta", "platform": "github", "handle": "meta-llama"},
        {"org": "acme", "platform": "github", "handle": "acme-labs"},
    ]
    assert validate_sources(d) == []


def test_org_handle_collision_is_a_hard_error():
    d = _with_second_org(_fixture())
    d["org_handles"]["handles"] = [
        {"org": "meta", "platform": "github", "handle": "shared-account"},
        {"org": "acme", "platform": "github", "handle": "shared-account"},
    ]
    errs = validate_sources(d)
    assert any("shared-account" in e and "claimed by both" in e for e in errs)


def test_org_handle_collision_folds_case():
    d = _with_second_org(_fixture())
    d["org_handles"]["handles"] = [
        {"org": "meta", "platform": "github", "handle": "SharedAccount"},
        {"org": "acme", "platform": "github", "handle": "sharedaccount"},
    ]
    errs = validate_sources(d)
    assert any("claimed by both" in e for e in errs)


def test_org_handle_collision_strips_leading_www():
    d = _with_second_org(_fixture())
    d["org_handles"]["handles"] = [
        {"org": "meta", "platform": "homepage_domain", "handle": "www.shared.example"},
        {"org": "acme", "platform": "homepage_domain", "handle": "shared.example"},
    ]
    errs = validate_sources(d)
    assert any("claimed by both" in e for e in errs)


def test_org_handle_does_not_collide_with_an_unrelated_orgs_slug():
    """A handle string that happens to equal another org's SLUG is not a collision -- the
    uniqueness key is (platform, folded handle), never an org slug."""
    d = _with_second_org(_fixture())
    d["org_handles"]["handles"] = [
        {"org": "meta", "platform": "github", "handle": "acme"},
    ]
    assert validate_sources(d) == []


def test_org_handle_naming_unknown_org_is_an_error():
    d = _fixture()
    d["org_handles"]["handles"] = [
        {"org": "no-such-org", "platform": "github", "handle": "whatever"},
    ]
    errs = validate_sources(d)
    assert any("no-such-org" in e and "no sources/organizations" in e for e in errs)


# --- model families (sources/model_families.yaml) -----------------------------------

def test_model_family_duplicate_pattern_is_a_hard_error():
    d = _fixture()
    d["model_families"]["families"] = [
        {"pattern": "llama-*", "product": "llama", "decided_in": "#1", "note": "x" * 20},
        {"pattern": "llama-*", "product": "filler-a", "decided_in": "#2", "note": "y" * 20},
    ]
    errs = validate_sources(d)
    assert any("llama-*" in e and "claimed by both" in e for e in errs)


def test_model_family_pattern_must_match_its_own_product():
    d = _fixture()
    d["model_families"]["families"] = [
        {"pattern": "llama-*", "product": "filler-a", "decided_in": "#1", "note": "x" * 20},
    ]
    errs = validate_sources(d)
    assert any("does not match its own product" in e for e in errs)


def test_model_family_overlap_is_a_warning_not_an_error():
    from build.validate import model_family_overlap_warnings

    d = _fixture()
    d["model_families"]["families"] = [
        {"pattern": "llama-*", "product": "llama", "decided_in": "#1", "note": "x" * 20},
    ]
    # One family alone never warns -- overlap needs a second, different-product pattern.
    assert model_family_overlap_warnings(d["model_families"]) == []
    assert validate_sources(d) == []


def test_model_family_overlapping_prefixes_warn():
    from build.validate import model_family_overlap_warnings

    families = {
        "families": [
            {"pattern": "deepseek-*", "product": "deepseek", "decided_in": "#1", "note": "x" * 20},
            {
                "pattern": "deepseek-coder-*",
                "product": "deepseek-coder",
                "decided_in": "#2",
                "note": "y" * 20,
            },
        ]
    }
    warnings = model_family_overlap_warnings(families)
    assert len(warnings) == 1
    assert "deepseek-*" in warnings[0] and "deepseek-coder-*" in warnings[0]


# --- load_sources tolerates an older tree, but the real repo must never be one -------

def test_model_families_and_org_handles_files_exist_in_the_repo():
    """`build/check_corpus_diff.py` runs `load_sources` against a checkout of a BASE commit to
    semantic-diff a PR's output against what main would produce -- and `load_sources` now
    tolerates that older tree having no `sources/model_families.yaml` or
    `sources/org_handles.yaml` at all, so a missing file loads as empty rather than raising
    (see `_load_optional_yaml`). That tolerance must never extend to the real repo: if either
    file were deleted from main, CI's `validate` job would still pass, silently losing every
    declared handle and family. This test is what makes that impossible."""
    assert (ROOT / "sources" / "model_families.yaml").exists()
    assert (ROOT / "sources" / "org_handles.yaml").exists()


def test_load_sources_tolerates_a_tree_with_no_model_families_or_org_handles_file(tmp_path):
    """An older tree (a `.ccd-worktree/` base checkout from before these files existed) must
    still serialize -- `load_sources` returns the empty-but-valid document for each, not an
    exception."""
    sources = tmp_path / "sources"
    for name in ("organizations", "categories", "rubrics", "products", "scores", "registry"):
        (sources / name).mkdir(parents=True)
    (sources / "taxonomy.yaml").write_text("arcs: []\n")
    # Deliberately no model_families.yaml or org_handles.yaml.

    data = load_sources(tmp_path)
    assert data["model_families"] == {"version": 1, "families": []}
    assert data["org_handles"] == {"version": 1, "handles": []}
    # And the real files load as themselves when present, exercised together so the two
    # branches of `_load_optional_yaml` (absent vs present) are both covered by this pair.
    real = load_sources(ROOT)
    assert real["model_families"]["families"], "the real corpus must not load as empty"
    assert real["org_handles"]["handles"], "the real corpus must not load as empty"
