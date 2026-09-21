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

Findings are self-clearing. Acting on one -- recording the `end_of_life`, correcting the license
-- removes it from the next run, so there is no acknowledgement ledger to keep in step with the
corpus, and no second place where a finding can be marked handled without being handled.

## Two legs

**Retirement.** `signal_github.artifact_state.is_archived` against the product's `end_of_life`.
A repository its owner marked read-only, under a product that records no end of life. This leg
has no abstention rules because it needs none: both sides are booleans about the same artifact.

**License.** The recorded openness license against `license_spdx_id` from the same table. This
leg abstains far more than it fires, and the abstentions are what make it worth reading:

  * **Product type.** A repository's SPDX id describes its CODE. For a `model` or a `dataset`
    the recorded openness license describes weights or data -- a different artifact, which may
    legitimately carry a different license, and comparing the two measures nothing. The corpus
    already draws this line: `normalize_license` strips `code `/`model ` scope prefixes because
    "the scope is which artifact the license covers". Only `software` products are compared.
  * **A compound recorded license.** More than one license part and there is no single thing for
    one SPDX id to disagree with. Abstains, exactly as `build.reverify._spdx_confirms` does.
  * **An SPDX id that declines to answer.** `NOASSERTION`, `other`, a blank, or the API's own
    no-license sentinel. GitHub saying "I could not classify this" is not GitHub disagreeing.

Both legs report the artifact and the column they read, so a finding can be checked against its
source without rerunning the sweep.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import re
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import yaml

from build.check_rubric import license_parts_of, normalize_license

ROOT = Path(__file__).resolve().parent.parent

RETIREMENT = "retirement"
LICENSE = "license"

#: SPDX ids that mean "not classified", not "classified as this". A license-detection API
#: reporting that it could not tell is not the API contradicting the record.
ABSTAIN_SPDX = frozenset({"", "noassertion", "other", "none", "null"})

#: The only product type whose repository license describes the product itself. See the module
#: docstring: for a model or a dataset the openness license covers a different artifact.
COMPARABLE_TYPE = "software"

STATE_QUERY = """
SELECT
  product_slug,
  repo,
  license_spdx_id,
  license_is_noassertion,
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


#: `GPLv3` and `GPL-3.0` are one license spelled two ways. Recognised here rather than in the
#: recorded-name alias table because `normalize_license` also feeds the rubric's tier matching,
#: and a name that resolves differently there resolves to a different tier -- a score change,
#: made by a read-only sweep, for the sake of a comparison. Putting it in the alias table is the
#: better durable fix and is a scoring decision, so it belongs to a person.
_VERSIONED_FAMILY = re.compile(r"^(a?gpl|lgpl)v(\d+)(?:\.(\d+))?$", re.IGNORECASE)


def _spelling(name: str) -> str:
    """One license name reduced to the spelling two records of it can be compared in.

    `normalize_license` first, for the recorded-name aliases, then case folding -- that function
    does NOT fold case, so it answers `'mit' != 'MIT'` and a lowercase record would never match
    an SPDX id. Then the `GPLv3`/`GPL-3.0` family, which no alias covers.
    """
    value = normalize_license(name).strip().casefold()
    match = _VERSIONED_FAMILY.match(value)
    if match:
        family, major, minor = match.group(1), match.group(2), match.group(3) or "0"
        return f"{family}-{major}.{minor}"
    return value


def same_license(recorded: str, spdx: str) -> bool:
    """Do these name the same license?

    A recorded name may offer alternatives -- `LGPL-3.0/GPL-3.0` is one declared name meaning
    either, because `license_segments` splits on `+` only and a compound the curator meant as one
    name deliberately stays one part. A repository reporting ONE of the alternatives agrees with
    such a record; it does not contradict it, and reading it as a contradiction would turn every
    dual-licensed product into a standing false finding.
    """
    target = _spelling(spdx)
    return any(_spelling(part) == target for part in recorded.split("/") if part.strip())


#: A `detail` that only says where the license sits on the openness scale, rather than qualifying
#: WHICH license the record means. Everything else -- a scope, a named license file, an appended
#: condition, a carve-out -- changes what the name is a claim about, and a repository-level
#: classifier cannot be compared against it.
_PLAIN_DETAIL = re.compile(r"^(osi\b.*|permissive.*|copyleft.*)?$", re.IGNORECASE)

#: A `detail` that binds the component to the repository's code. Such a component is comparable
#: whatever the product type, because it is a claim about the same artifact the SPDX id describes.
_CODE_SCOPED = re.compile(r"^(code|repository|repo)\b", re.IGNORECASE)

#: A `detail` naming the specific license file the record was read from. GitHub classifies ONE
#: repository-level file, so a record that deliberately points at a different one is not being
#: contradicted when the classifier reports the file it did read.
_NAMES_A_FILE = re.compile(r"\bvia\b|license-", re.IGNORECASE)


def comparable_license(score: Mapping, product_type: str) -> str | None:
    """The recorded license name a repository's SPDX id may be compared against, or `None`.

    `None` is an abstention, and this function is mostly abstentions on purpose. The corpus does
    not record a license as a bare name: `detail` carries the scope and the qualification, and
    discarding it is what makes an explained difference look like a contradiction. Two findings
    in the first run of this sweep were exactly that -- one product recording its code license
    from `LICENSE-CODE` while GitHub classified the documentation license at the repository root,
    another recording a bespoke license whose own detail says GitHub still reports the base
    license it was built from. Both records were right, both were already explained in the file,
    and both would have returned every week forever.

    So a part is comparable only when it says nothing that changes what its name claims:

      * exactly one part, since a single id cannot disagree with a compound;
      * a `detail` that grades the license (`OSI`, `permissive`, `copyleft`) or is empty, rather
        than one that scopes it (`core`, `API-only`, `SaaS`), names the file it came from, or
        describes a modification of a standard license;
      * a product whose repository licenses the product itself, which is `software` -- or any
        product whose part is explicitly bound to the code, since that part is a claim about the
        artifact the SPDX id describes however the product is classified.
    """
    components = (score.get("openness") or {}).get("components") or {}
    parts = license_parts_of(components.get("license"))
    if len(parts) != 1:
        return None
    name = (parts[0].get("name") or "").strip()
    if not name:
        return None
    detail = (parts[0].get("detail") or "").strip()
    if _NAMES_A_FILE.search(detail):
        return None
    code_scoped = bool(_CODE_SCOPED.match(detail))
    if not code_scoped and not _PLAIN_DETAIL.match(detail):
        return None
    if product_type != COMPARABLE_TYPE and not code_scoped:
        return None
    return name


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


def license_findings(
    rows: Iterable[Mapping], products: Mapping[str, Mapping], scores: Mapping[str, Mapping]
) -> list[Finding]:
    """Software products whose repository reports a license the record disagrees with."""
    out: list[Finding] = []
    for row in rows:
        slug = _text(row.get("product_slug"))
        product = products.get(slug)
        if product is None:
            continue
        spdx = _text(row.get("license_spdx_id"))
        if spdx.lower() in ABSTAIN_SPDX or _truthy(row.get("license_is_noassertion")):
            continue
        score = scores.get(slug)
        if score is None:
            continue
        recorded = comparable_license(score, _text(product.get("type")))
        if recorded is None or same_license(recorded, spdx):
            continue
        out.append(
            Finding(
                leg=LICENSE,
                product_slug=slug,
                recorded=recorded,
                observed=spdx,
                artifact=_text(row.get("repo")),
                source_column="license_spdx_id",
                as_of=_text(row.get("fetched_at"))[:10],
                settles=spdx,
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
    found = retirement_findings(rows, products) + license_findings(rows, products, scores)
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
            "No contradiction within this sweep's coverage: GitHub archival, and license ids for "
            "records that do not qualify what they name. Other collected signals -- Hub gating, "
            "weights availability, a disabled or vanished artifact -- are not examined here, so "
            "this is not a statement that every record was checked.\n"
        )
    lines = ["# Contradiction queue", ""]
    for leg, heading, action in (
        (RETIREMENT, "Archived repository, no recorded end of life",
         "Record `end_of_life` on the product, or settle it in `sources/contradictions_settled.yaml` "
         "with the reason the product outlived its repository."),
        (LICENSE, "Repository license disagrees with the record",
         "Correct the recorded license, or settle it in `sources/contradictions_settled.yaml` "
         "with the reason the repository's own SPDX id is not the product's license."),
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
        print(f"\n{len(findings)} contradicted: "
              f"{len([f for f in findings if f.leg == RETIREMENT])} retirement, "
              f"{len([f for f in findings if f.leg == LICENSE])} license")
    if args.queue:
        args.queue.write_text(queue_markdown(findings))
    return 1 if (args.strict and findings) else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
