"""Sync the README stat badges to the live source counts.

The badges (`categories`, `organizations`, `products`) are derived, not
hand-maintained: run this and they match `sources/` + the serialized payload.
Invoked by the regenerate workflow on merge to `main`, so the counts never drift.

    uv run python -m build.update_readme

Writes `README.md` in place, only when a number changed. Idempotent.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
PAYLOAD = ROOT / "build" / "notebook_data.json"


def counts() -> dict[str, int]:
    """The three figures shown as README badges."""
    n_total = json.loads(PAYLOAD.read_text())["n_total"]
    orgs = len(list((ROOT / "sources" / "organizations").glob("*.yaml")))
    cats = len(list((ROOT / "sources" / "categories").glob("*.yaml")))
    return {"products": n_total, "organizations": orgs, "categories": cats}


def _apply(text: str, metric: str, n: int) -> str:
    # shields.io image URL: .../badge/<metric>-<number>-<color>
    text = re.sub(rf"(badge/{metric}-)\d+(-)", rf"\g<1>{n}\g<2>", text)
    # accessible alt text: alt="<number> <metric>"
    text = re.sub(rf'(alt=")\d+( {metric}")', rf"\g<1>{n}\g<2>", text)
    return text


def main() -> int:
    original = README.read_text()
    updated = original
    for metric, n in counts().items():
        updated = _apply(updated, metric, n)
    if updated != original:
        README.write_text(updated)
        print(f"Updated README badges: {counts()}")
    else:
        print(f"README badges already current: {counts()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
