from __future__ import annotations

import os

from query_patterns.cli.tools.types import IndexSet, TableName


def setup_django(settings_module: str | None = None) -> None:
    """
    Initialize Django so that model metadata is available.

    If `settings_module` is provided, use it as the DJANGO_SETTINGS_MODULE.
    Otherwise, fall back to the environment variable.

    This function ensures:
      - Django is installed
      - settings are configured
      - django.setup() is called
    """
    try:
        import django
    except ImportError as e:
        raise RuntimeError(
            "Django support requires installing the 'django' extra "
            "(e.g. 'pip install query-patterns[django]')"
        ) from e

    if settings_module:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

    if not os.environ.get("DJANGO_SETTINGS_MODULE"):
        raise RuntimeError(
            "DJANGO_SETTINGS_MODULE is not set. Use --settings option "
            "or set the environment variable."
        )

    import django
    django.setup()


def collect_django_indexes_from_schema() -> IndexSet:
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


def collect_django_indexes_from_db() -> IndexSet:
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
            constraints = connection.introspection.get_constraints(cursor, table_name)

            for _, spec in constraints.items():
                # spec keys include:
                #   columns, primary_key, unique, index, check, foreign_key, ...

                # Keep ONLY real indexes (not PK)
                if spec.get("index") and not spec.get("primary_key"):
                    cols = tuple(spec["columns"])
                    indexes.add(
                        (TableName(table_name), cols)
                    )

    return indexes
