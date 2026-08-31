import json

import pytest

from pep508_matrix.cli import main
from pep508_matrix.models import AnalysisReport, Environment
from pep508_matrix.output import render_json


def test_json_is_deterministic(project_factory, broad_workflow, basic_project, capsys):
    root = project_factory(basic_project, {"ci.yml": broad_workflow})
    assert main(["check", str(root), "--format", "json"]) == 0
    first = capsys.readouterr().out
    assert main(["check", str(root), "--format", "json"]) == 0
    second = capsys.readouterr().out
    assert first == second
    assert json.loads(first)["observations"][0]["status"] == "BOTH_OUTCOMES"


def test_render_json_sorts_environment_keys():
    report = AnalysisReport((), (Environment("x", {"z": "1", "a": "2"}),))
    rendered = render_json(report)
    assert rendered.index('"a"') < rendered.index('"z"')


def test_cli_exit_zero_for_both(project_factory, broad_workflow, basic_project, capsys):
    root = project_factory(basic_project, {"ci.yml": broad_workflow})
    assert main(["check", str(root)]) == 0


def test_cli_exit_one_for_one_sided(project_factory, capsys):
    root = project_factory('''[project]\nname="x"\nversion="1"\ndependencies=["demo; sys_platform == 'win32'"]\n''', {"ci.yml": "jobs:\n  t:\n    runs-on: ubuntu-latest\n    strategy:\n      matrix:\n        python: ['3.11']\n"})
    assert main(["check", str(root)]) == 1


def test_unknown_warns_but_exit_zero(project_factory, capsys):
    root = project_factory('''[project]\nname="x"\nversion="1"\ndependencies=["demo; platform_machine == 'arm64'"]\n''', {"ci.yml": "jobs:\n  t:\n    runs-on: ubuntu-latest\n    strategy:\n      matrix:\n        python: ['3.11']\n"})
    assert main(["check", str(root)]) == 0
    assert "UNKNOWN" in capsys.readouterr().out


def test_strict_unknown_exits_one(project_factory, capsys):
    root = project_factory('''[project]\nname="x"\nversion="1"\ndependencies=["demo; platform_machine == 'arm64'"]\n''', {"ci.yml": "jobs:\n  t:\n    runs-on: ubuntu-latest\n"})
    assert main(["check", str(root), "--strict-unknown"]) == 1


def test_input_error_exits_two(tmp_path, capsys):
    assert main(["check", str(tmp_path)]) == 2
    assert "input error" in capsys.readouterr().err


def test_parse_error_exits_two():
    with pytest.raises(SystemExit) as raised:
        main(["check", "--format", "xml"])
    assert raised.value.code == 2


def test_no_markers_exit_zero(project_factory, broad_workflow, capsys):
    root = project_factory('''[project]\nname="x"\nversion="1"\ndependencies=["demo"]\n''', {"ci.yml": broad_workflow})
    assert main(["check", str(root)]) == 0
    assert "No PEP 508" in capsys.readouterr().out


def test_repeatable_workflow_override(project_factory, capsys):
    root = project_factory('''[project]\nname="x"\nversion="1"\ndependencies=["demo; sys_platform == 'win32'"]\n''')
    one = root / "one.yml"
    two = root / "two.yml"
    one.write_text("jobs:\n  a:\n    runs-on: ubuntu-latest\n    strategy:\n      matrix:\n        python: ['3.11']\n")
    two.write_text("jobs:\n  b:\n    runs-on: windows-latest\n    strategy:\n      matrix:\n        python: ['3.11']\n")
    assert main(["check", str(root), "--workflow", "one.yml", "--workflow", "two.yml"]) == 0


def test_json_zero_marker_shape(project_factory, capsys):
    root = project_factory('''[project]\nname="x"\nversion="1"\ndependencies=[]\n''')
    assert main(["check", str(root), "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["observations"] == []
