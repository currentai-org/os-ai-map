"""The one owner for vocabularies more than one module needs.

Every entry here was a literal repeated across `build/`, and this repo has now shipped four
defects of exactly that shape in a fortnight — a sibling copy that had quietly fallen behind
the thing it mirrored:

  * `check_routing.SOURCE_ARTIFACT` named five sources where the routing table declared
    seven, so a bridged `npm`/`crates` route would have read as uncovered;
  * `check_routing.artifacts_of` enumerated the same vocabulary a second time in the same
    file, so a correctly declared new kind was invisible to coverage;
  * `apply_provenance` reimplemented `prose_provenance.METHOD_WORDS` more narrowly, so
    `substitute sources` passed as a document name;
  * `check_payload` and `apply_provenance` each validated a date by shape, accepting
    `2026-99-99`.

None of them failed loudly. Each reported success over a narrower question than the one it
claimed to answer, which is the failure mode this module exists to stop repeating.

**The rule: a vocabulary that already has a declarative owner is derived from it, not
copied.** The score schema declares the axes; `sources/signal_routing.yaml` declares the
artifact kinds. Where a literal genuinely differs from its declarative source, the difference
is written down and tested, so it is a decision rather than drift.

## What is deliberately NOT here

`docs/openness-class-map.json` and its two in-code copies stay where they are. They are
already gated by `tests/test_openness_buckets.py`, which asserts all three agree — that is the
same protection this module provides, arrived at differently, and moving them would churn a
working invariant for symmetry.

`check_adoption._DOWNLOAD_INSTRUMENTS` also stays. It is not a copy of the `signal_type` enum;
it names the subset measured on a download scale, and its module explains why `unknown` is
excluded. A narrower vocabulary with a written reason is a decision, not a duplicate.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def axes() -> tuple[str, ...]:
    """The three scored axes, from `docs/schemas/score.schema.json`.

    The schema is the declarative owner: it lists them as properties and requires all three.
    Seven modules held this triple as a literal. None had drifted — a fourth axis has never
    been added — but a fourth axis is exactly the change that would silently narrow seven
    denominators at once, and a walk that quietly skips an axis passes green.
    """
    schema = json.loads((ROOT / "docs" / "schemas" / "score.schema.json").read_text())
    return tuple(k for k in schema["properties"] if k != "product")


@lru_cache(maxsize=1)
def artifact_kinds() -> frozenset[str]:
    """Product artifact keys any routing source declares it consumes, via `artifact_key`.

    A SOURCE (`semanticscholar`) and an ARTIFACT KEY (`arxiv`) are different layers, and
    conflating them is what made `arxiv` look undeclared while the router already reached it.
    """
    routing = yaml.safe_load((ROOT / "sources" / "signal_routing.yaml").read_text())
    return frozenset(
        source["artifact_key"]
        for source in (routing.get("sources") or {}).values()
        if source.get("artifact_key")
    )
