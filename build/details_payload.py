"""The per-product records the Details modal renders, and only those.

Its own module because `build/render.py` is a marimo notebook: every function in it sits under
an `@app.cell` decorator and is a cell, not an importable symbol. A helper defined there cannot
be imported by a test, which is how the size test came to rebuild the payload with its own
`{**product}` expansion instead of measuring the real one - so a trim in render.py changed
nothing the test saw. That is the second self-confirming test in this repo in as many days, and
the fix is the same one: one implementation, imported by both.

WHY TRIMMING IS CORRECTNESS, NOT A SIZE TRICK. The payload is a single marimo cell output under
a hard 8 MB cap. marimo does not raise when a cell exceeds it - it silently replaces the output,
and the Details buttons are rendered by a DIFFERENT cell, so the notebook looks perfect while
every button is wired to a handler that was never installed. That shipped on 2026-08-18.

The payload grows linearly with the corpus. At 527 products the untrimmed record set measures
close to the cap; a 135-product expansion put it at ~8.8 MB, over. Carrying a field the modal
never reads was already a defect at 527 - the expansion is only what made it visible.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

from build.vocabulary import axes

#: What the modal's JavaScript actually reads off a product. It renders the three axes, the
#: description and the identity line. It never reads `freshness`, `slug`, `org_slug`, `tier`,
#: `maturity`, `mature` or `overall_score` - those belong to the table and the gap arithmetic.
PRODUCT_KEYS = ("product", "org", "type", "description", "version_note", "lineage",
                "openness", "adoption", "capability")

#: Per axis. `bucket`, `governing_release` and `last_verified` are consumed elsewhere.
AXIS_KEYS = ("score", "class", "level", "reach", "value", "basis", "basis_detail", "note",
             "confidence", "components", "signal_type", "sources", "relative_to", "relation")

#: Per source. The modal shows a link and what the document showed. `content_sha256` is the
#: bulk of the excess - 64 hex characters per source, several sources per axis, three axes per
#: product - and `accessed`, `http_status` and `establishes` are never rendered either.
SOURCE_KEYS = ("url", "shows", "text")


def _trim_axis(axis: object) -> object:
    if not isinstance(axis, Mapping):
        return axis
    out = {k: v for k, v in axis.items() if k in AXIS_KEYS}
    sources = out.get("sources")
    if isinstance(sources, Sequence) and not isinstance(sources, (str, bytes)):
        out["sources"] = [{k: v for k, v in s.items() if k in SOURCE_KEYS}
                          for s in sources if isinstance(s, Mapping)]
    return out


def details_records(data: Mapping, order: Sequence[str]) -> dict[str, dict]:
    """Payload keyed by product name, carrying only what the modal renders."""
    payload: dict[str, dict] = {}
    for cid in order:
        category = data["categories"][cid]
        for product in category["products"]:
            record = {k: product[k] for k in PRODUCT_KEYS if k in product}
            for axis in axes():
                if axis in record:
                    record[axis] = _trim_axis(record[axis])
            record["category_label"] = category["label"]
            payload[product["product"]] = record
    return payload
