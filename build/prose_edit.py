"""Rewrite one prose field on one record, through `build/components.py`, with the guards a
prose pass is not allowed to think about.

The pass that tightens notes and footnotes (`skills/clean-corpus-prose/SKILL.md`) is run by
many workers over many files, and the rules it must not break are all mechanical: edit through
the helpers so nothing else in the file moves; keep the phrases two gates read; keep a date
that is on the product-fact allowlist; never leave a note empty; never write the retired
`Verified … via` line. Each worker remembering all five is how one of them gets forgotten, so
this puts them in one place and refuses rather than guessing.

    uv run python -m build.prose_edit note <slug> <axis> --text-file new.txt
    uv run python -m build.prose_edit shows <slug> <axis> <index> --text-file new.txt
    uv run python -m build.prose_edit comments <slug> --text-file new.txt
    uv run python -m build.prose_edit comments <slug> --drop

The text is read from a file rather than an argument so a worker's shell quoting cannot mangle
an apostrophe. Trailing whitespace is stripped; internal whitespace is left alone and the YAML
dumper re-wraps the field.

Refusals, each with its reason on stderr:

  * a note that would be empty, or over `prose_worklist.NOTE_CEILING`;
  * a note that drops a phrase `sweep_status.UNDERSTATES` / `INFLATED` matched in the old text
    (the under-coverage set is pinned in tests; withdrawing the claim is a re-read, not a
    rewording), or that introduces one the old text did not carry (the set would grow, and a
    prose pass makes no new claim), unless `--allow-phrase-change`;
  * a note on `tests/test_score_notes.DATES_THAT_ARE_PRODUCT_FACTS` that would lose its date;
  * a note that would gain an ISO date it did not have;
  * a `comments` that carries a dated verification sentence;
  * a `shows` that would be empty.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

from build.components import drop_document_field, set_document_field, set_field, set_source
from build.product_prose import dated_verification
from build.prose_worklist import NOTE_CEILING
from build.sweep_status import INFLATED, UNDERSTATES
from build.vocabulary import axes

ROOT = Path(__file__).resolve().parents[1]
ISO_DATE = re.compile(r"\b20\d\d-\d\d-\d\d\b")


def _product_fact_dates() -> set[tuple[str, str]]:
    from tests.test_score_notes import DATES_THAT_ARE_PRODUCT_FACTS

    return DATES_THAT_ARE_PRODUCT_FACTS


def _read_text(path: str) -> str:
    text = Path(path).read_text()
    return text.strip()


def _refuse(reason: str) -> int:
    print(f"refused: {reason}", file=sys.stderr)
    return 2


def edit_note(slug: str, axis: str, text: str, allow_phrase_change: bool = False) -> str | None:
    """Return a refusal reason, or None after writing."""
    path = ROOT / "sources" / "scores" / f"{slug}.yaml"
    doc = yaml.safe_load(path.read_text()) or {}
    old = ((doc.get(axis) or {}).get("note")) or ""
    if not text:
        return "a note may not be emptied; abstaining is a note too"
    if len(text) > NOTE_CEILING:
        return f"{len(text)} characters is over the {NOTE_CEILING} guard; move detail into shows"
    for pattern, name in ((UNDERSTATES, "UNDERSTATES"), (INFLATED, "INFLATED")):
        before, after = pattern.search(old), pattern.search(text)
        if before and not after and not allow_phrase_change:
            return (f"the old note matched sweep_status.{name} ({before.group(0)!r}) and the new "
                    "one does not; the under-coverage set is pinned. Keep the phrase, or pass "
                    "--allow-phrase-change if the claim itself is being withdrawn")
        if after and not before and not allow_phrase_change:
            return (f"the new note introduces {after.group(0)!r}, which check_channel_authority "
                    f"reads as an under-coverage admission (sweep_status.{name}); the pinned set "
                    "would grow. A prose pass makes no new claim: reword it, or pass "
                    "--allow-phrase-change if the record already supports the admission")
    had_date, has_date = bool(ISO_DATE.search(old)), bool(ISO_DATE.search(text))
    if (slug, axis) in _product_fact_dates() and had_date and not has_date:
        return "this axis is on DATES_THAT_ARE_PRODUCT_FACTS; its date is a fact about the product"
    if has_date and not had_date:
        return "the new note states a date the old one did not; when something happened is git's"
    new_text = set_field(path.read_text(), text, axis=axis, key="note")
    path.write_text(new_text)
    return None


def edit_shows(slug: str, axis: str, index: int, text: str) -> str | None:
    path = ROOT / "sources" / "scores" / f"{slug}.yaml"
    doc = yaml.safe_load(path.read_text()) or {}
    sources = (doc.get(axis) or {}).get("sources") or []
    if not 0 <= index < len(sources):
        return f"{axis} has {len(sources)} source(s); no index {index}"
    if not text:
        return "a shows may not be emptied"
    url = sources[index].get("url")
    new_text = set_source(path.read_text(), axis, url, {"shows": text}, index=index)
    path.write_text(new_text)
    return None


def edit_comments(slug: str, text: str | None) -> str | None:
    path = ROOT / "sources" / "products" / f"{slug}.yaml"
    raw = path.read_text()
    doc = yaml.safe_load(raw) or {}
    if text is None or not text:
        if "comments" not in doc:
            return "no comments field to drop"
        path.write_text(drop_document_field(raw, "comments"))
        return None
    if (sentence := dated_verification(text)):
        return f"comments may not carry a dated verification sentence: {sentence!r}"
    if "comments" not in doc:
        return "this product has no comments field; a prose pass adds none"
    path.write_text(set_document_field(raw, "comments", text))
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="field", required=True)

    p_note = sub.add_parser("note")
    p_note.add_argument("slug")
    p_note.add_argument("axis", choices=axes())
    p_note.add_argument("--text-file", required=True)
    p_note.add_argument("--allow-phrase-change", action="store_true")

    p_shows = sub.add_parser("shows")
    p_shows.add_argument("slug")
    p_shows.add_argument("axis", choices=axes())
    p_shows.add_argument("index", type=int)
    p_shows.add_argument("--text-file", required=True)

    p_comments = sub.add_parser("comments")
    p_comments.add_argument("slug")
    group = p_comments.add_mutually_exclusive_group(required=True)
    group.add_argument("--text-file")
    group.add_argument("--drop", action="store_true")

    args = parser.parse_args()
    if args.field == "note":
        reason = edit_note(args.slug, args.axis, _read_text(args.text_file), args.allow_phrase_change)
    elif args.field == "shows":
        reason = edit_shows(args.slug, args.axis, args.index, _read_text(args.text_file))
    else:
        reason = edit_comments(args.slug, None if args.drop else _read_text(args.text_file))
    if reason:
        return _refuse(reason)
    print(f"wrote {args.field} on {args.slug}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
