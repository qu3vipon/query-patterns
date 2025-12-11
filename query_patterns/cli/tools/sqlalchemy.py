from sqlalchemy import inspect

from query_patterns.cli.tools.types import IndexSet, TableName


def collect_sqlalchemy_indexes_from_schema(metadata: "MetaData") -> IndexSet:
    """
    Collects index definitions declared in SQLAlchemy ORM schema (MetaData).

    Returns:
        IndexSet: A set of index records in the form:
            {
                (TableName("table_name"), ("col1", "col2", ...)),
                ...
            }
    """
    indexes: IndexSet = set()

    for table in metadata.tables.values():
        for index in table.indexes:
            cols = tuple(index.columns.keys())
            indexes.add(
                (TableName(table.name), cols)
            )

    return indexes


def collect_sqlalchemy_indexes_from_db(engine: "Engine") -> IndexSet:
    """
    Collects actual indexes that exist in the database via SQLAlchemy Inspector.
    This reflects the real DB schema, independent of ORM definitions.

    Returns:
        IndexSet: A set of index records in the same (table_name, columns) format
                  used by collect_sqlalchemy_indexes_from_schema().
    """
    indexes: IndexSet = set()
    inspector = inspect(engine)

    for table_name in inspector.get_table_names():
        for idx in inspector.get_indexes(table_name):
            cols = tuple(idx["column_names"])
            indexes.add(
                (TableName(table_name), cols)
            )

    return indexes
