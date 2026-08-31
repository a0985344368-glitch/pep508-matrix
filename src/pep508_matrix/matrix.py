"""Safely load and statically enumerate supported GitHub Actions matrices."""

from __future__ import annotations

import itertools
import re
from pathlib import Path
from typing import Any

import yaml

from .errors import InputError
from .models import Environment

PYTHON_AXES = ("python-version", "python_version", "python")
OS_AXES = ("os", "runner", "runs-on")
MAX_MATRIX_JOBS = 256


class ActionsSafeLoader(yaml.SafeLoader):
    """Safe loader with YAML 1.2 boolean spelling for Actions-like files."""


ActionsSafeLoader.yaml_implicit_resolvers = {
    key: list(resolvers) for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
for resolver_key, resolvers in tuple(ActionsSafeLoader.yaml_implicit_resolvers.items()):
    ActionsSafeLoader.yaml_implicit_resolvers[resolver_key] = [
        resolver for resolver in resolvers if resolver[0] != "tag:yaml.org,2002:bool"
    ]
ActionsSafeLoader.add_implicit_resolver(
    "tag:yaml.org,2002:bool",
    re.compile(r"^(?:true|false)$", re.IGNORECASE),
    list("tTfF"),
)


def discover_workflows(root: Path) -> tuple[Path, ...]:
    directory = root / ".github" / "workflows"
    if not directory.is_dir():
        return ()
    return tuple(sorted((*directory.glob("*.yml"), *directory.glob("*.yaml"))))


def _dynamic(value: Any) -> bool:
    return isinstance(value, str) and "${{" in value


def _literal_scalar(value: Any) -> bool:
    return isinstance(value, (str, int, float, bool)) and not _dynamic(value)


def _matches(candidate: dict[str, Any], pattern: dict[str, Any]) -> bool:
    return all(candidate.get(key) == value for key, value in pattern.items())


def expand_matrix(matrix: Any) -> tuple[list[dict[str, Any]], tuple[str, ...]]:
    """Expand literal axes with GitHub-like include/exclude behavior."""
    if matrix is None:
        return [{}], ()
    if not isinstance(matrix, dict):
        return [{}], ("strategy.matrix is not a literal mapping",)
    axes: dict[str, list[Any]] = {}
    reasons: list[str] = []
    for key, value in matrix.items():
        if key in {"include", "exclude"}:
            continue
        if not isinstance(key, str) or not isinstance(value, list) or not value:
            reasons.append(f"matrix axis {key!r} is not a non-empty literal list")
            continue
        if any(not _literal_scalar(item) for item in value):
            reasons.append(f"matrix axis {key!r} contains a dynamic or non-scalar value")
            continue
        axes[key] = value
    if reasons:
        return [{}], tuple(sorted(set(reasons)))

    size = 1
    for values in axes.values():
        size *= len(values)
        if size > MAX_MATRIX_JOBS:
            return [{}], (f"matrix exceeds the static {MAX_MATRIX_JOBS}-job limit",)
    keys = sorted(axes)
    combinations = [dict(zip(keys, values, strict=True)) for values in itertools.product(*(axes[k] for k in keys))] if keys else [{}]
    exclude = matrix.get("exclude", [])
    if not isinstance(exclude, list) or any(not isinstance(item, dict) for item in exclude):
        return [{}], ("matrix.exclude is not a literal list of mappings",)
    for pattern in exclude:
        if any(not isinstance(k, str) or not _literal_scalar(v) for k, v in pattern.items()):
            return [{}], ("matrix.exclude contains a dynamic or non-scalar value",)
        combinations = [combo for combo in combinations if not _matches(combo, pattern)]

    include = matrix.get("include", [])
    if not isinstance(include, list) or any(not isinstance(item, dict) for item in include):
        return [{}], ("matrix.include is not a literal list of mappings",)
    if any(
        not isinstance(key, str) or not _literal_scalar(value)
        for addition in include
        for key, value in addition.items()
    ):
        return [{}], ("matrix.include contains a dynamic or non-scalar value",)
    original_axes = set(axes)
    if not original_axes and include:
        if len(include) > MAX_MATRIX_JOBS:
            return [{}], (f"matrix include exceeds the static {MAX_MATRIX_JOBS}-job limit",)
        return [dict(item) for item in include], ()
    base_combinations = [dict(combo) for combo in combinations]
    for addition in include:
        compatible_indices = [
            index
            for index, combo in enumerate(base_combinations)
            if all(key not in original_axes or combo.get(key) == value for key, value in addition.items())
        ]
        if compatible_indices:
            for index in compatible_indices:
                combinations[index].update(addition)
        else:
            if len(combinations) >= MAX_MATRIX_JOBS:
                return [{}], (f"matrix include exceeds the static {MAX_MATRIX_JOBS}-job limit",)
            combinations.append(dict(addition))
    return combinations, ()


def _first(combo: dict[str, Any], names: tuple[str, ...]) -> Any:
    for name in names:
        if name in combo:
            return combo[name]
    return None


def _python_environment(value: Any) -> tuple[dict[str, str], list[str]]:
    environment: dict[str, str] = {}
    reasons: list[str] = []
    if value is None:
        reasons.append("Python version is not statically known")
        return environment, reasons
    if not isinstance(value, str):
        reasons.append("Python version must be a quoted literal string")
        return environment, reasons
    text = value
    parts = text.split(".")
    if len(parts) not in {2, 3} or not all(part.isdigit() for part in parts):
        reasons.append(f"Python version {text!r} is not a literal numeric version")
        return environment, reasons
    environment.update(
        python_version=".".join(parts[:2]),
        implementation_name="cpython",
        platform_python_implementation="CPython",
    )
    if len(parts) >= 3:
        environment.update(python_full_version=text, implementation_version=text)
    else:
        reasons.append("Python patch version is not statically known")
    return environment, reasons


def _os_environment(value: Any) -> tuple[dict[str, str], list[str]]:
    if value is None:
        return {}, ["runner OS is not statically known"]
    if not isinstance(value, str):
        return {}, ["runs-on is not a literal string label"]
    text = value.lower()
    if re.fullmatch(r"ubuntu-(?:latest|[0-9]{2}\.[0-9]{2})(?:-arm)?", text):
        return {"platform_system": "Linux", "sys_platform": "linux", "os_name": "posix"}, []
    if re.fullmatch(r"windows-(?:latest|[0-9]{4}|[0-9]{2}-arm)", text):
        return {"platform_system": "Windows", "sys_platform": "win32", "os_name": "nt"}, []
    if re.fullmatch(r"macos-(?:latest|[0-9]{2})(?:-(?:large|xlarge|arm64|intel))?", text):
        return {"platform_system": "Darwin", "sys_platform": "darwin", "os_name": "posix"}, []
    return {}, [f"runner OS label {value!r} is not recognized"]


_MATRIX_REFERENCE = re.compile(
    r"^\s*\$\{\{\s*matrix\.([A-Za-z_][A-Za-z0-9_-]*)\s*\}\}\s*$"
)


def _resolve_os_value(runs_on: Any, combo: dict[str, Any]) -> tuple[Any, list[str]]:
    """Resolve only a literal runner or one exact matrix-axis reference."""
    if isinstance(runs_on, str):
        reference = _MATRIX_REFERENCE.fullmatch(runs_on)
        if reference:
            axis = reference.group(1)
            value = combo.get(axis)
            if value is None:
                return None, [f"runs-on references unknown matrix axis {axis!r}"]
            return value, []
        if _dynamic(runs_on):
            return None, ["runs-on contains an unevaluated expression"]
        return runs_on, []
    if runs_on is None:
        return None, ["runs-on is not specified"]
    return runs_on, []


def load_workflow(path: Path) -> tuple[Environment, ...]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            document = yaml.load(handle, Loader=ActionsSafeLoader)
    except FileNotFoundError as exc:
        raise InputError(f"workflow not found: {path}") from exc
    except (OSError, yaml.YAMLError) as exc:
        raise InputError(f"cannot read workflow {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise InputError(f"workflow root must be a mapping: {path}")
    jobs = document.get("jobs", {})
    if not isinstance(jobs, dict):
        raise InputError(f"workflow jobs must be a mapping: {path}")
    if any(not isinstance(key, str) for key in jobs):
        raise InputError(f"workflow job identifiers must be strings: {path}")

    environments: list[Environment] = []
    for job_name in sorted(jobs):
        job = jobs[job_name]
        if not isinstance(job, dict):
            raise InputError(f"job {job_name!r} must be a mapping: {path}")
        strategy = job.get("strategy", {})
        if not isinstance(strategy, dict):
            environments.append(Environment(f"{path.name}:{job_name}[0]", {}, ("job strategy is not a literal mapping",)))
            continue
        combinations, matrix_reasons = expand_matrix(strategy.get("matrix"))
        runs_on = job.get("runs-on")
        for index, combo in enumerate(combinations):
            python_data, python_reasons = _python_environment(_first(combo, PYTHON_AXES))
            os_value, resolution_reasons = _resolve_os_value(runs_on, combo)
            os_data, os_reasons = _os_environment(os_value)
            reasons = [*matrix_reasons, *python_reasons, *resolution_reasons, *os_reasons]
            marker_environment = {**python_data, **os_data}
            environments.append(
                Environment(
                    f"{path.name}:{job_name}[{index}]",
                    marker_environment,
                    tuple(sorted(set(reasons))),
                )
            )
    return tuple(environments)


def load_workflows(paths: tuple[Path, ...]) -> tuple[Environment, ...]:
    result: list[Environment] = []
    for path in sorted(paths, key=lambda item: str(item)):
        result.extend(load_workflow(path))
    return tuple(result)
