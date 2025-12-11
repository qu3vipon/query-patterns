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
    collect_django_indexes_from_schema, collect_django_indexes_from_db,
)


@click.command(name="django")
@click.option(
    "--source",
    type=click.Choice(["schema", "db"], case_sensitive=False),
    default="schema",
    help="Where to collect indexes from: Django model schema or actual DB.",
)
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
def django_cmd(module, settings, source):
    """
    Analyze Django query patterns against Django ORM indexes (schema or DB).
    """
    try:
        import django
    except ImportError:
        raise click.ClickException(
            "Django support requires installing with the [django] extra:\n"
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

    if source == "schema":
        click.echo("Collecting indexes from Django model schema...")
        indexes = collect_django_indexes_from_schema()
    else:
        click.echo("Collecting indexes from actual database...")
        indexes = collect_django_indexes_from_db()

    results = analyze_patterns(patterns, indexes)

    missing_found = False
    for status, pattern in results:
        key = f"{pattern.table}{pattern.columns}"
        if status == "ok":
            click.echo(click.style(f"[OK] {key}", fg="green"))
        else:
            missing_found = True
            click.echo(click.style(f"[MISSING] {key}", fg="red"))

    if missing_found:
        sys.exit(1)
