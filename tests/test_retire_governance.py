"""`build/retire_governance.py`: the `governance` clause leaves components.context and raw (#684).

The properties worth pinning: only that clause moves, `raw` still says what the mapping says, an
emptied `context` is dropped rather than left empty, a second run changes nothing, and the real
corpus carries no such clause afterwards. The corpus test asserts an invariant, not a count.
"""

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from build.check_components import RETIRED_CONTEXT_KEYS, check
from build.check_rubric import CONTEXT, recompose, split_components
from build.retire_governance import KEY, main, migrate_text, plan, strip_clause

ROOT = Path(__file__).resolve().parents[1]

# `context` holds governance and one other key: context survives, without governance.
KEPT_CONTEXT = """product: peft
openness:
  score: 5
  class: open_source
  components:
    license:
    - name: Apache-2.0
      detail: OSI
    source:
      value: public
      detail: huggingface/peft
    free_text:
    - no feature-gated core
    context:
      governance:
        value: Hugging Face
      managed-tier:
        value: none
  confidence: high
  note: Apache-2.0 with the full source public.
  last_verified: '2026-09-23'
  raw: license:Apache-2.0(OSI);source:public(huggingface/peft);governance:Hugging Face;no feature-gated
    core;managed-tier:none
  sources:
  - url: https://example.org/peft
    shows: The repository.
adoption:
  level: 4
"""

# `context` holds governance alone, with a detail that folds `raw` over two lines.
EMPTIED_CONTEXT = """product: vllm
openness:
  score: 5
  class: open_source
  components:
    license:
    - name: Apache-2.0
      detail: OSI
    source:
      value: public
    context:
      governance:
        value: vLLM-project
        detail: community,PyTorch-ecosystem adjacent
  confidence: high
  note: Apache-2.0 across the repository.
  raw: license:Apache-2.0(OSI);source:public;governance:vLLM-project(community,PyTorch-ecosystem
    adjacent)
  sources:
  - url: https://example.org/vllm
    shows: The repository.
adoption:
  level: 4
"""

NOTHING_TO_DO = """product: widget
openness:
  score: 5
  class: open_source
  components:
    source:
      value: public
    context:
      service:
        value: optional
  raw: source:public;service:optional
  sources: []
"""


def test_strip_clause_keeps_every_other_clause_byte_for_byte():
    raw = "a:1; b:2(x;y);governance:Acme(a;b);keyless words ;c:3"
    assert strip_clause(raw) == "a:1; b:2(x;y);keyless words ;c:3"
    assert strip_clause("source:public;governance:Acme") == "source:public"
    assert strip_clause("source:public") == "source:public"
    # A key that merely contains the word is a different key.
    assert strip_clause("governance-model:open;a:1") == "governance-model:open;a:1"


def test_a_context_with_other_keys_keeps_them_and_loses_only_governance():
    out = migrate_text(KEPT_CONTEXT)
    before, after = yaml.safe_load(KEPT_CONTEXT), yaml.safe_load(out)

    assert after["openness"]["components"][CONTEXT] == {"managed-tier": {"value": "none"}}
    assert after["openness"]["raw"] == (
        "license:Apache-2.0(OSI);source:public(huggingface/peft);no feature-gated core;managed-tier:none"
    )
    # Everything else, the free_text clause and the other axis included, is what it was.
    for doc in (before, after):
        doc["openness"].pop("components"), doc["openness"].pop("raw")
    assert before == after
    assert recompose(yaml.safe_load(out)["openness"]["components"]) == split_components(
        yaml.safe_load(out)["openness"]["raw"]
    )


def test_an_emptied_context_is_dropped_not_left_empty():
    out = migrate_text(EMPTIED_CONTEXT)
    components = yaml.safe_load(out)["openness"]["components"]
    assert CONTEXT not in components
    assert list(components) == ["license", "source"]
    assert yaml.safe_load(out)["openness"]["raw"] == "license:Apache-2.0(OSI);source:public"
    # Nothing outside the two fields was touched, line for line.
    old, new = EMPTIED_CONTEXT.splitlines(), out.splitlines()
    assert [line for line in new if line not in old] == [
        "  raw: license:Apache-2.0(OSI);source:public"
    ]
    assert out.endswith("adoption:\n  level: 4\n")


def test_a_file_without_the_clause_is_left_alone_and_a_second_run_is_a_no_op():
    assert migrate_text(NOTHING_TO_DO) is None
    once = migrate_text(KEPT_CONTEXT)
    assert migrate_text(once) is None
    assert migrate_text(migrate_text(EMPTIED_CONTEXT)) is None


@pytest.mark.parametrize(
    "text, message",
    [
        # At the top level a ladder may read it, which is a scoring question, not this migration's.
        (
            NOTHING_TO_DO.replace("    context:\n      service:\n        value: optional\n",
                                  "    governance:\n      value: Acme\n")
            .replace("raw: source:public;service:optional", "raw: source:public;governance:Acme"),
            "top level",
        ),
        # components and raw disagreeing is a defect in the record; choosing a side is a curation call.
        (EMPTIED_CONTEXT.replace(";governance:vLLM-project(community,PyTorch-ecosystem\n    adjacent)", ""),
         "in context but not in raw"),
    ],
)
def test_a_shape_it_does_not_cover_raises_rather_than_repairs(text, message):
    with pytest.raises(ValueError, match=message):
        migrate_text(text)


def test_plan_and_write_derive_the_files_from_the_corpus(tmp_path, capsys):
    scores = tmp_path / "sources" / "scores"
    scores.mkdir(parents=True)
    for name, text in {"peft": KEPT_CONTEXT, "vllm": EMPTIED_CONTEXT, "widget": NOTHING_TO_DO}.items():
        (scores / f"{name}.yaml").write_text(text)

    assert sorted(p.stem for p in plan(tmp_path)) == ["peft", "vllm"]

    # A dry run writes nothing; --write rewrites exactly the derived files; a rerun finds none.
    assert main([], root=tmp_path) == 0
    assert (scores / "peft.yaml").read_text() == KEPT_CONTEXT
    assert main(["--write"], root=tmp_path) == 0
    assert KEY not in (scores / "peft.yaml").read_text().replace("managed-tier", "")
    assert (scores / "widget.yaml").read_text() == NOTHING_TO_DO
    assert plan(tmp_path) == {}
    capsys.readouterr()
    assert main(["--write"], root=tmp_path) == 0
    assert "rewrote 0 score file(s)" in capsys.readouterr().out


def test_the_real_corpus_carries_no_governance_clause():
    # An invariant, not a census: whatever the corpus holds, nothing is left to retire, so the
    # script is a no-op and the gate that refuses the key has nothing to report.
    assert plan(ROOT) == {}
    assert [f for f in check(ROOT) if "no longer recorded" in f] == []


def test_the_key_is_the_one_the_gate_refuses():
    assert KEY in RETIRED_CONTEXT_KEYS


def test_the_score_schema_rejects_governance_under_context():
    schema = json.loads((ROOT / "docs" / "schemas" / "score.schema.json").read_text())
    validator = Draft202012Validator(schema)
    record = {
        "product": "p",
        "openness": {
            "score": 5,
            "class": "open_source",
            "components": {"source": {"value": "public"}, CONTEXT: {"governance": {"value": "Acme"}}},
            "raw": "source:public;governance:Acme",
        },
    }
    assert any("governance" in error.message or list(error.absolute_path)[-1:] == [CONTEXT]
               for error in validator.iter_errors(record))
    record["openness"]["components"][CONTEXT] = {"service": {"value": "optional"}}
    record["openness"]["raw"] = "source:public;service:optional"
    assert not [e for e in validator.iter_errors(record) if CONTEXT in list(e.absolute_path)]
