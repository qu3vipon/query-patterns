import os

import click

from query_patterns.cli.runner.base import BaseRunner
from query_patterns.cli.runner.types import IndexSet, TableName, PatternSource


class DjangoRunner(BaseRunner):
    settings: str | None
    source: PatternSource = "schema"

    def __init__(
        self, module: tuple[str, ...], settings: str, source: PatternSource, quiet: bool
    ):
        self.module = module
        self.settings = settings
        self.source = source
        self.quiet = quiet

    def _load_env(self):
        try:
            import django
        except ImportError:
            raise click.ClickException(
                "Django support requires installing with the [django] extra:\n"
                "    pip install query-patterns[django]"
            )

        if self.settings:
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", self.settings)

        if not os.environ.get("DJANGO_SETTINGS_MODULE"):
            raise click.ClickException(
                "DJANGO_SETTINGS_MODULE is not set. Use --settings option "
                "or set the environment variable."
            )

        import django

        django.setup()

    def _collect_indexes_by_source(self) -> IndexSet:
        if self.source == "schema":
            click.echo("Collecting indexes from Django model schema...")
            indexes = self._collect_django_indexes_from_schema()
        else:
            click.echo("Collecting indexes from actual database...")
            indexes = self._collect_django_indexes_from_db()
        return indexes

    @staticmethod
    def _collect_django_indexes_from_schema() -> IndexSet:
        """
        Collect all indexes defined in Django model declarations (schema level).

        Returns:
            IndexSet: a set of (table_name, (field1, field2, ...))
            NOTE:
                - Only Django model-declared indexes (model.Meta.indexes) are included.
                - Implicit PK indexes, unique constraints, and unique_together
                  are not included unless explicitly declared as Index().
        """
        indexes: IndexSet = set()

        from django.apps import apps

        for model in apps.get_models():
            table = TableName(model._meta.db_table)

            for index in model._meta.indexes:
                cols = tuple(index.fields)
                indexes.add((table, cols))
        return indexes

    @staticmethod
    def _collect_django_indexes_from_db() -> IndexSet:
        """
        Collect all actual indexes that exist in the database via Django's
        introspection system.

        Returns:
            IndexSet: a set of (table_name, (field1, field2, ...))
                      representing actual DB-level indexes.

        """
        indexes: IndexSet = set()

        from django.db import connection

        with connection.cursor() as cursor:
            for table_name in connection.introspection.table_names():
                constraints = connection.introspection.get_constraints(
                    cursor, table_name
                )

                for _, spec in constraints.items():
                    # spec keys include:
                    #   columns, primary_key, unique, index, check, foreign_key, ...

                    # Keep ONLY real indexes (not PK)
                    if spec.get("index") and not spec.get("primary_key"):
                        cols = tuple(spec["columns"])
                        indexes.add((TableName(table_name), cols))

        return indexes
