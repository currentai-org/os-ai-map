"""Recompute the long-tail universe counts from the warehouse, and write them into the snapshot.

`sources/snapshots/long_tail.json` carries the numbers the map publishes about its own coverage:
how many repositories, models and packages it tracks, how many of the scored products came out of
that catalog, and how many catalog artifacts are still uncategorized. Every one of them used to be
typed in by hand after a batch.

That is the defect #545 established a rule for: a number the repo states about itself should be
computed and compared, never typed, and refreshing a stale one by hand has the same defect as
leaving it stale, because a number published in the present tense reads as a claim about now.
Measured before this script existed, the stored figures had drifted a long way -- repos short by
thousands against its own successor table, models against a source that had since tripled, and
packages against a filter written down nowhere and reproducible by nobody.

So the three slices are defined here, in SQL a reader can run, rather than in a curator's memory.

## The three slices, and why each is drawn this way

  * **repos** -- every repository in the GoodAI List discovery catalogue. This is the set the map
    draws head products from, and `signal_goodailist.repo_catalog` is its live successor to the
    retired `catalog.goodailist_repos` static upload.
  * **models** -- every Hugging Face model repo at or above `signal_hfhub.model_universe`'s
    declared 1,000-download floor. The floor is the model's own, documented where it is applied;
    an unfiltered Hub is millions of near-zero-download repos and is not a denominator anybody
    means.
  * **packages** -- every package PUBLISHED BY a repository in the discovery catalogue, through
    `oso.package_owners_v0`. The alternative considered was every package those repositories
    DEPEND ON, which is a different question and answers it badly: it counts `shebang-regex` and
    every other generic transitive dependency as an open source AI artifact, and measured about
    seven times larger for that reason. What a project ships is a fact about that project; what it
    installs is a fact about the ecosystem underneath it.

Two numbers say how much of the universe the map has already scored, and they are not the same
number because they are not the same grain.

  * **matched** counts universe ARTIFACTS a scored product already declares, across all three
    slices. It is what the uncategorized remainder subtracts.
  * **overlap** counts scored PRODUCTS that came out of the universe. It is what lets the
    published sentence separate products the map found by discovery from the closed and
    proprietary ones it went looking for deliberately.

Subtracting `overlap` from `total` mixes products into an artifact count. That was survivable
while repositories were the only slice; with three it leaves every scored product's model and
published package in the universe and reports them as not yet scored.

`universe` is deliberately not written. Nothing rendered it, and a stored number with no reader is
a maintenance surface with no payoff.

The roster-dependent counts -- `scored`, `scored_outside`, `uncategorized` -- are NOT written here.
`build.serialize.derived_long_tail_counts` computes those at build time from the published roster,
so they cannot drift from the products the payload actually carries.

Usage:
    uv run python -m build.sync_long_tail            # show the diff, write nothing
    uv run python -m build.sync_long_tail --write    # write it
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "sources" / "snapshots" / "long_tail.json"

#: Every repository in the discovery catalogue.
REPOS = "SELECT COUNT(*) AS n FROM currentai.signal_goodailist.repo_catalog"

#: Every Hub model at or above the universe model's declared download floor. The floor lives in
#: that model rather than here, so this query cannot disagree with it.
MODELS = "SELECT COUNT(*) AS n FROM currentai.signal_hfhub.model_universe"

#: Every package published by a repository in the discovery catalogue. Joined on the owner
#: artifact rather than the dependent one -- see the module docstring for why that is the
#: question worth asking.
PACKAGES = """
SELECT COUNT(DISTINCT p.package_artifact_source || '/' || p.package_artifact_name) AS n
FROM oso.package_owners_v0 AS p
JOIN currentai.signal_goodailist.repo_catalog AS r
  ON LOWER(p.package_owner_artifact_namespace || '/' || p.package_owner_artifact_name)
   = LOWER(r.repo)
"""

#: Universe artifacts that a scored product already declares, across all three slices.
#:
#: This is what "already in the gap map" means at the ARTIFACT grain, and it is what the
#: uncategorized remainder has to subtract. Counting only the repository slice — which the first
#: version of this module did — left every scored product's Hugging Face model and published
#: package sitting in the universe and reported as not yet scored.
MATCHED = """
SELECT COUNT(*) AS n FROM (
  SELECT DISTINCT 'repo/' || LOWER(r.repo) AS artifact
  FROM currentai.signal_goodailist.repo_catalog AS r
  JOIN currentai.registry.product_artifacts AS a
    ON a.artifact_kind = 'github' AND LOWER(a.artifact_id) = LOWER(r.repo)
  UNION ALL
  SELECT DISTINCT 'model/' || LOWER(m.hf_id)
  FROM currentai.signal_hfhub.model_universe AS m
  JOIN currentai.registry.product_artifacts AS a
    ON a.artifact_kind = 'huggingface_model' AND LOWER(a.artifact_id) = LOWER(m.hf_id)
  UNION ALL
  SELECT DISTINCT 'package/' || p.package_artifact_source || '/' || LOWER(p.package_artifact_name)
  FROM oso.package_owners_v0 AS p
  JOIN currentai.signal_goodailist.repo_catalog AS r
    ON LOWER(p.package_owner_artifact_namespace || '/' || p.package_owner_artifact_name)
     = LOWER(r.repo)
  JOIN currentai.registry.product_artifacts AS a
    ON LOWER(a.artifact_id) = LOWER(p.package_artifact_name)
   AND ((a.artifact_kind = 'pypi'   AND p.package_artifact_source = 'PIP')
     OR (a.artifact_kind = 'npm'    AND p.package_artifact_source = 'NPM')
     OR (a.artifact_kind = 'crates' AND p.package_artifact_source = 'RUST'))
)
"""

#: Scored products that came out of the universe, at the PRODUCT grain.
#:
#: Distinct from MATCHED, and the distinction is the bug that was here first: `total` counts
#: artifacts and this counts products, so subtracting one from the other mixes units. It was
#: survivable while repositories were the only slice and a product had roughly one of them. It
#: is not survivable now.
OVERLAP = """
SELECT COUNT(DISTINCT a.product_slug) AS n
FROM currentai.registry.product_artifacts AS a
WHERE (a.artifact_kind = 'github' AND LOWER(a.artifact_id) IN
        (SELECT LOWER(repo) FROM currentai.signal_goodailist.repo_catalog))
   OR (a.artifact_kind = 'huggingface_model' AND LOWER(a.artifact_id) IN
        (SELECT LOWER(hf_id) FROM currentai.signal_hfhub.model_universe))
"""


def measure(query) -> dict:
    """The five stored numbers, as of now. `query` is injected so tests need no warehouse."""
    repos = int(query(REPOS)[0]["n"])
    models = int(query(MODELS)[0]["n"])
    packages = int(query(PACKAGES)[0]["n"])
    return {
        "repos": repos,
        "models": models,
        "packages": packages,
        "total": repos + models + packages,
        "matched": int(query(MATCHED)[0]["n"]),
        "overlap": int(query(OVERLAP)[0]["n"]),
    }


def apply(snapshot: dict, counts: dict, today: str) -> dict:
    """The snapshot with its counts replaced and dated. `top` is left alone.

    `measured_on` is what makes the staleness checkable: `build/check_long_tail.py` reads it, and
    without it a stale block and a fresh one are indistinguishable from the file.
    """
    out = dict(snapshot)
    out["counts"] = dict(counts)
    out["measured_on"] = today
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--write", action="store_true", help="write the snapshot rather than only reporting")
    parser.add_argument("--today", default=date.today().isoformat())
    args = parser.parse_args(argv)

    from build.warehouse import query

    snapshot = json.loads(SNAPSHOT.read_text())
    before = snapshot.get("counts") or {}
    counts = measure(query)

    width = max(len(k) for k in set(before) | set(counts))
    print(f"{'':{width}}  {'stored':>12}  {'measured':>12}")
    for key in sorted(set(before) | set(counts)):
        was, now = before.get(key), counts.get(key)
        mark = " " if was == now else "~"
        was_s = f"{was:,}" if isinstance(was, int) else "-"
        now_s = f"{now:,}" if isinstance(now, int) else "dropped"
        print(f"{mark} {key:{width}}  {was_s:>12}  {now_s:>12}")

    if not args.write:
        print("\nnothing written; pass --write")
        return 0
    SNAPSHOT.write_text(json.dumps(apply(snapshot, counts, args.today), indent=2) + "\n")
    print(f"\nwrote {SNAPSHOT.relative_to(ROOT)}, measured_on {args.today}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
