"""`components.context`: keyed clauses no ladder reads, recorded on purpose (#188).

The property everything here protects is that routing a key into or out of `context` is
invisible to every reader. `raw` does not change, `components_of` returns the same dict, so no
score, payload or evidence row can move. What `context` changes is what the gate can assert.
"""

from pathlib import Path

import pytest
import yaml

from build.check_components import check, context_failures
from build.check_rubric import (
    CONTEXT,
    FREE_TEXT,
    components_of,
    entries,
    recompose,
    route_context,
    split_components,
    structure,
    unread_keys,
)
from build.components import set_field

RECIPE = {
    "openness": {
        "dimensions": {
            "source": {"values": ["public", "closed"]},
            "core_gated": {"reads": ["core-gated", "self-host"], "values": ["gated", "ungated"]},
        },
        "license_tier": {"reads": ["license"]},
    }
}

RAW = (
    "license:Apache-2.0(OSI);source:public(the backend);service:optional(a hosted tier);"
    "core-gated:ungated;no feature-gated core;governance:Linux-Foundation(co-founded)"
)


def test_route_context_moves_exactly_the_unread_keys():
    routed = route_context(structure(RAW), RECIPE)

    assert list(routed) == ["license", "source", "core-gated", FREE_TEXT, CONTEXT]
    assert list(routed[CONTEXT]) == ["service", "governance"]
    assert routed[CONTEXT]["governance"] == {"value": "Linux-Foundation", "detail": "co-founded"}
    assert routed[FREE_TEXT] == ["no feature-gated core"]


def test_routing_is_invisible_to_every_reader():
    flat = structure(RAW)
    routed = route_context(flat, RECIPE)

    assert recompose(routed) == recompose(flat) == split_components(RAW)
    assert components_of({"components": routed}) == components_of({"components": flat})


def test_route_context_is_idempotent_and_moves_a_newly_read_key_back_out():
    routed = route_context(structure(RAW), RECIPE)
    assert route_context(routed, RECIPE) == routed

    # A ladder that starts reading `governance` must pull it out of context, not leave the
    # record calling read evidence "not scored".
    widened = {
        "openness": {
            **RECIPE["openness"],
            "dimensions": {**RECIPE["openness"]["dimensions"], "governance": {}},
        }
    }
    moved = route_context(routed, widened)
    assert "governance" in moved and list(moved[CONTEXT]) == ["service"]


def test_a_context_emptied_by_routing_disappears_rather_than_lingering_empty():
    routed = route_context(structure("license:MIT;service:hosted"), RECIPE)
    everything_read = {
        "openness": {
            **RECIPE["openness"],
            "dimensions": {**RECIPE["openness"]["dimensions"], "service": {}},
        }
    }
    assert CONTEXT not in route_context(routed, everything_read)


def test_entries_lifts_context_so_a_license_there_is_still_counted():
    # check_contradictions counts license keys through `entries`. `max` keeps its repository
    # license under context, and that second license is why the leg abstains on it.
    mapping = {
        "license": [{"name": "Modular-Community"}],
        CONTEXT: {"repo-license": [{"name": "Apache-2.0"}]},
    }
    assert list(entries(mapping)) == ["license", "repo-license"]


def test_the_gate_fails_an_unread_key_at_the_top_level():
    failures = context_failures("p", structure(RAW), RECIPE)
    assert len(failures) == 2
    assert all("dropped from the score silently" in f for f in failures)
    assert unread_keys(structure(RAW), RECIPE) == {"service", "governance"}


def test_the_gate_fails_a_read_key_hidden_in_context():
    mapping = {"license": [{"name": "MIT"}], CONTEXT: {"source": {"value": "public"}}}
    [failure] = context_failures("p", mapping, RECIPE)
    assert "p.context.source" in failure and "reads" in failure


def test_the_gate_fails_a_key_in_both_places_an_empty_context_and_a_reserved_name():
    both = {"service": {"value": "x"}, CONTEXT: {"service": {"value": "x"}}}
    assert any("both at the top level" in f for f in context_failures("p", both, RECIPE))

    assert context_failures("p", {CONTEXT: {}}, RECIPE) == [
        "p: context must be a non-empty mapping of key -> entry, or absent"
    ]
    for malformed in (None, ["service:x"]):
        # Reported rather than crashing the raw-agreement check or passing as absent.
        assert recompose({CONTEXT: malformed}) == {}
        assert "non-empty mapping" in context_failures("p", {CONTEXT: malformed}, RECIPE)[0]
    with pytest.raises(ValueError, match="both at the top level"):
        route_context(both, RECIPE)

    reserved = {CONTEXT: {FREE_TEXT: {"value": "x"}}}
    assert any("reserved" in f for f in context_failures("p", reserved, RECIPE))


def test_a_malformed_entry_is_reported_not_raised(tmp_path):
    # Top level and context alike: render_entry raises on these, which used to abort the gate.
    scores = tmp_path / "sources" / "scores"
    scores.mkdir(parents=True)
    bad = {
        "service": None,
        "license": [{"detail": "no name"}],
        "source": {"value": "public", "raw": None},
        1: {"value": "an integer key"},
        CONTEXT: {
            "governance": "a bare string",
            "repo-license": [{"name": "MIT", "raw": 7}],
        },
    }
    (scores / "p.yaml").write_text(
        yaml.safe_dump({"openness": {"components": bad, "raw": "service:x"}})
    )
    failures = check(tmp_path)
    assert {f.split(":")[0] for f in failures} == {
        "p.service", "p.license", "p.source", "p.1", "p.context.governance",
        "p.context.repo-license",
    }


def test_the_gate_passes_a_routed_record_and_skips_one_with_no_ladder():
    assert context_failures("p", route_context(structure(RAW), RECIPE), RECIPE) == []
    assert context_failures("p", structure(RAW), None) == []


def test_the_writer_emits_the_nested_mapping(tmp_path):
    # The one place #188 expected trouble: build/components.py locates the field by indent and
    # had never emitted a two-level nesting. It re-emits the whole value through the dumper, so
    # depth is the dumper's problem, and its three reparse assertions still hold.
    text = yaml.safe_dump(
        {"product": "p", "openness": {"score": 5, "components": structure(RAW), "raw": RAW,
                                      "sources": []}},
        sort_keys=False,
    )
    routed = route_context(structure(RAW), RECIPE)
    new_text = set_field(text, routed)

    parsed = yaml.safe_load(new_text)["openness"]
    assert parsed["components"] == routed
    assert parsed["raw"] == RAW
    assert "    context:\n      service:\n        value: optional\n" in new_text


def test_the_corpus_is_routed():
    """Every record already satisfies the gate — the sweep ran and nothing has regressed it."""
    root = Path(__file__).resolve().parents[1]
    assert [f for f in check(root) if CONTEXT in f or "dropped from the score" in f] == []
