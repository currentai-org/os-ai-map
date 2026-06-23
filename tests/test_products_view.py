"""Regression tests for the products-view notebook lookup engine.

The lookup tool (mode 1: "describe what you want to build") runs ``search()``
over every component and indexes ``CAT_KW`` by category id, both in the engine
cell and in the gap logic of the results cell. If a taxonomy category is missing
from ``CAT_KW``, selecting any user story raises ``KeyError`` and nothing renders
below the dropdown. These tests load the notebook's cells directly and exercise
that path so the regression cannot return silently.
"""
import importlib.util
from pathlib import Path

import pytest

NB = Path(__file__).resolve().parent.parent / "notebooks" / "products-view.py"


def _load_notebook():
    spec = importlib.util.spec_from_file_location("products_view_nb", NB)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def cells():
    nb = _load_notebook()
    _, data_defs = nb.data.run()
    _, gallery_defs = nb.gallery.run()
    _, engine_defs = nb.engine.run(
        CATS=data_defs["CATS"],
        COMPONENTS=data_defs["COMPONENTS"],
        STRUCTURAL_GAPS=gallery_defs["STRUCTURAL_GAPS"],
    )
    return {**data_defs, **gallery_defs, **engine_defs}


def test_cat_kw_covers_every_category(cells):
    missing = [c for c in cells["ORDER"] if c not in cells["CAT_KW"]]
    assert not missing, f"CAT_KW is missing taxonomy categories: {missing}"


def test_search_runs_over_all_components_for_every_preset(cells):
    search = cells["search"]
    for _story, query in cells["PRESETS"]:
        results = search(query, open_only=True)
        assert results, f"no components returned for preset query: {query!r}"


def test_gap_logic_indexes_cat_kw_for_every_category(cells):
    # Mirrors the `_weak` comprehension in the lookup_results cell, which does
    # CAT_KW[c] for every category in ORDER.
    CAT_KW, ORDER = cells["CAT_KW"], cells["ORDER"]
    qtok = {"chat", "agent", "rag"}
    weak = [c for c in ORDER if qtok & CAT_KW[c]]
    assert isinstance(weak, list)
