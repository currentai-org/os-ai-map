"""Tests for the re-read pass's fetcher.

The one that matters is `test_fetch_and_refetch_agree_on_the_digest`. This module exists only
so that a digest recorded during the re-read is a digest the sampled re-fetch can later
confirm, and the two agree because they are the same request, not because two authors kept
two copies in step. If someone gives this module its own User-Agent or its own requests call,
that test is what should fail.

`test_body_written_is_the_body_hashed` pins the other half. Fetching once to hash and a second
time to save the body would produce a file that does not correspond to the digest recorded
beside it, and a `shows` extract quoted from that file would be evidence for a response nobody
kept.
"""

import hashlib
from unittest.mock import Mock, patch

from build import check_refetch
from build.check_refetch import Source
from build.fetch_source import fetch

BODY = b"Apache License\nVersion 2.0, January 2004\n"


def response(content: bytes = BODY, status: int = 200, url: str = "https://x.example/LICENSE"):
    return Mock(content=content, status_code=status, url=url, headers={"Content-Type": "text/plain"})


def test_records_what_the_schema_requires():
    with patch("build.fetch_source.requests.get", return_value=response()):
        record = fetch("https://x.example/LICENSE")
    assert record["http_status"] == 200
    assert record["content_sha256"] == hashlib.sha256(BODY).hexdigest()
    assert record["bytes"] == len(BODY)


def test_fetch_and_refetch_agree_on_the_digest():
    """A digest this module records is one the sampled re-fetch confirms."""
    with patch("build.fetch_source.requests.get", return_value=response()):
        record = fetch("https://x.example/LICENSE")

    source = Source(
        product="p", axis="openness", url=record["url"], digest=record["content_sha256"],
        status=record["http_status"], accessed="2026-08-08",
    )
    with patch("build.check_refetch.requests.get", return_value=response()):
        outcome, _ = check_refetch.refetch(source, 20.0)
    assert outcome == "confirmed"


def test_user_agent_is_not_a_second_copy():
    """Same string, by import. A private copy here drifts and every digest reads as drift."""
    import build.fetch_source as fetch_source

    assert fetch_source.USER_AGENT is check_refetch.USER_AGENT


def test_body_written_is_the_body_hashed(tmp_path):
    with patch("build.fetch_source.requests.get", return_value=response()) as get:
        record = fetch("https://x.example/LICENSE", body_dir=tmp_path)
    assert get.call_count == 1, "a second request would save a body the digest does not describe"
    written = (tmp_path / record["body_path"].rsplit("/", 1)[-1]).read_bytes()
    assert hashlib.sha256(written).hexdigest() == record["content_sha256"]


def test_a_dead_host_is_a_record_not_a_crash():
    import requests

    with patch("build.fetch_source.requests.get", side_effect=requests.ConnectionError("no route")):
        record = fetch("https://gone.example/x")
    assert record["http_status"] is None
    assert "ConnectionError" in record["error"]
    assert "content_sha256" not in record, "nothing was served, so nothing may be recorded"


def test_a_404_still_reports_its_status():
    """The caller decides a 4xx establishes nothing. The fetcher's job is to report it."""
    with patch("build.fetch_source.requests.get", return_value=response(b"not found", 404)):
        record = fetch("https://x.example/missing")
    assert record["http_status"] == 404
    assert record["content_sha256"] == hashlib.sha256(b"not found").hexdigest()


def test_no_body_is_written_for_a_dead_page(tmp_path):
    with patch("build.fetch_source.requests.get", return_value=response(b"not found", 404)):
        record = fetch("https://x.example/missing", body_dir=tmp_path)
    assert "body_path" not in record
    assert list(tmp_path.iterdir()) == []


def test_a_redirect_is_recorded(tmp_path):
    landed = response(url="https://x.example/final")
    with patch("build.fetch_source.requests.get", return_value=landed):
        record = fetch("https://x.example/start")
    assert record["final_url"] == "https://x.example/final"
    assert record["redirected"] is True


def test_a_rate_limit_is_retried_then_reported_without_a_digest():
    """The pilot's worst defect: one un-retried 429 became the ground for a confirmation."""
    slept = []
    limited = response(b"rate limited", 429)
    with patch("build.fetch_source.requests.get", return_value=limited) as get:
        record = fetch("https://x.example/api", retries=2, sleep=slept.append)
    assert get.call_count == 3, "one attempt is not enough to tell a rate limit from an absence"
    assert record["transient"] is True
    assert "content_sha256" not in record, "a rate-limit page must not be recordable as evidence"
    assert slept == [2.0, 4.0]


def test_a_transient_status_that_clears_is_just_a_fetch():
    limited = response(b"rate limited", 429)
    ok = response()
    with patch("build.fetch_source.requests.get", side_effect=[limited, ok]) as get:
        record = fetch("https://x.example/api", retries=2, sleep=lambda _: None)
    assert get.call_count == 2
    assert record["http_status"] == 200
    assert "transient" not in record
    assert record["content_sha256"] == hashlib.sha256(BODY).hexdigest()


def test_a_404_is_not_transient_and_is_not_retried():
    """A 404 is a finding about the URL. Retrying it just costs time."""
    with patch("build.fetch_source.requests.get", return_value=response(b"nope", 404)) as get:
        record = fetch("https://x.example/missing", retries=2, sleep=lambda _: None)
    assert get.call_count == 1
    assert "transient" not in record
    assert record["http_status"] == 404


def test_a_github_blob_url_is_fetched_raw():
    """A rendered blob embeds a per-request token, so its digest drifts every week."""
    from build.fetch_source import canonical

    assert canonical("https://github.com/huggingface/trl/blob/main/LICENSE") == (
        "https://raw.githubusercontent.com/huggingface/trl/main/LICENSE"
    )
    with patch("build.fetch_source.requests.get", return_value=response()) as get:
        record = fetch("https://github.com/huggingface/trl/blob/main/LICENSE")
    assert get.call_args[0][0] == "https://raw.githubusercontent.com/huggingface/trl/main/LICENSE"
    assert record["rewritten_from"] == "https://github.com/huggingface/trl/blob/main/LICENSE"


def test_a_plain_github_url_is_left_alone():
    from build.fetch_source import canonical

    for url in ("https://github.com/huggingface/trl", "https://pypi.org/project/trl/"):
        assert canonical(url) == url
