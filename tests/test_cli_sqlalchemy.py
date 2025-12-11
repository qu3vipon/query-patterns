import click.testing
from query_patterns.cli.main import main as cli_main
from query_patterns.cli.tools.sqlalchemy import (
    collect_sqlalchemy_indexes,
)


from sqlalchemy import MetaData, Table, Column, Integer, Index


def test_collect_sqlalchemy_indexes():
    metadata = MetaData()

    Table(
        "users",
        metadata,
        Column("id", Integer),
        Column("email", Integer),
        Index("ix_users_id_email", "id", "email"),
    )

    indexes = collect_sqlalchemy_indexes(metadata)

    assert ("users", ("id", "email")) in indexes


def test_cli_sqlalchemy_ok(tmp_path, monkeypatch):
    """
    CLI end-to-end test with SQLAlchemy metadata.
    """

    # Build a fake module containing a Repo with @query_pattern usage
    module_file = tmp_path / "mod.py"
    module_file.write_text(
        """
from query_patterns import query_pattern
class Repo:
    @query_pattern(table="users", columns=["id"])
    def foo(self): pass
"""
    )

    # Make temp dir importable
    monkeypatch.syspath_prepend(str(tmp_path))

    # Build SQLAlchemy metadata
    from sqlalchemy import MetaData, Table, Column, Integer, Index
    metadata = MetaData()
    Table(
        "users",
        metadata,
        Column("id", Integer),
        Index("ix_users_id", "id"),
    )

    # Expose metadata via a module path
    meta_file = tmp_path / "meta.py"
    meta_file.write_text(
        f"""
from sqlalchemy import MetaData, Table, Column, Integer, Index
metadata = MetaData()
Table("users", metadata, Column("id", Integer), Index("ix_users_id", "id"))
"""
    )

    # Run CLI
    runner = click.testing.CliRunner()
    result = runner.invoke(
        cli_main,
        [
            "sqlalchemy",
            "--module", "mod",
            "--metadata", "meta.metadata",
        ],
    )

    assert result.exit_code == 0
    assert "[OK] users('id',)" in result.output
