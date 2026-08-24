"""Every warehouse SQL model must parse as Trino SQL.

CI validates the repository but never runs Trino, so a purely syntactic defect — a missing comma
between two CTEs, an unbalanced paren — sails through every existing gate and only surfaces when
the platform tries to materialize the model. That is exactly how an invalid
`product_adoption_current` revision reached review. A static parse is cheap and catches the whole
class before deploy.
"""

from pathlib import Path

import pytest
import sqlglot

ROOT = Path(__file__).resolve().parents[1]
SQL_FILES = sorted((ROOT / "warehouse" / "models").rglob("*.sql"))


def test_there_are_sql_models_to_check():
    assert SQL_FILES, "no warehouse SQL models found — did the models move?"


@pytest.mark.parametrize("path", SQL_FILES, ids=lambda p: str(p.relative_to(ROOT)))
def test_sql_model_parses_as_trino(path: Path):
    """Parse under the Trino dialect the platform runs. A syntax error raises here, naming the
    file, instead of failing a materialization after deploy."""
    try:
        sqlglot.parse_one(path.read_text(encoding="utf-8"), dialect="trino")
    except sqlglot.errors.ParseError as exc:  # pragma: no cover - message is the point
        pytest.fail(f"{path.relative_to(ROOT)} is not valid Trino SQL: {exc}")
