import importlib
import sys

import click

from query_patterns.analyze import analyze_patterns
from query_patterns.cli.tools.sqlalchemy import collect_sqlalchemy_indexes
from query_patterns.collect import discover_modules_from_cwd, collect_query_patterns


@click.command(name="sqlalchemy")
@click.option(
    "--module",
    multiple=True,
    help="Python module path to scan (default: auto-discover project)",
)
@click.option(
    "--metadata",
    required=True,
    help="Python path to SQLAlchemy MetaData "
         "(e.g. app.db.Base.metadata)",
)
@click.option(
    "--fail-on-missing",
    is_flag=True,
    help="Exit with non-zero status if missing indexes are found",
)
def sqlalchemy_cmd(module, metadata, fail_on_missing):
    """
    Analyze SQLAlchemy query-patterns vs database indexes.
    """
    # -----------------------------
    # lazy import / dependency check
    # -----------------------------
    try:
        import sqlalchemy  # noqa: F401
    except ImportError:
        raise click.ClickException(
            "SQLAlchemy support requires "
            "`pip install query-patterns[sqlalchemy]`"
        )

    # -----------------------------
    # collect modules
    # -----------------------------
    if module:
        modules = [importlib.import_module(m) for m in module]
    else:
        click.echo("Auto-discovering project modules...")
        modules = discover_modules_from_cwd()

    if not modules:
        raise click.ClickException("No modules found to scan")

    patterns = collect_query_patterns(modules)

    if not patterns:
        click.echo("No query-patterns found")
        return

    # -----------------------------
    # load metadata
    # -----------------------------
    try:
        mod_path, attr = metadata.rsplit(".", 1)
        meta = getattr(importlib.import_module(mod_path), attr)
    except Exception as e:
        raise click.ClickException(
            f"Failed to load MetaData: {metadata}\n{e}"
        )

    # -----------------------------
    # collect indexes + analyze
    # -----------------------------
    indexes = collect_sqlalchemy_indexes(meta)
    results = analyze_patterns(patterns, indexes)

    missing_found = False

    for status, pattern in results:
        key = f"{pattern.table}{pattern.columns}"
        if status == "ok":
            click.echo(click.style(f"[OK] {key}", fg="green"))
        else:
            missing_found = True
            click.echo(click.style(f"[MISSING] {key}", fg="red"))

    if missing_found and fail_on_missing:
        sys.exit(1)
