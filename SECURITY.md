# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Design: safe by default

`dupefinder` is read-only by design. The library reads file metadata and file bytes to calculate hashes.

It does **not**:

- delete, move, rename, or overwrite files;
- create or write files;
- connect to the internet or transmit data;
- execute subprocesses;
- import third-party packages.

## Symbolic links

Symbolic links are **not** followed by default. This prevents the scanner from escaping the intended directory tree or getting stuck in cycles.

Users who need symlink traversal must opt in explicitly:

```python
from dupefinder.models import ScanOptions
options = ScanOptions(follow_symlinks=True)
```

When `follow_symlinks=True`, the scanner tracks `(st_dev, st_ino)` pairs to detect and break cycles.

## Large files

Files are read in configurable chunks (default: 1 MiB). This prevents loading arbitrarily large files into memory.

## Permission errors

By default, files and directories that cannot be accessed are **skipped** and recorded as `ScanIssue` entries in the report. No exception is raised.

Users who want strict behavior can enable it:

```python
options = ScanOptions(on_error="raise")
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
