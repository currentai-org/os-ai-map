"""No module may hold a private copy of a vocabulary that has a declarative owner.

Four defects of this exact shape shipped in a fortnight, and none of them failed loudly —
each reported success over a narrower question than the one it claimed to answer:

  * `check_routing.SOURCE_ARTIFACT` named five sources where the routing table declared seven;
  * `check_routing.artifacts_of` enumerated the same vocabulary again in the same file, so a
    correctly declared new artifact kind was invisible to coverage;
  * `apply_provenance` reimplemented `METHOD_WORDS` more narrowly, so `substitute sources`
    passed as a document name;
  * `check_payload` and `apply_provenance` each validated a date by shape.

These tests are the ratchet. They do not stop a module defining a constant; they stop one
defining a constant that silently disagrees with the source of truth.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

from build.vocabulary import ROOT, artifact_kinds, axes

AXES_LITERAL = re.compile(r'\(\s*"openness"\s*,\s*"adoption"\s*,\s*"capability"\s*\)')


def test_axes_come_from_the_schema():
    """The schema lists them as properties and requires all three; it is the owner."""
    schema = json.loads((ROOT / "docs" / "schemas" / "score.schema.json").read_text())
    assert set(axes()) == set(schema["required"]) - {"product"}
    assert set(axes()) == set(schema["properties"]) - {"product"}


def test_no_module_holds_a_private_copy_of_the_axes():
    """Seven modules did. A fourth axis would have silently narrowed seven denominators at
    once, and a walk that quietly skips an axis passes green."""
    # render.py is the one build module invoked as a SCRIPT rather than with `-m`, so it
    # cannot import from the package. The exemption is asserted below rather than merely
    # allowed, so adding a second one is a visible decision.
    exempt = {"vocabulary.py", "render.py"}
    offenders = []
    for path in sorted((ROOT / "build").glob("*.py")):
        if path.name in exempt:
            continue
        if AXES_LITERAL.search(path.read_text()):
            offenders.append(path.name)
    assert not offenders, (
        "these define the axis triple as a literal instead of importing "
        f"build.vocabulary.axes(): {offenders}"
    )


def test_the_only_exemption_is_the_script_invoked_module():
    """If render.py ever moves to `-m`, this fails and the exemption comes out."""
    workflows = " ".join(
        p.read_text() for p in (ROOT / ".github" / "workflows").glob("*.yml")
    )
    assert "python build/render.py" in workflows, (
        "render.py no longer appears to be script-invoked; drop its exemption in "
        "test_no_module_holds_a_private_copy_of_the_axes and import axes() there"
    )


def test_artifact_kinds_come_from_the_routing_table():
    routing = yaml.safe_load((ROOT / "sources" / "signal_routing.yaml").read_text())
    declared = {
        s["artifact_key"] for s in routing["sources"].values() if s.get("artifact_key")
    }
    assert artifact_kinds() == declared
    # The layering the first cut of #184 got wrong: a source and an artifact key are
    # different things, and one source may consume a key that shares no name with it.
    assert "arxiv" in artifact_kinds()
    assert "arxiv" not in routing["sources"]


def test_verifiable_kinds_are_derived_with_an_explicit_exclusion():
    """`arxiv` is excluded on purpose. The test exists so the exclusion cannot silently widen
    into the drift it used to look like — if another kind is dropped, this fails."""
    from build.propose_artifacts import NOT_A_DISTRIBUTION_ARTIFACT, VERIFIABLE_KINDS

    assert set(VERIFIABLE_KINDS) == artifact_kinds() - NOT_A_DISTRIBUTION_ARTIFACT
    assert NOT_A_DISTRIBUTION_ARTIFACT == {"arxiv"}


def test_capability_relation_deltas_match_the_schema_enum():
    """`DELTA` maps each relation to an integer offset, which the schema cannot express — so
    the dict stays. What it must not do is disagree about which relations exist."""
    from build.check_capability import DELTA

    schema = json.loads((ROOT / "docs" / "schemas" / "score.schema.json").read_text())
    enum = schema["properties"]["capability"]["properties"]["relation"]["enum"]
    assert set(DELTA) == set(enum), (
        "check_capability.DELTA and the schema disagree about the relation vocabulary; a "
        "relation missing from DELTA would raise, but one missing from the schema would be "
        "accepted by the gate and rejected by validate"
    )


def test_the_method_vocabulary_has_exactly_one_definition():
    if not (ROOT / "build" / "prose_provenance.py").exists():
        pytest.skip("prose_provenance lands with #283; this activates when it merges")
    """`apply_provenance` held a narrower sibling of `METHOD_WORDS` until 2026-08-15, which is
    how `substitute sources` passed as a document name."""
    method_defs = [
        path.name
        for path in sorted((ROOT / "build").glob("*.py"))
        if re.search(r"^METHOD_WORDS\s*=", path.read_text(), re.M)
    ]
    assert method_defs == ["prose_provenance.py"], (
        f"METHOD_WORDS is defined in {method_defs}; it must have one owner"
    )


@pytest.mark.parametrize("module", ["check_payload", "apply_provenance"])
def test_dates_are_parsed_not_shape_matched(module):
    """Both validated a date with `\\d{4}-\\d{2}-\\d{2}` and accepted 2026-99-99. The same
    defect, in two modules, three days apart."""
    path = ROOT / "build" / f"{module}.py"
    if not path.exists():
        pytest.skip(f"{module} lands with #283; this activates when it merges")
    source = path.read_text()
    assert "fromisoformat" in source, f"{module} must parse dates, not match their shape"
    assert not re.search(r'r"\^?\\\\d\{4\}-\\\\d\{2\}-\\\\d\{2\}\$?"', source), (
        f"{module} still shape-matches a date"
    )
