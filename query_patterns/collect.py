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
    Discover Python modules in cwd without importing the same file twice.
    """
    cwd = Path.cwd()
    modules: list[ModuleType] = []
    visited_files: set[str] = set()

    if str(cwd) not in sys.path:
        sys.path.insert(0, str(cwd))

    for py in cwd.rglob("*.py"):
        # skip excluded dirs
        if any(part in EXCLUDE_DIRS for part in py.parts):
            continue

        # skip private/dunder
        if py.name.startswith("_"):
            continue

        # canonical file path
        abs_path = str(py.resolve())
        if abs_path in visited_files:
            continue
        visited_files.add(abs_path)

        # build a safe module name
        rel_parts = py.with_suffix("").relative_to(cwd).parts
        module_name = ".".join(rel_parts)

        # if module is already imported, reuse it
        if module_name in sys.modules:
            modules.append(sys.modules[module_name])
            continue

        try:
            mod = importlib.import_module(module_name)
            modules.append(mod)
        except Exception:
            continue

    return modules


def collect_query_patterns(
    modules: Iterable[ModuleType],
) -> list[QueryPattern]:
    """
    Collect all QueryPattern objects attached via @query_pattern
    from the given modules, deduplicating identical patterns.
    """
    unique: set[QueryPattern] = set()

    for module in modules:
        for name, obj in vars(module).items():
            if inspect.isfunction(obj):
                for p in getattr(obj, "__query_patterns__", []):
                    unique.add(p)
            if inspect.isclass(obj):
                for _, fn in inspect.getmembers(obj, inspect.isfunction):
                    for p in getattr(fn, "__query_patterns__", []):
                        unique.add(p)

    return list(unique)
