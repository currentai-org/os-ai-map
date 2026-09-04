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

from build.neon_schema import (
    ALL_TABLES,
    ENUM_MAPS,
    ENUMS,
    REGISTRY_PREFIX,
    SCHEMA_VERSION,
    SITE_TABLES,
    UnmappedValue,
    enum_value,
    load_payload,
    product_ids,
)
from build.publish_neon import (
    DEFAULT_SCHEMA,
    DSN_ENV,
    PROTECTED_SCHEMAS,
    PUBLISHED_TABLES,
    RUN_COLUMNS,
    RUN_TABLE,
    create_enum_sql,
    create_table_sql,
    copy_sql,
    grant_sql,
    infer_column_type,
    plan,
    plan_table,
    check_schema_is_ours,
    quote_ident,
    quote_schema,
    require_ssl,
    scrub,
    stream_bytes,
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


def test_the_run_table_carries_the_publish_identity_and_the_two_payload_dates():
    columns = dict(RUN_COLUMNS)
    assert set(columns) == {
        "run_id",
        "published_at",
        "schema_version",
        "built_at",
        "released_at",
        "source_git_sha",
        "declaration_version_id",
        "table_count",
        "row_counts",
    }
    assert columns["row_counts"] == "JSONB"
    assert columns["built_at"] == columns["released_at"] == "DATE"
    sql = create_table_sql("gapmap_staging", RUN_COLUMNS, RUN_TABLE)
    assert '"row_counts" JSONB' in sql


def test_the_schema_version_is_recorded_because_the_swap_is_the_migration():
    """Every publish rebuilds the schema from the mapping, so nothing else tells a reader
    which shape it is looking at."""
    assert isinstance(SCHEMA_VERSION, int) and SCHEMA_VERSION >= 1
    assert dict(RUN_COLUMNS)["schema_version"] == "INTEGER"


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


# --- the shared instance --------------------------------------------------------------

def test_the_default_schema_is_the_gap_maps_own():
    assert DEFAULT_SCHEMA == "os-ai-map"


def test_a_hyphenated_schema_name_is_quoted_not_refused():
    """The agreed Neon layout names the gap map's schema with a hyphen."""
    assert quote_schema("os-ai-map") == '"os-ai-map"'
    assert quote_schema("os-ai-map_staging") == '"os-ai-map_staging"'


@pytest.mark.parametrize("bad", ['os"ai', "os ai map", "-leading", "", "os\\map", "os;drop"])
def test_a_schema_name_that_would_need_escaping_is_refused(bad):
    """A schema name reaches DROP SCHEMA ... CASCADE."""
    with pytest.raises(ValueError):
        quote_schema(bad)


def test_a_hyphen_is_still_refused_in_a_table_or_column_name():
    """Fine in a schema a maintainer chose; never something a serializer should produce."""
    with pytest.raises(ValueError):
        quote_ident("os-ai-map")


@pytest.mark.parametrize("schema", sorted(PROTECTED_SCHEMAS))
def test_another_part_of_the_sites_schema_is_refused(schema):
    """drizzle, payload and public share this instance and this publisher drops schemas
    with CASCADE. A typo in --schema must not be able to take one of them."""
    with pytest.raises(ValueError, match="refusing"):
        check_schema_is_ours(schema)


@pytest.mark.parametrize("schema", ["os-ai-map_staging", "os-ai-map_previous"])
def test_the_publishers_own_working_schemas_are_refused_as_a_target(schema):
    with pytest.raises(ValueError, match="manages itself"):
        check_schema_is_ours(schema)


def test_the_gap_maps_own_schema_passes():
    check_schema_is_ours(DEFAULT_SCHEMA)


def test_a_protected_schema_on_the_cli_exits_2_without_connecting():
    result = _run(["--schema", "public"], {DSN_ENV: FAKE_DSN})
    assert result.returncode == 2
    assert "refusing" in result.stderr


def test_the_swap_touches_only_the_target_and_its_two_working_schemas():
    """Nothing on the shared instance outside these three names is named in the cutover."""
    named = set()
    for statement in swap_sql(DEFAULT_SCHEMA, live_exists=True):
        named.update(part.strip('"') for part in statement.split() if part.startswith('"'))
    assert named == {
        DEFAULT_SCHEMA,
        f"{DEFAULT_SCHEMA}_staging",
        f"{DEFAULT_SCHEMA}_previous",
    }
    assert not named & PROTECTED_SCHEMAS


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


def test_no_part_of_the_dsn_ever_reaches_stdout_or_stderr(tmp_path):
    """The publish will fail — the host does not resolve — and the failure is the point:
    a libpq error quotes the host, one delimiter from the password."""
    result = _run(
        [
            "--dir",
            str(_complete_dir(tmp_path / "csv")),
            "--site-dir",
            str(tmp_path / "site"),
        ],
        {DSN_ENV: FAKE_DSN},
    )
    assert result.returncode == 1, result.stdout + result.stderr
    output = result.stdout + result.stderr
    for secret in (FAKE_DSN, "pw-tripwire-9f31", "nowhere-tripwire.example.invalid", "mapuser"):
        assert secret not in output, f"{secret!r} leaked into the publisher's output"


# --- the table set --------------------------------------------------------------------

def test_the_registry_group_is_the_set_publish_registry_publishes_to_oso():
    """Neon and the warehouse must carry the same registry surface.

    Derived from `publish_registry.TABLES`, never from a glob over the output directory: a
    glob makes the published surface depend on which serializers happened to have run, so a
    directory left by a partial run would quietly publish a smaller map.
    """
    from build.publish_registry import TABLES as OSO_TABLES

    assert PUBLISHED_TABLES == OSO_TABLES
    for name in OSO_TABLES:
        assert f"{REGISTRY_PREFIX}{name}" in ALL_TABLES


def test_every_serializers_tables_are_in_the_set():
    from build.serialize_registry import TABLES as REGISTRY
    from build.serialize_routing import TABLES as ROUTING
    from build.serialize_rubric import TABLES as RUBRIC
    from build.serialize_scores import TABLES as SCORES

    for spec in (REGISTRY, RUBRIC, ROUTING, SCORES):
        assert set(spec).issubset(set(PUBLISHED_TABLES))


def test_the_two_groups_do_not_collide():
    """Both surfaces share one schema and both have a products, a categories and an
    organizations. The prefix is what keeps them apart."""
    assert set(SITE_TABLES) & set(PUBLISHED_TABLES), "the overlap is the reason for the prefix"
    assert len(set(ALL_TABLES)) == len(ALL_TABLES)
    assert not set(SITE_TABLES) & {f"{REGISTRY_PREFIX}{n}" for n in PUBLISHED_TABLES}


def test_a_declared_table_with_no_csv_is_reported_missing_not_skipped(tmp_path):
    """A table is absent because a serializer has not run. Loading the rest would publish
    a partial map that looks complete.

    Into an empty directory the registry serializer's own tables are regenerated, so what is
    left missing is the rubric, routing and scores sets — exactly the ones this module will
    not run for you.
    """
    from build.serialize_registry import TABLES as OWN

    plans, missing = plan(tmp_path, site_dir=tmp_path / "site")
    loaded = {p.name for p in plans if p.name not in SITE_TABLES}
    assert loaded == {f"{REGISTRY_PREFIX}{n}" for n in OWN}
    assert set(missing) == {
        f"{REGISTRY_PREFIX}{n}" for n in PUBLISHED_TABLES if n not in OWN
    }
    assert missing, "the other three serializers have not run, so something must be missing"


def test_plans_come_back_in_the_declared_order_map_group_first(tmp_path):
    """The map group loads first, so a failure in the part the site reads shows up first."""
    plans, _missing = plan(site_dir=tmp_path / "site")
    names = [p.name for p in plans]
    assert names == [name for name in ALL_TABLES if name in set(names)]
    assert names[: len(SITE_TABLES)] == list(SITE_TABLES)


def test_a_publish_missing_a_csv_exits_2_and_names_the_serializers(tmp_path):
    result = _run(
        ["--dir", str(tmp_path), "--site-dir", str(tmp_path / "site")], {DSN_ENV: FAKE_DSN}
    )
    assert result.returncode == 2
    assert "missing tables" in result.stderr
    assert "serialize_scores" in result.stderr


def _complete_dir(directory: Path) -> Path:
    """A header-only CSV per declared registry table, so the completeness gate passes.

    Header-only is a real state — a serializer emits a header for every table it declares,
    filled or not — and it lets a test exercise what happens after planning without running
    four serializers.
    """
    directory.mkdir(parents=True, exist_ok=True)
    for name in PUBLISHED_TABLES:
        (directory / f"{name}.csv").write_text("slug\n", encoding="utf-8")
    return directory


# --- enums ----------------------------------------------------------------------------

def test_all_eight_enums_are_declared():
    assert set(ENUMS) == {
        "alias_kind",
        "freshness_basis",
        "lineage_relation",
        "capability_relation",
        "metric_name",
        "health_status",
        "integration_type",
        "gap_type",
    }


def test_create_enum_sql_makes_every_enum_inside_the_schema_being_built():
    statements = create_enum_sql("os-ai-map_staging")
    assert len(statements) == len(ENUMS)
    assert (
        'CREATE TYPE "os-ai-map_staging"."alias_kind" AS ENUM (\'product\', \'organization\')'
        in statements
    )


def test_an_enum_column_qualifies_its_type_with_the_schema():
    """Enum types are schema-scoped and the staging schema is never on the search path."""
    sql = create_table_sql("os-ai-map_staging", SITE_TABLES["aliases"].columns, "aliases")
    assert '"kind" "os-ai-map_staging"."alias_kind"' in sql


def test_every_mapped_value_lands_inside_its_enum():
    for enum, mapping in ENUM_MAPS.items():
        for source, target in mapping.items():
            assert target in ENUMS[enum], f"{enum}: {source!r} -> {target!r} is not a value"


def test_an_unmapped_value_fails_the_load_and_names_the_value():
    """A serving layer that coerced an unknown vocabulary item to something adjacent would
    be worse than one that stopped."""
    with pytest.raises(UnmappedValue) as caught:
        enum_value("capability_relation", "three_below", column="capability.relation")
    assert "three_below" in str(caught.value)
    assert "capability.relation" in str(caught.value)


def test_an_absent_value_is_null_not_an_error():
    for empty in (None, ""):
        assert enum_value("capability_relation", empty, column="capability.relation") is None


def test_the_capability_relation_mapping_is_lossy_and_says_so():
    """The payload carries a signed distance; the target enum has no distance. Both
    `one_below` and `two_below` arrive as `tier_below`, and that is deliberate."""
    assert enum_value("capability_relation", "one_below", column="c") == "tier_below"
    assert enum_value("capability_relation", "two_below", column="c") == "tier_below"
    assert enum_value("capability_relation", "at", column="c") == "peer"
    assert enum_value("capability_relation", "one_above", column="c") == "tier_above"


def test_every_relation_the_payload_actually_carries_is_mapped():
    """The guard against a new vocabulary item reaching the load unmapped."""
    payload = load_payload()
    for cid in payload["order"]:
        for product in payload["categories"][cid]["products"]:
            relation = (product.get("capability") or {}).get("relation")
            enum_value("capability_relation", relation, column="capability.relation")
            basis = (product.get("freshness") or {}).get("basis")
            enum_value("freshness_basis", basis, column="products.freshness_basis")


# --- keys -----------------------------------------------------------------------------

def test_product_ids_are_assigned_by_sorted_slug_so_a_load_is_reproducible():
    """Surrogate ids exist for the designers' FK shape, but an id that moved between loads
    would make a diff of two loads unreadable."""
    payload = load_payload()
    ids = product_ids(payload)
    assert sorted(ids.values()) == list(range(1, len(ids) + 1))
    assert [slug for slug, _id in sorted(ids.items(), key=lambda kv: kv[1])] == sorted(ids)
    assert product_ids(payload) == ids


def test_categories_carry_a_slug_the_pdf_omitted():
    """Every deep link and every join from the registry group is by slug, and an id assigned
    by curated order changes whenever the order does."""
    assert "slug" in dict(SITE_TABLES["categories"].columns)


def test_the_foreign_keys_resolve_to_rows_that_exist():
    payload = load_payload()
    rows = {name: spec.rows(payload) for name, spec in SITE_TABLES.items()}
    product_id_set = {row["id"] for row in rows["products"]}
    category_id_set = {row["id"] for row in rows["categories"]}
    layer_id_set = {row["id"] for row in rows["layers"]}
    stage_id_set = {row["id"] for row in rows["stages"]}
    gap_id_set = {row["id"] for row in rows["gaps"]}
    org_slugs = {row["slug"] for row in rows["organizations"]}

    for row in rows["products"]:
        assert row["category"] in category_id_set
        assert row["org_slug"] in org_slugs
    for row in rows["categories"]:
        assert row["layer"] in layer_id_set
        assert row["stage"] in stage_id_set
    for table in ("openness", "adoption", "capability", "sources", "product_lineage"):
        for row in rows[table]:
            assert row["product_id"] in product_id_set
    for row in rows["gaps_categories"]:
        assert row["cat_id"] in category_id_set
        assert row["gap_id"] in gap_id_set


def test_each_axis_has_exactly_one_row_per_product():
    payload = load_payload()
    products = SITE_TABLES["products"].rows(payload)
    for axis in ("openness", "adoption", "capability"):
        rows = SITE_TABLES[axis].rows(payload)
        assert len(rows) == len(products)
        assert len({row["product_id"] for row in rows}) == len(products)


def test_the_gallery_tables_are_created_empty_because_the_content_is_cms_side():
    payload = load_payload()
    for name in ("gallery", "gallery_products", "gallery_gaps"):
        assert SITE_TABLES[name].rows(payload) == []
        assert SITE_TABLES[name].columns, f"{name} still needs its columns"


def test_the_long_tail_tables_are_filled_from_the_payload():
    payload = load_payload()
    assert len(SITE_TABLES["long_tail_top"].rows(payload)) == len(payload["long_tail"]["top"])
    assert len(SITE_TABLES["long_tail_counts"].rows(payload)) == len(
        payload["long_tail"]["counts"]
    )


def test_lineage_is_relational_and_carries_every_edge():
    payload = load_payload()
    rows = SITE_TABLES["product_lineage"].rows(payload)
    expected = sum(
        len(targets or [])
        for cid in payload["order"]
        for product in payload["categories"][cid]["products"]
        for targets in (product.get("lineage") or {}).values()
    )
    assert len(rows) == expected
    assert {row["relation"] for row in rows} <= set(ENUMS["lineage_relation"])


def test_aliases_carry_their_kind():
    payload = load_payload()
    rows = SITE_TABLES["aliases"].rows(payload)
    kinds = {row["kind"] for row in rows}
    assert kinds <= set(ENUMS["alias_kind"])
    assert len(rows) == sum(len(v) for v in payload["aliases"].values())


def test_the_amended_columns_are_all_present():
    """Carl's amendments to the PDF: per-axis dates, governing_release, basis_detail, the
    peer-relative pair, and the product freshness pair."""
    products = dict(SITE_TABLES["products"].columns)
    assert "freshness_date" in products and "freshness_basis" in products
    assert "last_verified" in dict(SITE_TABLES["openness"].columns)
    assert "governing_release" in dict(SITE_TABLES["openness"].columns)
    assert "last_verified" in dict(SITE_TABLES["adoption"].columns)
    capability = dict(SITE_TABLES["capability"].columns)
    for column in ("last_verified", "basis_detail", "relative_to", "relation"):
        assert column in capability


def test_an_array_column_is_written_as_a_postgres_array_literal():
    payload = load_payload()
    rows = SITE_TABLES["organizations"].rows(payload)
    assert all(row["github"].startswith("{") and row["github"].endswith("}") for row in rows)
    with_accounts = [row for row in rows if row["github"] != "{}"]
    assert with_accounts, "no organization declares a github account"
    assert with_accounts[0]["github"].startswith('{"http')


# --- the COPY payload -----------------------------------------------------------------

# A quoted CSV field holding both a newline and an escaped quote. Several real `strapline`
# and `note` values are shaped like this, and they are the rows a line-oriented or
# text-mode read would corrupt.
_AWKWARD = 'slug,note\nolmo-3,"a note with a ""quoted"" phrase\nand a second line"\n'


def test_the_copy_payload_is_the_file_byte_for_byte():
    path = _write_csv("awkward", _AWKWARD)
    chunks: list[bytes] = []
    written = stream_bytes(path, chunks.append)
    assert b"".join(chunks) == path.read_bytes()
    assert written == len(path.read_bytes())


@pytest.mark.parametrize("chunk_size", [1, 3, 7, 4096])
def test_a_chunk_boundary_may_fall_anywhere_including_inside_a_quoted_newline(chunk_size):
    """Postgres's CSV parser reassembles the stream, so the split point cannot matter.

    A chunked read that respected line boundaries would be a read that had to understand
    CSV quoting, which is the bug this guards.
    """
    path = _write_csv("awkward", _AWKWARD)
    chunks: list[bytes] = []
    stream_bytes(path, chunks.append, chunk_size=chunk_size)
    assert b"".join(chunks) == path.read_bytes()


def test_the_awkward_value_survives_a_full_csv_round_trip():
    """What Postgres will parse out of that payload, read back with the same dialect."""
    path = _write_csv("awkward", _AWKWARD)
    chunks: list[bytes] = []
    stream_bytes(path, chunks.append, chunk_size=5)
    import csv as _csv
    import io

    rows = list(_csv.reader(io.StringIO(b"".join(chunks).decode("utf-8"))))
    assert rows[0] == ["slug", "note"]
    assert rows[1] == ["olmo-3", 'a note with a "quoted" phrase\nand a second line']
    assert len(rows) == 2, "the embedded newline must not read as a row boundary"


def test_the_embedded_newline_is_not_counted_as_an_extra_row():
    plan_ = plan_table(_write_csv("awkward", _AWKWARD))
    assert plan_.row_count == 1
    assert dict(plan_.columns)["note"] == "TEXT"


# --- the read-back query --------------------------------------------------------------


def test_the_read_back_query_reaches_postgres_with_its_own_format_specifiers_intact():
    """`%I` is Postgres's, and psycopg claims `%` the moment parameters are passed.

    The first CI run of build/neon_status.py failed here: psycopg scanned the statement,
    found `%I`, and refused it before connecting. The schema is composed in as a literal
    instead, so there are no parameters and nothing scans the query.
    """
    from build.neon_status import counts_sql

    rendered = counts_sql("os-ai-map").as_string()
    assert "format('select count(*) as c from %I.%I', table_schema, table_name)" in rendered
    assert "%%" not in rendered, "a doubled specifier would reach format() as a literal %"
    assert "{schema}" not in rendered


def test_the_read_back_query_quotes_the_schema_it_filters_on():
    from build.neon_status import counts_sql

    rendered = counts_sql("os-ai-map").as_string()
    assert "WHERE table_schema = 'os-ai-map'" in rendered


def test_a_schema_name_carrying_a_quote_cannot_break_out_of_the_read_back_query():
    """`sql.Literal` escapes the value. This is not string interpolation into SQL."""
    from build.neon_status import counts_sql

    rendered = counts_sql("o'brien").as_string()
    assert "'o''brien'" in rendered


def test_the_runs_query_names_the_schema_and_the_run_table():
    from build.neon_status import RUNS_SQL

    rendered = RUNS_SQL.format(schema=quote_schema("os-ai-map"), table=f'"{RUN_TABLE}"')
    assert f'FROM "os-ai-map"."{RUN_TABLE}"' in rendered
    assert "%" not in rendered, "the runs query passes no parameters either"


def test_the_status_report_reads_back_every_column_the_run_record_writes():
    """A column added to RUN_COLUMNS and not to the report is a column nobody ever sees."""
    from build.neon_status import RUNS_SQL

    selected = RUNS_SQL.split("FROM")[0]
    for column, _type in RUN_COLUMNS:
        assert column in selected, f"{column} is written but never read back"


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
