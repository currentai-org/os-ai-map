"""Read and check the per-language classification the map consumes from Artio.

`currentai.language_representation.classification` is built and owned on the OSO platform
(R-2026-10-30-d, R-2026-11-10-l) and read here through its dependency contract in
`warehouse/dependencies.yaml`. Its rules live in `docs/reference/language-classification.md`;
nothing in this module computes a class. This module is the contract's reader: it fails when
the table breaks the contract the reference states, and it summarizes the codes the map's
products declare.

What it checks, row by row:

- every column of the contract is present, and no non-null column holds a NULL. Unknown is a
  value (`unknown`, `unresolved`, a full interval), never a NULL;
- every vocabulary column holds a value the reference allows;
- a resolved class or band has equal ends, and an `unresolved` one has different ends;
- the row's `method_version` has the major version this reader was written for.

And across the table:

- one row per code;
- every ISO 639-3 code declared in a product's `languages` has a row.

A failing check exits 1. The table never moves a product: membership and yardstick changes
are reviewed separately (R-2026-11-10-j, -k).

Usage:
    uv run python -m build.language_representation            # check, then summarize
    uv run python -m build.language_representation --check    # check only
"""

from __future__ import annotations

import argparse
import math
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

METHOD_MAJOR = 1

CLASSIFICATION_SQL = """
SELECT *
FROM currentai.language_representation.classification
"""

# The classification table's columns, in the reference's order, and whether each may be NULL.
COLUMNS: dict[str, bool] = {
    "iso639_3": False,
    "macrolanguage": True,
    "related_to": False,
    "flags": False,
    "written_best": False,
    "written_worst": False,
    "written_state": False,
    "representation_class": False,
    "representation_class_best": False,
    "representation_class_worst": False,
    "status_best": False,
    "status_worst": False,
    "status_state": False,
    "recognized": False,
    "speakers_low": True,
    "speakers_high": True,
    "speakers_state": False,
    "official": False,
    "many_speakers": False,
    "large_written_material": False,
    "scholarly_works": False,
    "endangerment": False,
    "descriptive_status": False,
    "provenance": False,
    "code_table_version": False,
    "method_version": False,
    "computed_at": False,
}

BANDS = ("A", "B", "C", "D")
CLASSES = ("high", "mid", "low", "very_low")
STATUSES = ("national", "subnational", "none")
VERDICTS = ("yes", "no", "unresolved")
FLAGS = {"historical", "constructed", "extinct", "macrolanguage"}
STATES = {
    "measured", "bounded", "observed_absent", "not_listed", "not_detected", "unmeasured",
    "excluded", "unknown", "bound_from_endangerment",
}

VOCABULARY: dict[str, tuple[str, ...]] = {
    "written_best": BANDS,
    "written_worst": BANDS,
    "representation_class": CLASSES + ("unresolved", "unknown"),
    "representation_class_best": CLASSES + ("unknown",),
    "representation_class_worst": CLASSES + ("unknown",),
    "status_best": STATUSES,
    "status_worst": STATUSES,
    "recognized": ("yes", "no", "unknown"),
    "official": VERDICTS,
    "many_speakers": VERDICTS,
    "large_written_material": VERDICTS,
}

STATE_COLUMNS = ("written_state", "status_state", "speakers_state")


def is_null(value: object) -> bool:
    """True for None and for the float NaN a pandas frame uses for a missing value."""
    if value is None:
        return True
    return isinstance(value, float) and math.isnan(value)


def as_list(value: object) -> list:
    """An array column as a list; the client returns arrays as lists or numpy arrays."""
    if is_null(value):
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    tolist = getattr(value, "tolist", None)
    return list(tolist()) if callable(tolist) else [value]


def major(version: object) -> int | None:
    try:
        return int(str(version).split(".")[0])
    except (TypeError, ValueError):
        return None


def row_errors(row: dict) -> list[str]:
    """Every way one classification row breaks the contract."""
    code = row.get("iso639_3")
    where = f"{code}" if not is_null(code) else "<row without iso639_3>"
    errors: list[str] = []

    missing = [c for c in COLUMNS if c not in row]
    if missing:
        return [f"{where}: missing columns {', '.join(missing)}"]

    for column, nullable in COLUMNS.items():
        if not nullable and is_null(row[column]):
            errors.append(f"{where}: NULL in non-null column {column}")
    if errors:
        return errors

    for column, allowed in VOCABULARY.items():
        if row[column] not in allowed:
            errors.append(f"{where}: {column} = {row[column]!r}, not one of {', '.join(allowed)}")
    for column in STATE_COLUMNS:
        if row[column] not in STATES:
            errors.append(f"{where}: {column} = {row[column]!r} is not a value state")
    for flag in as_list(row["flags"]):
        if flag not in FLAGS:
            errors.append(f"{where}: unknown flag {flag!r}")

    if row["written_best"] in BANDS and row["written_worst"] in BANDS:
        if BANDS.index(row["written_best"]) > BANDS.index(row["written_worst"]):
            errors.append(f"{where}: written interval runs backwards")

    cls = row["representation_class"]
    best, worst = row["representation_class_best"], row["representation_class_worst"]
    if cls in CLASSES and not (best == worst == cls):
        errors.append(f"{where}: resolved class {cls} has ends {best}..{worst}")
    if cls == "unresolved" and best == worst:
        errors.append(f"{where}: unresolved class has equal ends {best}")
    if cls == "unknown" and not (best == worst == "unknown"):
        errors.append(f"{where}: unknown class has ends {best}..{worst}")

    # `no` needs both routes to fail; the web-text route fails only when the written interval's best
    # end is below B (docs/reference/language-classification.md, "Resource profile").
    if row["large_written_material"] == "no" and row["written_best"] in ("A", "B"):
        errors.append(
            f"{where}: large_written_material is no but written material reaches {row['written_best']}"
        )

    low, high = row["speakers_low"], row["speakers_high"]
    if not is_null(low) and not is_null(high) and low > high:
        errors.append(f"{where}: speaker interval runs backwards")

    if major(row["method_version"]) != METHOD_MAJOR:
        errors.append(
            f"{where}: method_version {row['method_version']} is not major {METHOD_MAJOR}"
        )
    return errors


def declared_codes(products_dir: Path = ROOT / "sources" / "products") -> dict[str, list[str]]:
    """Every ISO 639-3 code a product declares in `languages`, with the products declaring it."""
    declared: dict[str, list[str]] = {}
    for path in sorted(products_dir.glob("*.yaml")):
        record = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for code in record.get("languages") or []:
            declared.setdefault(code, []).append(path.stem)
    return declared


def check(rows: list[dict], declared: dict[str, list[str]]) -> list[str]:
    """Every contract failure in the table, given the codes the map declares."""
    errors: list[str] = []
    seen: Counter = Counter()
    for row in rows:
        errors.extend(row_errors(row))
        if not is_null(row.get("iso639_3")):
            seen[row["iso639_3"]] += 1
    for code, count in sorted(seen.items()):
        if count > 1:
            errors.append(f"{code}: {count} rows; the table holds one row per code")
    for code in sorted(set(declared) - set(seen)):
        products = ", ".join(declared[code][:3])
        more = len(declared[code]) - 3
        errors.append(
            f"{code}: declared by {products}{f' and {more} more' if more > 0 else ''}"
            " but has no classification row"
        )
    return errors


def summary(rows: list[dict], declared: dict[str, list[str]]) -> str:
    """The class and profile distributions, over every row and over the declared codes."""
    lines = [f"{len(rows)} rows; {len(declared)} codes declared by the map's products", ""]
    declared_rows = [r for r in rows if r.get("iso639_3") in declared]
    for label, subset in (("all rows", rows), ("declared codes", declared_rows)):
        classes = Counter(r["representation_class"] for r in subset)
        lines.append(f"Representation class, {label}:")
        for cls in CLASSES + ("unresolved", "unknown"):
            lines.append(f"  {cls:<11} {classes.get(cls, 0)}")
        profiles = Counter(
            "/".join(
                {"yes": "Y", "no": "N"}.get(r[a], "U")
                for a in ("official", "many_speakers", "large_written_material")
            )
            for r in subset
        )
        resolved = {p: n for p, n in profiles.items() if "U" not in p}
        lines.append(f"Resource profile (official/many/large), {label}:")
        for profile, count in sorted(resolved.items(), key=lambda kv: (-kv[1], kv[0])):
            lines.append(f"  {profile}  {count}")
        lines.append(f"  at least one axis unresolved  {sum(profiles.values()) - sum(resolved.values())}")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--check", action="store_true", help="check the contract only")
    args = parser.parse_args(argv)

    from build.warehouse import query

    rows = query(CLASSIFICATION_SQL)
    declared = declared_codes()
    errors = check(rows, declared)
    for error in errors:
        print(f"ERROR {error}", file=sys.stderr)
    if errors:
        print(f"{len(errors)} contract failure(s)", file=sys.stderr)
        return 1
    if not args.check:
        print(summary(rows, declared))
    print(f"language_representation.classification: {len(rows)} rows, contract holds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
