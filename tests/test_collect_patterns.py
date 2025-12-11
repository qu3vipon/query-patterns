from query_patterns import query_pattern
from query_patterns.collect import collect_query_patterns


def test_collects_patterns_from_class_methods():
    class Module:
        class Repo:
            @staticmethod
            def foo(): pass

    pattern = object()
    Module.Repo.foo.__query_patterns__ = [pattern]

    patterns = collect_query_patterns([Module])
    assert patterns == [pattern]


def test_collects_patterns_from_functions():
    class Module:
        pass

    @query_pattern(table="users", columns=["id"])
    def foo():
        pass

    # assign function to module namespace
    Module.foo = foo

    # collector should discover the pattern
    patterns = collect_query_patterns([Module])

    assert len(patterns) == 1

    p = patterns[0]
    assert p.table == "users"
    assert p.columns == ("id",)


def test_collect_query_patterns_dedupes():
    class ModA:
        pass

    class ModB:
        pass

    @query_pattern(table="users", columns=["id"])
    def foo():
        pass

    ModA.foo = foo
    ModB.foo = foo

    patterns = collect_query_patterns([ModA, ModB])

    assert len(patterns) == 1
    p = patterns[0]
    assert p.table == "users"
    assert p.columns == ("id",)
