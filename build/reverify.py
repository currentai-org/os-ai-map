"""Deterministic rolling re-verification of the oldest products.

What it does: for each of the N oldest products (by the oldest of its three axis dates,
ties broken by slug), re-fetch every digested source that `establishes` a recorded
dimension on the selected axes through build.fetch_source. A dimension re-confirms when
every establishing source's fresh fetch is non-transient and either (a) the body is
byte-identical to what was recorded, (b) the source's recorded `shows` still checks out
against the fresh body — the whole sentence occurs, or every fragment quoted inside it
does and at least one of those is long enough to discriminate — or (c) for a GitHub
license API / repo endpoint or a Hugging Face model-info source, the fresh SPDX id
normalizes to the same license already recorded.
Whichever path confirms it, the source takes the new `accessed`, `http_status` and
`content_sha256`, and once every dimension an axis records has confirmed, that axis's
`last_verified` is stamped to today. Any drift, any transient result, or any dimension
with no digested establishing source leaves the axis untouched and goes in the report for
the agent leg.

The dimension set an axis must confirm is not re-derived here: `build.check_verification`
already owns the definition the `invariant` gate enforces (it excludes non-evidence keys
like `free_text`), so this module imports and reuses it rather than keeping a second copy
that could drift from the gate.

What it never does: derive a date from `accessed`, record a transient fetch as evidence,
touch an axis whose evidence changed, or write YAML by any route other than
build.components. Ruled on #445 (2026-09): a byte-identical re-fetch confirms an openness
dimension; adoption and capability sources carry numbers that move, so they are excluded
by default (--axes openness). Ruled again 2026-09-03 (#445 follow-up): shows-match and
SPDX comparison are also acceptable confirmations, since byte identity is the wrong test
for evidence pages that legitimately re-render on every load. See
docs/reference/evidence-and-freshness.md.

Shows-match tests the quoted fragments as well as the whole sentence, because `shows` is
written as a curator's sentence *about* the page with the verbatim material quoted inside
it, and such a sentence never occurs on the page it describes. Measured 2026-09-12 over
the 25 oldest products: 72 sources drifted, 0 were skipped, 0 carried a placeholder
`shows`, and whole-sentence match confirmed 4 of them. See `_fragments_confirm`.
"""
from __future__ import annotations

import argparse
import functools
import html
import json
import re
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml

from build import components
from build.check_freshness import parse_date
from build.check_rubric import components_of, license_part, license_segments, normalize_license
from build.check_verification import PLACEHOLDER_SHOWS, category_of, recorded_dimensions
from build.fetch_source import fetch as _fetch
from build.rubrics import load_product_types, load_shared, recipe_for, resolve_recipe_variants
from build.taxonomy import category_statuses
from build.vocabulary import axes as _axes

ROOT = Path(__file__).resolve().parents[1]

# api.github.com/repos/<owner>/<repo>/license and the bare repo endpoint both carry a
# `license.spdx_id`; a Hugging Face model-info endpoint carries the license under
# `cardData.license` or, on older records, a top-level `license`.
_GITHUB_LICENSE_RE = re.compile(r"^https://api\.github\.com/repos/[^/]+/[^/]+/license/?$")
_GITHUB_REPO_RE = re.compile(r"^https://api\.github\.com/repos/[^/]+/[^/]+/?$")
_HF_MODEL_RE = re.compile(r"^https://huggingface\.co/api/models/.+$")

_ABSTAIN_SPDX = {"", "noassertion", "other"}


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


@dataclass(frozen=True)
class Confirmation:
    """One re-read citation: the URL as it read at confirmation time, and the fetch record.

    The URL is captured HERE rather than recovered at write time. `apply` used to read it
    back out of a fresh parse at the same position, which made `set_source`'s index/url
    agreement check compare that parse against itself — it could never fire, and a
    confirmation would be stamped onto whatever now occupied the slot, carrying the wrong
    digest. Holding the URL from the moment of confirmation is what lets that check mean
    something.
    """
    url: str
    fetched: dict


@dataclass
class ProductResult:
    slug: str
    stamped: list[str] = field(default_factory=list)
    # axis -> the source's position in that axis's `sources` list -> the Confirmation for
    # it. Keyed by position and not by URL: two entries may cite one page for different
    # dimensions, and keying by URL collapsed them into a single record that `apply` then
    # wrote to whichever came first (#527).
    reconfirmed: dict[str, dict[int, Confirmation]] = field(default_factory=dict)
    reconfirmed_by_shows: list[tuple[str, str]] = field(default_factory=list)
    reconfirmed_by_spdx: list[tuple[str, str]] = field(default_factory=list)
    drifted: list[tuple[str, str]] = field(default_factory=list)
    transient: list[tuple[str, str]] = field(default_factory=list)
    skipped: list[tuple[str, str]] = field(default_factory=list)


@functools.lru_cache(maxsize=None)
def _recipe_context(root_str: str) -> tuple[dict[str, str], dict[str, dict], dict[str, str]]:
    """(category slug per product, resolved recipe variants per category, product type per product).

    Loaded the same way `build.check_verification.load` loads it, just parametrized on
    `root` so tests can point it at a fixture corpus instead of the real one.
    """
    root = Path(root_str)
    categories = {
        p.stem: yaml.safe_load(p.read_text()) or {}
        for p in sorted((root / "sources" / "categories").glob("*.yaml"))
    }
    shared = load_shared(root)
    recipes: dict[str, dict] = {}
    for slug, category in categories.items():
        variants, errors = resolve_recipe_variants(category, shared)
        if variants and not errors:
            recipes[slug] = variants
    return category_of(categories), recipes, load_product_types(root)


def _openness_dimensions(root: Path, slug: str, block: dict) -> dict[str, str]:
    """dimension name -> recorded key, for exactly the dimensions `check_verification`'s
    invariant gate requires an establishing source for. Not re-derived: this calls the
    gate's own `recorded_dimensions` against the recipe governing this product."""
    owner, recipes, product_types = _recipe_context(str(root))
    variants = recipes.get(owner.get(slug, ""), {})
    recipe, _ = recipe_for(variants, product_types.get(slug, ""))
    return recorded_dimensions(components_of(block), recipe or {})


def plan_product(root: Path, slug: str, score: dict, axes: tuple[str, ...]
                 ) -> dict[str, dict[str, list[tuple[int, dict]]]]:
    """axis -> dimension -> digested sources that establish it, each with its position.

    The position is the source's ordinal in the axis's `sources` list, and it is carried
    from here rather than recovered later because it is the only thing that distinguishes
    two entries citing one URL (#527). A URL does not identify an entry; an ordinal does.
    """
    plan: dict[str, dict[str, list[tuple[int, dict]]]] = {}
    for axis in axes:
        block = score.get(axis)
        if not isinstance(block, dict) or not block.get("last_verified"):
            continue
        if axis == "openness":
            required = _openness_dimensions(root, slug, block)  # name -> recorded key
        else:
            required = {axis: axis}
        dims: dict[str, list[tuple[int, dict]]] = {name: [] for name in required}
        # A source may name either the dimension or the recorded key that answers it
        # (`establishes: [post-training-data]` is more precise than `[data]`) — the same
        # either-or the invariant gate itself accepts.
        aliases = {key: name for name, key in required.items() if key != name}
        for position, src in enumerate(block.get("sources") or []):
            if not src.get("content_sha256"):
                continue
            targets = src.get("establishes") if axis == "openness" else [axis]
            for d in targets or []:
                name = d if d in dims else aliases.get(d)
                if name:
                    dims[name].append((position, src))
        plan[axis] = dims
    return plan


def _normalize_text(text: str) -> str:
    return " ".join(text.split())


def _is_placeholder_shows(shows: object) -> bool:
    normalized = _normalize_text(str(shows or ""))
    return any(marker in normalized for marker in PLACEHOLDER_SHOWS)


def _read_body(fetched: dict) -> str | None:
    body_path = fetched.get("body_path")
    if not body_path:
        return None
    try:
        raw = Path(body_path).read_bytes()
    except OSError:
        return None
    return html.unescape(raw.decode("utf-8", errors="replace"))


# The corpus quotes with both straight and curly double quotes, sometimes in one
# sentence, so the delimiters are folded together before the pair scan.
_SMART_DOUBLE_QUOTES = "\u201c\u201d\u201e\u201f\u2033"

# A quoted fragment shorter than this does not count toward a confirmation. Chosen off
# the corpus rather than by taste: of the 1,714 fragments quoted inside a `shows` today,
# the 563 below 24 characters are almost entirely JSON key names and license ids —
# `license`, `name`, `spdx_id`, `MIT`, `Apache-2.0`, `open_issues_count` — and one- or
# two-word English like `gated`, `open source`, `Enterprise`. Those occur on any page of
# the kind being cited, so finding one discriminates nothing. 426 of the 563 are one or
# two words, and at 24 characters only 5 of the 1,151 surviving fragments are that short
# (they are file paths, `surfsense_backend/app/proprietary/LICENSE` and the like). At a
# floor of 20 characters, 93 two-word fragments still qualify; at 24, two do. A two-word
# quote found somewhere on a page proves nothing, and 24 is where the corpus stops
# offering them.
MIN_FRAGMENT_CHARS = 24


def _shows_fragments(shows: str) -> list[str]:
    """The verbatim material quoted inside a curator's `shows` sentence.

    A plain double-quote pair scan: split the whitespace-normalized sentence on `"` and
    the odd-indexed segments are the insides of the pairs. An unbalanced trailing quote
    opens a pair that never closes, and that dangling segment is dropped rather than
    guessed at. Nested quotes are not parsed as nesting — the scan just pairs off
    quotes in order, which is what a curator writing `"license":{"spdxId":"MIT"}` inside
    a sentence actually means.

    Fragments are matched with `in` and are never compiled, so a regex metacharacter, a
    bracket or a bare URL inside one is only ever text.
    """
    text = _normalize_text(str(shows))
    for ch in _SMART_DOUBLE_QUOTES:
        text = text.replace(ch, '"')
    parts = text.split('"')
    pairs = (len(parts) - 1) // 2
    return [f for f in (p.strip() for p in parts[1::2][:pairs]) if f]


def _fragments_confirm(shows: str, body: str) -> bool:
    """Every fragment quoted inside `shows` still occurs in `body`, and at least one of
    them is long enough to mean something. `body` is already normalized.

    Both halves carry weight, and dropping either one breaks it in a different
    direction. **Every** is what stops a partial match being read as a confirmation: a
    `shows` that quotes nine things and finds two of them on the page has not been
    confirmed; seven of the things it says the page carries are not on the page. **At least one long fragment** is
    what stops the opposite failure, where a `shows` whose only quoted material is
    `"license"` and `"MIT"` would confirm against any GitHub API response ever served.
    A short fragment still has to be there; it just cannot be the thing that earns the
    date. A `shows` that quotes nothing at all has no long fragment and so never reaches
    this path — saying less must not make a source easier to confirm.
    """
    fragments = _shows_fragments(shows)
    if not any(len(f) >= MIN_FRAGMENT_CHARS for f in fragments):
        return False
    return all(f in body for f in fragments)


def _shows_confirms(src: dict, fetched: dict) -> bool:
    """The source's recorded `shows` still checks out against the fresh body.

    Two ways, under one normalization (whitespace collapsed, the body read through
    `html.unescape`). The whole sentence may occur verbatim, which is the original test
    and is unchanged. Otherwise the fragments quoted inside it must all occur.

    The second path exists because `shows` is almost never an excerpt. It is a curator's
    sentence *about* the page with the verbatim material quoted inside it — "repo page
    carries the label "Public archive" and the banner "This repository was archived..."" —
    and a sentence like that does not appear on the page it describes, so testing the
    whole of it tests the curator's prose rather than the evidence. Measured 2026-09-12
    over the 25 oldest products through `build.fetch_source`: 72 sources drifted, none
    skipped, none carrying a placeholder `shows`, and the whole-sentence path confirmed 4.
    """
    shows = src.get("shows")
    if not shows or _is_placeholder_shows(shows):
        return False
    body = _read_body(fetched)
    if body is None:
        return False
    body = _normalize_text(body)
    if _normalize_text(str(shows)) in body:
        return True
    return _fragments_confirm(str(shows), body)


def _spdx_confirms(url: str, fetched: dict, recorded_license: str) -> bool:
    """A GitHub license/repo API or HF model-info source whose fresh spdx id normalizes
    to the recorded license. Abstains (falls through to shows-match, then drift) on a
    compound license, a missing/NOASSERTION/other spdx id, or a non-matching source URL."""
    if not recorded_license:
        return False
    segments = license_segments(recorded_license)
    if len(segments) != 1:
        return False
    body = _read_body(fetched)
    if body is None:
        return False
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return False
    if _GITHUB_LICENSE_RE.match(url) or _GITHUB_REPO_RE.match(url):
        spdx = (payload.get("license") or {}).get("spdx_id") if isinstance(payload, dict) else None
    elif _HF_MODEL_RE.match(url):
        card = payload.get("cardData") if isinstance(payload, dict) else None
        spdx = (card or {}).get("license") or (payload.get("license") if isinstance(payload, dict) else None)
    else:
        return False
    if not isinstance(spdx, str) or spdx.strip().lower() in _ABSTAIN_SPDX:
        return False
    recorded_name = license_part(segments[0])["name"]
    return normalize_license(spdx.strip()) == normalize_license(recorded_name)


def reverify_product(root: Path, slug: str, today: date, axes: tuple[str, ...] = ("openness",),
                     fetch=_fetch, pace: float = 0.0, sleep=time.sleep,
                     body_dir: Path | None = None) -> ProductResult:
    score = _score(root, slug)
    result = ProductResult(slug=slug)
    cache: dict[str, dict] = {}
    for axis, dims in plan_product(root, slug, score, axes).items():
        block = score[axis]
        components_map = components_of(block) if axis == "openness" else {}
        license_key = None
        if axis == "openness":
            required = _openness_dimensions(root, slug, block)
            license_key = required.get("license")
        recorded_license = components_map.get(license_key, "") if license_key else ""

        ok = True
        # Keyed by position, so two entries citing one URL stay two confirmations. The
        # fetch cache stays keyed by URL — fetching one page once is correct, and it is
        # only the write-back that has to know which citation it belongs to.
        confirmed: dict[int, Confirmation] = {}
        for dim, sources in dims.items():
            if not sources:
                result.skipped.append((axis, f"{dim} has no digested establishing source"))
                ok = False
                continue
            for position, src in sources:
                url = src["url"]
                if url not in cache:
                    cache[url] = fetch(url, body_dir=body_dir)
                    if pace:
                        sleep(pace)
                got = cache[url]
                if got.get("transient") or not got.get("content_sha256"):
                    result.transient.append((axis, url))
                    ok = False
                    continue
                if got["content_sha256"] == src["content_sha256"]:
                    confirmed[position] = Confirmation(url, got)
                    continue
                if dim == "license" and _spdx_confirms(url, got, recorded_license):
                    confirmed[position] = Confirmation(url, got)
                    result.reconfirmed_by_spdx.append((axis, url))
                    continue
                if _shows_confirms(src, got):
                    confirmed[position] = Confirmation(url, got)
                    result.reconfirmed_by_shows.append((axis, url))
                    continue
                result.drifted.append((axis, url))
                ok = False
        if ok and confirmed:
            result.stamped.append(axis)
            result.reconfirmed[axis] = confirmed
    return result


def apply(root: Path, slug: str, result: ProductResult, today: date) -> None:
    path = root / "sources" / "scores" / f"{slug}.yaml"
    text = path.read_text()
    for axis in result.stamped:
        for position, confirmation in sorted(result.reconfirmed[axis].items()):
            # The URL comes from the confirmation, not from a re-read of the file, so
            # `set_source` compares what was confirmed against what is there now and
            # refuses when the citation at that position has changed underneath us.
            text = components.set_source(text, axis, confirmation.url, {
                "accessed": today.isoformat(),
                "http_status": confirmation.fetched["http_status"],
                "content_sha256": confirmation.fetched["content_sha256"],
            }, index=position)
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
    p.add_argument("--body-dir", type=Path, default=None,
                    help="where to save fetched bodies for shows/spdx matching (default: a temp dir)")
    args = p.parse_args(argv)
    today = parse_date(args.today) if args.today else date.today()
    axes = tuple(a.strip() for a in args.axes.split(",") if a.strip())
    body_dir = args.body_dir or Path(tempfile.mkdtemp(prefix="os-ai-map-reverify-"))

    report = {"today": today.isoformat(), "axes": axes, "products": []}
    for _oldest, slug in oldest_products(root, args.limit):
        result = reverify_product(root, slug, today, axes=axes, pace=args.pace, body_dir=body_dir)
        if not args.dry_run:
            apply(root, slug, result, today)
        report["products"].append({
            "slug": slug, "stamped": result.stamped, "drifted": result.drifted,
            "transient": result.transient, "skipped": result.skipped,
            "reconfirmed_by_shows": result.reconfirmed_by_shows,
            "reconfirmed_by_spdx": result.reconfirmed_by_spdx,
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
