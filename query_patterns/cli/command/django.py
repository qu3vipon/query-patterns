import importlib
import sys
import click

from query_patterns.collect import (
    discover_modules_from_cwd,
    collect_query_patterns,
)
from query_patterns.analyze import analyze_patterns
from query_patterns.cli.tools.django import (
    setup_django,
    collect_django_indexes,
)


@click.command(name="django")
@click.option(
    "--module",
    multiple=True,
    help="Explicit Python module(s) to scan. "
         "If omitted, auto-discovery scans the current project.",
)
@click.option(
    "--settings",
    help="Django settings module path (e.g. config.settings). "
         "If omitted, DJANGO_SETTINGS_MODULE must be set.",
)
@click.option(
    "--fail-on-missing",
    is_flag=True,
    help="Exit with code 1 if missing indexes are found.",
)
def django_cmd(module, settings, fail_on_missing):
    """
    Analyze Django query patterns against Django ORM indexes.
    """
    try:
        import django  # noqa: F401
    except ImportError:
        raise click.ClickException(
            "Django support requires installing query-patterns with the [django] extra:\n"
            "    pip install query-patterns[django]"
        )

    try:
        setup_django(settings)
    except RuntimeError as e:
        raise click.ClickException(str(e))

    if module:
        modules = [importlib.import_module(m) for m in module]
    else:
        click.echo("Auto-discovering project modules...")
        modules = discover_modules_from_cwd()

    if not modules:
        raise click.ClickException("No modules found to scan.")

    patterns = collect_query_patterns(modules)
    if not patterns:
        click.echo("No @query_pattern declarations found.")
        return

    indexes = collect_django_indexes()

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
