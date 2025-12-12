import click

from query_patterns.cli.runner.sqlalchemy import SQLAlchemyRunner


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
@click.option(
    "--quiet", "-q", is_flag=True, help="Show errors only (suppress normal output)."
)
def sqlalchemy_cmd(module, metadata, source, engine_url, quiet):
    SQLAlchemyRunner(
        module=module,
        metadata=metadata,
        source=source,
        engine_url=engine_url,
        quiet=quiet,
    ).run()
