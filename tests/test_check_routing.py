"""`source: null` in the routing table is a declaration, not a broken route.

Two adoption routes carry no machine source on purpose: `reported_traction`, the instrument
defined by having no count behind it, and `active_users`, a vendor-disclosed figure that no
endpoint serves. Both mark it with `hand_authored: true`.

Until 2026-08-15 `check_routing` read those nulls as "route names unknown source None" and
exited 1 on every invocation, so the two routes the table documents most carefully were the
two it called broken. It was also wired into none of the eight CI workflows, so nothing was
reading the failure — a gate that is both wrong and unrun cannot catch a real one.
"""

from __future__ import annotations

import yaml

from build.check_routing import ROOT, hand_authored, main, route_usable


def test_the_live_routing_table_is_structurally_clean():
    """The corpus's own table exits 0. This is the regression the fix was for."""
    assert main([]) == 0


def test_a_declared_null_source_is_hand_authored():
    assert hand_authored({"source": None, "hand_authored": True, "signal_type": "reported_traction"})


def test_a_bare_null_source_is_not_a_declaration():
    """`hand_authored: true` is what makes the absence deliberate. A null on its own is
    still a defect, and must keep failing — otherwise a typo that drops a source name
    reads as an intentional research route."""
    assert not hand_authored({"source": None})
    assert not hand_authored({"source": None, "hand_authored": False})


def test_a_bare_null_source_still_fails_the_structural_check(tmp_path, monkeypatch, capsys):
    routing = yaml.safe_load((ROOT / "sources" / "signal_routing.yaml").read_text())
    routing["dimensions"]["adoption"]["routes"].append({"source": None, "signal_type": "invented"})

    (tmp_path / "sources").mkdir()
    (tmp_path / "sources" / "signal_routing.yaml").write_text(yaml.safe_dump(routing))
    for sub in ("products", "categories"):
        (tmp_path / "sources" / sub).mkdir()
        for path in (ROOT / "sources" / sub).glob("*.yaml"):
            (tmp_path / "sources" / sub / path.name).write_bytes(path.read_bytes())

    monkeypatch.setattr("build.check_routing.ROOT", tmp_path)
    assert main([]) == 1
    assert "unknown source" in capsys.readouterr().out


def test_a_hand_authored_route_is_not_counted_as_blocked_by_a_bridge():
    """`blocked` means "a bridge would unblock this". Nothing is waiting on a bridge for an
    instrument that claims no count, so counting it there would overstate what bridging buys."""
    usable, why = route_usable({"source": None, "hand_authored": True}, {})
    assert not usable
    assert why == "hand-authored"

    usable, why = route_usable({"source": "lmarena"}, {"lmarena": {"bridged": False}})
    assert not usable
    assert why == "unbridged"


def test_the_source_to_artifact_map_is_read_from_the_table_not_mirrored():
    """#184: the mapping was a hardcoded dict and had already fallen behind the declaration.

    It named five sources where signal_routing.yaml declares seven — `npm` and `crates` were
    missing. Both are `bridged: false`, so the omission was inert; it would have stopped being
    inert the day a bridge landed, which is exactly when nobody would think to look here.
    """
    import yaml

    from build.check_routing import source_artifact

    routing = yaml.safe_load((ROOT / "sources" / "signal_routing.yaml").read_text())
    mapping = source_artifact(routing["sources"])

    assert mapping["semanticscholar"] == "arxiv", "a source may consume a differently-named key"
    assert {"npm", "crates"} <= set(mapping), "the hardcoded copy was missing exactly these"
    assert set(mapping) == {
        name for name, s in routing["sources"].items() if s.get("artifact_key")
    }


def test_a_bridged_source_without_an_artifact_key_is_still_a_finding(tmp_path, monkeypatch, capsys):
    """The structural check must keep firing when a bridged source declares nothing to read."""
    import yaml

    routing = yaml.safe_load((ROOT / "sources" / "signal_routing.yaml").read_text())
    routing["sources"]["invented"] = {"bridged": True}
    routing["dimensions"]["adoption"]["routes"].append(
        {"source": "invented", "signal_type": "usage_volume"}
    )

    (tmp_path / "sources").mkdir()
    (tmp_path / "sources" / "signal_routing.yaml").write_text(yaml.safe_dump(routing))
    for sub in ("products", "categories"):
        (tmp_path / "sources" / sub).mkdir()
        for path in (ROOT / "sources" / sub).glob("*.yaml"):
            (tmp_path / "sources" / sub / path.name).write_bytes(path.read_bytes())

    monkeypatch.setattr("build.check_routing.ROOT", tmp_path)
    assert main([]) == 1
    assert "no artifact mapping" in capsys.readouterr().out


def _corpus_with_new_kind(tmp_path, kind="rubygems"):
    """A checkout where `kind` is correctly declared end to end: a bridged source with an
    `artifact_key`, a route that names it, and one product carrying it."""
    import shutil

    import yaml

    (tmp_path / "sources").mkdir()
    routing = yaml.safe_load((ROOT / "sources" / "signal_routing.yaml").read_text())
    routing["sources"][kind] = {"artifact_key": kind, "bridged": True}
    routing["dimensions"]["adoption"]["routes"].insert(
        0, {"source": kind, "column": "downloads_30d", "signal_type": "usage_volume"}
    )
    (tmp_path / "sources" / "signal_routing.yaml").write_text(yaml.safe_dump(routing))
    for sub in ("products", "categories"):
        shutil.copytree(ROOT / "sources" / sub, tmp_path / "sources" / sub)
    path = tmp_path / "sources" / "products" / "accelerate.yaml"
    record = yaml.safe_load(path.read_text())
    record[kind] = [{"url": f"https://{kind}.org/x"}]
    path.write_text(yaml.safe_dump(record))
    return tmp_path


def test_coverage_sees_a_correctly_declared_new_artifact_kind(tmp_path, monkeypatch):
    """The second hardcoded list, and the more consequential one.

    `artifacts_of` enumerated the seven current keys literally, so a new kind that was
    declared correctly at every layer — source, `artifact_key`, route, product — was still
    invisible to coverage, and its routes reported as research rather than routed. The map
    would have understated its own automation with nothing failing.
    """
    import build.check_routing as cr

    root = _corpus_with_new_kind(tmp_path)
    monkeypatch.setattr(cr, "ROOT", root)
    routing, products, _, _ = cr.load()
    kinds = set(cr.source_artifact(routing["sources"]).values())

    assert "rubygems" in kinds, "the declaration itself must be readable"
    assert "rubygems" in cr.artifacts_of(products["accelerate"], kinds), (
        "a correctly declared artifact kind must be visible to coverage without editing "
        "a literal list in check_routing"
    )
    assert cr.main([]) == 0


def test_artifacts_of_reads_only_the_kinds_it_is_given():
    """It must not fall back to a built-in vocabulary when handed a narrow set — that is how
    the hardcoded list would creep back in as a default."""
    from build.check_routing import artifacts_of

    product = {"github": [{"url": "g"}], "pypi": [{"url": "p"}], "name": "x"}
    assert artifacts_of(product, {"github", "pypi"}) == {"github", "pypi"}
    assert artifacts_of(product, {"github"}) == {"github"}
    assert artifacts_of(product, set()) == set()
