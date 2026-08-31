"""Evaluate marker outcomes conservatively across enumerated environments."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from packaging.markers import Marker, Variable

from .matrix import discover_workflows, load_workflows
from .models import AnalysisReport, Dependency, Environment, MarkerObservation, Status
from .project import load_dependencies


def _variables(node: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(node, Variable):
        found.add(node.value)
    elif isinstance(node, (list, tuple)):
        for item in node:
            found.update(_variables(item))
    return found


def observe(dependency: Dependency, environments: tuple[Environment, ...]) -> MarkerObservation:
    marker = Marker(dependency.marker)
    required = _variables(marker._markers)  # packaging exposes no public marker-variable visitor
    matching: list[str] = []
    nonmatching: list[str] = []
    unknown: list[str] = []
    for environment in environments:
        missing = sorted(required - environment.marker_environment.keys())
        if missing:
            reasons = [f"{environment.identifier}: unknown marker variable {name}" for name in missing]
            reasons.extend(f"{environment.identifier}: {reason}" for reason in environment.unknown_reasons)
            unknown.extend(reasons)
            continue
        try:
            result = marker.evaluate(environment=dict(environment.marker_environment))
        except (KeyError, ValueError) as exc:
            unknown.append(f"{environment.identifier}: marker evaluation failed: {exc}")
            continue
        (matching if result else nonmatching).append(environment.identifier)

    if matching and nonmatching:
        status = Status.BOTH_OUTCOMES
    elif unknown:
        status = Status.UNKNOWN
    elif matching:
        status = Status.TRUE_ONLY
    elif nonmatching:
        status = Status.FALSE_ONLY
    else:
        status = Status.UNKNOWN
        unknown.append("no statically enumerable CI environments")
    return MarkerObservation(
        dependency.source_group,
        dependency.requirement,
        dependency.marker,
        status,
        tuple(matching),
        tuple(nonmatching),
        tuple(sorted(set(unknown))),
    )


def analyze(root: Path, workflow_paths: tuple[Path, ...] | None = None) -> AnalysisReport:
    dependencies = load_dependencies(root / "pyproject.toml")
    paths = discover_workflows(root) if workflow_paths is None else workflow_paths
    environments = load_workflows(paths)
    observations = tuple(observe(dependency, environments) for dependency in dependencies)
    return AnalysisReport(observations, environments)
