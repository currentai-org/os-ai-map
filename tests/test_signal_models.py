"""The signal-model sources this repo owns: do they satisfy the platform's contract?

`warehouse/models/` used to hold only SQL, and none of the `signal_*` models were in it at
all. Issue #173 records what that cost: the adoption bands lived in `signal_pypi` as a
hardcoded CASE nothing in the repo could see, and looking for the SQL where the runbook said
it lived turned up nothing, which reads as "no such model" rather than "the directory is
incomplete".

The npm and crates models are in the directory, so they can be checked here rather than after
a deploy rejects them. Two things are worth checking and one is not:

  * **The authoring contract.** `createDataModelRevision` validates a Python UDM before it is
    ever released — exactly one `@oso.model`, a return annotation, literal decorator
    arguments, fully-qualified `depends_on`, an allow-listed import set, no top-level
    statements. Every one of those is readable from the source with `ast`, and finding out at
    deploy time costs a round trip through a maintainer.
  * **The parsing.** Both registries answer with a different shape, both have a habit that
    misleads (npm reports zero for a missing day, crates.io omits the day), and the helpers
    that flatten them are pure functions. `oso` and `polars` are not installed here, so they
    are stubbed: the point is the arithmetic, not the frame.

What is NOT checked is whether the model runs. That needs the sandbox, the roster table and
the network, and asserting it here would be a fiction.
"""

from __future__ import annotations

import ast
import sys
import types
from datetime import date, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "warehouse" / "models"
PYTHON_MODELS = sorted(MODELS.glob("*.py"))

# The platform's allow list: the standard library except `sys`, plus these.
DATA_LIBRARIES = {"oso", "polars", "pandas", "pyarrow", "numpy"}


def _stub_environment() -> None:
    """Make `import oso` and `import polars` work without either package installed.

    The decorator has to be a no-op that returns the function, so the module imports and the
    helpers are reachable. Nothing here pretends to be a DataFrame — no test builds one.
    """
    if "oso" not in sys.modules:
        oso = types.ModuleType("oso")
        oso.model = lambda **_kwargs: (lambda function: function)  # type: ignore[attr-defined]
        oso.Context = object  # type: ignore[attr-defined]
        oso.AsyncContext = object  # type: ignore[attr-defined]
        oso.DataFrame = object  # type: ignore[attr-defined]
        sys.modules["oso"] = oso
    if "polars" not in sys.modules:
        polars = types.ModuleType("polars")
        for name in ("Utf8", "Int64", "Boolean", "Date"):
            setattr(polars, name, name)
        polars.Datetime = lambda _unit: "Datetime"  # type: ignore[attr-defined]
        polars.DataFrame = lambda *args, **kwargs: None  # type: ignore[attr-defined]
        sys.modules["polars"] = polars


@pytest.fixture(scope="module")
def daily():
    """The npm + crates fetch model, imported with `oso` and `polars` stubbed."""
    _stub_environment()
    import importlib.util

    path = MODELS / "signal_packages_package_downloads_daily.py"
    spec = importlib.util.spec_from_file_location("signal_packages_daily", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text())


def _models(tree: ast.Module) -> list[ast.AsyncFunctionDef | ast.FunctionDef]:
    out: list[ast.AsyncFunctionDef | ast.FunctionDef] = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            target = decorator.func if isinstance(decorator, ast.Call) else decorator
            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                if target.value.id == "oso" and target.attr == "model":
                    out.append(node)
    return out


def test_the_walk_finds_the_python_models():
    """Non-zero guard: every assertion below is vacuous over an empty glob."""
    assert PYTHON_MODELS, "no Python UDM sources found in warehouse/models/"


@pytest.mark.parametrize("path", PYTHON_MODELS, ids=lambda p: p.name)
def test_exactly_one_decorated_model_per_file(path: Path):
    """A revision holds exactly one model, and its name becomes the table name."""
    models = _models(_tree(path))
    assert len(models) == 1, f"{path.name}: found {len(models)} @oso.model functions, expected 1"


@pytest.mark.parametrize("path", PYTHON_MODELS, ids=lambda p: p.name)
def test_the_model_is_annotated_the_way_the_validator_requires(path: Path):
    """`async def` must take `oso.AsyncContext`, and the return must be `oso.DataFrame`.

    A mismatch is rejected at deploy with `context-annotation-mismatch`, which is a slow way
    to learn it.
    """
    model = _models(_tree(path))[0]
    assert model.returns is not None, f"{path.name}: no return annotation"
    assert ast.unparse(model.returns) in {
        "oso.DataFrame",
        "Iterator[oso.DataFrame]",
        "AsyncIterator[oso.DataFrame]",
    }, f"{path.name}: return annotation {ast.unparse(model.returns)} is not one the validator accepts"

    assert model.args.args, f"{path.name}: the model takes no context argument"
    annotation = model.args.args[0].annotation
    assert annotation is not None, f"{path.name}: the context argument is unannotated"
    expected = "oso.AsyncContext" if isinstance(model, ast.AsyncFunctionDef) else "oso.Context"
    assert ast.unparse(annotation) == expected, (
        f"{path.name}: {'async ' if isinstance(model, ast.AsyncFunctionDef) else ''}def must "
        f"annotate {expected}"
    )


@pytest.mark.parametrize("path", PYTHON_MODELS, ids=lambda p: p.name)
def test_decorator_arguments_are_literals_and_dependencies_are_fully_qualified(path: Path):
    """`depends_on` and `external_origins` are read statically by the validator.

    A computed value fails with `non-literal-depends-on`; a two-part table name fails with
    `non-fqn-depends-on`, which is the one a reader is most likely to write by hand.
    """
    model = _models(_tree(path))[0]
    call = next(
        decorator
        for decorator in model.decorator_list
        if isinstance(decorator, ast.Call)
    )
    for keyword in call.keywords:
        assert isinstance(keyword.value, (ast.List, ast.Constant)), (
            f"{path.name}: decorator argument {keyword.arg} is computed"
        )
        if isinstance(keyword.value, ast.List):
            for element in keyword.value.elts:
                assert isinstance(element, ast.Constant) and isinstance(element.value, str), (
                    f"{path.name}: {keyword.arg} holds a non-literal entry"
                )
        if keyword.arg == "depends_on" and isinstance(keyword.value, ast.List):
            for element in keyword.value.elts:
                table = element.value  # type: ignore[attr-defined]
                assert len([part for part in table.split(".") if part]) == 3, (
                    f"{path.name}: depends_on entry {table!r} is not org.dataset.table"
                )


@pytest.mark.parametrize("path", PYTHON_MODELS, ids=lambda p: p.name)
def test_only_allow_listed_imports_and_no_top_level_code(path: Path):
    """Third-party packages are blocked in the sandbox, and so is `sys`.

    `requests` is the trap: it is a dependency of this repo, so it imports fine locally and
    fails at deploy with `disallowed-import`.
    """
    tree = _tree(path)
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name.split(".")[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module.split(".")[0]]
        for name in names:
            assert name != "sys", f"{path.name}: `sys` is not importable in the sandbox"
            assert name in DATA_LIBRARIES or name in sys.stdlib_module_names, (
                f"{path.name}: {name} is neither stdlib nor an allow-listed data library"
            )

    for node in tree.body:
        allowed = (
            ast.Import,
            ast.ImportFrom,
            ast.FunctionDef,
            ast.AsyncFunctionDef,
            ast.Assign,
            ast.AnnAssign,
            ast.Expr,  # the module docstring
        )
        assert isinstance(node, allowed), (
            f"{path.name}: top-level {type(node).__name__} is rejected as "
            f"disallowed-toplevel-stmt"
        )
        if isinstance(node, ast.Assign):
            assert all(isinstance(target, ast.Name) for target in node.targets), (
                f"{path.name}: top-level assignment target is not a plain name"
            )
            assert isinstance(node.value, (ast.Constant, ast.Tuple, ast.List, ast.Dict)), (
                f"{path.name}: top-level assignment value is not a literal"
            )


@pytest.mark.parametrize("path", PYTHON_MODELS, ids=lambda p: p.name)
def test_the_returned_columns_match_the_declared_schema(path: Path):
    """The row builder and the polars schema are written twice; they must agree.

    They are two literals in one file, and a column added to one and not the other surfaces at
    query time as a type error rather than at deploy as a rejection. `signal_github.repo_state`
    carries the same duplication over 32 columns.
    """
    tree = _tree(path)
    schema_keys: list[list[str]] = []
    row_keys: list[list[str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        keys = [
            key.value
            for key in node.keys
            if isinstance(key, ast.Constant) and isinstance(key.value, str)
        ]
        if len(keys) != len(node.keys) or not keys:
            continue
        values = node.values
        if all(
            isinstance(value, (ast.Attribute, ast.Call))
            and "pl." in ast.unparse(value)
            for value in values
        ):
            schema_keys.append(keys)
        else:
            row_keys.append(keys)

    assert schema_keys, f"{path.name}: no polars schema literal found"
    for schema in schema_keys:
        # A dict sharing no key with the schema is something else entirely — the request
        # headers, for instance — so only the row literals are compared.
        for row in [keys for keys in row_keys if set(keys) & set(schema)]:
            assert row == schema, (
                f"{path.name}: a row literal and the declared schema disagree.\n"
                f"  row:    {row}\n  schema: {schema}"
            )


def test_npm_keeps_zero_days_because_the_total_already_counts_them(daily):
    """npm reports 0 for a day it has no data for, and that 0 is inside its own total.

    `n8n` had two in a 30-day window, both Sundays. Dropping them would make a total depressed
    by a data gap indistinguishable from one depressed by a fall in installs, and the windowed
    model reports `days_observed` so the difference is visible.
    """
    payload = {
        "package": "n8n",
        "start": "2026-07-11",
        "end": "2026-07-13",
        "downloads": [
            {"day": "2026-07-11", "downloads": 9296},
            {"day": "2026-07-12", "downloads": 0},
            {"day": "2026-07-13", "downloads": 9240},
        ],
    }
    series = daily.series_for("npm", payload)
    assert series == [
        (date(2026, 7, 11), 9296),
        (date(2026, 7, 12), 0),
        (date(2026, 7, 13), 9240),
    ]


def test_crates_sums_the_version_rows_and_the_roll_up(daily):
    """crates.io splits a day across versions and hides older ones in `extra_downloads`.

    Reading only `version_downloads` undercounts any crate old enough to have retired a
    version, which is every crate the map is likely to declare.
    """
    payload = {
        "version_downloads": [
            {"version": 1, "date": "2026-08-10", "downloads": 4},
            {"version": 2, "date": "2026-08-10", "downloads": 6},
        ],
        "meta": {"extra_downloads": [{"date": "2026-08-10", "downloads": 14}]},
    }
    assert daily.series_for("crates", payload) == [(date(2026, 8, 10), 24)]


def test_a_dead_artifact_becomes_one_row_carrying_its_status(daily):
    """A 404 has to be a row. An absent row reads as "not fetched yet", which is different.

    The registry declared 106 PyPI artifacts while `signal_pypi` held 98, so the roster running
    ahead of the signal is the normal state and must not look like a dead package.
    `playwright-mcp` carried `@anthropic-ai/mcp-playwright` for weeks, which api.npmjs.org
    answers 404 for, and nothing could say so.
    """
    fetched_at = datetime(2026, 8, 14, 12, 0, 0)
    rows = daily.rows_for(
        "playwright-mcp", "software", "npm", "@anthropic-ai/mcp-playwright", None, 404, fetched_at
    )
    assert len(rows) == 1
    assert rows[0]["http_status"] == 404
    assert rows[0]["day"] is None
    assert rows[0]["downloads"] is None
    assert rows[0]["package"] == "@anthropic-ai/mcp-playwright"


def test_a_scoped_npm_name_is_not_encoded(daily):
    """api.npmjs.org answers /range/<period>/@playwright/mcp and 404s the encoded form."""
    url = daily.request_url("npm", "@playwright/mcp", "2026-02-14:2026-08-13")
    assert url == (
        "https://api.npmjs.org/downloads/range/2026-02-14:2026-08-13/@playwright/mcp"
    )


def test_an_unknown_registry_routes_nowhere_rather_than_somewhere_wrong(daily):
    """A kind this model does not read must yield no URL and no series.

    The roster is a SQL filter today, so this is unreachable — which is the reason to assert
    it. A widened filter should produce a row with no data, never a crates URL built from a Go
    module path.
    """
    assert daily.request_url("go", "github.com/yomorun/yomo", "x") is None
    assert daily.series_for("go", {"downloads": [{"day": "2026-08-10", "downloads": 5}]}) == []


def test_the_npm_window_ends_yesterday_and_spans_npms_own_ceiling(daily):
    """Today is still accumulating, and npm silently clips a request over 18 months.

    Asking for exactly the ceiling is how the served start becomes readable rather than
    assumed: a request from 2024-08-14 came back beginning 2025-02-13.
    """
    period = daily.npm_period(date(2026, 8, 14))
    start, end = period.split(":")
    assert end == "2026-08-13"
    assert (date.fromisoformat(end) - date.fromisoformat(start)).days == 546
