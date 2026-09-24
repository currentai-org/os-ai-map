"""regenerate.yml's push retry must stand down on exactly the paths that trigger it.

When a merge lands on main while the workflow is building, its push is rejected. The retry
step compares the run's build base with the new main over `INPUTS` and rebases only when none
of them changed, because the artifacts it built are current only if its inputs are. A merge
that did change an input has queued its own run, which regenerates from the newer tree, and
that holds only for a merge the `paths` filter matched.

So `INPUTS` and the push trigger's `paths` are one list written twice, in two syntaxes. If
`INPUTS` misses a trigger path, a rebased commit can pair new inputs with artifacts built from
the old ones, and a changed `build/notebook_data.json` reaches the warehouse through
registry.yml before the queued run repairs it. If `INPUTS` names a path the filter does not,
the run stands down for a queued run that never comes, and the payload goes stale (#672, #690).
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github/workflows/regenerate.yml"


def trigger_paths() -> list[str]:
    # PyYAML reads the `on:` key as the boolean True, this being YAML.
    doc = yaml.safe_load(WORKFLOW.read_text())
    triggers = doc.get("on") or doc.get(True)
    return list(triggers["push"]["paths"])


def inputs_pathspecs() -> list[str]:
    match = re.search(r'^\s*INPUTS="([^"]*)"', WORKFLOW.read_text(), re.MULTILINE)
    assert match, "regenerate.yml no longer sets INPUTS in its push retry"
    return match.group(1).split()


def as_pathspec(filter_path: str) -> str:
    """The git pathspec a GitHub `paths` filter entry selects: `dir/**` is the directory,
    `!path` is an exclusion, anything else is literal."""
    if filter_path.startswith("!"):
        return ":!" + as_pathspec(filter_path[1:])
    if filter_path.endswith("/**"):
        return filter_path[: -len("/**")]
    assert "*" not in filter_path, (
        f"{filter_path!r} is a glob as_pathspec cannot translate; extend it rather than "
        "letting INPUTS and the trigger drift"
    )
    return filter_path


def test_inputs_are_exactly_the_push_trigger_paths():
    expected = sorted(as_pathspec(p) for p in trigger_paths())
    assert sorted(inputs_pathspecs()) == expected


def test_the_translation_covers_each_filter_shape():
    assert as_pathspec("sources/**") == "sources"
    assert as_pathspec("!build/notebook_data.json") == ":!build/notebook_data.json"
    assert as_pathspec("docs/methodology.md") == "docs/methodology.md"
