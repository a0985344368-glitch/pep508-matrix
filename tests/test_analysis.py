from pep508_matrix.analyzer import analyze, observe
from pep508_matrix.models import Dependency, Environment, Status


def env(identifier, **values):
    return Environment(identifier, values)


def dep(marker):
    return Dependency("project.dependencies", f"demo; {marker}", marker)


def test_both_outcomes_status():
    result = observe(dep("python_version < '3.12'"), (env("a", python_version="3.11"), env("b", python_version="3.12")))
    assert result.status is Status.BOTH_OUTCOMES


def test_true_only_status():
    result = observe(dep("python_version >= '3.11'"), (env("a", python_version="3.11"),))
    assert result.status is Status.TRUE_ONLY


def test_false_only_status():
    result = observe(dep("python_version < '3'"), (env("a", python_version="3.11"),))
    assert result.status is Status.FALSE_ONLY


def test_unknown_missing_variable():
    result = observe(dep("platform_machine == 'x86_64'"), (env("a", python_version="3.11"),))
    assert result.status is Status.UNKNOWN
    assert "platform_machine" in result.unknown_reasons[0]


def test_unknown_no_environments():
    result = observe(dep("python_version < '3.12'"), ())
    assert result.status is Status.UNKNOWN
    assert result.unknown_reasons == ("no statically enumerable CI environments",)


def test_both_outcomes_wins_despite_unrelated_unknown_environment():
    result = observe(dep("python_version < '3.12'"), (env("a", python_version="3.11"), env("b", python_version="3.12"), env("c")))
    assert result.status is Status.BOTH_OUTCOMES


def test_true_plus_unknown_is_unknown():
    result = observe(dep("python_version < '3.12'"), (env("a", python_version="3.11"), env("b")))
    assert result.status is Status.UNKNOWN


def test_patch_marker_unknown_for_two_part_selector(project_factory):
    project = '''[project]\nname="x"\nversion="1"\ndependencies=["demo; python_full_version < '3.12.5'"]\n'''
    workflow = "jobs:\n  t:\n    runs-on: ubuntu-latest\n    strategy:\n      matrix:\n        python: ['3.12']\n"
    root = project_factory(project, {"ci.yml": workflow})
    assert analyze(root).observations[0].status is Status.UNKNOWN


def test_matching_ids_are_recorded():
    result = observe(dep("os_name == 'nt'"), (env("win", os_name="nt"), env("linux", os_name="posix")))
    assert result.matching_environment_ids == ("win",)
    assert result.nonmatching_environment_ids == ("linux",)


def test_negative_control_clean_fixture(project_factory, broad_workflow):
    root = project_factory('''[project]\nname="x"\nversion="1"\ndependencies=["demo; sys_platform == 'win32'"]\n''', {"ci.yml": broad_workflow})
    assert analyze(root).observations[0].status is Status.BOTH_OUTCOMES


def test_mutation_removing_windows_is_flagged(project_factory):
    workflow = "jobs:\n  test:\n    runs-on: ubuntu-latest\n    strategy:\n      matrix:\n        python: ['3.11']\n"
    root = project_factory('''[project]\nname="x"\nversion="1"\ndependencies=["demo; sys_platform == 'win32'"]\n''', {"ci.yml": workflow})
    assert analyze(root).observations[0].status is Status.FALSE_ONLY


def test_cross_file_environment_order(project_factory):
    project = '''[project]\nname="x"\nversion="1"\ndependencies=["demo; python_version < '3.12'"]\n'''
    one = "jobs:\n  z:\n    runs-on: ubuntu-latest\n    strategy:\n      matrix:\n        python: ['3.12']\n"
    two = "jobs:\n  a:\n    runs-on: ubuntu-latest\n    strategy:\n      matrix:\n        python: ['3.11']\n"
    root = project_factory(project, {"z.yml": one, "a.yml": two})
    assert [item.identifier for item in analyze(root).environments] == ["a.yml:a[0]", "z.yml:z[0]"]
