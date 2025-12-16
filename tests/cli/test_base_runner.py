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


def test_collects_patterns_from_class_method(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    (tmp_path / "m.py").write_text(
        """
from query_patterns import query_pattern

class Repo:
    @query_pattern(table="users", columns=["id"])
    def foo(self):
        pass
"""
    )

    runner = DummyRunner()
    modules = runner._discover_modules_from_cwd()
    patterns, counts = runner._collect_query_patterns(modules)

    assert len(patterns) == 1
    p = patterns[0]
    assert p.table == "users"
    assert p.columns == ("id",)



def test_collects_patterns_from_function(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    (tmp_path / "m.py").write_text(
        """
from query_patterns import query_pattern

@query_pattern(table="users", columns=["id"])
def foo():
    pass
"""
    )
    runner = DummyRunner()

    modules = runner._discover_modules_from_cwd()
    patterns, counts = runner._collect_query_patterns(modules)

    assert len(patterns) == 1
    p = patterns[0]

    assert p.table == "users"
    assert p.columns == ("id",)
    assert counts[p] == 1



def test_collect_query_patterns_with_counts(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    (tmp_path / "a.py").write_text(
        """
from query_patterns import query_pattern

class RepoA:
    @query_pattern(table="users", columns=["id"])
    def foo(self):
        pass
"""
    )

    (tmp_path / "b.py").write_text(
        """
from query_patterns import query_pattern

class RepoB:
    @query_pattern(table="users", columns=["id"])
    def foo(self):
        pass
"""
    )

    runner = DummyRunner()

    modules = runner._discover_modules_from_cwd()
    patterns, counts = runner._collect_query_patterns(modules)

    # then
    assert len(patterns) == 1

    p = patterns[0]
    assert p.table == "users"
    assert p.columns == ("id",)
    assert counts[p] == 2



def test_import_module_from_cwd_ignores_stdlib(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    runner = DummyRunner()
    mods = runner._import_module_from_cwd(("logging",))

    assert mods == []


def test_discover_modules_excludes_stdlib(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    (tmp_path / "a.py").write_text("import logging\nx = 1")

    runner = DummyRunner()
    mods = runner._discover_modules_from_cwd()

    names = {m.__name__ for m in mods}

    assert "a" in names
    assert "logging" not in names


def test_collect_query_patterns_only_local_definitions(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    ext_dir = tmp_path.parent / "external_pkg"
    ext_dir.mkdir()

    (ext_dir / "external.py").write_text(
        """
from query_patterns import query_pattern

@query_pattern(table="external_table", columns=["id"])
def external_func():
    pass
"""
    )
    monkeypatch.syspath_prepend(str(ext_dir))

    (tmp_path / "local.py").write_text(
        """
from external import external_func
from query_patterns import query_pattern

@query_pattern(table="local_table", columns=["id"])
def local_func():
    pass
"""
    )

    runner = DummyRunner()
    modules = runner._discover_modules_from_cwd()

    module_names = {m.__name__ for m in modules}
    assert module_names == {"local"}

    patterns, counts = runner._collect_query_patterns(modules)

    tables = {p.table for p in patterns}

    assert tables == {"local_table"}

    assert list(counts.values()) == [1]
