#!/usr/bin/env python3
"""Scan repository text for generic secret/PII indicators.

Additional exact deny terms may be supplied at runtime, one per line, through
PEP508_MATRIX_DENY_TERMS. Terms are neither persisted nor printed.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()
SKIP_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
}
PATTERNS = {
    "cloud-access-key": re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    "email-address": re.compile(rb"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "private-key-header": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "secret-assignment": re.compile(
        rb"(?i)\b(?:api[_-]?key|password|secret|token)\s*[:=]\s*['\"][^'\"\s]{8,}['\"]"
    ),
}


def candidates() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and path.resolve() != SELF
        and not any(part in SKIP_PARTS or part.endswith(".egg-info") for part in path.parts)
        and path.name != "MANIFEST.sha256"
    )


def main() -> int:
    runtime_terms = tuple(
        item.encode("utf-8")
        for item in os.environ.get("PEP508_MATRIX_DENY_TERMS", "").splitlines()
        if item
    )
    findings: set[tuple[str, str]] = set()
    for path in candidates():
        try:
            content = path.read_bytes()
        except OSError:
            findings.add((path.relative_to(ROOT).as_posix(), "unreadable-file"))
            continue
        for category, pattern in PATTERNS.items():
            if pattern.search(content):
                findings.add((path.relative_to(ROOT).as_posix(), category))
        if any(term in content for term in runtime_terms):
            findings.add((path.relative_to(ROOT).as_posix(), "runtime-deny-term"))
    for relative, category in sorted(findings):
        print(f"{relative}: {category}")
    if findings:
        return 1
    print("boundary scan passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
