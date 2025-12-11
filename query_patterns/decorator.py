from query_patterns.pattern import QueryPattern


def query_pattern(*, table: str, columns: list[str]):
    if not table:
        raise ValueError("table must not be empty")
    if not columns:
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
