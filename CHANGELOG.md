# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

No unreleased changes.

## [0.3.1] — 2026-06-05

### Fixed

- SQLite cache files are now correctly excluded when the scan root is accessed through a symbolic link. Path comparison now uses `resolve(strict=False)` on both sides so symlinked and real paths map to the same canonical key.
- `-wal`, `-shm`, and `-journal` SQLite auxiliary files are excluded alongside the main cache database.
- PyPI publishing workflow (`publish.yml`) rewritten as valid YAML — the previous file contained Markdown code fences that made it unparseable by GitHub Actions.

### Changed

- Minimum supported Python version raised from 3.9 to 3.10. The codebase uses `X | Y` union syntax broadly; requiring 3.10 makes this consistent and allows `get_type_hints()` to resolve annotations correctly at runtime.
- `ProgressPhase` values corrected to `"discovery"`, `"hashing"`, and `"done"` — the `"grouping"` phase mentioned in the previous changelog was never emitted.

### Tooling

- CI restructured into three jobs: `quality` (Ruff lint + format check + Pyright), `tests` (matrix across Ubuntu/Windows/macOS and Python 3.10–3.13), and `package` (build, Twine check, `py.typed` verification, wheel smoke test).
- `pyyaml` added to development dependencies to enable workflow YAML validation in tests.
- New regression tests: symlink policy (directory and file roots, broken symlinks), cache exclusion through symlinked roots, WAL/SHM/journal exclusion, typing contract, cancellation exit codes, version consistency, `py.typed` marker, workflow YAML validation.

## [0.3.0] — 2026-06-04

### Added

- `DupeFinder` class — integration-ready scan engine with typed events, cancellation, and optional hash cache.
- `ScanEvent` frozen dataclass — typed events emitted during each scan phase (`scan_started`, `file_discovered`, `file_hashed`, `duplicate_group_found`, `issue`, `scan_completed`, `scan_cancelled`).
- `ScanProgress` frozen dataclass — simplified progress snapshots delivered to the new `on_progress` callback. Fields: `root`, `phase` (`"discovery"`, `"hashing"`, `"done"`), `scanned_files`, `hashed_files`, `total_candidates`, `duplicate_groups`, `elapsed_seconds`, `cancelled`.
- `DupeFinder.on_progress` parameter — optional callback that receives a `ScanProgress` snapshot after each file discovered or hashed, and once more at the end with `phase="done"`.
- `ScanOptions.max_files` — stop file discovery after N files.
- `ScanOptions.max_depth` — limit directory recursion depth (`0` = root only).
- `ScanOptions.timeout_seconds` — automatically cancel scan after N seconds.
- `ScanReport.cancelled` — `True` when the scan was cancelled early.
- `ScanReport.elapsed_seconds` — wall-clock scan duration.
- `ScanReport.total_bytes_read` — total bytes read during hashing (always populated; zero when no files were hashed).
- `ScanReport.to_dict()` and `ScanReport.to_json()` — convenience methods for serialization.
- `DuplicateGroup.to_dict()` — serialize a single group to a plain dictionary.
- `ScanIssue.to_dict()` — serialize a single issue to a plain dictionary.
- `HashCache` protocol — interface for pluggable hash caches.
- `SQLiteHashCache` — SQLite-backed persistent hash cache; entries validated by file size and mtime.
- `ScanEvent.from_cache` and `ScanEvent.bytes_read` fields.
- `grouping.candidate_files()` — public helper that filters files sharing a size with at least one other file.
- `grouping.groups_from_hash_map()` — public helper that builds and sorts `DuplicateGroup` objects from a `(size, digest) → paths` mapping.
- `_ScanCancelled` internal exception in `errors.py` — raised between chunks when `should_cancel` returns `True`; caught at the engine boundary.
- `hash_file()` accepts `should_cancel` and `on_bytes_read` keyword-only callbacks.
- `hash_files()` accepts `should_cancel` and `on_bytes_read` and forwards them to `hash_file()`.
- `SCHEMA_VERSION = "1.1"` constant; `schema_version` and `total_bytes_read` fields in all JSON/dict output.
- CLI flags: `--max-files`, `--max-depth`, `--timeout`, `--cache`, `--progress`.
- `--progress` flag prints live discovery/hashing progress to stderr.
- Cancelled CLI scans exit with status code `3`.

### Fixed

- Engine now emits `type="issue"` events for all issues collected during discovery and hashing.
- Cache error handling now catches `sqlite3.Error` in addition to `OSError`.
- CLI cache creation moved inside the `try` block so errors on cache open are caught and reported cleanly with exit code 1.
- Engine no longer duplicates the size-grouping and hash-grouping logic from `grouping.py`.

### Changed

- `SCHEMA_VERSION` bumped from `"1.0"` to `"1.1"`.
- `dupefinder.__version__` updated to `"0.3.0"`.
- Development status classifier updated from `3 - Alpha` to `4 - Beta`.

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

[Unreleased]: https://github.com/igors93/dupefinder/compare/v0.3.1...HEAD
[0.3.1]: https://github.com/igors93/dupefinder/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/igors93/dupefinder/compare/v0.1.0...v0.3.0
[0.1.0]: https://github.com/igors93/dupefinder/releases/tag/v0.1.0
