"""Command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .analyzer import analyze
from .errors import InputError
from .models import Status
from .output import render_json, render_text


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(2, f"pep508-matrix: error: {message}\n")


def build_parser() -> argparse.ArgumentParser:
    parser = Parser(prog="pep508-matrix", description="Observe PEP 508 markers across literal CI matrices")
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check", help="analyze a project")
    check.add_argument("root", nargs="?", default=".")
    check.add_argument("--workflow", action="append", default=[], metavar="PATH")
    check.add_argument("--format", choices=("text", "json"), default="text")
    check.add_argument("--strict-unknown", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    workflows = tuple(
        path if path.is_absolute() else root / path
        for raw in args.workflow
        for path in (Path(raw),)
    ) or None
    try:
        report = analyze(root, workflows)
    except InputError as exc:
        print(f"pep508-matrix: input error: {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(render_json(report) if args.format == "json" else render_text(report))
    failing = {Status.TRUE_ONLY, Status.FALSE_ONLY}
    if args.strict_unknown:
        failing.add(Status.UNKNOWN)
    return 1 if any(item.status in failing for item in report.observations) else 0
