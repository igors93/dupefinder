# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — 2026-06-04

### Added

- `scan(path, options)` — returns a complete `ScanReport` with duplicate groups, file counts, and any issues encountered.
- `find_duplicates(path, options)` — simplified function that returns only the duplicate groups.
- `ScanOptions` — frozen dataclass to configure every aspect of a scan (algorithm, chunk size, size filters, hidden-file handling, symlink following, error handling).
- `ScanReport`, `DuplicateGroup`, `FileInfo`, `ScanIssue` — typed, immutable data models for all scan results.
- Chunked file hashing via `hashlib` — any algorithm available in `hashlib.algorithms_available` is supported.
- Two-pass duplicate detection: group by file size first, hash only candidates.
- `format_report()` — human-readable text output.
- `report_to_json()` / `report_to_dict()` — structured JSON/dict output.
- `dupefinder` CLI command with flags: `--algorithm`, `--chunk-size`, `--min-size`, `--max-size`, `--include-ext`, `--ignore-ext`, `--no-ignore-hidden`, `--follow-symlinks`, `--strict`, `--json`, `--fail-on-duplicates`, `--version`.
- Custom exception hierarchy: `DupeFinderError`, `InvalidPathError`, `UnsupportedHashAlgorithmError`, `InvalidOptionError`, `FileAccessError`, `FileHashError`.
- Symlink loop detection in directory traversal.
- Unit tests for all modules using only the Python standard library.
- Zero runtime dependencies — standard library only.

[Unreleased]: https://github.com/igors93/dupefinder/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/igors93/dupefinder/releases/tag/v0.1.0
