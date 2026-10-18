"""Tests for build/license_rows.py, the warehouse-row license leg of #691 (report only)."""
from __future__ import annotations

import pytest

from build import license_rows as LR

BOUND = {LR.GITHUB: True, LR.HF_MODEL: True, LR.HF_DATASET: True}


@pytest.mark.parametrize("url, expected", [
    ("https://github.com/vllm-project/vllm", ("github", "vllm-project/vllm")),
    ("https://github.com/vllm-project/vllm/", ("github", "vllm-project/vllm")),
    ("https://github.com/vllm-project/vllm.git", ("github", "vllm-project/vllm")),
    ("https://api.github.com/repos/o/r", ("github", "o/r")),
    ("https://api.github.com/repos/o/r/license", ("github", "o/r")),
    ("https://huggingface.co/HuggingFaceH4/zephyr-7b-beta", ("huggingface_model", "HuggingFaceH4/zephyr-7b-beta")),
    ("https://huggingface.co/api/models/allenai/OLMo-2", ("huggingface_model", "allenai/OLMo-2")),
    ("https://huggingface.co/datasets/allenai/c4", ("huggingface_dataset", "allenai/c4")),
    ("https://huggingface.co/api/datasets/allenai/c4", ("huggingface_dataset", "allenai/c4")),
])
def test_declared_rewrites_name_the_artifact(url, expected):
    assert LR.route_for(url) == expected


@pytest.mark.parametrize("url", [
    # License documents stay on the direct-document path, raw or blob view alike: a label
    # cannot confirm a file's bytes, an added exception or extra terms.
    "https://raw.githubusercontent.com/o/r/main/LICENSE",
    "https://github.com/o/r/blob/main/LICENSE",
    "https://github.com/o/r/blob/main/LICENSE.md",
    # A LICENSE below the root may govern something other than what GitHub classifies.
    "https://github.com/o/r/blob/main/models/LICENSE",
    "https://github.com/o/r/blob/main/README.md",
    "https://huggingface.co/o/m/raw/main/README.md",
    "https://huggingface.co/api/models?author=o&search=m",
    "https://huggingface.co/api/models/o/m/tree/main",
    "https://huggingface.co/spaces/o/leaderboard",
    "https://huggingface.co/terms-of-service",
    "https://github.com/orgs/o/repositories",
    "https://api.github.com/repos/o/r/contents",
])
def test_everything_else_stays_on_the_direct_path(url):
    assert LR.route_for(url) is None


def test_aliases_apply_to_both_sides_of_the_comparison():
    # The corpus records ODC-BY and odc-by; the Hub serves odc-by, which its alias names
    # ODC-By-1.0. Reading the alias on one side only refuted every ODC-BY dataset.
    for recorded in ("ODC-BY", "odc-by", "ODC-By-1.0"):
        assert LR.canonical(recorded, LR.HF_DATASET) == LR.canonical("odc-by", LR.HF_DATASET)
    assert LR.canonical("Apache-2.0", LR.HF_MODEL) == LR.canonical("apache-2.0", LR.HF_MODEL)
    assert LR.canonical("MIT", LR.HF_MODEL) != LR.canonical("apache-2.0", LR.HF_MODEL)


ZEPHYR = {
    "type": "model",
    "huggingface_model": [
        {"url": "https://huggingface.co/HuggingFaceH4/zephyr-7b-beta"},
        {"url": "https://huggingface.co/HuggingFaceH4/zephyr-orpo-141b-A35b-v0.1"},
    ],
    "huggingface_dataset": [{"url": "https://huggingface.co/datasets/HuggingFaceH4/ultrachat_200k"}],
    "github": [{"url": "https://github.com/huggingface/alignment-handbook"}],
}
MIT = [{"name": "MIT", "detail": "OSI"}]


def _hf(slug, kind, artifact, license, status=200):
    return {"product_slug": slug, "artifact_kind": kind, "artifact_id": artifact, "resolved_id": artifact,
            "license": license, "http_status": status, "fetched_at": "2026-10-18 02:05:44"}


ROWS = LR.index_rows(
    [{"product_slug": "zephyr", "repo": "huggingface/alignment-handbook", "resolved_repo": "huggingface/alignment-handbook",
      "license_spdx_id": "Apache-2.0", "http_status": 200, "fetched_at": "2026-10-18 03:04:54"}],
    [
        _hf("zephyr", "huggingface_model", "HuggingFaceH4/zephyr-7b-beta", "mit"),
        _hf("zephyr", "huggingface_model", "HuggingFaceH4/zephyr-orpo-141b-A35b-v0.1", "apache-2.0"),
        _hf("zephyr", "huggingface_dataset", "HuggingFaceH4/ultrachat_200k", "mit"),
    ],
)


def _judge(url, product=ZEPHYR, entry=MIT, rows=ROWS, bound=BOUND, governing="zephyr-7b-beta"):
    return LR.judge_source("zephyr", url, product, entry, rows, bound, governing_release=governing)


def test_a_row_binds_to_the_governing_release_the_cited_url_names():
    v = _judge("https://huggingface.co/HuggingFaceH4/zephyr-7b-beta")
    assert (v.verdict, v.artifact, v.bound) == (LR.CONFIRMS, "HuggingFaceH4/zephyr-7b-beta", True)


def test_another_declared_release_abstains_rather_than_refuting():
    # The orpo-141b card says Apache-2.0. It is another release's answer, not a contradiction
    # of a record that governs on zephyr-7b-beta.
    v = _judge("https://huggingface.co/HuggingFaceH4/zephyr-orpo-141b-A35b-v0.1")
    assert v.verdict == LR.ABSTAINS
    assert "not the governing release" in v.reason


def test_a_multi_artifact_route_abstains_when_the_record_names_no_release():
    for url in ("https://huggingface.co/HuggingFaceH4/zephyr-7b-beta",
                "https://huggingface.co/HuggingFaceH4/zephyr-orpo-141b-A35b-v0.1"):
        assert _judge(url, governing="").verdict == LR.ABSTAINS


def test_a_single_declared_artifact_whose_row_disagrees_refutes():
    product = {"type": "model", "huggingface_model": [{"url": "https://huggingface.co/H/solo"}]}
    rows = LR.index_rows([], [_hf("zephyr", "huggingface_model", "H/solo", "apache-2.0")])
    v = _judge("https://huggingface.co/H/solo", product=product, rows=rows, governing="")
    assert (v.verdict, v.recorded, v.observed) == (LR.REFUTES, "MIT", "apache-2.0")


@pytest.mark.parametrize("artifact, release, expected", [
    ("HuggingFaceH4/zephyr-7b-beta", "zephyr-7b-beta", True),
    ("ByteDance-Seed/BAGEL-7B-MoT", "bagel-7b-mot", True),
    ("HuggingFaceH4/zephyr-7b-beta", "HuggingFaceH4/zephyr-7b-beta", True),
    ("HuggingFaceH4/zephyr-orpo-141b-A35b-v0.1", "zephyr-7b-beta", False),
    ("depth-anything/DA3-LARGE", "Depth Anything 3", False),
    ("o/r", "", False),
])
def test_the_governing_release_matches_only_an_exact_spelling(artifact, release, expected):
    assert LR.names_release(artifact, release) is expected


def test_a_dataset_card_never_answers_for_a_model_license():
    v = _judge("https://huggingface.co/datasets/HuggingFaceH4/ultrachat_200k")
    assert v.verdict == LR.ABSTAINS
    assert "about the dataset" in v.reason


def test_a_repository_license_never_answers_for_a_model_license():
    v = _judge("https://github.com/huggingface/alignment-handbook")
    assert v.verdict == LR.ABSTAINS
    assert "not about the repository" in v.reason


def test_an_explicitly_code_scoped_part_is_compared_with_the_repository():
    entry = [{"name": "Apache-2.0", "detail": "OSI, code"}, {"name": "MIT", "detail": "OSI, weights"}]
    assert _judge("https://github.com/huggingface/alignment-handbook", entry=entry).verdict == LR.CONFIRMS
    assert _judge("https://huggingface.co/HuggingFaceH4/zephyr-7b-beta", entry=entry).verdict == LR.CONFIRMS


def test_an_undeclared_artifact_abstains_even_when_a_row_would_agree():
    v = _judge("https://huggingface.co/meta-llama/LlamaGuard-7b")
    assert (v.verdict, v.reason) == (LR.ABSTAINS, "the cited artifact is not declared on the product")


def test_no_row_and_no_answer_both_abstain():
    product = {**ZEPHYR, "huggingface_model": ZEPHYR["huggingface_model"] + [{"url": "https://huggingface.co/H/other"}]}
    assert _judge("https://huggingface.co/H/other", product=product, governing="other").reason == \
        "no artifact_state row for the cited artifact"
    rows = LR.index_rows([], [_hf("zephyr", "huggingface_model", "HuggingFaceH4/zephyr-7b-beta", "other")])
    assert _judge("https://huggingface.co/HuggingFaceH4/zephyr-7b-beta", rows=rows).reason == "the row carries no usable license"
    rows = LR.index_rows([], [_hf("zephyr", "huggingface_model", "HuggingFaceH4/zephyr-7b-beta", "mit", status=404)])
    assert _judge("https://huggingface.co/HuggingFaceH4/zephyr-7b-beta", rows=rows).verdict == LR.ABSTAINS


def test_a_qualified_detail_abstains():
    v = _judge("https://huggingface.co/HuggingFaceH4/zephyr-7b-beta", entry=[{"name": "MIT", "detail": "OSI, adapters only"}])
    assert (v.verdict, v.reason) == (LR.ABSTAINS, "the detail qualifies the license")


def test_license_and_other_files_are_on_the_direct_path():
    for url in ("https://raw.githubusercontent.com/huggingface/alignment-handbook/main/LICENSE",
                "https://github.com/huggingface/alignment-handbook/blob/main/LICENSE"):
        v = _judge(url)
        assert (v.verdict, v.reason) == (LR.DIRECT, "a license file stays on the direct-document path")
    v = _judge("https://raw.githubusercontent.com/huggingface/alignment-handbook/main/README.md")
    assert (v.verdict, v.reason) == (LR.DIRECT, "a file URL stays on the direct-document path")


def _v(verdict, bound=True):
    return LR.SourceVerdict("s", "u", verdict, bound=bound)


@pytest.mark.parametrize("verdicts, outcome", [
    ([_v(LR.CONFIRMS), _v(LR.CONFIRMS)], "confirms"),
    ([_v(LR.CONFIRMS, bound=False)], "confirms on an unbound read"),
    ([_v(LR.CONFIRMS), _v(LR.DIRECT)], "confirms in part; the rest is on the direct path"),
    ([_v(LR.CONFIRMS), _v(LR.REFUTES)], "refuted"),
    ([_v(LR.CONFIRMS), _v(LR.ABSTAINS)], "abstains"),
    ([_v(LR.DIRECT)], "direct path only"),
])
def test_product_outcome_needs_every_source(verdicts, outcome):
    assert LR.product_outcome(verdicts) == outcome


def test_rows_supplied_from_a_file_are_never_bound(capsys):
    assert LR.main([], github_rows=[], hf_rows=[]) == 0
    out = capsys.readouterr().out
    assert "NOT BOUND" in out
    assert "0 would confirm their license from bound rows alone" in out
