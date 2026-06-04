# API Reference

## Top-level functions

These are the main entry points. Import them directly from `dupefinder`:

```python
from dupefinder import find_duplicates, scan
```

---

### `find_duplicates(path, options=None)`

```python
def find_duplicates(
    path: str | Path,
    options: ScanOptions | None = None,
) -> tuple[DuplicateGroup, ...]: ...
```

Scan `path` and return all duplicate groups. This is the simplest way to use the library.

Returns an empty tuple when no duplicates are found.

**Parameters**

| Name | Type | Description |
|------|------|-------------|
| `path` | `str \| Path` | File or directory to scan. |
| `options` | `ScanOptions \| None` | Scan configuration. Defaults to `ScanOptions()`. |

**Raises**

- `InvalidPathError` — path does not exist.
- `UnsupportedHashAlgorithmError` — `options.algorithm` is not available.
- `InvalidOptionError` — an option value is invalid.
- `FileAccessError` — a file could not be read and `on_error="raise"`.

---

### `scan(path, options=None)`

```python
def scan(
    path: str | Path,
    options: ScanOptions | None = None,
) -> ScanReport: ...
```

Scan `path` and return a complete `ScanReport`. Use this when you need statistics, non-fatal issues, or full control over the result.

**Parameters** and **Raises**: same as `find_duplicates`.

---

## Data models

Import from `dupefinder` or `dupefinder.models`:

```python
from dupefinder import ScanOptions, ScanReport, DuplicateGroup, FileInfo, ScanIssue
```

---

### `ScanOptions`

Frozen dataclass. Controls every aspect of a scan.

```python
@dataclass(frozen=True)
class ScanOptions:
    algorithm: Literal["skip", "raise"] = "sha256"
    chunk_size: int = 1_048_576        # 1 MiB
    min_size: int = 1                  # bytes
    max_size: int | None = None
    ignore_hidden: bool = True
    follow_symlinks: bool = False
    ignored_dirs: frozenset[str] = DEFAULT_IGNORED_DIRS
    ignored_extensions: frozenset[str] = frozenset()
    include_extensions: frozenset[str] | None = None
    on_error: Literal["skip", "raise"] = "skip"
```

**Fields**

| Field | Default | Description |
|-------|---------|-------------|
| `algorithm` | `"sha256"` | Any algorithm in `hashlib.algorithms_available`. |
| `chunk_size` | `1_048_576` | Bytes read per chunk when hashing. |
| `min_size` | `1` | Files smaller than this (in bytes) are skipped. |
| `max_size` | `None` | Files larger than this (in bytes) are skipped. `None` means no limit. |
| `ignore_hidden` | `True` | Skip files and directories whose path contains a dot-prefixed component. |
| `follow_symlinks` | `False` | Whether to follow symbolic links. Cycle detection is always active when enabled. |
| `ignored_dirs` | see `constants.py` | Directory names to skip (e.g. `.git`, `node_modules`, `__pycache__`). |
| `ignored_extensions` | `frozenset()` | File extensions to skip, e.g. `frozenset({".tmp", ".log"})`. |
| `include_extensions` | `None` | When set, only files with these extensions are scanned. |
| `on_error` | `"skip"` | `"skip"` records access errors as `ScanIssue`; `"raise"` raises `FileAccessError` or `FileHashError`. |

---

### `ScanReport`

Frozen dataclass. The complete result of a `scan()` call.

**Fields**

| Field | Type | Description |
|-------|------|-------------|
| `root` | `Path` | The resolved root path that was scanned. |
| `groups` | `tuple[DuplicateGroup, ...]` | All duplicate groups, sorted by size and hash. |
| `scanned_files` | `int` | Number of files that passed the filters. |
| `hashed_files` | `int` | Number of files that were actually hashed. |
| `issues` | `tuple[ScanIssue, ...]` | Non-fatal problems encountered during the scan. |

**Properties**

| Property | Type | Description |
|----------|------|-------------|
| `total_groups` | `int` | Number of duplicate groups. |
| `total_duplicate_files` | `int` | Total number of files across all groups. |
| `total_wasted_space` | `int` | Bytes that could be freed by keeping one file per group. |
| `has_duplicates` | `bool` | `True` when at least one duplicate group exists. |
| `has_issues` | `bool` | `True` when at least one issue was recorded. |

---

### `DuplicateGroup`

Frozen dataclass. Represents a set of files with identical content.

**Fields**

| Field | Type | Description |
|-------|------|-------------|
| `digest` | `str` | Hex digest of the file content. |
| `size` | `int` | File size in bytes. |
| `files` | `tuple[Path, ...]` | Sorted absolute paths of every file in the group. |

**Properties**

| Property | Type | Description |
|----------|------|-------------|
| `count` | `int` | Number of files in this group. |
| `wasted_space` | `int` | `size * (count - 1)` — bytes that could be freed. |

---

### `FileInfo`

Frozen dataclass. Metadata for a single file as it passes through the pipeline.

**Fields**

| Field | Type | Description |
|-------|------|-------------|
| `path` | `Path` | Absolute path to the file. |
| `size` | `int` | File size in bytes. |
| `digest` | `str \| None` | Hex digest after hashing, or `None` if not yet hashed. |

---

### `ScanIssue`

Frozen dataclass. A non-fatal problem recorded during a scan (only when `on_error="skip"`).

**Fields**

| Field | Type | Description |
|-------|------|-------------|
| `path` | `Path` | The file or directory where the issue occurred. |
| `message` | `str` | Human-readable description of the error. |
| `phase` | `str` | `"scan"` (discovery) or `"hash"` (hashing). |

---

## Report helpers

```python
from dupefinder.report import format_report, report_to_json, report_to_dict, bytes_to_human
```

### `format_report(report) -> str`

Return a human-readable text summary of the scan.

### `report_to_json(report, *, indent=2) -> str`

Serialize the report to a JSON string.

### `report_to_dict(report) -> dict[str, Any]`

Convert the report to a plain Python dictionary (all paths are stringified).

### `bytes_to_human(size) -> str`

Convert a byte count to a readable string, e.g. `1536` → `"1.54 KB"`.

---

## Exceptions

```python
from dupefinder.errors import (
    DupeFinderError,
    InvalidPathError,
    UnsupportedHashAlgorithmError,
    InvalidOptionError,
    FileAccessError,
    FileHashError,
)
```

All exceptions inherit from `DupeFinderError`, which inherits from `Exception`.

| Exception | When raised |
|-----------|-------------|
| `InvalidPathError` | The scan path does not exist or is not a file/directory. |
| `UnsupportedHashAlgorithmError` | The algorithm is not in `hashlib.algorithms_available`. |
| `InvalidOptionError` | An option value is invalid (e.g. `chunk_size=0`). |
| `FileAccessError` | A file or directory could not be accessed (strict mode only). |
| `FileHashError` | A file could not be hashed (strict mode only). |
