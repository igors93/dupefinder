# dupefinder

**dupefinder** is a small Python library for finding duplicate files using hashes.

It is designed to be:

- **Simple**: one obvious function for normal use.
- **Safe by default**: it only reads files; it never deletes or modifies anything.
- **Zero dependency**: it uses only the Python standard library.
- **Modular**: each part of the logic has a clear file and responsibility.
- **Memory-friendly**: files are hashed in chunks instead of being loaded fully into RAM.

## Install

For local development:

```bash
python -m pip install -e .
```

After publishing to PyPI, the goal is:

```bash
pip install dupefinder
```

## Quick use as a library

```python
from dupefinder import find_duplicates

groups = find_duplicates("./Downloads")

for group in groups:
    print(f"Duplicate group: {group.count} files, {group.size} bytes each")
    for file_path in group.files:
        print(" -", file_path)
```

## Advanced use

```python
from dupefinder import scan
from dupefinder.models import ScanOptions

report = scan(
    "./Downloads",
    options=ScanOptions(
        min_size=1024,
        algorithm="sha256",
        ignore_hidden=True,
        follow_symlinks=False,
    ),
)

print(report.total_groups)
print(report.total_wasted_space)
```

## Use from terminal

```bash
dupefinder ./Downloads
```

Show JSON:

```bash
dupefinder ./Downloads --json
```

Ignore tiny files:

```bash
dupefinder ./Downloads --min-size 1MB
```

## Safety philosophy

This library is intentionally read-only.

It does **not**:

- delete files;
- move files;
- rename files;
- send data to the internet;
- follow symbolic links by default.

If you later add deletion features, keep them outside the default flow and require explicit user confirmation.

## Project structure

```text
src/dupefinder/
├── api.py       # public functions for users
├── cli.py       # terminal command
├── scanner.py   # finds files safely
├── hashing.py   # calculates file hashes
├── grouping.py  # groups equal files
├── filters.py   # ignore/include rules
├── models.py    # data classes
├── report.py    # text/JSON output
├── safety.py    # validation and safe defaults
├── constants.py # default values
└── errors.py    # custom exceptions
```

## Run tests

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

On Windows PowerShell:

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests
```

## License

MIT.
