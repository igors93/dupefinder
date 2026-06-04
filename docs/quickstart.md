# Quickstart

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

## Using as a library

### Find duplicates (simple)

```python
from dupefinder import find_duplicates

groups = find_duplicates("./Downloads")

for group in groups:
    print(f"{group.count} files — {group.size} bytes each")
    for path in group.files:
        print(f"  {path}")
```

`find_duplicates` returns a tuple of `DuplicateGroup` objects. Each group contains files with identical content.

### Full scan report

```python
from dupefinder import scan

report = scan("./Downloads")

print(f"Scanned:    {report.scanned_files} files")
print(f"Hashed:     {report.hashed_files} files")
print(f"Groups:     {report.total_groups}")
print(f"Wasted:     {report.total_wasted_space} bytes")
```

### Custom options

```python
from dupefinder import scan
from dupefinder.models import ScanOptions

options = ScanOptions(
    min_size=1024 * 1024,       # skip files < 1 MiB
    ignore_hidden=True,          # skip dotfiles/dotfolders (default)
    follow_symlinks=False,       # do not follow symlinks (default)
    ignored_extensions=frozenset({".tmp", ".log"}),
    on_error="skip",             # record errors, keep going (default)
)

report = scan("./Downloads", options=options)
```

### Text and JSON output

```python
from dupefinder import scan
from dupefinder.report import format_report, report_to_json

report = scan(".")

# Human-readable text
print(format_report(report))

# JSON
print(report_to_json(report))
```

### Handling errors

```python
from dupefinder import scan
from dupefinder.errors import InvalidPathError

try:
    report = scan("/path/that/does/not/exist")
except InvalidPathError as exc:
    print(f"Bad path: {exc}")

# Non-fatal issues are available on the report
for issue in report.issues:
    print(f"[{issue.phase}] {issue.path}: {issue.message}")
```

## Using the CLI

```bash
# Scan a directory
dupefinder ./Downloads

# JSON output
dupefinder ./Downloads --json

# Skip files smaller than 1 MB
dupefinder ./Downloads --min-size 1MB

# Only scan images
dupefinder ./Pictures --include-ext .jpg,.jpeg,.png

# Ignore temp files
dupefinder . --ignore-ext .tmp,.log

# Exit with code 2 if duplicates found (useful in scripts)
dupefinder . --fail-on-duplicates && echo "No duplicates"
```

## What dupefinder does NOT do

- It does **not** delete files.
- It does **not** move or rename files.
- It does **not** connect to the internet.

It only reads files to calculate hashes. Deciding what to do with duplicates is up to you.
