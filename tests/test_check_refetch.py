"""Tests for the sampled re-fetch.

The two that matter are `test_reused_digest_across_urls_is_fabrication` and
`test_rate_limit_is_not_reported_dead`.

The first is the gate's whole reason to exist: the invariant and the digest requirement read
what the writer wrote, so the only thing that catches an invented digest is noticing it could
not have come from a body. Two URLs sharing sixty-four characters is the cheapest form of
that.

The second pins a bug the first real run produced. The sampled re-fetch reported a live
Mastra LICENSE as dead because GitHub answered 429, and a gate that reports rate limiting as
a dead source is a gate people learn to ignore. Transient statuses must stay out of the
findings bucket.
"""

import hashlib
from unittest.mock import Mock, patch

import pytest
import requests

from build.check_refetch import Source, offline_failures, refetch

DIGEST_A = "a" * 64
DIGEST_B = "b" * 64


def src(url: str, digest: str, product: str = "p", status: int = 200) -> Source:
    return Source(
        product=product, axis="openness", url=url, digest=digest, status=status,
        accessed="2026-07-30",
    )


def test_clean_sources_have_no_offline_failures():
    sources = [src("https://a.example/x", DIGEST_A), src("https://b.example/y", DIGEST_B)]
    assert offline_failures(sources) == []


def test_reused_digest_across_urls_is_fabrication():
    """The same digest on two different URLs means at least one was never fetched."""
    sources = [src("https://a.example/x", DIGEST_A), src("https://b.example/y", DIGEST_A)]
    problems = offline_failures(sources)
    assert len(problems) == 1
    assert "2 different URLs" in problems[0]


def test_same_digest_on_the_same_url_twice_is_fine():
    """Two axes citing one page legitimately share its digest — that is not a collision."""
    sources = [
        src("https://a.example/x", DIGEST_A, product="one"),
        src("https://a.example/x", DIGEST_A, product="two"),
    ]
    assert offline_failures(sources) == []


@pytest.mark.parametrize("bad", ["", "abc", "z" * 64, "A" * 64, "a" * 63, "a" * 65])
def test_malformed_digest_is_rejected(bad: str):
    problems = offline_failures([src("https://a.example/x", bad)])
    assert len(problems) == 1
    assert "not a SHA-256" in problems[0]


def _response(status: int, body: bytes = b"") -> Mock:
    return Mock(status_code=status, content=body)


def test_matching_digest_is_confirmed():
    body = b"stable content"
    source = src("https://a.example/x", hashlib.sha256(body).hexdigest())
    with patch("build.check_refetch.requests.get", return_value=_response(200, body)):
        assert refetch(source, 5.0)[0] == "confirmed"


def test_changed_body_is_drift_not_failure():
    source = src("https://a.example/x", DIGEST_A)
    with patch("build.check_refetch.requests.get", return_value=_response(200, b"new")):
        assert refetch(source, 5.0)[0] == "drifted"


@pytest.mark.parametrize("status", [429, 500, 502, 503])
def test_rate_limit_is_not_reported_dead(status: int):
    """429 and 5xx are 'not now', not 'not here'. Reported as unreachable, never as a finding."""
    source = src("https://a.example/x", DIGEST_A)
    with patch("build.check_refetch.requests.get", return_value=_response(status)):
        outcome, detail = refetch(source, 5.0)
    assert outcome == "unreachable"
    assert "transient" in detail


@pytest.mark.parametrize("status", [401, 403, 404, 410])
def test_client_errors_are_dead(status: int):
    source = src("https://a.example/x", DIGEST_A)
    with patch("build.check_refetch.requests.get", return_value=_response(status)):
        assert refetch(source, 5.0)[0] == "gone"


def test_network_error_is_unreachable_not_dead():
    source = src("https://a.example/x", DIGEST_A)
    with patch(
        "build.check_refetch.requests.get", side_effect=requests.Timeout("timed out")
    ):
        assert refetch(source, 5.0)[0] == "unreachable"
