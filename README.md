# dupefinder

[![PyPI version](https://img.shields.io/pypi/v/dupefinder.svg)](https://pypi.org/project/dupefinder/)
[![Python versions](https://img.shields.io/pypi/pyversions/dupefinder.svg)](https://pypi.org/project/dupefinder/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://github.com/igors93/dupefinder/actions/workflows/ci.yml/badge.svg)](https://github.com/igors93/dupefinder/actions)

**dupefinder** is a small, zero-dependency Python library and CLI tool for finding duplicate files using content hashes.

## Features

- **Simple**: one function for common use, a full report for advanced use.
- **Safe by default**: read-only. Never deletes, moves, or modifies files.
- **Zero dependency**: uses only the Python standard library.
- **Modular**: each responsibility lives in its own module.
- **Memory-friendly**: files are hashed in configurable chunks, not loaded fully into RAM.
- **Fast**: groups by file size before hashing — only candidates are hashed.
- **Typed**: ships with inline type annotations.

## Installation

```bash
pip install dupefinder
```

For development:

```bash
git clone https://github.com/igors93/dupefinder.git
cd dupefinder
pip install -e ".[dev]"
```

## Quick start

### As a library

```python
from dupefinder import find_duplicates

groups = find_duplicates("./Downloads")

for group in groups:
    print(f"{group.count} duplicate files — {group.size} bytes each")
    for path in group.files:
        print(f"  {path}")
```

### Full report

```python
from dupefinder import scan
from dupefinder.models import ScanOptions
from dupefinder.report import format_report

report = scan(
    "./Downloads",
    options=ScanOptions(
        min_size=1024,          # ignore files smaller than 1 KB
        ignore_hidden=True,     # skip dotfiles and dotfolders
        follow_symlinks=False,  # safe default
    ),
)

print(format_report(report))
print(f"Wasted space: {report.total_wasted_space} bytes")
```

### JSON output

```python
from dupefinder import scan
from dupefinder.report import report_to_json

report = scan("./Downloads")
print(report_to_json(report))
```

### CLI

```bash
# Basic scan
dupefinder ./Downloads

# JSON output
dupefinder ./Downloads --json

# Ignore files smaller than 1 MB
dupefinder ./Downloads --min-size 1MB

# Only scan images
dupefinder ./Pictures --include-ext .jpg,.jpeg,.png,.webp

# Ignore temp and log files
dupefinder . --ignore-ext .tmp,.log

# Exit with code 2 if any duplicates are found (useful in scripts/CI)
dupefinder . --fail-on-duplicates

# Strict mode: raise errors instead of skipping inaccessible files
dupefinder . --strict

# Follow symbolic links (disabled by default)
dupefinder . --follow-symlinks
```

Run `dupefinder --help` to see all options.

## CLI reference

| Flag | Description |
|---|---|
| `path` | File or directory to scan |
| `--algorithm` | Hash algorithm (default: `sha256`) |
| `--chunk-size` | Read chunk size, e.g. `1MB` (default: 1 MiB) |
| `--min-size` | Skip files smaller than this, e.g. `10KB` |
| `--max-size` | Skip files larger than this, e.g. `5GB` |
| `--include-ext` | Only scan these extensions, e.g. `.jpg,.png` |
| `--ignore-ext` | Skip these extensions, e.g. `.tmp,.log` |
| `--no-ignore-hidden` | Do not skip hidden dotfiles and dotfolders |
| `--follow-symlinks` | Follow symbolic links |
| `--strict` | Raise errors instead of skipping bad files |
| `--json` | Print JSON output |
| `--fail-on-duplicates` | Exit with code `2` when duplicates are found |
| `--version` | Show version and exit |

## API summary

| Symbol | Description |
|---|---|
| `find_duplicates(path, options)` | Return a tuple of `DuplicateGroup` |
| `scan(path, options)` | Return a full `ScanReport` |
| `ScanOptions` | Frozen dataclass with all scan settings |
| `ScanReport` | Result of a scan — groups, counts, issues |
| `DuplicateGroup` | One group of files with identical content |
| `FileInfo` | Path and size of a single file |
| `ScanIssue` | A non-fatal error recorded during a scan |

See [docs/api.md](docs/api.md) for the full reference.

## Project structure

```text
src/dupefinder/
├── api.py        public functions: scan, find_duplicates
├── cli.py        terminal command
├── scanner.py    file discovery (os.scandir, loop detection)
├── hashing.py    chunked file hashing
├── grouping.py   group by size then by hash
├── filters.py    ignore/include rules
├── models.py     frozen dataclasses
├── report.py     text and JSON output
├── safety.py     path/options validation, helpers
├── constants.py  default values
└── errors.py     custom exceptions
```

## Safety

`dupefinder` is intentionally read-only:

- Does **not** delete, move, or rename files.
- Does **not** connect to the internet.
- Does **not** follow symbolic links by default.
- Reads files in chunks — no large allocations.
- Permission errors are recorded and skipped by default.

See [SECURITY.md](SECURITY.md) for more details.

## Running tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=dupefinder --cov-report=term-missing
```

## Contributing

Contributions are welcome. Please open an issue first to discuss what you want to change.

1. Fork the repository.
2. Create a branch: `git checkout -b feature/your-feature`.
3. Make your changes and add tests.
4. Run `pytest` and make sure all tests pass.
5. Open a pull request.

## License

[MIT](LICENSE) — Igor Souza
