import click

from query_patterns.cli.runner.django import DjangoRunner


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
@click.option(
    "--quiet", "-q", is_flag=True, help="Show errors only (suppress normal output)."
)
def django_cmd(module, settings, source, quiet):
    DjangoRunner(module=module, settings=settings, source=source, quiet=quiet).run()
