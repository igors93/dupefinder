# Security

## Read-only by design

`dupefinder` reads file metadata and file bytes to compute hashes. It never writes to disk.

It does **not**:

- delete, move, rename, truncate, or overwrite any file;
- create new files or directories;
- spawn subprocesses;
- connect to the internet;
- import third-party packages.

## Symbolic links

Symbolic links are **not** followed by default (`follow_symlinks=False`). This prevents the scanner from:

- leaving the intended directory tree;
- reading files the user did not intend to expose;
- entering infinite loops caused by circular symlinks.

When `follow_symlinks=True`, the scanner tracks `(st_dev, st_ino)` pairs to detect and break cycles automatically.

## Large files

Files are read in configurable chunks (default: 1 MiB). The memory footprint is proportional to `chunk_size`, not file size. You can lower `chunk_size` to further limit peak memory usage.

## Permission errors

The default behavior (`on_error="skip"`) catches `OSError` during both directory traversal and file hashing, records the problem as a `ScanIssue`, and continues. No file content is exposed.

Strict mode (`on_error="raise"`) raises `FileAccessError` or `FileHashError` immediately instead.

## Input validation

All options are validated before the scan begins via `validate_options()`. Bad values (e.g. unsupported hash algorithms, negative sizes) raise a clear exception rather than silently producing wrong results.

## Reporting vulnerabilities

See [SECURITY.md](../SECURITY.md) for the vulnerability reporting process.
