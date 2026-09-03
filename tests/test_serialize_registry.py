"""Tests for the registry serializer.

The registry is the identity layer — what exists — so these tests concentrate on
the two things that would silently corrupt downstream joins: identifier parsing
and reference integrity.
"""

from build.serialize_registry import ROOT, TABLES, artifact_id, build_registry, category_layers
from build.validate import load_sources


def _sources(products=None, organizations=None, categories=None, taxonomy=None):
    return {
        "products": products or {},
        "organizations": organizations or {},
        "categories": categories or {},
        "taxonomy": taxonomy or {"arcs": []},
    }


def test_artifact_id_reduces_urls_to_api_identifiers():
    # github ids keep their declared casing -- registry.product_artifacts is joined against
    # signal tables on raw equality, so `artifact_id` must not rewrite it. Comparisons that
    # need case-insensitivity go through `identity.fold_for_proposal`, not this function.
    assert artifact_id("github", "https://github.com/allenai/OLMo") == "allenai/OLMo"
    assert artifact_id("github", "https://github.com/allenai/OLMo/") == "allenai/OLMo"
    assert (
        artifact_id("huggingface_dataset", "https://huggingface.co/datasets/allenai/c4")
        == "allenai/c4"
    )
    assert (
        artifact_id("huggingface_model", "https://huggingface.co/allenai/Olmo-3-1025-7B")
        == "allenai/Olmo-3-1025-7B"
    )
    assert artifact_id("pypi", "https://pypi.org/project/accelerate/") == "accelerate"


def test_artifact_id_rejects_org_level_github_urls():
    """An org page names no repo, so it cannot be measured as one."""
    assert artifact_id("github", "https://github.com/arduino") is None
    assert artifact_id("github", "https://github.com/lmstudio-ai") is None


def test_huggingface_model_pattern_does_not_swallow_datasets():
    assert artifact_id("huggingface_model", "https://huggingface.co/datasets/allenai/c4") is None


def test_category_layer_is_derived_from_the_arc():
    taxonomy = {
        "arcs": [
            {"name": "Model components", "layer": "model_components", "categories": ["base"]},
            {"name": "Infrastructure", "layer": "infrastructure", "categories": ["deployment"]},
        ]
    }
    layers = category_layers(taxonomy)
    assert layers["base"] == ("Model components", "model_components")
    assert layers["deployment"] == ("Infrastructure", "infrastructure")


def test_category_layer_accepts_lifecycle_entries():
    taxonomy = {
        "arcs": [
            {
                "name": "Infrastructure",
                "layer": "infrastructure",
                "categories": [{"name": "storage", "status": "preliminary"}],
            }
        ]
    }
    assert category_layers(taxonomy)["storage"] == ("Infrastructure", "infrastructure")


def test_membership_is_inverted_into_join_tables():
    sources = _sources(
        products={"olmo": {"display_name": "OLMo", "type": "model"}},
        organizations={"ai2": {"display_name": "Ai2", "type": "nonprofit", "products": ["olmo"]}},
        categories={"base": {"display_name": "Base", "weights": {}, "products": ["olmo"]}},
        taxonomy={"arcs": [{"name": "Model components", "layer": "model_components", "categories": ["base"]}]},
    )
    tables, errors, warnings = build_registry(sources)
    assert errors == []
    assert warnings == []
    assert tables["product_categories"] == [{"product_slug": "olmo", "category_slug": "base"}]
    assert tables["product_organizations"] == [{"product_slug": "olmo", "org_slug": "ai2"}]


def test_dangling_references_are_errors():
    sources = _sources(
        products={},
        organizations={"ai2": {"products": ["ghost"]}},
        categories={"base": {"weights": {}, "products": ["ghost"]}},
        taxonomy={"arcs": [{"name": "A", "layer": "a", "categories": ["base"]}]},
    )
    _, errors, _ = build_registry(sources)
    assert any("unknown product 'ghost'" in e for e in errors)


def test_orphan_products_are_errors():
    sources = _sources(
        products={"lonely": {"display_name": "Lonely", "type": "software"}},
    )
    _, errors, _ = build_registry(sources)
    assert any("'lonely' is in no category" in e for e in errors)
    assert any("'lonely' has no organization" in e for e in errors)


def test_category_outside_every_arc_is_an_error():
    sources = _sources(categories={"floating": {"weights": {}, "products": []}})
    _, errors, _ = build_registry(sources)
    assert any("'floating' sits in no arc" in e for e in errors)


def test_unaddressable_artifact_is_a_warning_not_an_error():
    """Coverage is lost but no join breaks, and the fix is a curation decision."""
    sources = _sources(
        products={"lm-studio": {"type": "software", "github": [{"url": "https://github.com/lmstudio-ai"}]}},
        organizations={"lms": {"products": ["lm-studio"]}},
        categories={"ui": {"weights": {}, "products": ["lm-studio"]}},
        taxonomy={"arcs": [{"name": "Product / UX", "layer": "product_ux", "categories": ["ui"]}]},
    )
    tables, errors, warnings = build_registry(sources)
    assert errors == []
    assert any("names no repo" in w for w in warnings)
    assert tables["product_artifacts"] == []


def test_shared_display_name_is_a_warning_naming_both_products_and_categories():
    """Slugs are unique because they are filenames, so nothing caught two products
    wearing one label. They render as two identical entries and a reader cannot tell
    whether the map is double counting. The warning has to name the categories,
    because base-vs-finetuned is the pair that is usually one product entered twice
    while two categories on the same layer is usually two real surfaces."""
    sources = _sources(
        products={
            "nemotron-3": {"type": "model", "display_name": "Nemotron 3"},
            "nemotron-3-nvidia": {"type": "model", "display_name": "Nemotron 3"},
        },
        organizations={"nvidia": {"products": ["nemotron-3", "nemotron-3-nvidia"]}},
        categories={
            "base_pretrained": {"weights": {}, "products": ["nemotron-3"]},
            "finetuned_chat": {"weights": {}, "products": ["nemotron-3-nvidia"]},
        },
        taxonomy={
            "arcs": [
                {
                    "name": "Model",
                    "layer": "model",
                    "categories": ["base_pretrained", "finetuned_chat"],
                }
            ]
        },
    )
    _, errors, warnings = build_registry(sources)
    assert errors == [], "a collision must not fail the build; the fix is a curation call"
    hits = [w for w in warnings if "display_name" in w]
    assert len(hits) == 1, hits
    assert "'Nemotron 3'" in hits[0]
    for token in ("nemotron-3", "nemotron-3-nvidia", "base_pretrained", "finetuned_chat"):
        assert token in hits[0], f"{token!r} missing from {hits[0]!r}"


def test_distinct_display_names_produce_no_collision_warning():
    _, _, warnings = build_registry(_sources())
    assert [w for w in warnings if "display_name" in w] == []


def test_every_declared_table_is_populated_or_present():
    tables, _, _ = build_registry(_sources())
    assert set(tables) == set(TABLES)


def test_tail_products_serialize_without_becoming_head_products():
    sources = _sources(
        categories={"storage": {"display_name": "Storage", "weights": {}, "products": []}},
        taxonomy={
            "arcs": [
                {
                    "name": "Infrastructure",
                    "layer": "infrastructure",
                    "categories": [{"name": "storage", "status": "preliminary"}],
                }
            ]
        },
    )
    sources["registry"] = {
        "storage": {
            "category": "storage",
            "products": [
                {
                    "slug": "lancedb",
                    "display_name": "LanceDB",
                    "type": "software",
                    "org": "lancedb",
                    "github": "lancedb/lancedb",
                }
            ],
        }
    }
    tables, errors, _ = build_registry(sources)
    assert errors == []
    assert tables["products"] == []
    assert tables["tail_products"] == [
        {
            "slug": "lancedb",
            "display_name": "LanceDB",
            "product_type": "software",
            "org_slug": "lancedb",
            "category_slug": "storage",
            "artifact_kind": "github",
            "artifact_id": "lancedb/lancedb",
            "artifact_url": "https://github.com/lancedb/lancedb",
        }
    ]
    assert tables["categories"][0]["status"] == "preliminary"


def test_tail_row_with_only_crates_serializes_with_the_crate_id():
    """#365 let a crates-only tail row validate; it must not then vanish from tail_products."""
    sources = _sources(
        categories={"storage": {"display_name": "Storage", "weights": {}, "products": []}},
        taxonomy={
            "arcs": [
                {
                    "name": "Infrastructure",
                    "layer": "infrastructure",
                    "categories": [{"name": "storage", "status": "preliminary"}],
                }
            ]
        },
    )
    sources["registry"] = {
        "storage": {
            "category": "storage",
            "products": [
                {
                    "slug": "some-crate",
                    "display_name": "Some Crate",
                    "type": "software",
                    "org": "acme",
                    "crates": "some-crate",
                }
            ],
        }
    }
    tables, errors, _ = build_registry(sources)
    assert errors == []
    assert tables["tail_products"] == [
        {
            "slug": "some-crate",
            "display_name": "Some Crate",
            "product_type": "software",
            "org_slug": "acme",
            "category_slug": "storage",
            "artifact_kind": "crates",
            "artifact_id": "some-crate",
            "artifact_url": "https://crates.io/crates/some-crate",
        }
    ]


def test_real_sources_serialize_without_structural_errors():
    from pathlib import Path

    from build.validate import load_sources

    root = Path(__file__).resolve().parents[1]
    tables, errors, _ = build_registry(load_sources(root))
    assert errors == [], f"registry has structural errors: {errors[:5]}"
    assert len(tables["products"]) == len(tables["product_categories"])
    assert len(tables["products"]) == len(tables["product_organizations"])


def test_arxiv_ids_normalize_from_every_form():
    """URL, bare id, arxiv: prefix and version suffix all reduce to the bare id,
    so the DOI is derivable as 10.48550/arXiv.<id> without further parsing."""
    assert artifact_id("arxiv", "https://arxiv.org/abs/2110.14168") == "2110.14168"
    assert artifact_id("arxiv", "https://arxiv.org/pdf/2009.03300v3") == "2009.03300"
    assert artifact_id("arxiv", "arxiv:1803.05457") == "1803.05457"
    assert artifact_id("arxiv", "2311.12022") == "2311.12022"


def test_arxiv_rejects_non_identifiers():
    assert artifact_id("arxiv", "https://arxiv.org/abs/not-an-id") is None
    assert artifact_id("arxiv", "") is None


def test_arxiv_artifacts_serialize_like_any_other_kind():
    sources = _sources(
        products={
            "gsm8k": {
                "display_name": "GSM8K",
                "type": "dataset",
                "arxiv": [{"url": "https://arxiv.org/abs/2110.14168"}],
            }
        },
        organizations={"openai": {"products": ["gsm8k"]}},
        categories={"bench": {"weights": {}, "products": ["gsm8k"]}},
        taxonomy={"arcs": [{"name": "Model components", "layer": "model_components", "categories": ["bench"]}]},
    )
    tables, errors, _ = build_registry(sources)
    assert errors == []
    assert tables["product_artifacts"] == [
        {
            "product_slug": "gsm8k",
            "product_type": "dataset",
            "artifact_kind": "arxiv",
            "artifact_id": "2110.14168",
            "artifact_url": "https://arxiv.org/abs/2110.14168",
        }
    ]


def test_resolution_ledger_table_has_one_row_per_ruling():
    tables, errors, _ = build_registry(_sources())
    rows = tables["resolution_ledger"]
    assert not errors
    keys = [(r["artifact_kind"], r["artifact_id"], r["relation"]) for r in rows]
    assert len(keys) == len(set(keys))
    assert all(r["relation"] in ("product_equivalence", "product_membership") for r in rows)


def test_product_aliases_table_matches_the_payload_alias_map():
    sources = load_sources(ROOT)
    tables, _, _ = build_registry(sources)
    from build.serialize import _aliases

    from build.validate import published_products

    published = published_products(sources.get("taxonomy") or {}, sources["categories"])
    payload_aliases = _aliases(
        sources["products"], sources["organizations"], published=published, org_slugs=set()
    )["products"]
    assert {(r["alias"], r["product_slug"]) for r in tables["product_aliases"]} == set(
        payload_aliases.items()
    )
