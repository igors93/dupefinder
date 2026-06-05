# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.3.x   | Yes       |
| < 0.3   | No        |

## Design: safe by default

`dupefinder` is read-only by design. The library reads file metadata and file bytes to calculate hashes.

It does **not**:

- delete, move, rename, or overwrite files;
- create or write files (except the SQLite cache when explicitly enabled);
- connect to the internet or transmit data;
- execute subprocesses;
- import third-party packages.

## SQLite cache

The optional hash cache writes **only** when the user explicitly enables it:

```python
# Library
from dupefinder.cache import SQLiteHashCache
with SQLiteHashCache("my-cache.sqlite") as cache:
    ...

# CLI
dupefinder ./data --cache my-cache.sqlite
```

The cache file is written only to the path the user selects. No cache file is created or modified without explicit user action.

## Symbolic links

Symbolic links are **not** followed by default. This prevents the scanner from escaping the intended directory tree or getting stuck in cycles.

Users who need symlink traversal must opt in explicitly:

```python
from dupefinder.models import ScanOptions
options = ScanOptions(follow_symlinks=True)
```

```bash
dupefinder ./path --follow-symlinks
```

When `follow_symlinks=True`, the scanner tracks `(st_dev, st_ino)` pairs to detect and break cycles.

Symbolic links used as the scan root are also rejected by default. Pass `follow_symlinks=True` to allow them.

## Large files

Files are read in configurable chunks (default: 1 MiB). This prevents loading arbitrarily large files into memory.

## Permission errors

By default, files and directories that cannot be accessed are **skipped** and recorded as `ScanIssue` entries in the report. No exception is raised.

Users who want strict behavior can enable it:

```python
options = ScanOptions(on_error="raise")
```

```bash
dupefinder ./path --strict
```

## Reporting a vulnerability

If you discover a security vulnerability, please **do not open a public GitHub issue**.

Instead, open a [private security advisory](https://github.com/igors93/dupefinder/security/advisories/new) in the repository, or contact the maintainer directly at **igor.souza.92@gmail.com**.

Please include:

- A clear description of the vulnerability.
- Steps to reproduce it.
- The version of `dupefinder` where you observed it.
- Any relevant environment details (OS, Python version).

You can expect an acknowledgement within 72 hours.
