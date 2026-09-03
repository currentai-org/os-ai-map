"""Deterministic rolling re-verification of the oldest products.

What it does: for each of the N oldest products (by the oldest of its three axis dates,
ties broken by slug), re-fetch every digested source that `establishes` a recorded
dimension on the selected axes through build.fetch_source. Where every establishing source
for an axis came back byte-identical (same content_sha256, non-transient), write `accessed`
and `http_status` on those sources and stamp that axis's `last_verified` to today. Any
drift, any transient result, or any dimension with no digested establishing source leaves
the axis untouched and goes in the report for the agent leg.

What it never does: derive a date from `accessed`, record a transient fetch as evidence,
touch an axis whose evidence changed, or write YAML by any route other than
build.components. Ruled on #445 (2026-09): a byte-identical re-fetch confirms an openness
dimension; adoption and capability sources carry numbers that move, so they are excluded
by default (--axes openness). See docs/reference/evidence-and-freshness.md.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml

from build import components
from build.check_freshness import parse_date
from build.fetch_source import fetch as _fetch
from build.taxonomy import category_statuses
from build.vocabulary import axes as _axes

ROOT = Path(__file__).resolve().parents[1]


def _published_slugs(root: Path) -> list[str]:
    taxonomy = yaml.safe_load((root / "sources" / "taxonomy.yaml").read_text())
    if taxonomy.get("arcs"):
        # The real corpus groups categories under arcs (see build/taxonomy.py); the unit
        # test fixture uses the older flat `categories:` shape, handled below.
        published = {slug for slug, status in category_statuses(taxonomy).items()
                     if status == "published"}
    else:
        published = {c["name"] for c in taxonomy.get("categories") or []
                     if c.get("status", "published") == "published"}
    slugs: list[str] = []
    for path in sorted((root / "sources" / "categories").glob("*.yaml")):
        cat = yaml.safe_load(path.read_text())
        if cat["name"] in published:
            slugs.extend(cat.get("products") or [])
    return slugs


def _score(root: Path, slug: str) -> dict:
    return yaml.safe_load((root / "sources" / "scores" / f"{slug}.yaml").read_text())


def oldest_products(root: Path, limit: int) -> list[tuple[date, str]]:
    ranked = []
    for slug in _published_slugs(root):
        score = _score(root, slug)
        dates = [parse_date(score[a]["last_verified"]) for a in _axes()
                 if isinstance(score.get(a), dict) and score[a].get("last_verified")]
        if dates:
            ranked.append((min(dates), slug))
    ranked.sort()
    return ranked[:limit]


@dataclass
class ProductResult:
    slug: str
    stamped: list[str] = field(default_factory=list)
    reconfirmed: dict[str, list[str]] = field(default_factory=dict)  # axis -> urls to re-date
    drifted: list[tuple[str, str]] = field(default_factory=list)
    transient: list[tuple[str, str]] = field(default_factory=list)
    skipped: list[tuple[str, str]] = field(default_factory=list)


def _recorded_dimensions(axis: str, block: dict) -> list[str]:
    if axis == "openness":
        comps = block.get("components")
        return sorted(comps) if isinstance(comps, dict) else []
    # adoption and capability record one dimension each for freshness purposes
    return [axis]


def plan_product(score: dict, axes: tuple[str, ...]) -> dict[str, dict[str, list[dict]]]:
    """axis -> dimension -> digested sources that establish it."""
    plan: dict[str, dict[str, list[dict]]] = {}
    for axis in axes:
        block = score.get(axis)
        if not isinstance(block, dict) or not block.get("last_verified"):
            continue
        dims = {d: [] for d in _recorded_dimensions(axis, block)}
        for src in block.get("sources") or []:
            if not src.get("content_sha256"):
                continue
            targets = src.get("establishes") if axis == "openness" else [axis]
            for d in targets or []:
                if d in dims:
                    dims[d].append(src)
        plan[axis] = dims
    return plan


def reverify_product(root: Path, slug: str, today: date, axes: tuple[str, ...] = ("openness",),
                     fetch=_fetch, pace: float = 0.0, sleep=time.sleep) -> ProductResult:
    score = _score(root, slug)
    result = ProductResult(slug=slug)
    cache: dict[str, dict] = {}
    for axis, dims in plan_product(score, axes).items():
        ok = True
        urls: list[str] = []
        for dim, sources in dims.items():
            if not sources:
                result.skipped.append((axis, f"{dim} has no digested establishing source"))
                ok = False
                continue
            for src in sources:
                url = src["url"]
                if url not in cache:
                    cache[url] = fetch(url)
                    if pace:
                        sleep(pace)
                got = cache[url]
                if got.get("transient") or not got.get("content_sha256"):
                    result.transient.append((axis, url))
                    ok = False
                elif got["content_sha256"] != src["content_sha256"]:
                    result.drifted.append((axis, url))
                    ok = False
                else:
                    urls.append(url)
        if ok and urls:
            result.stamped.append(axis)
            result.reconfirmed[axis] = sorted(set(urls))
    return result


def apply(root: Path, slug: str, result: ProductResult, today: date) -> None:
    path = root / "sources" / "scores" / f"{slug}.yaml"
    text = path.read_text()
    for axis in result.stamped:
        for url in result.reconfirmed[axis]:
            text = components.set_source(text, axis, url, {"accessed": today.isoformat(), "http_status": 200})
        text = components.put_field(text, today.isoformat(), axis=axis, key="last_verified", before="sources")
    if text != path.read_text():
        path.write_text(text)


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    root = root or ROOT
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--limit", type=int, default=150)
    p.add_argument("--axes", default="openness", help="comma-separated; default openness (see #445)")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--report", type=Path, default=None)
    p.add_argument("--today", default=None)
    p.add_argument("--pace", type=float, default=1.0, help="seconds to sleep between fetches")
    args = p.parse_args(argv)
    today = parse_date(args.today) if args.today else date.today()
    axes = tuple(a.strip() for a in args.axes.split(",") if a.strip())

    report = {"today": today.isoformat(), "axes": axes, "products": []}
    for _oldest, slug in oldest_products(root, args.limit):
        result = reverify_product(root, slug, today, axes=axes, pace=args.pace)
        if not args.dry_run:
            apply(root, slug, result, today)
        report["products"].append({
            "slug": slug, "stamped": result.stamped, "drifted": result.drifted,
            "transient": result.transient, "skipped": result.skipped,
        })
        print(f"{slug}: stamped={result.stamped} drifted={len(result.drifted)} "
              f"transient={len(result.transient)} skipped={len(result.skipped)}")
    if args.report:
        args.report.write_text(json.dumps(report, indent=2))
    stamped = sum(1 for r in report["products"] if r["stamped"])
    print(f"{stamped}/{len(report['products'])} products re-dated on {','.join(axes)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
