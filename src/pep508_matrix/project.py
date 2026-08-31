"""Read marker-bearing dependencies from pyproject.toml."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from packaging.requirements import InvalidRequirement, Requirement

from .errors import InputError
from .models import Dependency


def _require_string_list(value: Any, location: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise InputError(f"{location} must be a list of requirement strings")
    return value


def _parse_group(value: Any, group: str) -> list[Dependency]:
    dependencies: list[Dependency] = []
    for raw in _require_string_list(value, group):
        try:
            requirement = Requirement(raw)
        except InvalidRequirement as exc:
            raise InputError(f"invalid requirement in {group}: {raw!r}: {exc}") from exc
        if requirement.marker is not None:
            dependencies.append(Dependency(group, raw, str(requirement.marker)))
    return dependencies


def load_dependencies(path: Path) -> tuple[Dependency, ...]:
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except FileNotFoundError as exc:
        raise InputError(f"pyproject.toml not found: {path}") from exc
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise InputError(f"cannot read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise InputError("pyproject.toml root must be a table")
    project = data.get("project", {})
    if not isinstance(project, dict):
        raise InputError("[project] must be a table")

    result: list[Dependency] = []
    if "dependencies" in project:
        result.extend(_parse_group(project["dependencies"], "project.dependencies"))
    optional = project.get("optional-dependencies", {})
    if not isinstance(optional, dict):
        raise InputError("[project.optional-dependencies] must be a table")
    for name in sorted(optional):
        result.extend(
            _parse_group(optional[name], f"project.optional-dependencies.{name}")
        )
    return tuple(sorted(result, key=lambda dep: (dep.source_group, dep.requirement)))
