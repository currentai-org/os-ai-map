"""The observation-snapshot identity, and the properties §4.5 requires of it.

`build/observation_snapshot.py` derives `observation_snapshot_id` — the content address of a set
of normalized adoption observations, which `evaluation.adoption_reconciliation` and
`releases.manifest` key on. These tests pin the content-alone contract: it depends on the
measurement and nothing else (not lineage, not capture time, not row order, not the
canonicalization version), and it reproduces a fixed value over the immutable Phase-2 baseline.
"""

import copy
import datetime

import pytest

import build.observation_snapshot as osnap
from build.observation_snapshot import (
    CONTENT_COLUMNS,
    observation_snapshot_id,
    rows_from_parquet,
)

# The snapshot id over the committed baseline parquet. The baseline bytes are ratchet-locked
# (tests/test_baseline_contract.py), so this is a fixed contract; a change here means the
# canonicalization drifted, and CANONICALIZATION_VERSION must move with it.
BASELINE_SNAPSHOT_ID = "78922959233f1f83c72fb04d9877fbe67168a1e5517eaa3cb575c0886d1d1533"


def _row(**overrides) -> dict:
    """A minimal observation row carrying every column the id must ignore, plus the content."""
    base = {
        # content
        "product_slug": "acme", "product_type": "model", "artifact_kind": "github",
        "artifact_id": "acme/thing", "channel": "github", "metric_type": "stars",
        "raw_value": 100, "unit": "stars", "measurement_window_days": None,
        "observed_at": datetime.datetime(2026, 8, 20, 12, 0, 0),
        # excluded: lineage / capture-time / derived / history
        "observation_id": "deadbeef", "ingested_at": datetime.datetime(2026, 8, 25, 5, 0, 0),
        "source_dataset": "signal_github", "source_table": "currentai.signal_github.artifact_state",
        "source_run_id": None, "source_record_id": None, "is_valid": True,
        "supersedes_observation_id": None,
    }
    base.update(overrides)
    return base


# --- the content column set -------------------------------------------------------


def test_content_columns_exclude_lineage_and_capture_time():
    """The digest covers the measurement, not how or when it was recorded."""
    for excluded in (
        "observation_id", "ingested_at", "source_run_id", "source_record_id",
        "source_dataset", "source_table", "is_valid", "supersedes_observation_id",
    ):
        assert excluded not in CONTENT_COLUMNS
    for included in ("product_slug", "artifact_id", "metric_type", "raw_value", "observed_at"):
        assert included in CONTENT_COLUMNS


# --- content-alone behavior -------------------------------------------------------


def test_deterministic():
    rows = [_row()]
    assert observation_snapshot_id(rows) == observation_snapshot_id(rows)


def test_order_independent_multiset():
    a, b = _row(product_slug="a"), _row(product_slug="b")
    assert observation_snapshot_id([a, b]) == observation_snapshot_id([b, a])


def test_lineage_and_capture_time_do_not_change_the_id():
    """Run identifiers, capture time, and provenance are lineage — a re-run that changes only
    those keeps the same snapshot id (§4.3)."""
    base = observation_snapshot_id([_row()])
    for excluded, value in (
        ("source_run_id", "run-xyz"),
        ("ingested_at", datetime.datetime(2027, 1, 1, 0, 0, 0)),
        ("observation_id", "cafebabe"),
        ("source_table", "somewhere.else"),
        ("is_valid", False),
        ("supersedes_observation_id", "prior"),
    ):
        assert observation_snapshot_id([_row(**{excluded: value})]) == base, (
            f"changing {excluded} changed the snapshot id; it must be content-alone"
        )


def test_measurement_changes_do_change_the_id():
    base = observation_snapshot_id([_row()])
    assert observation_snapshot_id([_row(raw_value=101)]) != base
    assert observation_snapshot_id([_row(observed_at=datetime.datetime(2026, 8, 21, 12, 0, 0))]) != base
    assert observation_snapshot_id([_row(metric_type="downloads")]) != base
    assert observation_snapshot_id([_row(measurement_window_days=30)]) != base


def test_canonicalization_version_is_not_folded_into_the_id(monkeypatch):
    """§4.5 is strict: the id is content and nothing else. Bumping the canonicalization version
    (recorded beside the id) must NOT change the id itself."""
    before = observation_snapshot_id([_row()])
    monkeypatch.setattr(osnap, "CANONICALIZATION_VERSION", osnap.CANONICALIZATION_VERSION + 1)
    assert observation_snapshot_id([_row()]) == before


def test_shape_is_64_hex():
    vid = observation_snapshot_id([_row()])
    assert len(vid) == 64 and vid == vid.lower()
    int(vid, 16)


def test_non_finite_numbers_are_rejected():
    with pytest.raises(ValueError):
        observation_snapshot_id([_row(raw_value=float("inf"))])


def test_missing_content_column_is_loud():
    bad = _row()
    del bad["metric_type"]
    with pytest.raises(KeyError):
        observation_snapshot_id([bad])


# --- the pinned contract over the immutable baseline ------------------------------


def test_reproduces_the_baseline_snapshot_id():
    """The id over the committed baseline is a fixed contract: the baseline bytes are immutable,
    so this value only changes if the canonicalization changes — which requires a version bump."""
    rows = rows_from_parquet()
    assert len(rows) == 654
    assert observation_snapshot_id(rows) == BASELINE_SNAPSHOT_ID


def test_baseline_snapshot_ignores_the_row_order_it_is_read_in():
    rows = rows_from_parquet()
    shuffled = copy.deepcopy(rows)[::-1]
    assert observation_snapshot_id(shuffled) == BASELINE_SNAPSHOT_ID
