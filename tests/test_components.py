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

    Reads keys via `components_of`, not `split_components` directly on the raw field:
    `components_of` reads either shape, while a migrated record's `components` is a dict
    and handing that straight to `split_components` (which iterates its argument
    character by character) silently yields no keys at all rather than erroring. Left
    that way, this test's coverage would have shrunk to nothing as the migration
    proceeded, without ever failing loudly.
    """
    from build.check_rubric import components_of

    root = Path(__file__).resolve().parents[1]
    offenders = []
    inspected = 0
    for path in sorted((root / "sources" / "scores").glob("*.yaml")):
        openness = (yaml.safe_load(path.read_text()) or {}).get("openness") or {}
        for key in components_of(openness):
            inspected += 1
            if " " in key or "(" in key or ")" in key:
                offenders.append(f"{path.stem}: {key!r}")

    # A floor, not an exact count, for the same reason as the sibling equivalence test in
    # test_serialize_rubric.py: the corpus only grows as products are scored, so more keys
    # inspected than this is ordinary curation. This guard is here because `offenders == []`
    # alone cannot tell "nothing to flag" from "nothing was inspected" — which is exactly
    # how this test passed green while checking zero keys from every migrated record before
    # the `components_of` fix above.
    assert inspected >= 1_754, f"only {inspected} keys inspected; the corpus walk is broken"
    assert offenders == [], "phantom dimension keys minted from prose:\n  " + "\n  ".join(offenders)


def test_structure_splits_a_keyed_clause_into_value_and_detail():
    from build.check_rubric import structure

    assert structure("weights:open(downloadable on HF);data:closed") == {
        "weights": {"value": "open", "detail": "downloadable on HF"},
        "data": {"value": "closed"},
    }


def test_structure_keeps_a_keyless_clause_as_free_text():
    """A keyless clause has no key to sit under, and dropping it deletes evidence.

    `split_components` discards it silently and `check_recipe`'s blocking test only ever
    sees clauses that survived that discard — which is why the gate reports 0 blocking
    clauses while 221 of them go unread.
    """
    from build.check_rubric import structure

    assert structure("source:public;no feature-gated core") == {
        "source": {"value": "public"},
        "free_text": ["no feature-gated core"],
    }


def test_structure_records_raw_when_value_and_detail_cannot_round_trip():
    """Three clause shapes that split_value cannot reverse; `raw` is what keeps them.

    `rows:169,352` is the sharpest: the first comma is taken as the value/detail boundary,
    so a row count is cut in half. That is happening today, with no migration involved.
    """
    from build.check_rubric import structure

    assert structure("rows:169,352")["rows"] == {"value": "169", "detail": "352", "raw": "169,352"}
    assert structure("license:Apache-2.0(OSI) for the framework")["license"]["raw"] == (
        "Apache-2.0(OSI) for the framework"
    )
    assert structure("toolchain:open (fully open (MaixPy, Apache-2.0))")["toolchain"]["raw"] == (
        "open (fully open (MaixPy, Apache-2.0))"
    )


def test_components_of_reads_both_shapes_identically():
    """Both shapes are on main at once while the corpus migrates in batches."""
    from build.check_rubric import components_of, split_components, structure

    text = "weights:open(on HF);data:closed;rows:169,352;no feature-gated core"
    assert components_of({"components": text}) == split_components(text)
    assert components_of({"components": structure(text)}) == split_components(text)


def test_structure_round_trips_every_recorded_components_string():
    """The corpus-wide guarantee: no reader sees a different string after the migration.

    Byte-exact, not whitespace-insensitive. A normalizing comparison would let 108 entries
    that differ only by a space before the opening paren pass while quietly changing the
    detail text the warehouse evidence rows carry.
    """
    from build.check_rubric import recompose, split_components, structure

    root = Path(__file__).resolve().parents[1]
    failures = []
    walked = 0
    for path in sorted((root / "sources" / "scores").glob("*.yaml")):
        block = (yaml.safe_load(path.read_text()) or {}).get("openness") or {}
        components = block.get("components")
        if isinstance(components, dict):
            components = block.get("raw")
        if not isinstance(components, str) or not components:
            continue
        walked += 1
        if recompose(structure(components)) != split_components(components):
            failures.append(path.stem)

    # A floor, not an exact count, for the same reason as the sibling equivalence tests in
    # this file and in test_serialize_rubric.py: the corpus only grows as products are
    # scored, so more records walked than this is ordinary curation. `walked > 0` caught
    # total collapse but not a partial one — if a later change stripped `raw` from 400 of
    # 472 records, `walked` would drop to 72 and this test would pass having lost most of
    # its coverage, the same shrink-without-noticing failure the sibling tests were fixed
    # for. 472 is every record in the corpus today: phase 1a finished at 472 of 472
    # migrated, and check_components requires `raw` on every migrated record, so this walk
    # is now the full corpus rather than a subset of it.
    assert walked >= 472, f"only {walked} components strings walked; the corpus walk is broken"
    assert failures == [], f"structure/recompose does not round-trip: {failures}"


def test_check_components_flags_a_mapping_that_disagrees_with_its_raw(tmp_path):
    """A mangled migration parses, validates, and passes every other gate.

    Every reader takes the mapping at its word, so nothing else in the repo can tell a
    faithful migration from a lossy one. This gate can, and only because the original
    string is kept beside it.
    """
    from build.check_components import check

    scores = tmp_path / "sources" / "scores"
    scores.mkdir(parents=True)
    (scores / "good.yaml").write_text(yaml.safe_dump({"openness": {
        "components": {"weights": {"value": "open", "detail": "on HF"}},
        "raw": "weights:open(on HF)",
    }}, sort_keys=False))
    (scores / "mangled.yaml").write_text(yaml.safe_dump({"openness": {
        "components": {"weights": {"value": "closed"}},
        "raw": "weights:open(on HF)",
    }}, sort_keys=False))

    failures = check(tmp_path)
    assert len(failures) == 1
    assert "mangled.weights" in failures[0]


def test_check_components_requires_raw_on_a_migrated_record_and_forbids_it_otherwise(tmp_path):
    from build.check_components import check

    scores = tmp_path / "sources" / "scores"
    scores.mkdir(parents=True)
    (scores / "no-raw.yaml").write_text(yaml.safe_dump({"openness": {
        "components": {"weights": {"value": "open"}},
    }}, sort_keys=False))
    (scores / "stale-raw.yaml").write_text(yaml.safe_dump({"openness": {
        "components": "weights:open", "raw": "weights:closed",
    }}, sort_keys=False))

    failures = sorted(check(tmp_path))
    assert len(failures) == 2
    assert "no openness.raw" in failures[0]
    assert "still a string" in failures[1]


def test_check_components_flags_a_dropped_keyless_clause(tmp_path):
    """Dropping a keyless clause deletes evidence with every other gate green.

    `check_recipe`'s blocking test only ever sees clauses that survived
    `split_components`, which discards these before it runs — which is why it reports 0
    blocking clauses while 221 of them go unread.
    """
    from build.check_components import check

    scores = tmp_path / "sources" / "scores"
    scores.mkdir(parents=True)
    (scores / "dropped.yaml").write_text(yaml.safe_dump({"openness": {
        "components": {"source": {"value": "public"}},
        "raw": "source:public;no feature-gated core",
    }}, sort_keys=False))

    failures = check(tmp_path)
    assert len(failures) == 1
    assert "free_text" in failures[0]


def test_check_components_rejects_a_string_shaped_record(tmp_path):
    """Phase 1a finished at 472 of 472 records migrated to the mapping shape. Before this,
    a string-shaped `components` was silently skipped rather than flagged, so a new record
    scored from a stale template — or a hand-written string — would pass every gate and
    quietly return the corpus to mixed shape.
    """
    from build.check_components import check

    scores = tmp_path / "sources" / "scores"
    scores.mkdir(parents=True)
    (scores / "reverted.yaml").write_text(yaml.safe_dump({"openness": {
        "components": "license:MIT(OSI);source:public",
    }}, sort_keys=False))

    failures = check(tmp_path)
    assert len(failures) == 1
    assert "still a string" in failures[0]


def test_schema_rejects_a_string_shaped_components():
    """The schema must state the same rule check_components enforces: the mapping is the
    only accepted shape, so a new string-shaped record fails validation rather than being
    silently accepted by a `oneOf(string | mapping)` left over from the migration.
    """
    import json

    import jsonschema

    root = Path(__file__).resolve().parents[1]
    schema = json.loads((root / "docs/schemas/score.schema.json").read_text())
    doc = yaml.safe_load((root / "sources/scores/mastra.yaml").read_text())

    jsonschema.validate(doc, schema)

    doc["openness"]["components"] = "license:MIT(OSI);source:public"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(doc, schema)


def test_components_string_returns_the_flat_string_unchanged():
    """Branch 1: `components` is already a string, so there is nothing to recompose.

    This is the only branch the corpus exercises today (all 472 files), and it is also
    exactly what the payload emitted before this migration touched serialize.py — the
    property this test protects is that an unmigrated file's payload output is untouched.
    """
    from build.check_rubric import components_string

    openness = {"components": "weights:open(on HF);license:MIT"}
    assert components_string(openness) == "weights:open(on HF);license:MIT"


def test_components_string_prefers_the_raw_sibling_over_recomposing():
    """Branch 2: a migrated record's `raw` wins even though `components` is also present.

    `raw` is the verbatim pre-migration string, so preferring it is what makes the payload
    byte-identical to what it was before the file moved to the structured shape. If this
    preferred the recompose path instead, a migration could change the payload's `Components`
    text without moving a score, which is exactly the silent drift `raw` exists to catch.
    """
    from build.check_rubric import components_string

    openness = {
        "components": {"weights": {"value": "closed"}},  # deliberately disagrees with raw
        "raw": "weights:open(on HF);license:MIT",
    }
    assert components_string(openness) == "weights:open(on HF);license:MIT"


def test_components_string_recomposes_a_mapping_with_no_raw_sibling():
    """Branch 3: a structured mapping with no `raw` to fall back on.

    Every file Tasks 4-9 migrate hits this exact branch until `raw` is added alongside the
    mapping (or, per `check_components`'s invariant, never — a mapping with no `raw` is a
    gate failure, but `components_string` itself must still degrade sensibly if called on
    one). Exercises all three recompose cases in one mapping so a change to any of them
    fails this test: a keyed entry with a `detail` (parenthesized back on), a keyed entry
    with no `detail` (bare value), and a keyless `free_text` clause.

    `free_text` clauses are NOT restored into the joined string: `recompose` only walks
    keyed entries, so a keyless clause that survived structuring is dropped from this
    fallback's output. That is current, deliberate behavior of `recompose` (it has no key to
    rejoin the clause under) and this test pins it down rather than leaving it to be
    discovered by a migrated file's payload going quietly shorter than its `raw`.
    """
    from build.check_rubric import FREE_TEXT, components_string

    openness = {
        "components": {
            "weights": {"value": "open", "detail": "on HF"},
            "license": {"value": "MIT"},
            FREE_TEXT: ["no feature-gated core"],
        },
    }
    assert components_string(openness) == "weights:open(on HF);license:MIT"
