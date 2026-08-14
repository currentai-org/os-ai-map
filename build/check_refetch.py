"""The sampled re-fetch: independent evidence that a recorded fetch actually happened.

`docs/guides/verification.md` is normative. This module implements the gate. It is the third
leg of the anti-rubber-stamping defense the runbook names, and until now the only one that
was missing.

## Why the other two are not enough

The invariant asks whether a claimed date is supported by the `accessed` dates on record.
The digest requirement asks whether the sources carry an `http_status` and a
`content_sha256`. Both are real, and both share a blind spot: **they read what the writer
wrote.** An agent that never opened a page can still emit a plausible `accessed`, a plausible
`200`, and sixty-four plausible hex characters, and both gates pass. That is #108's failure
mode with better spelling.

The sampled re-fetch is the only check that goes and looks.

## What a match proves, and what a mismatch does not

Asymmetric, and the asymmetry is the point:

- **A digest that still matches is proof the original fetch was real.** SHA-256 preimages
  are not guessable, so a recorded digest reproducing from a live body could only have come
  from that body. This is positive evidence, and it is the reason to run the gate.
- **A digest that differs proves nothing on its own.** Pages change. `api.github.com/repos/*`
  carries a star count, HF model endpoints carry download counts — those bodies differ
  between any two requests. Treating drift as failure would make the gate noise, and a noisy
  gate gets switched off.

In practice only stable bodies reproduce — the first full run confirmed four sources, three
arXiv `/abs/` pages and one HF `/raw/` CSV, while every API endpoint carrying a star or
download count drifted. That is the expected shape, and it is why the count of confirmations
is the signal rather than the ratio: an agent that fetched nothing would confirm **zero**,
stable URLs included.

So the report separates *confirmed* from *drifted* and never fails on drift. What it does
fail on is the small set of things that admit no innocent reading:

- **A digest reused across two different URLs whose bodies genuinely differ.** The claim is
  tested rather than assumed — see `resolve_duplicates`. The old rule failed on the mere
  fact of a shared digest, reasoning that byte-identical bodies are "possible but rare", and
  that failed `main` on 2026-08-13 against five repos sharing one digest for their Apache-2.0
  LICENSE. A standard license IS the same bytes everywhere; that is what standard means.
  Re-fetching the group settles it either way, and only a real difference is fabrication.
- **A malformed digest.** `validate.py` enforces the schema pattern, so this should be
  unreachable — it is here because a gate that trusts another gate is how both stop working.

Status regressions (recorded `200`, now `404`) are reported as findings rather than
failures: a page can legitimately die between the read and the check. That is still exactly
the signal a re-read pass wants, and it is how the Lucie source that had never resolved as
cited was found — the URL was missing its `/datasets/` segment and the Hub answered 401 to
anyone who tried it.

## Sampling

The re-read surface is ~1,100 URLs and this runs weekly, so it samples. The sample is seeded
and therefore reproducible: the same seed re-checks the same sources, which is what makes a
newly-drifted source visible rather than lost in the shuffle. `--all` re-fetches everything
carrying a digest, which is the right mode after a bulk pass.

Usage:
    uv run python -m build.check_refetch                    # 25 sampled, report only
    uv run python -m build.check_refetch --all              # every source with a digest
    uv run python -m build.check_refetch --product apertus  # one product
    uv run python -m build.check_refetch --strict           # fail on findings too
"""

from __future__ import annotations

import argparse
import hashlib
import random
import re
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
AXES = ("openness", "adoption", "capability")

# A real browser-ish UA. Several vendor docs sites answer 403 to the default python-requests
# string, which would otherwise read as a dead source on every run.
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36 os-ai-map-verification/1.0"
)

# NO Accept / Accept-Language / Sec-Fetch-* here, and that is a finding rather than an
# omission. On 2026-08-14 the full browser header set was measured against every host that
# was blocking a verification pass — hailo.ai, www.demandsage.com, replit.com, openai.com,
# www.qualcomm.com, www.nxp.com — and it moved nothing: 403 stayed 403, the NXP 404 stayed
# 404, and Qualcomm's client-rendered shell merely grew from 8.7KB to 9.1KB of the same
# shell. Adding headers that fix nothing would still re-digest the whole corpus, because a
# body served under a different Accept can differ byte-for-byte, so every recorded digest
# would drift at once. The cost is real and the benefit measured zero.
#
# Accept-Encoding in particular must NEVER be set here. urllib3 advertises only the codecs
# it can decode, and this environment has no brotli; forcing `br` returned a 200 whose
# `.content` was raw compressed bytes. Every digest taken that way would be a digest of
# ciphertext-looking garbage that no re-fetch could reproduce or read.

# Statuses that mean "not now" rather than "not here" — a WAF, a rate limiter or a bad
# gateway, none of which say anything about whether the page exists.
TRANSIENT = {403, 408, 425, 429, 500, 502, 503, 504}

# openai.com sits behind a challenge that lets roughly one request in eight through: eight
# consecutive plain GETs on 2026-08-14 returned 403 403 403 403 403 200 403 403, with no
# header set changing the odds. Three attempts (the old default) clear that about a third of
# the time, which is why `gpt-5` capability kept reading as unfetchable. Six attempts clear
# it about two thirds of the time, and the cost of the extra attempts is paid only by hosts
# that were failing anyway.
RETRIES = 5
BACKOFF = 2.0

# The GitHub blob -> raw rewrite. It lives HERE, beside USER_AGENT, for the reason
# fetch_source's docstring already gives: "this module does not describe how to fetch. It
# imports USER_AGENT and re-uses the same requests call, and a change there changes both
# sides at once." Canonicalization is part of how to fetch, so keeping it in fetch_source
# left this module free to fetch differently — and it did.
#
# A rendered blob page embeds a per-request CSRF token, so its digest differs on every fetch.
# The raw file is the same bytes every time, which is what makes a digest worth recording.
# 86 cited sources are blob URLs; re-fetching them uncanonicalized reported drift forever and
# resolve_duplicates read one as fabrication.
BLOB = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/blob/(.+)$")


def canonical(url: str) -> str:
    """Rewrite a GitHub blob URL to its raw form."""
    match = BLOB.match(url)
    if not match:
        return url
    owner, repo, rest = match.groups()
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{rest}"


def http_get(
    url: str,
    timeout: float = 20.0,
    retries: int = RETRIES,
    backoff: float = BACKOFF,
    sleep=time.sleep,
) -> requests.Response:
    """One canonicalized GET, retrying the statuses that mean "not now".

    This is "how to fetch", and it lives here for the reason USER_AGENT and `canonical` do:
    `build/fetch_source` records a digest and this module re-checks it, and the comparison
    only means something if both sides performed the same operation. Retry policy is part of
    that. Before this existed only fetch_source retried, so an intermittently-challenged host
    could be recorded at 200 by the writer and then reported DEAD by the gate on a single
    unlucky roll — the gate calling a live page dead is exactly the noise its own docstring
    warns kills a gate.

    Raises `requests.RequestException` like a plain `requests.get`; a status is returned, not
    raised on, because a 404 is a finding to record rather than a crash.
    """
    url = canonical(url)
    attempts = 0
    while True:
        attempts += 1
        try:
            response = requests.get(
                url, timeout=timeout, headers={"User-Agent": USER_AGENT}, allow_redirects=True
            )
        except requests.RequestException:
            if attempts <= retries:
                sleep(backoff * attempts)
                continue
            raise
        if response.status_code in TRANSIENT and attempts <= retries:
            sleep(backoff * attempts)
            continue
        response.attempts = attempts  # type: ignore[attr-defined]
        return response



@dataclass(frozen=True)
class Source:
    product: str
    axis: str
    url: str
    digest: str
    status: object
    accessed: object

    @property
    def key(self) -> str:
        return f"{self.product}:{self.axis}"


def load_sources(product: str | None = None) -> list[Source]:
    """Every source across every score file that records a digest."""
    out: list[Source] = []
    for path in sorted((ROOT / "sources" / "scores").glob("*.yaml")):
        if product and path.stem != product:
            continue
        score = yaml.safe_load(path.read_text()) or {}
        for axis in AXES:
            block = score.get(axis) or {}
            if not isinstance(block, dict):
                continue
            for source in block.get("sources") or []:
                if not isinstance(source, dict):
                    continue
                digest = source.get("content_sha256")
                if not digest:
                    continue
                out.append(
                    Source(
                        product=path.stem,
                        axis=axis,
                        url=str(source.get("url") or ""),
                        digest=str(digest),
                        status=source.get("http_status"),
                        accessed=source.get("accessed"),
                    )
                )
    return out


def offline_failures(sources: list[Source]) -> list[str]:
    """Checks that need no network and admit no innocent reading."""
    problems: list[str] = []

    for source in sources:
        if len(source.digest) != 64 or any(c not in "0123456789abcdef" for c in source.digest):
            problems.append(
                f"{source.key}: {source.url!r} records {source.digest!r}, which is not a "
                f"SHA-256. Nothing that fetched a body would produce it."
            )

    return problems


def duplicate_digest_groups(sources: list[Source]) -> list[tuple[str, list[str]]]:
    """Digests recorded against more than one URL, for the resolver below."""
    by_digest: dict[str, set[str]] = defaultdict(set)
    for source in sources:
        by_digest[source.digest].add(source.url)
    return [(d, sorted(u)) for d, u in sorted(by_digest.items()) if len(u) > 1]


def resolve_duplicates(
    groups: list[tuple[str, list[str]]], timeout: float
) -> tuple[list[str], list[str]]:
    """(failures, benign) — decided by fetching, not by guessing.

    THE HEURISTIC THIS REPLACES WAS WRONG, and it failed `main` on 2026-08-13.

    The old rule read: a digest against two URLs is fabrication, because "two distinct pages
    with byte-identical bodies is possible but rare." Both halves of that turned out false in
    the corpus, in two different ways:

    - **Canonical texts.** Five repos — NeMo RL, peft, FastChat, ms-swift, vllm — recorded one
      digest for their LICENSE. Fetching all five live reproduced it exactly over an identical
      11,357-byte body: the unmodified Apache-2.0 text. A standard license IS the same bytes
      everywhere; that is what "standard" means, and a repo that changed it would no longer be
      under that license. Byte-identical is the expected result, not a rare coincidence.
    - **Host aliases.** `docs.developer.apple.com/…/coreml.md` 301s to
      `developer.apple.com/…/coreml.md`. Two URLs, one document. Nothing was pasted; the
      fetcher followed a redirect, which is what it is supposed to do.

    A gate that fails on both of those is not detecting fabrication, it is detecting the
    internet. And a gate whose failures are usually wrong stops being read, which costs more
    than the check was ever worth.

    So the claim is now TESTED rather than assumed. The old message asserted "it means at
    least one was not fetched" — that is a falsifiable statement, so falsify it: fetch every
    URL in the group and compare. If the bodies really are identical, the recorded digest is
    exactly what an honest fetch produces and there is nothing to report. If they differ, at
    least one digest could not have come from its URL, and that is fabrication with no
    innocent reading left.
    """
    failures, benign = [], []
    for digest, urls in groups:
        seen: dict[str, list[str]] = defaultdict(list)
        unreachable = []
        for url in urls:
            try:
                # Through `canonical`, exactly as build/fetch_source does. A GitHub blob URL
                # rewrites to its raw form, and comparing a rendered HTML page against the
                # plain file it points at is comparing two different documents. The first
                # draft of this resolver skipped that and reported `maple-ai` as fabrication:
                # its recorded digests were right all along, and the resolver was reading the
                # blob page. fetch_source's own docstring warns about precisely this —
                # "a digest taken with curl and re-checked with requests differs for reasons
                # that have nothing to do with whether anybody read the page."
                response = http_get(url, timeout=timeout)
            except requests.RequestException:
                unreachable.append(url)
                continue
            if response.status_code >= 400:
                unreachable.append(url)
                continue
            seen[hashlib.sha256(response.content).hexdigest()].append(url)

        listed = ", ".join(urls)
        if len(seen) > 1:
            split = " | ".join(
                f"{d[:12]}…: {', '.join(u)}" for d, u in sorted(seen.items())
            )
            failures.append(
                f"digest {digest[:12]}… is recorded for {len(urls)} URLs ({listed}), and "
                f"re-fetching them returns DIFFERENT bodies ({split}). At least one digest "
                f"could not have come from the URL it is recorded against."
            )
        elif seen:
            live = next(iter(seen))
            note = "" if live == digest else f" (both now hash to {live[:12]}…, so the pair has drifted together)"
            benign.append(
                f"digest {digest[:12]}… is shared by {len(urls)} URLs ({listed}), and "
                f"re-fetching confirms their bodies really are identical{note}."
            )
        if unreachable:
            benign.append(
                f"digest {digest[:12]}…: could not re-fetch {', '.join(unreachable)} this "
                f"run, so the group is unresolved rather than cleared."
            )
    return failures, benign


def refetch(source: Source, timeout: float) -> tuple[str, str]:
    """(outcome, detail). Outcome is one of confirmed / drifted / gone / unreachable."""
    try:
        response = http_get(source.url, timeout=timeout)
    except requests.RequestException as exc:
        return "unreachable", f"{type(exc).__name__}: {exc}"

    # 429 and 5xx are the host saying "not now", not "not here". Calling those dead would
    # make the gate fail on GitHub's rate limiter, which is how a gate earns a reputation
    # for lying. The first run of this module reported a live Mastra LICENSE as dead for
    # exactly that reason.
    #
    # 403 is deliberately NOT in this branch even though `http_get` retries it, and
    # `tests/test_check_refetch.py::test_client_errors_are_dead` pins that. A source that
    # answers 403 to six attempts is one nobody can re-read, which is precisely what a
    # re-read pass needs surfaced loudly rather than filed under "retry later".
    if response.status_code == 429 or response.status_code >= 500:
        return "unreachable", f"HTTP {response.status_code} (transient; retry)"
    if response.status_code >= 400:
        return "gone", f"recorded {source.status}, now HTTP {response.status_code}"

    live = hashlib.sha256(response.content).hexdigest()
    if live == source.digest:
        return "confirmed", ""
    return "drifted", f"body changed since {source.accessed}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", type=int, default=25, help="how many to re-fetch")
    parser.add_argument("--seed", type=int, default=0, help="sample seed; same seed, same set")
    parser.add_argument("--all", action="store_true", help="re-fetch every source with a digest")
    parser.add_argument("--product", help="restrict to one product slug")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="also fail on dead and unreachable sources, not just on fabrication",
    )
    args = parser.parse_args()

    sources = load_sources(args.product)
    if not sources:
        print("0 sources record a digest yet — nothing to re-fetch.")
        print("This is expected until the re-read pass populates content_sha256.")
        return 0

    failures = offline_failures(sources)

    # Duplicate digests are resolved by fetching rather than assumed to be fabrication. See
    # resolve_duplicates: the old heuristic failed main on canonical LICENSE texts and on a
    # host alias, neither of which is anybody pasting anything.
    dup_failures, dup_benign = resolve_duplicates(
        duplicate_digest_groups(sources), args.timeout
    )
    failures.extend(dup_failures)

    chosen = sources
    if not args.all and len(sources) > args.sample:
        chosen = random.Random(args.seed).sample(sources, args.sample)

    buckets: dict[str, list[tuple[Source, str]]] = defaultdict(list)
    for source in sorted(chosen, key=lambda s: (s.product, s.axis, s.url)):
        outcome, detail = refetch(source, args.timeout)
        buckets[outcome].append((source, detail))

    if dup_benign:
        print("\nSHARED DIGESTS — resolved by fetching, not a failure")
        for line in dup_benign:
            print(f"  {line}")

    for outcome, label in (
        ("gone", "DEAD — recorded as reachable, now an error"),
        ("unreachable", "UNREACHABLE — could not be checked this run"),
        ("drifted", "DRIFTED — body changed; re-check queue, not a failure"),
    ):
        if buckets[outcome]:
            print(f"\n{label}")
            for source, detail in buckets[outcome]:
                print(f"  {source.key:38s} {source.url}")
                if detail:
                    print(f"  {'':38s}   {detail}")

    if failures:
        print("\nFABRICATION — no innocent reading")
        for problem in failures:
            print(f"  {problem}")

    confirmed = len(buckets["confirmed"])
    print(
        f"\n{len(sources)} sources carry a digest, {len(chosen)} re-fetched: "
        f"{confirmed} confirmed, {len(buckets['drifted'])} drifted, "
        f"{len(buckets['gone'])} dead, {len(buckets['unreachable'])} unreachable."
    )
    if confirmed:
        print(
            f"{confirmed} digest(s) reproduced exactly, which only an actual fetch could "
            f"have produced. That is the positive evidence this gate exists for."
        )

    if failures:
        print(f"\n[FAIL] {len(failures)} source(s) could not have been fetched as recorded")
        return 1
    findings = len(buckets["gone"]) + len(buckets["unreachable"])
    if args.strict and findings:
        print(f"\n[FAIL] --strict: {findings} source(s) dead or unreachable")
        return 1
    print("\n[OK] no fabricated digests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
