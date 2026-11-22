"""The proposals bridge: platform proposals in, one labeled pull request per kind out.

Why it exists. Platform models and agents can observe, compare and rank, but nothing on the
platform can write to this repository, and ADR-004 says only a deterministic script writes to
`sources/` and only a person merges. So platform producers write rows to a proposals table, and
this module, run daily by `.github/workflows/proposals.yml`, reads them, applies each with the
repository's own tooling, and writes the report the workflow turns into the pull request body.

A proposal is a request, never the change. Nothing in a row is copied into `sources/`: the
handler for each kind re-derives what it writes, so a wrong or stale proposal costs a fetch and
nothing else. The one kind today is `redate`. Its handler re-reads the product's cited sources
with `build.reverify.reverify_product` and stamps only what that independent reading confirms,
under the same rules and refusals as the weekly re-verification (ruling R-2026-11-21-b; the
openness-only refusal of #445 binds here too). What the producer says it saw is shown to the
reviewer and decides nothing.

State is derived, never stored. A `redate` proposal whose axis already carries a
`last_verified` on or after the proposal's `observed_at` is current and is skipped, so the same
row read on consecutive days, or after its pull request merged, applies nothing twice.

Every proposal ends in exactly one outcome, and the report counts them apart:

    applied          the applier's own reading confirmed it and the file changed
    not_confirmed    the applier read the sources and could not confirm it; nothing written
    already_current  the axis was verified on or after the observation; nothing to do
    rejected         the row fails the schema, names no known product, or asks for an axis
                     the handler refuses

Usage:
    uv run python -m build.proposals apply --kind redate --report proposals-report.json
    uv run python -m build.proposals apply --kind redate --from-file proposals.jsonl --dry-run
    uv run python -m build.proposals summarize proposals-report.json   # the PR body
    uv run python -m build.proposals label redate                      # the PR's one label

The table's columns, how a producer assigns `proposal_id`, and how to switch the bridge on are
in `docs/operations/proposals-bridge.md`. The row shape is `docs/schemas/proposal.schema.json`.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import jsonschema
import yaml

from build import reverify
from build.check_freshness import parse_date

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "docs" / "schemas" / "proposal.schema.json"

#: The platform proposals table. Its contract and read-only mirror are in
#: warehouse/dependencies.yaml and warehouse/models/proposals/proposals.sql.
TABLE = "currentai.proposals.proposals"

#: The ADR-004 label each kind's pull request carries. A kind with no label here cannot be
#: applied: ADR-004 allows a bot PR exactly one label, from a closed list.
KIND_LABELS: dict[str, str] = {"redate": "freshness"}

APPLIED, NOT_CONFIRMED, ALREADY_CURRENT, REJECTED = (
    "applied", "not_confirmed", "already_current", "rejected")
OUTCOMES = (APPLIED, NOT_CONFIRMED, ALREADY_CURRENT, REJECTED)

_TABLE_RE = re.compile(r"^[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*$")


@dataclass(frozen=True)
class Outcome:
    proposal_id: str
    product_slug: str
    axis: str
    producer: str
    outcome: str
    reason: str = ""


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def read_file(path: Path) -> list[dict]:
    """Proposals from a JSON Lines file, one proposal per line, in the schema's shape."""
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _present(value: object) -> bool:
    """False for None and for the NaN pandas uses for a null in a text column."""
    return value is not None and not (isinstance(value, float) and math.isnan(value))


def row_to_proposal(row: dict) -> dict:
    """A flat warehouse row as a proposal in the schema's shape.

    The table stores `producer` as two columns and `evidence` as JSON text, because a nested
    column is awkward to write from a SQL model. An `evidence` value that is not valid JSON is
    passed through as the string, so the schema rejects the row rather than this crashing.
    """
    producer = {"model": row.get("producer_model")}
    if _present(row.get("producer_revision")):
        producer["revision"] = str(row["producer_revision"])
    evidence = row.get("evidence")
    if isinstance(evidence, str):
        try:
            evidence = json.loads(evidence)
        except json.JSONDecodeError:
            pass
    proposal = {
        "proposal_id": row.get("proposal_id"),
        "kind": row.get("kind"),
        "product_slug": row.get("product_slug"),
        "axis": row.get("axis"),
        "observed_at": str(row.get("observed_at"))[:10] if _present(row.get("observed_at")) else None,
        "producer": producer,
        "evidence": evidence,
    }
    if _present(row.get("created_at")):
        proposal["created_at"] = str(row["created_at"])
    return proposal


def table_query(table: str, kind: str, since_days: int) -> str:
    """The read of one kind's recent rows. Refuses a table name that is not org.dataset.table."""
    if not _TABLE_RE.match(table):
        raise ValueError(f"not a three-part table name: {table!r}")
    if kind not in KIND_LABELS:
        raise ValueError(f"unknown proposal kind: {kind!r}")
    return (
        "SELECT proposal_id, kind, product_slug, axis, CAST(observed_at AS VARCHAR) AS observed_at, "
        "producer_model, producer_revision, evidence, CAST(created_at AS VARCHAR) AS created_at "
        f"FROM {table} WHERE kind = '{kind}' "
        f"AND created_at >= current_timestamp - INTERVAL '{int(since_days)}' DAY "
        "ORDER BY created_at, proposal_id"
    )


def read_table(table: str, kind: str, since_days: int) -> list[dict]:
    from build.warehouse import query

    return [row_to_proposal(row) for row in query(table_query(table, kind, since_days))]


def schema_error(proposal: object, schema: dict) -> str | None:
    """Why a row fails the schema, or None. The best single error, not the whole cascade.

    Formats are checked, so `observed_at: 2026-99-99` is refused here rather than matching the
    pattern and failing later as a crash.
    """
    error = jsonschema.exceptions.best_match(
        jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER,
        ).iter_errors(proposal))
    if error is None:
        return None
    where = "/".join(str(p) for p in error.absolute_path)
    return f"{where}: {error.message}" if where else error.message


def _producer_label(proposal: dict) -> str:
    producer = proposal.get("producer") if isinstance(proposal.get("producer"), dict) else {}
    model = str(producer.get("model") or "?")
    return f"{model}@{producer['revision']}" if producer.get("revision") else model


def _last_verified(root: Path, slug: str, axis: str) -> date | None:
    score = yaml.safe_load((root / "sources" / "scores" / f"{slug}.yaml").read_text()) or {}
    block = score.get(axis)
    if isinstance(block, dict) and block.get("last_verified"):
        return parse_date(block["last_verified"])
    return None


def apply_redate(root: Path, proposals: list[dict], today: date, *, dry_run: bool = False,
                 fetch=None, pace: float = 0.0, body_dir: Path | None = None,
                 schema: dict | None = None) -> dict:
    """Apply `redate` proposals and return the report.

    Proposals for the same product and axis share one reading: the product is re-read once, and
    each of them takes the outcome that reading gives. Rows of another kind are left for that
    kind's run and are not counted here.
    """
    schema = schema or load_schema()
    outcomes: list[Outcome] = []
    due: dict[tuple[str, str], list[dict]] = {}
    seen_ids: set[str] = set()
    for proposal in proposals:
        if not isinstance(proposal, dict) or proposal.get("kind") != "redate":
            continue
        pid = str(proposal.get("proposal_id") or "")
        if pid and pid in seen_ids:
            continue
        seen_ids.add(pid)
        slug, axis = str(proposal.get("product_slug") or ""), str(proposal.get("axis") or "")

        def reject(reason: str) -> None:
            outcomes.append(Outcome(pid, slug, axis, _producer_label(proposal), REJECTED, reason))

        error = schema_error(proposal, schema)
        if error:
            reject(f"schema: {error}")
            continue
        refusal = reverify.axes_refusal((axis,))
        if refusal:
            reject(refusal)
            continue
        if not (root / "sources" / "scores" / f"{slug}.yaml").exists():
            reject("no score file for this product")
            continue
        verified = _last_verified(root, slug, axis)
        if verified is not None and verified >= parse_date(proposal["observed_at"]):
            outcomes.append(Outcome(pid, slug, axis, _producer_label(proposal), ALREADY_CURRENT,
                                    f"last_verified {verified.isoformat()}"))
            continue
        due.setdefault((slug, axis), []).append(proposal)

    products: list[dict] = []
    body_dir = body_dir or Path(tempfile.mkdtemp(prefix="os-ai-map-proposals-"))
    kwargs = {"pace": pace, "body_dir": body_dir}
    if fetch is not None:
        kwargs["fetch"] = fetch
    for (slug, axis), group in sorted(due.items()):
        result = reverify.reverify_product(root, slug, today, axes=(axis,), **kwargs)
        if not dry_run:
            reverify.apply(root, slug, result, today)
        products.append({
            "slug": slug, "stamped": result.stamped, "drifted": result.drifted,
            "refuted": result.refuted, "transient": result.transient, "skipped": result.skipped,
            "unchanged": result.unchanged,
            "reconfirmed_by_shows": result.reconfirmed_by_shows,
            "reconfirmed_by_spdx": result.reconfirmed_by_spdx,
        })
        confirmed = axis in result.stamped
        reason = "" if confirmed else _unconfirmed_reason(result)
        for proposal in group:
            outcomes.append(Outcome(str(proposal["proposal_id"]), slug, axis,
                                    _producer_label(proposal),
                                    APPLIED if confirmed else NOT_CONFIRMED, reason))

    return {
        "kind": "redate",
        "label": KIND_LABELS["redate"],
        "today": today.isoformat(),
        "dry_run": dry_run,
        "proposals": [o.__dict__ for o in outcomes],
        "products": products,
    }


def _unconfirmed_reason(result: reverify.ProductResult) -> str:
    parts = [f"{len(items)} {name}" for name, items in (
        ("drifted", result.drifted), ("refuted", result.refuted),
        ("transient", result.transient), ("skipped", result.skipped)) if items]
    return ", ".join(parts) or "no recorded dimension to confirm"


HANDLERS = {"redate": apply_redate}


def summary_markdown(report: dict) -> str:
    """The pull request body: proposals by outcome, then the applier's own reading."""
    proposals = report["proposals"]
    counts = {name: sum(p["outcome"] == name for p in proposals) for name in OUTCOMES}
    producers = sorted({p["producer"] for p in proposals})
    lines = [
        f"Applied from the platform proposals table by the daily bridge (`build.proposals`, kind "
        f"`{report['kind']}`). A proposal is a request: every change below comes from the "
        "applier's own fetch of the cited sources, not from the proposal.",
        "",
        f"{len(proposals)} proposal(s) read from {', '.join(f'`{p}`' for p in producers) or 'no producer'}:",
        "",
        f"- **{counts[APPLIED]} applied.** The applier's reading confirmed every recorded dimension.",
        f"- **{counts[NOT_CONFIRMED]} not confirmed.** The applier could not confirm the claim; the "
        "axis is untouched.",
        f"- **{counts[ALREADY_CURRENT]} already current.** The axis was verified on or after the "
        "observation.",
        f"- **{counts[REJECTED]} rejected.** The row failed the schema, named no known product, or "
        "asked for an axis this kind may not touch.",
        "",
        "This pull request updates itself daily until it merges.",
    ]
    held = [p for p in proposals if p["outcome"] in (NOT_CONFIRMED, REJECTED)]
    if held:
        lines += ["", "<details><summary>Proposals not applied</summary>", "", "```"]
        lines += [f"{p['outcome']:14} {p['product_slug'] or '?':32} {p['proposal_id']}  {p['reason']}"
                  for p in held]
        lines += ["```", "", "</details>"]
    if report["products"]:
        lines += ["", "## The applier's reading", "",
                  reverify.summary_markdown(
                      {"products": report["products"]},
                      selection=f"the {len(report['products'])} product(s) the proposals named",
                  ).rstrip()]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    root = root or ROOT
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    apply_p = sub.add_parser("apply", help="read proposals of one kind and apply them")
    apply_p.add_argument("--kind", required=True, choices=sorted(HANDLERS))
    source = apply_p.add_mutually_exclusive_group()
    source.add_argument("--from-table", metavar="ORG.DATASET.TABLE", default=TABLE,
                        help=f"the proposals table (default {TABLE})")
    source.add_argument("--from-file", type=Path, metavar="JSONL")
    apply_p.add_argument("--since-days", type=int, default=7,
                         help="with --from-table, read rows created in the last N days (default 7)")
    apply_p.add_argument("--report", type=Path, default=None)
    apply_p.add_argument("--dry-run", action="store_true")
    apply_p.add_argument("--today", default=None)
    apply_p.add_argument("--pace", type=float, default=1.0, help="seconds between fetches")

    summarize_p = sub.add_parser("summarize", help="print the PR body of a saved report")
    summarize_p.add_argument("report", type=Path)

    label_p = sub.add_parser("label", help="print the ADR-004 label a kind's PR carries")
    label_p.add_argument("kind", choices=sorted(KIND_LABELS))

    args = parser.parse_args(argv)
    if args.command == "summarize":
        print(summary_markdown(json.loads(args.report.read_text())), end="")
        return 0
    if args.command == "label":
        print(KIND_LABELS[args.kind])
        return 0

    proposals = (read_file(args.from_file) if args.from_file
                 else read_table(args.from_table, args.kind, args.since_days))
    today = parse_date(args.today) if args.today else date.today()
    report = HANDLERS[args.kind](root, proposals, today, dry_run=args.dry_run, pace=args.pace)
    if args.report:
        args.report.write_text(json.dumps(report, indent=2))
    counts = {name: sum(p["outcome"] == name for p in report["proposals"]) for name in OUTCOMES}
    print(" ".join(f"{name}={count}" for name, count in counts.items()))
    for p in report["proposals"]:
        if p["outcome"] == REJECTED:
            print(f"  REJECTED {p['proposal_id']}: {p['reason']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
