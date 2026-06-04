# API

## `find_duplicates(path, options=None)`

Simple function for most users.

Returns a tuple of `DuplicateGroup` objects.

```python
from dupefinder import find_duplicates

groups = find_duplicates(".")
```

## `scan(path, options=None)`

Advanced function for users who want a full report.

Returns a `ScanReport` object.

```python
from dupefinder import scan

report = scan(".")
print(report.total_groups)
```

## `ScanOptions`

Configuration object.

Useful fields:

- `algorithm`: hash algorithm, default `sha256`.
- `chunk_size`: how many bytes are read at a time.
- `min_size`: ignore smaller files.
- `max_size`: ignore larger files.
- `ignore_hidden`: ignore dotfiles and dotfolders.
- `follow_symlinks`: follow symbolic links. Default is `False`.
- `include_extensions`: scan only selected extensions.
- `ignored_extensions`: skip selected extensions.
- `on_error`: `skip` or `raise`.
