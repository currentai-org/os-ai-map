"""An axis cannot be both held in the verification queue and carrying a confirmation date.

`sources/verification_queue.yaml` holds axes a re-read opened, worked, and could not settle.
`last_verified` means the axis WAS confirmed. The two are mutually exclusive: a held axis is
by definition not confirmed, so it must not carry a date (it falls back to its commit date).

This existed as drift once — eight axes were re-fetched on 2026-08-13, dated, and left in the
hold queue with unresolved reasons, so the corpus claimed both at once. This gate rejects that
state, per the "never both" rule in docs/workflows/refresh-category.md.
"""

from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent


def test_no_axis_is_both_held_and_verified():
    queue = yaml.safe_load((REPO / "sources" / "verification_queue.yaml").read_text())
    held = (queue or {}).get("held") or {}
    problems = []
    for slug, axes in held.items():
        score_file = REPO / "sources" / "scores" / f"{slug}.yaml"
        if not score_file.exists():
            problems.append(f"{slug}: held in queue but no score file")
            continue
        score = yaml.safe_load(score_file.read_text()) or {}
        for axis in axes:
            axis_data = score.get(axis) or {}
            if axis_data.get("last_verified") is not None:
                problems.append(
                    f"{slug}.{axis}: held in verification_queue.yaml AND carries "
                    f"last_verified {axis_data['last_verified']!r} — a held axis is not confirmed"
                )
    assert not problems, "held-and-verified contradictions:\n" + "\n".join(problems)
