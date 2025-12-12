from importlib.metadata import version

__version__ = version("query-patterns")

from .decorator import query_pattern

__all__ = [
    "query_pattern",
]
