"""The one owner for vocabularies more than one module needs.

Every entry here was a literal repeated across `build/`, and this repo has now shipped four
defects of exactly that shape in a fortnight — a sibling copy that had quietly fallen behind
the thing it mirrored:

  * `check_routing.SOURCE_ARTIFACT` named five sources where the routing table declared
    seven, so a bridged `npm`/`crates` route would have read as uncovered;
  * `check_routing.artifacts_of` enumerated the same vocabulary a second time in the same
    file, so a correctly declared new kind was invisible to coverage;
  * the prose applier reimplemented `product_prose.METHOD_WORDS` more narrowly, so
    `substitute sources` passed as a document name;
  * two modules each validated a date by shape, accepting `2026-99-99`.

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

`build/product_prose.py` keeps `METHOD_WORDS` rather than moving it here. It has exactly one
owner already, that owner is the module the vocabulary is *about*, and the sibling test holds
it there. Relocating a constant with one owner buys nothing.

`check_adoption._DOWNLOAD_INSTRUMENTS` also stays. It is not a copy of the `signal_type` enum;
it names the subset measured on a download scale, and its module explains why `unknown` is
excluded. A narrower vocabulary with a written reason is a decision, not a duplicate.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def is_iso_date(value: object) -> bool:
    r"""A real calendar date in the hyphenated form this corpus uses.

    Not a vocabulary, but here for the same reason and by the same rule: two modules need it,
    it has one correct definition, and this repo has already shipped the wrong one twice —
    three days apart, the second written after the first was fixed.

    BOTH halves are required. A `\d{4}-\d{2}-\d{2}` shape test alone accepts `2026-99-99`
    and `2026-02-30`, which is a date check answering "does this look like a date".
    `date.fromisoformat` alone accepts Python 3.11's compact `20260815`, which would put a
    second date spelling into a corpus whose schema declares `format: date`.
    """
    text = str(value)
    if len(text) != 10 or text[4] != "-" or text[7] != "-":
        return False
    return parse_date(text) is not None


def parse_date(value: object) -> date | None:
    """A date for COMPARING, or None. The permissive sibling of `is_iso_date`.

    Two modules held identical copies of this, and a third rejected shapes the other two
    accepted, so "is this date fresh enough" and "is this field well-formed" were being
    answered by three different definitions of a date.

    The passthrough matters: PyYAML returns a real `date` for an unquoted `2026-08-15`, so a
    caller reading straight from a corpus file gets an object here and a string from a
    payload. Both must land on the same value or a freshness comparison silently fails one
    way round.

    This does NOT enforce the hyphenated spelling. `is_iso_date` is the gate; this is
    arithmetic, and refusing to compare a date because it was spelled unusually would fail a
    freshness check for a formatting reason.
    """
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def is_iso_timestamp(value: object) -> bool:
    r"""A real ISO-8601 timestamp carrying a time AND a timezone, in the form the runs API emits.

    The timestamp sibling of `is_iso_date`, and here for the same reason: `source_runs` records
    instants (`2026-08-23T01:00:00.266Z`), not calendar dates, so it needs a check that ACCEPTS a
    time and offset rather than rejecting them for exceeding ten characters. Both halves of the
    date rule carry over: a shape a `datetime` can actually parse — so `2026-99-99T99:99:99garbage`
    is refused for looking like a timestamp without being one — AND a timezone, because a run
    instant without an offset is ambiguous and this corpus records only UTC-stamped ones.
    """
    dt = parse_timestamp(value)
    return dt is not None and dt.tzinfo is not None


def parse_timestamp(value: object) -> datetime | None:
    """A timezone-carrying datetime for COMPARING, or None. The permissive sibling of
    `is_iso_timestamp`, mirroring `parse_date`/`is_iso_date`.

    `datetime.fromisoformat` accepts a trailing `Z` only on newer Pythons, so it is swapped for
    `+00:00` first. A `datetime` passthrough matches `parse_date`, for a caller that already holds
    one; ordering two of these is what a capture-bounds check needs.
    """
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


# The canonical adoption instrument vocabulary: the `signal_type` values a recorded score
# or a routing route may declare. A literal rather than a derivation — `signal_routing.yaml`
# names the routed instruments but not `unknown` (a recorded score with no routable
# instrument), so no declarative file carries the full set. Held here, once, because
# `validate.py` gates recorded scores against it and `serialize_routing.py` gates compiled
# routes against it, and a sibling copy in either is exactly the drift this module exists to
# stop: `mystery` compiled an eighth route with no error until both read the same set.
SIGNAL_TYPES = frozenset(
    {"active_users", "usage_volume", "reported_traction", "stars_fallback", "unknown"}
)

# The routable subset: the instruments a routing route or an aggregation rule may declare.
# `unknown` is a legitimate recorded-score `signal_type` — a score with no routable instrument
# behind it — but it is NOT a route: nothing fetches or bands it, so a route or a rule naming
# `unknown` is a declaration evaluation could not act on. `validate.py` keeps the full
# `SIGNAL_TYPES` for recorded scores; `serialize_routing.py` gates compiled routes and rules
# against this narrower set, and the difference between the two is the decision written here.
ROUTABLE_INSTRUMENTS = SIGNAL_TYPES - {"unknown"}


@lru_cache(maxsize=1)
def axes() -> tuple[str, ...]:
    """The three scored axes, from `docs/schemas/score.schema.json`.

    The schema is the declarative owner: it lists them as properties and requires all three.
    Ten modules held this triple as a literal — seven as a named constant and three inline,
    including `validate.py`, the schema gate itself. None had drifted, because no fourth axis
    has ever been added; a fourth axis is also exactly the change that would narrow ten
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
