from query_patterns.analyze import analyze_patterns
from query_patterns.pattern import QueryPattern


def test_analyze_patterns():
    pattern = QueryPattern(table="users", columns=("id", "email"))

    indexes = {("users", ("id", "email"))}

    results = analyze_patterns([pattern], indexes)

    assert results == [("ok", pattern)]
