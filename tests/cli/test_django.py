import os
import sys
import textwrap

import click.testing
import pytest
from django.apps import apps
from django.db import connection

from query_patterns.cli.main import main as cli_main
from tests.cli.conftest import run_cli_in_subprocess


@pytest.mark.parametrize("use_explicit_module", [False, True])
def test_cli_django_from_schema_success(
    tmp_path, monkeypatch, use_explicit_module, random_app_label
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

    (app_dir / "models.py").write_text(
        textwrap.dedent(f"""
            from django.db import models

            class User(models.Model):
                email = models.CharField(max_length=255, unique=True)
                username = models.CharField(max_length=50)
                age = models.IntegerField()

                class Meta:
                    app_label = "{random_app_label}"
                    db_table = "user"
                    constraints = [
                        models.UniqueConstraint(
                            fields=["username"],
                            name="uq_user_username",
                        ),
                    ]
                    indexes = [
                        models.Index(fields=["username", "age"]),
                    ]
        """)
    )

    (app_dir / "repo.py").write_text(
        textwrap.dedent("""
            from query_patterns import query_pattern

            class Repo:
                @query_pattern(table="user", columns=["id"])
                def by_id(self): ...

                @query_pattern(table="user", columns=["email"])
                def by_email(self): ...

                @query_pattern(table="user", columns=["username"])
                def by_username(self): ...

                @query_pattern(table="user", columns=["username", "age"])
                def by_username_and_age(self): ...
        """)
    )

    monkeypatch.chdir(project)
    monkeypatch.setenv("PYTHONPATH", str(project))
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "settings")
    sys.path.insert(0, str(project))

    # when
    cmd = ["query-patterns", "django", "--settings", "settings"]
    if use_explicit_module:
        cmd += ["--module", f"{random_app_label}.repo"]
    result = run_cli_in_subprocess(cmd, cwd=project)

    # then
    assert "[MISSING]" not in result.stdout

    assert "[OK] user('id',)" in result.stdout
    assert "[OK] user('email',)" in result.stdout
    assert "[OK] user('username',)" in result.stdout
    assert "[OK] user('username', 'age')" in result.stdout


@pytest.mark.parametrize("use_explicit_module", [False, True])
def test_cli_django_from_schema_missing(
    tmp_path, monkeypatch, use_explicit_module, random_app_label
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

    (app_dir / "models.py").write_text(
        textwrap.dedent(f"""
                from django.db import models

                class User(models.Model):
                    email = models.CharField(max_length=255)
                    username = models.CharField(max_length=50)
                    age = models.IntegerField()

                    class Meta:
                        app_label = "{random_app_label}"
                        db_table = "user"
            """)
    )

    (app_dir / "repo.py").write_text(
        textwrap.dedent("""
            from query_patterns import query_pattern

            class Repo:
                @query_pattern(table="user", columns=["id"])
                def by_id(self): ...

                @query_pattern(table="user", columns=["email"])
                def by_email(self): ...

                @query_pattern(table="user", columns=["username"])
                def by_username(self): ...

                @query_pattern(table="user", columns=["username", "age"])
                def by_username_and_age(self): ...
            """)
    )

    monkeypatch.chdir(project)
    monkeypatch.setenv("PYTHONPATH", str(project))
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "settings")
    sys.path.insert(0, str(project))

    # when
    cmd = ["query-patterns", "django", "--settings", "settings"]
    if use_explicit_module:
        cmd += ["--module", f"{random_app_label}.repo"]
    result = run_cli_in_subprocess(cmd, cwd=project)

    # then
    assert "[OK] user('id',)" in result.stdout

    assert "[MISSING] user('email',)" in result.stdout
    assert "[MISSING] user('username',)" in result.stdout
    assert "[MISSING] user('username', 'age')" in result.stdout



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
                "NAME": "test.db",
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
            @query_pattern(table="{table_name}", columns=["id"])
            def by_id(self): pass

            @query_pattern(table="{table_name}", columns=["email"])
            def by_email(self): pass

            @query_pattern(table="{table_name}", columns=["username"])
            def by_username(self): pass
    """)
    )

    monkeypatch.chdir(project)
    monkeypatch.setenv("PYTHONPATH", str(project))
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "settings")
    sys.path.insert(0, str(project))

    with connection.cursor() as cursor:
        cursor.execute(f"""
            CREATE TABLE {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                username TEXT UNIQUE
            );
        """)
        cursor.execute(f"""
            CREATE INDEX ix_{table_name}_email
            ON {table_name} (email);
        """)
    connection.close()

    # when
    cmd = ["query-patterns", "django", "--settings", "settings", "--source", "db"]
    if use_explicit_module:
        cmd += ["--module", f"{random_app_label}.repo"]
    result = run_cli_in_subprocess(cmd, cwd=project)

    # then
    assert "[MISSING]" not in result.stdout

    assert f"[OK] {table_name}('id',)" in result.stdout
    assert f"[OK] {table_name}('email',)" in result.stdout
    assert f"[OK] {table_name}('username',)" in result.stdout


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
                "NAME": "test.db",
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
            @query_pattern(table="{table_name}", columns=["id"])
            def by_id(self): pass

            @query_pattern(table="{table_name}", columns=["username"])
            def by_username(self): pass

            @query_pattern(table="{table_name}", columns=["email"])
            def by_email(self): pass
    """)
    )

    monkeypatch.chdir(project)
    monkeypatch.setenv("PYTHONPATH", str(project))
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "settings")
    sys.path.insert(0, str(project))

    with connection.cursor() as cursor:
        cursor.execute(f"""
            CREATE TABLE {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT,
                username TEXT UNIQUE
            );
        """)
    connection.close()

    # when
    cmd = ["query-patterns", "django", "--settings", "settings", "--source", "db"]
    if use_explicit_module:
        cmd += ["--module", f"{random_app_label}.repo"]
    result = run_cli_in_subprocess(cmd, cwd=project)

    # then
    assert f"[MISSING] {table_name}('email',)" in result.stdout

    assert f"[OK] {table_name}('id',)" in result.stdout
    assert f"[OK] {table_name}('username',)" in result.stdout
