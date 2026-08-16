"""No module may hold a private copy of a vocabulary that has a declarative owner.

Four defects of this exact shape shipped in a fortnight, and none of them failed loudly —
each reported success over a narrower question than the one it claimed to answer:

  * `check_routing.SOURCE_ARTIFACT` named five sources where the routing table declared seven;
  * `check_routing.artifacts_of` enumerated the same vocabulary again in the same file, so a
    correctly declared new artifact kind was invisible to coverage;
  * a second copy of `METHOD_WORDS` in the (now removed) applier was narrower, so
    `substitute sources` passed as a document name;
  * two modules each validated a date by shape, accepting `2026-99-99`.

**These tests inspect the AST and call the code, not the source text.** The first cut matched
strings — a double-quoted tuple in one exact order, a bare `NAME =` assignment, the substring
`fromisoformat` anywhere in a file — which reproduced the governing defect one level up: a
check reporting a semantic guarantee while testing a textual convention. A single-quoted list,
an annotated assignment, or a reordering would all have passed.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import yaml

from build.vocabulary import ROOT, artifact_kinds, axes

BUILD = ROOT / "build"


def _module_sources() -> dict[str, str]:
    return {p.name: p.read_text() for p in sorted(BUILD.glob("*.py"))}


def _string_collections(tree: ast.AST) -> list[tuple[int, frozenset[str]]]:
    """Every literal tuple/list/set of plain strings, as (lineno, frozenset).

    Structure rather than spelling: quote style, ordering and container type all normalize
    away, which is what makes this a check on the vocabulary rather than on its formatting.
    """
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Tuple, ast.List, ast.Set)):
            continue
        values = [
            e.value for e in node.elts
            if isinstance(e, ast.Constant) and isinstance(e.value, str)
        ]
        if values and len(values) == len(node.elts):
            found.append((getattr(node, "lineno", 0), frozenset(values)))
    return found


def _assigned_names(tree: ast.AST) -> set[str]:
    """Module-level names bound by assignment, including annotated ones."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def test_axes_come_from_the_schema():
    """The schema lists them as properties and requires all three; it is the owner."""
    schema = json.loads((ROOT / "docs" / "schemas" / "score.schema.json").read_text())
    assert set(axes()) == set(schema["required"]) - {"product"}
    assert set(axes()) == set(schema["properties"]) - {"product"}


def test_no_module_holds_a_private_copy_of_the_axes():
    """Ten modules did, seven as constants and three inline — including `validate.py`.

    Matched on the SET of strings, so a reordered tuple, a list, a set, or single quotes are
    all caught. The earlier regex required one exact spelling and would have missed every one
    of those.
    """
    wanted = frozenset(axes())
    offenders = []
    for name, source in _module_sources().items():
        if name == "vocabulary.py":
            continue
        for lineno, values in _string_collections(ast.parse(source)):
            if values == wanted:
                offenders.append(f"{name}:{lineno}")
    assert not offenders, (
        "these state the axis vocabulary literally instead of calling "
        f"build.vocabulary.axes(): {offenders}"
    )


def test_render_is_importable_so_it_needs_no_exemption():
    """render.py was exempted while it was script-invoked, and the exemption was unsound: a
    fourth axis would have left the rendered methodology silently omitting its sources while
    every other test passed. The invocation moved to `-m` instead of the exemption staying."""
    workflows = " ".join(p.read_text() for p in (ROOT / ".github" / "workflows").glob("*.yml"))
    docs = " ".join(
        (ROOT / f).read_text() for f in ("AGENTS.md", "README.md", "docs/operations/publish-map.md")
    )
    assert "python build/render.py" not in workflows + docs, (
        "render.py is script-invoked again, so it cannot import build.vocabulary and the "
        "axis vocabulary will silently fork"
    )


def test_artifact_kinds_come_from_the_routing_table():
    routing = yaml.safe_load((ROOT / "sources" / "signal_routing.yaml").read_text())
    declared = {s["artifact_key"] for s in routing["sources"].values() if s.get("artifact_key")}
    assert artifact_kinds() == declared
    # The layering the first cut of #184 got wrong: a source and an artifact key are
    # different things, and one source may consume a key that shares no name with it.
    assert "arxiv" in artifact_kinds()
    assert "arxiv" not in routing["sources"]


def test_proposer_support_is_defined_by_handlers_not_by_routing():
    """A routed kind is not automatically a proposable one.

    Deriving `VERIFIABLE_KINDS` from the routing table made any newly declared `artifact_key`
    an accepted `--kind` with no pattern, verifier or renderer behind it. The two sets are
    equal today, which is what made the coincidence look like a definition.
    """
    from build.propose_artifacts import (
        _PUBLIC_URL,
        _VERIFIABLE,
        NOT_A_DISTRIBUTION_ARTIFACT,
        PATTERNS,
        VERIFIABLE_KINDS,
    )

    patterned = {kind for kind, _ in PATTERNS}
    for kind in VERIFIABLE_KINDS:
        assert kind in patterned, f"{kind} has no URL pattern to mine it from prose"
        assert kind in _PUBLIC_URL, f"{kind} has no public URL renderer"
        assert kind in _VERIFIABLE, f"{kind} has no live existence check"

    # Supported must remain an intentional SUBSET of routed, with the gap named.
    assert set(VERIFIABLE_KINDS) <= artifact_kinds()
    assert artifact_kinds() - set(VERIFIABLE_KINDS) == NOT_A_DISTRIBUTION_ARTIFACT


def test_capability_relation_deltas_match_the_schema_enum():
    """`DELTA` maps each relation to an integer offset, which the schema cannot express — so
    the dict stays. What it must not do is disagree about which relations exist."""
    from build.check_capability import DELTA

    schema = json.loads((ROOT / "docs" / "schemas" / "score.schema.json").read_text())
    enum = schema["properties"]["capability"]["properties"]["relation"]["enum"]
    assert set(DELTA) == set(enum)


def test_the_method_vocabulary_has_exactly_one_definition():
    """A second, narrower copy in the applier is how `substitute sources` passed as a
    document name. The applier is gone; the rule outlives it, because the next module that
    needs to recognize a method word will be tempted to spell it out again.

    AST-based, so an annotated assignment (`METHOD_WORDS: re.Pattern = ...`) is caught; the
    first cut matched `^METHOD_WORDS\\s*=` and would not have been.
    """
    definers = [
        name for name, source in _module_sources().items()
        if "METHOD_WORDS" in _assigned_names(ast.parse(source))
    ]
    assert definers == ["product_prose.py"], (
        f"METHOD_WORDS is assigned in {definers}; it must have exactly one owner"
    )


def test_date_validation_rejects_impossible_dates():
    """Behavioral, not textual. The first cut asserted `fromisoformat` appeared somewhere in
    the file, which a module could satisfy while still shape-matching elsewhere.

    Both halves of the check are exercised: `20260815` parses but is the wrong spelling, and
    `2026-99-99` has the right spelling and is not a date.
    """
    from build.vocabulary import is_iso_date

    for bad in ("2026-99-99", "2026-02-30", "2026-02-29", "not-a-date", "", "20260815", None):
        assert not is_iso_date(bad), f"{bad!r} accepted as a date"
    for good in ("2026-08-15", "2026-02-28", "2024-02-29"):
        assert is_iso_date(good)


def test_date_handling_has_exactly_one_owner():
    """Five modules held four definitions of "a date" between them.

    Two `parse_date` copies were identical except that one accepted a `date` object and the
    other did not — and PyYAML returns an object for an unquoted date and a string from a
    payload, so the two answered the same freshness question differently depending on where
    the value came from. A third module validated by shape, accepting `2026-99-99`. A fourth
    arrived with the prose classifier's canonical gate, which is what prompted this test
    instead of a fifth.

    `build/vocabulary.py` now owns both: `is_iso_date` gates a field's spelling,
    `parse_date` produces something comparable.

    AST-based, and matched on what a function RETURNS rather than on its name. A name test
    let `validate_sources` through the filter as a false positive — it calls `fromisoformat`
    inline, which is use rather than a second definition — and the fix for that must not be
    to name the exception, because then the test passes by listing whatever it happens to
    find. A function returning a date verdict IS the construct; a function returning
    `list[str]` that parses a date on the way is not.
    """
    def _returns_a_date_verdict(node: ast.FunctionDef) -> bool:
        returns = ast.unparse(node.returns) if node.returns else ""
        return returns in ("bool", "date | None", "date") and "fromisoformat" in ast.dump(node)

    definers = sorted(
        name for name, source in _module_sources().items()
        if any(
            isinstance(node, ast.FunctionDef) and _returns_a_date_verdict(node)
            for node in ast.walk(ast.parse(source))
        )
    )
    assert definers == ["vocabulary.py"], (
        f"a date helper is defined in {definers}; build/vocabulary.py owns them"
    )
