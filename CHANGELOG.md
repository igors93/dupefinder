# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] — 2026-06-04

### Added

- `ScanProgress` frozen dataclass — simplified progress snapshots delivered to the new `on_progress` callback of `DupeFinder`. Fields: `root`, `phase` (`"discovery"`, `"hashing"`, `"grouping"`, `"done"`), `scanned_files`, `hashed_files`, `total_candidates`, `duplicate_groups`, `elapsed_seconds`, `cancelled`.
- `DupeFinder.on_progress` parameter — optional callback that receives a `ScanProgress` snapshot after each file discovered or hashed, and once more at the end with `phase="done"`.
- `ScanReport.total_bytes_read` is now always populated (previously always `None`). Zero when no files were hashed; positive when hashing occurred.
- `ScanEvent.from_cache` and `ScanEvent.bytes_read` fields — reserved for future per-file cache-hit tracking.
- `grouping.candidate_files()` — public helper that filters files sharing a size with at least one other file.
- `grouping.groups_from_hash_map()` — public helper that builds and sorts `DuplicateGroup` objects from a `(size, digest) → paths` mapping.
- `_ScanCancelled` internal exception in `errors.py` — raised by `hash_file()` between chunks when `should_cancel` returns `True`; caught at the engine boundary so partial digests are never stored.
- `hash_file()` now accepts `should_cancel` and `on_bytes_read` keyword-only callbacks for mid-file cancellation and byte-count tracking.
- `hash_files()` now accepts `should_cancel` and `on_bytes_read` and forwards them to `hash_file()`; `_ScanCancelled` propagates cleanly to the engine.
- `total_bytes_read` field in `report_to_dict()` / JSON output (schema version bumped to `"1.1"`).

### Fixed

- Engine now emits `type="issue"` events for all issues collected during discovery and hashing (previously issues were silently dropped from the event stream).
- Cache error handling now catches `sqlite3.Error` in addition to `OSError`; previously a corrupt or locked SQLite database would propagate unhandled.
- CLI cache creation moved inside the `try` block so `OSError` or `sqlite3.Error` on cache open is caught and reported cleanly with exit code 1.
- Engine no longer duplicates the size-grouping and hash-grouping logic from `grouping.py`; it now delegates to `group_by_size()`, `candidate_files()`, and `groups_from_hash_map()`.

### Changed

- `SCHEMA_VERSION` bumped from `"1.0"` to `"1.1"` (adds `total_bytes_read` to JSON output).
- `dupefinder.__version__` updated to `"0.3.0"`.
- Development status classifier updated from `3 - Alpha` to `4 - Beta`.

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

[Unreleased]: https://github.com/igors93/dupefinder/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/igors93/dupefinder/compare/v0.1.0...v0.3.0
[0.1.0]: https://github.com/igors93/dupefinder/releases/tag/v0.1.0
