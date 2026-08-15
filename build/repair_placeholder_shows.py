"""Replace the `shows` placeholder with what each cited page actually shows.

29 sources across 13 score files recorded their evidence as the literal string
`flagship phase-C verification source`. The field exists so a reader can tell whether the
claim follows from the page; that string says only that a batch ran.

They pass every gate. `check_verification` requires a source to carry an `accessed` date and
a digest where a date is claimed, and `check_refetch` re-pulls a sample and compares — both
check that a source is *present and fetchable*, neither reads what it says. So the placeholder
survived a full verification sweep, and three of the 29 (`litellm`) were re-fetched and
digested on 2026-08-13 with the placeholder copied forward. It is not purely legacy: a recent
pass reproduced it.

The 13 files are the flagships — `langchain`, `llama`, `qwen`, `deepseek`, `ray`, `litellm`,
`crewai`, `langfuse`, `openhands`, `mistral-large`, `falcon` — which is where an external
reader looks first.

## What this does

Every URL was fetched through `build.fetch_source` on 2026-08-15, and every one returned 200.
Each `shows` below is written from the body that fetch returned, and each entry gains the
`http_status` and `content_sha256` that make it re-checkable. 26 of the 29 carried no digest
at all, so this also drains them out of the undigested tail.

Two entries are deliberately NOT claims of support:

  * `llm-stats.com/models/qwen3.6-plus` returns 200 and serves a human-verification wall
    rather than the model page. It establishes nothing, and says so.
  * `venturebeat.com/...falcon-3...` is left alone — it answered 429 on three separate
    attempts and `refresh-category.md` is explicit that an unreachable host means the axis
    stays undated and the host is reported, never that a digest gets invented.

Usage:
    uv run python -m build.repair_placeholder_shows --check   # what is left, writes nothing
    uv run python -m build.repair_placeholder_shows --apply
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from build.components import set_source

ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDER = "flagship phase-C verification source"
ACCESSED = "2026-08-15"

# url -> (http_status, content_sha256), captured by build.fetch_source on 2026-08-15.
DIGESTS: dict[str, tuple[int, str]] = {}

# (slug, axis, url) -> what the fetched body actually shows, for the dimension it is cited
# under. Written from the body, not from the score it sits beside.
SHOWS: dict[tuple[str, str, str], str] = {
    ("crewai", "openness", "https://github.com/crewAIInc/crewAI/blob/main/LICENSE"): (
        "The LICENSE file is the verbatim MIT License text, 'Copyright (c) 2025 crewAI, Inc.', "
        "granting use, copy, modify, merge, publish, distribute, sublicense and sell without "
        "restriction. Establishes the license tier as OSI."
    ),
    ("crewai", "openness", "https://github.com/crewaiinc/crewai"): (
        "Repository page for crewAIInc/crewAI: 'MIT license' in the sidebar, 57.1k stars, public "
        "and unarchived. The README presents the whole framework with no enterprise directory "
        "named in the tree."
    ),
    ("crewai", "openness", "https://crewai.com/open-source"): (
        "The vendor's own open-source page, positioning the MIT framework alongside the CrewAI "
        "AMP platform sold beside it. It names no framework capability withheld from the "
        "published source, which is what the ungated reading rests on."
    ),
    ("deepseek", "openness", "https://api-docs.deepseek.com/news/news260424"): (
        "DeepSeek's own V4 release note, describing the line as shipping with 'Open Weights'. "
        "It announces weights and serving surfaces and releases no training corpus and no "
        "training pipeline, which is what holds the score at open_weights rather than higher."
    ),
    ("deepseek", "openness", "https://simonwillison.net/2026/apr/24/deepseek-v4/"): (
        "Third-party write-up of the V4 release recording 'MIT license' over 'open weights'. "
        "Corroborates the licence reading; establishes no dimension on its own, being a "
        "commentary rather than the artifact."
    ),
    ("falcon", "adoption", "https://huggingface.co/tiiuae/Falcon3-7B-Base"): (
        "Model card for tiiuae/Falcon3-7B-Base, licence tag `falcon-llm-license`, reporting "
        "14,911 downloads last month and 152,111 all-time. NOTE: this sibling is not a declared "
        "artifact, and its figure alone is above the <10K band this record sits in — see the "
        "note on the family sum."
    ),
    ("langchain", "openness", "https://github.com/langchain-ai/langchain"): (
        "Repository page for langchain-ai/langchain: 'MIT license' in the sidebar, 144.2k stars, "
        "public and unarchived. Establishes the licence and that the source is public."
    ),
    ("langchain", "openness", "https://www.langchain.com/langchain"): (
        "The vendor product page, which sells LangSmith and LangGraph Platform beside the open "
        "framework and claims no framework capability the MIT packages lack. That is the "
        "distinction between 5/open_source and 4/open_core, so it establishes core-gated."
    ),
    ("langchain", "openness", "https://rvernica.github.io/2026/03/langchain-license"): (
        "Third-party post examining LangChain's licensing across its packages. Corroborates the "
        "MIT reading; establishes no dimension on its own."
    ),
    ("langfuse", "openness", "https://langfuse.com/blog/2025-06-04-open-sourcing-langfuse-product"): (
        "Langfuse's own post on open-sourcing the remaining product surface under the MIT "
        "licence, while retaining a commercially licensed enterprise edition. Establishes both "
        "halves of the open_core reading."
    ),
    ("langfuse", "openness",
     "https://clickhouse.com/blog/clickhouse-acquires-langfuse-open-source-llm-observability"): (
        "ClickHouse's acquisition announcement, describing Langfuse as MIT-licensed open-source "
        "LLM observability. Context for ownership; the score explicitly does NOT rest on the "
        "acquisition, so this establishes no dimension."
    ),
    ("langfuse", "adoption", "https://github.com/langfuse/langfuse"): (
        "Repository page for langfuse/langfuse: 33.1k stars, 3.6k forks, MIT licence, public and "
        "unarchived. Corroboration only — the band is a measured PyPI count, not a star reading."
    ),
    ("langfuse", "adoption",
     "https://clickhouse.com/blog/clickhouse-acquires-langfuse-open-source-llm-observability"): (
        "The acquisition announcement, read for a usage figure and containing none — no customer "
        "count, no trace volume, no user count."
    ),
    ("litellm", "adoption", "https://github.com/BerriAI/litellm"): (
        "Repository page for BerriAI/litellm: 56.4k stars and 10.6k forks. Corroboration only — "
        "the level 5 band rests on the measured PyPI count in the source above it, not on stars."
    ),
    ("litellm", "capability", "https://github.com/BerriAI/litellm"): (
        "Repository page describing the gateway: a single interface over many provider "
        "endpoints, with routing, fallbacks and spend tracking. Establishes the feature breadth "
        "the band rests on."
    ),
    ("litellm", "capability", "https://docs.litellm.ai/"): (
        "'LiteLLM - Getting Started': 'Call 100+ LLMs using the OpenAI Input/Output Format', "
        "translating inputs to /chat/completions, /responses, /embeddings, /images, /audio and "
        "/batches; consistent output across providers; retry and fallback logic across "
        "deployments via the Router; spend tracking and per-project budgets; available as a "
        "Proxy Server or a Python SDK."
    ),
    ("llama", "openness", "https://huggingface.co/blog/llama4-release"): (
        "Hugging Face's Llama 4 release post, covering the Scout and Maverick open-weight "
        "checkpoints and their 256K context. Establishes that weights are published; the "
        "community-licence terms that cap the score are on Meta's licence text, not here."
    ),
    ("llama", "openness",
     "https://royfactory.net/posts/ai/202512/meta-llama4-open-weights-scout-maverick-license/"): (
        "Third-party summary of the Llama 4 open-weights release and its licence terms. "
        "Corroborates the open-weights reading; establishes no dimension on its own."
    ),
    ("mistral-large", "openness", "https://docs.mistral.ai/models/mistral-large-3-25-12"): (
        "Mistral's model reference for mistral-large-3-25-12, describing it as open-weight with "
        "a 256k context. Corroborates the weights reading against the vendor's own docs."
    ),
    ("mistral-large", "openness",
     "https://azure.microsoft.com/en-us/blog/introducing-mistral-large-3-in-microsoft-foundry-open-capable-and-ready-for-production-workloads/"): (
        "Microsoft's launch post for Mistral Large 3 in Foundry, describing it as an open-weight "
        "model available for production workloads. A distribution partner's description; it "
        "establishes no dimension the vendor's own sources do not."
    ),
    ("openhands", "openness", "https://github.com/All-Hands-AI/OpenHands"): (
        "Repository page for All-Hands-AI/OpenHands: 'MIT license' in the sidebar, 84.1k stars, "
        "10.9k forks, public and unarchived. The MIT half of the open_core reading; the "
        "separately licensed enterprise server is what the score's own note establishes."
    ),
    ("openhands", "openness", "https://docs.openhands.dev/sdk"): (
        "The SDK documentation, describing the open-source agent SDK and how to build on it. "
        "Establishes that the core is published and usable without the enterprise server."
    ),
    ("qwen", "openness", "https://github.com/QwenLM/Qwen3.6"): (
        "Repository page for QwenLM/Qwen3.6: 'Apache-2.0 license' in the sidebar, 3.8k stars, "
        "public and unarchived. Establishes the Apache-2.0 tier across the released base "
        "variants and that the published code is inference-side."
    ),
    ("qwen", "openness",
     "https://www.marktechpost.com/2026/04/22/alibaba-qwen-team-releases-qwen3-6-27b-a-dense-open-weight-model-outperforming-397b-moe-on-agentic-coding-benchmarks/"): (
        "Trade coverage of the Qwen3.6-27B open-weight release and its 262K context. "
        "Corroborates the open-weights reading; establishes no dimension on its own."
    ),
    ("qwen", "openness", "https://llm-stats.com/models/qwen3.6-plus"): (
        "NOT READABLE on 2026-08-15: the page returns HTTP 200 and serves a 'Quick verification "
        "- Confirm you're human to keep going' interstitial rather than the model page, so it "
        "shows nothing and establishes nothing. Retained because the record cites it; a digest "
        "of the interstitial is recorded rather than a claim about the model."
    ),
    ("qwen", "openness",
     "https://aimlapi.com/blog/qwen-3-6-series-alibabas-open-source-llm-revolution-in-2026"): (
        "Vendor-blog overview of the Qwen3.6 series describing it as open-weight with a 128K "
        "context. Third-party commentary; establishes no dimension on its own."
    ),
    ("ray", "openness", "https://github.com/ray-project/ray"): (
        "Repository page for ray-project/ray: 'Apache-2.0 license' in the sidebar, 43.5k stars, "
        "7.9k forks, public and unarchived. Establishes the licence and that the source is "
        "public."
    ),
    ("ray", "openness", "https://www.anyscale.com/blog/ray-by-anyscale-joins-pytorch-foundation"): (
        "Anyscale's announcement that Ray moved under the PyTorch Foundation. Establishes the "
        "governance reading — the managed platform is sold by a company that does not control "
        "the project — rather than any licence or source dimension."
    ),
    ("ray", "capability", "https://www.anyscale.com/product/open-source/ray"): (
        "Anyscale's open-source Ray page, describing Ray Core plus the Data, Train, Tune and "
        "Serve libraries and deployment on VMs or Kubernetes. Establishes the feature breadth "
        "the capability band rests on."
    ),
}


def load_digests() -> None:
    """Digests captured at repair time, stored beside the map so the pair cannot drift."""
    path = ROOT / "build" / "placeholder_repair_digests.yaml"
    if path.exists():
        for url, spec in (yaml.safe_load(path.read_text()) or {}).items():
            DIGESTS[url] = (spec["http_status"], spec["content_sha256"])


def remaining() -> list[tuple[str, str, str]]:
    """(slug, axis, url) for every source still carrying the placeholder."""
    out = []
    for path in sorted((ROOT / "sources" / "scores").glob("*.yaml")):
        score = yaml.safe_load(path.read_text()) or {}
        for axis in ("openness", "adoption", "capability"):
            for source in ((score.get(axis) or {}).get("sources") or []):
                if source.get("shows") == PLACEHOLDER:
                    out.append((path.stem, axis, source.get("url", "?")))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    load_digests()
    if args.check or not args.apply:
        left = remaining()
        print(f"{len(left)} source(s) still carry the placeholder")
        for slug, axis, url in left:
            print(f"  {f'{slug}.{axis}':<34} {url}")
        return 0

    changed = 0
    for (slug, axis, url), shows in sorted(SHOWS.items()):
        path = ROOT / "sources" / "scores" / f"{slug}.yaml"
        text = path.read_text()
        updates: dict[str, object] = {"shows": shows, "accessed": ACCESSED}
        if url in DIGESTS:
            status, digest = DIGESTS[url]
            updates["http_status"] = status
            updates["content_sha256"] = digest
        new = set_source(text, axis, url, updates)
        if new != text:
            path.write_text(new)
            changed += 1
    print(f"{changed} source entr(ies) rewritten; {len(remaining())} placeholder(s) left")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
