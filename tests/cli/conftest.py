import secrets
import sys

import pytest


@pytest.fixture
def random_app_label():
    return f"app_{secrets.token_hex(4)}"


@pytest.fixture
def isolated_cwd_and_module(tmp_path, monkeypatch):
    def _setup(*module_names: str):
        for name in module_names:
            sys.modules.pop(name, None)

        monkeypatch.chdir(tmp_path)
        monkeypatch.syspath_prepend(str(tmp_path))

        return tmp_path

    return _setup


def run_cli_in_subprocess(cmd, cwd):
    import subprocess

    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return result
