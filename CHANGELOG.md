# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `DupeFinder` class — integration-ready scan engine with typed events, cancellation, and optional hash cache.
- `ScanEvent` frozen dataclass — typed events emitted during each scan phase (`scan_started`, `file_discovered`, `file_hashed`, `duplicate_group_found`, `scan_completed`, `scan_cancelled`).
- `ScanOptions.max_files` — stop file discovery after N files.
- `ScanOptions.max_depth` — limit directory recursion depth (`0` = root only).
- `ScanOptions.timeout_seconds` — automatically cancel scan after N seconds.
- `ScanReport.cancelled` — `True` when the scan was cancelled early.
- `ScanReport.elapsed_seconds` — wall-clock scan duration (set when using `DupeFinder`).
- `ScanReport.to_dict()` and `ScanReport.to_json()` — convenience methods for serialization.
- `DuplicateGroup.to_dict()` — serialize a single group to a plain dictionary.
- `ScanIssue.to_dict()` — serialize a single issue to a plain dictionary.
- `HashCache` protocol — interface for pluggable hash caches.
- `SQLiteHashCache` — SQLite-backed persistent hash cache; entries validated by file size and mtime.
- `SCHEMA_VERSION = "1.0"` constant in `dupefinder.constants`.
- `schema_version` field in all JSON/dict output from `report_to_dict()` and `report_to_json()`.
- CLI flags: `--max-files`, `--max-depth`, `--timeout`, `--cache`, `--progress`.
- `--progress` flag prints live discovery/hashing progress to stderr.
- New examples: `fastapi_like_integration.py`, `ci_fail_on_duplicates.py`, `progress_callback.py`, `sqlite_cache.py`, `cancel_scan.py`.

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
