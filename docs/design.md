# Design

## Goal

Make duplicate detection simple for end users and easy to maintain for contributors. The library should be safe to run on any machine without needing to read its source code first.

## Data flow

```text
scan(path, options)
  │
  ├─ validate_options()       ← reject bad config early, clear error messages
  ├─ validate_scan_path()     ← reject missing/invalid paths
  │
  ├─ iter_files()             ← os.scandir loop, applies filters
  │       │
  │       ├─ should_ignore_directory()
  │       └─ should_ignore_file()
  │
  ├─ group_by_size()          ← O(n) dict grouping, no I/O
  │
  ├─ hash_files()             ← only files that share a size
  │       └─ hash_file()      ← chunked reads, any hashlib algorithm
  │
  ├─ group_by_hash()          ← collect groups with > 1 file
  │
  └─ ScanReport(...)          ← immutable result
```

## Why group by size first?

Two files with different sizes cannot be byte-for-byte identical. Grouping by size before hashing eliminates the vast majority of files without any I/O beyond the initial `stat()` call.

## Why hash in chunks?

Reading a file entirely into memory to hash it would make the library unsafe on machines with limited RAM or when scanning directories that contain large media files or disk images. Chunked reads keep memory usage constant regardless of file size.

## Why immutable models?

`ScanOptions`, `ScanReport`, `DuplicateGroup`, `FileInfo`, and `ScanIssue` are all frozen dataclasses. This makes results safe to cache, pass between threads, and compare for equality without defensive copying.

## Why no deletion feature?

Duplicate detection and duplicate deletion are different problems with different risk profiles. Detection is always safe. Deletion is irreversible and depends entirely on which copy the user wants to keep. Keeping these separate ensures that `dupefinder` can never accidentally destroy data.

## Why zero dependencies?

External dependencies have their own release cycles, security advisories, and compatibility constraints. Keeping the library dependency-free means it installs instantly on any Python 3.9+ environment, never has conflicting transitive requirements, and has a smaller attack surface.

## Module responsibilities

| Module | Responsibility |
|--------|---------------|
| `api.py` | Public entry points: `scan`, `find_duplicates` |
| `cli.py` | Argument parsing and terminal output |
| `scanner.py` | Directory traversal, `os.scandir`, cycle detection |
| `hashing.py` | Chunked file hashing via `hashlib` |
| `grouping.py` | Size-based pre-grouping and hash-based deduplication |
| `filters.py` | File and directory include/ignore rules |
| `models.py` | Frozen dataclasses for all domain objects |
| `report.py` | Text and JSON serialization |
| `safety.py` | Input validation, path normalization, extension helpers |
| `constants.py` | Default values — single source of truth |
| `errors.py` | Custom exception hierarchy |

## Extending the library

- **New output format**: add a function to `report.py` that takes a `ScanReport` and returns a string.
- **New filter**: add a condition to `should_ignore_file` or `should_ignore_directory` in `filters.py`.
- **New hash algorithm**: no code change needed — pass any name from `hashlib.algorithms_available` via `ScanOptions(algorithm=...)`.
- **Parallel hashing**: the pipeline in `grouping.py` can be replaced with a `concurrent.futures.ThreadPoolExecutor` without changing any other module.
