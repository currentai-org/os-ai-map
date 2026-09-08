"""The withdrawal mechanism: how a product leaves the map when nothing replaced it.

A rename leaves an alias behind and every gate that watches slugs reads that alias map. A
withdrawal has nothing to alias onto, so until `sources/withdrawals.yaml` existed the only
safe reading of a deleted product file was "somebody deleted this by accident", and two gates
took it. These tests pin the three things that make a withdrawal a mechanism rather than a
sentence in a pull request:

  1. an entry is refused unless it is TRUE of the tree it sits in (build/validate.py),
  2. a withdrawn slug leaving the payload passes, and any other slug leaving still fails
     (build/check_retirement.py),
  3. a file a withdrawal names is accounted for as a deletion, and any other deleted file
     under sources/ still has to be archived (build/assets.py).

Each of the negative cases matters as much as the positive one: a mechanism that passes a
withdrawal by passing every deletion has not distinguished anything.
"""
import copy
import json
from pathlib import Path

import pytest
import yaml

import build.assets as A
import build.check_retirement as cr
import build.declaration_version as DV
import build.withdrawals as W
from build.validate import load_sources, validate_sources

ROOT = Path(__file__).resolve().parents[1]


def _doc() -> dict:
    return copy.deepcopy(yaml.safe_load((ROOT / "sources" / "withdrawals.yaml").read_text()))


def _entry() -> dict:
    return _doc()["withdrawals"][0]


# --- the committed record ---------------------------------------------------------

def test_the_committed_withdrawals_file_is_coherent():
    """The real record passes its own checks against the real tree."""
    data = load_sources(ROOT)
    assert W.problems(
        data["withdrawals"],
        products=data["products"],
        scores=data["scores"],
        categories=data["categories"],
        organizations=data["organizations"],
    ) == []


def test_a_withdrawn_slug_is_gone_from_every_live_surface():
    data = load_sources(ROOT)
    for slug in W.withdrawn_slugs(ROOT):
        assert slug not in data["products"], f"{slug} still has a product file"
        assert slug not in data["scores"], f"{slug} still has a score file"
        assert not (ROOT / "sources" / "products" / f"{slug}.yaml").exists()


def test_withdrawals_is_classified_as_a_non_declaration_input():
    """A ruling about what left is not a declaration of what is here. Unclassified, the
    inventory gate fails; folded into the digest, writing down a reason would re-key every
    declaration_version_id corpus-wide."""
    assert "withdrawals.yaml" in DV.NON_DECLARATION_INPUTS
    assert "withdrawals.yaml" not in DV.DECLARATION_INPUTS


# --- validate.py: an entry must be true of its tree -------------------------------

@pytest.mark.parametrize(
    "label,mutate,expected",
    [
        ("alias_target", lambda e: e.__setitem__("alias", "some-other-product"), "no successor"),
        ("alias_omitted", lambda e: e.pop("alias"), "required and must be null"),
        ("no_removed_files", lambda e: e.__setitem__("removed_files", []),
         "removed_files does not name"),
        ("removed_file_still_present",
         lambda e: e.__setitem__("removed_files", e["removed_files"] + ["sources/taxonomy.yaml"]),
         "still exists"),
    ],
    ids=lambda v: v if isinstance(v, str) else "",
)
def test_a_dishonest_withdrawal_entry_is_refused(label, mutate, expected):
    doc = _doc()
    mutate(doc["withdrawals"][0])
    problems = W.problems(doc)
    assert any(expected in p for p in problems), f"{label}: expected {expected!r} in {problems}"


def test_a_withdrawal_whose_product_is_still_live_is_refused():
    """The check that stops a withdrawal from being a free pass: naming a slug in this file
    must not excuse a product that never left."""
    doc = _doc()
    slug = doc["withdrawals"][0]["slug"]
    problems = W.problems(
        doc,
        products={slug: {}},
        categories={"safeguards": {"products": [slug]}},
        organizations={"jigsaw": {"products": [slug]}},
    )
    assert any("still exists" in p for p in problems)
    assert any("category roster" in p for p in problems)
    assert any("organization roster" in p for p in problems)


def test_a_slug_that_is_both_withdrawn_and_aliased_is_refused():
    """One or the other. Both means somebody recorded a rename as a disappearance."""
    doc = _doc()
    slug = doc["withdrawals"][0]["slug"]
    problems = W.problems(doc, aliases={slug: "successor-product"})
    assert any("is a rename" in p for p in problems)


def test_the_same_slug_cannot_be_withdrawn_twice():
    doc = _doc()
    doc["withdrawals"].append(copy.deepcopy(doc["withdrawals"][0]))
    assert any("withdrawn twice" in p for p in W.problems(doc))


def test_an_unreadable_version_is_refused_rather_than_ignored():
    doc = _doc()
    doc["version"] = 2
    assert any("version" in p for p in W.problems(doc))


def test_validate_sources_surfaces_a_bad_withdrawal():
    """Wired in, not merely importable: the error reaches `uv run python -m build.validate`."""
    data = load_sources(ROOT)
    data = copy.deepcopy(data)
    data["withdrawals"]["withdrawals"][0]["alias"] = "something-else"
    assert any("withdrawal" in e for e in validate_sources(data))


# --- check_retirement: withdrawn passes, everything else still fails ---------------

def _payload(slugs, aliases=None) -> dict:
    return {
        "categories": {"c": {"products": [{"slug": s} for s in slugs]}},
        "aliases": {"products": aliases or {}, "organizations": {}},
    }


def test_unrouted_slugs_accounts_for_a_withdrawal_and_nothing_else():
    gone = {"withdrawn", "renamed", "vanished"}
    assert cr.unrouted_slugs(gone, {"renamed": "successor"}, {"withdrawn"}) == ["vanished"]


def test_check_retirement_passes_a_withdrawn_slug(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cr, "ROOT", tmp_path)
    _init(tmp_path)
    _commit_payload(tmp_path, _payload(["a", "b"]))
    (tmp_path / "build" / "notebook_data.json").write_text(json.dumps(_payload(["a"])))
    (tmp_path / "sources").mkdir(exist_ok=True)
    (tmp_path / "sources" / "withdrawals.yaml").write_text(
        yaml.safe_dump({"version": 1, "withdrawals": [{"slug": "b", "alias": None}]})
    )
    assert cr.main() == 0
    assert "1 withdrawn with no successor" in capsys.readouterr().out


def test_check_retirement_still_fails_a_slug_no_withdrawal_covers(tmp_path, monkeypatch, capsys):
    """The mechanism must not turn every deletion green."""
    monkeypatch.setattr(cr, "ROOT", tmp_path)
    _init(tmp_path)
    _commit_payload(tmp_path, _payload(["a", "b", "c"]))
    (tmp_path / "build" / "notebook_data.json").write_text(json.dumps(_payload(["a"])))
    (tmp_path / "sources").mkdir(exist_ok=True)
    (tmp_path / "sources" / "withdrawals.yaml").write_text(
        yaml.safe_dump({"version": 1, "withdrawals": [{"slug": "b", "alias": None}]})
    )
    assert cr.main() == 1
    err = capsys.readouterr().err
    assert "c" in err and "withdrawals.yaml" in err


def _init(root: Path) -> None:
    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=root, check=True, capture_output=True)


def _commit_payload(root: Path, payload: dict) -> None:
    import subprocess
    (root / "build").mkdir(parents=True, exist_ok=True)
    (root / "build" / "notebook_data.json").write_text(json.dumps(payload))
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-q", "-m", "p"],
        cwd=root, check=True, capture_output=True,
    )


# --- assets.py: the deletion completeness check ------------------------------------

def test_the_externalization_completeness_check_reads_the_withdrawal_record():
    """`sources/` sits in EXTERNALIZED_FILE_PREFIXES for one externalized asset, which made
    every product file undeletable. A withdrawal's `removed_files` is what accounts for the
    files it deleted -- an externalization receipt entry would claim they were externalized
    warehouse tables, which is false."""
    assert "sources/" in A.EXTERNALIZED_FILE_PREFIXES
    accounted = A.withdrawn_files()
    assert accounted, "the committed withdrawal should account for its deleted files"
    for path in accounted:
        assert not (ROOT / path).exists(), f"{path} is named as removed but is on disk"
        assert path not in {
            p for e in A.externalized() for p in (e.get("archived_source_sha256") or {})
        }, f"{path} should be accounted for as a withdrawal, not as an externalized table"
