# Security Policy

## Safe by default

`dupefinder` is read-only by design.

The library reads file metadata and file bytes to calculate hashes. It does not delete, move, rename, edit, upload, or transmit user files.

## Symbolic links

Symbolic links are not followed by default. This reduces the chance of scanning unexpected locations or getting stuck in link loops.

Users must explicitly enable symbolic link traversal with `follow_symlinks=True`.

## Large files

Files are read in chunks. This prevents the library from loading huge files entirely into memory.

## Permission errors

By default, files that cannot be read are skipped and recorded in the report errors. Users can request strict behavior with `on_error="raise"`.

## Reporting vulnerabilities

If you find a vulnerability, please open a private security advisory in the repository or contact the maintainer.
