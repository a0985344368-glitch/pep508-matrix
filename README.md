# pep508-matrix

`pep508-matrix` is an offline, static Python CLI that observes how PEP 508
environment markers behave across statically enumerable GitHub Actions job
matrices. For each marker it reports `BOTH_OUTCOMES`, `TRUE_ONLY`,
`FALSE_ONLY`, or `UNKNOWN`.

These results are observations and advisories. A one-sided marker is not proof
of a bug, and this tool makes no judgment about which platforms a project
should support.

## Quickstart

Python 3.11 or newer is required.

```console
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
pep508-matrix check .
pep508-matrix check . --format json
pep508-matrix check . --strict-unknown
```

By default, `check` reads `ROOT/pyproject.toml` plus every `.yml` and `.yaml`
file directly under `ROOT/.github/workflows`. Override discovery with one or
more paths (relative paths are resolved from `ROOT`):

```console
pep508-matrix check . --workflow examples/.github/workflows/ci.yml
```

The fully synthetic example contains an OS and Python matrix. Given a
dependency such as:

```toml
dependencies = [
  "colorama>=0.4; sys_platform == 'win32'",
  "importlib-metadata; python_version < '3.12'",
]
```

its three operating systems and three Python versions observe both outcomes
for both markers. Removing the Windows row makes the first marker
`FALSE_ONLY`; replacing the Python versions with only `3.11` makes the second
marker `TRUE_ONLY`.

## Interpretation and exit codes

| Status | Meaning |
|---|---|
| `BOTH_OUTCOMES` | At least one enumerated environment evaluates true and at least one evaluates false. |
| `TRUE_ONLY` | Every evaluable environment is true. |
| `FALSE_ONLY` | Every evaluable environment is false. |
| `UNKNOWN` | Static information is insufficient to determine a one- or two-sided result. |

Exit code `0` means there are no one-sided observations. `UNKNOWN` is a warning
unless `--strict-unknown` is used. Exit code `1` means a `TRUE_ONLY` or
`FALSE_ONLY` observation exists, or strict mode found `UNKNOWN`. Exit code `2`
means CLI usage or input is invalid. A project with no marker-bearing
dependencies exits `0`.

## Scope and limitations

The analyzer only handles literal matrices and literal scalar axis values.
Python versions must be quoted YAML strings (for example, `"3.11"`); YAML
numbers and booleans are conservatively unknown. A two-part selector provides
`python_version`, but patch-level markers such as `python_full_version` and
`implementation_version` remain unknown unless the matrix supplies a literal
three-part version. It
does not evaluate expressions, expand reusable workflows, inspect container
images, infer architecture, execute workflows, contact a network service, or
make support-policy judgments. A recognized literal OS matrix axis can be used
when `runs-on` references that axis, but the expression itself is not evaluated.
Self-hosted label arrays and unrecognized runner labels remain unknown.

YAML is parsed with a `SafeLoader`-derived loader that preserves GitHub Actions
keys under YAML 1.2 boolean rules. `check` starts no subprocesses, uses no
network, and writes no files.

## Development

```console
python -m pip install -e '.[dev]'
pytest
python scripts/verify_boundary.py
python -m build
```

See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and
[SOURCES.md](SOURCES.md).
