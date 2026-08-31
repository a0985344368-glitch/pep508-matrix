# Contributing

Contributions are welcome through a standard fork-and-review workflow.

1. Use Python 3.11 or newer and create an isolated virtual environment.
2. Install development dependencies with `python -m pip install -e '.[dev]'`.
3. Add focused, synthetic tests for behavior changes.
4. Run `pytest`, `python -m compileall -q src tests scripts`, and
   `python scripts/verify_boundary.py`.
5. Keep output deterministic and describe behavior changes in `CHANGELOG.md`.

Please avoid fixtures copied from private repositories or user projects. Do not
add network access or workflow execution to the `check` command. Reports should
remain neutral observations, not claims about a project's intended support.
