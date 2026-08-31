# Verification record

Verified at `2026-08-31T10:06:27Z` (UTC) with Python `3.12.13` in the
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
75 passed in 0.14s

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
99abd4e24f7501f8c9115c60a6b79b1fea902288e37427efff3c975d3c1294aa  dist/pep508_matrix-0.1.0-py3-none-any.whl
0b0486cb8bfec4061e8df3688d4860fefefe3b3387b4e7b5fbb57ba1326eb92a  dist/pep508_matrix-0.1.0.tar.gz

$ tar -tzf dist/pep508_matrix-0.1.0.tar.gz
# exit 0; expected source, tests, public documents, examples, scripts, and SBOM listed

$ .venv/bin/python -m zipfile -l dist/pep508_matrix-0.1.0-py3-none-any.whl
# exit 0; nine package modules plus metadata, entry point, license, and RECORD listed

$ .venv/bin/python -m pip download --only-binary=:all: --dest build/wheelhouse packaging==26.3 PyYAML==6.0.3
Successfully downloaded packaging PyYAML

$ python3 -m venv --clear build/wheel-venv
# exit 0, no output

$ build/wheel-venv/bin/python -m pip install --no-index --find-links build/wheelhouse dist/pep508_matrix-0.1.0-py3-none-any.whl
Successfully installed packaging-26.3 pep508-matrix-0.1.0 pyyaml-6.0.3

$ build/wheel-venv/bin/python -c 'import pep508_matrix; print(pep508_matrix.__version__)'
0.1.0

$ build/wheel-venv/bin/pep508-matrix check . --format json
# exit 0; nine statically enumerated environments and zero observations

$ build/wheel-venv/bin/pep508-matrix check examples --format text
# exit 1 as expected; two markers have both outcomes and one CPython marker is true-only
```

Both archives were inspected by listing their contents; no unexpected paths
were present. The wheel and both runtime dependencies were installed offline
into a fresh explicit virtual environment. Its import and command were exercised
against both the project and the synthetic example.

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
- Environment IDs use workflow basenames, so explicit workflow overrides with
  duplicate basenames can produce duplicate display IDs.
- Duplicate YAML mapping keys follow the loader's last-value behavior.
- The hosted-runner label allowlist is deliberately conservative and may need
  updates as new official labels are introduced.
