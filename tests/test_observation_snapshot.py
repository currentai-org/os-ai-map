"""The observation content digest, the versioned snapshot id, and the canonicalization ratchet.

`build/observation_snapshot.py` derives the two things §4.5 names separately —
`observation_content_digest` (the pure content address) and `observation_snapshot_id` (the
versioned, domain-separated identity). These tests pin the content-alone contract, the version
binding and exact preimage of the id, UTC timestamp normalization with strict typing, and a
merge-base ratchet over an explicit contract descriptor that forbids a serialization change without
a version bump.
"""

import datetime
import hashlib

import pytest

import build.observation_snapshot as osnap
from build.observation_snapshot import (
    CANONICALIZATION_CONTRACT,
    CANONICALIZATION_FINGERPRINT,
    CANONICALIZATION_VERSION,
    CONTENT_COLUMNS,
    IDENTITY_COLUMNS,
    CanonicalizationRatchetError,
    canonicalization_fingerprint,
    check_canonicalization_ratchet,
    merge_base_canonicalization,
    observation_content_digest,
    observation_snapshot_id,
    rows_from_parquet,
    snapshot_id_from_digest,
)

_UTC = datetime.timezone.utc

# Fixed contracts over the immutable Phase-2 baseline parquet.
BASELINE_CONTENT_DIGEST = "8a6c3e984776302ce116bc2f119a77eaf45dfc7b7aaffc734de74c63ae0d6eab"
BASELINE_SNAPSHOT_ID = "9bd4d93a6fc67a2b9d89d91adeb4bb3f4fd9b612cc26e6647c67210c9a37a8d4"

# A behavioral fixture exercising tz-aware + naive timestamps, a null window, and unicode. Its
# digest is a separate behavioral golden — the canonicalization FINGERPRINT is over the contract
# descriptor, not this fixture, so a declared-rule change is caught even if no fixture exercises it.
_BEHAVIOR_FIXTURE = (
    {
        "product_slug": "fixture-a", "product_type": "model", "artifact_kind": "github",
        "artifact_id": "ówner/repo", "channel": "github", "metric_type": "stars",
        "raw_value": 42, "unit": "stars", "measurement_window_days": None,
        "observed_at": datetime.datetime(2026, 1, 2, 3, 4, 5, tzinfo=_UTC),
    },
    {
        "product_slug": "fixture-b", "product_type": "dataset", "artifact_kind": "huggingface_dataset",
        "artifact_id": "org/set", "channel": "huggingface", "metric_type": "downloads",
        "raw_value": 1000, "unit": "downloads", "measurement_window_days": 30,
        "observed_at": datetime.datetime(2026, 1, 2, 3, 4, 5),  # naive → interpreted UTC
    },
)
BEHAVIOR_FIXTURE_DIGEST = "e2e93998bdcf8fabe99fc2fb6d8e3870bf255785b153ba53138fd15ae578eb5c"


def _row(**overrides) -> dict:
    base = {
        "product_slug": "acme", "product_type": "model", "artifact_kind": "github",
        "artifact_id": "acme/thing", "channel": "github", "metric_type": "stars",
        "raw_value": 100, "unit": "stars", "measurement_window_days": None,
        "observed_at": datetime.datetime(2026, 8, 20, 12, 0, 0),
        "observation_id": "deadbeef", "ingested_at": datetime.datetime(2026, 8, 25, 5, 0, 0),
        "source_dataset": "signal_github", "source_table": "currentai.signal_github.artifact_state",
        "source_run_id": None, "source_record_id": None, "is_valid": True,
        "supersedes_observation_id": None,
    }
    base.update(overrides)
    return base


# --- content columns & the pure content digest -----------------------------------


def test_content_columns_exclude_lineage_and_capture_time():
    for excluded in (
        "observation_id", "ingested_at", "source_run_id", "source_record_id",
        "source_dataset", "source_table", "is_valid", "supersedes_observation_id",
    ):
        assert excluded not in CONTENT_COLUMNS


def test_content_digest_is_deterministic_and_order_independent():
    a, b = _row(product_slug="a"), _row(product_slug="b")
    assert observation_content_digest([a, b]) == observation_content_digest([b, a])


def test_lineage_and_capture_time_do_not_change_the_content_digest():
    base = observation_content_digest([_row()])
    for excluded, value in (
        ("source_run_id", "run-xyz"),
        ("ingested_at", datetime.datetime(2027, 1, 1)),
        ("observation_id", "cafebabe"),
        ("is_valid", False),
    ):
        assert observation_content_digest([_row(**{excluded: value})]) == base


def test_measurement_changes_change_the_content_digest():
    base = observation_content_digest([_row()])
    assert observation_content_digest([_row(raw_value=101)]) != base
    assert observation_content_digest([_row(metric_type="downloads")]) != base


def test_content_digest_is_version_independent(monkeypatch):
    before = observation_content_digest([_row()])
    monkeypatch.setattr(osnap, "CANONICALIZATION_VERSION", osnap.CANONICALIZATION_VERSION + 1)
    assert observation_content_digest([_row()]) == before


# --- strict per-column typing ----------------------------------------------------


def test_observed_at_must_be_a_datetime():
    """A string or other lookalike is rejected — it would bypass UTC normalization."""
    for bad in ("2026-08-20T12:00:00", "2026-08-20T12:00:00Z", 1_755_000_000, datetime.date(2026, 8, 20)):
        with pytest.raises(TypeError):
            observation_content_digest([_row(observed_at=bad)])


def test_identity_columns_must_be_nonempty_strings():
    """Every identity/vocabulary/unit field rejects a non-string and an empty string."""
    assert IDENTITY_COLUMNS == {
        "product_slug", "product_type", "artifact_kind", "artifact_id",
        "channel", "metric_type", "unit",
    }
    for column in IDENTITY_COLUMNS:
        with pytest.raises(TypeError):  # a bare int is not a slug
            observation_content_digest([_row(**{column: 123})])
        with pytest.raises(TypeError):  # bool is not a str (exact-type check)
            observation_content_digest([_row(**{column: True})])
        with pytest.raises(TypeError):  # None is not a nonempty str
            observation_content_digest([_row(**{column: None})])
        with pytest.raises(ValueError):  # empty string
            observation_content_digest([_row(**{column: ""})])


def test_raw_value_must_be_a_finite_number_and_not_a_bool():
    with pytest.raises(TypeError):  # a numeric string is not a measurement
        observation_content_digest([_row(raw_value="100")])
    with pytest.raises(TypeError):  # bool is not a number (exact-type check)
        observation_content_digest([_row(raw_value=True)])
    with pytest.raises(TypeError):  # None is not a measurement
        observation_content_digest([_row(raw_value=None)])
    with pytest.raises(ValueError):
        observation_content_digest([_row(raw_value=float("inf"))])
    with pytest.raises(ValueError):
        observation_content_digest([_row(raw_value=float("nan"))])
    # a finite int and a finite float are both accepted, and 0 is a legitimate measurement.
    observation_content_digest([_row(raw_value=0)])
    observation_content_digest([_row(raw_value=3.5)])


def test_measurement_window_days_must_be_a_nonnegative_int_or_null():
    with pytest.raises(TypeError):  # bool is not an int here (exact-type check)
        observation_content_digest([_row(measurement_window_days=True)])
    with pytest.raises(TypeError):  # a float is not an int
        observation_content_digest([_row(measurement_window_days=30.0)])
    with pytest.raises(TypeError):  # a numeric string is not an int
        observation_content_digest([_row(measurement_window_days="30")])
    with pytest.raises(ValueError):  # negative
        observation_content_digest([_row(measurement_window_days=-1)])
    # None and a nonnegative int are both accepted.
    observation_content_digest([_row(measurement_window_days=None)])
    observation_content_digest([_row(measurement_window_days=0)])
    observation_content_digest([_row(measurement_window_days=30)])


def test_unexpected_type_in_a_content_column_is_rejected():
    with pytest.raises(TypeError):
        observation_content_digest([_row(raw_value={1, 2})])


def test_missing_content_column_is_loud():
    bad = _row()
    del bad["metric_type"]
    with pytest.raises(KeyError):
        observation_content_digest([bad])


# --- UTC timestamp normalization -------------------------------------------------


def test_equivalent_instants_produce_one_digest():
    aware_utc = _row(observed_at=datetime.datetime(2026, 8, 25, 12, 0, 0, tzinfo=_UTC))
    aware_off = _row(observed_at=datetime.datetime(
        2026, 8, 25, 8, 0, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=-4))))
    naive = _row(observed_at=datetime.datetime(2026, 8, 25, 12, 0, 0))
    d = observation_content_digest([aware_utc])
    assert observation_content_digest([aware_off]) == d
    assert observation_content_digest([naive]) == d


def test_different_instants_differ():
    a = _row(observed_at=datetime.datetime(2026, 8, 25, 12, 0, 0, tzinfo=_UTC))
    b = _row(observed_at=datetime.datetime(2026, 8, 25, 13, 0, 0, tzinfo=_UTC))
    assert observation_content_digest([a]) != observation_content_digest([b])


# --- the versioned, domain-separated snapshot id ---------------------------------


def test_snapshot_id_binds_the_canonicalization_version(monkeypatch):
    before = observation_snapshot_id([_row()])
    monkeypatch.setattr(osnap, "CANONICALIZATION_VERSION", osnap.CANONICALIZATION_VERSION + 1)
    assert observation_snapshot_id([_row()]) != before


def test_snapshot_id_uses_the_documented_domain_separated_preimage():
    """The id is SHA-256 of exactly 'os-ai-map:observation-snapshot:v<N>\\0<content_digest>'."""
    digest = "b" * 64
    expected = hashlib.sha256(
        f"os-ai-map:observation-snapshot:v{CANONICALIZATION_VERSION}\0{digest}".encode("utf-8")
    ).hexdigest()
    assert snapshot_id_from_digest(digest) == expected


def test_snapshot_id_from_digest_rejects_a_malformed_digest():
    """Fail closed before minting: only a 64-char lowercase hex digest is a valid preimage."""
    for bad in ("x", "b" * 63, "b" * 65, "B" * 64, "g" * 64, 123, None):
        with pytest.raises((ValueError, TypeError)):
            snapshot_id_from_digest(bad)


def test_snapshot_id_from_digest_rejects_a_nonpositive_or_nonint_version():
    good = "b" * 64
    for bad_version in (0, -1, True, 1.0, "1"):
        with pytest.raises((ValueError, TypeError)):
            snapshot_id_from_digest(good, version=bad_version)


def test_snapshot_id_is_not_the_bare_content_digest():
    rows = [_row()]
    assert observation_snapshot_id(rows) != observation_content_digest(rows)


def test_snapshot_id_shape():
    vid = observation_snapshot_id([_row()])
    assert len(vid) == 64 and vid == vid.lower()
    int(vid, 16)


# --- the canonicalization ratchet over an explicit contract descriptor -----------


def test_contract_descriptor_matches_the_live_constants():
    assert CANONICALIZATION_CONTRACT["version"] == CANONICALIZATION_VERSION
    assert CANONICALIZATION_CONTRACT["content_columns"] == list(CONTENT_COLUMNS)


def test_fingerprint_is_the_contract_descriptor_digest():
    """The fingerprint is over the DECLARED contract, so a rule change moves it even where no
    fixture exercises that rule."""
    assert canonicalization_fingerprint() == CANONICALIZATION_FINGERPRINT


def test_behavioral_fixture_digest_is_pinned():
    """Implementation behavior is pinned separately from the contract fingerprint."""
    assert observation_content_digest(_BEHAVIOR_FIXTURE) == BEHAVIOR_FIXTURE_DIGEST


def test_ratchet_fires_on_a_contract_change_without_a_version_bump():
    before = {"version": 1, "fingerprint": "a" * 64}
    with pytest.raises(CanonicalizationRatchetError):
        check_canonicalization_ratchet(before, {"version": 1, "fingerprint": "b" * 64})


def test_ratchet_passes_when_the_version_advances():
    before = {"version": 1, "fingerprint": "a" * 64}
    check_canonicalization_ratchet(before, {"version": 2, "fingerprint": "b" * 64})


def test_ratchet_passes_when_nothing_changed():
    same = {"version": 1, "fingerprint": "a" * 64}
    check_canonicalization_ratchet(same, dict(same))


def test_ratchet_first_install_is_not_a_violation():
    check_canonicalization_ratchet(None, {"version": 1, "fingerprint": "a" * 64})


def test_canonicalization_ratchet_against_the_merge_base():
    """The real gate: the module is new on this branch (absent at the merge base) so this passes
    without a skip; once merged, a contract change without a version bump fails here."""
    before = merge_base_canonicalization()
    now = {"version": CANONICALIZATION_VERSION, "fingerprint": CANONICALIZATION_FINGERPRINT}
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
