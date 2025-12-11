import tempfile

from query_patterns.collect import collect_query_patterns, discover_modules_from_cwd


def test_collect_from_module():
    class FakeModule:
        class Repo:
            @staticmethod
            def foo(): pass

    pattern = object()
    FakeModule.Repo.foo.__query_patterns__ = [pattern]

    patterns = collect_query_patterns([FakeModule])
    assert patterns == [pattern]


def test_auto_discover(tmp_path, monkeypatch):
    project_dir = tmp_path / "sample_project"
    project_dir.mkdir()

    (project_dir / "example").mkdir()
    (project_dir / "example" / "__init__.py").write_text("")

    (project_dir / "example" / "repo.py").write_text("""
from query_patterns import query_pattern

class Repo:
    @query_pattern(table="users", columns=["id"])
    def foo(self):
        pass
""")

    monkeypatch.chdir(project_dir)

    from query_patterns.collect import discover_modules_from_cwd, collect_query_patterns

    modules = discover_modules_from_cwd()
    patterns = collect_query_patterns(modules)

    assert len(patterns) == 1
    p = patterns[0]
    assert p.table == "users"
    assert p.columns == ("id",)


def test_discover_avoids_duplicate_imports(tmp_path, monkeypatch):
    """
    ensure discover loads correct module once,
    and symlink does not cause duplicate imports
    """

    # Ensure cwd for discover
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))

    # Unique module name
    modname = f"mod_{next(tempfile._get_candidate_names())}"

    # Actual module
    mod_file = tmp_path / f"{modname}.py"
    mod_file.write_text("value = 42")

    # Symlink to same file
    alias = tmp_path / "alias"
    alias.mkdir()
    alias_symlink = alias / f"{modname}.py"
    alias_symlink.symlink_to(mod_file)

    # Now run discover
    modules = discover_modules_from_cwd()

    assert len(modules) == 1

    m = modules[0]
    assert hasattr(m, "value")
    assert m.value == 42
