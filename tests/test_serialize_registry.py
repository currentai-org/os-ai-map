"""Tests for the registry serializer.

The registry is the identity layer — what exists — so these tests concentrate on
the two things that would silently corrupt downstream joins: identifier parsing
and reference integrity.
"""

from build.serialize_registry import TABLES, artifact_id, build_registry, category_layers


def _sources(products=None, organizations=None, categories=None, taxonomy=None):
    return {
        "products": products or {},
        "organizations": organizations or {},
        "categories": categories or {},
        "taxonomy": taxonomy or {"arcs": []},
    }


def test_artifact_id_reduces_urls_to_api_identifiers():
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


def test_every_declared_table_is_populated_or_present():
    tables, _, _ = build_registry(_sources())
    assert set(tables) == set(TABLES)


def test_real_sources_serialize_without_structural_errors():
    from pathlib import Path

    from build.validate import load_sources

    root = Path(__file__).resolve().parents[1]
    tables, errors, _ = build_registry(load_sources(root))
    assert errors == [], f"registry has structural errors: {errors[:5]}"
    assert len(tables["products"]) == len(tables["product_categories"])
    assert len(tables["products"]) == len(tables["product_organizations"])
