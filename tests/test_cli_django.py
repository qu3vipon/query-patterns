import sys
import textwrap
import click.testing

import pytest


@pytest.mark.parametrize("use_explicit_module", [False, True])
def test_django_command_end_to_end(tmp_path, monkeypatch, use_explicit_module):
    """
    Full end-to-end test for the Django CLI command.

    Steps:
    1) Create a fake Django project structure in tmp_path
    2) Define:
        - settings module
        - a Django app with a model
        - a repo file containing @query_pattern
    3) Run `query-patterns django` with CliRunner
    4) Ensure output shows index missing or ok
    """

    project = tmp_path / "proj"
    project.mkdir()

    (project / "settings.py").write_text(textwrap.dedent("""
        INSTALLED_APPS = ["app"]
        SECRET_KEY = "dummy"
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        }
    """))

    app_dir = project / "app"
    app_dir.mkdir()
    (app_dir / "__init__.py").write_text("")

    (app_dir / "models.py").write_text(textwrap.dedent("""
        from django.db import models

        class User(models.Model):
            email = models.CharField(max_length=255)

            class Meta:
                indexes = [
                    models.Index(fields=["email"]),
                ]
    """))

    repo_code = textwrap.dedent("""
        from query_patterns import query_pattern

        class Repo:
            @query_pattern(table="app_user", columns=["email"])
            def find(self):
                pass
    """)
    (app_dir / "repo.py").write_text(repo_code)

    monkeypatch.chdir(project)
    monkeypatch.setenv("PYTHONPATH", str(project))

    sys.path.insert(0, str(project))
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "settings")

    from query_patterns.cli.main import main as cli_main
    runner = click.testing.CliRunner()

    if use_explicit_module:
        result = runner.invoke(
            cli_main,
            [
                "django",
                "--module", "app.repo",
                "--settings", "settings",
            ],
        )
    else:
        result = runner.invoke(
            cli_main,
            [
                "django",
                "--settings", "settings",
            ],
        )

    assert result.exit_code == 0, result.output

    assert "[OK] app_user('email',)" in result.output
    assert "[MISSING]" not in result.output
