"""The two allowlists the prose gates read: notes whose date, or whose figure, is a fact about
the product rather than about the reading. Both are two-sided in tests/test_score_notes.py (an
entry whose note no longer carries the date or figure must leave), and build/prose_edit.py
refuses a rewrite that would drop an allowlisted date or add a figure that is not allowlisted.
docs/reference/product-copy.md, "No dates, no chronology" and "No usage figure", is the rule."""

# Axes whose note states a date that is a fact about the PRODUCT or the SOURCE, not about when
# somebody looked: a GA or ship date, an archive date, a measurement window, a retirement date.
# Each was reviewed when the score-history sweep (#323) ran. Adding to this list is a claim that
# the date would still be true if nobody ever re-read the record.
DATES_THAT_ARE_PRODUCT_FACTS = {
    # --- Model Context Protocol specification revisions, added 2026-09-17 with the
    # agent_protocols category. These dates are the NAMES OF SPECIFICATION VERSIONS -
    # 2024-11-05, 2025-03-26, 2025-06-18, 2025-11-25, 2026-07-28 - and the category's ladder
    # requires every implementation to name the revision its coverage was read against, because
    # band 5 asks for the current one. The date is the product's own version string, true
    # whether or not anybody re-reads the record, and removing it would delete the denominator
    # the band is computed from. `mcp-apps` carries its own extension spec version, 2026-01-26.
    ("mcp-apps", "capability"),
    ("mcp-go", "capability"),
    ("mcp-go-sdk", "capability"),
    ("mcp-java-sdk", "capability"),
    ("mcp-python-sdk", "capability"),
    ("mcp-rust-sdk", "capability"),
    ("mcp-swift-sdk", "capability"),
    ("mcp-typescript-sdk", "capability"),
    ("amazon-bedrock-evaluations", "adoption"),
    ("apertus", "adoption"),
    # A release date on each side of a trailing registry line. The whole reason the band does
    # not rest on the download figure is that the registry stopped at 1.0.4 in June while the
    # repository is on 2.1.0 from August; drop the dates and the note asserts a lag it can no
    # longer show. Both are publication facts, true whether or not anybody re-reads them.
    ("areal", "adoption"),
    ("apertus", "openness"),
    ("atropos", "adoption"),
    ("claude-haiku", "capability"),
    ("claude-sonnet", "capability"),
    ("claude-sonnet", "openness"),
    ("cloudflare-sandboxes", "adoption"),
    ("compar-ia", "adoption"),
    ("cruxeval", "adoption"),
    ("google-coral-dev-board", "adoption"),
    ("khoj", "openness"),
    ("kimi", "adoption"),
    ("langflow", "adoption"),
    ("localai", "adoption"),
    ("mmmu", "openness"),
    ("n8n", "adoption"),
    ("open-llm-leaderboard", "adoption"),
    ("perplexica", "adoption"),
    ("ragflow", "adoption"),
    ("sandbox-runtime", "adoption"),
    ("vercel-sandbox", "adoption"),
    # Same shape as areal: the PyPI upload of 2025-07-11 and the v1.0.1 release of 2026-05-15
    # are the two publication dates the 416-day gap is measured between.
    ("xtuner", "adoption"),
}


# Notes whose only "figure" is a durable fact about the product: a license threshold, a dataset
# size, a leaderboard score. The detector in build/prose_worklist.py reads any comma-grouped
# count as a usage figure and cannot tell these apart; a reader can. Adding here is a claim
# that the number would still be true if nobody ever re-read the record.
FIGURES_THAT_ARE_PRODUCT_FACTS = {
    ("humanitys-last-exam", "capability"),   # 2,500 questions: the dataset's size
    ("oasst1", "capability"),                # 9,209 examples: the QLoRA subset's size
    ("ernie", "capability"),                 # 1,223: a leaderboard score
    ("llama-instruct", "openness"),          # the Llama license's 700 million MAU threshold
    ("tulu", "openness"),                    # the same license threshold, inherited
    ("llama", "openness"),                   # the same license threshold
    ("kimi", "openness"),                    # the Modified MIT license's 100 million MAU threshold
    ("mineru", "openness"),                  # the AGPL exception's 100 million MAU threshold
}
