import importlib
from typing import TYPE_CHECKING

import click
from sqlalchemy import inspect

from query_patterns.cli.runner.base import BaseRunner
from query_patterns.cli.runner.types import IndexSet, TableName, PatternSource


if TYPE_CHECKING:
    from sqlalchemy import MetaData, Engine


class SQLAlchemyRunner(BaseRunner):
    source: PatternSource = "schema"
    metadata: str | None
    engine_url: str | None

    def __init__(
        self,
        module: tuple[str, ...],
        source: PatternSource,
        metadata: str | None,
        engine_url: str | None,
        quiet: bool,
    ):
        self.module = module
        self.source = source
        self.metadata = metadata
        self.engine_url = engine_url
        self.quiet = quiet

    def _load_env(self):
        try:
            import sqlalchemy  # noqa: F401
        except ImportError:
            raise click.ClickException(
                "SQLAlchemy support requires `pip install query-patterns[sqlalchemy]`"
            )

    def _collect_indexes_by_source(self) -> IndexSet:
        if self.source == "schema":
            if not self.metadata:
                raise click.ClickException(
                    "--metadata is required when --source=schema"
                )

            try:
                mod_path, attr = self.metadata.rsplit(".", 1)
                meta = getattr(importlib.import_module(mod_path), attr)
            except Exception as e:
                raise click.ClickException(
                    f"Failed to load MetaData: {self.metadata}\n{e}"
                )

            click.echo("Collecting indexes from SQLAlchemy schema...")
            return self._collect_sqlalchemy_indexes_from_schema(meta)
        else:
            if self.metadata:
                click.echo(
                    "[WARN] --metadata is ignored when --source=db",
                    err=True,
                )

            if not self.engine_url:
                raise click.ClickException("--engine-url is required when --source=db")

            from sqlalchemy import create_engine

            engine = create_engine(self.engine_url)

            click.echo(f"Collecting indexes from database: {self.engine_url}")
            return self._collect_sqlalchemy_indexes_from_db(engine)

    @staticmethod
    def _collect_sqlalchemy_indexes_from_schema(metadata: "MetaData") -> IndexSet:
        indexes: IndexSet = set()

        for table in metadata.tables.values():
            for index in table.indexes:
                cols = tuple(index.columns.keys())
                indexes.add((TableName(table.name), cols))

        return indexes

    @staticmethod
    def _collect_sqlalchemy_indexes_from_db(engine: "Engine") -> IndexSet:
        indexes: IndexSet = set()
        inspector = inspect(engine)

        for table_name in inspector.get_table_names():
            for idx in inspector.get_indexes(table_name):
                cols = tuple(idx["column_names"])
                indexes.add((TableName(table_name), cols))
        return indexes
