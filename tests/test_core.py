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
