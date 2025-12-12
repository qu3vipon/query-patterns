import importlib
import inspect
import sys
from collections import OrderedDict
from pathlib import Path
from types import ModuleType
from typing import List, Iterable

import click

from query_patterns.cli.runner.types import IndexSet
from query_patterns.pattern import QueryPattern
from query_patterns.utils import get_patterns


EXCLUDE_DIRS = {
    ".venv",
    "venv",
    "__pycache__",
    ".tox",
    ".git",
    "site-packages",
}


class BaseRunner:
    module: tuple[str, ...] = ()
    quiet: bool

    def run(self):
        self._load_env()
        modules = self._import_modules()
        patterns, counts = self._collect_query_patterns(modules)
        indexes = self._collect_indexes_by_source()
        results = self._analyze_patterns(patterns, indexes)
        self._print_results(results, counts)

    def _load_env(self):
        raise NotImplementedError()

    def _import_modules(self) -> list[ModuleType]:
        if self.module:
            click.echo(f"Import module from {', '.join(self.module)}...")
            modules = self._import_module_from_cwd(self.module)
        else:
            click.echo("Auto-discovering project modules...")
            modules = self._discover_modules_from_cwd()

        if not modules:
            raise click.ClickException("No modules found to scan.")
        return modules

    @staticmethod
    def _import_module_from_cwd(module: tuple[str, ...]) -> List[ModuleType]:
        cwd = Path.cwd()
        if cwd not in sys.path:
            sys.path.insert(0, str(cwd))
        return [importlib.import_module(m) for m in module]

    @staticmethod
    def _discover_modules_from_cwd() -> List[ModuleType]:
        """
        Discover Python modules in cwd without importing the same file twice.
        """
        cwd = Path.cwd()
        modules: list[ModuleType] = []
        visited_files: set[str] = set()

        if str(cwd) not in sys.path:
            sys.path.insert(0, str(cwd))

        for py in cwd.rglob("*.py"):
            if any(part in EXCLUDE_DIRS for part in py.parts):
                continue

            if py.name.startswith("_"):
                continue

            abs_path = str(py.resolve())
            if abs_path in visited_files:
                continue
            visited_files.add(abs_path)

            rel_parts = py.with_suffix("").relative_to(cwd).parts
            module_name = ".".join(rel_parts)

            if module_name in sys.modules:
                modules.append(sys.modules[module_name])
                continue

            try:
                mod = importlib.import_module(module_name)
                modules.append(mod)
            except Exception:
                continue

        return modules

    @staticmethod
    def _collect_query_patterns(
        modules: Iterable[ModuleType],
    ) -> tuple[list[QueryPattern], OrderedDict[QueryPattern, int]]:
        """
        Return (patterns, counts)
        patterns: ordered list with dedupe
        counts: {pattern: occurrence count}
        """
        counts: OrderedDict[QueryPattern, int] = OrderedDict()

        for module in modules:
            for _, obj in vars(module).items():
                if inspect.isfunction(obj):
                    for p in get_patterns(obj):
                        counts[p] = counts.get(p, 0) + 1
                elif inspect.isclass(obj):
                    for _, fn in inspect.getmembers(obj, inspect.isfunction):
                        for p in get_patterns(fn):
                            counts[p] = counts.get(p, 0) + 1

        patterns = list(counts.keys())
        if not patterns:
            raise click.ClickException("No @query_pattern declarations found.")
        return patterns, counts

    def _collect_indexes_by_source(self) -> IndexSet:
        raise NotImplementedError

    @staticmethod
    def _analyze_patterns(
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

    def _print_results(self, results, counts: OrderedDict[QueryPattern, int]):
        for status, pattern in results:
            key = f"{pattern.table}{pattern.columns}"

            usage_suffix = f"[usage={counts.get(pattern, 1)}]"
            if status == "missing":
                click.echo(click.style(f"[MISSING] {key} {usage_suffix}", fg="red"))
            else:
                if not self.quiet:
                    click.echo(click.style(f"[OK] {key} {usage_suffix}", fg="green"))
