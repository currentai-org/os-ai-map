"""`check_payload` must gate the SHAPE of a freshness caveat, not just its presence.

The defect the `partial` basis exists for was a lossy reduction no payload gate could see.
Shipping `partial` without gating it leaves that hole open one shape over: a record reading
`{"date": ..., "basis": "partial"}` with nothing saying what is partial is strictly worse
than `verified`, because it advertises a caveat and then withholds it. That shape passed the
first cut of this PR.
"""

import pytest

from build.check_payload import PayloadError, _check_freshness_caveats

HOLD = {"axis": "adoption", "since": "2026-08-15", "reason": "no figure published"}


@pytest.mark.parametrize(
    "name, record",
    [
        ("partial with nothing said to be partial", {"date": "d", "basis": "partial"}),
        ("verified carrying unconfirmed axes",
         {"date": "d", "basis": "verified", "unconfirmed_axes": ["adoption"]}),
        ("verified carrying a hold",
         {"date": "d", "basis": "verified", "verification_holds": [HOLD]}),
        ("an axis name that is not an axis",
         {"date": "d", "basis": "partial", "unconfirmed_axes": ["adoptionn"]}),
        ("the same axis twice",
         {"date": "d", "basis": "partial", "unconfirmed_axes": ["adoption", "adoption"]}),
        ("an empty unconfirmed list",
         {"date": "d", "basis": "partial", "unconfirmed_axes": []}),
        ("a hold on an axis that is confirmed",
         {"date": "d", "basis": "partial", "unconfirmed_axes": ["openness"],
          "verification_holds": [HOLD]}),
        ("a hold with no reason",
         {"date": "d", "basis": "partial", "unconfirmed_axes": ["adoption"],
          "verification_holds": [{**HOLD, "reason": "   "}]}),
        ("a hold with an unparseable since",
         {"date": "d", "basis": "partial", "unconfirmed_axes": ["adoption"],
          "verification_holds": [{**HOLD, "since": "soon"}]}),
    ],
)
def test_malformed_caveats_are_rejected(name, record):
    with pytest.raises(PayloadError):
        _check_freshness_caveats("widget", record)


@pytest.mark.parametrize(
    "name, record",
    [
        ("plain verified", {"date": "d", "basis": "verified"}),
        ("partial with a hold",
         {"date": "d", "basis": "partial", "unconfirmed_axes": ["adoption"],
          "verification_holds": [HOLD]}),
        # An undated axis is unconfirmed whether or not the queue explains it. A hold
        # explains an unconfirmed axis; its absence does not make one confirmed.
        ("partial with no queue entry",
         {"date": "d", "basis": "partial", "unconfirmed_axes": ["adoption"]}),
        ("commit carrying its holds",
         {"date": "d", "basis": "commit",
          "unconfirmed_axes": ["adoption", "capability", "openness"],
          "verification_holds": [HOLD]}),
    ],
)
def test_valid_caveats_pass(name, record):
    _check_freshness_caveats("widget", record)
