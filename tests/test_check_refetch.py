"""Tests for the sampled re-fetch.

The two that matter are `test_a_member_whose_file_never_changed_is_still_fabrication` and
`test_rate_limit_is_not_reported_dead`.

The first is the gate's whole reason to exist: the invariant and the digest requirement read
what the writer wrote, so the only thing that catches an invented digest is noticing it could
not have come from a body. A real digest recorded against a file that has not changed since
before the access, and serves something else, is that. A shared digest alone is not, and
neither is a member that changed after it was read
(`test_a_relicensed_member_of_a_shared_license_digest_is_drift`).

The second pins a bug the first real run produced. The sampled re-fetch reported a live
Mastra LICENSE as dead because GitHub answered 429, and a gate that reports rate limiting as
a dead source is a gate people learn to ignore. Transient statuses must stay out of the
findings bucket.
"""

import hashlib
from datetime import date
from unittest.mock import Mock, patch

import pytest
import requests

from build.check_refetch import Source, canonical, http_get, offline_failures, refetch
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


class _Resp:
    def __init__(self, body: bytes):
        self.content, self.status_code = body, 200


def _serve(monkeypatch, bodies: dict[str, bytes]):
    import build.check_refetch as mod

    monkeypatch.setattr(mod.requests, "get", lambda url, **kw: _Resp(bodies[url]))
    return mod


def test_identical_bodies_clear_the_group(monkeypatch):
    mod = _serve(monkeypatch, {"https://a.example/x": b"same", "https://b.example/y": b"same"})
    failures, benign = mod.resolve_duplicates(
        [(DIGEST_A, ["https://a.example/x", "https://b.example/y"])], 5.0
    )
    assert failures == [] and len(benign) == 1
    assert "really are identical" in benign[0]


def test_differing_bodies_without_history_are_drift_not_fabrication(monkeypatch):
    """The second heuristic this module retired: "bodies differ today, so one was never read."

    Two bodies fetched now say nothing about what either URL served on its access date. With
    no change history to consult, a member that differs is drift like any other.
    """
    apache = b"Apache License 2.0 text"
    digest = hashlib.sha256(apache).hexdigest()
    mod = _serve(monkeypatch, {"https://a.example/x": apache, "https://b.example/y": b"different"})
    failures, benign = mod.resolve_duplicates(
        [(digest, ["https://a.example/x", "https://b.example/y"])],
        5.0,
        accessed={(digest, "https://b.example/y"): date(2026, 8, 18)},
        last_changed=lambda url: None,
    )
    assert failures == []
    assert len(benign) == 1 and "Drift, not fabrication" in benign[0]
    assert "no change history" in benign[0]


LICENSE_URLS = [
    "https://raw.githubusercontent.com/huggingface/peft/main/LICENSE",
    "https://raw.githubusercontent.com/vllm-project/vllm/main/LICENSE",
    "https://github.com/treeverse/lakeFS/blob/master/LICENSE",
]
LAKEFS_RAW = "https://raw.githubusercontent.com/treeverse/lakeFS/master/LICENSE"
APACHE = b"                                 Apache License\n  Version 2.0, January 2004\n"
BSL = b"Business Source License 1.1\n"


def _license_group(monkeypatch, lakefs_last_changed: date):
    """The #692 shape: one Apache-2.0 digest on three LICENSE URLs, lakeFS now serving BSL."""
    digest = hashlib.sha256(APACHE).hexdigest()
    bodies = {canonical(u): APACHE for u in LICENSE_URLS}
    bodies[LAKEFS_RAW] = BSL
    mod = _serve(monkeypatch, bodies)
    asked = []

    def last_changed(url):
        asked.append(url)
        return lakefs_last_changed

    failures, benign = mod.resolve_duplicates(
        [(digest, sorted(LICENSE_URLS))],
        5.0,
        accessed={(digest, u): date(2026, 8, 18) for u in LICENSE_URLS},
        last_changed=last_changed,
    )
    return failures, benign, asked


def test_a_relicensed_member_of_a_shared_license_digest_is_drift(monkeypatch):
    """#692: lakeFS relicensed to BSL-1.1 on 2026-09-22, after its 2026-08-18 read.

    The other members still reproduce the Apache-2.0 digest, so the digest is real, and the
    lakeFS file changed after it was read. That is ordinary drift. The old resolver called it
    "FABRICATION — no innocent reading" and failed the weekly run.
    """
    failures, benign, asked = _license_group(monkeypatch, date(2026, 9, 22))
    assert failures == []
    assert asked == ["https://github.com/treeverse/lakeFS/blob/master/LICENSE"], (
        "history is looked up only for the member that changed"
    )
    assert len(benign) == 1
    assert "treeverse/lakeFS" in benign[0] and "2 of 3 URLs" in benign[0]
    assert "changed on 2026-09-22, after the recorded access on 2026-08-18" in benign[0]


def test_a_member_whose_file_never_changed_is_still_fabrication(monkeypatch):
    """The case the class exists for, kept intact.

    Same group, but the lakeFS LICENSE was last touched in 2020. It served the BSL body on
    2026-08-18 too, so the Apache-2.0 digest recorded against it could only have been copied
    from one of the other members.
    """
    failures, benign, _asked = _license_group(monkeypatch, date(2020, 8, 2))
    assert len(failures) == 1 and benign == []
    assert "treeverse/lakeFS" in failures[0]
    assert "has not changed since 2020-08-02" in failures[0]
    assert "copied" in failures[0]


def test_a_change_inside_the_commit_date_slack_is_not_called_fabrication(monkeypatch):
    """A committer date can predate the push, so a change close to the access is drift."""
    failures, benign, _asked = _license_group(monkeypatch, date(2026, 8, 14))
    assert failures == []
    assert "too close to rule out" in benign[0]


def test_an_unproven_digest_is_never_called_fabrication(monkeypatch):
    """If no member reproduces the digest, it is not shown to be a real body at all.

    It could be a digest of a fetch mode this module no longer uses (a rendered blob page,
    say), so an unchanged file serving something else proves nothing about copying. The
    history is not even consulted.
    """
    mod = _serve(monkeypatch, {"https://a.example/x": b"one", "https://b.example/y": b"two"})
    asked = []
    failures, benign = mod.resolve_duplicates(
        [(DIGEST_A, ["https://a.example/x", "https://b.example/y"])],
        5.0,
        accessed={(DIGEST_A, "https://a.example/x"): date(2026, 8, 18),
                  (DIGEST_A, "https://b.example/y"): date(2026, 8, 18)},
        last_changed=lambda url: asked.append(url) or date(2020, 1, 1),
    )
    assert failures == [] and asked == []
    assert len(benign) == 2 and all("every member has drifted" in b for b in benign)


def test_latest_access_keeps_the_most_recent_claim():
    from build.check_refetch import latest_access

    old = Source("p", "openness", "https://a.example/x", DIGEST_A, 200, "2026-07-01")
    new = Source("q", "openness", "https://a.example/x", DIGEST_A, 200, date(2026, 8, 18))
    assert latest_access([old, new]) == {(DIGEST_A, "https://a.example/x"): date(2026, 8, 18)}


def test_github_last_changed_reads_the_commit_history(monkeypatch):
    import build.check_refetch as mod

    seen = {}

    class Api:
        status_code = 200

        def json(self):
            return [{"commit": {"committer": {"date": "2026-09-22T13:49:51Z"}}}]

    def get(url, params=None, **kw):
        seen["url"], seen["params"] = url, params
        return Api()

    monkeypatch.setattr(mod.requests, "get", get)
    assert mod.github_last_changed(LICENSE_URLS[2]) == date(2026, 9, 22)
    assert seen["url"] == "https://api.github.com/repos/treeverse/lakeFS/commits"
    assert seen["params"] == {"path": "LICENSE", "sha": "master", "per_page": 1}

    assert mod.github_last_changed("https://example.com/LICENSE") is None
    Api.status_code = 403  # a rate limit is "no history", never evidence
    assert mod.github_last_changed(LICENSE_URLS[2]) is None


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
        assert refetch(source, 5.0, sleep=lambda _: None)[0] == "confirmed"


def test_changed_body_is_drift_not_failure():
    source = src("https://a.example/x", DIGEST_A)
    with patch("build.check_refetch.requests.get", return_value=_response(200, b"new")):
        assert refetch(source, 5.0, sleep=lambda _: None)[0] == "drifted"


@pytest.mark.parametrize("status", [429, 500, 502, 503])
def test_rate_limit_is_not_reported_dead(status: int):
    """429 and 5xx are 'not now', not 'not here'. Reported as unreachable, never as a finding."""
    source = src("https://a.example/x", DIGEST_A)
    with patch("build.check_refetch.requests.get", return_value=_response(status)):
        outcome, detail = refetch(source, 5.0, sleep=lambda _: None)
    assert outcome == "unreachable"
    assert "transient" in detail


@pytest.mark.parametrize("status", [401, 403, 404, 410])
def test_client_errors_are_dead(status: int):
    source = src("https://a.example/x", DIGEST_A)
    with patch("build.check_refetch.requests.get", return_value=_response(status)):
        assert refetch(source, 5.0, sleep=lambda _: None)[0] == "gone"


def test_network_error_is_unreachable_not_dead():
    source = src("https://a.example/x", DIGEST_A)
    with patch(
        "build.check_refetch.requests.get", side_effect=requests.Timeout("timed out")
    ):
        assert refetch(source, 5.0, sleep=lambda _: None)[0] == "unreachable"


# --- GitHub authentication --------------------------------------------------------------
# A 150-product weekly re-verify against GitHub-hosted sources burns through the anonymous
# 60/hour limit fast; `Authorization` fixes that without changing what bytes come back, so
# it is scoped to GitHub's own hosts and only sent when GITHUB_TOKEN is actually set.

def test_github_host_gets_authorization_when_token_is_set(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "secret-token")
    with patch("build.check_refetch.requests.get", return_value=_response(200)) as get:
        http_get("https://raw.githubusercontent.com/org/repo/main/LICENSE", timeout=5.0)
    assert get.call_args.kwargs["headers"]["Authorization"] == "Bearer secret-token"


def test_non_github_host_gets_no_authorization_even_with_token_set(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "secret-token")
    with patch("build.check_refetch.requests.get", return_value=_response(200)) as get:
        http_get("https://example.com/page", timeout=5.0)
    assert "Authorization" not in get.call_args.kwargs["headers"]


def test_github_host_gets_no_authorization_when_token_is_unset(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    with patch("build.check_refetch.requests.get", return_value=_response(200)) as get:
        http_get("https://raw.githubusercontent.com/org/repo/main/LICENSE", timeout=5.0)
    assert "Authorization" not in get.call_args.kwargs["headers"]


# --- The 403 encoding retry ----------------------------------------------------------
# Some hosts fingerprint urllib3's default `Accept-Encoding: gzip, deflate` and answer 403
# to it while serving any explicit single value. Measured against Huawei Cloud on
# 2026-09-17: 403 at 462 bytes on the default, 200 at 77,230 bytes with `Accept-Encoding:
# gzip`. The retry is scoped to a 403 so that no page which is already fetchable changes
# its bytes - a corpus-wide header pin was measured to re-digest 1 of 16 otherwise stable
# pages, which is why this is a retry and not a default.

def test_403_is_retried_once_with_an_explicit_encoding():
    responses = [_response(403), _response(200)]
    with patch("build.check_refetch.requests.get", side_effect=responses) as get:
        response = http_get("https://fingerprints.example/doc", timeout=5.0, sleep=lambda _: None)
    assert response.status_code == 200
    assert get.call_count == 2
    assert "Accept-Encoding" not in get.call_args_list[0].kwargs["headers"]
    assert get.call_args_list[1].kwargs["headers"]["Accept-Encoding"] == "gzip"
    assert response.encoding_retry is True


def test_a_200_never_sets_accept_encoding():
    """The default path is unchanged, which is what keeps every recorded digest valid."""
    with patch("build.check_refetch.requests.get", return_value=_response(200)) as get:
        http_get("https://a.example/x", timeout=5.0)
    assert get.call_count == 1
    assert "Accept-Encoding" not in get.call_args.kwargs["headers"]


def test_a_real_403_stays_a_403_and_the_encoding_is_tried_only_once():
    """A page that is genuinely forbidden answers 403 to both headers, and the finding survives.

    403 is also in TRANSIENT - openai.com lets roughly one request in eight through - so the
    backoff loop still runs after the encoding retry. What this pins is that the explicit
    header is tried exactly once rather than on every attempt.
    """
    with patch("build.check_refetch.requests.get", return_value=_response(403)) as get:
        response = http_get("https://forbidden.example/x", timeout=5.0, sleep=lambda _: None)
    assert response.status_code == 403
    encoded = [c for c in get.call_args_list if "Accept-Encoding" in c.kwargs["headers"]]
    assert len(encoded) == 1


def test_a_transient_from_the_retry_falls_through_to_the_backoff():
    """A gzip-path 503 is still "not now", so it must not skip the retries it deserves.

    The first draft returned any non-403 from the retry immediately, which spent the
    fingerprint check and then handed back a 503 that had never been retried once.
    """
    responses = [_response(403), _response(503), _response(200)]
    slept: list[float] = []
    with patch("build.check_refetch.requests.get", side_effect=responses) as get:
        response = http_get("https://flaky.example/x", timeout=5.0, sleep=slept.append)
    assert response.status_code == 200
    assert get.call_count == 3
    assert slept, "the transient path must back off rather than retry immediately"


def test_the_encoding_retry_is_tried_before_any_backoff():
    """Ordering matters: a fingerprint answers 403 to every attempt, so asking three times
    first costs six requests and two sleeps to learn nothing."""
    slept: list[float] = []
    with patch("build.check_refetch.requests.get", side_effect=[_response(403), _response(200)]) as get:
        http_get("https://fingerprints.example/doc", timeout=5.0, sleep=slept.append)
    assert get.call_count == 2
    assert slept == [], "no sleep should happen before the encoding retry"


def test_a_failed_encoding_retry_leaves_the_403_standing():
    def _get(*_args, **kwargs):
        if kwargs["headers"].get("Accept-Encoding"):
            raise requests.Timeout("timed out on the retry")
        return _response(403)

    with patch("build.check_refetch.requests.get", side_effect=_get):
        assert http_get("https://x.example/y", timeout=5.0, sleep=lambda _: None).status_code == 403


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
        outcome, detail = refetch(source, 5.0, sleep=lambda _: None)
    assert outcome == "unreachable"
    assert "bot wall" in detail


def test_a_wall_whose_digest_matches_is_never_confirmed():
    """The one case that must not read as CONFIRMED.

    A matching digest is this gate's only piece of positive evidence, and certifying a
    source whose recorded bytes are a challenge page would turn that evidence into a lie.
    """
    source = src("https://a.example/x", hashlib.sha256(WALL).hexdigest())
    with patch("build.check_refetch.requests.get", return_value=_response(200, WALL)):
        outcome, detail = refetch(source, 5.0, sleep=lambda _: None)
    assert outcome != "confirmed"
    assert "never read" in detail


def test_load_sources_walks_the_comparison_attestation(tmp_path, monkeypatch):
    """A comparison attestation cites the ROOT, so it is exactly the kind of claim that
    benefits from a weekly re-fetch. It sits outside `capability.sources` deliberately, which
    means the walker has to be told about it or it re-checks nothing."""
    import build.check_refetch as mod

    folder = tmp_path / "sources" / "scores"
    folder.mkdir(parents=True)
    (folder / "a.yaml").write_text(
        "product: a\n"
        "capability:\n"
        "  score: 4\n"
        "  basis: feature_matrix\n"
        "  relative_to: b\n"
        "  relation: one_below\n"
        "  sources:\n"
        "    - url: https://example.com/a\n"
        "      shows: what a does\n"
        "      accessed: 2026-08-31\n"
        f"      content_sha256: {DIGEST_A}\n"
        "  comparison:\n"
        "    last_attested: 2026-08-31\n"
        "    sources:\n"
        "      - url: https://example.com/b\n"
        "        shows: what b still does\n"
        "        accessed: 2026-08-31\n"
        f"        content_sha256: {DIGEST_B}\n"
    )
    monkeypatch.setattr(mod, "ROOT", tmp_path)

    found = {(s.axis, s.url, s.digest) for s in mod.load_sources()}
    assert found == {
        ("capability", "https://example.com/a", DIGEST_A),
        ("capability.comparison", "https://example.com/b", DIGEST_B),
    }
