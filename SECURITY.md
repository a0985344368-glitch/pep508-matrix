# Security policy

## Reporting

Please report a suspected vulnerability privately to the repository
maintainers through the hosting platform's security-reporting feature. Do not
include credentials, personal data, or exploit output in a public issue.

## Security model

`pep508-matrix check` is designed for offline static analysis. It parses TOML
with the Python standard library and YAML with `yaml.safe_load`; it does not
execute workflow content, invoke subprocesses, access the network, or write
files. Treat all diagnostic output as potentially containing paths or strings
from the analyzed project.

Only the latest released version is intended to receive security fixes during
this early development phase.
