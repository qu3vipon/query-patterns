from dataclasses import dataclass
from typing import Tuple

from query_patterns.types import TableLike


@dataclass(frozen=True)
class QueryPattern:
    table: str
    columns: Tuple[str, ...]

    def __init__(self, table: TableLike, columns: Tuple[str, ...]):
        object.__setattr__(self, "table", self._extract_table_name(table))
        object.__setattr__(self, "columns", columns)

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
