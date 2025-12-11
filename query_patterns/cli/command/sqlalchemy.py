import importlib
import sys

import click

from query_patterns.analyze import analyze_patterns
from query_patterns.cli.tools.sqlalchemy import collect_sqlalchemy_indexes_from_schema, \
    collect_sqlalchemy_indexes_from_db
from query_patterns.collect import discover_modules_from_cwd, collect_query_patterns


@click.command(name="sqlalchemy")
@click.option(
    "--module",
    multiple=True,
    help="Python module path to scan (default: auto-discover project)",
)
@click.option(
    "--source",
    type=click.Choice(["schema", "db"], case_sensitive=False),
    default="schema",
    help="Where to collect indexes from: ORM schema or actual database",
)
@click.option(
    "--metadata",
    help="Python path to SQLAlchemy MetaData "
         "(e.g. app.db.Base.metadata). Required if --source=schema.",
)
@click.option(
    "--engine-url",
    help="Database URL (required if --source=db)",
)
def sqlalchemy_cmd(module, metadata, source, engine_url):
    """
    Analyze SQLAlchemy query-patterns vs database indexes.
    """

    try:
        import sqlalchemy  # noqa: F401
    except ImportError:
        raise click.ClickException(
            "SQLAlchemy support requires "
            "`pip install query-patterns[sqlalchemy]`"
        )

    # collect modules
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

    # SCHEMA MODE
    if source == "schema":
        if not metadata:
            raise click.ClickException(
                "--metadata is required when --source=schema"
            )

        # load metadata
        try:
            mod_path, attr = metadata.rsplit(".", 1)
            meta = getattr(importlib.import_module(mod_path), attr)
        except Exception as e:
            raise click.ClickException(
                f"Failed to load MetaData: {metadata}\n{e}"
            )

        click.echo("Collecting indexes from SQLAlchemy schema...")
        indexes = collect_sqlalchemy_indexes_from_schema(meta)

    # DB MODE
    else:
        if metadata:
            click.echo(
                "[WARN] --metadata is ignored when --source=db",
                err=True,
            )

        if not engine_url:
            raise click.ClickException(
                "--engine-url is required when --source=db"
            )

        from sqlalchemy import create_engine
        engine = create_engine(engine_url)

        click.echo(f"Collecting indexes from database: {engine_url}")
        indexes = collect_sqlalchemy_indexes_from_db(engine)

    # analyze indexes
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
