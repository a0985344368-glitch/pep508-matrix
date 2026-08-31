#!/usr/bin/env python3
"""Write a deterministic SHA-256 manifest for tracked project files."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "MANIFEST.sha256"
SKIP_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", "build", "dist"}


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    paths = [ROOT / item.decode("utf-8") for item in result.stdout.split(b"\0") if item]
    return sorted(
        (
            path
            for path in paths
            if path != MANIFEST
            and path.is_file()
            and not any(part in SKIP_PARTS or part.endswith(".egg-info") for part in path.parts)
        ),
        # Sort on the POSIX relative path rather than the Path objects. Path
        # ordering is platform dependent: PureWindowsPath compares case
        # insensitively while PurePosixPath does not, so the same tree produced
        # a different line order on Windows than on Linux.
        key=lambda path: path.relative_to(ROOT).as_posix(),
    )


def main() -> int:
    lines = [
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(ROOT).as_posix()}"
        for path in tracked_files()
    ]
    MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {MANIFEST.name} with {len(lines)} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
