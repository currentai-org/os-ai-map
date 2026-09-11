"""Gate: an arXiv `/abs` citation may not carry a claim that only the paper body carries.

An arXiv abstract page holds a title, the authors, the abstract and the submission history. It
does not hold the tables, the figures or the appendices, so a source that cites `/abs/<id>` for a
number taken from a table is unfalsifiable as recorded: a re-reader who opens the cited page
cannot find the figure, and cannot tell a transcription error from a page that never said it.

The corpus had twelve of these (#263). `oasst1` claimed "Guanaco/QLoRA fine-tuned on OASST1"
against `arxiv.org/abs/2305.14314`, where OASST1 occurs zero times; it occurs nineteen times in
the PDF. `dolma-toolkit` cited an abstract page for a "Table 2" that page has never shown.

**The convention.** Cite `/pdf/<id>` whenever the claim rests on something in the body. `/abs` is
correct for what the abstract page itself carries: the abstract's own wording, the title, the
authorship, the submission and withdrawal history. `/html/<id>vN` is not a substitute — it does
not exist for older papers and its version suffix goes stale.

## The two checks

**Failure: a body locator over an `/abs` URL.** A `shows` that names a table, a figure, a
section, an appendix or a page number, or that says in words that the claim is in the paper body,
is a statement that the cited page does not carry the claim. The record says so itself, so this
needs no judgment and fails. A locator inside a quotation does not count: an abstract page's own
submission history can quote an author saying "specifically figure 5", and quoting it is what an
`/abs` citation is for.

**Report: a numeric claim over an `/abs` URL.** A `shows` containing a number may be quoting the
abstract, which is legitimate and common, or may be a body figure nobody labelled. Telling those
apart means reading the page, so this is the backlog and is reported rather than failed — the
same ratchet the capability and verification gates use. A curation job must not be able to
masquerade as a regression.

Usage:
    uv run python -m build.check_citations
    uv run python -m build.check_citations --candidates

Exit status is 1 on any failure, so CI can gate on it.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

from build.vocabulary import axes

ROOT = Path(__file__).resolve().parents[1]

ABS = re.compile(r"https?://arxiv\.org/abs/", re.I)

# Each of these says, in the record's own words, that the claim sits somewhere an abstract page
# does not reach. Deliberately narrow: every pattern here is a positive statement by the curator,
# so a hit is the record contradicting its own URL rather than a guess about the page.
LOCATOR = re.compile(
    r"\b(?:in|from)\s+the\s+(?:paper|pdf)\s+body\b"
    r"|\bnot\s+on\s+(?:this|the\s+abstract)\s+page\b"
    r"|\b(?:table|figure|fig\.|appendix)\s*\d"
    r"|\bsection\s*\d"
    r"|\bp\.\s*\d",
    re.I,
)

DIGIT = re.compile(r"\d")

# A locator inside a quotation is part of what the page says, not a claim about where the
# evidence lives. `lamini` quotes an arXiv withdrawal comment - "I want to revisit some of the
# experiments in this paper, specifically figure 5" - and that comment IS on the abstract page,
# in the submission history, which is exactly what an /abs citation is for.
QUOTED = re.compile(r"\"[^\"]*\"|'[^']*'")


def unquoted(shows: str) -> str:
    return QUOTED.sub(" ", shows)


def sources() -> list[tuple[str, str, str, str]]:
    """(slug, axis, url, shows) for every recorded source, in file order."""
    found = []
    for path in sorted((ROOT / "sources" / "scores").glob("*.yaml")):
        doc = yaml.safe_load(path.read_text()) or {}
        slug = doc.get("product")
        if not slug:
            continue
        for axis in axes():
            block = doc.get(axis)
            if not isinstance(block, dict):
                continue
            for source in block.get("sources") or []:
                if not isinstance(source, dict):
                    continue
                found.append((slug, axis, source.get("url") or "", source.get("shows") or ""))
    return found


def check(rows: list[tuple[str, str, str, str]] | None = None) -> list[str]:
    """An `/abs` citation whose own `shows` places the claim in the body."""
    failures = []
    for slug, axis, url, shows in rows if rows is not None else sources():
        if not ABS.match(url):
            continue
        hit = LOCATOR.search(unquoted(shows))
        if hit:
            failures.append(
                f"{slug}:{axis} cites {url} for a claim its own `shows` places in the body "
                f"({hit.group(0)!r}). An abstract page carries the abstract and the submission "
                f"history and nothing else, so cite https://arxiv.org/pdf/ instead and re-fetch "
                f"for the digest: uv run python -m build.fetch_source <url>"
            )
    return failures


def candidates(rows: list[tuple[str, str, str, str]] | None = None) -> list[str]:
    """An `/abs` citation carrying a number. Backlog, not a failure: it may be quoting the abstract."""
    return [
        f"{slug}:{axis} {url} - {shows[:90]}"
        for slug, axis, url, shows in (rows if rows is not None else sources())
        if ABS.match(url) and DIGIT.search(shows)
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--candidates", action="store_true",
                        help="list the `/abs` citations carrying a number, which are the backlog")
    args = parser.parse_args()

    failures = check()
    for line in failures:
        print(f"  x {line}")

    if args.candidates:
        backlog = candidates()
        print(f"\n  {len(backlog)} `/abs` citation(s) carrying a number, to read by hand:")
        for line in backlog:
            print(f"    ~ {line}")

    print(f"\ncitations gate   an arXiv /abs citation for a claim only the body carries  "
          f"{'[OK]' if not failures else f'{len(failures)} failure(s)'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
