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

## Two legs: retirement and license

**Retirement.** `signal_github.artifact_state.is_archived` against the product's `end_of_life`. A
repository its owner marked read-only, under a product that records no end of life. Both sides are
booleans about the same artifact, which is what makes the comparison safe to automate.

**License.** `signal_github.artifact_state.license_spdx_id` against the license the product's
openness score records. This one was built, reviewed twice and withdrawn both times, because the
corpus does not record a license as a bare name: it records a name plus a qualification, and the
qualification is not in one place. It sits in the detail as a scope and a file
(`code,via LICENSE-CODE`), after the grade in the detail (`OSI, client SDKs only`), inside the name
(`Apache-2.0-WITH-LLVM-exception`), and as one scoped part of a compound whose other part covers
the weights.

So the abstentions are not a detail of this leg. They ARE the leg, and the rules are below.

## What the license leg compares, and what it refuses to

The observation is one thing: the license GitHub classifies at the root of a repository. That is a
statement about CODE. So the leg compares it only against a recorded license that is also about
that code, and abstains everywhere else.

  * **Scope decides, not product type.** A part explicitly scoped to code -- a `code` token in the
    detail, or a `code ` prefix on the name -- is comparable whatever kind of product carries it,
    which is what makes the code-scoped half of a compound on a dataset or a model comparable. A
    part that names another artifact is not. Where the record states no scope, the product's own
    type supplies the default: for software the repository is the product, and for a model or a
    dataset the recorded license is about the weights or the data and this observation cannot
    speak to it.
  * **Any qualification abstains, wherever it sits.** A name that is not a bare license id, a
    `WITH ... exception` inside the name, or a detail carrying anything beyond the grade and the
    scope. `OSI` and `non-OSI` are grades and `code` is a scope; everything else is a
    qualification, including a named license file, a list of covered packages, and a carve-out.
  * **The observation binds to one artifact.** A product with more than one repository row is
    abstained on, because nothing here says which repository the recorded license was read off.
  * **The comparison itself is case-insensitive**, which `normalize_license` is not -- see below.

Getting this wrong is not a small cost. Every finding the earlier attempts produced was a record
that was already right and already explained in its own file, and a queue that reports correct
records is a queue nobody reads by its second week.

## normalize_license is case-sensitive, and this leg works around it

`normalize_license` resolves its alias table on a lowercased key but returns the value unchanged
when there is no alias, so a recorded `mit` and an observed `MIT` come back different. This leg
folds case at the point of comparison rather than changing that function, because
`normalize_license` also feeds tier matching and making it case-insensitive there is a scoring
decision rather than a cleanup.

## What a finding is, and is not

A finding is one observation disagreeing with one record. It is not a statement that the record
is wrong -- that is the question being raised, not its answer -- and it is not a statement that
anything else was checked. The sweep covers what the signal tables carry, which is a fraction of
what a score records.

"""

from __future__ import annotations

import argparse
import collections
import dataclasses
import json
import re
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import yaml

from build.check_rubric import (
    SCOPE_PREFIX,
    entries,
    is_license_key,
    license_parts_of,
    normalize_license,
)

ROOT = Path(__file__).resolve().parent.parent

RETIREMENT = "retirement"
LICENSE = "license"


STATE_QUERY = """
SELECT
  product_slug,
  repo,
  is_archived,
  license_spdx_id,
  http_status,
  pushed_at,
  fetched_at
FROM currentai.signal_github.artifact_state
"""

#: Detail tokens that are a GRADE rather than a qualification. A grade says how the license rates
#: against OSI; it does not narrow what the license covers, so it leaves the part comparable.
GRADE_TOKENS = frozenset({"osi", "non-osi"})

#: Detail tokens that scope a part to the repository's code. The observation is a repository
#: license, so this is the one scope it can speak to.
CODE_TOKENS = frozenset({"code"})

#: Detail tokens naming an artifact that is NOT the repository's code. Recorded on a part, they
#: settle the scope without falling through to the product type.
NON_CODE_TOKENS = frozenset({"model", "weights", "data", "dataset", "docs"})

#: The spdx values that are an absence of an observation rather than a license. GitHub returns
#: NOASSERTION for a repository whose LICENSE it cannot classify, which is not a contradiction of
#: anything.
ABSTAIN_SPDX = frozenset({"", "none", "noassertion", "other"})

#: A bare license id: what a name has to look like before it can be compared to an spdx id.
#: Deliberately strict - a name carrying a space, a paren or a slash is a recording that has not
#: been split, and resolving it on its first token is how a comparison invents a contradiction.
BARE_LICENSE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.+-]*$")

#: A qualification written into the name itself, which no amount of detail-reading catches.
QUALIFIED_NAME = re.compile(r"(?i)with|exception")


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
        # `settles` is case-folded because the license leg's own comparison is: it treats an
        # observed `MIT` and `mit` as the same observation, so a settlement bound to one has to
        # cover the other. Without this, a spelling change in what GitHub returns reopens a
        # question a person already answered. Harmless for `archived`, which has one spelling.
        return (self.leg, self.product_slug, self.artifact, self.settles.strip().lower())

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





def detail_tokens(part: Mapping) -> list[str]:
    """A recorded part's detail as its comma-separated tokens, lowercased.

    Only a comma separates tokens. A semicolon does not: `OSI; covers the code` is one clause a
    person wrote, and splitting it would turn a qualification into two tokens that both look
    allowed. Leaving it whole makes it fail the allowlist, which is the intended answer.
    """
    detail = part.get("detail")
    if not detail:
        return []
    return [token.strip().lower() for token in str(detail).split(",")]


def part_scope(part: Mapping, product_type: str) -> str:
    """`code` if this recorded license part covers the repository's code, else `other`.

    An explicit scope wins over the product type in both directions, which is what lets the
    code-scoped half of a compound on a dataset be compared while the dataset's own license is
    left alone. Where the record states no scope, the product type supplies it: a software
    product IS its repository, and a model or dataset product's unqualified license is about the
    weights or the data.

    `hardware` and any unknown type fall to `other`, because the repository underneath a hardware
    product is a driver or an SDK rather than the product.
    """
    tokens = set(detail_tokens(part))
    name = str(part.get("name") or "").strip().lower()
    if tokens & CODE_TOKENS or name.startswith("code "):
        return "code"
    if tokens & NON_CODE_TOKENS or name.startswith("model "):
        return "other"
    return "code" if product_type == "software" else "other"


def comparable_license(entry: object, product_type: str) -> tuple[dict | None, str]:
    """The one recorded part a repository license may be compared against, or why not.

    Returns `(part, "")` or `(None, reason)`. The reason is written to be printed at somebody,
    because an abstention here is the leg working rather than the leg failing, and a curator
    reading the run needs to know which rule stopped it.
    """
    parts = license_parts_of(entry)
    if not parts:
        return None, "no license parts recorded"

    scoped = [part for part in parts if part_scope(part, product_type) == "code"]
    if len(scoped) > 1:
        return None, "more than one recorded part covers the code"
    if not scoped:
        if len(parts) > 1:
            return None, "no part of the compound covers the code"
        return None, f"the recorded license is not about the repository ({product_type or 'unknown type'})"

    part = scoped[0]
    # Strip the scope prefix before judging the name. A record spelled `code Apache-2.0` declares
    # its scope in the one place `part_scope` reads it, and then the space in that very prefix
    # would fail the bare-id test below -- the leg refusing a record for saying exactly what the
    # leg asked it to say. `SCOPE_PREFIX` is the rubric's own rule rather than a second copy of
    # it. Only the prefix is removed: running the whole of `normalize_license` here would apply
    # the alias table too, which can turn a prose name like `custom weights license` into a
    # bare-looking one and let a comparison through that should never have started.
    name = SCOPE_PREFIX.sub("", str(part.get("name") or "").strip()).strip()
    if not BARE_LICENSE_ID.match(name):
        return None, "the recorded name is not a bare license id"
    if QUALIFIED_NAME.search(name):
        return None, "the name carries a qualification"
    extra = [t for t in detail_tokens(part) if t not in GRADE_TOKENS and t not in CODE_TOKENS]
    if extra:
        # The reason names the RULE, not the token that tripped it. Interpolating the token
        # gives every product its own tally line, which turns the one summary a curator reads
        # into a list as long as the corpus and hides how often each rule actually fires.
        return None, "the detail qualifies the license"
    return part, ""


def license_findings(
    rows: Iterable[Mapping],
    products: Mapping[str, Mapping],
    scores: Mapping[str, Mapping],
) -> tuple[list[Finding], collections.Counter]:
    """Repository licenses that contradict the license the openness score records.

    Returns the findings and a tally of why every other product was abstained on. The tally is
    returned rather than logged because a leg this conservative has to be able to show that it
    abstained for a reason, and a silent 0 findings is indistinguishable from a broken comparison.
    """
    abstained: collections.Counter = collections.Counter()
    seen: dict[str, list[Mapping]] = {}
    for row in rows:
        seen.setdefault(_text(row.get("product_slug")), []).append(row)

    out: list[Finding] = []
    for slug, product_rows in sorted(seen.items()):
        if not slug:
            # Rows carrying no product slug all group under the empty key, so without this they
            # would collapse into a single "more than one repository row" and report one
            # abstention for what is really N malformed rows.
            abstained["the row carries no product slug"] += len(product_rows)
            continue
        if len(product_rows) > 1:
            abstained["the product has more than one repository row"] += 1
            continue
        row = product_rows[0]
        spdx = _text(row.get("license_spdx_id"))
        if spdx.lower() in ABSTAIN_SPDX:
            abstained["no usable spdx id was observed"] += 1
            continue
        product = products.get(slug)
        score = scores.get(slug)
        if product is None or score is None:
            abstained["no product or score file"] += 1
            continue
        components = (score.get("openness") or {}).get("components") or {}
        if not isinstance(components, dict):
            abstained["components are not structured"] += 1
            continue
        # Counted across `context` too. `max` records its repository license there because no
        # ladder reads it, and it is still the second license that makes this leg abstain.
        recorded_entries = entries(components)
        keys = [key for key in recorded_entries if is_license_key(key)]
        if len(keys) != 1:
            abstained["not exactly one recorded license key"] += 1
            continue

        part, why = comparable_license(recorded_entries[keys[0]], _text(product.get("type")))
        if part is None:
            abstained[why] += 1
            continue

        recorded = str(part["name"]).strip()
        if normalize_license(recorded).lower() == normalize_license(spdx).lower():
            continue
        out.append(
            Finding(
                leg=LICENSE,
                product_slug=slug,
                recorded=f"license {recorded}",
                observed=f"the repository is classified {spdx}",
                artifact=_text(row.get("repo")),
                source_column="license_spdx_id",
                as_of=_text(row.get("fetched_at"))[:10],
                settles=spdx,
            )
        )
    return out, abstained


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
            str(entry.get("settles") or "").strip().lower(),
        ))
    return out


def representation_gaps(settled: Iterable[Mapping]) -> list[Mapping]:
    """Settlements that suppress a finding the schema cannot represent, rather than a defect.

    Most settlements say the record was right. A few say the opposite: the finding is real and
    there is no field to record the answer in. Filed as an ordinary settlement, one of those
    leaves the queue looking exactly like a vindicated record, which is the silencing this ledger
    exists to prevent. They are printed on every run so the suppression stays visible, and each is
    a standing argument for changing the schema rather than a closed question.
    """
    return [entry for entry in settled or () if entry.get("class") == "representation-gap"]


def sweep(
    rows: Iterable[Mapping],
    products: Mapping[str, Mapping],
    scores: Mapping[str, Mapping],
    settled: Iterable[Mapping] = (),
) -> tuple[list[Finding], collections.Counter]:
    """Every leg, over one read of the state table, minus what a person has already ruled on.

    Returns the findings and the license leg's abstention tally. The tally is part of the result
    rather than a debug print because this leg refuses far more often than it fires, and a run
    reporting nothing has to be able to show it looked.
    """
    rows = list(rows)
    licensed, abstained = license_findings(rows, products, scores)
    found = retirement_findings(rows, products) + licensed
    ruled = settled_keys(settled)
    return [f for f in found if f.key not in ruled], abstained


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
            "No contradiction within this sweep's coverage, which today is GitHub archival and the "
            "repository license. Other collected signals -- Hub gating, weights availability, a "
            "disabled or vanished artifact -- are not examined here, and the license leg abstains "
            "wherever the recorded license is not about the repository's code, so this is not a "
            "statement that every record was checked.\n"
        )
    lines = ["# Contradiction queue", ""]
    for leg, heading, action in (
        (RETIREMENT, "Archived repository, no recorded end of life",
         "Record `end_of_life` on the product, or settle it in `sources/contradictions_settled.yaml` "
         "with the reason the product outlived its repository."),
        (LICENSE, "Repository license contradicts the recorded license",
         "Re-read the repository and correct the score, or settle it in "
         "`sources/contradictions_settled.yaml` with the reason the recorded license is right. "
         "Check the scope first: this leg only ever compares a license it believes covers the "
         "repository's code, so a finding here means either the record moved or the scope was "
         "read wrong."),
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
    findings, abstained = sweep(rows, products, scores, settled)

    if args.json:
        print(json.dumps([dataclasses.asdict(f) for f in findings], indent=2))
    else:
        for finding in findings:
            print(finding.line())
        print(f"\n{len(findings)} contradicted")
        if abstained:
            total = sum(abstained.values())
            print(f"\nlicense leg: {total} product(s) abstained on")
            for reason, count in abstained.most_common():
                print(f"  {count:4}  {reason}")
        gaps = representation_gaps(settled)
        if gaps:
            print(f"\n{len(gaps)} finding(s) suppressed because the schema cannot record the answer:")
            for entry in gaps:
                print(f"  ~ {entry.get('product_slug')} [{entry.get('leg')}]")
            print("  These are real and unresolved. Each is an argument for a schema change.")
    if args.queue:
        args.queue.write_text(queue_markdown(findings))
    return 1 if (args.strict and findings) else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
