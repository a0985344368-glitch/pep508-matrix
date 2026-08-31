from pathlib import Path

import pytest

from pep508_matrix.errors import InputError
from pep508_matrix.project import load_dependencies


def test_reads_project_dependencies(project_factory, basic_project):
    root = project_factory(basic_project)
    result = load_dependencies(root / "pyproject.toml")
    assert [item.requirement for item in result] == ["colorama; sys_platform == 'win32'"]


def test_reads_optional_dependencies(project_factory):
    root = project_factory('''[project]\nname="x"\nversion="1"\n[project.optional-dependencies]\ntest=["old; python_version < '3.12'"]\n''')
    result = load_dependencies(root / "pyproject.toml")
    assert result[0].source_group == "project.optional-dependencies.test"


def test_optional_groups_are_sorted(project_factory):
    root = project_factory('''[project]\nname="x"\nversion="1"\n[project.optional-dependencies]\nz=["z; os_name == 'nt'"]\na=["a; os_name == 'nt'"]\n''')
    assert [item.source_group for item in load_dependencies(root / "pyproject.toml")] == [
        "project.optional-dependencies.a", "project.optional-dependencies.z"
    ]


def test_ignores_requirements_without_markers(project_factory):
    root = project_factory('''[project]\nname="x"\nversion="1"\ndependencies=["requests"]\n''')
    assert load_dependencies(root / "pyproject.toml") == ()


def test_missing_pyproject_is_input_error(tmp_path: Path):
    with pytest.raises(InputError, match="not found"):
        load_dependencies(tmp_path / "pyproject.toml")


def test_invalid_toml_is_input_error(project_factory):
    root = project_factory("[project\n")
    with pytest.raises(InputError, match="cannot read"):
        load_dependencies(root / "pyproject.toml")


def test_invalid_requirement_is_input_error(project_factory):
    root = project_factory('''[project]\nname="x"\nversion="1"\ndependencies=["bad ???"]\n''')
    with pytest.raises(InputError, match="invalid requirement"):
        load_dependencies(root / "pyproject.toml")


def test_dependencies_must_be_list(project_factory):
    root = project_factory('''[project]\nname="x"\nversion="1"\ndependencies="no"\n''')
    with pytest.raises(InputError, match="must be a list"):
        load_dependencies(root / "pyproject.toml")


def test_dependencies_must_contain_strings(project_factory):
    root = project_factory('''[project]\nname="x"\nversion="1"\ndependencies=[4]\n''')
    with pytest.raises(InputError, match="must be a list"):
        load_dependencies(root / "pyproject.toml")


def test_optional_dependencies_must_be_table(project_factory):
    root = project_factory('''[project]\nname="x"\nversion="1"\noptional-dependencies=[]\n''')
    with pytest.raises(InputError, match="must be a table"):
        load_dependencies(root / "pyproject.toml")
