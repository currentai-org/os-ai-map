"""Tests for the notebook generator's handling of contributor-authored strings.

`build/render.py` writes `notebooks/ai-stack-map.py`, so a contributor string reaches
generated Python and generated HTML. Both were interpolated raw, which fails in two
different ways: a quote in a strapline closes a Python literal early and the notebook
stops parsing, and markup in a display name or description is interpreted by the browser
rather than shown.

The second failure was live rather than theoretical - `ornith`'s description contains a
literal `<think>`, which the browser swallowed as an unknown element, so the published
map silently dropped that word.

These are adversarial rather than round-trip tests: the input is what a contributor
plausibly writes, and the assertion is that the output survives it.
"""

from __future__ import annotations

import ast
import html

import pytest

from build.render import _build_straplines_literal

HOSTILE = [
    'the "open" frontier, not open source',        # the realistic one
    "it's a dog's breakfast",                      # apostrophes
    'a backslash \\ and a quote "',                # escape interaction
    "line\nbreak",                                 # newline inside a literal
    '</p><script>alert(1)</script>',               # markup
    "unicode — em dash and emoji ⭐",
]


@pytest.mark.parametrize("strapline", HOSTILE)
def test_strapline_literal_survives_hostile_input(strapline):
    """The generated dict literal must parse for any string a contributor can type."""
    literal = _build_straplines_literal(["cat"], {"cat": {"strapline": strapline}})
    parsed = ast.literal_eval(literal)
    assert parsed == {"cat": strapline}, "literal must round-trip the exact string"


def test_strapline_literal_is_valid_python_in_context():
    """Parsed the way render.py actually uses it, as a substituted assignment."""
    literal = _build_straplines_literal(
        ["a", "b"],
        {"a": {"strapline": 'quote " here'}, "b": {"strapline": "plain"}},
    )
    ast.parse(f"STRAPLINES = {literal}\n")


def test_strapline_literal_does_not_emit_a_bare_interpolated_quote():
    """The specific regression: `"{cid}": "{strap}"` produced `"a": "quote " here",`.

    Asserted on the shape rather than only on parseability, because a future edit could
    reintroduce raw interpolation for a string that happens to contain no quote and the
    parse test would pass.
    """
    literal = _build_straplines_literal(["a"], {"a": {"strapline": 'quote " here'}})
    assert '\\"' in literal or "'" in literal, (
        "a quote in the value must be escaped or the literal requoted, not emitted raw"
    )


@pytest.mark.parametrize("text", ['<think>', '<script>alert(1)</script>', 'a & b', '"q"'])
def test_html_escape_neutralizes_contributor_markup(text):
    """Documents the contract the generated notebook relies on.

    The four interpolation sites that carry contributor text - category label, category
    description, and product display name in two tables - wrap it in html.escape. This
    pins the property those sites depend on, so the escaping is not silently dropped
    while the call sites keep looking correct.
    """
    escaped = html.escape(str(text))
    assert "<" not in escaped and ">" not in escaped
    if "&" in text:
        assert "&amp;" in escaped


def test_the_order_tolerates_a_payload_that_names_a_category_sources_no_longer_has():
    """The committed payload lags sources between a merge and the bot's regeneration.

    Until 2026-09-17 a renamed or removed category made `_build_straplines_literal` raise
    KeyError at module scope, which is an import error, which takes this whole file down as a
    collection error rather than one readable failure. The window is unavoidable - the payload
    is bot-owned and regenerated after merge - so the renderer has to survive it.
    """
    from build.render import _build_straplines_literal

    cats = {"kept": {"strapline": "still here"}}
    order = [cid for cid in ["kept", "renamed-away"] if cid in cats]
    literal = _build_straplines_literal(order, cats)
    assert '"kept": "still here"' in literal
    assert "renamed-away" not in literal


# --- the depth ladder's unresolved sets (R-2026-11-08-a) ---------------------------------------


def _helpers_namespace(data: dict) -> dict:
    """The notebook's `helpers` cell's inner functions, executed against `data` with stub styles,
    so a row can be rendered without running marimo."""
    from build import render

    tree = ast.parse(render.NB)
    cell = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "helpers")
    inner = [n for n in cell.body if isinstance(n, ast.FunctionDef)]
    ns = {"_html": html, "C": _StubStyle(), "F": _StubStyle(), "DATA": data}
    exec(compile(ast.Module(body=inner, type_ignores=[]), "helpers", "exec"), ns)
    return ns


class _StubStyle(dict):
    def __missing__(self, key):
        return "x"


def test_an_unresolved_set_reads_unresolved_not_na():
    ns = _helpers_namespace({})
    cap = {"score": None, "basis": "evaluation_depth",
           "depth": {"status": "unresolved", "unresolved_reason_text": "no approved measurement model"}}
    cell = ns["capability_cell"](cap)
    assert ">unresolved</span>" in cell and 'title="no approved measurement model"' in cell
    assert "n/a" not in cell
    # A banded set draws its bars, and an abstention elsewhere keeps the generic n/a.
    assert "unresolved" not in ns["capability_cell"]({"score": 3, "depth": {"status": "provisional"}})
    assert "n/a" in ns["capability_cell"]({"score": None, "basis": "n/a"})


def test_the_eval_sets_summary_names_evaluation_depth():
    data = {"categories": {"evals": {"products": [{"type": "dataset",
                                                   "capability": {"basis": "evaluation_depth"}}]}}}
    summary = _helpers_namespace(data)["_cap_summary"]("evals")
    assert summary.startswith("evaluation depth") and "unresolved" in summary
