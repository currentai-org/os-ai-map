"""Auto-adoption of confidence-1.0 digest items -- the one case the weekly review does not tick.

Ruling (2026-09-08, Block F question 17): an identity proposal at confidence 1.0 whose NAME agrees
and whose GRAPH agrees is adopted without a human tick; everything below 1.0, and every 1.0 item
that fails either test, keeps rendering as a review item in the digest issue. This module is the
mechanism. `build/identity_digest.py` calls it after the digest issue exists (so `decided_in`
can name the issue), and the workflow opens a pull request carrying whatever it wrote -- a bot
opens PRs, a person merges them, nothing here touches `main`.

## What "name agrees and graph agrees" means, per relation

The two tests are computed here, from the row, not read off a flag the warehouse set:

- **equivalence / membership** (written to `sources/resolution_ledger.yaml`).
  *Name agrees*: the name segment of the artifact id -- the part after the last `/` for
  `owner/repo` and Hub ids, the whole id for a package -- normalized (lowercased, non-alphanumeric
  runs collapsed to `-`) equals the product slug normalized the same way. This is the same test
  `identity_membership_edges.sql` and `identity_equivalence_edges.sql` call `name_match`, and it
  is recomputed rather than trusted so a row that says `name_match` for a name that does not
  match is held rather than written.
  *Graph agrees*: the row's `method` carries an authoritative source -- `resolution_ledger` or
  `declared` (`AUTHORITATIVE_METHODS`). Reading `udms/identity_digest.sql` and the two edge
  tables: 1.0 is reachable ONLY through those two methods (a declared alias is capped at 0.9, a
  model family at 0.8, a name match at 0.5), so today the confidence and the method gate are the
  same test; the method gate is kept explicit so a future evidence source scored 1.0 does not
  qualify by arithmetic alone.

- **org** (written to `sources/org_handles.yaml`).
  *Name agrees*: the account handle derived from the artifact side (`_org_handle` in the digest
  module) agrees with the org slug or with a handle that org already declares, under
  `build.propose_org_handles.name_agrees` -- the same column the #483 handle review read.
  *Graph agrees*: the row's `evidence` carries the graph's own `org_handles: <org> <platform>
  <handle>` claim naming this org, and its method includes `org_handle`. The org model's
  evidence sources are scored 0.85 / 0.80 / 0.75, so no org row reaches 1.0 today; the leg is
  wired for the day one does.
  A row whose artifact kind has no platform account in the handle vocabulary (`pypi`, `npm`,
  `crates`, `arxiv`) is never adopted: the digest's block for it defaults the platform to
  `homepage_domain` with a note asking a person to correct it, and an auto-adopt must not write
  a guess.

## Consequence of what 1.0 means today, stated plainly

Because a 1.0 equivalence rests on a `resolution_ledger` ruling, every 1.0 equivalence item is
by construction ALREADY answered in the ledger. `build/resolution.py::load` raises on a second
entry for the same `(artifact, relation)` key, so the adopt leg checks the destination file
first and classifies each qualifying row as one of:

- `written`          -- the entry was appended to the file that records the relation;
- `already_recorded` -- the file already holds an agreeing ruling (same target, confirm
                        direction); nothing is written, and the digest says so with the existing
                        `decided_in`, so the item stops being a checkbox to tick;
- `conflict`         -- the file holds a DISAGREEING ruling for the same key, or the handle is
                        claimed by another org, or the org has no `sources/organizations/` file.
                        Never overwritten; the item stays in the review queue with the reason.

## How an auto-adopted entry is marked

`note` starts with `build.resolution.AUTO_ADOPT_NOTE_PREFIX` (`digest auto-adopt (confidence
1.0):`), in both files. A fixed prefix, not a schema field: both files publish to warehouse
static tables whose schema cannot grow a column without delete-and-recreate. `build/identity_eval.py`
excludes every entry carrying the prefix from truth -- the graph must not be scored against
rulings the graph wrote.

## Write discipline

Entries are APPENDED as a YAML block, never load-modify-dump: both files are hand-formatted with
comments and a full rewrite would rewrap the corpus. Each entry is schema-validated before it is
written, and the file is re-read after the write so a malformed append fails loudly. The batch
dedupes on the destination key, so two rows resolving to one handle write it once.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import jsonschema
import yaml

from build import resolution
from build.identity import fold_for_proposal, fold_handle
from build.identity_digest import (
    _ORG_HANDLE_PLATFORM,
    _as_list,
    _ledger_entry,
    _org_handle,
    _org_handle_entry,
    _pair,
)
from build.propose_org_handles import name_agrees as _handle_name_agrees
from build.resolution import AUTO_ADOPT_NOTE_PREFIX

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = resolution.LEDGER
ORG_HANDLES_PATH = ROOT / "sources" / "org_handles.yaml"
ORGANIZATIONS_DIR = ROOT / "sources" / "organizations"
LEDGER_SCHEMA_PATH = ROOT / "docs" / "schemas" / "resolution_ledger.schema.json"
ORG_HANDLES_SCHEMA_PATH = ROOT / "docs" / "schemas" / "org_handles.schema.json"

#: The ruling's threshold. Compared EXACTLY: the digest SQL assigns 1.0 as a literal for the
#: authoritative methods, so a value that merely rounds to 1.0 (0.9999999995), NaN, or anything
#: above 1.0 is a row the SQL never produced and must be held, not adopted.
THRESHOLD = 1.0
#: The methods a 1.0 may legitimately rest on for a ledger relation. See the module docstring.
AUTHORITATIVE_METHODS = frozenset({"resolution_ledger", "declared"})
LEDGER_RELATIONS = ("equivalence", "membership")
ADOPTABLE_RELATIONS = LEDGER_RELATIONS + ("org",)
ACTIVE_STATES = ("active", "resurfaced")

LEDGER_REL = "sources/resolution_ledger.yaml"
ORG_HANDLES_REL = "sources/org_handles.yaml"


@dataclass
class Disposition:
    """What the adopt leg decided about one qualifying row."""

    row: dict
    outcome: str  # "written" | "already_recorded" | "conflict"
    target: str  # repo-relative path of the file that records the relation
    reason: str
    entry: dict | None = None

    @property
    def item_id(self) -> str:
        return str(self.row.get("item_id"))

    def to_json(self) -> dict:
        left_kind, left_id = _pair(self.row.get("left"))
        right_kind, right_id = _pair(self.row.get("right"))
        return {
            "item_id": self.item_id,
            "rank": self.row.get("rank"),
            "relation": self.row.get("relation"),
            "left": f"{left_kind}:{left_id}",
            "right": f"{right_kind}:{right_id}",
            "confidence": self.row.get("confidence"),
            "method": _as_list(self.row.get("method")),
            "evidence": _as_list(self.row.get("evidence")),
            "outcome": self.outcome,
            "target": self.target,
            "reason": self.reason,
            "entry": self.entry,
        }


@dataclass
class AdoptReport:
    decided_in: str
    decided_on: str
    written: list[Disposition] = field(default_factory=list)
    already_recorded: list[Disposition] = field(default_factory=list)
    conflicts: list[Disposition] = field(default_factory=list)
    dry_run: bool = False

    def adopted_item_ids(self) -> set[str]:
        """Items that no longer need a tick: written now, or already recorded by a person."""
        return {d.item_id for d in self.written} | {d.item_id for d in self.already_recorded}

    def conflict_reasons(self) -> dict[str, str]:
        return {d.item_id: d.reason for d in self.conflicts}

    def to_json(self) -> dict:
        return {
            "decided_in": self.decided_in,
            "decided_on": self.decided_on,
            "dry_run": self.dry_run,
            "written": [d.to_json() for d in self.written],
            "already_recorded": [d.to_json() for d in self.already_recorded],
            "conflicts": [d.to_json() for d in self.conflicts],
        }


# -- the two tests -------------------------------------------------------------------------


def _normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")


def _name_segment(kind: str, ident: str) -> str:
    """The part of an artifact id a product slug is compared to: the segment after the last `/`
    for `owner/repo` and Hub ids, the folded id itself for a package. `homepage` ids fold to
    `host/path`; the last path segment is the closest thing to a name they carry."""
    folded = fold_for_proposal(kind, ident) if kind else (ident or "")
    return folded.rsplit("/", 1)[-1] if "/" in folded else folded


def _load_org_handles(path: Path) -> dict:
    if not path.exists():
        return {"version": 1, "handles": []}
    return yaml.safe_load(path.read_text()) or {"version": 1, "handles": []}


def _handles_of(org_handles: dict, org_slug: str) -> list[str]:
    return [
        str(e.get("handle"))
        for e in (org_handles.get("handles") or [])
        if isinstance(e, dict) and e.get("org") == org_slug and isinstance(e.get("handle"), str)
    ]


def name_agrees(row: dict, org_handles: dict | None = None) -> bool:
    """See the module docstring: name segment == product slug (ledger relations), or the derived
    handle agrees with the org slug / one of its declared handles (org)."""
    relation = row.get("relation")
    left_kind, left_id = _pair(row.get("left"))
    _, right_id = _pair(row.get("right"))
    if relation in LEDGER_RELATIONS:
        return _normalize_name(_name_segment(left_kind, left_id)) == _normalize_name(right_id)
    if relation == "org":
        if left_kind not in _ORG_HANDLE_PLATFORM:
            return False
        _, handle = _org_handle(left_kind, left_id)
        declared = _handles_of(org_handles or {}, right_id)
        return _handle_name_agrees(handle, right_id, declared)
    return False


def graph_agrees(row: dict) -> bool:
    """See the module docstring: an authoritative method for a ledger relation; the graph's own
    `org_handles: <org> ...` evidence line plus the `org_handle` method for an org row."""
    relation = row.get("relation")
    methods = set(_as_list(row.get("method")))
    if relation in LEDGER_RELATIONS:
        return bool(methods & AUTHORITATIVE_METHODS)
    if relation == "org":
        _, org_slug = _pair(row.get("right"))
        if "org_handle" not in methods:
            return False
        marker = f"org_handles: {org_slug} "
        return any(marker in e for e in _as_list(row.get("evidence")))
    return False


def qualifies(row: dict, org_handles: dict | None = None) -> tuple[bool, str]:
    """`(qualifies, reason)` for one digest row under the ruling. A row must be a ranked,
    active item of an adoptable relation, at the threshold, and pass both tests."""
    if row.get("state") not in ACTIVE_STATES or row.get("rank") is None:
        return False, "not a ranked active item"
    if row.get("relation") not in ADOPTABLE_RELATIONS:
        return False, f"relation {row.get('relation')!r} has no file to write"
    try:
        confidence = float(row.get("confidence"))
    except (TypeError, ValueError):
        return False, "confidence unreadable"
    if isinstance(row.get("confidence"), bool) or not math.isfinite(confidence):
        return False, f"confidence {row.get('confidence')!r} is not a finite number"
    if confidence != THRESHOLD:
        return False, f"confidence {confidence} is not exactly {THRESHOLD}"
    if not graph_agrees(row):
        return False, "graph does not agree (no authoritative method or evidence line)"
    if not name_agrees(row, org_handles):
        return False, "name does not agree"
    return True, "confidence 1.0, name agrees, graph agrees"


# -- destination checks --------------------------------------------------------------------


def _ledger_disposition(row: dict, ledger: dict) -> tuple[str, str, dict | None]:
    """`(outcome, reason, existing_entry)` against the loaded ledger for a ledger relation."""
    relation = row.get("relation")
    left_kind, left_id = _pair(row.get("left"))
    _, right_id = _pair(row.get("right"))
    if relation == "membership":
        existing = resolution.verdict_for(
            left_kind, left_id, "product_membership", ledger, product_slug=right_id
        )
        if existing is None:
            return "written", "no prior ruling", None
        decided_in = existing.get("decided_in", "an earlier ruling")
        if existing.get("verdict") == "member_of":
            return "already_recorded", f"member_of {right_id}, decided in {decided_in}", existing
        return "conflict", f"ledger rules {existing.get('verdict')} for {right_id}, decided in {decided_in}; not overturned", existing
    existing = resolution.verdict_for(left_kind, left_id, "product_equivalence", ledger)
    if existing is None:
        return "written", "no prior ruling", None
    decided_in = existing.get("decided_in", "an earlier ruling")
    target = existing.get("resolves_to") or existing.get("product")
    if existing.get("verdict") in ("existing_product", "sku_of") and target == right_id:
        return (
            "already_recorded",
            f"{existing['verdict']} -> {right_id}, decided in {decided_in}",
            existing,
        )
    return (
        "conflict",
        f"ledger rules {existing.get('verdict')}"
        + (f" -> {target}" if target else "")
        + f", decided in {decided_in}; not overturned",
        existing,
    )


def _handle_owner_map(org_handles: dict) -> dict[tuple[str, str], str]:
    out: dict[tuple[str, str], str] = {}
    for e in org_handles.get("handles") or []:
        if not isinstance(e, dict):
            continue
        platform, handle, org = e.get("platform"), e.get("handle"), e.get("org")
        if isinstance(platform, str) and isinstance(handle, str) and isinstance(org, str):
            out.setdefault((platform, fold_handle(platform, handle)), org)
    return out


def _org_disposition(
    row: dict, owners: dict[tuple[str, str], str], organizations_dir: Path
) -> tuple[str, str]:
    left_kind, left_id = _pair(row.get("left"))
    _, org_slug = _pair(row.get("right"))
    platform, handle = _org_handle(left_kind, left_id)
    owner = owners.get((platform, fold_handle(platform, handle)))
    if owner == org_slug:
        return "already_recorded", f"{platform} handle {handle!r} declared for {org_slug}"
    if owner is not None:
        return "conflict", f"{platform} handle {handle!r} is declared for {owner!r}, not {org_slug!r}"
    if not (organizations_dir / f"{org_slug}.yaml").exists():
        return "conflict", f"no sources/organizations/{org_slug}.yaml to attach the handle to"
    return "written", "no prior handle"


# -- entries and the append ----------------------------------------------------------------


def _auto_note(row: dict, reason: str) -> str:
    left_kind, left_id = _pair(row.get("left"))
    right_kind, right_id = _pair(row.get("right"))
    methods = ", ".join(_as_list(row.get("method"))) or "none"
    return (
        f"{AUTO_ADOPT_NOTE_PREFIX} {left_kind}:{left_id} -> {right_kind}:{right_id}; "
        f"{reason}; method {methods}."
    )


def build_entry(row: dict, decided_in: str, decided_on: date, reason: str) -> dict:
    """The exact dict appended for a qualifying row -- the digest's own confirm-direction block,
    with `decided_in` naming the digest issue and the auto-adopt note."""
    if row.get("relation") == "org":
        entry = _org_handle_entry(row)
    else:
        entry = _ledger_entry(row, decided_on)
        entry["decided_in"] = decided_in
    entry["note"] = _auto_note(row, reason)
    return entry


def _append_yaml(path: Path, entries: list[dict]) -> None:
    text = path.read_text()
    if text and not text.endswith("\n"):
        text += "\n"
    block = yaml.safe_dump(entries, sort_keys=False, default_flow_style=False, width=100, allow_unicode=True)
    path.write_text(text + block)


def plan(
    rows: list[dict],
    *,
    decided_in: str,
    decided_on: date,
    ledger_path: Path = LEDGER_PATH,
    org_handles_path: Path = ORG_HANDLES_PATH,
    organizations_dir: Path = ORGANIZATIONS_DIR,
) -> AdoptReport:
    """Classify every qualifying row without writing anything."""
    org_handles = _load_org_handles(org_handles_path)
    ledger = resolution.load(ledger_path)
    owners = _handle_owner_map(org_handles)
    ledger_schema = json.loads(LEDGER_SCHEMA_PATH.read_text())
    handle_schema = json.loads(ORG_HANDLES_SCHEMA_PATH.read_text())["properties"]["handles"]["items"]

    report = AdoptReport(decided_in=decided_in, decided_on=decided_on.isoformat())
    seen_ledger_keys: set = set()
    ranked = sorted(
        (r for r in rows if r.get("state") in ACTIVE_STATES and r.get("rank") is not None),
        key=lambda r: r["rank"],
    )
    for row in ranked:
        ok, reason = qualifies(row, org_handles)
        if not ok:
            continue
        if row.get("relation") == "org":
            outcome, why = _org_disposition(row, owners, organizations_dir)
            target = ORG_HANDLES_REL
            if outcome == "written":
                entry = build_entry(row, decided_in, decided_on, reason)
                jsonschema.validate(entry, handle_schema)
                # A second row onto the same handle in one batch: the first writes it.
                owners[(entry["platform"], fold_handle(entry["platform"], entry["handle"]))] = entry["org"]
                report.written.append(Disposition(row, outcome, target, why, entry))
                continue
        else:
            outcome, why, _existing = _ledger_disposition(row, ledger)
            target = LEDGER_REL
            if outcome == "written":
                entry = build_entry(row, decided_in, decided_on, reason)
                jsonschema.validate(entry, ledger_schema)
                key = resolution.key_for(entry)
                if key in seen_ledger_keys:
                    report.already_recorded.append(
                        Disposition(row, "already_recorded", target, "written earlier in this batch")
                    )
                    continue
                seen_ledger_keys.add(key)
                ledger[key] = entry
                report.written.append(Disposition(row, outcome, target, why, entry))
                continue
        if outcome == "already_recorded":
            report.already_recorded.append(Disposition(row, outcome, target, why))
        else:
            report.conflicts.append(Disposition(row, outcome, target, why))
    return report


def apply(
    report: AdoptReport,
    *,
    ledger_path: Path = LEDGER_PATH,
    org_handles_path: Path = ORG_HANDLES_PATH,
) -> None:
    """Append the `written` entries to their files, then re-read both so a malformed append
    fails here rather than in a later gate."""
    ledger_entries = [d.entry for d in report.written if d.target == LEDGER_REL and d.entry]
    handle_entries = [d.entry for d in report.written if d.target == ORG_HANDLES_REL and d.entry]
    if ledger_entries:
        _append_yaml(ledger_path, ledger_entries)
        resolution.load(ledger_path)  # raises DuplicateResolution / YAML errors loudly
    if handle_entries:
        _append_yaml(org_handles_path, handle_entries)
        doc = _load_org_handles(org_handles_path)
        jsonschema.validate(doc, json.loads(ORG_HANDLES_SCHEMA_PATH.read_text()))


def adopt(
    rows: list[dict],
    *,
    decided_in: str,
    decided_on: date | None = None,
    write: bool = True,
    ledger_path: Path = LEDGER_PATH,
    org_handles_path: Path = ORG_HANDLES_PATH,
    organizations_dir: Path = ORGANIZATIONS_DIR,
) -> AdoptReport:
    """Plan, then (unless `write=False`) append. Returns the report either way."""
    decided_on = decided_on or date.today()
    report = plan(
        rows,
        decided_in=decided_in,
        decided_on=decided_on,
        ledger_path=ledger_path,
        org_handles_path=org_handles_path,
        organizations_dir=organizations_dir,
    )
    if write:
        apply(report, ledger_path=ledger_path, org_handles_path=org_handles_path)
    else:
        report.dry_run = True
    return report
