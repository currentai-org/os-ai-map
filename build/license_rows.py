"""Judge cited license sources from the weekly `artifact_state` rows instead of a fetch (#691).

Report only. This module never writes a score, a source entry or a date.

## Why

`build/reverify.py` confirms a license by re-fetching what the record cites. It can read a
license out of only three API endpoints, so a record citing `github.com/<o>/<r>` or a Hub model
page drifts every week however settled its license is: the page re-renders, the digest moves,
and the HTML carries nothing the SPDX comparison can read. Two scheduled platform models
already fetch the API form of every declared artifact, license included:

  * `currentai.signal_github.artifact_state` (`license_spdx_id`), and
  * `currentai.signal_huggingface.artifact_state` (`license`, for models and datasets).

So the observation exists. What #691 needed was three rulings, all taken 2026-09-25:

  1. **Evidence identity.** A cited github.com or huggingface.co page may be judged from its API
     form, with the rewrite declared in one place. It is declared under
     `dimensions.license.source_rewrites` in `sources/signal_routing.yaml`, and this module
     infers nothing beyond it.
  2. **Part scoping.** A license is compared only with the part it covers: a repository license
     with the part about the code (`check_contradictions.comparable_license`), a Hub model card
     with the part about the weights, a Hub dataset card with the part about the data. This is
     what keeps a dataset card from refuting a model's license, which produced five false
     refutations when it was tried without it.
  3. **The freshness event.** What would be re-dated is measured, here, before anything writes.

The 2026-10-03 review on the issue added the rule that makes the comparison safe on a product
declaring several artifacts: **a row is bound to the artifact the cited URL names.** zephyr cites
the zephyr-7b-beta card and records MIT; the zephyr-orpo card it also declares says Apache-2.0.
Matching by product would refute a correct record. Matching by the cited artifact confirms it.

## What a verdict is

Three-valued, as in `reverify._spdx_verdict`. A source CONFIRMS when the row's license, normalized
through its route's alias group (`aliases.huggingface` for the Hub, so `odc-by` reads as
`ODC-By-1.0`), equals the recorded part. It REFUTES when a usable row disagrees, and a refutation
is a question for a person: it ends in a corrected record or a settlement in
`sources/contradictions_settled.yaml`, never an automatic correction. Everything else ABSTAINS,
with the reason. A source whose URL no rewrite covers is on the DIRECT path: it stays with
reverify's fetch, and a raw LICENSE file always does.

## Why nothing writes yet

A confirmation here is a warehouse row, not a fetch of the cited URL, so it has no `accessed`,
`http_status` or digest of its own to record. The review asked for per-dimension provenance (the
artifact, column, observed value, `fetched_at` and the scheduled run) before any date is written,
and the score schema and `check_verification` do not accept that yet. Until they do this is the
dry run the ruling asked for: one report over the whole corpus.

A read counts only when it is bound to a SCHEDULED, successful materialization at most
`MAX_BINDING_AGE_DAYS` old, checked by `build.read_binding` and
`adoption_freshness.binding_problems` exactly as the adoption reconciliation checks its read.
An unbound read is still reported, but nothing in it is counted as a confirmation.

Usage:
    uv run python -m build.license_rows                 # live, bound reads
    uv run python -m build.license_rows --json out.json
    uv run python -m build.license_rows --rows-github g.json --rows-huggingface h.json
"""
from __future__ import annotations

import argparse
import collections
import dataclasses
import datetime
import functools
import json
import re
import sys
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path

import yaml

from build.check_contradictions import (
    BARE_LICENSE_ID,
    CODE_TOKENS,
    GRADE_TOKENS,
    QUALIFIED_NAME,
    comparable_license,
    detail_tokens,
)
from build.check_rubric import SCOPE_PREFIX, entries, is_license_key, license_parts_of, normalize_license

ROOT = Path(__file__).resolve().parents[1]

CONFIRMS, REFUTES, ABSTAINS, DIRECT = "confirms", "refutes", "abstains", "direct"

GITHUB, HF_MODEL, HF_DATASET = "github", "huggingface_model", "huggingface_dataset"
#: The product-file key that declares each route's artifacts. They happen to coincide.
DECLARATION_KEY = {GITHUB: "github", HF_MODEL: "huggingface_model", HF_DATASET: "huggingface_dataset"}
#: Where each route's rows live: (dataset, model, column holding the license).
TABLES = {
    GITHUB: ("signal_github", "artifact_state", "license_spdx_id"),
    HF_MODEL: ("signal_huggingface", "artifact_state", "license"),
    HF_DATASET: ("signal_huggingface", "artifact_state", "license"),
}

GITHUB_QUERY = """
SELECT product_slug, repo, resolved_repo, license_spdx_id, http_status, fetched_at
FROM currentai.signal_github.artifact_state
"""
HUGGINGFACE_QUERY = """
SELECT product_slug, artifact_kind, artifact_id, resolved_id, license, http_status, fetched_at
FROM currentai.signal_huggingface.artifact_state
"""

#: Detail tokens that scope a recorded part to the weights, or to the data. Together with
#: `check_contradictions.CODE_TOKENS` they are the scopes a route's `governs` can name.
WEIGHTS_TOKENS = frozenset({"model", "weights"})
DATA_TOKENS = frozenset({"data", "dataset"})
SCOPE_TOKENS = {"weights": WEIGHTS_TOKENS, "dataset": DATA_TOKENS, "code": CODE_TOKENS}
#: The scope a product type's unqualified license is about.
DEFAULT_SCOPE = {"software": "code", "model": "weights", "dataset": "dataset"}

#: How a cited URL that no rewrite covers is classified on the direct path.
_RAW_LICENSE_FILE = re.compile(r"(?i)/(?:LICEN[CS]E|COPYING|NOTICE)(?:[.-][^/]*)?$")


# --- declarations -------------------------------------------------------------------------------


@functools.lru_cache(maxsize=None)
def _license_routing(root_str: str) -> dict:
    routing = yaml.safe_load((Path(root_str) / "sources" / "signal_routing.yaml").read_text()) or {}
    return ((routing.get("dimensions") or {}).get("license")) or {}


def rewrites(root: Path = ROOT) -> list[tuple[str, re.Pattern]]:
    """The declared (route source, pattern) pairs, in declaration order."""
    out = []
    for entry in _license_routing(str(root)).get("source_rewrites") or []:
        out.append((str(entry["source"]), re.compile(str(entry["match"]))))
    return out


def route_for(url: str, root: Path = ROOT) -> tuple[str, str] | None:
    """(route source, artifact id) for a URL a rewrite covers, or None. The first match wins."""
    for source, pattern in rewrites(root):
        match = pattern.match(str(url).strip())
        if match:
            return source, match.group("artifact")
    return None


def route_policy(root: Path = ROOT) -> dict[str, dict]:
    """Per route source: what it `governs` and the values that mean "no answer"."""
    out: dict[str, dict] = {}
    for route in _license_routing(str(root)).get("routes") or []:
        values = {str(v).strip().lower() for v in route.get("abstain_values") or []}
        out[str(route["source"])] = {"governs": str(route.get("governs") or ""), "abstain": values | {""}}
    return out


def observed_aliases(root: Path = ROOT) -> dict[str, dict[str, str]]:
    """Per route source, the alias group its observed values are read through.

    The Hub serves slugs (`odc-by`, `llama3.1`) and `aliases.huggingface` names them. GitHub
    serves SPDX ids already, so it has no group. Without this every ODC-BY dataset refutes on
    day one, which the 2026-10-03 preview caught on refinedweb.
    """
    groups = _license_routing(str(root)).get("aliases") or {}
    hub = {str(k).strip().lower(): str(v).strip() for k, v in (groups.get("huggingface") or {}).items()}
    return {GITHUB: {}, HF_MODEL: hub, HF_DATASET: hub}


def canonical(name: str, source: str, root: Path = ROOT) -> str:
    """One license name as the comparison sees it, lowercased.

    Both sides go through the route's alias group, then `normalize_license` (which applies the
    `recorded` group). An alias says what a license is CALLED, so it applies to a hand-written
    name as much as to a served slug: the corpus records `ODC-BY` and `odc-by` where the Hub's
    `odc-by` is named `ODC-By-1.0`, and reading the alias on one side only refuted every one of
    them.
    """
    value = str(name).strip()
    value = observed_aliases(root)[source].get(value.lower(), value)
    return normalize_license(value).lower()


def declared_artifacts(product: Mapping, root: Path = ROOT) -> dict[str, set[str]]:
    """Per route source, the lowercased artifact ids the product file declares.

    Parsed with the same declared rewrites as the cited URL, so a declaration and a citation
    can only match when both name the artifact the same way.
    """
    out: dict[str, set[str]] = {source: set() for source in DECLARATION_KEY}
    for source, key in DECLARATION_KEY.items():
        for item in product.get(key) or []:
            url = item.get("url") if isinstance(item, Mapping) else item
            routed = route_for(str(url or ""), root)
            if routed and routed[0] == source:
                out[source].add(routed[1].lower())
    return out


# --- rows ---------------------------------------------------------------------------------------


def index_rows(github_rows: Iterable[Mapping], hf_rows: Iterable[Mapping]) -> dict[tuple[str, str, str], dict]:
    """(route source, product slug, lowercased artifact id) -> row.

    A row is indexed under both the declared id and the id it resolved to, so a renamed
    repository still binds to the citation that names either spelling.
    """
    out: dict[tuple[str, str, str], dict] = {}
    for row in github_rows:
        for key in ("repo", "resolved_repo"):
            if row.get(key):
                out.setdefault((GITHUB, str(row["product_slug"]), str(row[key]).lower()), dict(row))
    for row in hf_rows:
        source = str(row.get("artifact_kind") or "")
        if source not in (HF_MODEL, HF_DATASET):
            continue
        for key in ("artifact_id", "resolved_id"):
            if row.get(key):
                out.setdefault((source, str(row["product_slug"]), str(row[key]).lower()), dict(row))
    return out


# --- part scoping -------------------------------------------------------------------------------


def _scope(part: Mapping, product_type: str) -> str:
    """`code`, `weights`, `dataset`, or `` when nothing says which artifact the part is about."""
    tokens = set(detail_tokens(part))
    name = str(part.get("name") or "").strip().lower()
    named = [scope for scope, scope_tokens in SCOPE_TOKENS.items() if tokens & scope_tokens]
    if name.startswith("code "):
        named.append("code")
    if name.startswith("model "):
        named.append("weights")
    if len(set(named)) == 1:
        return named[0]
    if named:
        return ""  # more than one scope on one part: nothing here can say which governs
    return DEFAULT_SCOPE.get(product_type, "")


def comparable_part(entry: object, product_type: str, governs: str) -> tuple[dict | None, str]:
    """The one recorded part a row governing `governs` may be compared with, or why not.

    For `code` this is `check_contradictions.comparable_license` unchanged, so the sweep and
    this leg cannot disagree about a repository license. For `weights` and `dataset` it is the
    same rule pointed at the other artifact: exactly one part about that artifact, a bare id,
    no qualification in the name, and nothing in the detail beyond the grade and the scope.
    """
    if governs == "code":
        return comparable_license(entry, product_type)
    parts = license_parts_of(entry)
    if not parts:
        return None, "no license parts recorded"
    scoped = [part for part in parts if _scope(part, product_type) == governs]
    if len(scoped) > 1:
        return None, f"more than one recorded part covers the {governs}"
    if not scoped:
        return None, f"no recorded part is about the {governs} ({product_type or 'unknown type'})"
    part = scoped[0]
    name = SCOPE_PREFIX.sub("", str(part.get("name") or "").strip()).strip()
    if not BARE_LICENSE_ID.match(name):
        return None, "the recorded name is not a bare license id"
    if QUALIFIED_NAME.search(name):
        return None, "the name carries a qualification"
    allowed = GRADE_TOKENS | SCOPE_TOKENS[governs]
    if any(token not in allowed for token in detail_tokens(part)):
        return None, "the detail qualifies the license"
    return part, ""


def recorded_license(score: Mapping) -> tuple[str | None, object, str]:
    """(license key, entry, reason): the one license the openness score records, or why not."""
    components = (score.get("openness") or {}).get("components") or {}
    if not isinstance(components, dict):
        return None, None, "components are not structured"
    recorded = entries(components)
    keys = [key for key in recorded if is_license_key(key)]
    if len(keys) != 1:
        return None, None, "not exactly one recorded license key"
    return keys[0], recorded[keys[0]], ""


# --- verdicts -----------------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class SourceVerdict:
    slug: str
    url: str
    verdict: str
    reason: str = ""
    route: str = ""
    artifact: str = ""
    recorded: str = ""
    observed: str = ""
    fetched_at: str = ""
    bound: bool = False


def _direct_class(url: str) -> str:
    if "raw.githubusercontent.com" in url or _RAW_LICENSE_FILE.search(url.split("?")[0]):
        return "a raw license file stays on the direct-document path"
    return "no declared rewrite covers this URL"


def judge_source(
    slug: str,
    url: str,
    product: Mapping,
    entry: object,
    rows: Mapping[tuple[str, str, str], Mapping],
    bound: Mapping[str, bool],
    root: Path = ROOT,
) -> SourceVerdict:
    """One cited license source, judged from the row of the artifact it names."""
    routed = route_for(url, root)
    if routed is None:
        return SourceVerdict(slug, url, DIRECT, _direct_class(url))
    source, artifact = routed
    base = {"route": source, "artifact": artifact, "bound": bool(bound.get(source))}
    if artifact.lower() not in declared_artifacts(product, root)[source]:
        return SourceVerdict(slug, url, ABSTAINS, "the cited artifact is not declared on the product", **base)
    row = rows.get((source, slug, artifact.lower()))
    if row is None:
        return SourceVerdict(slug, url, ABSTAINS, "no artifact_state row for the cited artifact", **base)
    fetched_at = str(row.get("fetched_at") or "")
    if str(row.get("http_status")) != "200":
        return SourceVerdict(slug, url, ABSTAINS, "the row's fetch did not return 200", fetched_at=fetched_at, **base)
    policy = route_policy(root).get(source, {"governs": "", "abstain": {""}})
    column = TABLES[source][2]
    raw = row.get(column)
    value = "" if raw is None or (isinstance(raw, float) and raw != raw) else str(raw).strip()
    if value.lower() in policy["abstain"]:
        return SourceVerdict(slug, url, ABSTAINS, "the row carries no usable license", fetched_at=fetched_at, **base)
    part, why = comparable_part(entry, str(product.get("type") or ""), policy["governs"])
    if part is None:
        return SourceVerdict(slug, url, ABSTAINS, why, observed=value, fetched_at=fetched_at, **base)
    recorded = str(part["name"]).strip()
    if canonical(value, source, root) == canonical(recorded, source, root):
        return SourceVerdict(slug, url, CONFIRMS, recorded=recorded, observed=value, fetched_at=fetched_at, **base)
    return SourceVerdict(slug, url, REFUTES, "the row disagrees with the record",
                         recorded=recorded, observed=value, fetched_at=fetched_at, **base)


def license_sources(score: Mapping, license_key: str) -> list[dict]:
    """The digested openness sources that establish the license, as reverify would plan them."""
    out = []
    for src in (score.get("openness") or {}).get("sources") or []:
        if not src.get("content_sha256"):
            continue
        targets = set(src.get("establishes") or [])
        if "license" in targets or license_key in targets:
            out.append(src)
    return out


#: The three endpoints reverify's fetch path already reads a license from. A product whose
#: license is reachable through one of them is not new reach.
_ALREADY_ROUTED = (
    re.compile(r"^https://api\.github\.com/repos/[^/]+/[^/]+(?:/license)?/?$"),
    re.compile(r"^https://huggingface\.co/api/models/.+$"),
)


@dataclasses.dataclass
class ProductReport:
    slug: str
    last_verified: str
    outcome: str
    sources: list[SourceVerdict]
    reached_before: bool


def product_outcome(verdicts: Sequence[SourceVerdict]) -> str:
    """What the license dimension would do if the rows were the only evidence read.

    `confirms` needs every establishing source to confirm from a bound read, the same "every
    source" rule reverify stamps on. One refutation decides the dimension. A mix of row
    confirmations and direct sources needs the direct fetch for the rest.
    """
    if any(v.verdict == REFUTES for v in verdicts):
        return "refuted"
    if verdicts and all(v.verdict == CONFIRMS and v.bound for v in verdicts):
        return "confirms"
    if verdicts and all(v.verdict == CONFIRMS for v in verdicts):
        return "confirms on an unbound read"
    if any(v.verdict == CONFIRMS for v in verdicts) and all(v.verdict in (CONFIRMS, DIRECT) for v in verdicts):
        return "confirms in part; the rest is on the direct path"
    if all(v.verdict == DIRECT for v in verdicts):
        return "direct path only"
    return "abstains"


def build_report(
    products: Mapping[str, Mapping],
    scores: Mapping[str, Mapping],
    rows: Mapping[tuple[str, str, str], Mapping],
    bound: Mapping[str, bool],
    root: Path = ROOT,
) -> tuple[list[ProductReport], collections.Counter]:
    reports: list[ProductReport] = []
    skipped: collections.Counter = collections.Counter()
    for slug in sorted(scores):
        score, product = scores[slug], products.get(slug)
        if product is None:
            skipped["no product file"] += 1
            continue
        key, entry, why = recorded_license(score)
        if key is None:
            skipped[why] += 1
            continue
        sources = license_sources(score, key)
        if not sources:
            skipped["no digested source establishes the license"] += 1
            continue
        verdicts = [judge_source(slug, src["url"], product, entry, rows, bound, root) for src in sources]
        reports.append(ProductReport(
            slug=slug,
            last_verified=str((score.get("openness") or {}).get("last_verified") or ""),
            outcome=product_outcome(verdicts),
            sources=verdicts,
            reached_before=any(p.match(str(s["url"])) for s in sources for p in _ALREADY_ROUTED),
        ))
    return reports, skipped


# --- reading ------------------------------------------------------------------------------------


def _load_dir(directory: Path) -> dict[str, dict]:
    return {p.stem: yaml.safe_load(p.read_text()) or {} for p in sorted(directory.glob("*.yaml"))}


def live_rows(reader: Callable[[str], list[dict]] | None = None) -> tuple[list[dict], list[dict], dict[str, list[str]]]:
    """Both tables read inside a materialization bracket, with what each binding lacks."""
    from build.adoption_freshness import binding_problems
    from build.read_binding import BindingLookupError, bound_read

    if reader is None:
        from build.warehouse import query as reader  # type: ignore[assignment]
    out: dict[str, list[dict]] = {}
    problems: dict[str, list[str]] = {}
    for dataset, sql in (("signal_github", GITHUB_QUERY), ("signal_huggingface", HUGGINGFACE_QUERY)):
        try:
            result = bound_read(lambda sql=sql: reader(sql), model_name="artifact_state", dataset_name=dataset)
        except BindingLookupError as exc:
            out[dataset] = reader(sql)
            problems[dataset] = [f"the read could not be bound: {exc}"]
            continue
        out[dataset] = result.rows
        # `read_at` is the reader's to stamp, as the adoption reconciliation stamps it: the
        # bracket proves which materialization served the rows, not when they were read.
        binding = {**result.binding, "read_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
        problems[dataset] = binding_problems(binding)
    return out["signal_github"], out["signal_huggingface"], problems


def render(reports: Sequence[ProductReport], skipped: collections.Counter, problems: Mapping[str, list[str]]) -> str:
    lines = ["License sources judged from artifact_state rows (#691). Report only: nothing is written.", ""]
    for dataset, issues in sorted(problems.items()):
        lines.append(f"{dataset}.artifact_state: " + ("bound to a scheduled run" if not issues else "NOT BOUND - " + "; ".join(issues)))
    outcomes = collections.Counter(r.outcome for r in reports)
    new_reach = [r for r in reports if r.outcome == "confirms" and not r.reached_before]
    lines += [
        "",
        f"{len(reports)} products cite a digested source for their license",
        f"{sum(1 for r in reports if r.reached_before)} were already readable by reverify's API fetch",
        f"{outcomes['confirms']} would confirm their license from bound rows alone, "
        f"{len(new_reach)} of them not readable by the fetch path today",
        "",
        "by product outcome:",
    ]
    lines += [f"  {n:5}  {outcome}" for outcome, n in outcomes.most_common()]
    per_source = collections.Counter((v.verdict, v.reason) for r in reports for v in r.sources)
    lines += ["", "by source verdict:"]
    lines += [f"  {n:5}  {verdict}{': ' + reason if reason else ''}" for (verdict, reason), n in per_source.most_common()]
    if skipped:
        lines += ["", "products not judged:"]
        lines += [f"  {n:5}  {why}" for why, n in skipped.most_common()]
    refuted = [v for r in reports for v in r.sources if v.verdict == REFUTES]
    lines += ["", f"{len(refuted)} refutation(s), each a question for a person:"]
    lines += [f"  {v.slug}: records {v.recorded!r}; {v.route} {v.artifact} reads {v.observed!r} ({v.fetched_at[:10]})"
              for v in refuted]
    return "\n".join(lines)


def main(argv: list[str] | None = None, root: Path | None = None,
         github_rows: list[dict] | None = None, hf_rows: list[dict] | None = None) -> int:
    root = root or ROOT
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", type=Path, metavar="PATH", help="write the full per-source report here")
    parser.add_argument("--rows-github", type=Path, help="read signal_github rows from a JSON file instead of live")
    parser.add_argument("--rows-huggingface", type=Path, help="read signal_huggingface rows from a JSON file")
    args = parser.parse_args(argv)

    if github_rows is not None or hf_rows is not None or args.rows_github or args.rows_huggingface:
        github_rows = github_rows if github_rows is not None else (
            json.loads(args.rows_github.read_text()) if args.rows_github else [])
        hf_rows = hf_rows if hf_rows is not None else (
            json.loads(args.rows_huggingface.read_text()) if args.rows_huggingface else [])
        problems = {d: ["rows were supplied from a file, so no run can be attributed to them"]
                    for d in ("signal_github", "signal_huggingface")}
    else:
        github_rows, hf_rows, problems = live_rows()
    bound = {
        GITHUB: not problems.get("signal_github"),
        HF_MODEL: not problems.get("signal_huggingface"),
        HF_DATASET: not problems.get("signal_huggingface"),
    }
    reports, skipped = build_report(
        _load_dir(root / "sources" / "products"), _load_dir(root / "sources" / "scores"),
        index_rows(github_rows, hf_rows), bound, root,
    )
    print(render(reports, skipped, problems))
    if args.json:
        args.json.write_text(json.dumps({
            "bindings": problems,
            "products": [{**dataclasses.asdict(r), "sources": [dataclasses.asdict(v) for v in r.sources]}
                         for r in reports],
        }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
