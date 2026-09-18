"""Find a dated verification sentence in a product's `comments`, which may no longer carry one.

`docs/reference/product-copy.md` used to require every `comments` field to end in

    Verified <YYYY-MM-DD> via <document>.

and this module classified the line into five states so `sweep_status` could age the prose on
it. The line was a third copy of a fact the record already holds twice: each axis carries
`last_verified`, and the product page prints `Verified <date>` from it. Visitors read the line
as a footnote about the product. #619 retired it, and the guide now says a `comments` field is
a footnote about our reading or nothing at all.

So the classifier is inverted. It no longer asks "is the line canonical"; it asks "is there a
dated verification sentence here at all", in any of the spellings the corpus has carried
(`Verified live <date> on`, `verified <date> against`, lowercase, no period). A hit is a defect,
and `tests/test_product_prose.py` holds the corpus at zero.

What the line named, the document that was read, is not lost. It belongs on the axis that the
reading settled, as a source entry with `url` and `shows`, where a re-fetch can confirm it.

Usage:
    uv run python -m build.product_prose          # list every product still carrying one
    uv run python -m build.product_prose --quiet  # the count only
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

# A verification verb, then a date within a short span. The span allows the words the corpus
# has put between them (`live`, `on HF`, `against the card`) and stops at a sentence end, so a
# `Verified` in one sentence does not borrow a date from the next.
#
# Deliberately not anchored to the start of a sentence and not requiring `via`: the old
# classifier's precision about the canonical form is what let `Verified live 2026-08-13 on
# huggingface.co` count as a different state from the line it was supposed to find. Every
# spelling is the same defect now.
DATED_VERIFICATION = re.compile(
    r"\b[Vv]erif(?:ied|ication)\b[^.;!?]{0,45}?\b(\d{4}-\d{2}-\d{2})\b"
)

# The reverse order, `2026-08-13: verified against the card`, has not appeared in the corpus
# but is the same claim; catching it costs one alternative.
DATE_THEN_VERIFIED = re.compile(
    r"\b(\d{4}-\d{2}-\d{2})\b[^.;!?]{0,45}?\b[Vv]erif(?:ied|ication)\b"
)


def products() -> dict[str, dict]:
    return {
        p.stem: (yaml.safe_load(p.read_text()) or {})
        for p in sorted((ROOT / "sources" / "products").glob("*.yaml"))
    }


def dated_verification(comments: object) -> str | None:
    """The dated verification sentence in `comments`, or None when there is none.

    Returns the whole sentence rather than the match, so a failure message shows the reader
    what to delete. Whitespace is normalized first because the corpus is hand-wrapped and a
    date can sit on the line after its verb.
    """
    text = " ".join(str(comments or "").split())
    if not text:
        return None
    match = DATED_VERIFICATION.search(text) or DATE_THEN_VERIFIED.search(text)
    if not match:
        return None
    start = max(text.rfind(". ", 0, match.start()), text.rfind("; ", 0, match.start()))
    start = 0 if start < 0 else start + 2
    end = text.find(". ", match.end())
    end = len(text) if end < 0 else end + 1
    return text[start:end].strip()


def census() -> dict[str, str]:
    """slug -> the offending sentence, for every product whose comments carry one."""
    found = {}
    for slug, product in products().items():
        sentence = dated_verification(product.get("comments"))
        if sentence:
            found[slug] = sentence
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--quiet", action="store_true", help="the count only")
    args = parser.parse_args()

    total = len(products())
    found = census()
    print(f"{len(found)} of {total} products carry a dated verification sentence in comments")
    if found and not args.quiet:
        for slug, sentence in found.items():
            print(f"  {slug:30} {sentence}")
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
