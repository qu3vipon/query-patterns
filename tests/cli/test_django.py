import sys
import textwrap

import click.testing
import pytest
from django.db import connection

from query_patterns.cli.main import main as cli_main


@pytest.mark.parametrize("use_explicit_module", [False, True])
def test_cli_django_from_schema_success(
    tmp_path, monkeypatch, use_explicit_module, random_app_label
):
    # given
    project = tmp_path / "sample_project"
    project.mkdir()

    (project / "settings.py").write_text(
        textwrap.dedent(f"""
            INSTALLED_APPS = ["django.contrib.contenttypes", "{random_app_label}"]
            SECRET_KEY = "dummy"
            DATABASES = {{
                "default": {{
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }}
            }}
        """)
    )

    app_dir = project / random_app_label
    app_dir.mkdir()
    (app_dir / "__init__.py").write_text("")

    (app_dir / "orm.py").write_text(
        textwrap.dedent(f"""
            from django.db import models

            class User(models.Model):
                email = models.CharField(max_length=255)

                class Meta:
                    app_label = "{random_app_label}"
                    db_table = "user"
                    indexes = [
                        models.Index(fields=["email"]),
                    ]
        """)
    )

    (app_dir / "repo.py").write_text(
        textwrap.dedent("""
            from query_patterns import query_pattern

            class Repo:
                @query_pattern(table="user", columns=["email"])
                def find(self):
                    pass
        """)
    )

    monkeypatch.chdir(project)
    monkeypatch.setenv("PYTHONPATH", str(project))
    sys.path.insert(0, str(project))
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "settings")

    # when
    runner = click.testing.CliRunner()
    if use_explicit_module:
        result = runner.invoke(
            cli_main,
            [
                "django",
                "--module",
                f"{random_app_label}.repo",
                "--settings",
                "settings",
            ],
        )
    else:
        result = runner.invoke(
            cli_main,
            [
                "django",
                "--settings",
                "settings",
            ],
        )

    # then
    assert "[OK] user('email',)" in result.output, result.output
    assert "[MISSING]" not in result.output, result.output


@pytest.mark.parametrize("use_explicit_module", [False, True])
def test_cli_django_from_schema_missing(
    tmp_path, monkeypatch, use_explicit_module, random_app_label
):
    project = tmp_path / "sample_project"
    project.mkdir()

    (project / "settings.py").write_text(
        textwrap.dedent(f"""
            INSTALLED_APPS = ["{random_app_label}"]
            SECRET_KEY = "dummy"
            DATABASES = {{
                "default": {{
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }}
            }}
        """)
    )

    app_dir = project / random_app_label
    app_dir.mkdir()
    (app_dir / "__init__.py").write_text("")

    (app_dir / "orm.py").write_text(
        textwrap.dedent(f"""
            from django.db import models

            class User(models.Model):
                email = models.CharField(max_length=255)

                class Meta:
                    app_label = "{random_app_label}"
                    db_table = "app_user"
                    indexes = []
        """)
    )

    (app_dir / "repo.py").write_text(
        textwrap.dedent("""
            from query_patterns import query_pattern

            class Repo:
                @query_pattern(table="app_user", columns=["email"])
                def find(self):
                    pass
        """)
    )

    monkeypatch.chdir(project)
    monkeypatch.setenv("PYTHONPATH", str(project))
    sys.path.insert(0, str(project))
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "settings")

    runner = click.testing.CliRunner()

    if use_explicit_module:
        result = runner.invoke(
            cli_main,
            [
                "django",
                "--module",
                f"{random_app_label}.repo",
                "--settings",
                "settings",
            ],
        )
    else:
        result = runner.invoke(
            cli_main,
            ["django", "--settings", "settings"],
        )

    assert "[MISSING] app_user('email',)" in result.output
    assert "[usage=1]" in result.output
    assert "[OK]" not in result.output


@pytest.mark.parametrize("use_explicit_module", [False, True])
def test_cli_django_from_db_success(
    tmp_path,
    monkeypatch,
    use_explicit_module,
    random_app_label,
):
    # given
    project = tmp_path / "sample_project"
    project.mkdir()

    (project / "settings.py").write_text(
        textwrap.dedent(f"""
        INSTALLED_APPS = ["{random_app_label}"]
        SECRET_KEY = "dummy"
        DATABASES = {{
            "default": {{
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }}
        }}
    """)
    )

    app_dir = project / random_app_label
    app_dir.mkdir()
    (app_dir / "__init__.py").write_text("")

    table_name = f"{random_app_label}_user"

    (app_dir / "repo.py").write_text(
        textwrap.dedent(f"""
        from query_patterns import query_pattern

        class Repo:
            @query_pattern(table="{table_name}", columns=["email"])
            def find(self):
                pass
    """)
    )

    monkeypatch.chdir(project)
    monkeypatch.setenv("PYTHONPATH", str(project))
    sys.path.insert(0, str(project))
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "settings")

    with connection.cursor() as cursor:
        cursor.execute(f"""
            CREATE TABLE {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT
            );
        """)
        cursor.execute(f"""
            CREATE INDEX ix_{table_name}_email
            ON {table_name} (email);
        """)

    # when
    runner = click.testing.CliRunner()
    if use_explicit_module:
        result = runner.invoke(
            cli_main,
            [
                "django",
                "--source",
                "db",
                "--settings",
                "settings",
                "--module",
                f"{random_app_label}.repo",
            ],
        )
    else:
        result = runner.invoke(
            cli_main,
            [
                "django",
                "--source",
                "db",
                "--settings",
                "settings",
            ],
        )

    # then
    assert f"[OK] {table_name}('email',)" in result.output
    assert "[MISSING]" not in result.output


@pytest.mark.parametrize("use_explicit_module", [False, True])
def test_cli_django_from_db_missing(
    tmp_path,
    monkeypatch,
    use_explicit_module,
    random_app_label,
):
    # given
    project = tmp_path / "sample_project"
    project.mkdir()

    (project / "settings.py").write_text(
        textwrap.dedent(f"""
        INSTALLED_APPS = ["{random_app_label}"]
        SECRET_KEY = "dummy"
        DATABASES = {{
            "default": {{
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }}
        }}
    """)
    )

    app_dir = project / random_app_label
    app_dir.mkdir()
    (app_dir / "__init__.py").write_text("")

    table_name = f"{random_app_label}_user"

    (app_dir / "repo.py").write_text(
        textwrap.dedent(f"""
        from query_patterns import query_pattern

        class Repo:
            @query_pattern(table="{table_name}", columns=["email"])
            def find(self):
                pass
    """)
    )

    monkeypatch.chdir(project)
    monkeypatch.setenv("PYTHONPATH", str(project))
    sys.path.insert(0, str(project))
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "settings")

    with connection.cursor() as cursor:
        cursor.execute(f"""
            CREATE TABLE {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT
            );
        """)

    # when
    runner = click.testing.CliRunner()
    if use_explicit_module:
        result = runner.invoke(
            cli_main,
            [
                "django",
                "--source",
                "db",
                "--settings",
                "settings",
                "--module",
                f"{random_app_label}.repo",
            ],
        )
    else:
        result = runner.invoke(
            cli_main,
            [
                "django",
                "--source",
                "db",
                "--settings",
                "settings",
            ],
        )

    # then
    assert f"[MISSING] {table_name}('email',)" in result.output
    assert "[usage=1]" in result.output
    assert "[OK]" not in result.output
