"""Typed public data models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Status(StrEnum):
    """Stable marker observation status values."""

    BOTH_OUTCOMES = "BOTH_OUTCOMES"
    TRUE_ONLY = "TRUE_ONLY"
    FALSE_ONLY = "FALSE_ONLY"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class Dependency:
    source_group: str
    requirement: str
    marker: str


@dataclass(frozen=True, slots=True)
class Environment:
    """One statically enumerated CI environment."""

    identifier: str
    marker_environment: dict[str, str]
    unknown_reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MarkerObservation:
    source_group: str
    requirement: str
    marker: str
    status: Status
    matching_environment_ids: tuple[str, ...]
    nonmatching_environment_ids: tuple[str, ...]
    unknown_reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AnalysisReport:
    observations: tuple[MarkerObservation, ...]
    environments: tuple[Environment, ...]
