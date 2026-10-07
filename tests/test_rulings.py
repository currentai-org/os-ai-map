"""The rulings log keeps its shape: append-only in date order, and every reference resolves.

`docs/rulings/log.yaml` is what an agent reads before it asks the maintainer anything, so a
malformed entry is worse than a missing one: it reads as a ruling that was never made, or one
still in force after it was replaced. The rules are written up in docs/rulings/README.md.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import pytest

from build.review_queue import load_rulings
from build.vocabulary import parse_date

REPO = Path(__file__).resolve().parents[1]
REQUIRED = ("id", "date", "by", "venue", "question", "ruling", "status", "executor")
VENUES = {"session", "walk-and-talk", "oso-task", "issue", "pr-review"}
STATUSES = {"in-force", "deferred", "replaced"}
EXECUTORS = {"agent", "maintainer", "none"}
ID = re.compile(r"^R-(\d{4}-\d{2}-\d{2})-[a-z]+$")


@pytest.fixture(scope="module")
def rulings() -> list[dict]:
    return load_rulings(REPO)


def test_the_log_parses_and_has_entries(rulings):
    assert rulings, "docs/rulings/log.yaml has no rulings"


def test_every_entry_carries_the_required_fields(rulings):
    missing = [(r.get("id"), f) for r in rulings for f in REQUIRED if not str(r.get(f) or "").strip()]
    assert not missing, f"entries missing a required field: {missing}"


def test_enumerated_fields_take_declared_values(rulings):
    bad = [
        (r["id"], field, r.get(field))
        for r in rulings
        for field, allowed in (("venue", VENUES), ("status", STATUSES), ("executor", EXECUTORS))
        if r.get(field) not in allowed
    ]
    assert not bad, f"undeclared values: {bad}"


def test_ids_are_unique_and_carry_their_date(rulings):
    ids = [r["id"] for r in rulings]
    assert len(ids) == len(set(ids)), "a ruling id is reused"
    for r in rulings:
        m = ID.match(r["id"])
        assert m, f"{r['id']} is not R-<YYYY-MM-DD>-<letter>"
        assert parse_date(m.group(1)) == parse_date(r["date"]), f"{r['id']} disagrees with its date"


def test_entries_are_appended_in_date_order_and_not_from_the_future(rulings):
    dates = [parse_date(r["date"]) for r in rulings]
    assert all(dates), "a ruling date does not parse"
    assert dates == sorted(dates), "rulings are not in date order; the log is append-only"
    assert max(dates) <= date.today(), "a ruling is dated in the future"


def test_replacement_is_recorded_on_both_sides(rulings):
    ids = {r["id"] for r in rulings}
    for r in rulings:
        if r["status"] == "replaced":
            assert r.get("replaced_by") in ids, f"{r['id']} is replaced by nothing that exists"
        else:
            assert not r.get("replaced_by"), f"{r['id']} names a replacement but is {r['status']}"


def test_every_home_a_ruling_lands_in_exists(rulings):
    missing = [(r["id"], p) for r in rulings for p in r.get("lands_in") or [] if not (REPO / p).exists()]
    assert not missing, f"lands_in paths that do not exist: {missing}"
