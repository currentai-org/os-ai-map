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

A FOURTH thing is a failure since the license was structured into parts: a license key
recorded as a `{value, detail}` mapping rather than a list of `{name, detail?, raw?}`.
`license_tier` resolves the parts a curator recorded and never splits a value itself, so a
license left in the dimension shape is a compound nobody decomposed — which is the failure
this repo has now had twice, once per reader.

A FIFTH thing is a failure since #188 gave a keyed clause somewhere to go when no ladder reads
it: the split between the top level and the reserved `context` mapping must match the product's
resolved ladder, in both directions.

  * A key at the top level that the ladder neither declares nor `reads` is dropped from the score
    without a word. `serialize_rubric` used to warn about it, 394 times across 266 records, and a
    warning that fires 394 times is read by nobody.
  * A key under `context` that the ladder DOES read is the opposite claim — "deliberately not
    scored" on evidence the formula consumes. That is what a ladder gaining a `reads` entry would
    leave behind, so the gate names it rather than letting the record contradict itself.

`build/route_context.py --write` repairs both, through `build/components.py`.

Exit status is 1 on any failure, so CI can gate on it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

from build.check_rubric import (
    CONTEXT,
    FREE_TEXT,
    RESERVED,
    _clauses,
    entries,
    is_license_key,
    recompose,
    split_components,
    unread_keys,
)
from build.rubrics import load_product_recipes

ROOT = Path(__file__).resolve().parents[1]


def check(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    recipes = load_product_recipes(root)
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

        malformed = malformed_entries(slug, components)
        if malformed:
            # Rendering one of these raises, and a traceback here would abort the gate for
            # every other record too.
            failures += malformed
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

        for key, entry in entries(components).items():
            if not is_license_key(key):
                continue
            if not isinstance(entry, list):
                failures.append(
                    f"{slug}.{key}: a license is recorded as a LIST of "
                    f"{{name, detail?, raw?}} parts, one per license the product makes you "
                    f"accept, not as {type(entry).__name__}. `license_tier` resolves the "
                    f"parts as recorded and never splits a value itself; a mapping here "
                    f"would abstain or resolve on the wrong half. Structure it with "
                    f"build.check_rubric.license_entry and write it through "
                    f"build/components.py."
                )

        keyless = [c.strip() for c in _clauses(raw) if ":" not in c.strip()]
        recorded = components.get(FREE_TEXT, [])
        if keyless != recorded:
            failures.append(f"{slug}: free_text is {recorded!r}, raw's keyless clauses are {keyless!r}")

        failures += context_failures(slug, components, recipes.get(slug))

    return failures


def malformed_entries(slug: str, components: dict) -> list[str]:
    """Entries neither `{value, ...}` nor a list of `{name, ...}` parts, top level or context.

    The schema rejects these, but this gate may run without it, and `render_entry` crashes on
    them rather than reporting.
    """
    context = components.get(CONTEXT)
    placed = [(key, entry) for key, entry in components.items() if key not in RESERVED]
    if isinstance(context, dict):
        placed += [(f"{CONTEXT}.{key}", entry) for key, entry in context.items()]
    failures = []
    for where, entry in placed:
        if isinstance(entry, dict):
            ok = isinstance(entry.get("value"), str)
        elif isinstance(entry, list):
            ok = bool(entry) and all(
                isinstance(part, dict) and isinstance(part.get("name"), str) for part in entry
            )
        else:
            ok = False
        if not ok:
            failures.append(
                f"{slug}.{where}: {entry!r} is neither a {{value, detail?, raw?}} mapping nor a "
                f"non-empty list of {{name, detail?, raw?}} license parts"
            )
    return failures


def context_failures(slug: str, components: dict, recipe: dict | None) -> list[str]:
    """Whether `context` holds exactly the keys this product's ladder does not read."""
    if CONTEXT not in components:
        context = {}
    elif not isinstance(context := components[CONTEXT], dict) or not context:
        return [f"{slug}: {CONTEXT} must be a non-empty mapping of key -> entry, or absent"]

    failures = [
        f"{slug}.{CONTEXT}.{key}: `{key}` is reserved and cannot be recorded as context"
        for key in context
        if key in RESERVED
    ]
    failures += [
        f"{slug}.{key}: recorded both at the top level and under {CONTEXT}"
        for key in context
        if key in components
    ]
    if recipe is None:
        # No ladder governs it, so "unread" is undefined. validate and check_recipe report the
        # missing ladder; this gate has nothing to compare against.
        return failures

    unread = unread_keys(components, recipe)
    fix = "Run `uv run python -m build.route_context --write`."
    failures += [
        f"{slug}.{key}: the product's ladder neither declares nor reads `{key}`, so at the top "
        f"level it is dropped from the score silently. It belongs under {CONTEXT}. {fix}"
        for key in components
        if key in unread
    ]
    failures += [
        f"{slug}.{CONTEXT}.{key}: the product's ladder reads `{key}`, so recording it as "
        f"context contradicts the formula that consumes it. Move it to the top level. {fix}"
        for key in context
        if key not in unread and key not in RESERVED
    ]
    return failures


def main() -> int:
    failures = check()
    for line in failures:
        print(f"  x {line}")
    print(f"\ncomponents gate  a mapping that disagrees with its raw string or its ladder  "
          f"{'[OK]' if not failures else f'{len(failures)} failure(s)'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
