from query_patterns import query_pattern
from query_patterns.cli.runner.base import BaseRunner
from query_patterns.pattern import QueryPattern


class DummyRunner(BaseRunner):
    pass


def test_analyze_patterns():
    # given
    pattern = QueryPattern(table="users", columns=("id", "email"))
    indexes = {("users", ("id", "email"))}

    runner = DummyRunner()
    runner.patterns = [pattern]
    runner.indexes = indexes

    # when
    results = runner._analyze_patterns([pattern], indexes)

    # then
    assert results == [("ok", pattern)]


def test_auto_discover(tmp_path, monkeypatch):
    # given
    project_dir = tmp_path / "sample_project"
    project_dir.mkdir()

    (project_dir / "example").mkdir()
    (project_dir / "example" / "__init__.py").write_text("")
    (project_dir / "example" / "repo.py").write_text("")

    monkeypatch.chdir(project_dir)

    # when
    runner = DummyRunner()
    modules = runner._discover_modules_from_cwd()

    # then
    module_names = {m.__name__ for m in modules}
    assert "example.repo" in module_names


def test_auto_discover_avoids_duplicate_imports(tmp_path, monkeypatch):
    # given
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))

    mod_file = tmp_path / "my_mod.py"
    mod_file.write_text("")

    alias = tmp_path / "alias"
    alias.mkdir()
    alias_symlink = alias / "my_mod.py"
    alias_symlink.symlink_to(mod_file)

    # when
    runner = DummyRunner()
    modules = runner._discover_modules_from_cwd()

    # then
    assert len(modules) == 1


def test_collects_patterns_from_class_method():
    # given
    class Module:
        class Repo:
            @query_pattern(table="users", columns=["id"])
            def foo(self):
                pass

    # when
    runner = DummyRunner()
    patterns, counts = runner._collect_query_patterns([Module])

    # then
    assert len(patterns) == 1
    p = patterns[0]
    assert p.table == "users"
    assert p.columns == ("id",)


def test_collects_patterns_from_function():
    # given
    class Module:
        pass

    @query_pattern(table="users", columns=["id"])
    def foo():
        pass

    Module.foo = foo

    # when
    runner = DummyRunner()
    patterns, counts = runner._collect_query_patterns([Module])

    # then
    assert counts[patterns[0]] == 1
    assert len(patterns) == 1
    p = patterns[0]
    assert p.table == "users"
    assert p.columns == ("id",)


def test_collect_query_patterns_with_counts():
    # given
    class ModA:
        @query_pattern(table="users", columns=["id"])
        def foo(self):
            pass

    class ModB:
        @query_pattern(table="users", columns=["id"])
        def foo(self):
            pass

    # when
    runner = DummyRunner()
    patterns, counts = runner._collect_query_patterns([ModA, ModB])

    # then
    assert len(patterns) == 1
    p = patterns[0]
    assert p.table == "users"
    assert p.columns == ("id",)
    assert counts[p] == 2
