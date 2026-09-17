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

Scope, and why it ratchets: the population is records whose own prose mentions
NOASSERTION. A record that never disputes the classifier is not covered, because there is
nothing to check - its licence claim rests on whatever the classifier said and agreeing
with a classifier needs no second source.
"""
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCORES = ROOT / "sources" / "scores"
PRODUCTS = ROOT / "sources" / "products"

# A licence BODY: the raw file, a blob view of one, or a path ending in the usual names.
# `api.github.com/repos/<o>/<r>/license` is deliberately NOT here - it is the endpoint that
# returns NOASSERTION, so accepting it would let the disputed evidence answer the dispute.
CLASSIFIER = re.compile(r"api\.github\.com/repos/[^/]+/[^/]+/license/?$", re.IGNORECASE)

_BODY = re.compile(
    r"(raw\.githubusercontent\.com/.+)"
    r"|(/blob/[^?#]*(LICENSE|LICENCE|COPYING|NOTICE)[^/?#]*$)"
    r"|(/(LICENSE|LICENCE|COPYING|NOTICE)[^/?#]*$)",
    re.IGNORECASE,
)


def BODY(url: str):  # noqa: N802 - reads as a matcher at the call sites
    """Truthy when `url` points at a licence FILE rather than at the classifier.

    The exclusion is the whole point: `api.github.com/repos/<o>/<r>/license` ends in
    `/license` and would otherwise look like a body, but it is the endpoint that returned
    NOASSERTION in the first place. Letting it answer the dispute is circular.
    """
    if CLASSIFIER.search(url):
        return None
    return _BODY.search(url)


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
