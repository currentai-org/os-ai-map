"""Evidence status of a coverage entry: provisional, estimated or unresolved.

Every depth band says how it was established (R-2026-11-02-e, -t):

- provisional: derived from item counts and the task family's stated assumptions;
- estimated: derived from a task-appropriate statistical procedure, recorded on the entry as a
  `precision` block that meets R-2026-11-02-f;
- unresolved: not enough information to assign even a provisional band.

This module decides that status for one `capability.language_coverage` entry and checks a
`precision` block. It computes no band: the depth ladder does, and publishes the status beside
every task, language and dataset band it derives (R-2026-11-02-e). docs/reference/capability.md,
"Evidence status", is normative.

Usage:
    uv run python -m build.evidence_status sources/scores/flores-plus.yaml
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

# Task families with a measurement model under R-2026-11-02-e, so a count gives a provisional
# band. Every other task class stays unresolved until a ruling gives it a model: sequence labeling
# (F1 over entities, not the sentences recorded) and speech (D3, R-2026-11-02-l) are ruled
# unresolved, and language identification, retrieval, safety, transliteration and
# vision-language have not been ruled on (R-2026-11-02-b: a task without a defensible model stays
# unresolved). question_answering is read with reading comprehension, the family R-2026-11-02-e
# names for XQuAD and TyDi QA.
COUNT_MODEL_TASKS: frozenset[str] = frozenset({
    "machine_translation",
    "text_classification",
    "natural_language_inference",
    "reasoning",
    "knowledge_exam",
    "reading_comprehension",
    "question_answering",
    "instruction_following",
    "text_generation",
    "summarization",
})

# The units a count model reads. Hours, words and tokens are not item counts: hours stand in for
# words, not speakers, and tokens are not the unit any model above scores.
COUNT_MODEL_UNITS: frozenset[str] = frozenset({"items", "questions", "sentences", "documents",
                                               "utterances"})

# Estimation methods approved by ruling, keyed by method id, each with the task classes it
# applies to. Empty: each task family's procedure needs its own ruling, backed by a calibration
# example comparing provisional and estimated bands (R-2026-11-02-f). A ruling that approves one
# adds it here in the same PR that cites the ruling.
APPROVED_METHODS: dict[str, frozenset[str]] = {}

QUALIFYING = {"native", "human_translated", "post_edited"}
MEASURED_ZERO = {"machine_translated", "generated"}


@dataclass(frozen=True)
class EntryStatus:
    status: str  # provisional | estimated | unresolved
    reason: str  # count_model | measured_zero | estimate | no_measurement_model |
    #              unit_not_countable | depth_unknown


def _depth(entry: dict) -> str:
    """measured, zero or unknown, by the provenance rule of R-2026-11-03-b.

    Machine translation the cited source says people reviewed (`human_validated: true`) counts;
    its provenance stays `machine_translated`. Generated items never count, reviewed or not.
    """
    if entry.get("count") == 0 and "provenance" not in entry:
        return "zero"  # a documented zero
    prov = entry.get("provenance")
    if prov in QUALIFYING:
        return "measured"
    if prov == "machine_translated" and entry.get("human_validated") is True:
        return "measured"
    if prov in MEASURED_ZERO:
        return "zero"
    if prov == "mixed" and "qualifying_count" in entry:
        return "measured" if entry["qualifying_count"] else "zero"
    return "unknown"


def entry_status(entry: dict, approved: dict[str, frozenset[str]] | None = None) -> EntryStatus | None:
    """The evidence status of one coverage entry, or None for an entry that is not counted.

    Only official-evaluation entries count toward depth (R-2026-11-01-d). Order: unknown depth is
    unresolved whatever else the entry carries; a task family or unit without a model is
    unresolved, a zero included, since a family without a model stays unresolved
    (R-2026-11-02-b, -l); a measured zero is then provisional; a valid estimate under an approved
    method is estimated; otherwise the count gives a provisional band.
    """
    approved = APPROVED_METHODS if approved is None else approved
    if not entry.get("official_eval"):
        return None
    depth = _depth(entry)
    if depth == "unknown":
        return EntryStatus("unresolved", "depth_unknown")
    if entry.get("task") not in COUNT_MODEL_TASKS:
        return EntryStatus("unresolved", "no_measurement_model")
    if entry.get("unit") not in COUNT_MODEL_UNITS:
        return EntryStatus("unresolved", "unit_not_countable")
    if depth == "zero":
        return EntryStatus("provisional", "measured_zero")
    precision = entry.get("precision")
    if precision and not precision_errors(entry, "", approved=approved):
        return EntryStatus("estimated", "estimate")
    return EntryStatus("provisional", "count_model")


def precision_errors(entry: dict, where: str, cited: set[str] | None = None,
                     approved: dict[str, frozenset[str]] | None = None,
                     today: date | None = None) -> list[str]:
    """What keeps an entry's `precision` block from establishing an estimated band (R-2026-11-02-f).

    `cited` is the set of `capability.sources` URLs; when given, every URL the block cites must be
    one of them, as for the entry's own `cites`.
    """
    if "precision" not in entry:
        return []
    precision = entry["precision"]
    if not isinstance(precision, dict):
        # The hook runs before the schema reports shapes, so a malformed block is reported here
        # rather than allowed to raise.
        return [f"{where}: `precision` must be a mapping"]
    approved = APPROVED_METHODS if approved is None else approved
    today = today or date.today()
    errors: list[str] = []

    if not entry.get("official_eval"):
        errors.append(f"{where}: carries `precision` but is not an official evaluation split; only "
                      f"the official split counts toward depth")
    if _depth(entry) != "measured":
        errors.append(f"{where}: carries `precision` but its qualifying depth is not established "
                      f"(provenance unknown, or a measured zero); an interval cannot stand in for "
                      f"provenance")
    method = precision.get("method")
    if not isinstance(method, str) or method not in approved:
        errors.append(f"{where}: precision method {method!r} has no approving ruling. Each task "
                      f"family's estimation procedure is approved by its own ruling, with a "
                      f"calibration example (R-2026-11-02-f); until then the entry stays provisional")
    elif entry.get("task") not in approved[method]:
        errors.append(f"{where}: precision method {method!r} is not approved for task "
                      f"{entry.get('task')!r}")

    runs = precision.get("runs")
    if not isinstance(runs, list):
        errors.append(f"{where}: precision.runs must be a list of runs")
        runs = []
    families = Counter(r["model_family"] for r in runs
                       if isinstance(r, dict) and isinstance(r.get("model_family"), str))
    if len(runs) < 2 or len(families) < 2:
        errors.append(f"{where}: an estimate needs runs from at least two different model families; "
                      f"checkpoints of one family do not count (R-2026-11-02-f)")
    for i, run in enumerate(runs):
        interval = run.get("interval") if isinstance(run, dict) else None
        low, high = interval if isinstance(interval, list) and len(interval) == 2 else (None, None)
        if not (isinstance(low, (int, float)) and isinstance(high, (int, float))
                and not isinstance(low, bool) and not isinstance(high, bool)
                and 0 <= low <= high <= 100):
            errors.append(f"{where}: precision.runs[{i}]: interval must be [low, high] on the 0 to "
                          f"100 score, with low <= high")

    raw = precision.get("evidence_date")
    try:
        when = date.fromisoformat(str(raw))
        if when > today:
            errors.append(f"{where}: precision.evidence_date {when} is later than today ({today})")
    except ValueError:
        errors.append(f"{where}: precision.evidence_date {raw!r} is not an ISO date")

    if not isinstance(precision.get("cites"), list) or not precision.get("cites"):
        errors.append(f"{where}: precision.cites must list the capability.sources urls for the "
                      f"procedure and the per-item results it read")
    if cited is not None:
        urls = [u for u in precision.get("cites") or [] if isinstance(u, str)] \
            if isinstance(precision.get("cites"), list) else []
        for run in runs:
            if isinstance(run, dict) and isinstance(run.get("cites"), list):
                urls += [u for u in run["cites"] if isinstance(u, str)]
        for url in urls:
            if url not in cited:
                errors.append(f"{where}: precision cites {url!r}, which is not the url of any "
                              f"capability.sources entry")
    return errors


def widest_margin(precision: dict) -> float | None:
    """The widest 95% half-width among the runs, the figure that sets an estimated band."""
    runs = precision.get("runs") if isinstance(precision, dict) else None
    widths = [(r["interval"][1] - r["interval"][0]) / 2 for r in runs or []
              if isinstance(r, dict) and isinstance(r.get("interval"), list) and len(r["interval"]) == 2]
    return max(widths) if widths else None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("score", type=Path, help="a sources/scores/<slug>.yaml file")
    args = ap.parse_args()
    cap = (yaml.safe_load(args.score.read_text()) or {}).get("capability") or {}
    tally: Counter = Counter()
    for entry in cap.get("language_coverage") or []:
        s = entry_status(entry)
        if s is not None:
            tally[(s.status, s.reason)] += 1
    for (status, reason), n in sorted(tally.items()):
        print(f"{status:12s} {reason:22s} {n}")


if __name__ == "__main__":
    main()
