"""Tests for the sampled re-fetch.

The two that matter are `test_a_miss_is_a_suspected_copy_never_a_failure` and
`test_rate_limit_is_not_reported_dead`.

The first pins what the gate does with a shared digest it cannot account for: it looks for a
revision of the file that hashes to the recorded digest, clears the member as drift when it
finds one (`test_a_relicensed_member_whose_tip_served_the_digest_is_drift`, the #692 lakeFS
case), and otherwise raises a suspected copy for a human. It never fails on it, because every
rule that did was wrong and a miss cannot be told apart from an incomplete history.

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
    digest = hashlib.sha256(b"same").hexdigest()
    mod = _serve(monkeypatch, {"https://a.example/x": b"same", "https://b.example/y": b"same"})
    failures, benign, suspected = mod.resolve_duplicates(
        [(digest, ["https://a.example/x", "https://b.example/y"])], 5.0,
        history=lambda *a: pytest.fail("a group that reproduces looks up no history"),
    )
    assert failures == [] and suspected == [] and len(benign) == 1
    assert "really are identical" in benign[0]


APACHE = b"                                 Apache License\n  Version 2.0, January 2004\n"
BSL = b"Business Source License 1.1\n"
APACHE_DIGEST = hashlib.sha256(APACHE).hexdigest()
LICENSE_URLS = [
    "https://raw.githubusercontent.com/huggingface/peft/main/LICENSE",
    "https://raw.githubusercontent.com/vllm-project/vllm/main/LICENSE",
    "https://github.com/treeverse/lakeFS/blob/master/LICENSE",
]
LAKEFS_RAW = "https://raw.githubusercontent.com/treeverse/lakeFS/master/LICENSE"
ACCESSED = {date(2026, 8, 18)}
T0, T1, T2, T3 = "0" * 39 + "1", "1" * 40, "2" * 40, "3" * 40


class _Api:
    def __init__(self, payload=None, status=200, content=b"", links=None):
        self.payload, self.status_code, self.content = payload, status, content
        self.links = links or {}

    def json(self):
        return self.payload


class FakeGitHub:
    """Just enough of GitHub: refs, one branch's activity log, files at SHAs.

    `activity` is (timestamp, before, after), served newest first in pages of `page_size`,
    with a `next` link that carries the query string the way GitHub's does. `files` maps
    (repo, sha) to the file body; any other SHA answers 404.
    """

    def __init__(self, live, heads, tags=(), activity=(), files=None, activity_status=200,
                 page_size=100):
        self.live, self.heads, self.tags, self.activity = live, heads, tags, activity
        self.files, self.activity_status, self.page_size = files or {}, activity_status, page_size
        self.calls: list[tuple[str, dict | None]] = []

    def get(self, url, params=None, **kw):
        self.calls.append((url, params))
        if url in self.live:
            return _Resp(self.live[url])
        if url.startswith("https://api.github.com/repos/"):
            parts = url.split("?")[0].split("/")
            rest = parts[6:]
            if rest[:2] == ["git", "matching-refs"]:
                kind, prefix = rest[2], "/".join(rest[3:])
                names = self.heads if kind == "heads" else self.tags
                return _Api([{"ref": f"refs/{kind}/{n}"} for n in names if n.startswith(prefix)])
            if rest[0] == "activity":
                if self.activity_status != 200:
                    return _Api({"message": "rate limited"}, self.activity_status)
                query = url.split("?")[1] if "?" in url else ""
                page = int(query.split("page=")[1]) if "page=" in query else 0
                rows = sorted(self.activity, reverse=True)
                chunk = rows[page * self.page_size:(page + 1) * self.page_size]
                links = {}
                if len(rows) > (page + 1) * self.page_size:
                    links = {"next": {"url": f"{url.split('?')[0]}?ref=refs%2Fheads%2Fmaster&page={page + 1}"}}
                return _Api([{"timestamp": t, "before": b, "after": a, "activity_type": "push"}
                             for t, b, a in chunk], links=links)
        if url.startswith("https://raw.githubusercontent.com/"):
            parts = url.split("/")
            key = (f"{parts[3]}/{parts[4]}", parts[5])
            if key in self.files:
                return _Resp(self.files[key])
            return _Api(status=404)
        raise AssertionError(f"unexpected fetch {url}")


def _install(monkeypatch, fake):
    import build.check_refetch as mod

    monkeypatch.setattr(mod.requests, "get", fake.get)
    return mod


def _lakefs(monkeypatch, activity, files, **kw):
    """The #692 shape: one Apache-2.0 digest on three LICENSE URLs, lakeFS now serving BSL."""
    live = {canonical(u): APACHE for u in LICENSE_URLS}
    live[LAKEFS_RAW] = BSL
    fake = FakeGitHub(live, heads=["master"], activity=activity,
                      files={("treeverse/lakeFS", k): v for k, v in files.items()}, **kw)
    mod = _install(monkeypatch, fake)
    result = mod.resolve_duplicates(
        [(APACHE_DIGEST, sorted(LICENSE_URLS))], 5.0,
        accessed={(APACHE_DIGEST, u): ACCESSED for u in LICENSE_URLS},
    )
    return (*result, fake)


RELICENSE = [("2026-08-16T07:46:56Z", T0, T1), ("2026-09-22T15:16:16Z", T1, T2)]


def test_a_relicensed_member_whose_tip_served_the_digest_is_drift(monkeypatch):
    """#692: lakeFS relicensed to BSL-1.1 on 2026-09-22, after its 2026-08-18 read. Master was
    at T1 on the access date and T1's LICENSE is Apache-2.0, so the URL served the digest."""
    failures, benign, suspected, fake = _lakefs(monkeypatch, RELICENSE, {T1: APACHE, T2: BSL})
    assert failures == [] and suspected == []
    assert len(benign) == 1 and "treeverse/lakeFS" in benign[0] and "2 of 3 URLs" in benign[0]
    assert "Drift" in benign[0] and f"master was at {T1[:10]}" in benign[0]
    assert not any("peft" in u and "api.github.com" in u for u, _ in fake.calls), (
        "only the changed member is looked up"
    )


def test_a_miss_is_a_suspected_copy_never_a_failure(monkeypatch):
    """No tip around the access serves the digest. That is what a copy looks like, and also
    what an incomplete log looks like, so a human confirms it; the gate does not fail."""
    failures, benign, suspected, _fake = _lakefs(monkeypatch, RELICENSE, {T1: BSL, T2: BSL})
    assert failures == [] and benign == []
    assert len(suspected) == 1 and "treeverse/lakeFS" in suspected[0]
    assert "Confirm by hand" in suspected[0] and "does not guarantee" in suspected[0]


def test_main_exits_zero_on_a_suspected_copy_and_raises_a_workflow_warning(monkeypatch, capsys):
    import build.check_refetch as mod

    monkeypatch.setattr(mod, "load_sources", lambda product=None: [src(LAKEFS_RAW, APACHE_DIGEST)])
    monkeypatch.setattr(mod, "resolve_duplicates", lambda *a, **k: ([], [], ["suspected line"]))
    monkeypatch.setattr(mod, "refetch", lambda source, timeout: ("drifted", "changed"))
    monkeypatch.setattr("sys.argv", ["check_refetch"])
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert mod.main() == 0
    out = capsys.readouterr().out
    assert "SUSPECTED COPIES" in out
    assert "::warning title=refetch: suspected copied digest::suspected line" in out


def test_neither_member_reproducing_is_two_suspected_copies_not_failures(monkeypatch):
    """Codex finding 1 on #699: a digest pasted onto two URLs, neither reproducing it."""
    urls = ["https://raw.githubusercontent.com/o/one/main/LICENSE",
            "https://raw.githubusercontent.com/o/two/main/LICENSE"]
    fake = FakeGitHub({urls[0]: b"one", urls[1]: b"two"}, heads=["main"],
                      activity=[("2026-06-01T00:00:00Z", T0, T1)],
                      files={("o/one", T1): b"one", ("o/two", T1): b"two"})
    mod = _install(monkeypatch, fake)
    failures, benign, suspected = mod.resolve_duplicates(
        [("f" * 64, urls)], 5.0, accessed={("f" * 64, u): ACCESSED for u in urls}
    )
    assert failures == [] and benign == [] and len(suspected) == 2


def test_a_late_merged_commit_is_judged_by_the_tip_not_its_date(monkeypatch):
    """Codex finding 2 on #699: a merge the day after the access brings in PR commits dated
    weeks earlier. The tip entering the window still served Apache, so it is drift."""
    activity = [("2026-08-01T00:00:00Z", T0, T1), ("2026-08-19T09:00:00Z", T1, T2)]
    failures, benign, suspected, _fake = _lakefs(monkeypatch, activity, {T1: APACHE, T2: BSL})
    assert failures == [] and suspected == [] and "Drift" in benign[0]


def test_a_force_push_does_not_hide_the_tip_that_was_served(monkeypatch):
    activity = [("2026-08-01T00:00:00Z", T0, T1), ("2026-09-01T00:00:00Z", T1, T3)]
    failures, benign, suspected, _fake = _lakefs(monkeypatch, activity, {T1: APACHE, T3: BSL})
    assert failures == [] and suspected == [] and "Drift" in benign[0]


def test_an_inaccessible_tip_does_not_stop_the_search(monkeypatch):
    """The first tip (by sort order) is gone; a later tip in the window matches. Drift."""
    activity = [("2026-08-01T00:00:00Z", T0, T1), ("2026-08-18T12:00:00Z", T1, T2)]
    failures, benign, suspected, _fake = _lakefs(monkeypatch, activity, {T2: APACHE})
    assert sorted([T1, T2])[0] == T1, "T1 is checked first and answers 404"
    assert failures == [] and suspected == [] and "Drift" in benign[0]


def test_an_inaccessible_tip_with_no_match_is_unresolved_not_suspected(monkeypatch):
    activity = [("2026-08-01T00:00:00Z", T0, T1), ("2026-08-18T12:00:00Z", T1, T2)]
    failures, benign, suspected, _fake = _lakefs(monkeypatch, activity, {T2: BSL})
    assert failures == [] and suspected == []
    assert "Unresolved: no checked tip matches, and 1 of 2 could not be fetched" in benign[0]


def test_an_empty_activity_log_is_unresolved(monkeypatch):
    """No tip is known, and today's head is not substituted for the one at access time."""
    failures, benign, suspected, _fake = _lakefs(monkeypatch, [], {})
    assert failures == [] and suspected == []
    assert "Unresolved: the activity log shows no tip" in benign[0]


@pytest.mark.parametrize("status", [403, 429, 500])
def test_an_unavailable_activity_log_is_unresolved(monkeypatch, status):
    failures, benign, suspected, _fake = _lakefs(monkeypatch, RELICENSE, {T1: BSL}, activity_status=status)
    assert failures == [] and suspected == []
    assert f"Unresolved: the activity lookup failed (HTTP {status})" in benign[0]


def test_pagination_follows_next_links_with_the_ref_filter_kept(monkeypatch):
    """Three pages back to the window. The first call passes the ref as a param, and each
    `next` link carries it in its own query string; losing it would read the whole repo."""
    busy = [(f"2026-09-{d:02d}T00:00:00Z", f"{d:040x}", f"{d + 1:040x}") for d in range(1, 26)]
    busy[0] = (busy[0][0], T1, busy[0][2])  # the first update after the access leaves T1
    activity = [("2026-08-01T00:00:00Z", T0, T1)] + busy
    failures, benign, suspected, fake = _lakefs(monkeypatch, activity, {T1: APACHE}, page_size=10)
    assert failures == [] and suspected == [] and "Drift" in benign[0]
    pages = [(u, p) for u, p in fake.calls if "/activity" in u]
    assert len(pages) == 3
    assert all((p or {}).get("ref") == "refs/heads/master" or "ref=refs%2Fheads%2Fmaster" in u
               for u, p in pages)


def test_an_activity_log_past_the_page_cap_is_unresolved(monkeypatch):
    import build.check_refetch as mod

    monkeypatch.setattr(mod, "MAX_ACTIVITY_PAGES", 2)
    busy = [(f"2026-09-{d:02d}T00:00:00Z", f"{d:040x}", f"{d + 1:040x}") for d in range(1, 26)]
    failures, benign, suspected, _fake = _lakefs(monkeypatch, busy, {}, page_size=10)
    assert failures == [] and suspected == [] and "runs past 2 pages" in benign[0]


def test_an_ambiguous_slash_ref_is_unresolved(monkeypatch):
    url = "https://raw.githubusercontent.com/o/r/feature/x/LICENSE"
    mod = _install(monkeypatch, FakeGitHub({url: b"x"}, heads=["feature", "feature/x"]))
    verdict, detail = mod.served_on_access_verdict(url, APACHE_DIGEST, ACCESSED)
    assert verdict == "unresolved" and "exactly one current branch" in detail


def test_a_deleted_branch_shape_never_yields_a_suspected_copy(monkeypatch):
    """Codex finding 2 on a1d23aeb: `feature/x/LICENSE` was branch `feature/x` at access time,
    since deleted, and branch `feature` exists now. The current-refs split lands on `feature`
    and path `x/LICENSE`, which does not match. That miss must not be reported."""
    url = "https://raw.githubusercontent.com/o/r/feature/x/LICENSE"
    fake = FakeGitHub({url: b"x"}, heads=["feature"],
                      activity=[("2026-08-01T00:00:00Z", T0, T1)], files={("o/r", T1): b"other"})
    mod = _install(monkeypatch, fake)
    verdict, detail = mod.served_on_access_verdict(url, APACHE_DIGEST, ACCESSED)
    assert verdict == "unresolved" and "current refs" in detail


def test_an_unambiguous_slash_ref_still_finds_positive_evidence(monkeypatch):
    url = "https://raw.githubusercontent.com/o/r/feature/x/LICENSE"
    fake = FakeGitHub({url: b"x"}, heads=["feature/x", "featurex"],
                      activity=[("2026-08-01T00:00:00Z", T0, T1)], files={("o/r", T1): APACHE})
    mod = _install(monkeypatch, fake)
    verdict, detail = mod.served_on_access_verdict(url, APACHE_DIGEST, ACCESSED)
    assert verdict == "served" and "feature/x was at" in detail


def test_a_tag_ref_is_unresolved(monkeypatch):
    url = "https://raw.githubusercontent.com/o/r/v1.0/LICENSE"
    mod = _install(monkeypatch, FakeGitHub({url: b"x"}, heads=["main"], tags=["v1.0"]))
    verdict, _detail = mod.served_on_access_verdict(url, APACHE_DIGEST, ACCESSED)
    assert verdict == "unresolved"


def test_a_non_github_member_is_unresolved(monkeypatch):
    apache = b"Apache License 2.0 text"
    digest = hashlib.sha256(apache).hexdigest()
    mod = _serve(monkeypatch, {"https://a.example/x": apache, "https://b.example/y": b"different"})
    failures, benign, suspected = mod.resolve_duplicates(
        [(digest, ["https://a.example/x", "https://b.example/y"])], 5.0
    )
    assert failures == [] and suspected == [] and len(benign) == 1
    assert "Unresolved: b.example has no ref history this check can read" in benign[0]


def test_access_dates_keeps_every_claim():
    from build.check_refetch import access_dates

    old = Source("p", "openness", "https://a.example/x", DIGEST_A, 200, "2026-07-01")
    new = Source("q", "openness", "https://a.example/x", DIGEST_A, 200, date(2026, 8, 18))
    assert access_dates([old, new]) == {
        (DIGEST_A, "https://a.example/x"): {date(2026, 7, 1), date(2026, 8, 18)}
    }


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
