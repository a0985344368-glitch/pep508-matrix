# Verification record

Verified at `2026-08-31T10:04:45Z` (UTC) with Python `3.12.13` in the
project-local `.venv`.

## Environment

```console
$ .venv/bin/python -m pip show packaging PyYAML pytest build hatchling editables
packaging 26.3
PyYAML 6.0.3
pytest 9.1.1
build 1.6.0
hatchling 1.32.0
editables 0.6
```

## Tests and static checks

```console
$ .venv/bin/pytest -q
........................................................................ [ 96%]
...                                                                      [100%]
75 passed in 0.13s

$ .venv/bin/python -m compileall -q src tests scripts
# exit 0, no output

$ .venv/bin/python scripts/verify_boundary.py
boundary scan passed
```

The tests cover project parsing, optional dependency groups, malformed input,
safe YAML behavior and Actions-style keys, bounded Cartesian expansion,
include/exclude behavior, include-only and duplicate includes, OS and Python
aliases, conservative runner precedence, version normalization, patch-version
unknowns, dynamic/unknown values, all four statuses, deterministic JSON, CLI
exit codes, cross-file ordering, the no-marker case, a clean negative control,
and a deliberately one-sided mutation.

## Package build and inspection

```console
$ .venv/bin/python -m build --no-isolation
Successfully built pep508_matrix-0.1.0.tar.gz and pep508_matrix-0.1.0-py3-none-any.whl

$ sha256sum dist/*
b0dd7cf275e4423b159a092684e2edef7cdc5ea76a8f6131df93c3ccdd9775ae  dist/pep508_matrix-0.1.0-py3-none-any.whl
a229e318ccb1cc871e1fda8e3e87a00e54b2eac18aefe8524e3d524cd016537b  dist/pep508_matrix-0.1.0.tar.gz

$ tar -tzf dist/pep508_matrix-0.1.0.tar.gz
# exit 0; expected source, tests, public documents, examples, scripts, and SBOM listed

$ .venv/bin/python -m zipfile -l dist/pep508_matrix-0.1.0-py3-none-any.whl
# exit 0; nine package modules plus metadata, entry point, license, and RECORD listed

$ .venv/bin/python -m pip install --force-reinstall --no-deps dist/pep508_matrix-0.1.0-py3-none-any.whl
Successfully installed pep508-matrix-0.1.0

$ .venv/bin/pep508-matrix check . --format json
# exit 0; nine statically enumerated environments and zero observations

$ .venv/bin/python -c 'import pep508_matrix; print(pep508_matrix.__version__)'
0.1.0
```

Both archives were inspected by listing their contents; no unexpected paths
were present. The wheel was installed locally without dependency resolution and
its installed command and import were exercised.

The first no-isolation build attempt failed because the build backend was not
installed in the development environment. `hatchling>=1.26` was added to the
development extra and installed; `editables>=0.5` was also added so editable
no-isolation installs are reproducible. The exact build command above was then
rerun successfully.

## Known limitations

- Static literal matrices and literal scalar axis values only.
- No general expression evaluation or reusable workflow expansion.
- No container image introspection or architecture inference.
- No interpretation of self-hosted runner label arrays.
- No support-policy judgment; results are observations and advisories.
- Python versions must be quoted YAML strings.
