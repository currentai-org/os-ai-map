"""Report a band read off a distribution channel that has stopped carrying the product.

`select_route` picks the highest-precedence declared artifact and, once an authoritative
usage route exists, forbids falling through to `stars_fallback`. That rule is what stopped a
large star count overstating use, which is the direction ~45 corrections all ran in during
the August adoption sweep, and it stays. #435 asked whether a verified but non-primary
channel should keep winning or abstain instead. It keeps winning: abstention moves no
published number, because `_stage_and_gaps` reads `L` off a >= 4.5 count and `B` off a
`max()`, and the trigger only ever fires at the bottom of the distribution.

What the answer leaves open is the thing #435 was actually right about. A band read off a
registry release nobody has published to in a year is a real number about the wrong thing,
and `docs/reference/adoption.md`'s under-coverage ladder already says what to do with one.
Until now nothing checked that anybody did it. This is that check.

## Two legs, because there are two ways to see the same defect

  1. **The release line.** The newest release on the registry is at least one stable major
     line behind the repository's newest stable release or tag. That is mechanical: two
     public APIs, two version strings, one comparison. It is the ONLY form of "demonstrably
     non-primary" that can be audited, and it is narrow — a stale release line, not primacy
     in general.
  2. **The note.** A record whose own prose says the signal understates (or is inflated by CI
     and mirror traffic) with a band recorded on that signal anyway. That tell is named in
     `adoption.md` and implemented in `build/sweep_status.py`; it is imported here rather
     than restated, so the two cannot drift.

The legs agree on the cases that motivated #435 and disagree with the ratio test that
motivated the issue's framing, which is the useful result. Both catch `areal` and `xtuner`.
Neither catches `qwenpaw`, whose PyPI release `2.2.0b5` was uploaded the same day as the repo
tag `v2.2.0-beta.5` — its registry is exactly current and only its downloads-to-stars ratio
looked wrong. Neither catches `atropos`, a dormant project accurately measured.

## What is deliberately excluded

  * **A pre-release repo tag.** A beta ahead of the registry is ordinary publishing, not a
    trailing channel, so a repo tag carrying `a`/`b`/`rc`/`alpha`/`beta`/`dev`/`preview` is
    reported as an exclusion rather than a finding. Excluding it is what keeps `qwenpaw`
    clear. Four records are excluded this way today — `flash-attention`, `khoj`, `lance`,
    `mineru` — and the report prints the list, so this docstring does not become a second
    copy of a count that moves.
  * **A repo tag that does not parse to a version.** Date stamps, model names, per-package
    monorepo tags. Undecidable is not clean: the comparison could not be made, and saying so
    is different from saying there is no lag. Two records today: `chroma` and `mlflow`, both
    tagging `latest`.
  * **Everything that is not a registry channel.** A Hugging Face model or dataset repo IS
    the artifact; there is no registry-version-against-source-version gap to measure, which
    puts four categories out of leg 1's reach entirely. npm and crates are unbridged.
  * **The downloads-against-stars ratio.** Computable, and wrong. The precedence rule exists
    to stop stars setting a band; a test that lets stars decide whether a usage measurement
    counts hands stars a veto instead of a vote, which is the closed failure re-entering one
    level up.

**This split is not the one the #435 simulation reported, on purpose.** The simulation had
three pre-release exclusions and fourteen undecidable where this gate has four and two, and the
difference is two widenings rather than a disagreement: this gate falls back to `/tags` where a
repository publishes no releases at all, which reaches a verdict on most of the simulation's
undecidable products instead of abandoning them, and `parse_version` reads a version out of a
decorated tag like `fa4-v4.0.0.beta28`, which the simulation left unparsed. **The seven fires
are identical** — `areal`, `gpt-researcher`, `langtrace`, `openlit`, `sageattention`,
`swe-agent`, `xtuner` — and the fires are the part any ruling rests on.

## Report, never re-band

The same instruction #426 carries, for the same reason. A trailing channel and a monorepo
versioning its application separately from its pip package are indistinguishable from here, and
only one of them is a finding: `openlit` tags `openlit-2.0.0` and `gpt-researcher` versions an
app three lines ahead of its package. Nothing available decides which is which, and re-banding
on a guess attaches a level to a judgment nobody made.

Report-only also because the direction of the error matters. Applied to the prose tell as
written, abstention erases `gvisor` — level 5 on container distribution its note describes
honestly — and demotes `deployment` from stage 5 to 4 on the strength of a candid note. A
gate that punishes candor gets its notes rewritten rather than its bands fixed.

Ships non-strict, per this repo's convention (`check_adoption`, `check_instrument`,
`check_artifacts`). `--strict` is what CI passes once the backlog is clear.

Usage:
    uv run python -m build.check_channel_authority           # the prose leg, no network
    uv run python -m build.check_channel_authority --live    # add the release-line leg
    uv run python -m build.check_channel_authority --strict  # exit 1 on any finding
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

from build.adoption_measurements import all_routes, load_inputs, route_scopes, select_route
from build.propose_artifacts import _get_json, check_token
from build.serialize_registry import artifact_id
from build.sweep_status import under_coverage

# Stay polite across a few hundred calls, the same pace propose_artifacts uses for the same
# APIs. Leg 1 makes up to three requests per pypi-routed product (one PyPI, one releases, one
# tags fallback), so a full run is a few hundred requests rather than a handful.
_PACE_SECONDS = 0.12

ROOT = Path(__file__).resolve().parents[1]

# A repo tag that is a pre-release of a line the registry has not reached yet. Matched on the
# suffix rather than by full PEP 440 parsing, because a GitHub tag is not a PEP 440 version:
# `v2.2.0-beta.5`, `v12.0.0-beta.6`, `v4.0.0a6` and `2.0.0-beta.28` are all real tags in this
# corpus and only the third would parse.
#
# The digit lookbehind is load-bearing rather than defensive. A word-boundary alternative
# reads `v4.0.0a6` as stable, because `0` and `a` are both word characters and there is no
# boundary between them - which put MinerU's alpha tag in the findings as a whole major line
# ahead of its registry, the exact false positive this exclusion exists to prevent.
_PRERELEASE = re.compile(
    r"(?:[-_.]|(?<=\d))(?:a|b|c|rc|alpha|beta|dev|pre|preview|nightly|snapshot)\.?\d*$",
    re.IGNORECASE,
)
_VERSION = re.compile(r"(?:^|[^0-9])v?(\d+)\.(\d+)(?:\.(\d+))?")

# An instrument other than `usage_volume` is not banding on the registry count, so a trailing
# release line says nothing about the level it carries. Those are the records the ladder has
# already been applied to.
_BANDS_ON_THE_REGISTRY = "usage_volume"


def is_prerelease(tag: str) -> bool:
    """True when a tag names a pre-release of the line it belongs to."""
    return bool(_PRERELEASE.search((tag or "").strip()))


def parse_version(tag: str) -> tuple[int, int, int] | None:
    """(major, minor, patch) from a tag, or None when it does not carry a version.

    None is a real answer and is reported as undecidable rather than folded into "clear".
    A tag like `2026-08-01` or `openlit-2.0.0` is not evidence of an absent lag; it is
    evidence that this comparison could not be made.
    """
    matched = _VERSION.search((tag or "").strip())
    if not matched:
        return None
    return (int(matched.group(1)), int(matched.group(2)), int(matched.group(3) or 0))


def lag_verdict(pypi_version: str, repo_tag: str) -> tuple[str, int]:
    """(verdict, majors behind) for one registry version against one repository tag.

    Verdicts: `fires`, `clear`, `prerelease`, `undecidable`. Stable against stable, and
    strictly on the major line — a minor or patch lag is ordinary release cadence, and a
    threshold looser than a whole major would fire on most of the corpus.
    """
    registry, source = parse_version(pypi_version), parse_version(repo_tag)
    if registry is None or source is None:
        return ("undecidable", 0)
    behind = source[0] - registry[0]
    if behind <= 0:
        return ("clear", 0)
    if is_prerelease(repo_tag):
        # Reported only where it would otherwise have fired: a pre-release tag on a line the
        # registry already carries is not an exclusion, it is simply clean.
        return ("prerelease", behind)
    return ("fires", behind)


def pypi_routed(root: Path | None = None) -> dict[str, str]:
    """slug -> declared package, for every product whose winning adoption route is PyPI."""
    tables, _bands, category_of, declared, recorded = load_inputs(root or ROOT)
    routes, scopes = all_routes(tables), route_scopes(tables)
    base = root or ROOT
    out: dict[str, str] = {}
    for slug in sorted(declared):
        route = select_route(
            declared[slug], recorded.get(slug), category_of.get(slug), routes, scopes
        )
        if not route or route.get("artifact_kind") != "pypi":
            continue
        product = _load(base / "sources" / "products" / f"{slug}.yaml")
        for entry in product.get("pypi") or []:
            ident = artifact_id("pypi", entry.get("url") or "")
            if ident:
                out[slug] = ident
                break
    return out


def _load(path: Path) -> dict:
    return (yaml.safe_load(path.read_text()) or {}) if path.exists() else {}


def declared_repo_id(slug: str, root: Path | None = None) -> str | None:
    """`owner/repo` for the product's first declared GitHub artifact.

    Named `_id` rather than `declared_repo` because `propose_artifacts.declared_repo` already
    exists and answers a different question — what a PACKAGE's metadata claims, not what the
    product record declares. Two functions with one name and opposite inputs is how a wrong
    repository gets attached to a product.
    """
    product = _load((root or ROOT) / "sources" / "products" / f"{slug}.yaml")
    for entry in product.get("github") or []:
        ident = artifact_id("github", entry.get("url") or "")
        if ident:
            return ident
    return None


def newest_pypi_release(package: str) -> tuple[str, str] | None:
    """(version, ISO upload timestamp) for the package's newest release, or None.

    Read off the release history rather than off `info.version`, because the upload date is
    half the finding: "one major behind" and "one major behind for four hundred days" are
    different sentences to a reviewer.
    """
    body = _get_json(f"https://pypi.org/pypi/{package}/json", None)
    if not body:
        return None
    version = ((body.get("info") or {}).get("version") or "").strip()
    if not version:
        return None
    uploaded = ""
    for file_entry in (body.get("releases") or {}).get(version) or []:
        stamp = file_entry.get("upload_time_iso_8601") or file_entry.get("upload_time") or ""
        if stamp and (not uploaded or stamp < uploaded):
            uploaded = stamp
    return (version, uploaded)


def newest_repo_tag(repo: str, token: str | None = None) -> str | None:
    """The repository's newest release tag, falling back to its newest git tag.

    Releases first: a release carries an explicit publication order, where `/tags` does not
    and a repository that tags without releasing is common enough to need the fallback.
    `/releases` is ordered by creation, NOT by version, so the first entry is the most
    recently cut release and not necessarily the highest version — a backport to an older
    line published today would come back ahead of the current major.

    **The `prerelease` flag on the release is discarded on purpose.** GitHub's flag is a
    checkbox the publisher ticks; the version string is the release's own semantic claim, and
    `lag_verdict` compares strings. The case that decides it is `xtuner`, whose `v1.0.1` is
    flagged `prerelease: true` while its README documents XTuner V1 as the current release and
    the registry sits on `0.2.0`. Honoring the flag would call that registry current, which is
    the opposite of what the project's own documentation says. `qwenpaw` is protected by the
    string test instead (`v2.2.0-beta.5`), which is where the protection belongs. Reading the
    flag would flip both, so do not "tidy" this into the return value without re-deciding it —
    `tests/test_check_channel_authority.py` pins the boundary.
    """
    releases = _get_json(f"https://api.github.com/repos/{repo}/releases?per_page=1", token)
    if isinstance(releases, list) and releases:
        tag = (releases[0].get("tag_name") or "").strip()
        if tag:
            return tag
    time.sleep(_PACE_SECONDS)
    tags = _get_json(f"https://api.github.com/repos/{repo}/tags?per_page=1", token)
    if isinstance(tags, list) and tags:
        return (tags[0].get("name") or "").strip() or None
    return None


def _age_days(uploaded: str, today: date | None = None) -> int | None:
    if not uploaded:
        return None
    try:
        when = datetime.fromisoformat(uploaded.replace("Z", "+00:00"))
    except ValueError:
        return None
    reference = today or datetime.now(timezone.utc).date()
    return (reference - when.astimezone(timezone.utc).date()).days


def release_lines(root: Path | None = None, token: str | None = None) -> dict:
    """Leg 1, live. `{fires, prerelease, undecidable, considered, skipped}`.

    The three lists hold per-product rows. `considered` is the population — every pypi-routed
    product — and `skipped` counts the ones no verdict could be reached for, broken down by
    which lookup came back empty.

    A product whose package or repository could not be read is not a finding: a transport
    failure is not evidence of a trailing channel, and treating it as one would make the count
    a function of PyPI's availability. But it is not nothing either, and the first draft
    dropped it silently. A run degraded by 503s or an exhausted rate limit then reports fewer
    findings and looks *healthier* than a clean one, which is the worst failure mode a report
    can have. So the skips are counted and printed against the denominator.
    """
    base = root or ROOT
    scores = base / "sources" / "scores"
    routed = pypi_routed(base)
    out: dict = {
        "fires": [], "prerelease": [], "undecidable": [],
        "considered": len(routed),
        "skipped": {"declare no repository": 0, "package unreadable": 0, "repository unreadable": 0},
    }
    for slug, package in routed.items():
        repo = declared_repo_id(slug, base)
        if not repo:
            out["skipped"]["declare no repository"] += 1
            continue
        release = newest_pypi_release(package)
        if not release:
            out["skipped"]["package unreadable"] += 1
            continue
        version, uploaded = release
        time.sleep(_PACE_SECONDS)
        tag = newest_repo_tag(repo, token)
        if not tag:
            out["skipped"]["repository unreadable"] += 1
            continue
        time.sleep(_PACE_SECONDS)
        verdict, behind = lag_verdict(version, tag)
        if verdict == "clear":
            continue
        adoption = (_load(scores / f"{slug}.yaml").get("adoption") or {})
        row = {
            "slug": slug,
            "package": package,
            "version": version,
            "repo": repo,
            "tag": tag,
            "behind": behind,
            "age_days": _age_days(uploaded),
            "instrument": adoption.get("signal_type") or "",
            "banded_quantity": adoption.get("banded_quantity") or "",
        }
        out["prerelease" if verdict == "prerelease" else
            "undecidable" if verdict == "undecidable" else "fires"].append(row)
    return out


def skipped_total(legs: dict) -> int:
    return sum((legs.get("skipped") or {}).values())


def unremedied(fires: list[dict]) -> list[dict]:
    """Release-line fires whose band still rests on the registry count, unremedied.

    `docs/reference/adoption.md`'s ladder offers two remedies and this recognizes both, because
    a gate that advertises two and accepts one is a gate that flags a fixed product forever.

      * **Relabel.** A record on an instrument other than `usage_volume` no longer claims to be
        a download count of the product, so the trailing line says nothing about its level.
      * **Name the quantity.** A `banded_quantity` says what the figure actually counts, which
        is the whole remedy for the `langflow` and `semantic-kernel` shape — the band stands, a
        reader can see what stands behind it, and nobody is misled by a precise number about
        the wrong channel.

    The second is taken at face value: nothing here can read a `banded_quantity` and judge
    whether it describes the release line honestly. That is why the report still prints EVERY
    fire and marks only the unremedied ones — the remedied rows stay visible for a reviewer,
    they just stop counting as findings.
    """
    return [
        row for row in fires
        if row["instrument"] == _BANDS_ON_THE_REGISTRY and not row.get("banded_quantity")
    ]


REMEDY = (
    "Remedy, per docs/reference/adoption.md's under-coverage ladder: either record a\n"
    "  `banded_quantity` naming what the figure actually counts (a trailing release line, a\n"
    "  minority channel, a lifetime average admitted as a floor), or relabel the record\n"
    "  `reported_traction` with `reach` null and a digested source behind the level. Never\n"
    "  substitute the star count: the precedence rule exists to stop that."
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--live", action="store_true",
                        help="add the release-line leg, which reads PyPI and the GitHub API")
    parser.add_argument("--strict", action="store_true", help="exit 1 on any finding")
    args = parser.parse_args()

    findings = 0
    fires: list[dict] = []

    if args.live:
        # The rate limit is the difference between a short report and a wrong one. Leg 1 makes
        # up to three calls per product; unauthenticated GitHub allows 60 an hour, and an
        # exhausted limit returns an error body that reads here as "no repository tag" — a
        # skip, not a finding. So the report would quietly shrink rather than fail.
        token = check_token(os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"))
        if not token:
            print("warning: no working GITHUB_TOKEN. GitHub allows 60 unauthenticated requests")
            print("an hour and this leg needs a few hundred, so most repositories will come back")
            print("unreadable and be counted as skipped rather than checked. Read the skipped")
            print("line below before trusting the findings.\n")
        legs = release_lines(ROOT, token)
        fires, flagged = legs["fires"], unremedied(legs["fires"])
        marked = {row["slug"] for row in flagged}
        findings += len(flagged)
        checked = legs["considered"] - skipped_total(legs)
        print(f"{len(fires)} pypi-routed product(s) publish a release line at least one stable")
        print(f"major behind their repository; {len(flagged)} still band on that registry count.")
        print(f"{checked} of {legs['considered']} pypi-routed products were readable"
              + (f" ({skipped_total(legs)} skipped: "
                 + ", ".join(f"{n} {k}" for k, n in legs["skipped"].items() if n) + ")"
                 if skipped_total(legs) else "") + ".\n")
        for row in sorted(fires, key=lambda r: r["slug"]):
            age = f"{row['age_days']}d" if row["age_days"] is not None else "age unknown"
            mark = "~" if row["slug"] in marked else " "
            print(f"  {mark} {row['slug']:<22} {row['package']}=={row['version']} "
                  f"({age}) vs {row['repo']} {row['tag']} — {row['behind']} major(s) behind, "
                  f"{row['instrument'] or 'no instrument'}")
        if legs["prerelease"]:
            print(f"\n{len(legs['prerelease'])} excluded: the repository's newest tag is a "
                  "pre-release, which is")
            print("ordinary publishing rather than a trailing channel.")
            for row in sorted(legs["prerelease"], key=lambda r: r["slug"]):
                print(f"    {row['slug']:<22} {row['package']}=={row['version']} vs {row['tag']}")
        if legs["undecidable"]:
            print(f"\n{len(legs['undecidable'])} undecidable: the repository's newest tag does "
                  "not parse to a version, so")
            print("no comparison was made. Not the same as no lag.")
            for row in sorted(legs["undecidable"], key=lambda r: r["slug"]):
                print(f"    {row['slug']:<22} {row['package']}=={row['version']} vs {row['tag']!r}")
        print()
    else:
        print("release-line leg skipped; pass --live to read PyPI and the GitHub API.\n")

    prose = under_coverage()
    findings += len(prose)
    print(f"{len(prose)} measured band(s) whose own note says the signal does not measure the")
    print("product, with a band recorded on that signal anyway.\n")
    for slug, direction, phrase in sorted(prose):
        print(f"  ~ {slug:<28} {direction:<12} {phrase!r}")

    print(f"\n{REMEDY}")
    print("\nReport-only unless --strict. Nothing here re-bands a product.")
    if args.live and fires:
        # No count and no classification here on purpose. An earlier draft narrated "five of
        # the seven read as trailing channels and two look like a monorepo", which is a copy of
        # a count that drifts on the next release AND a judgment this module cannot make. The
        # heuristic that would derive it (does the tag look package-scoped) is a guess wearing a
        # derivation's clothes, which is worse than saying plainly that a human decides.
        print(f"Each of the {len(fires)} release-line fire(s) needs a person: a trailing channel")
        print("and a monorepo versioning its application apart from its package look identical")
        print("from here, and only one of them is a finding.")
    return 1 if findings and args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
