import os

import click
from django.apps import apps
from django.db.models import UniqueConstraint

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
        """
        indexes: IndexSet = set()

        for model in apps.get_models():
            meta = model._meta
            table = TableName(meta.db_table)

            for index in meta.indexes:
                cols = tuple(index.fields)
                indexes.add((table, cols))

            if meta.pk:
                indexes.add((table, (meta.pk.name,)))

            for field in meta.fields:
                if field.unique:
                    indexes.add((table, (field.name,)))

            for constraint in meta.constraints:
                if isinstance(constraint, UniqueConstraint):
                    cols = tuple(constraint.fields)
                    indexes.add((table, cols))

        return indexes

    @staticmethod
    def _collect_django_indexes_from_db() -> IndexSet:
        """
        Collect all actual indexes that exist in the database via Django's
        introspection system.
        """
        indexes: IndexSet = set()

        from django.db import connection

        with connection.cursor() as cursor:
            for table_name in connection.introspection.table_names():
                constraints = connection.introspection.get_constraints(
                    cursor, table_name
                )

                for _, spec in constraints.items():
                    cols = tuple(spec.get("columns") or ())
                    if not cols:
                        continue

                    if spec.get("primary_key"):
                        indexes.add((TableName(table_name), cols))
                        continue

                    if spec.get("unique"):
                        indexes.add((TableName(table_name), cols))
                        continue

                    if spec.get("index"):
                        indexes.add((TableName(table_name), cols))

        return indexes
