from pathlib import Path

import pytest

from pep508_matrix.errors import InputError
from pep508_matrix.matrix import discover_workflows, expand_matrix, load_workflow


def test_cartesian_product():
    combinations, reasons = expand_matrix({"os": ["a", "b"], "python": ["3.11", "3.12"]})
    assert len(combinations) == 4
    assert reasons == ()


def test_matrix_size_cap_prevents_cartesian_explosion():
    combinations, reasons = expand_matrix({f"axis_{index}": [0, 1] for index in range(30)})
    assert combinations == [{}]
    assert "256-job limit" in reasons[0]


def test_exclude_partial_match():
    combinations, _ = expand_matrix({"os": ["a", "b"], "python": ["3.11"], "exclude": [{"os": "b"}]})
    assert combinations == [{"os": "a", "python": "3.11"}]


def test_include_adds_new_combination():
    combinations, _ = expand_matrix({"python": ["3.11"], "include": [{"python": "3.13", "os": "ubuntu-24.04"}]})
    assert {"python": "3.13", "os": "ubuntu-24.04"} in combinations


def test_duplicate_unmatched_includes_remain_separate_rows():
    addition = {"python": "3.13", "os": "ubuntu-24.04"}
    combinations, reasons = expand_matrix({
        "python": ["3.11"],
        "include": [addition, addition],
    })
    assert reasons == ()
    assert combinations.count(addition) == 2


def test_include_only_matrix_preserves_each_entry():
    combinations, reasons = expand_matrix({"include": [
        {"os": "ubuntu-latest", "python-version": "3.11"},
        {"os": "windows-latest", "python-version": "3.12"},
    ]})
    assert reasons == ()
    assert combinations == [
        {"os": "ubuntu-latest", "python-version": "3.11"},
        {"os": "windows-latest", "python-version": "3.12"},
    ]


def test_include_augments_compatible_combination():
    combinations, _ = expand_matrix({"python": ["3.11", "3.12"], "include": [{"color": "green"}]})
    assert all(item["color"] == "green" for item in combinations)


def test_unmatched_include_is_not_mutated_by_later_include():
    combinations, _ = expand_matrix({
        "python": ["3.11"],
        "include": [
            {"python": "3.12", "os": "ubuntu-latest"},
            {"color": "green"},
        ],
    })
    added = next(item for item in combinations if item.get("python") == "3.12")
    assert "color" not in added


def test_dynamic_axis_is_unknown():
    combinations, reasons = expand_matrix({"python": ["${{ value }}"]})
    assert combinations == [{}]
    assert "dynamic" in reasons[0]


def test_object_axis_is_unknown():
    _, reasons = expand_matrix({"python": [{"version": "3.11"}]})
    assert reasons


def test_bad_include_is_unknown():
    _, reasons = expand_matrix({"python": ["3.11"], "include": "no"})
    assert "include" in reasons[0]


def test_include_only_dynamic_value_is_unknown():
    combinations, reasons = expand_matrix({"include": [{"os": "${{ value }}"}]})
    assert combinations == [{}]
    assert "dynamic" in reasons[0]


def test_include_can_augment_matrix_at_size_limit():
    combinations, reasons = expand_matrix({
        "left": list(range(16)),
        "right": list(range(16)),
        "include": [{"color": "green"}],
    })
    assert len(combinations) == 256
    assert reasons == ()
    assert all(item["color"] == "green" for item in combinations)


def test_bad_exclude_is_unknown():
    _, reasons = expand_matrix({"python": ["3.11"], "exclude": "no"})
    assert "exclude" in reasons[0]


@pytest.mark.parametrize(
    ("label", "system", "platform", "os_name"),
    [
        ("ubuntu-24.04", "Linux", "linux", "posix"),
        ("windows-latest", "Windows", "win32", "nt"),
        ("macos-14", "Darwin", "darwin", "posix"),
    ],
)
def test_os_mapping(project_factory, label, system, platform, os_name):
    root = project_factory("[project]\nname='x'\nversion='1'", {"ci.yml": f"jobs:\n  t:\n    runs-on: ${{{{ matrix.os }}}}\n    strategy:\n      matrix:\n        os: [{label}]\n        python: ['3.11']\n"})
    env = load_workflow(root / ".github/workflows/ci.yml")[0]
    assert env.marker_environment["platform_system"] == system
    assert env.marker_environment["sys_platform"] == platform
    assert env.marker_environment["os_name"] == os_name


@pytest.mark.parametrize("axis", ["python-version", "python_version", "python"])
def test_python_axis_aliases(project_factory, axis):
    root = project_factory("[project]\nname='x'\nversion='1'", {"ci.yml": f"jobs:\n  t:\n    runs-on: ubuntu-latest\n    strategy:\n      matrix:\n        {axis}: ['3.12']\n"})
    env = load_workflow(root / ".github/workflows/ci.yml")[0]
    assert env.marker_environment["python_version"] == "3.12"
    assert "python_full_version" not in env.marker_environment


def test_full_python_version_preserved(project_factory):
    root = project_factory("[project]\nname='x'\nversion='1'", {"ci.yml": "jobs:\n  t:\n    runs-on: ubuntu-latest\n    strategy:\n      matrix:\n        python: ['3.11.8']\n"})
    env = load_workflow(root / ".github/workflows/ci.yml")[0]
    assert env.marker_environment["python_version"] == "3.11"
    assert env.marker_environment["python_full_version"] == "3.11.8"


@pytest.mark.parametrize("numeric", ["3.10", "311", "true"])
def test_unquoted_python_versions_are_unknown(project_factory, numeric):
    root = project_factory("[project]\nname='x'\nversion='1'", {"ci.yml": f"jobs:\n  t:\n    runs-on: ubuntu-latest\n    strategy:\n      matrix:\n        python: [{numeric}]\n"})
    env = load_workflow(root / ".github/workflows/ci.yml")[0]
    assert "python_version" not in env.marker_environment
    assert any("quoted literal string" in reason for reason in env.unknown_reasons)


def test_default_cpython(project_factory):
    root = project_factory("[project]\nname='x'\nversion='1'", {"ci.yml": "jobs:\n  t:\n    runs-on: ubuntu-latest\n    strategy:\n      matrix:\n        python: ['3.11']\n"})
    env = load_workflow(root / ".github/workflows/ci.yml")[0]
    assert env.marker_environment["implementation_name"] == "cpython"


def test_dynamic_python_does_not_invent_cpython(project_factory):
    root = project_factory("[project]\nname='x'\nversion='1'", {"ci.yml": "jobs:\n  t:\n    runs-on: ubuntu-latest\n    strategy:\n      matrix:\n        python: ['${{ value }}']\n"})
    env = load_workflow(root / ".github/workflows/ci.yml")[0]
    assert "implementation_name" not in env.marker_environment


def test_pypy_selector_does_not_invent_cpython(project_factory):
    root = project_factory("[project]\nname='x'\nversion='1'", {"ci.yml": "jobs:\n  t:\n    runs-on: ubuntu-latest\n    strategy:\n      matrix:\n        python: ['pypy3.10']\n"})
    env = load_workflow(root / ".github/workflows/ci.yml")[0]
    assert "implementation_name" not in env.marker_environment


def test_literal_runs_on_without_os_axis(project_factory):
    root = project_factory("[project]\nname='x'\nversion='1'", {"ci.yml": "jobs:\n  t:\n    runs-on: windows-latest\n    strategy:\n      matrix:\n        python: ['3.11']\n"})
    env = load_workflow(root / ".github/workflows/ci.yml")[0]
    assert env.marker_environment["sys_platform"] == "win32"


def test_os_axis_is_static_even_when_runs_on_references_it(project_factory):
    root = project_factory("[project]\nname='x'\nversion='1'", {"ci.yml": "jobs:\n  t:\n    runs-on: ${{ matrix.os }}\n    strategy:\n      matrix:\n        os: [windows-latest]\n        python: ['3.11']\n"})
    env = load_workflow(root / ".github/workflows/ci.yml")[0]
    assert env.marker_environment["sys_platform"] == "win32"


def test_literal_runs_on_wins_over_different_os_axis(project_factory):
    root = project_factory("[project]\nname='x'\nversion='1'", {"ci.yml": "jobs:\n  t:\n    runs-on: ubuntu-latest\n    strategy:\n      matrix:\n        os: [windows-latest]\n        python: ['3.11']\n"})
    env = load_workflow(root / ".github/workflows/ci.yml")[0]
    assert env.marker_environment["platform_system"] == "Linux"


def test_runs_on_reference_uses_only_referenced_axis(project_factory):
    root = project_factory("[project]\nname='x'\nversion='1'", {"ci.yml": "jobs:\n  t:\n    runs-on: ${{ matrix.runner }}\n    strategy:\n      matrix:\n        os: [windows-latest]\n        runner: [macos-14]\n        python: ['3.11']\n"})
    env = load_workflow(root / ".github/workflows/ci.yml")[0]
    assert env.marker_environment["platform_system"] == "Darwin"


def test_nontrivial_runs_on_expression_is_unknown(project_factory):
    root = project_factory("[project]\nname='x'\nversion='1'", {"ci.yml": "jobs:\n  t:\n    runs-on: ${{ matrix.os || 'ubuntu-latest' }}\n    strategy:\n      matrix:\n        os: [windows-latest]\n        python: ['3.11']\n"})
    env = load_workflow(root / ".github/workflows/ci.yml")[0]
    assert "sys_platform" not in env.marker_environment
    assert any("unevaluated expression" in reason for reason in env.unknown_reasons)


def test_self_hosted_runs_on_list_is_unknown(project_factory):
    root = project_factory("[project]\nname='x'\nversion='1'", {"ci.yml": "jobs:\n  t:\n    runs-on: [self-hosted, linux]\n    strategy:\n      matrix:\n        python: ['3.11']\n"})
    env = load_workflow(root / ".github/workflows/ci.yml")[0]
    assert "sys_platform" not in env.marker_environment
    assert any("not a literal string" in reason for reason in env.unknown_reasons)


def test_unknown_runner_reason(project_factory):
    root = project_factory("[project]\nname='x'\nversion='1'", {"ci.yml": "jobs:\n  t:\n    runs-on: custom\n"})
    env = load_workflow(root / ".github/workflows/ci.yml")[0]
    assert any("not recognized" in reason for reason in env.unknown_reasons)


@pytest.mark.parametrize("label", ["windows-custom", "ubuntu-private", "macos-team"])
def test_custom_prefix_runner_is_not_guessed(project_factory, label):
    root = project_factory("[project]\nname='x'\nversion='1'", {"ci.yml": f"jobs:\n  t:\n    runs-on: {label}\n"})
    env = load_workflow(root / ".github/workflows/ci.yml")[0]
    assert "platform_system" not in env.marker_environment
    assert any("not recognized" in reason for reason in env.unknown_reasons)


def test_safe_yaml_rejects_python_object(project_factory):
    root = project_factory("[project]\nname='x'\nversion='1'", {"ci.yml": "!!python/object/apply:builtins.str [unsafe]"})
    with pytest.raises(InputError, match="cannot read"):
        load_workflow(root / ".github/workflows/ci.yml")


def test_actions_on_job_identifier_stays_string(project_factory):
    root = project_factory("[project]\nname='x'\nversion='1'", {"ci.yml": "jobs:\n  on:\n    runs-on: ubuntu-latest\n  other:\n    runs-on: windows-latest\n"})
    environments = load_workflow(root / ".github/workflows/ci.yml")
    assert [item.identifier for item in environments] == ["ci.yml:on[0]", "ci.yml:other[0]"]


def test_non_string_job_identifier_is_input_error(project_factory):
    root = project_factory("[project]\nname='x'\nversion='1'", {"ci.yml": "jobs:\n  12:\n    runs-on: ubuntu-latest\n"})
    with pytest.raises(InputError, match="job identifiers must be strings"):
        load_workflow(root / ".github/workflows/ci.yml")


def test_jobs_must_be_mapping(project_factory):
    root = project_factory("[project]\nname='x'\nversion='1'", {"ci.yml": "jobs: []\n"})
    with pytest.raises(InputError, match="jobs must be a mapping"):
        load_workflow(root / ".github/workflows/ci.yml")


def test_discovery_orders_extensions(project_factory):
    root = project_factory("[project]\nname='x'\nversion='1'", {"z.yaml": "jobs: {}", "a.yml": "jobs: {}"})
    assert [path.name for path in discover_workflows(root)] == ["a.yml", "z.yaml"]
