from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def project_factory(tmp_path: Path):
    def create(pyproject: str, workflows: dict[str, str] | None = None) -> Path:
        (tmp_path / "pyproject.toml").write_text(pyproject, encoding="utf-8")
        if workflows:
            directory = tmp_path / ".github" / "workflows"
            directory.mkdir(parents=True)
            for name, content in workflows.items():
                (directory / name).write_text(content, encoding="utf-8")
        return tmp_path

    return create


@pytest.fixture
def basic_project() -> str:
    return '''
[project]
name = "fixture"
version = "1"
dependencies = [
  "colorama; sys_platform == 'win32'",
  "plain-package",
]
'''


@pytest.fixture
def broad_workflow() -> str:
    return '''
name: synthetic
on: push
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-14]
        python-version: ["3.11", "3.13"]
    steps: []
'''
