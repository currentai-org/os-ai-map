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

import base64
import json
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


#: How much base64 one hidden iframe may carry. marimo's cap is 8,000,000 bytes on a cell's
#: SERIALIZED output, which was measured at twice the attribute's own size, so a chunk has to
#: stay under 4,000,000 to be safe and this leaves a wide margin. The corpus crossed the cap on
#: 2026-09-17 at 4,048,380 base64 characters - 1.2% over, after eighteen months of linear
#: growth - and would have crossed it on the next promotion whatever this number were set to.
#: Chunking is what makes the cap stop being a deadline.
CHUNK_CHARS = 2_000_000


def payload_base64(data: Mapping, order: Sequence[str]) -> str:
    """The whole payload, base64 of UTF-8 JSON.

    Base64 rather than raw JSON for two reasons that both bit on 2026-08-18: the payload is
    interpolated into an HTML attribute, so `"` would be escaped and expand it, and one astral
    character anywhere in a score note widens the entire Python string to 4 bytes per character.
    Base64 is pure ASCII and contains none of `&"<`.
    """
    return base64.b64encode(
        json.dumps(details_records(data, order), ensure_ascii=False).encode("utf-8")
    ).decode("ascii")


def payload_chunks(data: Mapping, order: Sequence[str], chunk_chars: int = CHUNK_CHARS) -> list[str]:
    """The same base64, split so no single cell output approaches marimo's cap.

    Splitting the BASE64 rather than the records keeps the decoder synchronous: the chunks are
    concatenated back into one string before a single `atob`, so the JavaScript never has to
    merge objects or know what a record looks like. It also keeps the split invisible to the
    modal - there is one payload, delivered in pieces.

    Compression was the alternative and was rejected: gzip would cut this 4.2x, and inflating it
    in the browser means `DecompressionStream`, which is async, which makes the bootstrap async,
    which races the click handler that reads the payload. A synchronous decoder is worth more
    than the bytes.
    """
    encoded = payload_base64(data, order)
    if chunk_chars <= 0:
        raise ValueError("chunk_chars must be positive")
    return [encoded[i:i + chunk_chars] for i in range(0, len(encoded), chunk_chars)] or [""]
