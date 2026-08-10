"""Tests for the block-safe components rewriter.

The load-bearing test is `test_rewrites_a_value_folded_across_three_lines`. A single-line
fixture passes against a naive `^  components: (.*)$` substitution by accident, so a
single-line test proves nothing about the bug this module exists to prevent. Every fixture
here that matters folds.
"""

from pathlib import Path

import pytest
import yaml

from build.components import field_span, format, parse, render, rewrite, set_field

# `granite-code-instruct`'s real components value, which folds across four lines in the
# repo. Real rather than invented on purpose: what makes a value fold is spaces inside the
# parentheticals, and a hand-written fixture is liable to have too few of them and quietly
# stop folding. `test_the_folded_fixture_really_folds` asserts it still does.
GRANITE = (
    "weights:open(Apache-2.0,on HF);code:partial(inference + fine-tune sample scripts via "
    "Dolomite Engine; no full training pipeline in repo);data:described_not_released("
    "CommitPackFT/MathInstruct/Glaive/HelpSteer/Open-Platypus named in card but processed corpus "
    "not redistributable);post-training-data:described(SFT mixture named, not released);"
    "paper:open(arXiv 2405.04324);model_card:open;license:Apache-2.0(OSI)"
)

FOLDED_THREE = f"""product: granite-code-instruct
openness:
  score: 4
  class: open_weights
  components: {GRANITE}
  confidence: high
  note: 'Open-core in the LangGraph shape: the framework itself is a real OSI license.'
  last_verified: '2026-07-29'
  sources:
  - url: https://github.com/mastra-ai/mastra/blob/main/LICENSE.md
    shows: LICENSE.md scopes the carve-out to `ee/` directories
    accessed: '2026-07-29'
adoption:
  level: 4
  reach: 1M-10M
capability:
  score: 4
  basis: feature_matrix
"""

SINGLE_LINE = """product: olmo
openness:
  score: 5
  class: open_source
  components: weights:open;data:open;license:Apache-2.0(OSI)
  confidence: high
adoption:
  level: 4
capability:
  score: 4
  basis: benchmark
"""


def _fold(text: str) -> str:
    """Re-emit the fixture so `components` really is folded, not just long."""
    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.startswith("  components:"):
            value = yaml.safe_load(text)["openness"]["components"]
            return "".join(lines[:index] + render("components", value) + lines[index + 1 :])
    raise AssertionError("fixture has no components field")


def test_the_folded_fixture_really_folds_across_three_lines():
    """Guards the guard. If this fixture stopped folding, every test below would still
    pass while testing nothing, which is exactly the accident being defended against."""
    text = _fold(FOLDED_THREE)
    lines = text.splitlines(keepends=True)
    start, end = field_span(lines, (1, len(lines)), "components")
    assert end - start >= 3, text


def test_rewrites_a_value_folded_across_three_lines():
    text = _fold(FOLDED_THREE)
    new = set_field(text, "license:MIT(OSI);source:public;core-gated:ungated")
    parsed = yaml.safe_load(new)
    assert parsed["openness"]["components"] == "license:MIT(OSI);source:public;core-gated:ungated"


def test_a_fold_leaves_no_continuation_line_behind():
    """The actual corruption: a regex replaces line one and the old tail survives, so the
    parsed value ends with a fragment of the value that was supposed to be replaced."""
    text = _fold(FOLDED_THREE)
    parsed = yaml.safe_load(set_field(text, "source:closed"))
    assert parsed["openness"]["components"] == "source:closed"
    assert "training pipeline" not in parsed["openness"]["components"]


def test_neighboring_fields_survive_a_fold_rewrite():
    text = _fold(FOLDED_THREE)
    before = yaml.safe_load(text)
    after = yaml.safe_load(set_field(text, "source:public;core-gated:ungated"))
    for key in ("score", "class", "confidence", "note", "last_verified", "sources"):
        assert after["openness"][key] == before["openness"][key], key
    assert after["adoption"] == before["adoption"]
    assert after["capability"] == before["capability"]
    assert after["product"] == before["product"]


def test_single_line_value_also_rewrites():
    parsed = yaml.safe_load(set_field(SINGLE_LINE, "weights:open;data:closed"))
    assert parsed["openness"]["components"] == "weights:open;data:closed"


def test_a_value_needing_quotes_round_trips():
    """`vellum` records `vellum-assistant: gateway+clients`, and a bare `: ` inside a plain
    scalar changes the parse. The dumper has to quote it and does."""
    value = "license:MIT(OSI);source:public+full-agent(vellum-assistant: gateway+clients)"
    parsed = yaml.safe_load(set_field(SINGLE_LINE, value))
    assert parsed["openness"]["components"] == value


def test_a_long_value_folds_at_its_spaces():
    value = format({f"dimension-{n}": f"value {n} with some detail" for n in range(20)})
    text = set_field(SINGLE_LINE, value)
    assert len(text.splitlines()) > len(SINGLE_LINE.splitlines())
    assert yaml.safe_load(text)["openness"]["components"] == value


def test_a_long_value_with_no_spaces_stays_on_one_line():
    """YAML folds at spaces, so a `k:v;k:v` run with none cannot be folded and correctly
    is not. Worth pinning: it means line length alone never tells you whether a value
    folds, which is why `field_span` tests indentation instead of guessing from width."""
    value = format({f"dimension-{n}": f"value-{n}-detail" for n in range(20)})
    text = set_field(SINGLE_LINE, value)
    assert len(text.splitlines()) == len(SINGLE_LINE.splitlines())
    assert yaml.safe_load(text)["openness"]["components"] == value


def test_rewriting_is_idempotent():
    once = set_field(_fold(FOLDED_THREE), "source:public;core-gated:gated")
    assert set_field(once, "source:public;core-gated:gated") == once


def test_missing_axis_raises():
    with pytest.raises(ValueError, match="no top-level"):
        set_field(SINGLE_LINE, "x:y", axis="hardware")


def test_missing_field_raises_rather_than_inventing_one():
    text = SINGLE_LINE.replace("  components: weights:open;data:open;license:Apache-2.0(OSI)\n", "")
    with pytest.raises(ValueError, match="no 'components' field"):
        set_field(text, "x:y")


def test_rewrite_writes_the_file_and_reports_change(tmp_path: Path):
    path = tmp_path / "mastra.yaml"
    path.write_text(_fold(FOLDED_THREE))
    assert rewrite(path, "source:public;core-gated:ungated") is True
    assert yaml.safe_load(path.read_text())["openness"]["components"] == (
        "source:public;core-gated:ungated"
    )
    assert rewrite(path, "source:public;core-gated:ungated") is False


def test_parse_and_format_round_trip():
    value = "weights:open(Apache-2.0, safetensors);data:closed;license:MIT(OSI)"
    assert format(parse(value)) == value


def test_parse_is_paren_aware():
    """One parser, shared with check_rubric: a `;` inside parentheses is not a separator."""
    assert parse("license:Apache-2.0(OSI; see LICENSE);source:public") == {
        "license": "Apache-2.0(OSI; see LICENSE)",
        "source": "public",
    }


def test_every_real_score_file_round_trips():
    """The corpus is the fixture. Setting each file's components to its own current value
    must be a no-op, which exercises the span logic against all 277 folded fields."""
    root = Path(__file__).resolve().parents[1]
    checked = 0
    for path in sorted((root / "sources" / "scores").glob("*.yaml")):
        text = path.read_text()
        current = ((yaml.safe_load(text) or {}).get("openness") or {}).get("components")
        if current is None:
            continue
        checked += 1
        assert yaml.safe_load(set_field(text, current)) == yaml.safe_load(text), path.name
    assert checked > 400


def test_the_naive_regex_corrupts_the_same_fixture():
    """Not a test of this module, but of the substitution it replaces.

    Pinned so the reason the module exists cannot be argued away later: the same edit done
    with a line regex parses fine and yields a value with the old tail spliced onto it.
    """
    import re

    text = _fold(FOLDED_THREE)
    naive = re.sub(r"^  components: .*$", "  components: source:closed", text, count=1, flags=re.M)
    corrupted = yaml.safe_load(naive)["openness"]["components"]
    # The old value's tail survives and is spliced onto the new one mid-key, so the parsed
    # result reads as a key called `source` whose value trails off into the previous value.
    assert corrupted.startswith("source:closed Engine; no full training pipeline")
    assert "license:Apache-2.0(OSI)" in corrupted


# --- the document-level variant, for sources/products/*.yaml ---

PRODUCT = """name: widget
display_name: Widget
type: software
description: A thing that does a thing, and wraps onto a second line because the corpus wraps
  at about a hundred and five columns rather than eighty.
github:
- url: https://github.com/org/widget
pypi:
- url: https://pypi.org/project/widget
comments: Verified 2026-08-08 via GitHub.
"""


def test_a_top_level_field_is_replaced_without_touching_its_neighbors():
    from build.components import set_document_field

    out = set_document_field(PRODUCT, "description", "A shorter thing.")
    after, before = yaml.safe_load(out), yaml.safe_load(PRODUCT)
    assert after["description"] == "A shorter thing."
    assert {k: v for k, v in after.items() if k != "description"} == {
        k: v for k, v in before.items() if k != "description"
    }


def test_a_list_item_in_column_zero_is_not_a_sibling_key():
    """`github:` is followed by `- url:` at indent 0. Treating that as the next key would end
    the span early and splice the replacement above the list."""
    from build.components import set_document_field

    out = set_document_field(PRODUCT, "github", [{"url": "https://github.com/org/renamed"}])
    after = yaml.safe_load(out)
    assert after["github"] == [{"url": "https://github.com/org/renamed"}]
    assert after["pypi"] == [{"url": "https://pypi.org/project/widget"}]
    assert out.count("github:") == 1


def test_the_last_field_can_be_replaced():
    from build.components import set_document_field

    out = set_document_field(PRODUCT, "comments", "Verified 2026-08-09 via the LICENSE body.")
    assert yaml.safe_load(out)["comments"] == "Verified 2026-08-09 via the LICENSE body."


def test_a_colon_in_the_value_is_the_dumper_problem():
    """The motivating hazard one level up, and identical here: a bare `: ` changes the parse."""
    from build.components import set_document_field

    value = "TRL post-trains models through Trainer classes: SFT, DPO, GRPO."
    out = set_document_field(PRODUCT, "description", value)
    assert yaml.safe_load(out)["description"] == value


def test_a_missing_field_raises_rather_than_appending():
    from build.components import set_document_field

    with pytest.raises(ValueError, match="no top-level"):
        set_document_field(PRODUCT, "strapline", "nope")


def test_every_product_file_round_trips_through_its_own_description():
    """Setting a field to what it already holds must be a no-op across the whole corpus."""
    from build.components import set_document_field

    checked = 0
    root = Path(__file__).resolve().parents[1]
    for path in sorted((root / "sources" / "products").glob("*.yaml")):
        text = path.read_text()
        doc = yaml.safe_load(text)
        if not doc.get("description"):
            continue
        checked += 1
        assert yaml.safe_load(set_document_field(text, "description", doc["description"])) == doc, path.name
    assert checked > 400


def test_no_score_file_mints_a_phantom_dimension_key():
    """A components clause with no key must not produce a dimension.

    split_components splits each clause on its first ':' with no paren-awareness, so a
    keyless clause whose parenthetical contains a colon mints a key out of prose. That
    corrupts every corpus-wide key inventory and would carry into the structured form.
    A phantom key is recognizable: real dimension keys are short, lowercase, and contain
    no spaces or parentheses.
    """
    from build.check_rubric import split_components

    root = Path(__file__).resolve().parents[1]
    offenders = []
    for path in sorted((root / "sources" / "scores").glob("*.yaml")):
        components = (yaml.safe_load(path.read_text()).get("openness") or {}).get("components")
        if not components:
            continue
        for key in split_components(components):
            if " " in key or "(" in key or ")" in key:
                offenders.append(f"{path.stem}: {key!r}")

    assert offenders == [], "phantom dimension keys minted from prose:\n  " + "\n  ".join(offenders)
