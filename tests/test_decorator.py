import pytest

from query_patterns.decorator import query_pattern
from query_patterns.pattern import QueryPattern
from query_patterns.utils import get_patterns


def test_single_query_pattern_attached():
    class Repo:
        @query_pattern(
            table="user_mission_submissions",
            columns=["user_id", "mission_id"],
        )
        def foo(self):
            pass

    fn = Repo.foo

    assert get_patterns(fn)
    patterns = fn.__query_patterns__
    assert len(patterns) == 1

    p = patterns[0]
    assert isinstance(p, QueryPattern)
    assert p.table == "user_mission_submissions"
    assert p.columns == ("user_id", "mission_id")


def test_multiple_query_patterns_attached():
    class Repo:
        @query_pattern(table="t", columns=["a"])
        @query_pattern(table="t", columns=["a", "b"])
        def foo(self):
            pass

    patterns = get_patterns(Repo.foo)
    assert len(patterns) == 2

    assert patterns[0].columns == ("a", "b")
    assert patterns[1].columns == ("a",)


def test_invalid_table_raises():
    with pytest.raises(ValueError):

        @query_pattern(table="", columns=["a"])
        def foo():
            pass


def test_empty_columns_raises():
    with pytest.raises(ValueError):

        @query_pattern(table="t", columns=[])
        def foo():
            pass


def test_query_pattern_decorator_prevents_duplicates(tmp_path, monkeypatch):
    import importlib
    import sys
    import tempfile

    module_name = f"mod_{next(tempfile._get_candidate_names())}"

    mod_file = tmp_path / f"{module_name}.py"
    mod_file.write_text(
        "from query_patterns import query_pattern\n"
        "@query_pattern(table='users', columns=['id'])\n"
        "def foo():\n"
        "    pass\n"
    )

    # Ensure import works and uses this path only
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))
    sys.modules.pop(module_name, None)

    # First import
    mod1 = importlib.import_module(module_name)
    fn1 = mod1.foo
    patterns1 = get_patterns(fn1)
    assert len(patterns1) == 1

    # Reload the module
    mod2 = importlib.reload(mod1)
    fn2 = mod2.foo
    patterns2 = get_patterns(fn2)

    # Ensure only one pattern registered
    assert len(patterns1) == len(patterns2) == 1
    pat = patterns2[0]
    assert pat.table == "users"
    assert pat.columns == ("id",)


def test_query_pattern_with_sqlalchemy_orm():
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

    class Base(DeclarativeBase):
        pass

    class User(Base):
        __tablename__ = "sa_users"

        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str]

    @query_pattern(table=User, columns=["id", "name"])
    def foo():
        pass

    patterns = get_patterns(foo)
    assert len(patterns) == 1
    assert patterns[0].table == "sa_users"
    assert patterns[0].columns == ("id", "name")


def test_query_pattern_with_sqlalchemy_table():
    from sqlalchemy import MetaData, Table, Column, Integer

    metadata = MetaData()

    user_table = Table(
        "sa_users",
        metadata,
        Column("id", Integer, primary_key=True),
    )

    @query_pattern(table=user_table, columns=["id"])
    def foo():
        pass

    patterns = get_patterns(foo)
    assert len(patterns) == 1
    assert patterns[0].table == "sa_users"
    assert patterns[0].columns == ("id",)


def setup_django():
    from django.conf import settings
    from django.apps import apps

    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[],
            DATABASES={
                "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
            },
        )
    if not apps.ready:
        apps.populate(settings.INSTALLED_APPS)


def test_query_pattern_with_django_model():
    setup_django()

    from django.db import models

    class User(models.Model):
        id = models.AutoField(primary_key=True)

        class Meta:
            app_label = "tests"
            db_table = "django_users"

    @query_pattern(table=User, columns=["id"])
    def foo():
        pass

    patterns = get_patterns(foo)
    assert patterns[0].table == "django_users"


def test_query_pattern_rejects_unsupported_type():
    class NotATable:
        pass

    with pytest.raises(TypeError):

        @query_pattern(table=NotATable, columns=["id"])
        def foo():
            pass


def test_columns_with_sqlalchemy_orm():
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

    class Base(DeclarativeBase):
        pass

    class User(Base):
        __tablename__ = "users"
        id: Mapped[int] = mapped_column(primary_key=True)
        email: Mapped[str]

    @query_pattern(table=User, columns=(User.id, User.email))
    def foo():
        pass

    patterns = get_patterns(foo)
    assert patterns[0].columns == ("id", "email")


def test_columns_with_sqlalchemy_table():
    from sqlalchemy import MetaData, Table, Column, Integer, String

    metadata = MetaData()

    user_table = Table(
        "users",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("email", String),
    )

    @query_pattern(table=user_table, columns=(user_table.c.id, user_table.c.email))
    def foo():
        pass

    patterns = get_patterns(foo)
    assert patterns[0].columns == ("id", "email")


def test_columns_with_django_fields():
    setup_django()

    from django.db import models

    class User2(models.Model):
        id = models.AutoField(primary_key=True)
        email = models.CharField(max_length=50)

        class Meta:
            app_label = "tests"
            db_table = "users"

    @query_pattern(
        table=User2,
        columns=(
            User2._meta.get_field("id"),
            User2._meta.get_field("email"),
        ),
    )
    def foo():
        pass

    patterns = get_patterns(foo)
    assert patterns[0].columns == ("id", "email")


def test_columns_invalid_type():
    class NotAColumn:
        pass

    with pytest.raises(TypeError):
        QueryPattern(table="users", columns=(NotAColumn(),))
