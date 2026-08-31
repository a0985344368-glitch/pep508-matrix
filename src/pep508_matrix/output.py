"""Deterministic report renderers."""

from __future__ import annotations

import json

from .models import AnalysisReport


def as_dict(report: AnalysisReport) -> dict[str, object]:
    return {
        "environments": [
            {
                "id": env.identifier,
                "marker_environment": dict(sorted(env.marker_environment.items())),
                "unknown_reasons": list(env.unknown_reasons),
            }
            for env in report.environments
        ],
        "observations": [
            {
                "marker": item.marker,
                "matching_environment_ids": list(item.matching_environment_ids),
                "nonmatching_environment_ids": list(item.nonmatching_environment_ids),
                "requirement": item.requirement,
                "source_group": item.source_group,
                "status": item.status.value,
                "unknown_reasons": list(item.unknown_reasons),
            }
            for item in report.observations
        ],
    }


def render_json(report: AnalysisReport) -> str:
    return json.dumps(as_dict(report), indent=2, sort_keys=True) + "\n"


def render_text(report: AnalysisReport) -> str:
    if not report.observations:
        return "No PEP 508 environment markers found.\n"
    lines: list[str] = []
    for item in report.observations:
        lines.extend(
            [
                f"{item.status.value}  {item.requirement}",
                f"  source: {item.source_group}",
                f"  marker: {item.marker}",
                f"  true: {', '.join(item.matching_environment_ids) or '-'}",
                f"  false: {', '.join(item.nonmatching_environment_ids) or '-'}",
            ]
        )
        for reason in item.unknown_reasons:
            lines.append(f"  unknown: {reason}")
    return "\n".join(lines) + "\n"
