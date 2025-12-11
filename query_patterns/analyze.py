from .pattern import QueryPattern
from typing import Iterable

def analyze_patterns(
    patterns: Iterable[QueryPattern],
    indexes: set[tuple[str, tuple[str, ...]]],
):
    """
    Compare declared QueryPatterns with actual indexes.
    """
    results = []
    for pattern in patterns:
        key = (pattern.table, pattern.columns)
        status = "ok" if key in indexes else "missing"
        results.append((status, pattern))
    return results
