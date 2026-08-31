# Changelog

All notable changes are documented here. This project follows semantic
versioning once stable releases begin.

## 0.1.1 - 2026-08-31

This release exists to correct licensing metadata. There is no change to
program behavior, and no source module was modified.

- The `LICENSE` file shipped in 0.1.0 carried the "Apache License, Version 2.0"
  heading but was not the Apache-2.0 text: three clauses in Section 1
  (Definitions) had been reworded and the APPENDIX section was missing. The
  0.1.0 archives on PyPI-style distribution channels and on the GitHub release
  therefore embed license text that is inconsistent with the declared
  Apache-2.0 metadata. **0.1.1 supersedes 0.1.0; do not use the 0.1.0
  archives.**
- Replace `LICENSE` with the complete, unmodified Apache-2.0 text, and move the
  copyright statement into a separate `NOTICE` file so `LICENSE` stays
  byte-identical to the canonical text.
- Declare the license with PEP 639 (`license = "Apache-2.0"` plus
  `license-files`), so both `LICENSE` and `NOTICE` ship inside the wheel and
  sdist, and drop the now-redundant license classifier.
- Make `scripts/generate_manifest.py` ordering platform independent; it sorted
  `pathlib.Path` objects, which compare case insensitively on Windows and case
  sensitively on POSIX, so the "deterministic" manifest was only reproducible
  per platform.
- CI now verifies, on all nine matrix jobs, that regenerating the manifest is a
  no-op and that the wheel and sdist still build.

## 0.1.0 - 2026-08-31

- Add offline parsing of marker-bearing project and optional dependencies.
- Add literal GitHub Actions matrix expansion with include and exclude support.
- Add conservative marker evaluation and deterministic text and JSON reports.
- Add documented exit codes, boundary checking, manifest generation, and SBOM.
