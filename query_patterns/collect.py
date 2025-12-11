import sys
import inspect
import importlib
from pathlib import Path
from types import ModuleType
from typing import Iterable, List

from .pattern import QueryPattern


EXCLUDE_DIRS = {
    ".venv",
    "venv",
    "__pycache__",
    ".tox",
    ".git",
    "site-packages",
}


def discover_modules_from_cwd() -> List[ModuleType]:
    """
    Discover and import all Python modules under the current working directory.
    Import errors are ignored to avoid side effects.
    """
    cwd = Path.cwd()
    modules: list[ModuleType] = []

    # Make project root importable
    if str(cwd) not in sys.path:
        sys.path.insert(0, str(cwd))

    for py in cwd.rglob("*.py"):
        # skip excluded directories
        if any(part in EXCLUDE_DIRS for part in py.parts):
            continue

        # skip private / dunder files
        if py.name.startswith("_"):
            continue

        try:
            module_path = ".".join(py.with_suffix("").relative_to(cwd).parts)
            modules.append(importlib.import_module(module_path))
        except Exception:
            # ignore import side-effects / errors
            continue

    return modules


def collect_query_patterns(
    modules: Iterable[ModuleType],
) -> list[QueryPattern]:
    """
    Collect all QueryPattern objects attached via @query_pattern
    from the given modules.
    """
    patterns: list[QueryPattern] = []

    for module in modules:
        for obj in vars(module).values():
            if inspect.isclass(obj):
                for _, fn in inspect.getmembers(obj, inspect.isfunction):
                    patterns.extend(
                        getattr(fn, "__query_patterns__", [])
                    )

    return patterns
