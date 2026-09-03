"""Weekly digest of low-confidence identity items -- Carl's Monday review queue.

`currentai.identity.digest` (see `udms/identity_digest.sql`) ranks every reviewable
membership, equivalence, and org edge the identity graph proposed this week and caps the
active review queue at 25 rows. This module renders that table into the markdown body of
one GitHub issue, so the review happens where Carl already works instead of in a warehouse
client.

## Section order and the cap

`render()` groups items into four sections -- equivalence, membership, org, artifact
identity, in that fixed order (equivalence first, per the design's digest contract) -- and
within a section orders by `blast_radius` descending, `tiebreak` descending, `confidence`
descending. Only `state in (active, resurfaced)` rows render as reviewable items; the SQL
already caps those at 25 rows per sweep, but `render()` re-applies the same cap defensively
(so a fixture or a future SQL revision cannot silently blow the queue past what a person can
review in a sitting) and says how many were cut if more than 25 arrive.

`parked` rows never render as items -- they are weak (name-match-only) evidence recently
seen, held back per the design's resurfacing rule -- and appear only as a count per section.
`pool` rows are eligible items that ranked below this week's cap; they appear only as one
total count in the footer, not per section, since they are overflow rather than a review
decision.

## The pre-filled block, per relation

Each item carries a pre-filled block Carl can paste straight into the file that actually
records its kind of ruling -- never a placeholder in the wrong file, which would suppress a
question the item never asked:

- `membership` -> a `resolution_ledger.yaml` entry, `verdict: member_of` (the confirm
  direction; edit to `not_member_of` to reject), `relation: product_membership`.
- `equivalence` -> a `resolution_ledger.yaml` entry, `verdict: existing_product`,
  `relation: product_equivalence`.
- `org` -> an `org_handles.yaml` entry (`org`, `platform`, `handle`, `note`) -- an org edge is
  never a ledger question (it does not say "is this a new product", it says "who owns this
  account"), so a `product_equivalence` placeholder here would be worse than nothing: it
  would durably suppress a real equivalence question about the same artifact the next time
  one comes up. See `docs/schemas/org_handles.schema.json` (landing in a parallel PR; see
  `_ORG_HANDLES_STUB_SCHEMA` below for the shape this validates against until then).
- `artifact_identity` -> no block at all, just a one-line instruction. Nothing in this repo
  records that ruling yet, and this relation never actually appears in
  `currentai.identity.digest` today (`udms/identity_digest.sql` unions membership,
  equivalence and org only) -- the section stays in the fixed order and says so, rather than
  disappearing or rendering dead furniture.

Every YAML block validates against its schema (see `tests/test_identity_digest.py`). A row
whose `relation` is none of the four above raises in `render()`, before the cap is even
applied -- an unrecognized relation must never silently rank, consume a cap slot, and vanish.

## The three scorecard numbers

- **Unresolved pool size**: every row in the digest table, since none of them carry
  `state = resolved` (that only happens once a ruling lands and the *next* sweep drops the
  row) -- this is the standing backlog size, not just this week's active queue.
- **New vs resolved this week**: new = rows whose `first_seen` falls inside the sweep week
  (`week`'s Monday through Sunday); resolved cannot be read off the digest table at all --
  it is counted from `sources/resolution_ledger.yaml` entries whose `decided_on` falls in
  the same window, via `build.resolution.load()`.
- **Oldest unresolved age**: `week`'s Monday minus the earliest `first_seen` across every
  row, in whole weeks. Catches an item starved behind the top-25 ranking indefinitely.

CLI:
    uv run python -m build.identity_digest --week 2026-36 --out /tmp/digest.md
    uv run python -m build.identity_digest --week 2026-36 --rows fixture.json --out /tmp/digest.md
    uv run python -m build.identity_digest --week 2026-36 --out /tmp/digest.md --allow-unprovisioned
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlsplit

import yaml

from build import resolution
from build.identity_eval import _TABLE_NOT_FOUND_MARKERS
from build.vocabulary import parse_date, parse_timestamp

ROOT = Path(__file__).resolve().parents[1]
TABLE = "currentai.identity.digest"

#: Section order -- equivalence first, per the design's digest contract, then the rest in
#: the order the brief names them.
RELATION_ORDER = ("equivalence", "membership", "org", "artifact_identity")
RELATION_LABELS = {
    "equivalence": "Equivalence",
    "membership": "Membership",
    "org": "Org",
    "artifact_identity": "Artifact identity",
}
#: Rows beyond this rank, among `active`/`resurfaced`-eligible rows, are cut from the
#: rendered item list -- matching the cap `udms/identity_digest.sql` already enforces.
CAP = 25
ACTIVE_STATES = ("active", "resurfaced")


def _pair(value) -> tuple[str, str]:
    """`(kind, id)` from a `left`/`right` cell -- a dict, a mapping, or a 2-tuple/list.

    The warehouse emits `ROW(kind VARCHAR, id VARCHAR)`; a JSON fixture emits a `{"kind":
    ..., "id": ...}` object or a two-element array. Every shape lands here.
    """
    if isinstance(value, dict):
        return (str(value.get("kind")), str(value.get("id")))
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return (str(value[0]), str(value[1]))
    raise TypeError(f"cannot read a (kind, id) pair from {value!r}")


def _as_list(value) -> list[str]:
    """`method`/`evidence`/`penalties`/`options` normalized to a list of strings.

    Every deployed model emits these as `ARRAY(VARCHAR)`; a fixture may still hand this a
    bare string or `None`, both accepted for convenience.
    """
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    try:
        return [str(v) for v in value]
    except TypeError:
        return [str(value)]


def _row_date(value):
    """The calendar date `value` names, whichever of `first_seen`/`decided_on`'s shapes it
    arrives in -- `digest.sql` casts `first_seen` to `TIMESTAMP(6)`, a fixture may carry a
    bare date string, and `build.vocabulary` already owns both parsers (`parse_date`,
    `parse_timestamp`) so this delegates rather than adding a third.
    """
    ts = parse_timestamp(value)
    if ts is not None:
        return ts.date()
    return parse_date(value)


def _week_bounds(week: str) -> tuple[date, date]:
    """(Monday, Sunday) of an ISO week given as `"YYYY-WW"`."""
    year_s, week_s = week.split("-")
    monday = date.fromisocalendar(int(year_s), int(week_s), 1)
    return monday, monday + timedelta(days=6)


def _rank_key(row: dict) -> tuple:
    """Section order, then `blast_radius` desc, `tiebreak` desc, `confidence` desc."""
    relation = row.get("relation")
    section_rank = RELATION_ORDER.index(relation) if relation in RELATION_ORDER else len(RELATION_ORDER)
    blast_radius = int(row.get("blast_radius") or 0)
    tiebreak = int(row.get("tiebreak") or 0)
    confidence = float(row.get("confidence") or 0.0)
    return (section_rank, -blast_radius, -tiebreak, -confidence)


def _ledger_entry(row: dict, decided_on: date) -> dict:
    """A `resolution_ledger.yaml` entry pre-filled from a `membership` or `equivalence` row,
    in the confirm direction of its `proposed_action`. Always validates against
    `resolution_ledger.schema.json`; Carl edits the verdict (e.g. `member_of` ->
    `not_member_of`) once he has actually decided. Never called for `org` or
    `artifact_identity` -- see `_org_handle_entry` and `_render_item`.
    """
    relation = row.get("relation")
    left_kind, left_id = _pair(row.get("left"))
    _, right_id = _pair(row.get("right"))
    decided_on_s = decided_on.isoformat()

    if relation == "membership":
        return {
            "artifact": {"kind": left_kind, "id": left_id},
            "verdict": "member_of",
            "relation": "product_membership",
            "resolves_to": right_id,
            "decided_in": "#<issue>",
            "decided_on": decided_on_s,
            "note": (
                f"digest review: confirm {left_kind}:{left_id} is a member of "
                f"{right_id}'s adoption measurement."
            ),
        }
    if relation == "equivalence":
        return {
            "artifact": {"kind": left_kind, "id": left_id},
            "verdict": "existing_product",
            "relation": "product_equivalence",
            "resolves_to": right_id,
            "decided_in": "#<issue>",
            "decided_on": decided_on_s,
            "note": (
                f"digest review: confirm {left_kind}:{left_id} resolves to the existing "
                f"product {right_id}, not a new one."
            ),
        }
    raise ValueError(f"_ledger_entry() takes 'membership' or 'equivalence', got {relation!r}")


#: `left.kind` -> the `org_handles.yaml` `platform` it maps to, for the three platforms that
#: kind actually carries an account or domain on. `pypi`/`npm`/`crates`/`arxiv` artifacts have
#: no such handle in this vocabulary (a package publisher name is weaker, unhandled evidence
#: per the design's org section) -- `_org_handle` falls those back to `homepage_domain` with
#: the raw id and flags it in the note for a human to correct.
_ORG_HANDLE_PLATFORM = {
    "github": "github",
    "huggingface_model": "huggingface",
    "huggingface_dataset": "huggingface",
    "homepage": "homepage_domain",
}


def _org_handle(left_kind: str, left_id: str) -> tuple[str, str]:
    """`(platform, handle)` for an `org_handles.yaml` entry, derived from the artifact side of
    an `org` item. `github`/`huggingface_*` carry the account as the owner segment of
    `owner/repo`; `homepage` carries it as the URL's host.
    """
    platform = _ORG_HANDLE_PLATFORM.get(left_kind)
    if platform == "homepage_domain":
        return platform, (urlsplit(left_id).netloc or left_id)
    if platform is not None:
        return platform, (left_id.split("/", 1)[0] if "/" in left_id else left_id)
    return "homepage_domain", left_id


def _org_handle_entry(row: dict) -> dict:
    """An `org_handles.yaml` entry pre-filled from an `org` row -- never a
    `resolution_ledger.yaml` placeholder, since an org edge answers "who owns this account",
    not "is this a new product"; see this module's docstring.
    """
    left_kind, left_id = _pair(row.get("left"))
    _, org_slug = _pair(row.get("right"))
    platform, handle = _org_handle(left_kind, left_id)
    note = f"digest review: confirm {left_kind}:{left_id} is owned by org {org_slug} on {platform} ({handle})."
    if left_kind not in _ORG_HANDLE_PLATFORM:
        note += (
            f" {left_kind} carries no direct platform account in this vocabulary -- platform "
            f"defaulted to homepage_domain; verify and correct by hand before merging."
        )
    return {"org": org_slug, "platform": platform, "handle": handle, "note": note}


def _render_item(row: dict, decided_on: date) -> list[str]:
    left_kind, left_id = _pair(row.get("left"))
    right_kind, right_id = _pair(row.get("right"))
    methods = _as_list(row.get("method"))
    evidence = _as_list(row.get("evidence"))
    penalties = _as_list(row.get("penalties"))
    options = _as_list(row.get("options"))
    relation = row.get("relation")

    lines = [
        f"#### `{row.get('item_id')}`",
        "",
        f"- Left: `({left_kind}, {left_id})`",
        f"- Right: `({right_kind}, {right_id})`",
        f"- Confidence: {row.get('confidence')}",
        f"- Method: {', '.join(methods) if methods else 'none'}",
        f"- Evidence: {', '.join(evidence) if evidence else 'none'}",
        f"- Penalties: {', '.join(penalties) if penalties else 'none'}",
        f"- Proposed action: {row.get('proposed_action')}",
        f"- Options: {', '.join(options) if options else 'none'}",
    ]
    if row.get("state") == "resurfaced" and row.get("resurfaced_reason"):
        lines.append(f"- Resurfaced reason: {row['resurfaced_reason']}")
    lines.append("")

    if relation == "artifact_identity":
        lines.append(
            "_No automated block for this relation -- review the pair by hand; nothing in "
            "this repo records an artifact-identity ruling yet._"
        )
        lines.append("")
        return lines

    entry = _org_handle_entry(row) if relation == "org" else _ledger_entry(row, decided_on)
    lines.append("```yaml")
    lines.append(yaml.safe_dump([entry], sort_keys=False, default_flow_style=False).rstrip())
    lines.append("```")
    lines.append("")
    return lines


def _resolved_this_week(monday: date, sunday: date) -> int:
    """Ledger entries whose `decided_on` falls in `[monday, sunday]` AND whose relation is
    one the digest actually proposes -- the only way to learn "resolved this week", since a
    ruling never comes back through the digest table itself (a resolved row simply stops
    appearing next sweep, it is not marked `resolved`).

    The relation filter is `resolution.RELATIONS` (`product_equivalence`,
    `product_membership`) -- today every ledger entry's relation is already one of those two
    (`resolution.relation_of` defaults an absent `relation` key to `product_equivalence`, and
    the schema names no third), so this is a no-op against the corpus as it exists. It is kept
    anyway: a bulk backfill unrelated to this digest still counts today (see the review this
    fixed), and this is the seam a future, more specific relation would need.
    """
    count = 0
    # `resolution.LEDGER` looked up at call time (not `load`'s bound default) so a test can
    # monkeypatch `build.resolution.LEDGER` to a fixture ledger and get a deterministic count.
    for entry in resolution.load(resolution.LEDGER).values():
        if resolution.relation_of(entry) not in resolution.RELATIONS:
            continue
        decided_on = entry.get("decided_on")
        if not decided_on:
            continue
        d = parse_date(decided_on)
        if d is None:
            continue
        if monday <= d <= sunday:
            count += 1
    return count


def _oldest_age_weeks(rows: list[dict], monday: date) -> int:
    dates = [_row_date(r["first_seen"]) for r in rows if r.get("first_seen") is not None]
    dates = [d for d in dates if d is not None]
    if not dates:
        return 0
    return max(0, (monday - min(dates)).days // 7)


def render(rows: list[dict], week: str, resolved_count: int | None = None) -> str:
    """The digest issue body for `week` (`"YYYY-WW"`), rendered from `rows`.

    Pure over its arguments when `resolved_count` is supplied (the CLI's `main()` always
    supplies it, computed once via `_resolved_this_week`). Left `None`, it falls back to a
    read of `sources/resolution_ledger.yaml` for convenience -- callers that don't care where
    "resolved this week" comes from, and this module's own tests.

    Raises `ValueError` if any row names a relation outside `RELATION_ORDER`, before the cap
    is applied -- an unrecognized relation must never rank, silently consume a cap slot, and
    then vanish because the section loop only iterates known relations.
    """
    monday, sunday = _week_bounds(week)

    unknown = sorted({r.get("relation") for r in rows} - set(RELATION_ORDER))
    if unknown:
        raise ValueError(f"unknown digest relation(s) {unknown!r}; expected one of {RELATION_ORDER}")

    if resolved_count is None:
        resolved_count = _resolved_this_week(monday, sunday)

    eligible = [r for r in rows if r.get("state") in ACTIVE_STATES]
    eligible.sort(key=_rank_key)
    cut = max(0, len(eligible) - CAP)
    capped = eligible[:CAP]

    parked_by_relation: dict[str, int] = {}
    pool_total = 0
    for row in rows:
        state = row.get("state")
        if state == "parked":
            relation = row.get("relation")
            parked_by_relation[relation] = parked_by_relation.get(relation, 0) + 1
        elif state == "pool":
            pool_total += 1

    lines = [f"# identity digest: {week}", ""]
    for relation in RELATION_ORDER:
        items = [r for r in capped if r.get("relation") == relation]
        label = RELATION_LABELS[relation]
        lines.append(f"### {label} ({len(items)} item{'s' if len(items) != 1 else ''})")
        lines.append("")
        if not items:
            if relation == "artifact_identity":
                lines.append(
                    "_No active items this week -- udms/identity_digest.sql does not yet "
                    "union artifact_identity edges into this table, so this section is "
                    "always empty until it does._"
                )
            else:
                lines.append("_No active items this week._")
            lines.append("")
        for row in items:
            lines.extend(_render_item(row, monday))
        parked_n = parked_by_relation.get(relation, 0)
        lines.append(f"Parked (weak evidence only, held back): {parked_n}")
        lines.append("")

    if cut:
        lines.append(
            f"_{cut} additional item(s) ranked below the weekly cap of {CAP} are not shown "
            f"this week._"
        )
        lines.append("")

    new_count = sum(
        1 for r in rows
        if r.get("first_seen") is not None
        and (_d := _row_date(r["first_seen"])) is not None and monday <= _d <= sunday
    )
    oldest_weeks = _oldest_age_weeks(rows, monday)

    lines.append("### Scorecard")
    lines.append("")
    lines.append(f"- Unresolved pool size: {len(rows)}")
    lines.append(f"- New vs resolved this week: {new_count} new, {resolved_count} resolved")
    lines.append(
        f"- Oldest unresolved age: {oldest_weeks} week{'s' if oldest_weeks != 1 else ''}"
    )
    lines.append(f"- Overflow this week (ranked below the cap, not reviewed): {pool_total}")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


# -- warehouse plumbing, mirroring build/identity_eval.py's exact pattern (PR #476) --------


class WarehouseTableMissing(RuntimeError):
    """The table genuinely does not exist -- the only failure `--allow-unprovisioned` may
    swallow."""

    def __init__(self, table: str, cause: Exception):
        super().__init__(
            f"{table} does not exist ({type(cause).__name__}: {cause}). The "
            f"currentai.identity.digest model has not deployed yet -- see docs/operations/"
            f"deploy-models.md."
        )
        self.table = table


class WarehouseQueryFailed(RuntimeError):
    """A query against `table` failed for a reason OTHER than the table not existing --
    auth, a timeout, a planner error. Always exits 2, `--allow-unprovisioned` or not."""

    def __init__(self, table: str, cause: Exception):
        super().__init__(f"{table} could not be queried ({type(cause).__name__}: {cause})")
        self.table = table


def _is_table_not_found(exc: Exception) -> bool:
    """Whether `exc` is Trino's own "this table does not exist" failure.

    Reuses `build.identity_eval._TABLE_NOT_FOUND_MARKERS` rather than a second copy -- that
    tuple carries the real, verified live text (`USER_ERROR: TablesNotFound - Tables do not
    exist or are inaccessible: <table>`) plus the singular/underscored wordings Trino uses
    elsewhere in its error surface. A local copy of this list is exactly how it drifted from
    the real string once already; see `build/identity_eval.py`'s own comment on that history.
    """
    text = str(exc).lower()
    return any(marker in text for marker in _TABLE_NOT_FOUND_MARKERS)


def load_rows_from_warehouse() -> list[dict]:
    """`currentai.identity.digest`, read live.

    Raises `WarehouseTableMissing` when the failure text says the table does not exist (the
    only case `--allow-unprovisioned` may treat as "not deployed yet"); every other failure
    raises `WarehouseQueryFailed`, which always exits 2.
    """
    from build.warehouse import query

    try:
        return query(f"SELECT * FROM {TABLE}")
    except Exception as exc:  # noqa: BLE001 -- re-raised typed, with the table named
        if _is_table_not_found(exc):
            raise WarehouseTableMissing(TABLE, exc) from exc
        raise WarehouseQueryFailed(TABLE, exc) from exc


def load_rows_from_file(path: Path) -> list[dict]:
    return json.loads(path.read_text())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--week", required=True, help='ISO week, e.g. "2026-36"')
    parser.add_argument("--out", required=True, type=Path, help="path to write the rendered markdown")
    parser.add_argument(
        "--rows", type=Path,
        help="path to a JSON fixture of digest rows, read instead of the warehouse",
    )
    parser.add_argument(
        "--allow-unprovisioned", action="store_true",
        help=(
            "a missing currentai.identity.digest table exits 0 (\"skipped\") instead of 2. "
            "Ignored when --rows is given."
        ),
    )
    args = parser.parse_args(argv)

    if args.rows:
        rows = load_rows_from_file(args.rows)
    else:
        try:
            rows = load_rows_from_warehouse()
        except WarehouseTableMissing as exc:
            if args.allow_unprovisioned:
                print("skipped: identity.digest not provisioned")
                return 0
            print(f"[FAIL] {exc}")
            return 2
        except WarehouseQueryFailed as exc:
            print(f"[FAIL] {exc}")
            return 2

    monday, sunday = _week_bounds(args.week)
    resolved_count = _resolved_this_week(monday, sunday)
    body = render(rows, args.week, resolved_count=resolved_count)
    args.out.write_text(body)
    print(f"wrote {args.out} ({len(rows)} row(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
