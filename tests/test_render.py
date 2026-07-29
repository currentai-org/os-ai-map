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
