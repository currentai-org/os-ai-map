"""Backfill `adoption.banded_quantity` — say what a reported_traction band actually counted.

## The contract this implements

**Old.** A `reported_traction` record carries a `level`, an optional word from the three-word
vocabulary in `reach`, and a `note`. Where the level was read off something other than the
product — a parent platform's user base, a revenue figure, a star count, a cumulative total —
that fact lived in the note's prose and nowhere a machine could see it.

**New.** An optional `banded_quantity` string names what was counted, whenever that is not a
current usage figure for the product itself. Absent means the level is a judgment about this
product with no borrowed quantity behind it, which is a real and common case: `claude-opus`
and `claude-fable` both record a market-position reading and cite no number at all.

**Why the field rather than better prose.** `active_users` already solved exactly this. Its
route in `sources/signal_routing.yaml` carries an `attribution_note` requiring a record to
"say in its note which quantity it actually banded on" where the figure is not an active
count, and three records name their substitution because of it. `reported_traction` is the
instrument where the substitution is most common — measured 2026-08-15, 19 of 109 records
band on a parent platform — and it had no equivalent. Curators wrote the caveat in prose
every single time; nothing could read it, so nothing could count it, and a consumer reading
`level: 4` off the warehouse got a number about Replit or about Perplexity's chat app with
nothing attached saying so.

**What is NOT changing.** No level moves. This migration adds a field and touches nothing
else — the whole point is that the curators' judgments were right and only illegible. The
before/after distribution in `--report` is the evidence for that claim.

## Idempotent and re-runnable

`components.put_field` sets the field where it exists and inserts it where it does not, with
the reparse assertion that catches an insert landing inside a neighboring folded scalar.
Running this twice is a no-op the second time.

Usage:
    uv run python -m build.migrate_banded_quantity --report   # distributions, writes nothing
    uv run python -m build.migrate_banded_quantity --apply
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import yaml

from build.components import put_field

ROOT = Path(__file__).resolve().parents[1]

# What each band was actually read off, transcribed from the record's own note. Every value
# here is a restatement of something the note already said — this migration researches
# nothing, and a value that could not be sourced from the note is not in this map.
#
# Four shapes recur, and the wording keeps them tellable apart:
#   * a parent platform's reach, where the product is a feature inside something larger;
#   * a real count of the product that is not a current active one (cumulative, all-time,
#     lifetime, weekly where the scale is monthly);
#   * a proxy of a different kind entirely — revenue, funding, stars, citations;
#   * nothing at all, where the note cites a figure only to reject it.
BANDED_QUANTITY: dict[str, str] = {
    # --- a parent platform's reach, not this product's ---
    "amazon-bedrock-evaluations": "Amazon Bedrock platform footprint, not the Evaluations feature",
    "azure-ai-foundry-observability": (
        "Microsoft Foundry platform reach, not usage of the observability surface"
    ),
    "azure-ai-model-inference": "Azure enterprise base, not this inference endpoint",
    "datadog-llm-observability": (
        "Datadog platform installed base, not the LLM Observability module"
    ),
    "vertex-ai-model-observability": "Vertex AI platform reach, not the tracing surface",
    "grok": "the X and grok.com surfaces the tier powers, not a per-model count",
    "gemini-pro": (
        "the Gemini app, AI Studio, API and Vertex surfaces the Pro tier powers, "
        "not a per-model count"
    ),
    "glean-assistant": (
        "Glean platform annual recurring revenue ($300M, May 2026) and deployment breadth, "
        "not a seat count"
    ),
    "glean-workplace-search-ai": (
        "the same Glean platform ARR and seat base as the Assistant record, not an "
        "independent measurement"
    ),
    "modal-sandboxes": "Modal platform teams (10,000+), not Sandboxes sessions or jobs",
    "northflank-sandboxes": (
        "Northflank platform developers (100k+) and organizations (2,000+), not Sandboxes use"
    ),
    "replit-agent": (
        "Replit platform registered users (50M+, March 2026), not an agent active count"
    ),
    "perplexity-sonar-api": (
        "Perplexity consumer-app MAU (45M+, aggregator-reported), not API requests or developers"
    ),
    "new-relic-ai-monitoring": (
        "New Relic platform users (~6.6M, aggregator-reported), not the AI Monitoring module"
    ),
    "lumo": "Proton's account base (100M+), not Lumo use",
    "coop": (
        "adopter deployments including Notion and carried-over Cove clients; the 150M+ "
        "messages figure is one adopter's platform, not Coop's own use"
    ),
    "rockchip-rk3588": (
        "the multi-vendor SBC set the SoC powers, not units shipped of the chip"
    ),
    "openrlhf": "named adopters listed in the repository, not a download or user count",
    # --- a real count of the product, but not a current active one ---
    "v0": "cumulative users since GA (4M+), not an active count",
    "windsurf": (
        "a vendor headline user total (1M+) with no period attached, so not an active count"
    ),
    "codex-cli": (
        "weekly active developers (6M+), weekly rather than the monthly the scale is written in"
    ),
    "huggingchat-chat-ui": (
        "lifetime users of the hosted product (1M+), a vendor statement at one remove"
    ),
    "open-llm-leaderboard": (
        "peak lifetime figures of an archived leaderboard: 13,000+ models evaluated and "
        "2M+ unique visitors"
    ),
    "math": (
        "all-time downloads (1,034,712) of a takedown-walled repo now reporting 0 in the "
        "trailing 30 days"
    ),
    "hailo-8": (
        "a vendor-reported user count (100K+) that is not re-derivable — hailo.ai answers 403"
    ),
    "groq-inference": "a vendor-reported developer count (5M+, June 2026)",
    # --- a proxy of a different kind: revenue, funding, throughput, stars, citations ---
    "claude-code": "revenue run-rate (~$2.5B, February 2026), not a developer count",
    "arize": (
        "platform throughput (~1T spans and ~1B evals a month), not an account or user count"
    ),
    "sambanova-cloud": (
        "third-party routed token volume via OpenRouter (~1.65B tokens on one day), not users"
    ),
    "ernie": (
        "the ERNIE/Wenxiaoyan assistant app's MAU (~200M), which is app-level rather than "
        "model-level"
    ),
    "datology-ai": "funding raised ($57.5M), which is credibility rather than usage",
    "predibase": (
        "the acquisition value ($100M-$500M, press estimate), not a jobs or customer count"
    ),
    "openpcc": (
        "GitHub stars (948) and seed funding ($5M), with no production adopter documented"
    ),
    "inflection": (
        "the $650M technology licence and acqui-hire, neither of which is an adoption figure"
    ),
    "openhands": "GitHub stars (83.9k) and Series A funding ($18.8M), not a user count",
    "opencode": "npm downloads of opencode-ai (8,643,056 in the trailing month) and 197.0k stars",
    "opencompass": "GitHub stars (7,299) and framework distribution breadth",
    "kata-containers": (
        "GitHub stars (~8k), corroboration only; no download or user figure is published"
    ),
    "tensorrt-llm": "GitHub stars (14,342), not a download or user count",
    "confident-ai": (
        "a vendor customer claim (500+ companies), corroborated by DeepEval's GitHub stars "
        "(17,578)"
    ),
    "laminar": (
        "GitHub stars (~3k); the ~17M lmnr PyPI figure is treated as CI/mirror-inflated and "
        "discounted rather than banded"
    ),
    "helm": (
        "research citations and hosted-leaderboard use; crfm-helm on PyPI at ~3,142 a month "
        "understates reach rather than measuring it"
    ),
    "inspect-ai": (
        "frontier-lab adoption; the ~9.9M PyPI downloads are treated as CI-inflated "
        "corroboration rather than the basis"
    ),
    "swe-bench": (
        "frontier release-report citations; the ~31.5M PyPI downloads are treated as "
        "runner-inflated corroboration rather than the basis"
    ),
    "osworld": (
        "frontier-lab release-report citations; 2.9k GitHub stars corroborate only"
    ),
    "compar-ia": (
        "the hosted arena's own collected data — 600,000+ prompts and 250,000+ preference "
        "votes — rather than repository or user counts"
    ),
    "openfn": (
        "workflow runs (~5M a year, about 417k a month) across 55+ countries, an "
        "institutional deployment count"
    ),
    "agent2agent-protocol": (
        "supporting organizations (150+) and shipped integrations, a breadth count rather "
        "than a usage figure"
    ),
    "cerebras-inference": "named customer testimonials, not a developer or usage count",
    "fireworks-inference": "named high-volume production customers, not a user count",
    "bedrock-guardrails": "named customer logos, not a count of anything",
    "lakera-guard": (
        "a '1M+ hackers' figure from the Gandalf game and 1,000 Slack members, neither of "
        "which counts users of the product"
    ),
    "osprey": (
        "production deployment at named platforms and the v1.0 post's 50M+ figure; the "
        "previous '400M daily actions' is no longer carried by any cited source"
    ),
    # --- nothing at all: the note cites a figure only to reject it ---
    "openai-moderation": (
        "none published; the level reads the distribution of the free default moderation "
        "endpoint rather than any figure"
    ),
    "azure-content-safety": (
        "none published; the level reads the default content-safety layer's distribution "
        "in front of Azure AI"
    ),
    "perspective-api": "none published; Jigsaw has never published a usage figure",
    "snorkel-flow": (
        "none published; the withdrawn $1.3B valuation was never an adoption figure"
    ),
}


def score_path(slug: str) -> Path:
    return ROOT / "sources" / "scores" / f"{slug}.yaml"


def apply(slug: str, value: str) -> bool:
    """Write `adoption.banded_quantity`. Returns whether the file changed."""
    path = score_path(slug)
    text = path.read_text()
    doc = yaml.safe_load(text)
    adoption = doc.get("adoption") or {}
    if adoption.get("banded_quantity") == value:
        return False
    # The field describes what the level rests on, so it reads before the prose that
    # elaborates it. Records without a `note` fall back to the `sources` anchor every
    # axis has.
    anchor = "note" if "note" in adoption else "sources"
    path.write_text(put_field(text, value, axis="adoption", key="banded_quantity", before=anchor))
    return True


def report() -> None:
    """Before/after distributions — migrate-axis step 9.

    The claim this has to support is that the migration added a field and moved nothing
    else, so it prints the level and signal_type distributions rather than a count of
    files touched. A migration that reshaped the axis would show up here.
    """
    levels: Counter = Counter()
    instruments: Counter = Counter()
    covered = Counter()
    for path in sorted((ROOT / "sources" / "scores").glob("*.yaml")):
        adoption = (yaml.safe_load(path.read_text()) or {}).get("adoption") or {}
        instruments[adoption.get("signal_type")] += 1
        if adoption.get("signal_type") == "reported_traction":
            levels[adoption.get("level")] += 1
            covered["with banded_quantity" if adoption.get("banded_quantity") else "without"] += 1

    print("signal_type across the corpus:")
    for name, n in instruments.most_common():
        print(f"  {str(name):<20}{n:>5}")
    print("\nreported_traction levels:")
    for level in sorted(levels, key=lambda x: (x is None, x)):
        print(f"  level {level}: {levels[level]}")
    print("\nreported_traction coverage:")
    for name, n in covered.most_common():
        print(f"  {name:<24}{n:>5}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="write the files")
    parser.add_argument("--report", action="store_true", help="print distributions only")
    args = parser.parse_args()

    if args.report or not args.apply:
        report()
        if not args.apply:
            print(f"\n{len(BANDED_QUANTITY)} slugs in the map. Pass --apply to write.")
            return 0

    missing = [slug for slug in BANDED_QUANTITY if not score_path(slug).exists()]
    if missing:
        print(f"no score file for: {', '.join(missing)}")
        return 1

    changed = sum(apply(slug, value) for slug, value in sorted(BANDED_QUANTITY.items()))
    print(f"\n{changed} file(s) changed, {len(BANDED_QUANTITY) - changed} already current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
