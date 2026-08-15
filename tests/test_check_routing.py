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
