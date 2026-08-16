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
  * a non-empty `support` sentence;
  * a `prose_digest` still matching the live product, so a decision cannot be applied to
    prose it was not reviewed against.

Refusing on a missing field is the point. A packet that cannot say why a document settled the
prose has not established that it did, and the honest output is the untouched line plus a
re-read.

## Binding a decision to the prose it was reviewed against

A packet is a judgment about a specific description and a specific comments field. Without a
binding it survives every later edit to either, so a decision taken against last week's prose
could be written over this week's — and because `rewrite` substitutes the whole dated clause,
a packet whose `verification_date` had drifted would silently ADVANCE the live date, which is
the one thing this is not allowed to do. Reproduced before the fix: applying a packet dated
2026-08-13 to a line reading `Verified live 2026-08-12 via primary sources.` produced
`Verified 2026-08-13 via the README.`

So `prose_digest` covers the normalized description plus comments with the dated clause
removed, and the applier recomputes it. Any edit to the reviewed prose invalidates the
packet, and the product goes back for a fresh reading rather than being written blind. It
also re-checks that the live line is still `generic` and still carries the packet's date.

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
from datetime import date
from pathlib import Path

import yaml

from build.components import set_document_field
from build.prose_provenance import (ANY_DATED, AXES, CLAUSE_HEAD, HAS_WORD, METHOD_WORDS,
                                    UNRESOLVED, classify, prose_digest)

ROOT = Path(__file__).resolve().parents[1]

# This module deliberately holds NO clause pattern. It used to carry its own copy of the
# boundary regex and re-match the clause at write time, which made every boundary bug a silent
# corruption of prose. The boundary is now proposed once by `prose_provenance.clause_span`,
# confirmed by a reviewer in the packet, and substituted here literally.
# `tests/test_prose_provenance.py::test_the_applier_holds_no_clause_pattern` keeps it that way.


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
    for field in ("selected_document", "source_url", "source_accessed", "support",
                  "prose_digest", "current_clause", "current_state"):
        if not str(packet.get(field) or "").strip():
            raise Refused(f"{slug}: packet has no {field}")

    claimed = str(packet.get("verification_date") or "")
    try:
        date.fromisoformat(claimed)
    except (TypeError, ValueError):
        raise Refused(f"{slug}: verification_date {claimed!r} is not a real date")
    if str(packet["source_accessed"]) != claimed:
        raise Refused(
            f"{slug}: source accessed {packet['source_accessed']} but the prose line claims "
            f"{claimed}; a document read on another day did not settle this line"
        )

    # The URL is checked against the corpus, not believed from the packet. A packet naming a
    # source the product does not cite is the one way this could launder an invented document.
    recorded = score_sources(slug)
    url = str(packet["source_url"])
    if url not in recorded:
        raise Refused(f"{slug}: {url} is not a source in that product's score file")
    if recorded[url] != claimed:
        raise Refused(f"{slug}: {url} is recorded as accessed {recorded[url]}, not {claimed}")

    # One vocabulary, shared with the classifier. A sibling regex here was narrower and let
    # `substitute sources` through — the exact phrase behind the four hardware records pulled
    # out of the class-A rewording.
    document = str(packet["selected_document"])
    if METHOD_WORDS.match(document):
        raise Refused(f"{slug}: {document!r} names a method, which is what this repairs")
    if not HAS_WORD.search(document):
        raise Refused(f"{slug}: selected_document names nothing")

    # The live corpus must still be the prose this decision was taken against.
    path = ROOT / "sources" / "products" / f"{slug}.yaml"
    if not path.exists():
        raise Refused(f"{slug}: no product file")
    product = yaml.safe_load(path.read_text()) or {}
    state, live_date, _ = classify(product.get("comments"))
    if state not in UNRESOLVED:
        raise Refused(
            f"{slug}: live line is {state!r}, which this does not repair — it has changed "
            "since review"
        )
    if state != str(packet["current_state"]):
        raise Refused(
            f"{slug}: reviewed as {packet['current_state']!r}, live line is now {state!r}"
        )
    if live_date != claimed:
        raise Refused(
            f"{slug}: live line is dated {live_date}, packet claims {claimed}; applying this "
            "would move the date"
        )

    # The packet decides the clause BOUNDARY — a reviewer confirms the exact string. It does
    # not get to decide which CLAIM is rewritten. Without the three checks below, a packet
    # could nominate any other unique dated sentence: the rewrite would land there, the real
    # verification line would survive untouched, and `CANONICAL.search` would still find the
    # newly written one and call the result a success.
    comments = " ".join(str(product.get("comments") or "").split())
    clause = str(packet["current_clause"])
    if comments.count(clause) != 1:
        raise Refused(
            f"{slug}: the reviewed clause appears {comments.count(clause)} times in the live "
            "prose, not once"
        )
    head = CLAUSE_HEAD.match(clause)
    if not head:
        raise Refused(f"{slug}: current_clause is not a verification line: {clause[:60]!r}")
    if head.group(1) != claimed:
        raise Refused(
            f"{slug}: current_clause is dated {head.group(1)}, packet claims {claimed}"
        )

    live_digest = prose_digest(product)
    if live_digest != str(packet["prose_digest"]):
        raise Refused(
            f"{slug}: description/comments changed since the packet was reviewed "
            f"({live_digest[:12]} != {str(packet['prose_digest'])[:12]})"
        )


def rewrite(comments: str, clause: str, document: str, iso: str) -> str:
    """Replace the EXACT reviewed `clause` with the canonical line. No boundary is re-derived.

    The applier used to re-match the clause with a regex at write time, which made every
    boundary bug a silent corruption: `[^.;]*` stopped inside `huggingface.co` and orphaned
    the rest, and adding a whitespace test still split `the U.S. AI Safety Institute report`
    into two grammatical-looking halves. A heuristic good enough to propose a clause for
    review is not good enough to rewrite prose unsupervised.

    So the boundary is decided once, in the packet, where a human sees the exact string that
    will be replaced — and this does a literal substitution of that string, refusing if it is
    not present exactly once.

    `date` is passed in already validated rather than scraped back out of the clause. Deriving
    it here would have meant the written date came from whatever string the packet nominated,
    while every check upstream was about `verification_date`.
    """
    if not clause:
        raise Refused("packet carries no current_clause")
    occurrences = comments.count(clause)
    if occurrences != 1:
        raise Refused(
            f"the reviewed clause appears {occurrences} times in the live prose, not once; "
            "the record has changed since review"
        )
    try:
        date.fromisoformat(iso)
    except (TypeError, ValueError):
        raise Refused(f"{iso!r} is not a real date")
    head = CLAUSE_HEAD.match(clause)
    if not head:
        raise Refused(f"the reviewed clause is not a verification line: {clause[:60]!r}")
    if head.group(1) != iso:
        raise Refused(f"the reviewed clause is dated {head.group(1)}, not {iso}")
    trailing = clause[-1] if clause and clause[-1] in ".;" else "."
    return comments.replace(
        clause, f"Verified {iso} via {document.rstrip('.')}{trailing}", 1
    )


def apply_one(packet: dict) -> bool:
    check(packet)
    slug = packet["product"]
    claimed = str(packet["verification_date"])
    path = ROOT / "sources" / "products" / f"{slug}.yaml"
    text = path.read_text()
    doc = yaml.safe_load(text) or {}

    # Normalized, because that is the form the clause was proposed and reviewed in: the corpus
    # wraps `comments` across lines, so a clause spanning a wrap would never match the raw
    # text literally. `set_document_field` re-wraps on write, and `prose_digest` normalizes,
    # so this changes the whitespace of the stored line and nothing else.
    comments = " ".join(str(doc.get("comments") or "").split())

    new_comments = rewrite(
        comments, str(packet["current_clause"]), str(packet["selected_document"]), claimed
    )
    if new_comments == comments:
        return False

    # Postconditions on the RESULT, not on "a canonical line exists somewhere in it".
    state, live_date, _ = classify(new_comments)
    if state != "canonical":
        raise Refused(f"{slug}: rewrite produced a {state!r} line, not a canonical one")
    if live_date != claimed:
        raise Refused(f"{slug}: rewrite produced a line dated {live_date}, not {claimed}")
    if len(ANY_DATED.findall(new_comments)) != 1:
        raise Refused(
            f"{slug}: rewrite left {len(ANY_DATED.findall(new_comments))} dated verification "
            "lines; exactly one must remain"
        )

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
