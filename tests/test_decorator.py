import pytest

from query_patterns.decorator import query_pattern
from query_patterns.pattern import QueryPattern


def test_single_query_pattern_attached():
    class Repo:
        @query_pattern(
            table="user_mission_submissions",
            columns=["user_id", "mission_id"],
        )
        def foo(self):
            pass

    fn = Repo.foo

    assert hasattr(fn, "__query_patterns__")
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

    patterns = Repo.foo.__query_patterns__
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
    import importlib, sys, tempfile

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
    patterns1 = getattr(fn1, '__query_patterns__', [])

    # Reload the module
    mod2 = importlib.reload(mod1)
    fn2 = mod2.foo
    patterns2 = getattr(fn2, '__query_patterns__', [])

    # Ensure only one pattern registered
    assert len(patterns1) == len(patterns2) == 1
    pat = patterns2[0]
    assert pat.table == "users"
    assert pat.columns == ("id",)
