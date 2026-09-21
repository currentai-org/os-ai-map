"""Hunt for records the world now contradicts, and raise them for a person to settle.

A re-check that asks "is this byte-identical to what I saw last time" can only ever answer
"confirmed" or "drifted", and drift is a statement about a fetch, not about a score. This asks
the other question: **is there anything we already collect that says the record is wrong?**

That question is cheap, which is the point. The signal tables refresh weekly and already carry
the fields a contradiction would show up in, so the whole sweep is a warehouse read and a pass
over the corpus. Nothing is fetched. The cost that made frequent re-checking look expensive
belonged to fetching pages and diffing them, not to the checking.

## This raises; it does not decide

Every finding here is a question for a person, and `main` returns 0 with findings present. An
archived repository is a fact about a repository; `end_of_life` is a claim about a product, and
the step from one to the other is a judgment nobody should automate -- a project can be archived
because it moved, because it was folded into something larger, or because it is genuinely over,
and only the first two leave the product alive. The sweep's job is to make sure that judgment is
never skipped for want of noticing.

Acting on a finding -- recording the `end_of_life` -- removes it from the next run. Where the
answer is that the record was right all along, `sources/contradictions_settled.yaml` carries the
ruling, bound to the observed value so it expires if the observation changes. Without that file
the only way to clear a finding would be to write something untrue, since a product can outlive
the repository somebody archived.

## One leg today: retirement

`signal_github.artifact_state.is_archived` against the product's `end_of_life`. A repository its
owner marked read-only, under a product that records no end of life. Both sides are booleans
about the same artifact, which is what makes the comparison safe to automate.

A license leg belongs here and is not here yet. The obvious form of it -- the recorded openness
license against `license_spdx_id` -- was built, reviewed twice, and withdrawn both times for the
same reason in different clothes: the corpus records a license as a NAME plus a qualification,
and the qualification lives in more places than a comparison can guess at. It sits in the detail
(`code,via LICENSE-CODE`), after the grade in the detail (`OSI, client SDKs only`), inside the
name (`Apache-2.0-WITH-LLVM-exception`), and as one scoped part of a compound whose other part
covers the weights. A comparison that misses any of them reports a record that was already right,
every week, until people stop reading the queue. Getting it right means reusing the rubric's own
parsing rather than re-deriving scope from punctuation, which is its own piece of work.

## What a finding is, and is not

A finding is one observation disagreeing with one record. It is not a statement that the record
is wrong -- that is the question being raised, not its answer -- and it is not a statement that
anything else was checked. The sweep covers what the signal tables carry, which is a fraction of
what a score records.

"""

from __future__ import annotations

import argparse
import dataclasses
import json
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import yaml

ROOT = Path(__file__).resolve().parent.parent

RETIREMENT = "retirement"


STATE_QUERY = """
SELECT
  product_slug,
  repo,
  is_archived,
  http_status,
  pushed_at,
  fetched_at
FROM currentai.signal_github.artifact_state
"""


@dataclasses.dataclass(frozen=True)
class Finding:
    """One record the world contradicts, with both sides and where each came from."""

    leg: str
    product_slug: str
    recorded: str
    observed: str
    artifact: str
    source_column: str
    as_of: str
    #: The observed value a settlement is bound to -- `archived`, or the SPDX id seen. A ruling
    #: covers this value and nothing else, so a different observation raises the finding again.
    settles: str = ""

    @property
    def key(self) -> tuple[str, str, str, str]:
        return (self.leg, self.product_slug, self.artifact, self.settles)

    def line(self) -> str:
        return (
            f"{self.leg}: {self.product_slug} -- recorded {self.recorded}, "
            f"observed {self.observed} ({self.artifact}, {self.source_column}, {self.as_of})"
        )


def _text(value: object) -> str:
    return "" if value is None else str(value).strip()


#: Spellings of true that reach here as text. Anything not in this set, and not a real boolean,
#: is treated as MISSING rather than as false-because-falsy.
_TRUE_TEXT = frozenset({"true", "t", "1", "yes", "y"})


def _truthy(value: object) -> bool:
    """A warehouse boolean, where a missing value is false rather than whatever `bool()` says.

    `warehouse.query` converts through pandas, and a null boolean column arrives as `nan` -- for
    which `bool(nan)` is **True**. Read naively, a product whose archived flag was never
    populated reports as archived and lands in the queue as a retirement finding with nothing
    behind it. The producer permits a null flag, so this is reachable rather than theoretical.

    A missing value is not a contradiction: it is the absence of an observation, and this sweep
    only ever fires on something a signal actually said.
    """
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() in _TRUE_TEXT
    if isinstance(value, float) and value != value:  # nan, including pandas' null boolean
        return False
    try:
        return bool(value)
    except (TypeError, ValueError):  # pandas.NA raises rather than answering
        return False





def retirement_findings(rows: Iterable[Mapping], products: Mapping[str, Mapping]) -> list[Finding]:
    """Products whose repository is archived and whose record does not say the product ended."""
    out: list[Finding] = []
    for row in rows:
        if not _truthy(row.get("is_archived")):
            continue
        slug = _text(row.get("product_slug"))
        product = products.get(slug)
        if product is None or product.get("end_of_life"):
            continue
        pushed = _text(row.get("pushed_at")) or "unknown"
        out.append(
            Finding(
                leg=RETIREMENT,
                product_slug=slug,
                recorded="no end_of_life",
                observed=f"repository archived, last pushed {pushed[:10]}",
                artifact=_text(row.get("repo")),
                source_column="is_archived",
                as_of=_text(row.get("fetched_at"))[:10],
                settles="archived",
            )
        )
    return sorted(out, key=lambda f: (f.product_slug, f.artifact))


def settled_keys(settled: Iterable[Mapping]) -> set[tuple[str, str, str, str]]:
    """The observations a person has ruled on, keyed the way a `Finding` keys itself.

    An entry with no `note` is ignored rather than honoured. A settlement is a ruling, and a
    ruling with no reason is indistinguishable from a finding somebody wanted to stop seeing;
    honouring it would make this file the place a real contradiction goes to hide.
    """
    out = set()
    for entry in settled or ():
        if not str(entry.get("note") or "").strip():
            continue
        out.add((
            str(entry.get("leg") or ""),
            str(entry.get("product_slug") or ""),
            str(entry.get("artifact") or ""),
            str(entry.get("settles") or ""),
        ))
    return out


def sweep(
    rows: Iterable[Mapping],
    products: Mapping[str, Mapping],
    scores: Mapping[str, Mapping],
    settled: Iterable[Mapping] = (),
) -> list[Finding]:
    """Every leg, over one read of the state table, minus what a person has already ruled on."""
    rows = list(rows)
    found = retirement_findings(rows, products)
    ruled = settled_keys(settled)
    return [f for f in found if f.key not in ruled]


def _load(directory: Path) -> dict[str, dict]:
    return {
        path.stem: yaml.safe_load(path.read_text()) or {}
        for path in sorted(directory.glob("*.yaml"))
    }


def corpus(root: Path | None = None) -> tuple[dict[str, dict], dict[str, dict], list[dict]]:
    """`(products, scores, settled)`."""
    base = root or ROOT
    ledger = base / "sources" / "contradictions_settled.yaml"
    settled = (yaml.safe_load(ledger.read_text()) or {}).get("settled") or [] if ledger.exists() else []
    return _load(base / "sources" / "products"), _load(base / "sources" / "scores"), settled


def queue_markdown(findings: Sequence[Finding]) -> str:
    """The findings as the queue a person reads, grouped by leg.

    Each line carries both sides and the artifact, so the queue can be worked through without
    re-running the sweep or opening the warehouse.
    """
    if not findings:
        return (
            "# Contradiction queue\n\n"
            "No contradiction within this sweep's coverage, which today is GitHub archival. "
            "Other collected signals -- license ids, Hub gating, weights availability, a disabled "
            "or vanished artifact -- are not examined here, so this is not a statement that every "
            "record was checked.\n"
        )
    lines = ["# Contradiction queue", ""]
    for leg, heading, action in (
        (RETIREMENT, "Archived repository, no recorded end of life",
         "Record `end_of_life` on the product, or settle it in `sources/contradictions_settled.yaml` "
         "with the reason the product outlived its repository."),
    ):
        rows = [f for f in findings if f.leg == leg]
        if not rows:
            continue
        lines += [f"## {heading} ({len(rows)})", "", action, ""]
        lines += ["| product | recorded | observed | artifact | as of |", "|---|---|---|---|---|"]
        lines += [
            f"| `{f.product_slug}` | {f.recorded} | {f.observed} | `{f.artifact}` | {f.as_of} |"
            for f in rows
        ]
        lines.append("")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None, root: Path | None = None, rows: Iterable[Mapping] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--queue", type=Path, metavar="PATH", help="write the queue markdown here")
    parser.add_argument("--json", action="store_true", help="print the findings as JSON")
    parser.add_argument(
        "--strict", action="store_true",
        help="exit 1 when anything is contradicted. Off by default: this raises for a person, "
             "and a check that blocks the branch on a question nobody has answered yet stops "
             "being read and starts being worked around",
    )
    args = parser.parse_args(argv)

    if rows is None:
        from build.warehouse import query

        rows = query(STATE_QUERY)
    products, scores, settled = corpus(root)
    findings = sweep(rows, products, scores, settled)

    if args.json:
        print(json.dumps([dataclasses.asdict(f) for f in findings], indent=2))
    else:
        for finding in findings:
            print(finding.line())
        print(f"\n{len(findings)} contradicted")
    if args.queue:
        args.queue.write_text(queue_markdown(findings))
    return 1 if (args.strict and findings) else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
