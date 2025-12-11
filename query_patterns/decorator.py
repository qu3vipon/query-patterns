from typing import Iterable

from query_patterns.pattern import QueryPattern
from query_patterns.types import TableLike, ColumnLike


def query_pattern(*, table: TableLike, columns: Iterable[ColumnLike]):
    if table is None or table == "":
        raise ValueError("table must not be empty")
    if columns is None or not columns:
        raise ValueError("columns must not be empty")

    pattern = QueryPattern(table=table, columns=tuple(columns))

    def decorator(fn):
        patterns = getattr(fn, "__query_patterns__", None)
        if patterns is None:
            patterns = []
            setattr(fn, "__query_patterns__", patterns)

        if pattern not in patterns:
            patterns.append(pattern)
        return fn

    return decorator
