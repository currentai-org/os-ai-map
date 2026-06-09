import json
from pathlib import Path
from build.serialize import build_payload
from build.validate import load_sources

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = Path("/workspace/GitHub/oso/insights-private/projects/currentai/stack-map/generator/notebook_data.json")

def test_serialize_reproduces_current_notebook_data():
    current = json.load(open(OVERLAY))
    rebuilt = build_payload(load_sources(ROOT), frozen_long_tail=current["long_tail"])
    assert rebuilt["order"] == current["order"]
    assert rebuilt["n_total"] == current["n_total"]
    for cid in current["order"]:
        cur_ps = current["categories"][cid]["products"]
        new_ps = rebuilt["categories"][cid]["products"]
        assert len(new_ps) == len(cur_ps), cid
        for a, b in zip(new_ps, cur_ps):
            for field in ("product", "org", "type", "description",
                          "openness", "adoption", "capability", "flags", "version_note"):
                assert a.get(field) == b.get(field), f"{cid}/{a.get('product')}/{field}"
