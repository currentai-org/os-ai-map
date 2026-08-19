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
from build.check_refetch import bot_wall as pr_bot_wall

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


def test_a_reused_digest_is_a_question_for_the_resolver_not_an_offline_failure():
    """Changed 2026-08-13, after the old rule failed `main` on facts about the internet.

    It read: a digest on two URLs means at least one was never fetched. Both of its
    counterexamples are ordinary, and the corpus has plenty of each.

    - **Canonical texts.** Five repos shared one digest for their Apache-2.0 LICENSE.
      Re-fetching all five reproduced it exactly over an identical 11,357-byte body. A
      standard license IS the same bytes everywhere; a repo that changed the text would no
      longer be under that license.
    - **Host aliases.** `docs.developer.apple.com/…/coreml.md` 301s to
      `developer.apple.com/…/coreml.md`. Two URLs, one document, no paste.

    So the offline pass no longer decides it. `resolve_duplicates` fetches the group and
    lets the bytes answer, which is what the old message's own wording invited — "it means
    at least one was not fetched" is falsifiable, so falsify it.
    """
    sources = [src("https://a.example/x", DIGEST_A), src("https://b.example/y", DIGEST_A)]
    assert offline_failures(sources) == []

    from build.check_refetch import duplicate_digest_groups

    groups = duplicate_digest_groups(sources)
    assert groups == [(DIGEST_A, ["https://a.example/x", "https://b.example/y"])]


def test_the_resolver_fails_only_when_the_bodies_actually_differ(monkeypatch):
    """The claim is tested, and it still fails when it should.

    Identical bodies clear the group; differing bodies are fabrication with no innocent
    reading left, because no honest fetch of two different documents yields one digest.
    """
    import build.check_refetch as mod

    class Resp:
        def __init__(self, body): self.content, self.status_code = body, 200

    bodies = {"https://a.example/x": b"same", "https://b.example/y": b"same"}
    monkeypatch.setattr(mod.requests, "get", lambda url, **kw: Resp(bodies[url]))
    failures, benign = mod.resolve_duplicates(
        [(DIGEST_A, ["https://a.example/x", "https://b.example/y"])], 5.0
    )
    assert failures == [] and len(benign) == 1
    assert "really are identical" in benign[0]

    bodies["https://b.example/y"] = b"different"
    failures, _benign = mod.resolve_duplicates(
        [(DIGEST_A, ["https://a.example/x", "https://b.example/y"])], 5.0
    )
    assert len(failures) == 1
    assert "DIFFERENT bodies" in failures[0]


def test_the_resolver_fetches_through_canonical_like_every_other_fetch():
    """A blob URL and its raw form are one document, and comparing them is comparing two.

    The first draft of the resolver fetched `source.url` directly and reported `maple-ai`
    as fabrication: its digests were of the RAW bodies, correctly, while the resolver was
    hashing the rendered blob page. `fetch_source` warns about exactly this — a digest taken
    one way and re-checked another "differs for reasons that have nothing to do with whether
    anybody read the page." So `canonical` now lives beside USER_AGENT here, and both
    modules go through it.
    """
    from build import fetch_source
    from build.check_refetch import canonical

    assert fetch_source.canonical is canonical, "the two fetch paths can diverge again"
    assert canonical("https://github.com/o/r/blob/main/LICENSE") == (
        "https://raw.githubusercontent.com/o/r/main/LICENSE"
    )
    assert canonical("https://example.com/x") == "https://example.com/x"


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


# --- Bot walls -------------------------------------------------------------------------
# A wall answers 200 and hands back a page that is not the document, so neither the
# TRANSIENT branch nor the >=400 branch sees it. On 2026-08-13 two PyPI sources were
# digested from one, recorded the same digest because the wall is byte-identical whatever
# you ask for, and the duplicate resolver called it fabrication. Nobody forged anything.

WALL = (
    b"<html><head><title>Client Challenge</title></head>"
    b"<body>JavaScript is disabled in your browser</body></html>"
)


def test_a_wall_is_recognised_by_marker_and_size():
    assert "Client Challenge" in (pr_bot_wall(_response(200, WALL)) or "")


def test_a_real_page_quoting_the_marker_is_not_a_wall():
    """The size bound is what stops a docs page ABOUT bot protection being discarded.

    Without it this check would silently drop legitimate evidence, which is a worse
    failure than the one it is here to prevent.
    """
    big = WALL + b"x" * 30_000
    assert pr_bot_wall(_response(200, big)) is None


def test_a_walled_refetch_is_unreachable_not_drift():
    """DRIFTED would assert the document changed. The host just declined to serve it."""
    source = src("https://a.example/x", DIGEST_A)
    with patch("build.check_refetch.requests.get", return_value=_response(200, WALL)):
        outcome, detail = refetch(source, 5.0)
    assert outcome == "unreachable"
    assert "bot wall" in detail


def test_a_wall_whose_digest_matches_is_never_confirmed():
    """The one case that must not read as CONFIRMED.

    A matching digest is this gate's only piece of positive evidence, and certifying a
    source whose recorded bytes are a challenge page would turn that evidence into a lie.
    """
    source = src("https://a.example/x", hashlib.sha256(WALL).hexdigest())
    with patch("build.check_refetch.requests.get", return_value=_response(200, WALL)):
        outcome, detail = refetch(source, 5.0)
    assert outcome != "confirmed"
    assert "never read" in detail
