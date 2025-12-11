from dataclasses import dataclass
from typing import Tuple

from query_patterns.types import TableLike, ColumnLike


@dataclass(frozen=True)
class QueryPattern:
    table: str
    columns: tuple[str]

    def __init__(self, table: TableLike, columns: tuple[ColumnLike, ...]):
        object.__setattr__(self, "table", self._extract_table_name(table))
        object.__setattr__(self, "columns", self._extract_column_names(columns))

    @staticmethod
    def _extract_table_name(table: TableLike) -> str:
        # SQLAlchemy ORM
        if hasattr(table, "__tablename__"):
            return table.__tablename__

        # SQLAlchemy Core Table
        if hasattr(table, "name") and hasattr(table, "columns"):
            return table.name

        # Django Model
        if hasattr(table, "_meta") and hasattr(table._meta, "db_table"):
            return table._meta.db_table

        # String
        if isinstance(table, str):
            return table

        raise TypeError(f"Unsupported table type: {type(table)!r}")

    @staticmethod
    def _extract_column_names(columns: Tuple[ColumnLike, ...]) -> tuple[str, ...]:
        result = []

        for col in columns:
            if isinstance(col, str):
                result.append(col)
                continue

            # SQLAlchemy ORM attribute
            if hasattr(col, "key"):
                result.append(col.key)
                continue

            # SQLAlchemy Core Column (Table.c.id) or Django Field
            if hasattr(col, "name"):
                result.append(col.name)
                continue

            raise TypeError(f"Unsupported column type: {type(col)!r}")

        return tuple(result)
