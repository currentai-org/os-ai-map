"""Gate: a structured `components` mapping says exactly what the string said.

Phase 1a changes the SHAPE of the most load-bearing field in the corpus and promises it
moves no score. That promise is only as good as the migration, and a migration that mangled
one value would still parse, still validate, and still pass every existing gate — because
every existing gate reads the mapping and would simply believe it.

So each migrated record keeps its original string in `openness.raw`, and this gate asserts
the mapping and the string produce the same key -> clause dict, key for key, byte for byte.
It is the only check that compares the migration's output against its input.

It also asserts the two directions nobody would otherwise notice:

  * a migrated record MUST carry `raw`, or there is nothing to check it against;
  * an unmigrated record must NOT, or a stale `raw` will be silently believed by
    `components_string` and shipped to the payload.

The migration finished at 472 of 472 records, so a THIRD thing is now a failure rather than
a skip: `components` recorded as a string at all. Before this the string shape was simply
narrowed past, which meant a new or reverted string-shaped record passed every gate,
including this one, and silently returned the corpus to mixed shape. The mapping is now the
only shape this field may take.

Exit status is 1 on any failure, so CI can gate on it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

from build.check_rubric import FREE_TEXT, _clauses, recompose, split_components

ROOT = Path(__file__).resolve().parents[1]


def check(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    for path in sorted((root / "sources" / "scores").glob("*.yaml")):
        block = (yaml.safe_load(path.read_text()) or {}).get("openness") or {}
        components = block.get("components")
        raw = block.get("raw")
        slug = path.stem

        if isinstance(components, str):
            failures.append(
                f"{slug}: openness.components is still a string. The mapping is now the "
                f"only accepted shape for this field (phase 1a migrated all 472 records); "
                f"migrate it with build/components.py rather than hand-writing a string."
            )
            continue

        if not isinstance(components, dict):
            failures.append(f"{slug}: openness.components is missing or not a mapping")
            continue

        if not isinstance(raw, str) or not raw:
            failures.append(f"{slug}: components is a mapping with no openness.raw to check it against")
            continue

        expected = split_components(raw)
        actual = recompose(components)
        if actual != expected:
            for key in sorted(set(expected) | set(actual)):
                if expected.get(key) != actual.get(key):
                    failures.append(
                        f"{slug}.{key}: mapping recomposes to {actual.get(key)!r}, "
                        f"raw says {expected.get(key)!r}"
                    )

        keyless = [c.strip() for c in _clauses(raw) if ":" not in c.strip()]
        recorded = components.get(FREE_TEXT, [])
        if keyless != recorded:
            failures.append(f"{slug}: free_text is {recorded!r}, raw's keyless clauses are {keyless!r}")

    return failures


def main() -> int:
    failures = check()
    for line in failures:
        print(f"  x {line}")
    print(f"\ncomponents gate  a structured mapping that disagrees with its raw string  "
          f"{'[OK]' if not failures else f'{len(failures)} failure(s)'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
