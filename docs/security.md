# Security notes

`dupefinder` is safe by default because it only reads files.

## No destructive actions

The library does not delete files. This is intentional.

Duplicate detection and duplicate deletion are different problems. A detector should be safe and predictable.

## No network

The library does not connect to the internet.

## No symlink traversal by default

Symbolic links can point outside the folder the user thinks they are scanning. For that reason, `follow_symlinks` is disabled by default.

## Chunked reads

Large files are read piece by piece. This reduces memory risk.

## Permission errors

The default behavior is to record issues and continue. Strict mode is available for users who prefer exceptions.
