import textwrap
import click.testing

from query_patterns.cli.main import main as cli_main

from sqlalchemy import MetaData, Table, Column, Integer, Index, create_engine


def test_cli_sqlalchemy_from_schema_success(tmp_path, monkeypatch, isolated_cwd_and_module):
    # given
    mod_name = "mod"
    isolated_cwd_and_module(mod_name)

    module_file = tmp_path / f"{mod_name}.py"
    module_file.write_text(
        textwrap.dedent((
            """
            from query_patterns import query_pattern
            class Repo:
                @query_pattern(table="users", columns=["id"])
                def foo(self): pass
            """
        ))
    )

    monkeypatch.syspath_prepend(str(tmp_path))

    metadata = MetaData()
    Table(
        "users",
        metadata,
        Column("id", Integer),
        Index("ix_users_id", "id"),
    )

    meta_file = tmp_path / "meta.py"
    meta_file.write_text(
        textwrap.dedent("""
                from sqlalchemy import MetaData, Table, Column, Integer, Index
                metadata = MetaData()
                Table("users", metadata, Column("id", Integer), Index("ix_users_id", "id"))
                """)
    )

    # when
    runner = click.testing.CliRunner()
    result = runner.invoke(
        cli_main,
        [
            "sqlalchemy",
            "--module",
            mod_name,
            "--metadata",
            "meta.metadata",
        ],
    )

    # then
    assert "[OK] users('id',)" in result.output
    assert "[MISSING]" not in result.output


def test_cli_sqlalchemy_from_schema_missing(tmp_path, monkeypatch, isolated_cwd_and_module):
    # given
    mod_name = "mod_missing"
    isolated_cwd_and_module(mod_name)

    module_file = tmp_path / f"{mod_name}.py"
    module_file.write_text(
        textwrap.dedent(
            """
            from query_patterns import query_pattern
            class Repo:
                @query_pattern(table="users", columns=["id"])
                def foo(self): pass
            """
        )
    )

    monkeypatch.syspath_prepend(str(tmp_path))

    meta_file = tmp_path / "meta_missing.py"
    meta_file.write_text(
        textwrap.dedent(
            """
            from sqlalchemy import MetaData, Table, Column, Integer
            metadata = MetaData()
            Table("users", metadata, Column("id", Integer))
            """
        )
    )

    # when
    runner = click.testing.CliRunner()
    result = runner.invoke(
        cli_main,
        [
            "sqlalchemy",
            "--module",
            mod_name,
            "--metadata",
            "meta_missing.metadata",
        ],
    )

    # then
    assert "[MISSING]" in result.output
    assert "users('id',)" in result.output
    assert "[usage=1]" in result.output
    assert "[OK]" not in result.output


def test_cli_sqlalchemy_from_db_success(tmp_path, monkeypatch, isolated_cwd_and_module):
    # given
    mod_name = "mod"
    isolated_cwd_and_module(mod_name)

    module_file = tmp_path / f"{mod_name}.py"
    module_file.write_text(
        textwrap.dedent(
            """
from query_patterns import query_pattern

class Repo:
    @query_pattern(table="users", columns=["id"])
    def foo(self): pass
"""
        )
    )

    monkeypatch.syspath_prepend(str(tmp_path))

    db_path = tmp_path / "test.db"
    engine_url = f"sqlite:///{db_path}"

    metadata = MetaData()
    Table(
        "users",
        metadata,
        Column("id", Integer),
        Index("ix_users_id", "id"),
    )

    engine = create_engine(engine_url)
    metadata.create_all(engine)

    # when
    runner = click.testing.CliRunner()
    result = runner.invoke(
        cli_main,
        [
            "sqlalchemy",
            "--module",
            mod_name,
            "--source",
            "db",
            "--engine-url",
            engine_url,
        ],
    )

    # then
    assert result.exit_code == 0, result.output
    assert "[OK] users('id',)" in result.output
    assert "[MISSING]" not in result.output


def test_cli_sqlalchemy_from_db_missing(tmp_path, monkeypatch, isolated_cwd_and_module):
    # given
    mod_name = "mod_missing"
    isolated_cwd_and_module(mod_name)

    module_file = tmp_path / f"{mod_name}.py"
    module_file.write_text(
        textwrap.dedent(
            """
            from query_patterns import query_pattern

            class Repo:
                @query_pattern(table="users", columns=["id"])
                def foo(self): pass
            """
        )
    )

    monkeypatch.syspath_prepend(str(tmp_path))

    db_path = tmp_path / "test_missing.db"
    engine_url = f"sqlite:///{db_path}"

    metadata = MetaData()
    Table(
        "users",
        metadata,
        Column("id", Integer),
    )

    engine = create_engine(engine_url)
    metadata.create_all(engine)

    # when
    runner = click.testing.CliRunner()
    result = runner.invoke(
        cli_main,
        [
            "sqlalchemy",
            "--module",
            mod_name,
            "--source",
            "db",
            "--engine-url",
            engine_url,
        ],
    )

    # then
    assert "[MISSING]" in result.output
    assert "users('id',)" in result.output
    assert "[usage=1]" in result.output
    assert "[OK]" not in result.output
