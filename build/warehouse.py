"""The only supported way to read the OSO warehouse from `build/`.

## Why a helper for one line of SQL

Warehouse query results are cached keyed on the QUERY TEXT. A tool that issues a fixed
string therefore keeps receiving its FIRST answer for that string, and it never self-heals:
re-running it, waiting, or re-materializing the model changes nothing, because the text is
still the same text. There is no cache-control knob to reach for from the client side.

This has already cost real time. `build/apply_scores.py` returned the pre-run baseline for
a full run cycle after the models had re-materialized, and adding a single trailing comment
to the same SQL returned the fresh numbers. The failure is silent and confidence-inspiring
in the wrong direction: the tool reports success, against data from before the change it
was checking.

Verification tooling is the worst possible place for that, because a stale read there
writes a stale date into `sources/scores/` under a field whose name asserts a fresh check.
So the nonce lives here rather than in each caller's discipline. `query()` cannot be called
without one — there is no parameter to switch it off.

Note that this defeats the cache on purpose and therefore costs a real query every time.
That is the intended trade: these are low-frequency build and verification reads, and a
wrong answer is far more expensive than a slow one.

Usage:
    from build.warehouse import query
    rows = query("SELECT product_slug FROM currentai.scores.openness_computed")
"""

from __future__ import annotations

import os
import uuid

MARKER = "-- cache-bust"


def cache_busted(sql: str) -> str:
    """`sql` with a unique trailing comment, so no two calls share a cache key.

    A comment rather than anything semantic: it changes the text, which is what the cache
    keys on, while leaving the query plan and the result identical. A `WHERE 1=1 AND
    '<uuid>' = '<uuid>'` would also work and would be a real predicate the planner has to
    carry, which is a worse trade.
    """
    return f"{sql.rstrip()}\n{MARKER} {uuid.uuid4()}\n"


def has_nonce(sql: str) -> bool:
    """Whether a query text already carries a nonce. For tests and for asserting callers."""
    return MARKER in sql


def require_api_key() -> str:
    """The key, or a clear failure. Every caller here needs it, so it is asked for once."""
    token = os.environ.get("OSO_API_KEY")
    if not token:
        raise RuntimeError("OSO_API_KEY must be set to read the warehouse")
    return token


def query(sql: str) -> list[dict]:
    """Run `sql` with a forced nonce and return rows as plain dicts.

    Returns dicts rather than a DataFrame so callers do not have to think about pandas
    null sentinels. `build/apply_scores.has_date` exists because a null DATE arrives as
    NaT or float nan depending on the column dtype, and both satisfy `is not None`.
    """
    from pyoso import Client

    require_api_key()
    return Client().to_pandas(cache_busted(sql)).to_dict("records")
