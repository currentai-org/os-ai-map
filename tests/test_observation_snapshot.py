"""The observation content digest, the versioned snapshot id, and the canonicalization ratchet.

`build/observation_snapshot.py` derives two things §4.5 names separately:
`observation_content_digest` (the pure content address) and `observation_snapshot_id` (the
versioned identity reconciliation and releases key on). These tests pin the content-alone contract
of the digest, the version binding of the id, UTC timestamp normalization, and a merge-base ratchet
that forbids changing the serializer without a version bump.
"""

import datetime

import pytest

import build.observation_snapshot as osnap
from build.observation_snapshot import (
    CANONICALIZATION_FINGERPRINT,
    CONTENT_COLUMNS,
    CanonicalizationRatchetError,
    check_canonicalization_ratchet,
    merge_base_canonicalization,
    observation_content_digest,
    observation_snapshot_id,
    rows_from_parquet,
    snapshot_id_from_digest,
    _FINGERPRINT_FIXTURE,
)

_UTC = datetime.timezone.utc

# Fixed contracts over the immutable Phase-2 baseline parquet.
BASELINE_CONTENT_DIGEST = "8a6c3e984776302ce116bc2f119a77eaf45dfc7b7aaffc734de74c63ae0d6eab"
BASELINE_SNAPSHOT_ID = "ae1e9dfbc55c82c522edddc03c6286a6b57242a5fd104d2763ec2f966ef3e462"


def _row(**overrides) -> dict:
    base = {
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


# --- content columns -------------------------------------------------------------


def test_content_columns_exclude_lineage_and_capture_time():
    for excluded in (
        "observation_id", "ingested_at", "source_run_id", "source_record_id",
        "source_dataset", "source_table", "is_valid", "supersedes_observation_id",
    ):
        assert excluded not in CONTENT_COLUMNS
    for included in ("product_slug", "artifact_id", "metric_type", "raw_value", "observed_at"):
        assert included in CONTENT_COLUMNS


# --- the pure content digest -----------------------------------------------------


def test_content_digest_is_deterministic_and_order_independent():
    a, b = _row(product_slug="a"), _row(product_slug="b")
    assert observation_content_digest([a, b]) == observation_content_digest([b, a])


def test_lineage_and_capture_time_do_not_change_the_content_digest():
    base = observation_content_digest([_row()])
    for excluded, value in (
        ("source_run_id", "run-xyz"),
        ("ingested_at", datetime.datetime(2027, 1, 1, 0, 0, 0)),
        ("observation_id", "cafebabe"),
        ("is_valid", False),
    ):
        assert observation_content_digest([_row(**{excluded: value})]) == base


def test_measurement_changes_change_the_content_digest():
    base = observation_content_digest([_row()])
    assert observation_content_digest([_row(raw_value=101)]) != base
    assert observation_content_digest([_row(metric_type="downloads")]) != base


def test_content_digest_is_version_independent(monkeypatch):
    """§4.5: the content digest is content and nothing else — the version is bound in the snapshot
    id, not the digest."""
    before = observation_content_digest([_row()])
    monkeypatch.setattr(osnap, "CANONICALIZATION_VERSION", osnap.CANONICALIZATION_VERSION + 1)
    assert observation_content_digest([_row()]) == before


def test_non_finite_numbers_are_rejected():
    with pytest.raises(ValueError):
        observation_content_digest([_row(raw_value=float("inf"))])


def test_missing_content_column_is_loud():
    bad = _row()
    del bad["metric_type"]
    with pytest.raises(KeyError):
        observation_content_digest([bad])


# --- UTC timestamp normalization (finding 2) -------------------------------------


def test_equivalent_instants_produce_one_digest():
    """The same instant, whatever its written offset or naivety, digests identically."""
    aware_utc = _row(observed_at=datetime.datetime(2026, 8, 25, 12, 0, 0, tzinfo=_UTC))
    aware_off = _row(observed_at=datetime.datetime(
        2026, 8, 25, 8, 0, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=-4))))
    naive = _row(observed_at=datetime.datetime(2026, 8, 25, 12, 0, 0))
    d = observation_content_digest([aware_utc])
    assert observation_content_digest([aware_off]) == d  # -04:00 same instant
    assert observation_content_digest([naive]) == d       # naive interpreted UTC


def test_different_instants_differ():
    a = _row(observed_at=datetime.datetime(2026, 8, 25, 12, 0, 0, tzinfo=_UTC))
    b = _row(observed_at=datetime.datetime(2026, 8, 25, 13, 0, 0, tzinfo=_UTC))
    assert observation_content_digest([a]) != observation_content_digest([b])


# --- the versioned snapshot id (finding 1) ---------------------------------------


def test_snapshot_id_binds_the_canonicalization_version(monkeypatch):
    """Bumping the version MUST change the snapshot id, so a stored id names its rule."""
    before = observation_snapshot_id([_row()])
    monkeypatch.setattr(osnap, "CANONICALIZATION_VERSION", osnap.CANONICALIZATION_VERSION + 1)
    assert observation_snapshot_id([_row()]) != before


def test_snapshot_id_is_not_the_bare_content_digest():
    rows = [_row()]
    assert observation_snapshot_id(rows) != observation_content_digest(rows)


def test_snapshot_id_is_a_function_of_the_content_digest():
    rows = [_row()]
    assert observation_snapshot_id(rows) == snapshot_id_from_digest(
        observation_content_digest(rows)
    )


def test_snapshot_id_shape():
    vid = observation_snapshot_id([_row()])
    assert len(vid) == 64 and vid == vid.lower()
    int(vid, 16)


# --- the canonicalization ratchet (finding 3) ------------------------------------


def test_fingerprint_matches_the_current_serializer():
    """The committed fingerprint must equal the digest the current serializer produces over the
    fixture; regenerating it is the only way to change it, which the ratchet then guards."""
    assert observation_content_digest(_FINGERPRINT_FIXTURE) == CANONICALIZATION_FINGERPRINT


def test_ratchet_fires_on_a_serializer_change_without_a_version_bump():
    before = {"version": 1, "fingerprint": "a" * 64}
    with pytest.raises(CanonicalizationRatchetError):
        check_canonicalization_ratchet(before, {"version": 1, "fingerprint": "b" * 64})


def test_ratchet_passes_when_the_version_advances_with_the_fingerprint():
    before = {"version": 1, "fingerprint": "a" * 64}
    check_canonicalization_ratchet(before, {"version": 2, "fingerprint": "b" * 64})


def test_ratchet_passes_when_nothing_changed():
    same = {"version": 1, "fingerprint": "a" * 64}
    check_canonicalization_ratchet(same, dict(same))


def test_ratchet_first_install_is_not_a_violation():
    check_canonicalization_ratchet(None, {"version": 1, "fingerprint": "a" * 64})


def test_canonicalization_ratchet_against_the_merge_base():
    """The real gate: on this branch the module is new (absent at the merge base) so there is
    nothing to ratchet against and this passes; once merged, any serializer change without a
    version bump fails here."""
    before = merge_base_canonicalization()
    now = {"version": osnap.CANONICALIZATION_VERSION, "fingerprint": CANONICALIZATION_FINGERPRINT}
    check_canonicalization_ratchet(before, now)


# --- the pinned contracts over the immutable baseline ----------------------------


def test_reproduces_the_baseline_digests():
    rows = rows_from_parquet()
    assert len(rows) == 654
    digest = observation_content_digest(rows)
    assert digest == BASELINE_CONTENT_DIGEST
    assert snapshot_id_from_digest(digest) == BASELINE_SNAPSHOT_ID


def test_baseline_digest_ignores_read_order():
    rows = rows_from_parquet()
    assert observation_content_digest(rows[::-1]) == BASELINE_CONTENT_DIGEST
