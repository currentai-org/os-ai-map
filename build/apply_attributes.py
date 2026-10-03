"""Apply a curation ledger of identity attributes to the corpus: `country`, `languages`, `steward`.

The three attributes (docs/reference/identity.md) are researched in batches and recorded as
JSON Lines ledgers, one row per organization or product, each carrying the value, the page
that evidences it, and a confidence. A ledger is the record of what research found, including
the rows that found nothing, so it is kept as it was written and this module decides, row by
row, what may reach a file in `sources/`. The ledger format and the batch plan are in
`docs/sweeps/2026-09-30-identity-attributes/README.md`.

A row is applied only when it has a value, an `http(s)` evidence URL and a confidence of
`high` or `medium`. The value is then checked against the same vocabulary the gate uses
(`build/vocabulary.py` for country and language codes; the org files for a steward), so a row
this module writes cannot be one `build.validate` rejects. A `languages` list is sorted on the
way in. Two rows that disagree about one slug are both refused, because choosing between them
is a curation decision.

Every edit goes through `build/components.py` (`add_document_field`, `set_document_field`),
which re-parses the file and refuses to write unless only that one key moved. A corpus file is
never loaded and dumped. Where a field is inserted is fixed per kind, so the result does not
depend on the order ledgers are applied in:

  country    after `homepage`, else `aliases`, else `type`, else `display_name`  (organizations)
  steward    after `type`                                                           (products)
  languages  after `steward`, else `type`, as a wrapped `[a, b, ...]` list          (products)

A field that already holds the same value is left alone, which makes a second run a no-op. A
field that holds a different value is reported as a conflict and left alone unless
`--overwrite` is given.

Usage:
    uv run python -m build.apply_attributes --kind country --ledger PATH [--ledger PATH ...]
    uv run python -m build.apply_attributes --kind languages --ledger 'docs/sweeps/*/languages/*.jsonl'
    uv run python -m build.apply_attributes --kind steward --ledger PATH --write

Without `--write` nothing is changed and the summary says what would be. `--ledger` may repeat
and each value may be a glob. The exit status is 1 when a row was rejected or conflicts with
the corpus, 0 otherwise; a row skipped for low confidence or a missing value is expected and
does not fail the run.
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from build.components import add_document_field, set_document_field
from build.vocabulary import country_codes, language_codes

ROOT = Path(__file__).resolve().parents[1]

CONFIDENCE = ("high", "medium", "low")


@dataclass(frozen=True)
class Kind:
    """One attribute: which file family it lives in and where a new one is inserted."""

    field: str
    directory: str
    after: tuple[str, ...]
    flow: bool = False  # write a list as a wrapped `[a, b, ...]` rather than one item per line


KINDS: dict[str, Kind] = {
    "country": Kind("country", "organizations", ("homepage", "aliases", "type", "display_name")),
    "steward": Kind("steward", "products", ("type",)),
    # A flow sequence: a multilingual dataset can list well over a thousand codes.
    "languages": Kind("languages", "products", ("steward", "type"), flow=True),
}

# Outcomes. `set`, `changed` and `unchanged` describe a row that was valid; `skipped` is a row
# policy says is never applied; `rejected` and `conflict` are rows someone has to look at.
SET, CHANGED, UNCHANGED, SKIPPED, REJECTED, CONFLICT = (
    "set", "changed", "unchanged", "skipped", "rejected", "conflict",
)
FAILING = (REJECTED, CONFLICT)


@dataclass
class Row:
    slug: str
    value: object
    origin: str
    outcome: str = ""
    reason: str = ""


@dataclass
class Report:
    kind: str
    rows: list[Row] = field(default_factory=list)
    written: list[Path] = field(default_factory=list)

    def count(self, outcome: str) -> int:
        return sum(1 for row in self.rows if row.outcome == outcome)

    @property
    def failed(self) -> bool:
        return any(row.outcome in FAILING for row in self.rows)


def expand_ledgers(patterns: list[str]) -> list[Path]:
    """Each pattern is a path or a glob; the result is sorted and de-duplicated."""
    found: dict[Path, None] = {}
    for pattern in patterns:
        matches = sorted(glob.glob(pattern, recursive=True))
        if not matches:
            raise FileNotFoundError(f"no ledger matches {pattern!r}")
        for match in matches:
            found[Path(match)] = None
    return list(found)


def read_ledger(path: Path, key: str) -> list[tuple[str, dict | None, str]]:
    """(origin, row or None, problem) for each non-blank line. None means the line is unusable."""
    out: list[tuple[str, dict | None, str]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        origin = f"{path.name}:{number}"
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            out.append((origin, None, f"not valid JSON ({error.msg})"))
            continue
        if not isinstance(row, dict) or not isinstance(row.get("slug"), str) or not row["slug"]:
            out.append((origin, None, "row has no `slug`"))
        elif key not in row:
            out.append((origin, None, f"row has no `{key}` key (use null for unknown)"))
        else:
            out.append((origin, row, ""))
    return out


def _is_url(value: object) -> bool:
    return isinstance(value, str) and value.startswith(("http://", "https://")) and len(value) > 8


def _owning_org(root: Path, product: str) -> str | None:
    for path in sorted((root / "sources" / "organizations").glob("*.yaml")):
        roster = (yaml.safe_load(path.read_text()) or {}).get("products") or []
        if product in roster:
            return path.stem
    return None


def normalize(kind: str, value: object, slug: str, root: Path, doc: dict) -> tuple[object, str]:
    """(value to write, "") or (None, why it may not be written)."""
    if kind == "country":
        if doc.get("type") == "individual":
            return None, "an individual carries no country"
        if isinstance(value, str) and value in country_codes():
            return value, ""
        return None, (f"{value!r} is not an ISO 3166-1 alpha-2 code in the snapshot "
                      "(United Kingdom is GB)")
    if kind == "languages":
        if doc.get("type") != "dataset":
            return None, f"`languages` applies to datasets only (this is {doc.get('type')!r})"
        if not isinstance(value, list) or not value or not all(isinstance(c, str) for c in value):
            return None, "`languages` must be a non-empty list of codes"
        bad = sorted({c for c in value if c not in language_codes()})
        if bad:
            return None, f"not ISO 639-3 codes of scope I or M: {bad}"
        return sorted(set(value)), ""
    if not isinstance(value, str) or not (root / "sources" / "organizations" / f"{value}.yaml").exists():
        return None, f"steward {value!r} has no sources/organizations/{value}.yaml"
    if value == _owning_org(root, slug):
        return None, f"steward {value!r} is the owning organization"
    return value, ""


def plan(kind: str, ledgers: list[Path], root: Path = ROOT, overwrite: bool = False) -> tuple[Report, dict[Path, str]]:
    """Decide every row; return the report and the new text of each file that would change."""
    spec = KINDS[kind]
    report = Report(kind)
    candidates: list[Row] = []

    for ledger in ledgers:
        for origin, row, problem in read_ledger(ledger, spec.field):
            if row is None:
                report.rows.append(Row("", None, origin, REJECTED, problem))
                continue
            entry = Row(row["slug"], row[spec.field], origin)
            report.rows.append(entry)
            confidence = row.get("confidence")
            if confidence not in CONFIDENCE:
                entry.outcome, entry.reason = REJECTED, f"confidence {confidence!r} is not one of {list(CONFIDENCE)}"
            elif entry.value is None:
                entry.outcome, entry.reason = SKIPPED, "no value (recorded as unknown)"
            elif confidence == "low":
                entry.outcome, entry.reason = SKIPPED, "confidence is low"
            elif not _is_url(row.get("evidence")):
                entry.outcome, entry.reason = SKIPPED, "no http(s) evidence URL"
            else:
                path = root / "sources" / spec.directory / f"{entry.slug}.yaml"
                if not path.exists():
                    entry.outcome, entry.reason = REJECTED, f"no sources/{spec.directory}/{entry.slug}.yaml"
                    continue
                value, why = normalize(kind, entry.value, entry.slug, root, yaml.safe_load(path.read_text()) or {})
                if why:
                    entry.outcome, entry.reason = REJECTED, why
                else:
                    entry.value = value
                    candidates.append(entry)

    # Two usable rows that disagree about one slug: neither is applied.
    by_slug: dict[str, list[Row]] = {}
    for entry in candidates:
        by_slug.setdefault(entry.slug, []).append(entry)
    decided: list[Row] = []
    for slug, entries in by_slug.items():
        if len({json.dumps(e.value) for e in entries}) > 1:
            for entry in entries:
                others = ", ".join(f"{o.origin} says {o.value!r}" for o in entries if o is not entry)
                entry.outcome, entry.reason = REJECTED, f"ledger rows disagree ({others})"
        else:
            entries[0].outcome = "pending"
            for duplicate in entries[1:]:
                duplicate.outcome, duplicate.reason = UNCHANGED, f"same value as {entries[0].origin}"
            decided.append(entries[0])

    texts: dict[Path, str] = {}
    for entry in decided:
        path = root / "sources" / spec.directory / f"{entry.slug}.yaml"
        text = path.read_text()
        doc = yaml.safe_load(text) or {}
        current = doc.get(spec.field)
        if current == entry.value:
            entry.outcome = UNCHANGED
        elif current is None:
            # A key that is present but null is filled in place rather than added a second time.
            texts[path] = (
                set_document_field(text, spec.field, entry.value, flow=spec.flow)
                if spec.field in doc
                else add_document_field(text, spec.field, entry.value, after=spec.after, flow=spec.flow)
            )
            entry.outcome = SET
        elif overwrite:
            texts[path] = set_document_field(text, spec.field, entry.value, flow=spec.flow)
            entry.outcome, entry.reason = CHANGED, f"was {current!r}"
        else:
            entry.outcome, entry.reason = CONFLICT, f"file has {current!r}; pass --overwrite to replace it"
    return report, texts


def apply(kind: str, ledgers: list[Path], root: Path = ROOT, write: bool = False, overwrite: bool = False) -> Report:
    report, texts = plan(kind, ledgers, root=root, overwrite=overwrite)
    if write:
        for path, text in sorted(texts.items()):
            path.write_text(text)
            report.written.append(path)
    return report


def render(report: Report, write: bool) -> str:
    lines = []
    for row in report.rows:
        if row.outcome == UNCHANGED and not row.reason:
            continue
        who = row.slug or "(unreadable row)"
        detail = f" -> {row.value!r}" if row.outcome in (SET, CHANGED) else ""
        why = f"  [{row.reason}]" if row.reason else ""
        lines.append(f"  {row.outcome:<9} {who}{detail}{why}  ({row.origin})")
    counts = Counter(row.outcome for row in report.rows)
    summary = ", ".join(f"{counts.get(name, 0)} {name}" for name in (SET, CHANGED, UNCHANGED, SKIPPED, REJECTED, CONFLICT))
    verb = "wrote" if write else "dry run, would write"
    files = len(report.written) if write else report.count(SET) + report.count(CHANGED)
    lines.append(f"{report.kind}: {summary}; {verb} {files} file(s)")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--kind", required=True, choices=sorted(KINDS))
    parser.add_argument("--ledger", action="append", required=True, metavar="PATH",
                        help="a ledger file or glob; repeatable")
    parser.add_argument("--write", action="store_true", help="change files (default is a dry run)")
    parser.add_argument("--overwrite", action="store_true",
                        help="replace a field that already holds a different value")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        ledgers = expand_ledgers(args.ledger)
    except FileNotFoundError as error:
        parser.error(str(error))
    report = apply(args.kind, ledgers, root=args.root, write=args.write, overwrite=args.overwrite)
    print(render(report, args.write))
    return 1 if report.failed else 0


if __name__ == "__main__":
    sys.exit(main())
