"""Per-product-type recipe resolution.

A mixed-type category (safeguards: 9 models, 17 software) declares
`extends: {model: model, software: software}`. Everything else keeps
`extends: <name>` and resolves exactly as before.
"""

from build.rubrics import recipe_for, resolve_recipe, resolve_recipe_variants

SHARED = {
    "software": {"openness": {"formula": [{"otherwise": {"score": 1, "class": "closed"}}]}},
    "model": {"openness": {"formula": [{"otherwise": {"score": 5, "class": "open_source"}}]}},
}


def test_string_extends_resolves_to_star():
    category = {"scoring_recipe": {"extends": "software", "version": 1}}
    variants, errors = resolve_recipe_variants(category, SHARED)
    assert errors == []
    assert set(variants) == {"*"}
    assert variants["*"]["openness"] == SHARED["software"]["openness"]
    assert variants["*"]["version"] == 1  # category keys ride along


def test_no_recipe_resolves_to_empty():
    assert resolve_recipe_variants({}, SHARED) == ({}, [])


def test_mapping_extends_resolves_per_type():
    category = {"scoring_recipe": {"extends": {"model": "model", "software": "software"}}}
    variants, errors = resolve_recipe_variants(category, SHARED)
    assert errors == []
    assert set(variants) == {"model", "software"}
    assert variants["model"]["openness"] == SHARED["model"]["openness"]
    assert variants["software"]["openness"] == SHARED["software"]["openness"]


def test_mapping_extends_unknown_ladder_is_an_error():
    category = {"scoring_recipe": {"extends": {"model": "nonexistent"}}}
    variants, errors = resolve_recipe_variants(category, SHARED)
    assert variants == {}
    assert len(errors) == 1 and "nonexistent" in errors[0]


def test_recipe_for_star_covers_every_type():
    variants, _ = resolve_recipe_variants({"scoring_recipe": {"extends": "software"}}, SHARED)
    recipe, why = recipe_for(variants, "model")
    assert recipe is not None and why is None


def test_recipe_for_missing_type_returns_reason():
    variants, _ = resolve_recipe_variants(
        {"scoring_recipe": {"extends": {"model": "model"}}}, SHARED
    )
    recipe, why = recipe_for(variants, "dataset")
    assert recipe is None
    assert "dataset" in why and "model" in why


def test_resolve_recipe_rejects_mapping_extends():
    category = {"scoring_recipe": {"extends": {"model": "model"}}}
    recipe, errors = resolve_recipe(category, SHARED)
    assert recipe is None
    assert errors and "resolve_recipe_variants" in errors[0]
