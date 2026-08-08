"""G4 — the sampled re-fetch: independent evidence that a recorded fetch actually happened.

`docs/guides/verification.md` is normative; this module implements the gate. It is the third
leg of the anti-rubber-stamping defense the runbook names, and until now the only one that
was missing.

## Why the other two are not enough

G1 asks whether a claimed date is supported by the `accessed` dates on record. G2 asks
whether the sources carry an `http_status` and a `content_sha256`. Both are real, and both
share a blind spot: **they read what the writer wrote.** An agent that never opened a page
can still emit a plausible `accessed`, a plausible `200`, and sixty-four plausible hex
characters, and both gates pass. That is #108's failure mode with better spelling.

G4 is the only check that goes and looks.

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

- **A digest reused across two different URLs.** Two distinct pages with byte-identical
  bodies is possible but rare; the same sixty-four characters pasted twice is the ordinary
  explanation, and it is fabrication.
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

    by_digest: dict[str, set[str]] = defaultdict(set)
    for source in sources:
        by_digest[source.digest].add(source.url)
    for digest, urls in sorted(by_digest.items()):
        if len(urls) > 1:
            listed = ", ".join(sorted(urls))
            problems.append(
                f"digest {digest[:12]}… is recorded for {len(urls)} different URLs "
                f"({listed}). Two pages with byte-identical bodies is possible; the same "
                f"digest pasted twice is likelier, and it means at least one was not fetched."
            )
    return problems


def refetch(source: Source, timeout: float) -> tuple[str, str]:
    """(outcome, detail). Outcome is one of confirmed / drifted / gone / unreachable."""
    try:
        response = requests.get(
            source.url,
            timeout=timeout,
            headers={"User-Agent": USER_AGENT},
            allow_redirects=True,
        )
    except requests.RequestException as exc:
        return "unreachable", f"{type(exc).__name__}: {exc}"

    # 429 and 5xx are the host saying "not now", not "not here". Calling those dead would
    # make the gate fail on GitHub's rate limiter, which is how a gate earns a reputation
    # for lying. The first run of this module reported a live Mastra LICENSE as dead for
    # exactly that reason.
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
        print("0 sources record a digest yet — nothing for G4 to re-fetch.")
        print("This is expected until the re-read pass populates content_sha256.")
        return 0

    failures = offline_failures(sources)

    chosen = sources
    if not args.all and len(sources) > args.sample:
        chosen = random.Random(args.seed).sample(sources, args.sample)

    buckets: dict[str, list[tuple[Source, str]]] = defaultdict(list)
    for source in sorted(chosen, key=lambda s: (s.product, s.axis, s.url)):
        outcome, detail = refetch(source, args.timeout)
        buckets[outcome].append((source, detail))

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
