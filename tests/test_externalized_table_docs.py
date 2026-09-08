"""An externalized table must not be described anywhere as if it were still current.

ADR-003 moved 28 tables out of this repository's scope. They were left live on the OSO
platform and frozen at their last publish: they still answer a query, they just stop
advancing. That is the dangerous shape. A deleted table announces itself; a frozen one
returns rows and looks fine, and the reader only finds out that the numbers stopped moving
if the docs say so.

So every mention of a still-externalized table in the hand-maintained docs has to carry a
word that marks it as historical. The list of tables is read from
`warehouse/audits/externalization.json` through `build.assets.still_externalized()`, not
kept here: adding a table to the receipt puts it under this rule immediately, with no test
edit, and reclaiming one (`reclaims`, disposition `reclaimed-as-dependency`) takes it back
out, because a reclaimed table is live in the governed graph again and describing it as
current is correct.

Granularity: **the unit of the rule is the unit of copying.**

A mention inside a fenced code block is satisfied by a marker anywhere in that fence at or
above the mention's own line. A fence is what a reader selects and pastes, so a comment in
the fence travels with the query into their SQL client, which is where the warning has to
arrive. Requiring the marker on the mention's own physical line -- the rule the first draft
of this test used -- cannot be satisfied inside SQL without wedging a comment between
`FROM` and the table name, and a warning that mangles the query gets deleted.

A mention in prose is satisfied only by a marker on the same line. Prose is read, not
copied, and the eye lands on the line, so the line is the unit. Deliberately NOT a
nearest-heading or n-lines-of-context rule: a preamble fifteen lines up is invisible to
someone who arrived at the section from the table of contents, and a rule that a distant
paragraph can satisfy is a rule any distant paragraph can fool.

A marker below the mention inside its fence does not count. A warning printed after the
thing it warns about is not a warning.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from build.assets import still_externalized

ROOT = Path(__file__).resolve().parent.parent

# Words that mark a mention as historical rather than a recommendation. The last three are
# the receipt's own vocabulary for what ADR-003 did.
MARKERS = (
    "archived",
    "superseded",
    "frozen",
    "deprecated",
    "retired",
    "do not",
    "externaliz",
    "no producer",
    "out of scope",
)

# The hand-maintained documentation surface, matching tests/test_docs_integrity.py plus the
# warehouse's own prose. Generated files and the gitignored session workspace are excluded.
DOC_GLOBS = ("docs/**/*.md", "warehouse/**/*.md", "skills/**/SKILL.md")
DOC_FILES = ("README.md", "CONTRIBUTING.md", "AGENTS.md", "CLAUDE.md")


def doc_files() -> list[Path]:
    found = {p for pattern in DOC_GLOBS for p in ROOT.glob(pattern) if p.is_file()}
    found |= {ROOT / name for name in DOC_FILES if (ROOT / name).exists()}
    return sorted(found)


def externalized_tables() -> list[str]:
    """Fully-qualified tables currently outside the repo's graph, from the receipt."""
    return sorted({e["table"] for e in still_externalized() if e.get("table")})


def has_marker(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in MARKERS)


def unmarked_mentions(text: str, table: str) -> list[tuple[int, str]]:
    """Lines mentioning `table` with no marker in their copy unit.

    Inside a fenced block the unit is the fence, from its opening line down to the mention.
    Outside one it is the single line.
    """
    offenders: list[tuple[int, str]] = []
    in_fence = False
    fence_marked = False
    for number, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            fence_marked = has_marker(line) if in_fence else False
            continue
        marked = has_marker(line)
        if in_fence:
            fence_marked = fence_marked or marked
        if table in line and not (fence_marked if in_fence else marked):
            offenders.append((number, line.strip()))
    return offenders


@pytest.mark.parametrize("table", externalized_tables())
def test_no_doc_presents_an_externalized_table_as_current(table: str) -> None:
    offenders: list[str] = []
    for path in doc_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        if table not in text:
            continue
        for number, line in unmarked_mentions(text, table):
            offenders.append(f"{path.relative_to(ROOT)}:{number}: {line[:120]}")
    assert not offenders, (
        f"{table} was externalized under ADR-003 and is frozen at its last publish, but these "
        f"lines present it as current. A reader would copy them and get data that stopped "
        f"advancing.\nMark the mention with one of {list(MARKERS)} -- on the same line in prose, "
        f"or anywhere at or above it inside the code fence:\n  " + "\n  ".join(offenders)
    )


def test_the_table_list_comes_from_the_receipt_and_tracks_reclaims() -> None:
    """Guard on the guard: an empty or hand-copied list would make the check vacuous."""
    tables = externalized_tables()
    assert tables, "the externalization receipt lists no un-reclaimed tables; delete this test"
    receipt_ids = {e["id"] for e in still_externalized()}
    assert {t.split(".", 1)[1] for t in tables} == receipt_ids
    # A reclaimed table is live again and is deliberately out of scope for the rule.
    from build.assets import externalized, reclaimed_tables

    for reclaimed in reclaimed_tables():
        assert reclaimed not in tables, f"{reclaimed} was reclaimed; the rule should not cover it"
    assert len(tables) == len(externalized()) - len(reclaimed_tables())


def test_the_check_rejects_an_unmarked_mention_and_accepts_a_marked_one() -> None:
    """Prove the marker logic can fail, in both copy units."""
    table = externalized_tables()[0]
    prose = f"Query `{table}` for the current roster.\n"
    assert unmarked_mentions(prose, table), "an unmarked prose mention must be caught"
    assert not unmarked_mentions(f"`{table}` is frozen; do not read it as current.\n", table)

    fenced = f"```sql\n-- FROZEN: stopped advancing at externalization.\nSELECT * FROM {table}\n```\n"
    assert not unmarked_mentions(fenced, table), "a marker in the fence must satisfy the rule"
    assert unmarked_mentions(f"```sql\nSELECT * FROM {table}\n```\n", table)
    # A marker after the mention does not warn anyone.
    trailing = f"```sql\nSELECT * FROM {table}\n-- that table is frozen\n```\n"
    assert unmarked_mentions(trailing, table), "a marker below the mention must not count"
