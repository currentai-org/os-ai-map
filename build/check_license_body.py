"""Fail when a record argues against GitHub's licence classifier without citing the body.

GitHub's licence endpoint reports NOASSERTION whenever the LICENSE file is not a
byte-recognizable copy of a template. Three things in this corpus trip it, all of them
benign, and all of them found by reading the file:

    slurm            COPYING opens with a SLURM LICENSE AGREEMENT preamble before the GPL
    dlrover          LICENSE opens "The following Apache license applies to all files"
    openpai          the MIT text is indented four spaces
    executorch       the BSD-3-Clause header names eight copyright holders
    nemo-guardrails  an SPDX header sits above the Apache text

So NOASSERTION is not a licence finding, it is a prompt to read the file - and the corpus
already does. 23 records say so in prose and 20 of them cite the body they read. This gate
holds that line: if a record's prose disputes the classifier, the evidence for what the
licence actually says has to be a licence FILE, not the API record that reported
NOASSERTION in the first place.

The failure it prevents is narrow and real. A curator who reads NOASSERTION, decides the
repository "looks Apache", and records Apache-2.0 leaves behind a record that is
indistinguishable from one written by a curator who opened the file - same score, same
prose, same confidence. The citation is the only thing that separates them, and without it
the next re-verification pass has nothing to re-read.

Scope, and why it ratchets: the population is records whose own prose MENTIONS
NOASSERTION - a deliberately broader test than "disputes it", because a record that
explains why the classifier did or did not report NOASSERTION is making a claim about the
licence body either way, and a claim about a body should cite one. A record that never
mentions it is not covered: its licence claim rests on whatever the classifier said, and
agreeing with a classifier needs no second source.
"""
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCORES = ROOT / "sources" / "scores"
PRODUCTS = ROOT / "sources" / "products"

# A licence BODY is decided on the URL's PATH, never on the whole string. The first draft
# matched the raw URL with `$`-anchored alternatives and got it wrong in both directions:
# `/blob/main/LICENSE.md#L1` and `/legal/LICENSE?download=1` were rejected because a fragment
# or a query follows the filename, while `raw.githubusercontent.com/o/r/main/README.md`,
# `/blob/main/NOT_A_LICENSE.txt` and a repository literally named `github.com/o/LICENSE` were
# accepted because the pattern matched a substring of something that is not a licence file.
#
# `api.github.com/repos/<o>/<r>/license` is excluded by name: it is the endpoint that returned
# NOASSERTION, so letting it answer the dispute is circular.
LICENCE_FILE = re.compile(r"^(licen[cs]e|copying|notice)([.\-][A-Za-z0-9._\-]+)?$", re.IGNORECASE)


def BODY(url: str) -> bool:  # noqa: N802 - reads as a matcher at the call sites
    """True when `url` names a licence FILE rather than a page that merely mentions one.

    The test is the last path segment, so a fragment or a query cannot defeat it and a
    same-named repository cannot satisfy it: `github.com/o/LICENSE` has only two path
    segments and a licence file always sits deeper than the repository it belongs to.
    """
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    segments = [s for s in parsed.path.split("/") if s]
    if not segments:
        return False
    if host == "api.github.com" and segments[-1:] == ["license"]:
        return False
    # On GitHub the filename has to sit deeper than owner/repo, or a repository NAMED
    # `LICENSE` would satisfy the gate. Off GitHub there is no such shape to exclude, and a
    # vendor licence page at `/legal/LICENSE` is a real body.
    if host in {"github.com", "raw.githubusercontent.com"} and len(segments) < 3:
        return False
    return bool(LICENCE_FILE.match(segments[-1]))


def _prose(slug: str, openness: dict) -> str:
    """Everything a curator could have written the dispute into, for one product."""
    parts = [str(openness.get(key) or "") for key in ("note", "raw")]
    product = PRODUCTS / f"{slug}.yaml"
    if product.exists():
        record = yaml.safe_load(product.read_text()) or {}
        parts.append(str(record.get("comments") or ""))
    return " ".join(parts)


def disputed(scores_dir: Path = SCORES) -> list[tuple[str, list[str]]]:
    """(slug, openness source urls) for every record whose prose disputes the classifier."""
    found = []
    for path in sorted(scores_dir.glob("*.yaml")):
        record = yaml.safe_load(path.read_text()) or {}
        openness = record.get("openness") or {}
        if "NOASSERTION" not in _prose(path.stem, openness).upper():
            continue
        urls = [str(s.get("url") or "") for s in (openness.get("sources") or [])]
        found.append((path.stem, urls))
    return found


def failures(scores_dir: Path = SCORES) -> list[str]:
    return [slug for slug, urls in disputed(scores_dir) if not any(BODY(u) for u in urls)]


def main() -> int:
    population = disputed()
    bad = failures()
    print(f"{len(population)} record(s) dispute GitHub's licence classifier in prose")
    print(f"  {len(population) - len(bad)} cite a licence body; {len(bad)} do not")
    for slug in bad:
        print(
            f"  ! {slug}: openness prose says NOASSERTION but no source is a licence file. "
            "Cite the raw LICENSE/COPYING body that was read."
        )
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
