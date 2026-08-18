"""The Details modal's payload has to stay inside marimo's per-cell output cap.

On 2026-08-18 it did not, and nothing noticed. marimo does not raise when a cell's
output exceeds `output_max_bytes` -- it silently replaces the output with a "Your
output is too large" callout and carries on. The Details *buttons* are rendered by a
different cell, so the published notebook looked correct: 472 buttons, right product
count, right prose. Every one of them was wired to a click handler that had never been
installed, and the only way to find out was to click one.

Two multipliers stacked to get there, and both are worth stating because either alone
would have fit:

  1. The payload doubled (1.28 MB -> 2.44 MB of JSON) when the score notes were
     rewritten and source provenance was added.
  2. A single astral character -- one U+1F917 in PEFT's openness note -- widened the
     whole Python string from 2 bytes per character to 4. `sys.getsizeof`, which is
     what marimo measures, doubled on the strength of one emoji.

Base64 removes both: it is pure ASCII (1 byte per character, and no astral character
can ever appear in it) and contains none of `&"<`, so the HTML-attribute escaping that
inflated the raw JSON has nothing to expand. This test fails if anyone reverts to
interpolating raw JSON, or if the payload simply grows past the cap again.
"""

import base64
import json
import sys
from pathlib import Path

# marimo's default, from marimo/_config/config.py. Overridable via
# MARIMO_OUTPUT_MAX_BYTES or [tool.marimo.runtime], but CI and the OSO publish
# runner both use the default, so that is what has to hold.
OUTPUT_MAX_BYTES = 8_000_000

# marimo measures the serialized cell output, which carries the attribute value through
# one further round of HTML escaping. Observed 2026-08-18: a 12,239,840-byte attribute
# was reported by marimo as 24,505,824 bytes.
MARIMO_SERIALIZATION_FACTOR = 2

PAYLOAD = Path(__file__).resolve().parents[1] / "build" / "notebook_data.json"


def _details_attribute() -> str:
    """Rebuild exactly what build/render.py puts in the iframe's onload attribute."""
    data = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    order = data["order"] if isinstance(data.get("order"), list) else list(data["categories"])
    payload = {}
    for cid in order:
        for product in data["categories"][cid]["products"]:
            payload[product["product"]] = {
                **product,
                "category_label": data["categories"][cid]["label"],
            }
    encoded = base64.b64encode(
        json.dumps(payload, ensure_ascii=False).encode("utf-8")
    ).decode("ascii")
    # The attribute escaping render.py applies. A no-op on base64, deliberately.
    return encoded.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


def test_the_details_payload_fits_in_a_marimo_cell_output():
    attribute = _details_attribute()
    measured = sys.getsizeof(attribute) * MARIMO_SERIALIZATION_FACTOR
    assert measured < OUTPUT_MAX_BYTES, (
        f"the Details payload measures ~{measured:,} bytes against marimo's "
        f"{OUTPUT_MAX_BYTES:,}-byte output_max_bytes. marimo will drop this cell's output "
        f"silently and every Details button in the published notebook will do nothing when "
        f"clicked. Trim the payload to the fields the modal actually renders (it ignores "
        f"freshness, slug, org_slug, tier, overall_score and the sources' content_sha256 / "
        f"accessed / http_status), or split it across cells."
    )


def test_the_payload_is_ascii_so_one_emoji_cannot_widen_it():
    """The property that makes the size predictable, asserted directly.

    A non-ASCII character here would mean someone stopped base64-encoding, which
    reintroduces both multipliers at once -- and it would do so silently, since the
    size test above might still pass on a smaller payload.
    """
    attribute = _details_attribute()
    assert attribute.isascii(), (
        "the Details payload is no longer pure ASCII, so it is no longer base64. "
        "Raw JSON in an HTML attribute is what broke the modal on 2026-08-18."
    )
    assert sys.getsizeof(attribute) // max(1, len(attribute)) == 1, (
        "the payload is stored at more than 1 byte per character, which means a "
        "wide character crept in and doubled what marimo measures."
    )
