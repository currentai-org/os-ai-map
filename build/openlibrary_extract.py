"""Count Open Library works per language from a monthly editions dump.

The language classification reads Open Library only from a reproducible extract of Open
Library's monthly data dumps, never from its search API (R-2026-11-10-r;
docs/reference/language-classification.md, "Written material"). This module is that extract.

It streams one editions dump (`ol_dump_editions_<date>.txt.gz`, published monthly through
https://openlibrary.org/developers/dumps) without storing it, and for every MARC language
code counts:

- `works`: distinct works with at least one edition in that language, the quantity the
  method's `open_library_works` measure reads;
- `editions`: editions in that language.

An edition with several languages counts once for each. An edition with no work key counts
toward `editions` only. The output is a CSV, one row per MARC code, plus a JSON sidecar that
pins the dump: its URL, date, byte count, SHA-256 and the number of lines read. Rerunning on
the same dump gives the same bytes.

Usage:
    uv run python -m build.openlibrary_extract --date 2026-10-31 --out-dir sources/snapshots
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import re
import sys
import urllib.request
from array import array
from collections import defaultdict
from pathlib import Path

DUMP_URL = "https://archive.org/download/ol_dump_{date}/ol_dump_editions_{date}.txt.gz"
USER_AGENT = "gapmap-language-representation/1.0 (+https://github.com/currentai-org/os-ai-map)"

LANGUAGE_RE = re.compile(r'"/languages/([a-z]{3})"')
WORK_RE = re.compile(r'"/works/OL(\d+)W"')


class HashingReader:
    """A file-like wrapper that hashes and counts every byte read through it."""

    def __init__(self, raw):
        self.raw = raw
        self.sha = hashlib.sha256()
        self.bytes = 0

    def read(self, size: int = -1) -> bytes:
        chunk = self.raw.read(size)
        self.sha.update(chunk)
        self.bytes += len(chunk)
        return chunk


def count(stream, progress_every: int = 5_000_000) -> tuple[dict, dict, int]:
    """Per-language distinct-work arrays and edition counts from an editions dump stream."""
    works: dict[str, array] = defaultdict(lambda: array("I"))
    editions: dict[str, int] = defaultdict(int)
    lines = 0
    for raw_line in stream:
        lines += 1
        if progress_every and lines % progress_every == 0:
            print(f"{lines:,} lines", file=sys.stderr, flush=True)
        line = raw_line.decode("utf-8", errors="replace")
        # Columns: type, key, revision, last_modified, JSON. Only the JSON holds the fields.
        record = line.rsplit("\t", 1)[-1]
        languages = set(LANGUAGE_RE.findall(record))
        if not languages:
            continue
        work_ids = {int(w) for w in WORK_RE.findall(record)}
        for code in languages:
            editions[code] += 1
            works[code].extend(work_ids)
    return works, editions, lines


def distinct(values: array) -> int:
    return len(set(values))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--date", required=True, help="dump date, YYYY-MM-DD")
    parser.add_argument("--out-dir", type=Path, default=Path("sources/snapshots"))
    parser.add_argument("--file", type=Path, help="read a local copy of the dump instead")
    args = parser.parse_args(argv)

    url = DUMP_URL.format(date=args.date)
    if args.file:
        raw = args.file.open("rb")
    else:
        raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": USER_AGENT}))
    hashing = HashingReader(raw)
    with gzip.GzipFile(fileobj=hashing) as stream:
        works, editions, lines = count(stream)

    rows = sorted((code, distinct(works[code]), editions[code]) for code in editions)
    stem = f"openlibrary-works-by-language-{args.date}"
    args.out_dir.mkdir(parents=True, exist_ok=True)
    with (args.out_dir / f"{stem}.csv").open("w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["marc_code", "works", "editions"])
        writer.writerows(rows)
    meta = {
        "source_url": url,
        "dump_date": args.date,
        "bytes": hashing.bytes,
        "sha256": hashing.sha.hexdigest(),
        "lines": lines,
        "languages": len(rows),
        "counts": "works = distinct work keys with an edition in the language; editions = editions in the language",
    }
    (args.out_dir / f"{stem}.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta))
    return 0


if __name__ == "__main__":
    sys.exit(main())
