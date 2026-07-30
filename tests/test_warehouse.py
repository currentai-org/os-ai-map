"""Tests for the nonce-forcing query helper.

No network here. What matters is that the nonce cannot be skipped and that two calls with
the same SQL do not produce the same query text, since the cache keys on exactly that.
"""

import pytest

from build.apply_scores import fetch_computed
from build.warehouse import cache_busted, has_nonce, query, require_api_key


def test_a_nonce_is_appended():
    assert has_nonce(cache_busted("SELECT 1"))


def test_two_calls_on_identical_sql_differ():
    """The whole point. Identical text hits the cache, so the text must not be identical."""
    assert cache_busted("SELECT 1") != cache_busted("SELECT 1")


def test_the_nonce_is_a_trailing_comment():
    """A comment leaves the plan and the result untouched; a predicate would not."""
    busted = cache_busted("SELECT 1 FROM t")
    body, _, nonce = busted.partition("-- cache-bust")
    assert body.strip() == "SELECT 1 FROM t"
    assert len(nonce.strip()) == 36  # a uuid4


def test_query_requires_a_key_before_it_tries_the_network(monkeypatch):
    monkeypatch.delenv("OSO_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OSO_API_KEY"):
        require_api_key()


def test_fetch_computed_goes_through_the_helper(monkeypatch):
    """apply_scores must not build its own SQL string. Asserted by capturing what reaches
    the helper: if the port were reverted, the captured text would have no nonce."""
    seen: list[str] = []

    def fake_query(sql: str) -> list[dict]:
        seen.append(sql)
        return []

    monkeypatch.setattr("build.apply_scores.query", fake_query)
    fetch_computed("base_pretrained")
    assert len(seen) == 1
    assert "currentai.scores.openness_computed" in seen[0]
    assert "WHERE category_slug = 'base_pretrained'" in seen[0]
    # The nonce is added inside `query`, so what apply_scores hands over must NOT carry one -
    # a nonce here would mean a second, hand-rolled implementation had crept back in.
    assert not has_nonce(seen[0])
    assert has_nonce(cache_busted(seen[0]))


def test_query_is_the_only_entry_point_and_always_busts(monkeypatch):
    captured: list[str] = []

    class FakeFrame:
        def to_dict(self, _how):
            return [{"ok": 1}]

    class FakeClient:
        def to_pandas(self, sql):
            captured.append(sql)
            return FakeFrame()

    import sys
    import types

    module = types.ModuleType("pyoso")
    module.Client = FakeClient
    monkeypatch.setitem(sys.modules, "pyoso", module)
    monkeypatch.setenv("OSO_API_KEY", "test-key")

    assert query("SELECT 1") == [{"ok": 1}]
    assert has_nonce(captured[0])
