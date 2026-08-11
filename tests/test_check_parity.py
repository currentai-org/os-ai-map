"""Tests for the repo/warehouse parity gate.

No network. The warehouse half is faked, because what needs testing is the comparison: which
disagreements the gate calls a failure, and which it lets through as a shared abstention.

`local_scores` does read the real `sources/`, on purpose. Its job is to replay what
`check_rubric` would conclude, and a fixture would let the two drift - which is the exact
failure mode this gate exists to catch, one level up.
"""

import build.check_parity as parity
from build.check_parity import as_pair, local_scores


def row(product, category, score=None, klass=None, deferred=False, rule=None):
    return {
        "product_slug": product,
        "category_slug": category,
        "openness_score": score,
        "openness_class": klass,
        "is_deferred": deferred,
        "winning_rule_index": rule,
        "dimension_values": "",
        "scoring_note": None,
    }


def run(monkeypatch, published, category=None, verbose=False):
    """Drive main() with a faked warehouse. Returns its exit status."""
    monkeypatch.setattr(parity, "warehouse_scores", lambda _c: published)

    class Args:
        pass

    args = Args()
    args.category = category
    args.verbose = verbose
    monkeypatch.setattr(parity.argparse.ArgumentParser, "parse_args", lambda self: args)
    return parity.main()


def test_local_scores_matches_check_rubrics_split():
    """392 products the ladders decide, 80 the categories defer. The same 472 the warehouse
    publishes, so a change to either number should show up as a failure here first. Was 384
    before Luciole (base_pretrained) and OpenRAG (orchestration_agents) were added, both
    computed rather than deferred, and 386/86 until the verification sweep read megatron-lm
    and recorded the core-gated:ungated its deferral was waiting on. Then 387/85 -> 391/81
    when the sweep reached `inference_code`: reading vllm, apple-core-ml-runtime,
    google-cloud-tpu-inference and qualcomm-ai-engine-direct recorded the `source` and
    `core-gated` values their deferrals had been waiting on, and check_recipe failed until
    the four stale deferrals were removed. Then 391/81 -> 392/80 when compound licenses
    started resolving on all their parts: `smoltalk`'s deferral existed because the ladder
    could not see the `+per-component` half of its license and computed a 5 against a
    recorded 4, and reading the whole value makes it reproduce. Then 392/80 -> 395/77 when
    `core_gated` started reading `self-host`: syfthub, thunderbolt and otari were all deferred
    with the same text, that core-gated is not recorded in a form the ladder can read, and all
    three had recorded it under `self-host`. Then 395/77 -> 400/72 when the keyless clauses
    that were a dimension's only record were promoted to keys: cosmopedia, openthoughts-114k,
    synth, tulu-3-sft-mixture and wildchat-1m all recorded `dataset card present`, and four of
    them `ungated`, as clauses with no colon, which the parser discards. Their five deferral
    texts named that defect and prescribed the fix. No score moved - all five already recorded
    the 5/open the ladder now computes. Then 400/72 -> 405/67 when a license tier stopped
    being resolved ahead of the formula: apify, chatbot-arena, patronus-evaluation-platform,
    artificial-analysis-intelligence-index and confer all record a `source` value the
    software ladder settles on its own, and were abstained on a license no rung deciding
    them was going to read. All five reproduce their recorded 2/source_available."""
    computed, deferred = local_scores(None)
    assert len(deferred) == 67
    assert len(computed) == 405
    assert not set(computed) & set(deferred)
    # Every one of the 405 reproduces today, so none should abstain.
    assert [key for key, value in computed.items() if value is None] == []


def test_agreement_passes(monkeypatch):
    computed, deferred = local_scores("base_pretrained")
    published = {
        key: row(key[0], key[1], value[0], value[1], rule=0) for key, value in computed.items()
    }
    published.update({key: row(key[0], key[1], deferred=True) for key in deferred})
    assert run(monkeypatch, published, "base_pretrained") == 0


def test_a_different_score_fails(monkeypatch, capsys):
    computed, _ = local_scores("base_pretrained")
    published = {
        key: row(key[0], key[1], value[0], value[1], rule=0) for key, value in computed.items()
    }
    victim = sorted(published)[0]
    published[victim]["openness_score"] = 1
    published[victim]["openness_class"] = "closed"
    assert run(monkeypatch, published, "base_pretrained") == 1
    assert "1 diverge" in capsys.readouterr().out


def test_a_missing_row_fails(monkeypatch, capsys):
    """The shape that hid 36 deferrals when the roster came from the evidence store: a
    product the repo knows about and the warehouse never published at all."""
    computed, _ = local_scores("base_pretrained")
    published = {
        key: row(key[0], key[1], value[0], value[1], rule=0) for key, value in computed.items()
    }
    del published[sorted(published)[0]]
    assert run(monkeypatch, published, "base_pretrained") == 1
    assert "no row in the warehouse at all" in capsys.readouterr().out


def test_scoring_a_deferred_product_fails(monkeypatch, capsys):
    """The safeguards bug: a ladder ending in `otherwise` scoring what the repo declined."""
    computed, deferred = local_scores("safeguards")
    published = {
        key: row(key[0], key[1], value[0], value[1], rule=0) for key, value in computed.items()
    }
    published.update({key: row(key[0], key[1], deferred=True) for key in deferred})
    victim = sorted(deferred)[0]
    published[victim] = row(victim[0], victim[1], 3, "open_weights", deferred=False, rule=6)
    assert run(monkeypatch, published, "safeguards") == 1
    assert "repo defers it, the warehouse does not know" in capsys.readouterr().out


def test_a_shared_abstention_is_not_a_divergence(monkeypatch, capsys):
    """Both sides declining is a curation work list, not a parity failure."""
    _, deferred = local_scores("ui_api")
    published = {key: row(key[0], key[1], deferred=True) for key in deferred}
    assert run(monkeypatch, published, "ui_api") == 1  # the scored products are missing
    out = capsys.readouterr().out
    assert f"{len(deferred)} abstain on both sides" in out


def test_as_pair_normalizes_the_score_type():
    assert as_pair(row("x", "y", 4, "open_core")) == (4, "open_core")
    assert as_pair(row("x", "y")) is None
