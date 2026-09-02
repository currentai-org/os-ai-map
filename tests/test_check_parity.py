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
    them was going to read. All five reproduce their recorded 2/source_available. Then
    405/67 -> 410/62 when five vendor licenses joined the `competition_restricted` tier:
    max, dify, open-webui, lobe-chat and autogpt all record `source:public`, which reaches
    the rung that tests the tier, so mapping the license was the only thing left. autogpt
    needed its license recorded by name first - it said `DUAL`, which names no license. That
    rung produces 2/source_available, which is what all five already recorded, so again no
    score moved. Then 410/62 -> 416/56 when the orchestration_agents evidence sweep read the
    repo and pricing page behind ten deferrals: codex-cli, claude-code, cursor, haystack,
    langgraph and hexabot gained the `source` or `core-gated` key their deferral was waiting
    on and every one reproduced its recorded score, so six deferrals came off. Then 416/56 ->
    420/52 when the other four of those ten were ruled on rather than re-read: langchain,
    llama-index, pydantic-ai and zed each rested a 4/open_core on a `commercial:` clause naming
    a paid product sold beside an unwithheld core, which `core_gated` does not ask about, and
    all four moved to the 5/open_source the ladder computes. This is the one recent step where
    published scores MOVED rather than deferrals merely coming off. langgraph did not move: its
    gate is a closed Elastic-2.0 package behind a license key, not a product beside the core.

    Then 420/52 -> 425/47 when the evidence sweep reached inference_code,
    dataset_processing_tools and finetuning_code. Five deferrals came off: sglang,
    text-generation-inference and axolotl recorded `core-gated:ungated` and reproduced their
    5/open_source, while sambanova-cloud and anyscale-fine-tuning recorded `source:closed` and
    reproduced their 1/closed on rung 0 alone. anyscale-fine-tuning is the one worth
    remembering - it already recorded a `source` key, spelled `not-public`, which is outside
    the dimension's enum and carries no value_alias, so the deferral was vocabulary drift
    rather than a missing read. openpipe moved 4/open_core -> 5/open_source on the langchain
    reading: its hosted ART backend is an optional service beside a full-featured open core.
    Three deferrals stayed and had their reasons rewritten as conflicts: aws-neuron
    (`source:partial`, computing 2 against a recorded 1), unsloth (`core-gated:gated` from a
    pricing page selling multi-GPU the free tier does not have, computing 4 against a recorded
    5) and nemo-data-designer (Apache-2.0 and public per NVIDIA's own docs, so the recorded
    1/closed is unreachable at either value of core-gated).

    Then 425/47 -> 432/40 when the sweep reached `evaluation_code` and all seven of its
    deferrals came off, every one reproducing its recorded score. Five are research or public
    artifacts with no vendor at all - bigcodebench, osworld, simpleaudit, open-llm-leaderboard
    and the publicly-funded compar-ia - so `core-gated:ungated` there is an absence of anything
    to sell rather than a judgment about what is sold. The other two settle on `source` alone:
    epoch-ai-benchmarks records `partial`, its org publishing a client library and component
    repos while the engine behind the dashboard and the FrontierMath problems stay unpublished,
    and scale-evaluation records `closed`, its VPC option being a customer-cloud deployment of a
    proprietary product rather than published source.

    Then 432/40 -> 437/35 when the sweep reached `ui_api` and all five of its deferrals came
    off, every one reproducing its recorded score. deepseek-chat, doubao and meta-ai record
    `source:closed` and settle on rung 0 alone - Meta's own AI Terms grant "rights of access
    and use" to a service Meta runs and nothing more. nextchat records `source:public` and
    `core-gated:gated`: its Enterprise Edition sells a private deployment with an admin panel,
    permission control and an internal knowledge base, none of which is in the MIT repo, whose
    own features list says all data stays local in the browser. continue records
    `core-gated:ungated` - the whole monorepo is Apache-2.0 with no ee/ directory, and its
    "Enterprise License Key" turns out to be published Apache-2.0 code carrying only a
    customerId, an expiry and a control-plane apiUrl, unlocking no client feature.

    Then 437/35 -> 438/34 when the sweep reached `telemetry_observability`, where only one of
    four deferrals came off. langfuse closed at the 4 it already had: its root LICENSE carves
    ee/, web/src/ee/ and worker/src/ee/ out of MIT and under an Enterprise License, ee/src
    ships a license check, and web/src/ee/features holds multi-tenant SSO, the audit-log
    viewer, the admin API and billing. The other three each turned out to be blocked on
    something other than the missing key and stayed deferred as conflicts: agentops (app/
    ships the whole self-hostable platform, so nothing is gated, but app/LICENSE is Elastic
    2.0 rather than the recorded MIT, so the ladder reaches 5 or 2 and never 4), langtrace
    (abstains on the tier, its license recorded as the unmappable `app=AGPL-3.0`, and on the
    evidence ungated with a cloud tier the vendor charges nothing for, computing 5 against a
    recorded 4) and weave (the Apache-2.0 repo publishes an SDK and a trace-server library but
    no UI, no deployment manifest and not the HTTP service, which its own README places in
    W&B's closed core repo - `source:partial`, computing 2 against a recorded 4).

    Then 438/34 -> 442/30 when the sweep reached `agent_tools_protocols` and `ml_frameworks`.
    Four of those five deferrals came off, each reproducing its recorded 5/open_source on a
    `core-gated:ungated` that rests on there being no vendor at all rather than on a pricing
    page: agent2agent-protocol is an LF project whose six reference SDKs are separate public
    repos, yomo publishes its whole Rust runtime in src/ while Vivgrid sells a hosted platform
    that the README does not mention, feluda ships all nine of its operators under one GPL-3.0
    license for a civic-tech non-profit, and pysyft publishes eleven syft-* packages and runs
    on cloud storage the user already owns. model-context-protocol stayed, and its reason was
    rewritten: source and core-gated are now recorded, but its LICENSE splits three ways and
    the CC-BY-4.0 documentation branch maps to no tier, so the ladder abstains on the license
    rather than on the missing keys the old reason blamed.

    Then 446/26 -> 448/24 when a card read closed mt-bench and livebench in
    `benchmark_eval_data`. Neither needed a license: both already recorded one the ladder
    reads, and what the top rung was missing was a documentation key, which it asks for
    deliberately so a product recording nothing cannot reach 5 by default. Both document
    themselves in the repository rather than on a Hub card - FastChat's llm_judge README for
    mt-bench, a datasheets-for-datasets questionnaire for livebench - and recording that
    reproduces the 5/open each already carried.

    Before that, 442/30 -> 446/26 when the four guardrail-model deferrals in `safeguards` came off.
    All four were recorded 4/open_weights against a ladder computing 3, and all four dropped
    to 3 rather than the ladder bending. qwen3guard, granite-guardian and gpt-oss-safeguard
    were one case argued once - Apache-2.0 weights, `data:not-released`, no recipe published -
    and the 4-rung needs the post-training data AND the fine-tuning pipeline, so the recorded
    4 was crediting a recipe the products' own cards say does not exist. wildguard looked
    different and was settled by reading the project rather than by judgment: its `data:open`
    is real, the WildGuardMix corpus is public, but `allenai/wildguard` ships nine files with
    no trainer and no training config, its companion Safety-Eval repo is an evaluation suite,
    and the card sends readers to the paper appendix for training details. That is
    `code:partial`, the 4-rung still fails, and open data on its own does not carry it.

    Then 448/24 -> 453/19 when the five conflicts the sweep had left open were ruled on
    rather than re-read, on 2026-08-12. Two were factual errors in the record: agentops
    carried the root MIT that covers only its SDK while app/LICENSE is Elastic 2.0, and
    langtrace spelled its license `app=AGPL-3.0`, a scope prefix matching no tier example
    and so blocking every rung that tests one. One was a read recorded but not acted on:
    weave's `source` said `public` while the read established `partial`. The other two
    already computed a score the record disagreed with, and the record moved: unsloth
    4/open_core on its recorded `core-gated:gated`, aws-neuron 2/source_available on its
    recorded `source:partial`. Four of the five moved a published score, in both
    directions. nemo-data-designer stayed deferred - both rungs it can reach test
    core-gated, nobody has read what the NeMo Platform withholds from the published
    library, and a value was not invented to close it.

    Then 453/19 -> 460/12 when the owner ruled on the ten deferrals of the first resolution
    batch, on 2026-08-12. Seven closed. Five were transcription and four of those moved no
    score - gaia's unstated license, humanitys-last-exam's MIT out of a compound key,
    compar-ia-datasets' gate as a token, openhands' enterprise directory as `core-gated:
    gated`. math moved 2 -> 1: recording the DMCA takedown as `access:closed` lands it on the
    rung for data that is not distributed rather than the gated rung the record assumed.
    swe-bench-verified moved 4 -> 5 and nemo-data-designer 1 -> 5, the first on the ruling
    that a repository license governs over a distribution point that states none, the second
    on a read that established the NeMo Platform withholds nothing from the published
    library. Three stayed deferred and each on a rubric gap rather than a missing fact:
    livecodebench and openhermes-2-5 record 3 on unstated licenses the ladder gives no rung,
    and multipl-e records the repository's BSD-3-with-ML-restriction, which this ladder has
    no tier for.

    Then 460/12 -> 465/7 when the second resolution batch ran, on 2026-08-12. Five closed and
    none of them moved a published score. Three were evidence reads whose deferral texts had
    gone stale: jina-reader, maple-ai and privatemode were all recorded as computing a score
    that disagreed with the record, and none of them computed anything by the time they were
    read - #201 and #203 had turned all three into ordinary unanswered dimensions. jina-reader
    and maple-ai gained `core-gated:ungated` on repo and pricing reads, and privatemode gained
    `source:partial`, its recorded `TCB-public` being outside the dimension's enum. The other
    two were rulings. llamafirewall transcribed `source` and `license` off its `framework` and
    `self-host` keys, on the rule that a product is scored on the artifact it ships rather than
    on what it can load - the bundled guard models are separate products here with their own
    scores. raspberry-pi-ai-hat-plus kept its 4 through a new `accessory_host` dimension in the
    hardware ladder, because an accessory tracks the platform it completes. arduino-uno-q is the
    sixth and the only published score that moved, 3/documented -> the 5/open_hardware the ladder
    computes: its design files are openly licensed under CC-BY-SA 4.0, which is the same
    `schematics: open` that puts beagley-ai at 5, and the proprietary SoC the old note cited is a
    reason no rung applies. A cap on proprietary silicon was considered and rejected because every
    board in the category runs on it, so the cap would flatten all 20 to 3 and leave the 4 and 5
    rungs unreachable. Of the six that remain, model-context-protocol and txt360-pipeline both had
    their licenses recorded properly and both still abstain, which is now the finding rather than
    a defect.

    Then 466/6 -> 467/5 on 2026-08-12, when model-context-protocol closed. It did NOT close on
    the rubric ruling it looked like it was waiting for. `permissive_non_osi` did gain a rung
    that day - 3/source_available, on the reasoning that attribution asks less than a
    no-compete clause but a non-OSI license still cannot enter the open bucket under MOF or
    OSAID - and MCP does not reach it. Its CC-BY-4.0 covers documentation other than the
    specifications and had been recorded inside the `license` compound, where
    most-restrictive-wins let a license over the project's PROSE decide the score of the
    artifact you run, pulling a 5 down to a 3. `autogen` records the identical facts under a
    separate `docs:` key the ladder does not read and has always scored 5. MCP now matches it
    and reproduces at 5/open_source, so the published score did not move. The rung stays,
    unexercised and pinned by tests/test_openness_buckets.py, because the ruling it encodes is
    about a license class rather than about one product."""
    computed, deferred = local_scores(None)
    # 467/5 -> 517/5 on 2026-08-18, when compilers and storage were promoted from the tail
    # registry: 50 products in, and no net change to the deferral count. Both promotions turned
    # up one product the shared `osi` tier plainly covered and could not name - liger-kernel on
    # BSD-2-Clause, pgvector on the PostgreSQL License - and both closed the same day when the
    # owner ruled the two names onto the tier. Each was the first product on the map to record
    # its license, so the ruling moved no existing score; the measurement is in software.yaml
    # beside the names.
    assert len(deferred) == 5
    # 517/5 -> 522/5 on 2026-08-30, when the first five products were promoted out of the
    # agent_tools_protocols tail registry: 5 products in, and no net change to the deferral
    # count. Two licenses the tiers plainly covered and could not name were ruled on that day -
    # MinerU-Open-Source-License and AI-Pubs-Open-RAIL-M-Modified onto `competition_restricted`,
    # and Crawl4AI-Attribution-License onto `permissive_non_osi`, which no product had ever
    # reached. Each was the first product on the map to record its license, so no existing score
    # moved; the measurements are in software.yaml beside the names.
    # 548/5 -> 571/5 on 2026-09-01, the Round 1 calibration tranche: 23 products in across
    # five categories, no net change to the deferral count, and no new license ruling needed -
    # every add recorded a spelling its ladder already tiers (mle-bench's Kaggle corpus lands
    # on the enumerated `per-component` spelling of deferred_to_components).
    # 571/5 -> 578/5 on 2026-09-02, the Round 2 telemetry_observability promotion: seven
    # candidates in (ragaai-catalyst, logfire, monocle, traccia, axon, latitude-llm, evidently),
    # no net change to the deferral count, and no new license ruling needed - every license
    # recorded (Apache-2.0, MIT) already tiers on the shared `osi` rung.
    assert len(computed) == 578
    assert not set(computed) & set(deferred)
    # Every one of them reproduces today, so none should abstain.
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


# Both tests below need a category that actually defers something, and the category they
# named is chosen by the corpus rather than by them. They ran against `safeguards` and
# `ui_api` until 2026-08-12, when the second resolution batch took both to zero deferrals -
# at which point one raised IndexError and the other passed while asserting "0 abstain on
# both sides", which is the silent-narrowing failure this repo has already been bitten by
# three times. `edge_hardware` holds the two deferrals least likely to close soon: one waits
# on the form_factor taxonomy proposal (#219) and one on a direction for the whole hardware
# ladder. Re-point them rather than loosening them if that stops being true.
def test_scoring_a_deferred_product_fails(monkeypatch, capsys):
    """The safeguards bug: a ladder ending in `otherwise` scoring what the repo declined."""
    computed, deferred = local_scores("edge_hardware")
    assert deferred, "pick a category that still defers something"
    published = {
        key: row(key[0], key[1], value[0], value[1], rule=0) for key, value in computed.items()
    }
    published.update({key: row(key[0], key[1], deferred=True) for key in deferred})
    victim = sorted(deferred)[0]
    published[victim] = row(victim[0], victim[1], 3, "open_weights", deferred=False, rule=6)
    assert run(monkeypatch, published, "edge_hardware") == 1
    assert "repo defers it, the warehouse does not know" in capsys.readouterr().out


def test_a_shared_abstention_is_not_a_divergence(monkeypatch, capsys):
    """Both sides declining is a curation work list, not a parity failure."""
    _, deferred = local_scores("edge_hardware")
    assert deferred, "pick a category that still defers something"
    published = {key: row(key[0], key[1], deferred=True) for key in deferred}
    assert run(monkeypatch, published, "edge_hardware") == 1  # the scored products are missing
    out = capsys.readouterr().out
    assert f"{len(deferred)} abstain on both sides" in out


def test_as_pair_normalizes_the_score_type():
    assert as_pair(row("x", "y", 4, "open_core")) == (4, "open_core")
    assert as_pair(row("x", "y")) is None
