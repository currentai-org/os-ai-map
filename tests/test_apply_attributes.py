"""`build/apply_attributes.py` applies a curation ledger without rewriting anything else.

Every test builds its own small corpus under `tmp_path`; nothing here touches `sources/`.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from build import apply_attributes as aa

ORG = """name: acme
display_name: Acme
type: company
homepage: https://www.acme.example
github:
- url: https://github.com/acme
products:
- widget
- corpus
comments: Hand-wrapped prose that an edit elsewhere in the file must leave exactly as it is, down to
  the line break.
"""

ORG_NO_HOMEPAGE = """name: bare
display_name: Bare
type: lab
products:
- other
"""

FOUNDATION = """name: lf
display_name: Linux Foundation
type: foundation
products: []
"""

DATASET = """name: corpus
display_name: Corpus
type: dataset
description: A multilingual corpus, wrapped the way the corpus wraps prose, so that an edit must not
  reflow it.
huggingface_dataset:
- url: https://huggingface.co/datasets/acme/corpus
"""

SOFTWARE = """name: widget
display_name: Widget
type: software
description: A widget.
"""

OTHER = """name: other
display_name: Other
type: dataset
description: Another.
"""


@pytest.fixture()
def corpus(tmp_path: Path) -> Path:
    for directory, files in {
        "organizations": {"acme": ORG, "bare": ORG_NO_HOMEPAGE, "lf": FOUNDATION},
        "products": {"corpus": DATASET, "widget": SOFTWARE, "other": OTHER},
    }.items():
        (tmp_path / "sources" / directory).mkdir(parents=True)
        for stem, text in files.items():
            (tmp_path / "sources" / directory / f"{stem}.yaml").write_text(text)
    return tmp_path


def ledger(tmp_path: Path, rows: list[dict | str], name: str = "batch.jsonl") -> Path:
    path = tmp_path / name
    path.write_text("\n".join(r if isinstance(r, str) else json.dumps(r) for r in rows) + "\n")
    return path


def row(slug: str, key: str, value, **extra) -> dict:
    return {"slug": slug, key: value, "evidence": "https://acme.example/about",
            "basis": "about page", "confidence": "high", **extra}


def read(root: Path, directory: str, slug: str) -> str:
    return (root / "sources" / directory / f"{slug}.yaml").read_text()


def run(corpus: Path, kind: str, rows, write=True, overwrite=False, name="batch.jsonl") -> aa.Report:
    return aa.apply(kind, [ledger(corpus, rows, name)], root=corpus, write=write, overwrite=overwrite)


# --- country -------------------------------------------------------------------------------


def test_a_country_on_an_individual_is_rejected(corpus):
    path = corpus / "sources" / "organizations" / "bare.yaml"
    path.write_text(path.read_text().replace("type: lab", "type: individual"))
    report = run(corpus, "country", [row("bare", "country", "US")])
    assert "country" not in yaml.safe_load(read(corpus, "organizations", "bare"))
    assert any("individual" in r.reason for r in report.rows)


def test_a_country_is_inserted_after_homepage_and_nothing_else_changes(corpus):
    report = run(corpus, "country", [row("acme", "country", "US")])
    assert report.count(aa.SET) == 1 and not report.failed
    out = read(corpus, "organizations", "acme")
    assert out.splitlines()[3:5] == ["homepage: https://www.acme.example", "country: US"]
    assert out.replace("country: US\n", "") == ORG


def test_country_falls_back_to_after_type_when_there_is_no_homepage(corpus):
    run(corpus, "country", [row("bare", "country", "GB")])
    assert read(corpus, "organizations", "bare").splitlines()[:4] == [
        "name: bare", "display_name: Bare", "type: lab", "country: GB"]


def test_a_dry_run_changes_nothing(corpus):
    report = run(corpus, "country", [row("acme", "country", "US")], write=False)
    assert report.count(aa.SET) == 1 and report.written == []
    assert read(corpus, "organizations", "acme") == ORG


def test_a_second_run_is_a_no_op(corpus):
    run(corpus, "country", [row("acme", "country", "US")])
    once = read(corpus, "organizations", "acme")
    report = run(corpus, "country", [row("acme", "country", "US")])
    assert report.count(aa.UNCHANGED) == 1 and report.count(aa.SET) == 0
    assert report.written == [] and read(corpus, "organizations", "acme") == once


def test_a_different_value_is_a_conflict_until_overwrite_is_given(corpus):
    (corpus / "sources/organizations/acme.yaml").write_text(
        ORG.replace("homepage: https://www.acme.example\n",
                    "homepage: https://www.acme.example\ncountry: USA\n"))
    report = run(corpus, "country", [row("acme", "country", "US")])
    assert report.count(aa.CONFLICT) == 1 and report.failed
    assert "country: USA" in read(corpus, "organizations", "acme")

    report = run(corpus, "country", [row("acme", "country", "US")], overwrite=True)
    assert report.count(aa.CHANGED) == 1 and not report.failed
    out = read(corpus, "organizations", "acme")
    assert "country: US\n" in out and "USA" not in out
    assert out.count("country:") == 1


@pytest.mark.parametrize("bad", ["USA", "United States", "UK", "EU", "XK", "us", "", 5])
def test_a_country_outside_the_vocabulary_is_rejected_and_not_written(corpus, bad):
    report = run(corpus, "country", [row("acme", "country", bad)])
    assert report.count(aa.REJECTED) == 1 and report.failed
    assert read(corpus, "organizations", "acme") == ORG


def test_norway_is_quoted_so_it_does_not_read_as_false(corpus):
    run(corpus, "country", [row("acme", "country", "NO")])
    assert yaml.safe_load(read(corpus, "organizations", "acme"))["country"] == "NO"


# --- which rows are skipped ---------------------------------------------------------------


def test_low_confidence_missing_evidence_and_null_rows_are_skipped(corpus):
    rows = [
        row("acme", "country", "US", confidence="low"),
        {**row("bare", "country", "GB"), "evidence": ""},
        row("lf", "country", None),
    ]
    report = run(corpus, "country", rows)
    assert [r.outcome for r in report.rows] == [aa.SKIPPED] * 3
    assert "low" in report.rows[0].reason and "evidence" in report.rows[1].reason
    assert not report.failed and report.written == []
    assert read(corpus, "organizations", "acme") == ORG


def test_a_row_without_the_evidence_key_or_with_a_bare_string_is_skipped(corpus):
    no_key = row("acme", "country", "US")
    del no_key["evidence"]
    report = run(corpus, "country", [no_key, row("bare", "country", "GB", evidence="about page")])
    assert [r.outcome for r in report.rows] == [aa.SKIPPED, aa.SKIPPED]


def test_medium_confidence_is_applied(corpus):
    assert run(corpus, "country", [row("acme", "country", "US", confidence="medium")]).count(aa.SET) == 1


def test_malformed_rows_are_rejected_and_the_rest_still_apply(corpus):
    report = run(corpus, "country", ["{not json", {"country": "US"}, {"slug": "acme"},
                                     row("acme", "country", "US"),
                                     row("ghost", "country", "US"),
                                     row("bare", "country", "GB", confidence="sure")])
    outcomes = [r.outcome for r in report.rows]
    assert outcomes == [aa.REJECTED, aa.REJECTED, aa.REJECTED, aa.SET, aa.REJECTED, aa.REJECTED]
    assert "country: US" in read(corpus, "organizations", "acme") and report.failed


def test_two_rows_that_disagree_are_both_refused_but_repeats_are_fine(corpus):
    report = run(corpus, "country", [row("acme", "country", "US"), row("acme", "country", "CA")])
    assert [r.outcome for r in report.rows] == [aa.REJECTED, aa.REJECTED]
    assert read(corpus, "organizations", "acme") == ORG
    again = run(corpus, "country", [row("acme", "country", "US"), row("acme", "country", "US")])
    assert [r.outcome for r in again.rows] == [aa.SET, aa.UNCHANGED]


# --- languages ---------------------------------------------------------------------------


def test_languages_are_sorted_and_inserted_after_type_as_a_flow_list(corpus):
    report = run(corpus, "languages", [row("corpus", "languages", ["swa", "amh", "hau"])])
    assert report.count(aa.SET) == 1
    out = read(corpus, "products", "corpus")
    assert "type: dataset\nlanguages: [amh, hau, swa]\ndescription:" in out
    assert out.replace("languages: [amh, hau, swa]\n", "") == DATASET


def _many_codes(n: int) -> list[str]:
    from build.vocabulary import language_codes

    return sorted(language_codes())[:n]


def test_a_very_long_language_list_wraps_at_the_product_width_and_round_trips(corpus):
    codes = _many_codes(1200)
    report = run(corpus, "languages", [row("corpus", "languages", codes[::-1])])
    assert report.count(aa.SET) == 1 and not report.failed
    out = read(corpus, "products", "corpus")
    lines = out.splitlines()
    start = lines.index(next(l for l in lines if l.startswith("languages: [")))
    block = []
    for line in lines[start:]:
        if not line.startswith(("languages:", "  ")):
            break
        block.append(line)
    assert 1 < len(block) < 120  # wrapped, not one line per code and not one endless line
    assert all(len(line) < 125 for line in block)
    assert all(line.startswith("  ") for line in block[1:])
    assert yaml.safe_load(out)["languages"] == codes
    assert out.replace("\n".join(block) + "\n", "") == DATASET
    # the file is stable: a second run finds the same value and writes nothing
    again = run(corpus, "languages", [row("corpus", "languages", codes)])
    assert again.count(aa.UNCHANGED) == 1 and again.written == []


def test_replacing_a_long_flow_list_takes_its_continuation_lines_with_it(corpus):
    run(corpus, "languages", [row("corpus", "languages", _many_codes(400))])
    run(corpus, "languages", [row("corpus", "languages", ["eng"])], overwrite=True)
    out = read(corpus, "products", "corpus")
    assert "languages: [eng]\ndescription:" in out
    assert yaml.safe_load(out)["languages"] == ["eng"]


def test_languages_are_checked_against_the_vocabulary_and_the_product_type(corpus):
    report = run(corpus, "languages", [
        row("corpus", "languages", ["eng", "mul"]),
        row("other", "languages", ["en"]),
        row("widget", "languages", ["eng"]),
        row("corpus", "languages", []),
        row("corpus", "languages", "eng"),
    ])
    assert [r.outcome for r in report.rows] == [aa.REJECTED] * 5
    assert read(corpus, "products", "corpus") == DATASET


def test_languages_that_differ_in_order_only_are_unchanged(corpus):
    run(corpus, "languages", [row("corpus", "languages", ["amh", "hau"])])
    report = run(corpus, "languages", [row("corpus", "languages", ["hau", "amh"])])
    assert report.count(aa.UNCHANGED) == 1 and report.written == []


def test_a_changed_language_list_replaces_the_block(corpus):
    run(corpus, "languages", [row("corpus", "languages", ["amh", "hau"])])
    report = run(corpus, "languages", [row("corpus", "languages", ["eng"])], overwrite=True)
    assert report.count(aa.CHANGED) == 1
    assert yaml.safe_load(read(corpus, "products", "corpus"))["languages"] == ["eng"]


# --- steward -----------------------------------------------------------------------------


def test_a_steward_goes_after_type_and_languages_after_it_in_either_order(corpus):
    for order in (("steward", "languages"), ("languages", "steward")):
        (corpus / "sources/products/corpus.yaml").write_text(DATASET)
        for kind in order:
            value = "lf" if kind == "steward" else ["eng"]
            run(corpus, kind, [row("corpus", kind, value)])
        out = read(corpus, "products", "corpus")
        assert list(yaml.safe_load(out))[:5] == ["name", "display_name", "type", "steward", "languages"]


def test_a_steward_must_be_an_org_file_and_not_the_owner(corpus):
    report = run(corpus, "steward", [row("corpus", "steward", "nobody"), row("corpus", "steward", "acme")])
    assert [r.outcome for r in report.rows] == [aa.REJECTED, aa.REJECTED]
    assert "owning organization" in report.rows[1].reason
    assert read(corpus, "products", "corpus") == DATASET


def test_a_steward_other_than_the_owner_is_applied(corpus):
    assert run(corpus, "steward", [row("widget", "steward", "lf")]).count(aa.SET) == 1
    assert "type: software\nsteward: lf\n" in read(corpus, "products", "widget")


# --- the command line ----------------------------------------------------------------------


def test_the_cli_accepts_a_glob_and_repeats_and_reports(corpus, capsys):
    ledger(corpus, [row("acme", "country", "US")], "a-01.jsonl")
    ledger(corpus, [row("bare", "country", "GB")], "a-02.jsonl")
    ledger(corpus, [row("lf", "country", "SE")], "b.jsonl")
    argv = ["--kind", "country", "--root", str(corpus),
            "--ledger", str(corpus / "a-*.jsonl"), "--ledger", str(corpus / "b.jsonl")]
    assert aa.main(argv) == 0
    assert read(corpus, "organizations", "acme") == ORG  # dry run by default
    assert aa.main(argv + ["--write"]) == 0
    out = capsys.readouterr().out
    assert "3 set" in out and "wrote 3 file(s)" in out
    assert aa.main(argv + ["--write"]) == 0
    assert "3 unchanged" in capsys.readouterr().out


def test_the_cli_exits_non_zero_on_a_rejected_row_and_zero_on_a_skipped_one(corpus):
    bad = ledger(corpus, [row("acme", "country", "USA")], "bad.jsonl")
    skipped = ledger(corpus, [row("acme", "country", "US", confidence="low")], "skip.jsonl")
    assert aa.main(["--kind", "country", "--root", str(corpus), "--ledger", str(bad)]) == 1
    assert aa.main(["--kind", "country", "--root", str(corpus), "--ledger", str(skipped)]) == 0


def test_a_missing_ledger_is_a_usage_error(corpus):
    with pytest.raises(SystemExit):
        aa.main(["--kind", "country", "--root", str(corpus), "--ledger", str(corpus / "nope-*.jsonl")])
