from typing import Any, Sequence

from query_patterns.pattern import QueryPattern


def get_patterns(obj: Any) -> Sequence[QueryPattern]:
    return getattr(obj, "__query_patterns__", [])
