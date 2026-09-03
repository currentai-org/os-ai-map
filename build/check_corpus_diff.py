"""The semantic-diff gate: what a PR does to the published narrative.

Compares HEAD's committed build/notebook_data.json against the freshly serialized payload
and reports, per category, the stage, gap set, product count, and tier deltas. A stage
move fails the gate unless --allow-stage-move is passed (CI passes it when the PR carries
the `stage-move` label), so a stage can only move on purpose. Separately, every axis
assessment row belonging to a product whose source files the PR did not touch must be
byte-identical before and after; a change there is a silent rewrite and fails the gate.

This replaces the corpus-wide digest pins that used to live in tests/ (build/goldens.py):
they caught silent rewrites by hashing everything, which made every product PR collide.
This gate catches the same class of change per row and per PR instead.

Output: a markdown review sheet (--sheet PATH, default stdout) meant for the PR body or the
job summary. It is the reviewer's first read.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_PRODUCT_PATH = re.compile(r"^sources/(?:scores|products)/([a-z0-9][a-z0-9-]*)\.yaml$")


@dataclass
class CategoryDelta:
    stage_before: int | None
    stage_after: int | None
    gaps_before: list[str]
    gaps_after: list[str]
    products_added: list[str]
    products_removed: list[str]
    tier_changes: list[tuple[str, str | None, str | None]] = field(default_factory=list)

    @property
    def stage_moved(self) -> bool:
        return self.stage_before != self.stage_after or sorted(self.gaps_before) != sorted(self.gaps_after)


@dataclass
class CorpusDiff:
    categories: dict[str, CategoryDelta]

    @property
    def stage_moves(self) -> list[str]:
        return [f"{c}: {d.stage_before} -> {d.stage_after}, gaps {d.gaps_before} -> {d.gaps_after}"
                for c, d in sorted(self.categories.items()) if d.stage_moved]


def _index(payload: dict) -> dict[str, dict]:
    return payload.get("categories") or {}


def diff_payloads(before: dict, after: dict) -> CorpusDiff:
    out: dict[str, CategoryDelta] = {}
    b_cats, a_cats = _index(before), _index(after)
    for cid in sorted(set(b_cats) | set(a_cats)):
        b, a = b_cats.get(cid, {}), a_cats.get(cid, {})
        b_prod = {p["slug"]: p for p in b.get("products", [])}
        a_prod = {p["slug"]: p for p in a.get("products", [])}
        tiers = [(s, b_prod[s].get("tier"), a_prod[s].get("tier"))
                 for s in sorted(set(b_prod) & set(a_prod))
                 if b_prod[s].get("tier") != a_prod[s].get("tier")]
        out[cid] = CategoryDelta(
            stage_before=(b.get("stage") or {}).get("num"),
            stage_after=(a.get("stage") or {}).get("num"),
            gaps_before=list(b.get("gaps") or []),
            gaps_after=list(a.get("gaps") or []),
            products_added=sorted(set(a_prod) - set(b_prod)),
            products_removed=sorted(set(b_prod) - set(a_prod)),
            tier_changes=tiers,
        )
    return CorpusDiff(categories=out)


def products_from_paths(paths: list[str]) -> set[str]:
    return {m.group(1) for p in paths for m in [_PRODUCT_PATH.match(p)] if m}


def touched_products(root: Path, base_ref: str) -> set[str]:
    names = subprocess.run(["git", "diff", "--name-only", f"{base_ref}...HEAD"],
                           cwd=root, capture_output=True, text=True, check=True).stdout.split()
    return products_from_paths(names)


def _rows_at(root: Path, ref: str | None) -> dict[str, str]:
    """Axis-assessment rows keyed by product|axis, canonicalized, for the tree at ref (None = worktree)."""
    from build import axis_assessments
    if ref is None:
        rows = axis_assessments.resolve(root, allow_dirty=True)
    else:
        # A temporary worktree at ref keeps the comparison honest without touching the checkout.
        tmp = root / ".ccd-worktree"
        subprocess.run(["git", "worktree", "add", "--detach", str(tmp), ref], cwd=root, check=True,
                       capture_output=True)
        try:
            rows = axis_assessments.resolve(tmp, allow_dirty=True)
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", str(tmp)], cwd=root, check=True,
                           capture_output=True)
    return {f"{r['product_slug']}|{r['axis']}": axis_assessments.canonical_row(r) for r in rows}


def compare_rows(before: dict[str, str], after: dict[str, str], touched: set[str]) -> list[str]:
    out = []
    for key in sorted(set(before) & set(after)):
        slug = key.split("|", 1)[0]
        if slug not in touched and before[key] != after[key]:
            out.append(f"{key} changed but sources/{{scores,products}}/{slug}.yaml did not")
    return out


def untouched_row_changes(root: Path, base_ref: str, touched: set[str]) -> list[str]:
    return compare_rows(_rows_at(root, base_ref), _rows_at(root, None), touched)


def render_sheet(diff: CorpusDiff, row_changes: list[str]) -> str:
    lines = ["## Review sheet", "", "| category | stage | gaps | products | tier changes |", "|---|---|---|---|---|"]
    for cid, d in sorted(diff.categories.items()):
        stage = f"{d.stage_before} -> {d.stage_after}" if d.stage_moved else f"{d.stage_after}"
        gaps = f"{d.gaps_before} -> {d.gaps_after}" if d.stage_moved else f"{d.gaps_after}"
        n = f"+{len(d.products_added)} / -{len(d.products_removed)}"
        tiers = "; ".join(f"{s}: {b} -> {a}" for s, b, a in d.tier_changes) or "none"
        if d.products_added or d.products_removed or d.stage_moved or d.tier_changes:
            lines.append(f"| {cid} | {stage} | {gaps} | {n} | {tiers} |")
    lines += ["", f"stage moves: {', '.join(diff.stage_moves) or 'none'}", ""]
    lines.append("untouched-product row changes: " + ("none" if not row_changes else ""))
    lines += [f"- {c}" for c in row_changes]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    root = root or ROOT
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base", required=True, help="git ref of the base (e.g. origin/main)")
    p.add_argument("--allow-stage-move", action="store_true")
    p.add_argument("--sheet", type=Path, default=None)
    args = p.parse_args(argv)

    before_txt = subprocess.run(["git", "show", f"{args.base}:build/notebook_data.json"], cwd=root,
                                capture_output=True, text=True, check=True).stdout
    before = json.loads(before_txt)
    after = json.loads((root / "build" / "notebook_data.json").read_text())
    diff = diff_payloads(before, after)
    touched = touched_products(root, args.base)
    row_changes = untouched_row_changes(root, args.base, touched)
    sheet = render_sheet(diff, row_changes)
    (args.sheet.write_text(sheet) if args.sheet else print(sheet))

    rc = 0
    if diff.stage_moves and not args.allow_stage_move:
        print("stage moved without the stage-move label:", *diff.stage_moves, sep="\n  ")
        rc = 1
    if row_changes:
        print("silent rewrites of untouched products:", *row_changes, sep="\n  ")
        rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
