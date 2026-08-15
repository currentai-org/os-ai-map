"""Write derived provenance into a product's verification line. Deterministic, one at a time.

`build/prose_provenance.py` classifies and gathers; a reviewer decides; this applies. The
split exists because the decision is a reading and the write must not be: a script that both
chose a document and wrote it would be inventing provenance at scale, which is the failure
this whole exercise is correcting.

## What it refuses

A packet is applied only if it carries every part of its own justification:

  * `decision: derive` — anything else, including `reread`, is skipped, never written;
  * a `selected_document` a reader can reopen;
  * a `source_url` that is **in that product's score file**, checked against the corpus
    rather than trusted from the packet;
  * a `source_accessed` equal to the verification date the prose line already claims;
  * a non-empty `support` sentence.

Refusing on a missing field is the point. A packet that cannot say why a document settled the
prose has not established that it did, and the honest output is the untouched line plus a
re-read.

## What it never does

**It never changes the date.** This is a provenance repair, not a re-verification: the claim
"somebody confirmed these facts on 2026-08-13" is unchanged, and only the record of what they
read improves. Advancing the date would convert a formatting fix into a fresh verification
nobody performed.

It also never touches a score file. `last_verified` is a different field with a different
rule (`docs/reference/evidence-and-freshness.md`), and `product-copy.md` is explicit that
writing the comments line does not earn one.

Usage:
    uv run python -m build.apply_provenance --packets FILE            # report, writes nothing
    uv run python -m build.apply_provenance --packets FILE --apply
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml

from build.components import set_document_field
from build.prose_provenance import AXES, CANONICAL

ROOT = Path(__file__).resolve().parents[1]

# The whole dated clause, however it is currently worded, up to its terminator. Replaced
# wholesale so `Verified live <date> via primary sources` and `verified live <date> via
# primary-source research` collapse to the one canonical form.
CLAUSE = re.compile(
    r"[Vv]erified(?: live)?\s+(\d{4}-\d{2}-\d{2})\s*[,;]?\s*(?:via|on|against|using)?\s*[^.;]*",
)


class Refused(Exception):
    """A packet that cannot justify itself. Never a reason to write something else."""


def score_sources(slug: str) -> dict[str, str]:
    """url -> accessed, for every source in the product's score file."""
    path = ROOT / "sources" / "scores" / f"{slug}.yaml"
    score = yaml.safe_load(path.read_text()) or {}
    return {
        str(s.get("url")): str(s.get("accessed"))
        for axis in AXES
        for s in (score.get(axis) or {}).get("sources") or []
    }


def check(packet: dict) -> None:
    """Raise `Refused` unless the packet carries every part of its own justification."""
    slug = packet.get("product")
    for field in ("selected_document", "source_url", "source_accessed", "support"):
        if not str(packet.get(field) or "").strip():
            raise Refused(f"{slug}: packet has no {field}")

    date = str(packet.get("verification_date") or "")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise Refused(f"{slug}: verification_date {date!r} is not a date")
    if str(packet["source_accessed"]) != date:
        raise Refused(
            f"{slug}: source accessed {packet['source_accessed']} but the prose line claims "
            f"{date}; a document read on another day did not settle this line"
        )

    # The URL is checked against the corpus, not believed from the packet. A packet naming a
    # source the product does not cite is the one way this could launder an invented document.
    recorded = score_sources(slug)
    url = str(packet["source_url"])
    if url not in recorded:
        raise Refused(f"{slug}: {url} is not a source in that product's score file")
    if recorded[url] != date:
        raise Refused(f"{slug}: {url} is recorded as accessed {recorded[url]}, not {date}")

    if METHOD := re.match(r"\s*(primary sources?|research|web search)", str(packet["selected_document"]), re.I):
        raise Refused(f"{slug}: {METHOD.group(1)!r} names a method, which is what this repairs")


def rewrite(comments: str, date: str, document: str) -> str:
    """Replace the dated clause with the canonical form, leaving the rest of the prose alone."""
    replacement = f"Verified {date} via {document.rstrip('.')}"
    new, n = CLAUSE.subn(replacement, comments, count=1)
    if n != 1:
        raise Refused("could not locate exactly one dated verification clause")
    return new


def apply_one(packet: dict) -> bool:
    check(packet)
    slug = packet["product"]
    path = ROOT / "sources" / "products" / f"{slug}.yaml"
    text = path.read_text()
    doc = yaml.safe_load(text) or {}
    comments = str(doc.get("comments") or "")

    new_comments = rewrite(comments, str(packet["verification_date"]), str(packet["selected_document"]))
    if new_comments == comments:
        return False
    if not CANONICAL.search(" ".join(new_comments.split())):
        raise Refused(f"{slug}: rewrite did not produce a canonical line")
    path.write_text(set_document_field(text, "comments", new_comments))
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packets", required=True)
    parser.add_argument("--apply", action="store_true", help="write; otherwise report only")
    args = parser.parse_args()

    rows = yaml.safe_load(Path(args.packets).read_text()) or []
    derive = [r for r in rows if r.get("decision") == "derive"]
    reread = [r for r in rows if r.get("decision") == "reread"]
    undecided = [r for r in rows if r.get("decision") not in ("derive", "reread")]

    print(f"{len(rows)} packets: {len(derive)} derive, {len(reread)} reread, "
          f"{len(undecided)} undecided")

    applied, refused = 0, []
    for packet in derive:
        try:
            if args.apply:
                applied += apply_one(packet)
            else:
                check(packet)
        except Refused as e:
            refused.append(str(e))

    for line in refused:
        print(f"  refused: {line}")
    if args.apply:
        print(f"\n{applied} product file(s) rewritten; {len(refused)} refused")
    else:
        print(f"\n{len(derive) - len(refused)} packet(s) would apply; {len(refused)} refused")
    return 1 if refused else 0


if __name__ == "__main__":
    raise SystemExit(main())
