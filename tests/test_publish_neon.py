"""The Neon publisher, without a database.

Everything that decides what reaches the serving layer is a pure function here — the type
a column gets, the DDL for a table, the statement sequence the cutover runs — so all of it
is tested against strings rather than against a live Postgres. The two things that cannot
be checked that way are covered by running the CLI as a subprocess: that `--check` plans
without connecting, and that a DSN never reaches stdout or stderr.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from build.publish_neon import (
    DSN_ENV,
    RUN_COLUMNS,
    RUN_TABLE,
    create_table_sql,
    copy_sql,
    grant_sql,
    infer_column_type,
    plan_table,
    quote_ident,
    require_ssl,
    scrub,
    swap_sql,
)

ROOT = Path(__file__).resolve().parent.parent

# A DSN shaped like Neon's, with parts distinctive enough that a leak is unambiguous.
FAKE_DSN = "postgresql://mapuser:pw-tripwire-9f31@nowhere-tripwire.example.invalid/gapmapdb"


# --- type inference ------------------------------------------------------------------

@pytest.mark.parametrize(
    ("name", "values", "expected"),
    [
        ("weight_adopt", ["0.6", "0.3", ""], "DOUBLE PRECISION"),
        ("table_count", ["1", "12", "300"], "INTEGER"),
        ("big", ["9999999999"], "BIGINT"),
        ("decided_on", ["2026-08-30", ""], "DATE"),
        ("is_mature", ["true", "false"], "BOOLEAN"),
        ("is_mature", ["True", "FALSE"], "BOOLEAN"),
        ("note", ["a note", ""], "TEXT"),
        ("mixed", ["1", "one"], "TEXT"),
        ("blank", ["", ""], "TEXT"),
        ("almost_date", ["2026-08-30", "August"], "TEXT"),
    ],
)
def test_a_column_gets_the_narrowest_type_every_value_satisfies(name, values, expected):
    assert infer_column_type(name, values) == expected


@pytest.mark.parametrize(
    "name", ["slug", "product_slug", "category_slug", "artifact_id", "declaration_version_id"]
)
def test_identity_columns_stay_text_however_numeric_this_run_looks(name):
    """A digits-only artifact id is a string with digits in it.

    Inferring INTEGER off one run's values would change the column type from under a query
    the first time a non-numeric id arrives.
    """
    assert infer_column_type(name, ["1", "2", "3"]) == "TEXT"


def test_an_empty_column_is_text_not_a_guess():
    assert infer_column_type("artifact_url", []) == "TEXT"


# --- DDL ------------------------------------------------------------------------------

def test_create_table_sql_names_the_schema_and_every_typed_column():
    sql = create_table_sql(
        "gapmap_staging", (("slug", "TEXT"), ("weight_adopt", "DOUBLE PRECISION")), "categories"
    )
    assert sql.startswith('CREATE TABLE "gapmap_staging"."categories" (')
    assert '"slug" TEXT' in sql
    assert '"weight_adopt" DOUBLE PRECISION' in sql


def test_copy_sql_lists_the_columns_and_reads_a_header():
    plan = plan_table(_write_csv("products", "slug,display_name\na,A\nb,B\n"))
    sql = copy_sql("gapmap_staging", plan)
    assert 'COPY "gapmap_staging"."products" ("slug", "display_name")' in sql
    assert "FORMAT csv, HEADER true" in sql


def test_the_run_table_carries_the_publish_identity():
    columns = dict(RUN_COLUMNS)
    assert set(columns) == {
        "run_id",
        "published_at",
        "source_git_sha",
        "declaration_version_id",
        "table_count",
        "row_counts",
    }
    assert columns["row_counts"] == "JSONB"
    sql = create_table_sql("gapmap_staging", RUN_COLUMNS, RUN_TABLE)
    assert '"row_counts" JSONB' in sql


@pytest.mark.parametrize("bad", ["products; DROP SCHEMA gapmap", "two words", "", '"quoted"'])
def test_an_identifier_that_is_not_a_plain_name_is_refused(bad):
    with pytest.raises(ValueError):
        quote_ident(bad)


def test_grants_go_to_public_by_default_and_to_a_named_role_when_given():
    public = grant_sql("gapmap_staging", None)
    assert public[0].endswith("TO PUBLIC")
    assert 'GRANT SELECT ON ALL TABLES IN SCHEMA "gapmap_staging" TO PUBLIC' == public[1]
    named = grant_sql("gapmap_staging", "site_reader")
    assert all('"site_reader"' in statement for statement in named)


# --- the swap -------------------------------------------------------------------------

def test_the_first_run_is_a_single_rename():
    """There is no live schema to move aside, and renaming one that is absent is a
    different error from every other reason a rename fails."""
    assert swap_sql("gapmap", live_exists=False) == [
        'ALTER SCHEMA "gapmap_staging" RENAME TO "gapmap"'
    ]


def test_the_steady_state_swap_moves_aside_renames_and_drops_in_that_order():
    assert swap_sql("gapmap", live_exists=True) == [
        'DROP SCHEMA IF EXISTS "gapmap_previous" CASCADE',
        'ALTER SCHEMA "gapmap" RENAME TO "gapmap_previous"',
        'ALTER SCHEMA "gapmap_staging" RENAME TO "gapmap"',
        'DROP SCHEMA "gapmap_previous" CASCADE',
    ]


def test_the_swap_clears_a_previous_schema_left_by_a_run_that_died_mid_cutover():
    statements = swap_sql("gapmap", live_exists=True)
    assert statements[0].startswith('DROP SCHEMA IF EXISTS "gapmap_previous"')
    assert statements.index('ALTER SCHEMA "gapmap" RENAME TO "gapmap_previous"') == 1


def test_the_swap_never_drops_the_live_schema_by_name():
    """The live schema is renamed out of the way and the *old name's* holder is dropped.

    A `DROP SCHEMA gapmap` anywhere in this sequence would be a window with no serving
    layer at all, which is the failure the transaction exists to prevent.
    """
    for statement in swap_sql("gapmap", live_exists=True):
        assert not statement.startswith('DROP SCHEMA "gapmap" ')
        assert 'DROP SCHEMA IF EXISTS "gapmap" ' not in statement


# --- the DSN --------------------------------------------------------------------------

def test_require_ssl_appends_sslmode_when_the_url_omits_it():
    assert "sslmode=require" in require_ssl("postgresql://u:p@host/db")
    assert "sslmode=require" in require_ssl("postgresql://u:p@host/db?application_name=x")


def test_require_ssl_leaves_an_explicit_sslmode_alone():
    dsn = "postgresql://u:p@host/db?sslmode=verify-full"
    assert require_ssl(dsn) == dsn


def test_require_ssl_handles_a_keyword_dsn():
    assert require_ssl("host=h dbname=d") == "host=h dbname=d sslmode=require"
    assert require_ssl("host=h sslmode=disable") == "host=h sslmode=disable"


def test_scrub_removes_the_dsn_its_password_and_its_host():
    message = (
        f'could not translate host name "nowhere-tripwire.example.invalid" to address; '
        f"dsn was {FAKE_DSN}"
    )
    cleaned = scrub(message, FAKE_DSN)
    for secret in ("pw-tripwire-9f31", "nowhere-tripwire.example.invalid", "mapuser"):
        assert secret not in cleaned


# --- the CLI --------------------------------------------------------------------------

def _run(args: list[str], env_extra: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    import os

    env = dict(os.environ)
    env.pop(DSN_ENV, None)
    env.update(env_extra or {})
    return subprocess.run(
        [sys.executable, "-m", "build.publish_neon", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
    )


def test_check_plans_without_a_dsn_and_prints_the_row_counts():
    result = _run(["--check"])
    assert result.returncode == 0, result.stderr
    assert "would load" in result.stdout
    assert "products" in result.stdout
    assert RUN_TABLE in result.stdout


def test_a_publish_with_no_dsn_exits_2_and_says_which_variable():
    result = _run([])
    assert result.returncode == 2
    assert DSN_ENV in result.stderr
    assert "not set" in result.stderr


def test_no_part_of_the_dsn_ever_reaches_stdout_or_stderr():
    """The publish will fail — the host does not resolve — and the failure is the point:
    a libpq error quotes the host, one delimiter from the password."""
    result = _run([], {DSN_ENV: FAKE_DSN})
    assert result.returncode == 1
    output = result.stdout + result.stderr
    for secret in (FAKE_DSN, "pw-tripwire-9f31", "nowhere-tripwire.example.invalid", "mapuser"):
        assert secret not in output, f"{secret!r} leaked into the publisher's output"


# --- helpers --------------------------------------------------------------------------

_TMP: dict[str, Path] = {}


def _write_csv(name: str, text: str) -> Path:
    import tempfile

    directory = _TMP.setdefault("dir", Path(tempfile.mkdtemp()))
    path = directory / f"{name}.csv"
    path.write_text(text, encoding="utf-8")
    return path


def test_plan_table_reads_the_header_and_counts_data_rows_only():
    plan = plan_table(_write_csv("categories", "slug,weight_adopt\na,0.6\nb,0.3\n"))
    assert plan.name == "categories"
    assert plan.row_count == 2
    assert plan.columns == (("slug", "TEXT"), ("weight_adopt", "DOUBLE PRECISION"))


def test_a_header_only_csv_plans_as_a_real_table_with_no_rows():
    """A serializer emits a header for every table it declares, filled or not."""
    plan = plan_table(_write_csv("tail_products", "slug,artifact_id\n"))
    assert plan.row_count == 0
    assert plan.columns == (("slug", "TEXT"), ("artifact_id", "TEXT"))


def test_a_short_row_does_not_shift_a_columns_inferred_type():
    """csv tolerates a row with missing trailing fields; the absent value is empty, not
    the next column's."""
    plan = plan_table(_write_csv("ragged", "a,b\n1,2\n3\n"))
    assert dict(plan.columns)["b"] == "INTEGER"
